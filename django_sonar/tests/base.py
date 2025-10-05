"""
Base test case with common setup and utilities for all test modules.
"""

from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse
from django_sonar import utils


class BaseMiddlewareTestCase(TestCase):
    """Base test case with common setup for middleware tests"""

    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Mock get_response callable
        self.get_response = Mock(return_value=HttpResponse('OK', status=200))
        
        # Reset thread locals
        utils.reset_sonar_dump()
        utils.reset_sonar_exceptions()
        
        # Mock resolve to avoid URL routing issues in tests
        self.mock_resolve_patcher = patch('django_sonar.middlewares.requests.resolve')
        self.mock_resolve = self.mock_resolve_patcher.start()
        
        # Configure mock resolve to return a valid resolved match
        mock_func = MagicMock()
        mock_func.__module__ = 'test.views'
        mock_func.__name__ = 'test_view'
        
        mock_resolved = MagicMock()
        mock_resolved.func = mock_func
        
        self.mock_resolve.return_value = mock_resolved

    def tearDown(self):
        """Clean up after tests"""
        self.mock_resolve_patcher.stop()

    def _add_session_to_request(self, request):
        """Helper to add session to request"""
        middleware = SessionMiddleware(self.get_response)
        middleware.process_request(request)
        request.session.save()
        return request
