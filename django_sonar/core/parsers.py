"""
Request parsing utilities.

Handles extraction and parsing of request data including:
- Client IP addresses
- AJAX detection
- Request body payloads (JSON, form-encoded, etc.)
"""

import json
from urllib.parse import parse_qs


class RequestParser:
    """Utility class for parsing HTTP request data"""

    @staticmethod
    def get_client_ip(request):
        """
        Get the client IP address from the request object.
        
        Prioritizes X-Forwarded-For header for proxied requests.
        
        :param request: Django request object
        :return: Client IP address as string
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    @staticmethod
    def is_ajax(request):
        """
        Check if the request is an AJAX request.
        
        :param request: Django request object
        :return: True if AJAX request, False otherwise
        """
        return request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    @staticmethod
    def get_body_payload(request):
        """
        Get request body data for all HTTP methods (POST, PUT, PATCH, etc.)
        
        Handles different content types:
        - application/json
        - application/x-www-form-urlencoded
        - multipart/form-data
        
        :param request: Django request object
        :return: Dictionary with parsed body data
        """
        if request.method == 'GET':
            return {}
        
        # For POST requests, use the standard request.POST
        if request.method == 'POST':
            return request.POST.dict()
        
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
