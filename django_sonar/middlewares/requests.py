import socket
import time
import tracemalloc
from datetime import datetime

from django.conf import settings
from django.db import connection
from django.urls import resolve
from django.utils.timezone import make_aware

from django_sonar import utils
from django_sonar.models import SonarRequest, SonarData


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
        print('-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-')
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

        # Create a SonarRequest object
        sonar_request = SonarRequest.objects.create(
            verb=http_verb,
            path=url_path,
            status=http_status,
            duration=duration,
            ip_address=ip_address,
            hostname=hostname,
            is_ajax=is_ajax,
            created_at=timestamp,
        )

        # saves request's details
        self.process_details(sonar_request.uuid, user_info, view_func, middlewares_used)

        # saves request's dump data
        self.process_dumps(sonar_request.uuid)

        # saves request's payload
        self.process_payload(sonar_request.uuid, get_payload, post_payload)

        # stores the queries
        self.process_queries(sonar_request.uuid, executed_queries)

        # saves request's headers
        self.process_headers(sonar_request.uuid, request_headers)

        # saves request's session
        self.process_session(sonar_request.uuid, session_data)

        # Reset the thread-local storage
        utils.reset_sonar_dump()

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

    def process_dumps(self, sonar_request_uuid):
        """Process the dumps and save them to the database."""
        sonar_dumps = utils.get_sonar_dump()
        for dump in sonar_dumps:
            SonarData.objects.create(
                sonar_request_id=sonar_request_uuid,
                category='dumps',
                data=dump
            )

    def process_details(self, sonar_request_uuid, user_info, view_func, middlewares_used):
        """Process the details and save them to the database."""
        details = {
            'user_info': user_info,
            'view_func': view_func,
            'middlewares_used': middlewares_used
        }
        SonarData.objects.create(
            sonar_request_id=sonar_request_uuid,
            category='details',
            data=details
        )

    def process_payload(self, sonar_request_uuid, get_payload, post_payload):
        """Process the payload and save them to the database."""
        payload = {
            'get_payload': get_payload,
            'post_payload': post_payload
        }
        SonarData.objects.create(
            sonar_request_id=sonar_request_uuid,
            category='payload',
            data=payload
        )

    def process_queries(self, sonar_request_uuid, executed_queries):
        """Process the queries and save them to the database."""
        queries = {
            'executed_queries': executed_queries
        }
        SonarData.objects.create(
            sonar_request_id=sonar_request_uuid,
            category='queries',
            data=queries
        )

    def process_headers(self, sonar_request_uuid, request_headers):
        """Process the headers and save them to the database."""
        headers = {
            'request_headers': request_headers
        }
        SonarData.objects.create(
            sonar_request_id=sonar_request_uuid,
            category='headers',
            data=headers
        )

    def process_session(self, sonar_request_uuid, session_data):
        """Process the session and save them to the database."""
        session = {
            'session_data': session_data
        }
        SonarData.objects.create(
            sonar_request_id=sonar_request_uuid,
            category='session',
            data=session
        )
