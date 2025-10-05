"""
Path filtering utilities.

Handles exclusion of specific paths from monitoring based on:
- Literal string matching (e.g., '/admin/')
- Regex patterns (e.g., 'r^/api/v[0-9]+/')

Sensitive data filtering utilities.

Handles masking of sensitive data in payloads, headers, and session data.
"""

import re
from django.conf import settings


class PathFilter:
    """Handles path exclusion logic for the middleware"""

    def __init__(self):
        """Initialize filter by compiling exclusion patterns from settings"""
        self.compiled_excludes = self._compile_excludes()

    def _compile_excludes(self):
        """
        Compile the excludes list provided in the settings.
        
        Patterns starting with 'r' are treated as regex patterns,
        all others are treated as literal strings for startswith matching.
        
        :return: List of tuples (pattern_type, pattern) where pattern_type 
                 is 'regex' or 'literal'
        """
        excluded_paths = settings.DJANGO_SONAR.get('excludes', [])
        compiled = []
        
        for pattern in excluded_paths:
            if isinstance(pattern, str) and pattern.startswith('r'):
                try:
                    regex_pattern = pattern[1:]
                    compiled.append(('regex', re.compile(regex_pattern)))
                except re.error:
                    # If regex compilation fails, treat as literal
                    compiled.append(('literal', pattern))
            else:
                compiled.append(('literal', pattern))
        
        return compiled

    def should_exclude(self, path):
        """
        Check if the path should be excluded based on configured patterns.
        
        :param path: Request path to check
        :return: True if path should be excluded, False otherwise
        """
        for pattern_type, pattern in self.compiled_excludes:
            if pattern_type == 'regex':
                if pattern.match(path):
                    return True
            else:  # literal
                if path.startswith(pattern):
                    return True
        return False


class SensitiveDataFilter:
    """Handles sensitive data masking in request data"""
    
    # Default sensitive field patterns (case-insensitive)
    DEFAULT_SENSITIVE_FIELDS = [
        'password',
        'passwd', 
        'pwd',
        'pass',
        'secret',
        'api_key',
        'apikey',
        'api_secret',
        'token',
        'access_token',
        'refresh_token',
        'auth',
        'authorization',
        'credit_card',
        'card_number',
        'cvv',
        'cvc',
        'ssn',
        'pin',
        'session_id',
        'csrf',
        'private_key',
    ]
    
    MASK_VALUE = '***FILTERED***'
    
    def __init__(self):
        """Initialize filter with configured sensitive fields"""
        sonar_settings = getattr(settings, 'DJANGO_SONAR', {})
        custom_fields = sonar_settings.get('sensitive_fields', [])
        
        # Combine default and custom fields, convert to lowercase for case-insensitive matching
        self.sensitive_fields = set(
            field.lower() for field in (self.DEFAULT_SENSITIVE_FIELDS + custom_fields)
        )
    
    def _is_sensitive_key(self, key):
        """
        Check if a key represents sensitive data.
        
        :param key: Field name to check
        :return: True if key is sensitive, False otherwise
        """
        if not isinstance(key, str):
            return False
            
        key_lower = key.lower()
        
        # Check for exact matches
        if key_lower in self.sensitive_fields:
            return True
        
        # Check if any sensitive field is contained in the key
        for sensitive_field in self.sensitive_fields:
            if sensitive_field in key_lower:
                return True
        
        return False
    
    def filter_dict(self, data):
        """
        Recursively filter sensitive data from a dictionary.
        
        :param data: Dictionary to filter
        :return: Filtered dictionary with sensitive values masked
        """
        if not isinstance(data, dict):
            return data
        
        filtered = {}
        for key, value in data.items():
            if self._is_sensitive_key(key):
                filtered[key] = self.MASK_VALUE
            elif isinstance(value, dict):
                filtered[key] = self.filter_dict(value)
            elif isinstance(value, (list, tuple)):
                filtered[key] = self._filter_list(value)
            else:
                filtered[key] = value
        
        return filtered
    
    def _filter_list(self, data):
        """
        Filter sensitive data from a list/tuple.
        
        :param data: List or tuple to filter
        :return: Filtered list with sensitive values masked
        """
        filtered = []
        for item in data:
            if isinstance(item, dict):
                filtered.append(self.filter_dict(item))
            elif isinstance(item, (list, tuple)):
                filtered.append(self._filter_list(item))
            else:
                filtered.append(item)
        
        return filtered if isinstance(data, list) else tuple(filtered)
