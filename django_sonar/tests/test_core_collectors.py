"""
Tests for core.collectors module.

Tests DataCollector class functionality for data persistence.
"""

import uuid
from django.test import override_settings
from django_sonar.core.collectors import DataCollector
from django_sonar.models import SonarRequest, SonarData
from django_sonar import utils
from .base import BaseMiddlewareTestCase


class DataCollectorTestCase(BaseMiddlewareTestCase):
    """Test DataCollector functionality"""

    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        
        # Create a SonarRequest for testing
        self.sonar_request = SonarRequest.objects.create(
            verb='GET',
            path='/test/',
            status='200',
            duration=100,
            ip_address='127.0.0.1',
            hostname='testhost',
            is_ajax=False
        )
        self.collector = DataCollector(self.sonar_request.uuid)

    def test_save_details(self):
        """Test save_details creates correct SonarData entry"""
        user_info = {'user_id': 1, 'username': 'test'}
        view_func = 'test.views.home'
        middlewares = ['middleware1', 'middleware2']
        memory_diff = 1.5
        
        self.collector.save_details(user_info, view_func, middlewares, memory_diff)
        
        # Verify data was saved
        data = SonarData.objects.get(
            sonar_request=self.sonar_request,
            category='details'
        )
        self.assertEqual(data.data['user_info'], user_info)
        self.assertEqual(data.data['view_func'], view_func)
        self.assertEqual(data.data['middlewares_used'], middlewares)
        self.assertEqual(data.data['memory_used'], memory_diff)

    def test_save_payload(self):
        """Test save_payload creates correct SonarData entry"""
        get_payload = {'q': 'search', 'page': '1'}
        post_payload = {'username': 'test', 'email': 'test@example.com'}
        
        self.collector.save_payload(get_payload, post_payload)
        
        # Verify data was saved
        data = SonarData.objects.get(
            sonar_request=self.sonar_request,
            category='payload'
        )
        self.assertEqual(data.data['get_payload'], get_payload)
        self.assertEqual(data.data['post_payload'], post_payload)

    def test_save_queries(self):
        """Test save_queries creates correct SonarData entry"""
        queries = [
            {'sql': 'SELECT * FROM users', 'time': '0.001'},
            {'sql': 'INSERT INTO logs', 'time': '0.002'}
        ]
        
        self.collector.save_queries(queries)
        
        # Verify data was saved
        data = SonarData.objects.get(
            sonar_request=self.sonar_request,
            category='queries'
        )
        self.assertEqual(data.data['executed_queries'], queries)
        self.assertEqual(data.data['query_count'], 2)

    def test_save_headers(self):
        """Test save_headers creates correct SonarData entry"""
        headers = {'User-Agent': 'TestAgent', 'Accept': 'application/json'}
        
        self.collector.save_headers(headers)
        
        # Verify data was saved
        data = SonarData.objects.get(
            sonar_request=self.sonar_request,
            category='headers'
        )
        self.assertEqual(data.data['request_headers'], headers)

    def test_save_session(self):
        """Test save_session creates correct SonarData entry"""
        session_data = {'session_key': 'value', 'user_id': 1}
        
        self.collector.save_session(session_data)
        
        # Verify data was saved
        data = SonarData.objects.get(
            sonar_request=self.sonar_request,
            category='session'
        )
        self.assertEqual(data.data['session_data'], session_data)

    def test_save_dumps(self):
        """Test save_dumps retrieves and saves dumps from utils"""
        # Add some dumps to thread local storage
        utils.sonar('test_value_1', {'key': 'value'}, [1, 2, 3])
        
        self.collector.save_dumps()
        
        # Verify dumps were saved
        dumps = SonarData.objects.filter(
            sonar_request=self.sonar_request,
            category='dumps'
        )
        self.assertEqual(dumps.count(), 3)
        
        # Verify dumps were reset
        self.assertEqual(len(utils.get_sonar_dump()), 0)

    def test_save_exceptions(self):
        """Test save_exceptions retrieves and saves exceptions from utils"""
        # Add exception to thread local storage
        exception_info = {
            'file_name': 'test.py',
            'line_number': 42,
            'exception_message': 'Test error'
        }
        utils.add_sonar_exception(exception_info)
        
        self.collector.save_exceptions()
        
        # Verify exception was saved
        exceptions = SonarData.objects.filter(
            sonar_request=self.sonar_request,
            category='exception'
        )
        self.assertEqual(exceptions.count(), 1)
        self.assertEqual(exceptions.first().data, exception_info)
        
        # Verify exceptions were reset
        self.assertEqual(len(utils.get_sonar_exceptions()), 0)

    def test_collector_with_different_request(self):
        """Test collector can work with multiple requests"""
        # Create another request
        request2 = SonarRequest.objects.create(
            verb='POST',
            path='/test2/',
            status='201',
            duration=200,
            ip_address='127.0.0.2',
            hostname='testhost2',
            is_ajax=False
        )
        collector2 = DataCollector(request2.uuid)
        
        # Save data for both requests
        self.collector.save_details(None, 'view1', [], 0)
        collector2.save_details(None, 'view2', [], 0)
        
        # Verify each collector saved to the correct request
        data1 = SonarData.objects.get(
            sonar_request=self.sonar_request,
            category='details'
        )
        data2 = SonarData.objects.get(
            sonar_request=request2,
            category='details'
        )
        
        self.assertEqual(data1.data['view_func'], 'view1')
        self.assertEqual(data2.data['view_func'], 'view2')
