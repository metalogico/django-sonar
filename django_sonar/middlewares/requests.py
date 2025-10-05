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
from django_sonar.models import SonarRequest
from django_sonar.core import RequestParser, DataCollector, PathFilter, SensitiveDataFilter

class RequestsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.sonar_request_uuid = None
        self.path_filter = PathFilter()
        self.sensitive_filter = SensitiveDataFilter()
        self.parser = RequestParser()
        tracemalloc.start()  # Start tracing memory allocation    

    def __call__(self, request):
        # Check if the request path is excluded
        if self.path_filter.should_exclude(request.path):
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

        # Capture session data
        session_data = dict(request.session)

        # Capture GET/POST data
        get_payload = request.GET.dict()
        post_payload = self.parser.get_body_payload(request)
        
        # Filter sensitive data from all captured data
        request_headers = self.sensitive_filter.filter_dict(request_headers)
        session_data = self.sensitive_filter.filter_dict(session_data)
        get_payload = self.sensitive_filter.filter_dict(get_payload)
        post_payload = self.sensitive_filter.filter_dict(post_payload)

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
        query_count = len(executed_queries)

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
        is_ajax = self.parser.is_ajax(request)
        timestamp = make_aware(datetime.now())  # Make sure the timestamp is timezone-aware
        hostname = socket.gethostname()
        ip_address = self.parser.get_client_ip(request)
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
            query_count=query_count,
            ip_address=ip_address,
            hostname=hostname,
            is_ajax=is_ajax,
            created_at=timestamp,
        )

        # saves request's uuid
        self.sonar_request_uuid = sonar_request.uuid

        # Initialize data collector for this request
        collector = DataCollector(self.sonar_request_uuid)

        # Save all collected data
        collector.save_details(user_info, view_func, middlewares_used, memory_diff)
        collector.save_payload(get_payload, post_payload)
        collector.save_queries(executed_queries)
        collector.save_headers(request_headers)
        collector.save_session(session_data)
        collector.save_dumps()
        collector.save_exceptions()

        return response

    def process_exception(self, request, exception):
        """
        Process exceptions and store them in thread-local storage.
        
        This method is called by Django when an exception occurs during request processing.
        The exception data is stored temporarily and will be saved to the database
        by the DataCollector during the normal request flow.
        
        :param request: Django request object
        :param exception: Exception instance that was raised
        """
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
