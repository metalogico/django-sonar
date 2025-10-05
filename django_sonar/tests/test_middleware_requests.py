"""
Tests for different HTTP request types and methods.

Covers GET, POST, PUT, PATCH, DELETE requests with various
content types and payloads.
"""

import json
from unittest.mock import Mock
from django.test import override_settings
from django.http import HttpResponse
from django_sonar.middlewares.requests import RequestsMiddleware
from django_sonar.models import SonarRequest, SonarData
from .base import BaseMiddlewareTestCase


class MiddlewareRequestTypesTestCase(BaseMiddlewareTestCase):
    """Test different HTTP request types"""

    @override_settings(DJANGO_SONAR={'excludes': []})
    def test_middleware_post_request_with_data(self):
        """Test middleware captures POST request with data"""
        post_data = {'username': 'testuser', 'email': 'test@example.com'}
        request = self.factory.post('/submit/', data=post_data)
        request = self._add_session_to_request(request)
        request.user = self.user
        
        middleware = RequestsMiddleware(self.get_response)
        response = middleware(request)
        
        # Verify SonarRequest
        sonar_request = SonarRequest.objects.first()
        self.assertEqual(sonar_request.verb, 'POST')
        
        # Verify payload was captured
        payload_data = SonarData.objects.get(
            sonar_request=sonar_request,
            category='payload'
        )
        self.assertIn('post_payload', payload_data.data)
        self.assertEqual(payload_data.data['post_payload']['username'], 'testuser')

    @override_settings(DJANGO_SONAR={'excludes': []})
    def test_middleware_get_request_with_query_string(self):
        """Test middleware captures GET request with query parameters"""
        request = self.factory.get('/search/?q=test&page=1')
        request = self._add_session_to_request(request)
        request.user = self.user
        
        middleware = RequestsMiddleware(self.get_response)
        response = middleware(request)
        
        # Verify full URL includes query string
        sonar_request = SonarRequest.objects.first()
        self.assertIn('q=test', sonar_request.path)
        self.assertIn('page=1', sonar_request.path)
        
        # Verify GET payload
        payload_data = SonarData.objects.get(
            sonar_request=sonar_request,
            category='payload'
        )
        self.assertEqual(payload_data.data['get_payload']['q'], 'test')
        self.assertEqual(payload_data.data['get_payload']['page'], '1')

    @override_settings(DJANGO_SONAR={'excludes': []})
    def test_middleware_put_request_json(self):
        """Test middleware captures PUT request with JSON body"""
        json_data = {'name': 'Updated Name', 'value': 42}
        request = self.factory.put(
            '/api/resource/1/',
            data=json.dumps(json_data),
            content_type='application/json'
        )
        request = self._add_session_to_request(request)
        request.user = self.user
        
        middleware = RequestsMiddleware(self.get_response)
        response = middleware(request)
        
        # Verify request was captured
        sonar_request = SonarRequest.objects.first()
        self.assertEqual(sonar_request.verb, 'PUT')
        
        # Verify JSON payload was parsed
        payload_data = SonarData.objects.get(
            sonar_request=sonar_request,
            category='payload'
        )
        self.assertEqual(payload_data.data['post_payload']['name'], 'Updated Name')
        self.assertEqual(payload_data.data['post_payload']['value'], 42)

    @override_settings(DJANGO_SONAR={'excludes': []})
    def test_middleware_patch_request_form_encoded(self):
        """Test middleware captures PATCH request with form-encoded body"""
        form_data = 'field1=value1&field2=value2'
        request = self.factory.patch(
            '/api/resource/1/',
            data=form_data,
            content_type='application/x-www-form-urlencoded'
        )
        request = self._add_session_to_request(request)
        request.user = self.user
        
        middleware = RequestsMiddleware(self.get_response)
        response = middleware(request)
        
        # Verify request was captured
        sonar_request = SonarRequest.objects.first()
        self.assertEqual(sonar_request.verb, 'PATCH')
        
        # Verify form data was parsed
        payload_data = SonarData.objects.get(
            sonar_request=sonar_request,
            category='payload'
        )
        self.assertEqual(payload_data.data['post_payload']['field1'], 'value1')
        self.assertEqual(payload_data.data['post_payload']['field2'], 'value2')

    @override_settings(DJANGO_SONAR={'excludes': []})
    def test_middleware_delete_request(self):
        """Test middleware captures DELETE request"""
        request = self.factory.delete('/api/resource/1/')
        request = self._add_session_to_request(request)
        request.user = self.user
        
        middleware = RequestsMiddleware(self.get_response)
        response = middleware(request)
        
        # Verify request was captured
        sonar_request = SonarRequest.objects.first()
        self.assertEqual(sonar_request.verb, 'DELETE')

    @override_settings(DJANGO_SONAR={'excludes': []})
    def test_middleware_ajax_request(self):
        """Test middleware detects AJAX requests"""
        request = self.factory.get('/api/data/')
        request = self._add_session_to_request(request)
        request.user = self.user
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        
        middleware = RequestsMiddleware(self.get_response)
        response = middleware(request)
        
        # Verify AJAX flag
        sonar_request = SonarRequest.objects.first()
        self.assertTrue(sonar_request.is_ajax)

    @override_settings(DJANGO_SONAR={'excludes': []})
    def test_middleware_invalid_json_body(self):
        """Test middleware handles invalid JSON gracefully"""
        invalid_json = '{invalid json'
        request = self.factory.put(
            '/api/resource/1/',
            data=invalid_json,
            content_type='application/json'
        )
        request = self._add_session_to_request(request)
        request.user = self.user
        
        middleware = RequestsMiddleware(self.get_response)
        response = middleware(request)
        
        # Verify request was still captured
        sonar_request = SonarRequest.objects.first()
        self.assertIsNotNone(sonar_request)
        
        # Verify error info was stored
        payload_data = SonarData.objects.get(
            sonar_request=sonar_request,
            category='payload'
        )
        self.assertIn('_parse_error', payload_data.data['post_payload'])

    @override_settings(DJANGO_SONAR={'excludes': []})
    def test_middleware_different_status_codes(self):
        """Test middleware captures different HTTP status codes"""
        status_codes = [200, 201, 400, 404, 500]
        
        for status_code in status_codes:
            # Create new middleware with mock response
            get_response = Mock(return_value=HttpResponse('Response', status=status_code))
            middleware = RequestsMiddleware(get_response)
            
            request = self.factory.get(f'/test-{status_code}/')
            request = self._add_session_to_request(request)
            request.user = self.user
            
            response = middleware(request)
            
            # Verify status code was captured
            sonar_request = SonarRequest.objects.filter(
                path=f'/test-{status_code}/'
            ).first()
            self.assertEqual(sonar_request.status, str(status_code))

    @override_settings(DJANGO_SONAR={'excludes': []})
    def test_post_request_with_form_data(self):
        """Test middleware captures POST request with standard form data"""
        # Simple POST request with form data (not multipart)
        request = self.factory.post('/upload/', data={'field': 'value', 'name': 'test'})
        request = self._add_session_to_request(request)
        request.user = self.user
        
        middleware = RequestsMiddleware(self.get_response)
        response = middleware(request)
        
        # Verify request was captured
        sonar_request = SonarRequest.objects.first()
        self.assertEqual(sonar_request.verb, 'POST')
        
        payload_data = SonarData.objects.get(
            sonar_request=sonar_request,
            category='payload'
        )
        
        # Verify POST data was captured
        self.assertIsNotNone(payload_data.data['post_payload'])
        self.assertEqual(payload_data.data['post_payload']['field'], 'value')
        self.assertEqual(payload_data.data['post_payload']['name'], 'test')
