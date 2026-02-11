from django.utils import timezone

from django_sonar import utils
from django_sonar.utils import make_json_serializable


def sonar_event(name, payload=None, level='info', tags=None):
    """Queue a structured event entry for persistence at request end."""
    event = {
        'name': name,
        'level': level,
        'payload': make_json_serializable(payload or {}),
        'tags': tags or [],
        'timestamp': timezone.now().isoformat(),
    }
    utils.add_sonar_event(event)
    return event
