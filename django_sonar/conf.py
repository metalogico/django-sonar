"""Django Sonar configuration with safe, backwards-compatible defaults."""

from django.conf import settings


DEFAULTS = {
    'excludes': [],
    'sensitive_fields': [],
    'custom_panels': [],
    'capture_raw_body': False,
    'raw_body_max_bytes': 10_000,
    'max_queries_per_request': 500,
    'page_size': 25,
    'capture_memory': True,
}


def get_sonar_settings():
    """Return configured values merged with Django Sonar defaults."""
    configured = getattr(settings, 'DJANGO_SONAR', {}) or {}
    return {**DEFAULTS, **configured}


def get_sonar_setting(name):
    """Return one Django Sonar setting."""
    return get_sonar_settings()[name]
