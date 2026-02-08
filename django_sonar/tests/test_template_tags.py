"""Tests for custom template tags/filters."""

from django.test import SimpleTestCase

from django_sonar.templatetags.sonar_badges import sonar_level_badge_class


class SonarBadgeTemplateTagTestCase(SimpleTestCase):
    """Validate level-to-badge class mapping."""

    def test_known_levels_map_to_expected_bootstrap_classes(self):
        cases = [
            ('debug', 'bg-secondary'),
            ('info', 'bg-info text-dark'),
            ('warning', 'bg-warning text-dark'),
            ('error', 'bg-danger'),
            ('critical', 'bg-dark'),
            ('success', 'bg-success'),
        ]

        for level, expected_class in cases:
            with self.subTest(level=level):
                self.assertEqual(sonar_level_badge_class(level), expected_class)

    def test_alias_levels_map_to_expected_classes(self):
        self.assertEqual(sonar_level_badge_class('warn'), 'bg-warning text-dark')
        self.assertEqual(sonar_level_badge_class('fatal'), 'bg-dark')

    def test_unknown_level_falls_back_to_secondary(self):
        self.assertEqual(sonar_level_badge_class('custom-level'), 'bg-secondary')

    def test_none_level_defaults_to_info(self):
        self.assertEqual(sonar_level_badge_class(None), 'bg-info text-dark')
