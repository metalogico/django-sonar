import logging
import socket
import sys
import time
import traceback
import tracemalloc

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import DEFAULT_DB_ALIAS, router, transaction
from django.urls import Resolver404, resolve

from django_sonar import utils
from django_sonar.conf import get_sonar_settings
from django_sonar.core import DataCollector, PathFilter, RequestParser, SensitiveDataFilter
from django_sonar.core.query_capture import capture_database_queries
from django_sonar.models import SonarRequest


logger = logging.getLogger(__name__)


class RequestsMiddleware:
    """Collect request telemetry without changing the application response."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.path_filter = PathFilter()
        self.sensitive_filter = SensitiveDataFilter()
        self.parser = RequestParser()
        self.sonar_settings = get_sonar_settings()

        if self.sonar_settings['capture_memory'] and not tracemalloc.is_tracing():
            tracemalloc.start()

    def __call__(self, request):
        if self.path_filter.should_exclude(request.path):
            return self.get_response(request)

        context_token = utils.start_capture_context()
        collection_errors = []

        try:
            started_at = time.perf_counter()
            start_memory_usage = self._current_memory_usage()

            with capture_database_queries(self.sonar_settings['max_queries_per_request']) as query_capture:
                if query_capture.setup_error is not None:
                    collection_errors.append(query_capture.setup_error)
                try:
                    captured_request = self._capture_request_data(request)
                except Exception:
                    collection_errors.append(sys.exc_info())
                    captured_request = {
                        'headers': {},
                        'session': {},
                        'get_payload': {},
                        'post_payload': {},
                    }
                response = self.get_response(request)

            duration = round((time.perf_counter() - started_at) * 1000)
            memory_diff = self._memory_difference(start_memory_usage)

            try:
                self._persist_capture(
                    request=request,
                    response=response,
                    captured_request=captured_request,
                    duration=duration,
                    memory_diff=memory_diff,
                    query_capture=query_capture,
                )
            except Exception:
                collection_errors.append(sys.exc_info())

            return response
        finally:
            utils.end_capture_context(context_token)
            for collection_error in collection_errors:
                logger.warning(
                    'Django Sonar could not collect or persist telemetry for %s',
                    getattr(request, 'path', '<unknown>'),
                    exc_info=collection_error,
                )

    def _capture_request_data(self, request):
        request_headers = dict(request.headers.items())
        session = getattr(request, 'session', None)
        session_data = dict(session) if session is not None else {}
        get_payload = request.GET.dict()
        post_payload = self.parser.get_body_payload(
            request,
            capture_raw_body=self.sonar_settings['capture_raw_body'],
            raw_body_max_bytes=self.sonar_settings['raw_body_max_bytes'],
        )

        return {
            'headers': self.sensitive_filter.filter(request_headers),
            'session': self.sensitive_filter.filter(session_data),
            'get_payload': self.sensitive_filter.filter(get_payload),
            'post_payload': self.sensitive_filter.filter(post_payload),
        }

    def _persist_capture(
        self,
        request,
        response,
        captured_request,
        duration,
        memory_diff,
        query_capture,
    ):
        query_string = request.GET.copy()
        for key, value in captured_request['get_payload'].items():
            query_string[key] = value
        full_url = request.path
        if query_string:
            full_url = f'{full_url}?{query_string.urlencode()}'

        database_alias = router.db_for_write(SonarRequest) or DEFAULT_DB_ALIAS
        with transaction.atomic(using=database_alias):
            sonar_request = SonarRequest.objects.using(database_alias).create(
                verb=request.method,
                path=full_url,
                status=response.status_code,
                duration=duration,
                query_count=query_capture.query_count,
                ip_address=self.parser.get_client_ip(request),
                hostname=socket.gethostname(),
                is_ajax=self.parser.is_ajax(request),
            )

            collector = DataCollector(
                sonar_request.uuid,
                sensitive_filter=self.sensitive_filter,
                using=database_alias,
            )
            collector.save_details(
                self._get_user_info(request),
                self._get_view_function(request),
                getattr(settings, 'MIDDLEWARE', []),
                memory_diff,
            )
            collector.save_payload(
                captured_request['get_payload'],
                captured_request['post_payload'],
            )
            collector.save_queries(
                query_capture.queries,
                query_count=query_capture.query_count,
                truncated=query_capture.truncated,
            )
            collector.save_headers(captured_request['headers'])
            collector.save_session(captured_request['session'])
            collector.save_events()
            collector.save_logs()
            collector.save_dumps()
            collector.save_exceptions()

    @staticmethod
    def _get_view_function(request):
        resolved = getattr(request, 'resolver_match', None)
        if resolved is None:
            try:
                resolved = resolve(getattr(request, 'path_info', request.path))
            except Resolver404:
                return '<unresolved>'

        func = resolved.func
        module = getattr(func, '__module__', func.__class__.__module__)
        name = getattr(func, '__name__', func.__class__.__name__)
        return f'{module}.{name}'

    @staticmethod
    def _get_user_info(request):
        user = getattr(request, 'user', None)
        if user is None or not getattr(user, 'is_authenticated', False):
            return None

        user_model = get_user_model()
        return {
            'user_id': user.id,
            'username': user.get_username(),
            'email': getattr(user, user_model.get_email_field_name(), 'No email provided'),
        }

    def _current_memory_usage(self):
        if not self.sonar_settings['capture_memory'] or not tracemalloc.is_tracing():
            return None
        return tracemalloc.get_traced_memory()[0]

    @staticmethod
    def _memory_difference(start_memory_usage):
        if start_memory_usage is None:
            return None
        return (tracemalloc.get_traced_memory()[0] - start_memory_usage) / 1024 / 1024

    def process_exception(self, request, exception):
        """Queue concise exception information in the active request context."""
        exc_traceback = traceback.extract_tb(exception.__traceback__)
        if exc_traceback:
            last_frame = exc_traceback[-1]
            error_info = {
                'file_name': last_frame.filename,
                'line_number': last_frame.lineno,
                'function_name': last_frame.name,
                'exception_message': str(exception),
            }
        else:
            error_info = {
                'exception_message': str(exception),
                'detailed_traceback': 'No traceback available',
            }
        utils.add_sonar_exception(error_info)
