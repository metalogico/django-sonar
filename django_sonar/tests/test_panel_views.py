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

    def tearDown(self):
        panel_registry.clear()
        super().tearDown()

    @override_settings(DJANGO_SONAR={
        'custom_panels': ['django_sonar.tests.test_panel_views.EventsPanel'],
    })
    def test_generic_list_view_renders_custom_panel(self):
        """Generic list endpoint should resolve a custom panel and render data."""
        self.client.login(username='admin', password='admin123')

        response = self.client.get(reverse('sonar_panel_list', kwargs={'panel_key': 'audit_events'}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'user.login')
        self.assertEqual(response.context['panel'].key, 'audit_events')

    @override_settings(DJANGO_SONAR={
        'custom_panels': ['django_sonar.tests.test_panel_views.EventsPanel'],
    })
    def test_generic_detail_view_renders_custom_panel(self):
        """Generic detail endpoint should pass panel-specific detail context."""
        self.client.login(username='admin', password='admin123')

        response = self.client.get(reverse(
            'sonar_panel_detail',
            kwargs={
                'panel_key': 'audit_events',
                'uuid': self.sonar_request.uuid,
            }
        ))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'user.login')
        self.assertEqual(response.context['event_entry'].id, self.event_entry.id)

    def test_generic_list_view_invalid_panel_returns_404(self):
        """Unknown panel keys should return not found."""
        self.client.login(username='admin', password='admin123')

        response = self.client.get(reverse('sonar_panel_list', kwargs={'panel_key': 'does-not-exist'}))
        self.assertEqual(response.status_code, 404)

    def test_builtin_events_panel_renders_generic_route(self):
        """Built-in events panel should be available via generic route."""
        self.client.login(username='admin', password='admin123')

        response = self.client.get(reverse('sonar_panel_list', kwargs={'panel_key': 'events'}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'user.login')

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
    def test_home_navigation_renders_registered_panels(self):
        """Home sidebar should render built-ins plus discovered custom panels."""
        self.client.login(username='admin', password='admin123')

        response = self.client.get(reverse('sonar_index'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Requests')
        self.assertContains(response, 'Queries')
        self.assertContains(response, 'Events')
        self.assertContains(response, 'Audit Events')
        self.assertContains(response, '/p/audit_events/')
