"""
Tests for core.parsers module.

Tests RequestParser class functionality for parsing request data.
"""

from unittest.mock import Mock
from django.test import override_settings
from django_sonar.core.parsers import RequestParser
from .base import BaseMiddlewareTestCase


class RequestParserTestCase(BaseMiddlewareTestCase):
    """Test RequestParser functionality"""

    def test_get_client_ip_with_x_forwarded_for(self):
        """Test get_client_ip with X-Forwarded-For header"""
        request = self.factory.get('/test/')
        request.META['HTTP_X_FORWARDED_FOR'] = '10.0.0.1, 192.168.1.1'
        request.META['REMOTE_ADDR'] = '192.168.1.100'
        
        ip = RequestParser.get_client_ip(request)
        self.assertEqual(ip, '10.0.0.1')

    def test_get_client_ip_with_remote_addr_only(self):
        """Test get_client_ip with only REMOTE_ADDR"""
        request = self.factory.get('/test/')
        request.META['REMOTE_ADDR'] = '192.168.1.100'
        
        ip = RequestParser.get_client_ip(request)
        self.assertEqual(ip, '192.168.1.100')

    def test_is_ajax_true(self):
        """Test is_ajax returns True for AJAX requests"""
        request = self.factory.get('/test/')
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        
        self.assertTrue(RequestParser.is_ajax(request))

    def test_is_ajax_false(self):
        """Test is_ajax returns False for non-AJAX requests"""
        request = self.factory.get('/test/')
        
        self.assertFalse(RequestParser.is_ajax(request))

    def test_get_body_payload_get_request(self):
        """Test get_body_payload returns empty dict for GET"""
        request = self.factory.get('/test/')
        
        result = RequestParser.get_body_payload(request)
        self.assertEqual(result, {})

    def test_get_body_payload_post_request(self):
        """Test get_body_payload handles POST data"""
        request = self.factory.post('/test/', data={'key': 'value', 'name': 'test'})
        
        result = RequestParser.get_body_payload(request)
        self.assertIn('key', result)
        self.assertEqual(result['key'], 'value')
        self.assertEqual(result['name'], 'test')

    def test_get_body_payload_json(self):
        """Test get_body_payload parses JSON data"""
        import json
        
        json_data = {'name': 'test', 'value': 42}
        request = self.factory.put(
            '/test/',
            data=json.dumps(json_data),
            content_type='application/json'
        )
        
        result = RequestParser.get_body_payload(request)
        self.assertEqual(result['name'], 'test')
        self.assertEqual(result['value'], 42)

    def test_get_body_payload_form_encoded(self):
        """Test get_body_payload parses form-encoded data"""
        form_data = 'field1=value1&field2=value2'
        request = self.factory.patch(
            '/test/',
            data=form_data,
            content_type='application/x-www-form-urlencoded'
        )
        
        result = RequestParser.get_body_payload(request)
        self.assertEqual(result['field1'], 'value1')
        self.assertEqual(result['field2'], 'value2')

    def test_get_body_payload_invalid_json(self):
        """Test get_body_payload handles invalid JSON gracefully"""
        invalid_json = '{invalid json'
        request = self.factory.put(
            '/test/',
            data=invalid_json,
            content_type='application/json'
        )
        
        result = RequestParser.get_body_payload(request)
        self.assertIn('_parse_error', result)
        self.assertIn('_raw_body', result)
