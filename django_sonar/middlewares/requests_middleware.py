import json
import socket
import time
import tracemalloc
import uuid
from datetime import datetime

from django.conf import settings
from django.db import connection
from django.urls import resolve
from django.utils.timezone import make_aware


class RequestsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
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
        memory_diff = (end_memory_usage - start_memory_usage) / 1024  # Convert to KB

        # Ensure the response has a content attribute and is not a streaming response
        response_content = None
        if hasattr(response, 'content'):
            response_content = response.content

        # log all queries
        executed_queries = connection.queries

        # Capture request details
        http_verb = request.method
        url_path = request.path
        http_status = response.status_code

        # logged user
        user_info = None
        if request.user.is_authenticated:
            user_info = {
                'user_id': request.user.id,
                'username': request.user.username,
                'email': request.user.email
            }

        # Additional details
        is_ajax = self.is_ajax(request)
        timestamp = make_aware(datetime.now())  # Make sure the timestamp is timezone-aware
        hostname = socket.gethostname()
        ip_address = self.get_client_ip(request)
        middlewares_used = settings.MIDDLEWARE

        # Log or save the request details here
        request_id = uuid.uuid4()
        print('-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-')
        print(f"Request Details: {request_id}")
        print(f"HTTP Verb: {http_verb}",
              f"URL Path: {url_path}, HTTP Status: {http_status}, Ajax: {is_ajax}",
              f"IP Address: {ip_address}, Hostname: {hostname}")
        print(f"User Info: {user_info}")
        print(f"Timestamp: {timestamp}, View Function: {view_func},"
              f"Middlewares Used: {middlewares_used}, "
              f"Memory Usage Difference: {memory_diff} KB, "
              f"Duration: {duration} ms")
        print(f"Executed Queries: {executed_queries}")
        print(f"Request Headers: {request_headers}")
        print(f"Request GET Payload: {get_payload}")
        print(f"Request POST Payload: {post_payload}")
        print(f"Response size: {len(response_content)} bytes")
        print(f"Session Data: {session_data}")

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
