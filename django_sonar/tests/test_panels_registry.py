"""
Tests for panel registry behavior and settings-based discovery.
"""

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings

from django_sonar.panels import SonarPanel
from django_sonar.panels import registry as panel_registry


class CustomEventsPanel(SonarPanel):
    key = 'audit_events'
    label = 'Audit Events'
    icon = 'bi-calendar-event'
    category = 'events'
    list_template = 'django_sonar/panels/test_events_list.html'
    list_context_name = 'events'


class DuplicateQueriesPanel(SonarPanel):
    key = 'queries'
    label = 'Queries Copy'
    icon = 'bi-database'
    category = 'queries-copy'
    list_template = 'django_sonar/panels/test_events_list.html'


class PanelRegistryTestCase(TestCase):
    """Test panel registration, ordering, discovery, and collisions."""

    def setUp(self):
        super().setUp()
        panel_registry.clear()

    def tearDown(self):
        panel_registry.clear()
        super().tearDown()

    def test_builtin_panels_registered_in_expected_order(self):
        """Built-in panels should always register in stable order."""
        panels = panel_registry.all(force_reload=True, include_disabled=True)
        keys = [panel.key for panel in panels]

        self.assertEqual(
            keys[:7],
            ['requests', 'exceptions', 'dumps', 'queries', 'events', 'logs', 'signals']
        )

    @override_settings(DJANGO_SONAR={
        'custom_panels': ['django_sonar.tests.test_panels_registry.CustomEventsPanel'],
    })
    def test_custom_panel_discovery_from_settings(self):
        """Custom panels defined in settings should be loaded after built-ins."""
        panels = panel_registry.all(force_reload=True, include_disabled=True)
        keys = [panel.key for panel in panels]

        self.assertIn('audit_events', keys)
        self.assertEqual(keys[-1], 'audit_events')
        self.assertEqual(panel_registry.get('audit_events'), CustomEventsPanel)

    @override_settings(DJANGO_SONAR={
        'custom_panels': ['django_sonar.tests.test_panels_registry.DuplicateQueriesPanel'],
    })
    def test_custom_panel_key_collision_raises_error(self):
        """Custom panel keys cannot collide with built-ins or each other."""
        with self.assertRaises(ImproperlyConfigured):
            panel_registry.all(force_reload=True)

    @override_settings(DJANGO_SONAR={
        'custom_panels': 'django_sonar.tests.test_panels_registry.CustomEventsPanel',
    })
    def test_custom_panel_setting_must_be_list_or_tuple(self):
        """custom_panels setting must be a sequence of dotted paths."""
        with self.assertRaises(ImproperlyConfigured):
            panel_registry.all(force_reload=True)
