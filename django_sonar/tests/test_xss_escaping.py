"""
Regression tests for stored XSS sinks in Sonar templates (GHSA-9vgp-2j2c-w2mx).

SQL and dump payloads must be HTML-escaped when rendered in the dashboard.
"""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from django_sonar.models import SonarData, SonarRequest

XSS_PAYLOAD = '<img src=x onerror=alert(document.domain)>'
ESCAPED_PAYLOAD = '&lt;img src=x onerror=alert(document.domain)&gt;'


class XssEscapingTestCase(TestCase):
    """Ensure attacker-controlled SQL/dump text is escaped in HTML responses."""

    def setUp(self):
        self.client = Client()
        User = get_user_model()
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123',
        )
        self.client.login(username='admin', password='admin123')

        self.sonar_request = SonarRequest.objects.create(
            verb='GET',
            path='/search/',
            status='200',
            duration=10,
            query_count=1,
        )

        self.malicious_sql = f"SELECT '{XSS_PAYLOAD}'"
        SonarData.objects.create(
            sonar_request_id=self.sonar_request.uuid,
            category='queries',
            data={
                'executed_queries': [{'sql': self.malicious_sql, 'time': '0.001'}],
                'query_count': 1,
            },
        )
        SonarData.objects.create(
            sonar_request_id=self.sonar_request.uuid,
            category='dumps',
            data={'payload': XSS_PAYLOAD},
        )

    def _hx_get(self, url):
        return self.client.get(url, HTTP_HX_REQUEST='true')

    def test_query_detail_escapes_sql_payload(self):
        """Query detail must not render raw HTML from stored SQL text."""
        url = reverse(
            'sonar_queries_detail',
            kwargs={'uuid': self.sonar_request.uuid, 'index': 0},
        )
        response = self._hx_get(url)

        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertNotIn(XSS_PAYLOAD, body)
        self.assertIn(ESCAPED_PAYLOAD, body)

    def test_request_detail_queries_escapes_sql_payload(self):
        """Request detail queries tab must HTML-escape stored SQL text."""
        url = reverse('sonar_detail_queries', kwargs={'uuid': self.sonar_request.uuid})
        response = self._hx_get(url)

        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertNotIn(XSS_PAYLOAD, body)
        self.assertIn(ESCAPED_PAYLOAD, body)

    def test_dumps_list_escapes_payload(self):
        """Dumps list must HTML-escape dump data containing markup."""
        url = reverse('sonar_dumps')
        response = self._hx_get(url)

        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertNotIn(XSS_PAYLOAD, body)
        self.assertIn(ESCAPED_PAYLOAD, body)

    def test_clear_get_does_not_delete(self):
        """GET /clear/ must not delete Sonar data (CSRF-safe)."""
        self.assertEqual(SonarRequest.objects.count(), 1)

        response = self.client.get(reverse('sonar_request_clear'))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(SonarRequest.objects.count(), 1)

    def test_clear_post_deletes_all(self):
        """POST /clear/ deletes Sonar telemetry and redirects home."""
        self.assertEqual(SonarRequest.objects.count(), 1)

        response = self.client.post(reverse('sonar_request_clear'))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('sonar_index'))
        self.assertEqual(SonarRequest.objects.count(), 0)
