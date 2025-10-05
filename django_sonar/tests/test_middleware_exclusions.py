"""
Tests for path exclusion functionality.

Tests middleware's ability to exclude certain paths from monitoring
using both literal and regex patterns.
"""

from django.test import override_settings
from django_sonar.middlewares.requests import RequestsMiddleware
from django_sonar.models import SonarRequest
from .base import BaseMiddlewareTestCase


class MiddlewareExclusionsTestCase(BaseMiddlewareTestCase):
    """Test path exclusion functionality"""

    @override_settings(DJANGO_SONAR={'excludes': ['/admin/', '/static/']})
    def test_middleware_excludes_paths_literal(self):
        """Test middleware excludes paths based on literal patterns"""
        # Test excluded path
        request = self.factory.get('/admin/users/')
        request = self._add_session_to_request(request)
        request.user = self.user
        
        middleware = RequestsMiddleware(self.get_response)
        response = middleware(request)
        
        # Verify no SonarRequest was created
        self.assertEqual(SonarRequest.objects.count(), 0)
        
        # Test non-excluded path
        request = self.factory.get('/api/data/')
        request = self._add_session_to_request(request)
        request.user = self.user
        
        response = middleware(request)
        
        # Verify SonarRequest was created
        self.assertEqual(SonarRequest.objects.count(), 1)

    @override_settings(DJANGO_SONAR={'excludes': ['r^/api/v[0-9]+/']})
    def test_middleware_excludes_paths_regex(self):
        """Test middleware excludes paths based on regex patterns"""
        middleware = RequestsMiddleware(self.get_response)
        
        # Test excluded paths matching regex
        for path in ['/api/v1/users/', '/api/v2/posts/', '/api/v99/data/']:
            request = self.factory.get(path)
            request = self._add_session_to_request(request)
            request.user = self.user
            
            response = middleware(request)
        
        # Verify no SonarRequest was created
        self.assertEqual(SonarRequest.objects.count(), 0)
        
        # Test non-excluded path
        request = self.factory.get('/api/users/')
        request = self._add_session_to_request(request)
        request.user = self.user
        
        response = middleware(request)
        
        # Verify SonarRequest was created
        self.assertEqual(SonarRequest.objects.count(), 1)

    @override_settings(DJANGO_SONAR={'excludes': ['/health/', 'r^/metrics']})
    def test_middleware_excludes_mixed_patterns(self):
        """Test middleware handles mixed literal and regex patterns"""
        middleware = RequestsMiddleware(self.get_response)
        
        # Test literal exclusion
        request = self.factory.get('/health/check/')
        request = self._add_session_to_request(request)
        request.user = self.user
        response = middleware(request)
        
        self.assertEqual(SonarRequest.objects.count(), 0)
        
        # Test regex exclusion
        request = self.factory.get('/metrics/performance/')
        request = self._add_session_to_request(request)
        request.user = self.user
        response = middleware(request)
        
        self.assertEqual(SonarRequest.objects.count(), 0)
        
        # Test non-excluded path
        request = self.factory.get('/api/data/')
        request = self._add_session_to_request(request)
        request.user = self.user
        response = middleware(request)
        
        self.assertEqual(SonarRequest.objects.count(), 1)

    @override_settings(DJANGO_SONAR={'excludes': []})
    def test_middleware_no_exclusions(self):
        """Test middleware with empty exclusions list"""
        middleware = RequestsMiddleware(self.get_response)
        
        # All paths should be captured
        paths = ['/admin/', '/static/', '/api/', '/health/']
        for path in paths:
            request = self.factory.get(path)
            request = self._add_session_to_request(request)
            request.user = self.user
            response = middleware(request)
        
        # Verify all requests were captured
        self.assertEqual(SonarRequest.objects.count(), len(paths))
