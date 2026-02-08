"""
Tests for generic panel list/detail rendering and dynamic navigation.
"""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from django_sonar.models import SonarData, SonarRequest
from django_sonar.panels import SonarPanel
from django_sonar.panels import registry as panel_registry


class EventsPanel(SonarPanel):
    key = 'audit_events'
    label = 'Audit Events'
    icon = 'bi-calendar-event'
    category = 'events'
    list_template = 'django_sonar/panels/test_events_list.html'
    detail_template = 'django_sonar/panels/test_events_detail.html'
    list_context_name = 'events'
    detail_context_name = 'event_entry'


class GenericPanelViewTestCase(TestCase):
    """Test generic panel list/detail endpoints and permissions."""

    def setUp(self):
        super().setUp()
        panel_registry.clear()

        self.client = Client()
        self.User = get_user_model()
        self.superuser = self.User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        self.user = self.User.objects.create_user(
            username='user',
            email='user@example.com',
            password='user123'
        )

        self.sonar_request = SonarRequest.objects.create(
            verb='GET',
            path='/events/',
            status='200',
            duration=10,
            query_count=0,
        )

        self.event_entry = SonarData.objects.create(
            sonar_request_id=self.sonar_request.uuid,
            category='events',
            data={'name': 'user.login'}
        )

        SonarData.objects.create(
            sonar_request_id=self.sonar_request.uuid,
            category='queries',
            data={
                'executed_queries': [{'sql': 'SELECT 1', 'time': '0.001'}],
                'query_count': 1,
            }
        )

    def tearDown(self):
        panel_registry.clear()
        super().tearDown()

    def _hx_get(self, url, params=None):
        return self.client.get(url, params or {}, HTTP_HX_REQUEST='true')

    def test_requests_list_non_htmx_renders_shell_with_permalink_bootstrap(self):
        """Direct requests list URL should render shell and bootstrap same list URL."""
        self.client.login(username='admin', password='admin123')

        response = self.client.get(reverse('sonar_requests'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="main-content"')
        self.assertContains(response, "htmx.ajax('GET', '/requests/'")

    def test_requests_list_htmx_renders_partial(self):
        """HTMX requests list URL should return list fragment, not full shell."""
        self.client.login(username='admin', password='admin123')

        response = self._hx_get(reverse('sonar_requests'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<h5 class="card-title">Requests</h5>', html=True)
        self.assertNotContains(response, '<!doctype html>', html=False)

    @override_settings(DJANGO_SONAR={
        'custom_panels': ['django_sonar.tests.test_panel_views.EventsPanel'],
    })
    def test_generic_list_view_non_htmx_renders_shell(self):
        """Direct generic panel URL should render shell and bootstrap same panel URL."""
        self.client.login(username='admin', password='admin123')

        response = self.client.get(reverse('sonar_panel_list', kwargs={'panel_key': 'audit_events'}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "htmx.ajax('GET', '/p/audit_events/'")

    @override_settings(DJANGO_SONAR={
        'custom_panels': ['django_sonar.tests.test_panel_views.EventsPanel'],
    })
    def test_generic_list_view_htmx_renders_custom_panel(self):
        """Generic panel HTMX endpoint should render custom panel data."""
        self.client.login(username='admin', password='admin123')

        response = self._hx_get(reverse('sonar_panel_list', kwargs={'panel_key': 'audit_events'}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'user.login')
        self.assertEqual(response.context['panel'].key, 'audit_events')

    @override_settings(DJANGO_SONAR={
        'custom_panels': ['django_sonar.tests.test_panel_views.EventsPanel'],
    })
    def test_generic_detail_view_htmx_renders_custom_panel(self):
        """Generic detail endpoint should pass panel-specific detail context."""
        self.client.login(username='admin', password='admin123')

        response = self._hx_get(reverse(
            'sonar_panel_detail',
            kwargs={
                'panel_key': 'audit_events',
                'uuid': self.sonar_request.uuid,
            }
        ))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'user.login')
        self.assertEqual(response.context['event_entry'].id, self.event_entry.id)

    def test_builtin_events_panel_renders_legacy_route(self):
        """Built-in events panel should be available via the legacy URL wrapper."""
        self.client.login(username='admin', password='admin123')

        response = self._hx_get(reverse('sonar_events'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'user.login')

    def test_request_detail_non_htmx_renders_shell(self):
        """Direct request detail URL should render shell and bootstrap detail permalink."""
        self.client.login(username='admin', password='admin123')

        response = self.client.get(reverse('sonar_request_detail', kwargs={'uuid': self.sonar_request.uuid}))

        self.assertEqual(response.status_code, 200)
        encoded_uuid = str(self.sonar_request.uuid).replace('-', '\\u002D')
        self.assertContains(response, "htmx.ajax('GET', '/requests/")
        self.assertContains(response, f'/requests/{encoded_uuid}/')

    def test_requests_table_non_htmx_redirects_to_requests(self):
        """Direct requests table URL should redirect to canonical requests list URL."""
        self.client.login(username='admin', password='admin123')

        response = self.client.get(reverse('sonar_requests_table'), {'page': 2, 'verb': 'GET'})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/requests/?page=2&verb=GET')

    def test_request_detail_subroutes_non_htmx_redirect_to_request_detail(self):
        """Direct request subroutes should redirect to request detail permalink."""
        self.client.login(username='admin', password='admin123')

        routes = [
            'sonar_detail_payload',
            'sonar_detail_headers',
            'sonar_detail_queries',
            'sonar_detail_session',
            'sonar_detail_dumps',
            'sonar_detail_middlewares',
            'sonar_detail_exception',
        ]

        for route_name in routes:
            with self.subTest(route=route_name):
                response = self.client.get(reverse(route_name, kwargs={'uuid': self.sonar_request.uuid}))
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.url, f'/requests/{self.sonar_request.uuid}/')

    def test_generic_list_view_invalid_panel_returns_404(self):
        """Unknown panel keys should return not found."""
        self.client.login(username='admin', password='admin123')

        response = self.client.get(reverse('sonar_panel_list', kwargs={'panel_key': 'does-not-exist'}))
        self.assertEqual(response.status_code, 404)

    def test_generic_list_view_requires_authentication(self):
        """Anonymous users should be redirected to sonar login."""
        response = self.client.get(reverse('sonar_panel_list', kwargs={'panel_key': 'queries'}))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('sonar_login'), response.url)

    def test_generic_list_view_requires_superuser(self):
        """Authenticated non-superusers should be redirected to denied page."""
        self.client.login(username='user', password='user123')

        response = self.client.get(reverse('sonar_panel_list', kwargs={'panel_key': 'queries'}))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('sonar_denied'))

    @override_settings(DJANGO_SONAR={
        'custom_panels': ['django_sonar.tests.test_panel_views.EventsPanel'],
    })
    def test_home_navigation_renders_registered_panels_and_push_url(self):
        """Home sidebar should render built-ins, custom panels, and push-url attributes."""
        self.client.login(username='admin', password='admin123')

        response = self.client.get(reverse('sonar_index'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Requests')
        self.assertContains(response, 'Queries')
        self.assertContains(response, 'Events')
        self.assertContains(response, 'Audit Events')
        self.assertContains(response, '/p/audit_events/')
        self.assertContains(response, 'hx-push-url="true"')

    def test_requests_and_queries_templates_include_push_url_on_primary_links(self):
        """Primary request/query navigation links should push URLs to browser history."""
        self.client.login(username='admin', password='admin123')

        requests_response = self._hx_get(reverse('sonar_requests'))
        self.assertContains(requests_response, 'hx-push-url="true"')

        requests_table_response = self._hx_get(reverse('sonar_requests_table'))
        self.assertContains(requests_table_response, 'hx-push-url="true"')

        queries_response = self._hx_get(reverse('sonar_queries'))
        self.assertContains(queries_response, 'hx-push-url="true"')
