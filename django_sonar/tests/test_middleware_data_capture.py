"""
Tests for data capture functionality.

Tests middleware's ability to capture various request data including
headers, sessions, user info, IP addresses, memory usage, etc.
"""

from django.test import override_settings
from django.contrib.auth.models import AnonymousUser
from django_sonar.middlewares.requests import RequestsMiddleware
from django_sonar.models import SonarRequest, SonarData
from django_sonar import utils
from .base import BaseMiddlewareTestCase


class MiddlewareDataCaptureTestCase(BaseMiddlewareTestCase):
    """Test data capture functionality"""

    @override_settings(DJANGO_SONAR={'excludes': []})
    def test_middleware_captures_user_info(self):
        """Test middleware captures authenticated user information"""
        request = self.factory.get('/profile/')
        request = self._add_session_to_request(request)
        request.user = self.user
        
        middleware = RequestsMiddleware(self.get_response)
        response = middleware(request)
        
        # Verify user info in details
        sonar_request = SonarRequest.objects.first()
        details_data = SonarData.objects.get(
            sonar_request=sonar_request,
            category='details'
        )
        
        user_info = details_data.data['user_info']
        self.assertIsNotNone(user_info)
        self.assertEqual(user_info['user_id'], self.user.id)
        self.assertEqual(user_info['username'], 'testuser')
        self.assertEqual(user_info['email'], 'test@example.com')

    @override_settings(DJANGO_SONAR={'excludes': []})
    def test_middleware_anonymous_user(self):
        """Test middleware handles anonymous users"""
        request = self.factory.get('/public/')
        request = self._add_session_to_request(request)
        request.user = AnonymousUser()
        
        middleware = RequestsMiddleware(self.get_response)
        response = middleware(request)
        
        # Verify user_info is None for anonymous users
        sonar_request = SonarRequest.objects.first()
        details_data = SonarData.objects.get(
            sonar_request=sonar_request,
            category='details'
        )
        
        self.assertIsNone(details_data.data['user_info'])

    @override_settings(DJANGO_SONAR={'excludes': []})
    def test_middleware_captures_headers(self):
        """Test middleware captures request headers"""
        request = self.factory.get('/test/', HTTP_USER_AGENT='TestAgent/1.0')
        request = self._add_session_to_request(request)
        request.user = self.user
        
        middleware = RequestsMiddleware(self.get_response)
        response = middleware(request)
        
        # Verify headers
        sonar_request = SonarRequest.objects.first()
        headers_data = SonarData.objects.get(
            sonar_request=sonar_request,
            category='headers'
        )
        
        self.assertIn('request_headers', headers_data.data)
        self.assertIn('User-Agent', headers_data.data['request_headers'])

    @override_settings(DJANGO_SONAR={'excludes': []})
    def test_middleware_captures_session_data(self):
        """Test middleware captures session data"""
        request = self.factory.get('/test/')
        request = self._add_session_to_request(request)
        request.user = self.user
        request.session['test_key'] = 'test_value'
        request.session.save()
        
        middleware = RequestsMiddleware(self.get_response)
        response = middleware(request)
        
        # Verify session data
        sonar_request = SonarRequest.objects.first()
        session_data = SonarData.objects.get(
            sonar_request=sonar_request,
            category='session'
        )
        
        self.assertIn('session_data', session_data.data)
        self.assertEqual(session_data.data['session_data']['test_key'], 'test_value')

    @override_settings(DJANGO_SONAR={'excludes': []})
    def test_middleware_captures_ip_address(self):
        """Test middleware captures client IP address"""
        request = self.factory.get('/test/')
        request = self._add_session_to_request(request)
        request.user = self.user
        request.META['REMOTE_ADDR'] = '192.168.1.100'
        
        middleware = RequestsMiddleware(self.get_response)
        response = middleware(request)
        
        # Verify IP address
        sonar_request = SonarRequest.objects.first()
        self.assertEqual(sonar_request.ip_address, '192.168.1.100')

    @override_settings(DJANGO_SONAR={'excludes': []})
    def test_middleware_captures_forwarded_ip(self):
        """Test middleware captures X-Forwarded-For IP"""
        request = self.factory.get('/test/')
        request = self._add_session_to_request(request)
        request.user = self.user
        request.META['HTTP_X_FORWARDED_FOR'] = '10.0.0.1, 192.168.1.1'
        request.META['REMOTE_ADDR'] = '192.168.1.100'
        
        middleware = RequestsMiddleware(self.get_response)
        response = middleware(request)
        
        # Verify first IP from X-Forwarded-For is used
        sonar_request = SonarRequest.objects.first()
        self.assertEqual(sonar_request.ip_address, '10.0.0.1')

    @override_settings(DJANGO_SONAR={'excludes': []})
    def test_middleware_captures_memory_usage(self):
        """Test middleware captures memory usage"""
        request = self.factory.get('/test/')
        request = self._add_session_to_request(request)
        request.user = self.user
        
        middleware = RequestsMiddleware(self.get_response)
        response = middleware(request)
        
        # Verify memory usage is captured
        sonar_request = SonarRequest.objects.first()
        details_data = SonarData.objects.get(
            sonar_request=sonar_request,
            category='details'
        )
        
        self.assertIn('memory_used', details_data.data)
        self.assertIsInstance(details_data.data['memory_used'], (int, float))

    @override_settings(DJANGO_SONAR={'excludes': []})
    def test_middleware_captures_view_function(self):
        """Test middleware captures view function name"""
        request = self.factory.get('/test/')
        request = self._add_session_to_request(request)
        request.user = self.user
        
        middleware = RequestsMiddleware(self.get_response)
        response = middleware(request)
        
        # Verify view function is captured
        sonar_request = SonarRequest.objects.first()
        details_data = SonarData.objects.get(
            sonar_request=sonar_request,
            category='details'
        )
        
        self.assertIn('view_func', details_data.data)
        self.assertIsInstance(details_data.data['view_func'], str)

    @override_settings(DJANGO_SONAR={'excludes': []})
    def test_middleware_captures_middlewares_used(self):
        """Test middleware captures list of middlewares"""
        request = self.factory.get('/test/')
        request = self._add_session_to_request(request)
        request.user = self.user
        
        middleware = RequestsMiddleware(self.get_response)
        response = middleware(request)
        
        # Verify middlewares list is captured
        sonar_request = SonarRequest.objects.first()
        details_data = SonarData.objects.get(
            sonar_request=sonar_request,
            category='details'
        )
        
        self.assertIn('middlewares_used', details_data.data)
        self.assertIsInstance(details_data.data['middlewares_used'], (list, tuple))

    @override_settings(DJANGO_SONAR={'excludes': []})
    def test_middleware_sonar_dump_integration(self):
        """Test middleware captures sonar dumps"""
        request = self.factory.get('/test/')
        request = self._add_session_to_request(request)
        request.user = self.user
        
        # Add some dumps
        utils.sonar('test_value_1', {'key': 'value'})
        
        middleware = RequestsMiddleware(self.get_response)
        response = middleware(request)
        
        # Verify dumps were captured
        sonar_request = SonarRequest.objects.first()
        dumps_entries = SonarData.objects.filter(
            sonar_request=sonar_request,
            category='dumps'
        )
        
        self.assertEqual(dumps_entries.count(), 2)
        
        # Verify dumps were reset
        self.assertEqual(len(utils.get_sonar_dump()), 0)

    @override_settings(DJANGO_SONAR={'excludes': []})
    def test_middleware_exception_handling(self):
        """Test middleware captures exceptions via process_exception"""
        request = self.factory.get('/test/')
        request = self._add_session_to_request(request)
        request.user = self.user
        
        middleware = RequestsMiddleware(self.get_response)
        
        # Simulate an exception
        try:
            raise ValueError("Test error message")
        except ValueError as e:
            middleware.process_exception(request, e)
        
        # Process the request
        response = middleware(request)
        
        # Verify exception was captured
        sonar_request = SonarRequest.objects.first()
        exception_entries = SonarData.objects.filter(
            sonar_request=sonar_request,
            category='exception'
        )
        
        self.assertEqual(exception_entries.count(), 1)
        exception_data = exception_entries.first().data
        self.assertIn('exception_message', exception_data)
        self.assertEqual(exception_data['exception_message'], 'Test error message')

    @override_settings(DJANGO_SONAR={'excludes': []})
    def test_middleware_filters_sensitive_post_data(self):
        """Test middleware filters sensitive data in POST payloads"""
        request = self.factory.post('/login/', {
            'username': 'john',
            'password': 'secret123',
            'email': 'john@example.com'
        })
        request = self._add_session_to_request(request)
        request.user = self.user
        
        middleware = RequestsMiddleware(self.get_response)
        response = middleware(request)
        
        # Verify payload was captured with filtered password
        sonar_request = SonarRequest.objects.first()
        payload_data = SonarData.objects.get(
            sonar_request=sonar_request,
            category='payload'
        )
        
        post_payload = payload_data.data['post_payload']
        self.assertEqual(post_payload['username'], 'john')
        self.assertEqual(post_payload['password'], '***FILTERED***')
        self.assertEqual(post_payload['email'], 'john@example.com')

    @override_settings(DJANGO_SONAR={'excludes': []})
    def test_middleware_filters_sensitive_headers(self):
        """Test middleware filters sensitive data in headers"""
        request = self.factory.get('/api/data/', HTTP_AUTHORIZATION='Bearer secret_token_123')
        request = self._add_session_to_request(request)
        request.user = self.user
        
        middleware = RequestsMiddleware(self.get_response)
        response = middleware(request)
        
        # Verify headers were captured with filtered authorization
        sonar_request = SonarRequest.objects.first()
        headers_data = SonarData.objects.get(
            sonar_request=sonar_request,
            category='headers'
        )
        
        request_headers = headers_data.data['request_headers']
        self.assertEqual(request_headers['Authorization'], '***FILTERED***')

    @override_settings(DJANGO_SONAR={'excludes': []})
    def test_middleware_filters_sensitive_session_data(self):
        """Test middleware filters sensitive data in session"""
        request = self.factory.get('/test/')
        request = self._add_session_to_request(request)
        request.user = self.user
        request.session['user_id'] = 123
        request.session['api_token'] = 'secret_token_value'
        request.session['theme'] = 'dark'
        request.session.save()
        
        middleware = RequestsMiddleware(self.get_response)
        response = middleware(request)
        
        # Verify session data was captured with filtered sensitive fields
        sonar_request = SonarRequest.objects.first()
        session_data = SonarData.objects.get(
            sonar_request=sonar_request,
            category='session'
        )
        
        session = session_data.data['session_data']
        self.assertEqual(session['user_id'], 123)
        self.assertEqual(session['api_token'], '***FILTERED***')
        self.assertEqual(session['theme'], 'dark')

    @override_settings(DJANGO_SONAR={'excludes': []})
    def test_middleware_captures_query_count(self):
        """Test middleware captures query count in SonarRequest"""
        request = self.factory.get('/test/')
        request = self._add_session_to_request(request)
        request.user = self.user
        
        middleware = RequestsMiddleware(self.get_response)
        response = middleware(request)
        
        # Verify query_count field is set
        sonar_request = SonarRequest.objects.first()
        self.assertIsNotNone(sonar_request.query_count)
        self.assertIsInstance(sonar_request.query_count, int)
        self.assertGreaterEqual(sonar_request.query_count, 0)
        
        # Verify query_count also in queries data
        queries_data = SonarData.objects.get(
            sonar_request=sonar_request,
            category='queries'
        )
        self.assertIn('query_count', queries_data.data)
        self.assertEqual(
            queries_data.data['query_count'],
            len(queries_data.data['executed_queries'])
        )
