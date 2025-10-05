"""
Tests for middleware exception handling.

Tests the process_exception method of the middleware.
Note: Helper methods like is_ajax, get_client_ip, and get_body_payload
are now tested in test_core_parsers.py as they've been moved to RequestParser.
"""

import traceback
from django.test import override_settings
from django_sonar.middlewares.requests import RequestsMiddleware
from django_sonar import utils
from .base import BaseMiddlewareTestCase


class MiddlewareHelpersTestCase(BaseMiddlewareTestCase):
    """Test middleware helper methods"""

    @override_settings(DJANGO_SONAR={'excludes': []})
    def test_process_exception_stores_exception_info(self):
        """Test process_exception stores exception in thread local"""
        middleware = RequestsMiddleware(self.get_response)
        request = self.factory.get('/test/')
        
        # Reset exceptions
        utils.reset_sonar_exceptions()
        
        # Create and process an exception
        try:
            raise ValueError("Test exception message")
        except ValueError as e:
            middleware.process_exception(request, e)
        
        # Verify exception was stored
        exceptions = utils.get_sonar_exceptions()
        self.assertEqual(len(exceptions), 1)
        self.assertIn('exception_message', exceptions[0])
        self.assertEqual(exceptions[0]['exception_message'], 'Test exception message')

    @override_settings(DJANGO_SONAR={'excludes': []})
    def test_process_exception_captures_traceback(self):
        """Test process_exception captures traceback information"""
        middleware = RequestsMiddleware(self.get_response)
        request = self.factory.get('/test/')
        
        # Reset exceptions
        utils.reset_sonar_exceptions()
        
        # Create and process an exception with traceback
        try:
            def inner_function():
                raise RuntimeError("Inner error")
            inner_function()
        except RuntimeError as e:
            middleware.process_exception(request, e)
        
        # Verify exception details were captured
        exceptions = utils.get_sonar_exceptions()
        self.assertEqual(len(exceptions), 1)
        exc_data = exceptions[0]
        
        self.assertIn('file_name', exc_data)
        self.assertIn('line_number', exc_data)
        self.assertIn('function_name', exc_data)
        self.assertEqual(exc_data['function_name'], 'inner_function')
        self.assertEqual(exc_data['exception_message'], 'Inner error')
