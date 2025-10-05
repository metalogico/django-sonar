"""
Tests for core.filters module.

Tests PathFilter class functionality for path exclusion.
Tests SensitiveDataFilter class functionality for masking sensitive data.
"""

from django.test import override_settings
from django_sonar.core.filters import PathFilter, SensitiveDataFilter
from .base import BaseMiddlewareTestCase


class PathFilterTestCase(BaseMiddlewareTestCase):
    """Test PathFilter functionality"""

    @override_settings(DJANGO_SONAR={'excludes': ['/admin/', '/static/']})
    def test_should_exclude_literal_match(self):
        """Test should_exclude with literal patterns"""
        path_filter = PathFilter()
        
        # Should exclude
        self.assertTrue(path_filter.should_exclude('/admin/users/'))
        self.assertTrue(path_filter.should_exclude('/static/css/style.css'))
        
        # Should not exclude
        self.assertFalse(path_filter.should_exclude('/api/users/'))
        self.assertFalse(path_filter.should_exclude('/home/'))

    @override_settings(DJANGO_SONAR={'excludes': ['r^/api/v[0-9]+/']})
    def test_should_exclude_regex_match(self):
        """Test should_exclude with regex patterns"""
        path_filter = PathFilter()
        
        # Should exclude
        self.assertTrue(path_filter.should_exclude('/api/v1/users/'))
        self.assertTrue(path_filter.should_exclude('/api/v2/posts/'))
        self.assertTrue(path_filter.should_exclude('/api/v99/data/'))
        
        # Should not exclude
        self.assertFalse(path_filter.should_exclude('/api/users/'))
        self.assertFalse(path_filter.should_exclude('/api/vX/data/'))

    @override_settings(DJANGO_SONAR={'excludes': ['/health/', 'r^/metrics']})
    def test_should_exclude_mixed_patterns(self):
        """Test should_exclude with mixed literal and regex patterns"""
        path_filter = PathFilter()
        
        # Literal exclusion
        self.assertTrue(path_filter.should_exclude('/health/check/'))
        
        # Regex exclusion
        self.assertTrue(path_filter.should_exclude('/metrics/performance/'))
        self.assertTrue(path_filter.should_exclude('/metrics'))
        
        # Not excluded
        self.assertFalse(path_filter.should_exclude('/api/data/'))

    @override_settings(DJANGO_SONAR={'excludes': []})
    def test_should_exclude_empty_list(self):
        """Test should_exclude with no exclusions"""
        path_filter = PathFilter()
        
        # Nothing should be excluded
        self.assertFalse(path_filter.should_exclude('/admin/'))
        self.assertFalse(path_filter.should_exclude('/static/'))
        self.assertFalse(path_filter.should_exclude('/any/path/'))

    @override_settings(DJANGO_SONAR={'excludes': ['r[invalid(regex']})
    def test_should_exclude_invalid_regex_fallback_to_literal(self):
        """Test should_exclude treats invalid regex as literal"""
        path_filter = PathFilter()
        
        # Invalid regex should be treated as literal string
        self.assertTrue(path_filter.should_exclude('r[invalid(regex/path/'))
        self.assertFalse(path_filter.should_exclude('/some/path/'))


class SensitiveDataFilterTestCase(BaseMiddlewareTestCase):
    """Test SensitiveDataFilter functionality"""

    def test_filter_simple_password_field(self):
        """Test filtering of password field"""
        sensitive_filter = SensitiveDataFilter()
        
        data = {
            'username': 'john',
            'password': 'secret123',
            'email': 'john@example.com'
        }
        
        filtered = sensitive_filter.filter_dict(data)
        
        self.assertEqual(filtered['username'], 'john')
        self.assertEqual(filtered['password'], '***FILTERED***')
        self.assertEqual(filtered['email'], 'john@example.com')

    def test_filter_multiple_sensitive_fields(self):
        """Test filtering of multiple sensitive fields"""
        sensitive_filter = SensitiveDataFilter()
        
        data = {
            'user': 'admin',
            'password': 'pass123',
            'api_key': 'abc123xyz',
            'token': 'bearer_token_here',
            'credit_card': '1234-5678-9012-3456'
        }
        
        filtered = sensitive_filter.filter_dict(data)
        
        self.assertEqual(filtered['user'], 'admin')
        self.assertEqual(filtered['password'], '***FILTERED***')
        self.assertEqual(filtered['api_key'], '***FILTERED***')
        self.assertEqual(filtered['token'], '***FILTERED***')
        self.assertEqual(filtered['credit_card'], '***FILTERED***')

    def test_filter_case_insensitive(self):
        """Test case-insensitive filtering"""
        sensitive_filter = SensitiveDataFilter()
        
        data = {
            'Password': 'secret',
            'API_KEY': 'key123',
            'Authorization': 'Bearer xyz',
            'normal_field': 'value'
        }
        
        filtered = sensitive_filter.filter_dict(data)
        
        self.assertEqual(filtered['Password'], '***FILTERED***')
        self.assertEqual(filtered['API_KEY'], '***FILTERED***')
        self.assertEqual(filtered['Authorization'], '***FILTERED***')
        self.assertEqual(filtered['normal_field'], 'value')

    def test_filter_nested_dict(self):
        """Test filtering in nested dictionaries"""
        sensitive_filter = SensitiveDataFilter()
        
        data = {
            'user': {
                'name': 'John',
                'password': 'secret',
                'preferences': {
                    'theme': 'dark',
                    'api_token': 'token123'
                }
            },
            'public_data': 'visible'
        }
        
        filtered = sensitive_filter.filter_dict(data)
        
        self.assertEqual(filtered['user']['name'], 'John')
        self.assertEqual(filtered['user']['password'], '***FILTERED***')
        self.assertEqual(filtered['user']['preferences']['theme'], 'dark')
        self.assertEqual(filtered['user']['preferences']['api_token'], '***FILTERED***')
        self.assertEqual(filtered['public_data'], 'visible')

    def test_filter_list_of_dicts(self):
        """Test filtering in list of dictionaries"""
        sensitive_filter = SensitiveDataFilter()
        
        data = {
            'users': [
                {'name': 'John', 'password': 'secret1'},
                {'name': 'Jane', 'password': 'secret2'}
            ]
        }
        
        filtered = sensitive_filter.filter_dict(data)
        
        self.assertEqual(filtered['users'][0]['name'], 'John')
        self.assertEqual(filtered['users'][0]['password'], '***FILTERED***')
        self.assertEqual(filtered['users'][1]['name'], 'Jane')
        self.assertEqual(filtered['users'][1]['password'], '***FILTERED***')

    def test_filter_partial_key_match(self):
        """Test filtering fields containing sensitive keywords"""
        sensitive_filter = SensitiveDataFilter()
        
        data = {
            'user_password': 'secret',
            'my_api_key': 'key123',
            'current_token': 'token456',
            'username': 'john'
        }
        
        filtered = sensitive_filter.filter_dict(data)
        
        self.assertEqual(filtered['user_password'], '***FILTERED***')
        self.assertEqual(filtered['my_api_key'], '***FILTERED***')
        self.assertEqual(filtered['current_token'], '***FILTERED***')
        self.assertEqual(filtered['username'], 'john')

    @override_settings(DJANGO_SONAR={'sensitive_fields': ['custom_secret', 'internal_key']})
    def test_filter_custom_sensitive_fields(self):
        """Test filtering with custom sensitive fields from settings"""
        sensitive_filter = SensitiveDataFilter()
        
        data = {
            'custom_secret': 'my_secret',
            'internal_key': 'internal_value',
            'public_field': 'public_value',
            'password': 'still_filtered'  # Default should still work
        }
        
        filtered = sensitive_filter.filter_dict(data)
        
        self.assertEqual(filtered['custom_secret'], '***FILTERED***')
        self.assertEqual(filtered['internal_key'], '***FILTERED***')
        self.assertEqual(filtered['public_field'], 'public_value')
        self.assertEqual(filtered['password'], '***FILTERED***')

    def test_filter_empty_dict(self):
        """Test filtering empty dictionary"""
        sensitive_filter = SensitiveDataFilter()
        
        data = {}
        filtered = sensitive_filter.filter_dict(data)
        
        self.assertEqual(filtered, {})

    def test_filter_non_dict_returns_unchanged(self):
        """Test that non-dict values are returned unchanged"""
        sensitive_filter = SensitiveDataFilter()
        
        self.assertEqual(sensitive_filter.filter_dict("string"), "string")
        self.assertEqual(sensitive_filter.filter_dict(123), 123)
        self.assertEqual(sensitive_filter.filter_dict(None), None)
