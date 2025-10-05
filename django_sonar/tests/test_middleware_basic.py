"""
Basic middleware functionality tests.

Tests core middleware behavior including request processing,
response handling, and basic data capture.
"""

from django.test import override_settings
from django_sonar.middlewares.requests import RequestsMiddleware
from django_sonar.models import SonarRequest, SonarData
from .base import BaseMiddlewareTestCase


class MiddlewareBasicTestCase(BaseMiddlewareTestCase):
    """Test basic middleware functionality"""

    @override_settings(DJANGO_SONAR={'excludes': []})
    def test_middleware_basic_get_request(self):
        """Test middleware captures basic GET request"""
        request = self.factory.get('/test-path/')
        request = self._add_session_to_request(request)
        request.user = self.user
        
        middleware = RequestsMiddleware(self.get_response)
        response = middleware(request)
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        
        # Verify SonarRequest was created
        sonar_request = SonarRequest.objects.first()
        self.assertIsNotNone(sonar_request)
        self.assertEqual(sonar_request.verb, 'GET')
        self.assertEqual(sonar_request.path, '/test-path/')
        self.assertEqual(sonar_request.status, '200')
        self.assertFalse(sonar_request.is_ajax)
        
        # Verify SonarData entries were created
        sonar_data_entries = SonarData.objects.filter(sonar_request=sonar_request)
        categories = [entry.category for entry in sonar_data_entries]
        
        self.assertIn('details', categories)
        self.assertIn('payload', categories)
        self.assertIn('queries', categories)
        self.assertIn('headers', categories)
        self.assertIn('session', categories)

    @override_settings(DJANGO_SONAR={'excludes': []})
    def test_middleware_captures_duration(self):
        """Test middleware captures request duration"""
        request = self.factory.get('/test/')
        request = self._add_session_to_request(request)
        request.user = self.user
        
        middleware = RequestsMiddleware(self.get_response)
        response = middleware(request)
        
        # Verify duration is captured and is a non-negative number
        sonar_request = SonarRequest.objects.first()
        self.assertIsNotNone(sonar_request.duration)
        self.assertGreaterEqual(sonar_request.duration, 0)

    @override_settings(DJANGO_SONAR={'excludes': []})
    def test_middleware_hostname_capture(self):
        """Test middleware captures hostname"""
        request = self.factory.get('/test/')
        request = self._add_session_to_request(request)
        request.user = self.user
        
        middleware = RequestsMiddleware(self.get_response)
        response = middleware(request)
        
        # Verify hostname is captured
        sonar_request = SonarRequest.objects.first()
        self.assertIsNotNone(sonar_request.hostname)
        self.assertIsInstance(sonar_request.hostname, str)

    @override_settings(DJANGO_SONAR={'excludes': []})
    def test_sonar_request_uuid_persistence(self):
        """Test sonar_request_uuid is properly set and used"""
        request = self.factory.get('/test/')
        request = self._add_session_to_request(request)
        request.user = self.user
        
        middleware = RequestsMiddleware(self.get_response)
        response = middleware(request)
        
        # Verify UUID was set
        self.assertIsNotNone(middleware.sonar_request_uuid)
        
        # Verify all SonarData entries reference the same UUID
        sonar_request = SonarRequest.objects.first()
        sonar_data_entries = SonarData.objects.filter(sonar_request=sonar_request)
        
        for entry in sonar_data_entries:
            self.assertEqual(entry.sonar_request_id, sonar_request.uuid)
