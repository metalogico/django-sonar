import socket
import time
import traceback
import tracemalloc
from datetime import datetime
from urllib.parse import urlencode

from django.conf import settings
from django.db import connection
from django.urls import resolve
from django.utils.timezone import make_aware
from django.contrib.auth import get_user_model
from django_sonar import utils
from django_sonar.models import SonarRequest, SonarData

class RequestsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.sonar_request_uuid = None
        tracemalloc.start()  # Start tracing memory allocation

    def __call__(self, request):
        # Get the list of excluded paths from settings
        excluded_paths = settings.DJANGO_SONAR.get('excludes', [])

        # Check if the request path is excluded
        if any(request.path.startswith(path) for path in excluded_paths):
            return self.get_response(request)

        # Reset query log at the beginning of the request
        connection.queries_log.clear()

        # Start timer
        start_time = time.time()

        start_memory_usage = tracemalloc.get_traced_memory()[0]  # Get current memory usage

        # Resolve view function
        resolved = resolve(request.path)
        view_func = f"{resolved.func.__module__}.{resolved.func.__name__}"

        # Capture request headers
        request_headers = {k: v for k, v in request.headers.items()}

        # Capture session data (ensure sensitive data is handled appropriately)
        session_data = dict(request.session)

        # Capture GET/POST data
        get_payload = request.GET.dict()
        post_payload = self.get_post_payload(request)

        # Process the request
        response = self.get_response(request)

        # Stop timer / duration
        end_time = time.time()
        duration = (end_time - start_time) * 1000  # Convert to milliseconds

        # memory used
        end_memory_usage = tracemalloc.get_traced_memory()[0]  # End memory usage
        memory_diff = (end_memory_usage - start_memory_usage) / 1024 / 1024  # Convert to MB

        # Ensure the response has a content attribute and is not a streaming response
        response_content = None
        if hasattr(response, 'content'):
            response_content = response.content

        # log all queries
        executed_queries = connection.queries

        # Capture request details
        http_verb = request.method
        url_path = request.path
        query_string = urlencode(get_payload)
        http_status = response.status_code

        # logged user
        user_info = None
        # get user info if user is authenticated
        User = get_user_model()
        if request.user.is_authenticated:
            # use get_username() instead of username to support custom user models
            # use get_email_field_name() instead of email to support custom user models
            user_info = {
                "user_id": request.user.id,
                "username": request.user.get_username(),
                "email": getattr(request.user, User.get_email_field_name(), 'No email provided'),
                }

        # Additional details
        is_ajax = self.is_ajax(request)
        timestamp = make_aware(datetime.now())  # Make sure the timestamp is timezone-aware
        hostname = socket.gethostname()
        ip_address = self.get_client_ip(request)
        middlewares_used = settings.MIDDLEWARE

        # if there is a querystring add it to the full url
        if query_string:
            full_url = f"{url_path}?{query_string}"
        else:
            full_url = url_path

        # Create a SonarRequest object
        sonar_request = SonarRequest.objects.create(
            verb=http_verb,
            path=full_url,
            status=http_status,
            duration=duration,
            ip_address=ip_address,
            hostname=hostname,
            is_ajax=is_ajax,
            created_at=timestamp,
        )

        # saves request's uuid
        self.sonar_request_uuid = sonar_request.uuid

        # saves request's details
        self.sonar_details(user_info, view_func, middlewares_used, memory_diff)

        # saves request's payload
        self.sonar_payload(get_payload, post_payload)

        # stores the queries
        self.sonar_queries(executed_queries)

        # saves request's headers
        self.sonar_headers(request_headers)

        # saves request's session
        self.sonar_sessions(session_data)

        # saves request's dump data
        self.sonar_dumps()
        utils.reset_sonar_dump()

        # process the exception
        self.sonar_exceptions()
        utils.reset_sonar_exceptions()

        return response

    def get_client_ip(self, request):
        """Get the client IP address from the request object."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def is_ajax(self, request):
        return request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    def get_post_payload(self, request):
        post_data = request.POST.copy()
        return post_data

    def process_exception(self, request, exception):
        """Process the exception and keep it in local storage."""
        exc_traceback = traceback.extract_tb(exception.__traceback__)

        # If there's at least one frame in the traceback
        if exc_traceback:
            # Get the last frame of the traceback
            last_frame = exc_traceback[-1]

            error_info = {
                "file_name": last_frame.filename,
                "line_number": last_frame.lineno,
                "function_name": last_frame.name,
                "exception_message": str(exception)
            }
        else:
            # Fallback if traceback is empty for some reason
            error_info = {
                "exception_message": str(exception),
                "detailed_traceback": "No traceback available",
            }
        utils.add_sonar_exception(error_info)

    def sonar_exceptions(self):
        sonar_exceptions = utils.get_sonar_exceptions()
        for ex in sonar_exceptions:
            SonarData.objects.create(
                sonar_request_id=self.sonar_request_uuid,
                category='exception',
                data=ex
            )

    def sonar_dumps(self):
        """Process the dumps and save them to the database."""
        sonar_dumps = utils.get_sonar_dump()
        for dump in sonar_dumps:
            SonarData.objects.create(
                sonar_request_id=self.sonar_request_uuid,
                category='dumps',
                data=dump
            )

    def sonar_details(self, user_info, view_func, middlewares_used, memory_diff):
        """Process the details and save them to the database."""
        details = {
            'user_info': user_info,
            'view_func': view_func,
            'middlewares_used': middlewares_used,
            'memory_used': memory_diff
        }
        SonarData.objects.create(
            sonar_request_id=self.sonar_request_uuid,
            category='details',
            data=details
        )

    def sonar_payload(self, get_payload, post_payload):
        """Process the payload and save them to the database."""
        payload = {
            'get_payload': get_payload,
            'post_payload': post_payload
        }
        SonarData.objects.create(
            sonar_request_id=self.sonar_request_uuid,
            category='payload',
            data=payload
        )

    def sonar_queries(self, executed_queries):
        """Process the queries and save them to the database."""
        queries = {
            'executed_queries': executed_queries
        }
        SonarData.objects.create(
            sonar_request_id=self.sonar_request_uuid,
            category='queries',
            data=queries
        )

    def sonar_headers(self, request_headers):
        """Process the headers and save them to the database."""
        headers = {
            'request_headers': request_headers
        }
        SonarData.objects.create(
            sonar_request_id=self.sonar_request_uuid,
            category='headers',
            data=headers
        )

    def sonar_sessions(self, session_data):
        """Process the session and save them to the database."""
        session = {
            'session_data': session_data
        }
        SonarData.objects.create(
            sonar_request_id=self.sonar_request_uuid,
            category='session',
            data=session
        )
