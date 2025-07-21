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
        # Check if the request path is excluded
        if self._should_exclude(request.path):
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
        post_payload = self.get_body_payload(request)

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

    def get_body_payload(self, request):
        """Get request body data for all HTTP methods (POST, PUT, PATCH, etc.)"""
        if request.method == 'GET':
            return {}
        
        # For POST requests, use the standard request.POST
        if request.method == 'POST':
            return request.POST.copy()
        
        # For PUT, PATCH, and other methods, parse the request body
        try:
            content_type = request.content_type.lower()
            
            # Handle JSON content
            if 'application/json' in content_type:
                if hasattr(request, 'body') and request.body:
                    return json.loads(request.body.decode('utf-8'))
                return {}
            
            # Handle form-encoded content
            elif 'application/x-www-form-urlencoded' in content_type:
                if hasattr(request, 'body') and request.body:
                    parsed_data = parse_qs(request.body.decode('utf-8'))
                    # Convert lists to single values for consistency with request.POST
                    return {k: v[0] if len(v) == 1 else v for k, v in parsed_data.items()}
                return {}
            
            # Handle multipart form data (files)
            elif 'multipart/form-data' in content_type:
                # For multipart, try to get data from request.FILES and any parsed data
                data = {}
                if hasattr(request, 'FILES') and request.FILES:
                    data['_files'] = list(request.FILES.keys())
                # Note: Django doesn't populate request.POST for PUT/PATCH multipart,
                # so we'd need custom parsing for complex multipart PUT/PATCH requests
                return data
            
            # For other content types, store raw body (truncated for safety)
            else:
                if hasattr(request, 'body') and request.body:
                    body_str = request.body.decode('utf-8', errors='ignore')
                    # Truncate large bodies to avoid storage issues
                    if len(body_str) > 10000:
                        body_str = body_str[:10000] + '... (truncated)'
                    return {'_raw_body': body_str, '_content_type': content_type}
                return {}
                
        except (json.JSONDecodeError, UnicodeDecodeError, Exception) as e:
            # If parsing fails, store error info and raw body (truncated)
            try:
                body_str = request.body.decode('utf-8', errors='ignore')[:1000]
            except:
                body_str = '<unable to decode>'
            
            return {
                '_parse_error': str(e),
                '_raw_body': body_str,
                '_content_type': getattr(request, 'content_type', 'unknown')
            }

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
        
    def _compile_excludes(self):
        """
        Compile the excludes list provided in the settings.

        :return: a list of tuples (pattern_type, pattern) where pattern_type is one of
            'regex' or 'literal' and pattern is a compiled regex pattern or a string
        """
        excluded_paths = settings.DJANGO_SONAR.get('excludes', [])
        compiled = []
        
        for pattern in excluded_paths:
            if isinstance(pattern, str) and pattern.startswith('r'):
                try:
                    regex_pattern = pattern[1:]
                    compiled.append(('regex', re.compile(regex_pattern)))
                except re.error:
                    compiled.append(('literal', pattern))
            else:
                compiled.append(('literal', pattern))
        
        return compiled

    def _should_exclude(self, path):
        """
        Check if the path should be excluded based on the excludes list provided in the settings.

        :param path: the path to check
        :return: whether the path should be excluded
        """
        for pattern_type, pattern in self.compiled_excludes:
            if pattern_type == 'regex':
                if pattern.match(path):
                    return True
            else:  # literal
                if path.startswith(pattern):
                    return True
        return False
