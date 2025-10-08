"""
Tests for request filtering functionality in views.
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django_sonar.models import SonarRequest


class RequestFilteringTestCase(TestCase):
    """Test case for filtering requests by method, path, status, and date"""

    def setUp(self):
        """Set up test fixtures"""
        self.client = Client()
        self.User = get_user_model()
        self.superuser = self.User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        
        # Create test requests with different attributes
        now = timezone.now()
        
        # Request 1: GET /api/users/ 200
        self.request1 = SonarRequest.objects.create(
            verb='GET',
            path='/api/users/',
            status='200',
            duration=100,
            query_count=5,
            created_at=now - timedelta(hours=2)
        )
        
        # Request 2: POST /api/users/ 201
        self.request2 = SonarRequest.objects.create(
            verb='POST',
            path='/api/users/',
            status='201',
            duration=150,
            query_count=3,
            created_at=now - timedelta(hours=1)
        )
        
        # Request 3: GET /api/products/ 200
        self.request3 = SonarRequest.objects.create(
            verb='GET',
            path='/api/products/',
            status='200',
            duration=80,
            query_count=2,
            created_at=now - timedelta(minutes=30)
        )
        
        # Request 4: DELETE /api/users/1/ 404
        self.request4 = SonarRequest.objects.create(
            verb='DELETE',
            path='/api/users/1/',
            status='404',
            duration=50,
            query_count=1,
            created_at=now - timedelta(minutes=10)
        )
        
        # Request 5: GET /admin/ 500
        self.request5 = SonarRequest.objects.create(
            verb='GET',
            path='/admin/',
            status='500',
            duration=200,
            query_count=10,
            created_at=now
        )
        
        # Login as superuser
        self.client.login(username='admin', password='admin123')

    def test_no_filters_returns_all_requests(self):
        """Test that without filters, all requests are returned"""
        response = self.client.get(reverse('sonar_requests'))
        self.assertEqual(response.status_code, 200)
        # With pagination, check the page object
        self.assertEqual(response.context['page_obj'].paginator.count, 5)

    def test_filter_by_verb_get(self):
        """Test filtering by GET method"""
        response = self.client.get(reverse('sonar_requests'), {'verb': 'GET'})
        self.assertEqual(response.status_code, 200)
        requests = list(response.context['sonar_requests'])
        self.assertEqual(len(requests), 3)
        for req in requests:
            self.assertEqual(req.verb, 'GET')

    def test_filter_by_verb_post(self):
        """Test filtering by POST method"""
        response = self.client.get(reverse('sonar_requests'), {'verb': 'POST'})
        self.assertEqual(response.status_code, 200)
        requests = list(response.context['sonar_requests'])
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0].verb, 'POST')

    def test_filter_by_path_contains(self):
        """Test filtering by path substring"""
        response = self.client.get(reverse('sonar_requests'), {'path': '/api/users'})
        self.assertEqual(response.status_code, 200)
        requests = list(response.context['sonar_requests'])
        self.assertEqual(len(requests), 3)
        for req in requests:
            self.assertIn('/api/users', req.path)

    def test_filter_by_path_admin(self):
        """Test filtering by admin path"""
        response = self.client.get(reverse('sonar_requests'), {'path': '/admin'})
        self.assertEqual(response.status_code, 200)
        requests = list(response.context['sonar_requests'])
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0].path, '/admin/')

    def test_filter_by_status_200(self):
        """Test filtering by status 200"""
        response = self.client.get(reverse('sonar_requests'), {'status': '200'})
        self.assertEqual(response.status_code, 200)
        requests = list(response.context['sonar_requests'])
        self.assertEqual(len(requests), 2)
        for req in requests:
            self.assertEqual(req.status, '200')

    def test_filter_by_status_404(self):
        """Test filtering by status 404"""
        response = self.client.get(reverse('sonar_requests'), {'status': '404'})
        self.assertEqual(response.status_code, 200)
        requests = list(response.context['sonar_requests'])
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0].status, '404')


    def test_combined_filters_verb_and_path(self):
        """Test combining verb and path filters"""
        response = self.client.get(reverse('sonar_requests'), {
            'verb': 'GET',
            'path': '/api/users'
        })
        self.assertEqual(response.status_code, 200)
        requests = list(response.context['sonar_requests'])
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0].verb, 'GET')
        self.assertIn('/api/users', requests[0].path)

    def test_combined_filters_verb_and_status(self):
        """Test combining verb and status filters"""
        response = self.client.get(reverse('sonar_requests'), {
            'verb': 'GET',
            'status': '200'
        })
        self.assertEqual(response.status_code, 200)
        requests = list(response.context['sonar_requests'])
        self.assertEqual(len(requests), 2)
        for req in requests:
            self.assertEqual(req.verb, 'GET')
            self.assertEqual(req.status, '200')

    def test_filter_values_preserved_in_context(self):
        """Test that filter values are passed back to template"""
        response = self.client.get(reverse('sonar_requests'), {
            'verb': 'POST',
            'path': '/api/',
            'status': '201'
        })
        self.assertEqual(response.status_code, 200)
        filters = response.context['filters']
        self.assertEqual(filters['verb'], 'POST')
        self.assertEqual(filters['path'], '/api/')
        self.assertEqual(filters['status'], '201')

    def test_case_insensitive_verb_filter(self):
        """Test that verb filter is case-insensitive"""
        response = self.client.get(reverse('sonar_requests'), {'verb': 'get'})
        self.assertEqual(response.status_code, 200)
        requests = list(response.context['sonar_requests'])
        self.assertEqual(len(requests), 3)
        for req in requests:
            self.assertEqual(req.verb, 'GET')

    def test_no_results_with_strict_filters(self):
        """Test that no results are returned when filters don't match"""
        response = self.client.get(reverse('sonar_requests'), {
            'verb': 'PUT',
            'status': '999'
        })
        self.assertEqual(response.status_code, 200)
        requests = list(response.context['sonar_requests'])
        self.assertEqual(len(requests), 0)

    def test_ordering_preserved_with_filters(self):
        """Test that results are ordered by created_at descending"""
        response = self.client.get(reverse('sonar_requests'), {'verb': 'GET'})
        self.assertEqual(response.status_code, 200)
        requests = list(response.context['sonar_requests'])
        # Check that requests are ordered by created_at descending
        for i in range(len(requests) - 1):
            self.assertGreaterEqual(requests[i].created_at, requests[i + 1].created_at)

    def test_pagination_works(self):
        """Test that pagination is working correctly"""
        # Create more requests to test pagination (25 per page)
        for i in range(30):
            SonarRequest.objects.create(
                verb='GET',
                path=f'/test/{i}/',
                status='200',
                duration=100,
                query_count=1,
            )
        
        # Test first page
        response = self.client.get(reverse('sonar_requests'))
        self.assertEqual(response.status_code, 200)
        page_obj = response.context['page_obj']
        self.assertEqual(len(response.context['sonar_requests']), 25)
        self.assertTrue(page_obj.has_next())
        self.assertFalse(page_obj.has_previous())
        
        # Test second page
        response = self.client.get(reverse('sonar_requests'), {'page': 2})
        self.assertEqual(response.status_code, 200)
        page_obj = response.context['page_obj']
        self.assertEqual(len(response.context['sonar_requests']), 10)  # 35 total - 25 on first page
        self.assertFalse(page_obj.has_next())
        self.assertTrue(page_obj.has_previous())
