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
    def get_body_payload(request, capture_raw_body=False, raw_body_max_bytes=10_000):
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

        try:
            content_type = (request.content_type or '').lower()

            # Django parses standard POST forms and multipart uploads for us.
            if request.method == 'POST' and (
                'application/x-www-form-urlencoded' in content_type
                or 'multipart/form-data' in content_type
            ):
                return request.POST.dict()
            
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
                content_length = request.META.get('CONTENT_LENGTH')
                metadata = {'_content_type': content_type}
                if content_length:
                    try:
                        metadata['_body_size'] = int(content_length)
                    except (TypeError, ValueError):
                        pass

                if not capture_raw_body:
                    metadata['_raw_body_captured'] = False
                    return metadata

                if hasattr(request, 'body') and request.body:
                    raw_body = request.body
                    truncated = len(raw_body) > raw_body_max_bytes
                    body_str = raw_body[:raw_body_max_bytes].decode('utf-8', errors='replace')
                    if truncated:
                        body_str += '... (truncated)'
                    metadata['_raw_body'] = body_str
                    metadata['_raw_body_truncated'] = truncated
                return metadata
                
        except Exception as e:
            result = {
                '_parse_error': str(e),
                '_content_type': getattr(request, 'content_type', 'unknown'),
            }
            if not capture_raw_body:
                result['_raw_body_captured'] = False
                return result

            try:
                raw_body = request.body
                truncated = len(raw_body) > raw_body_max_bytes
                result['_raw_body'] = raw_body[:raw_body_max_bytes].decode(
                    'utf-8', errors='replace'
                )
                result['_raw_body_truncated'] = truncated
            except Exception:
                result['_raw_body'] = '<unable to decode>'
                result['_raw_body_truncated'] = False
            return result
