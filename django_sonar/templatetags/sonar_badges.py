from django import template


register = template.Library()

_LEVEL_BADGE_CLASSES = {
    'debug': 'bg-secondary',
    'trace': 'bg-secondary',
    'info': 'bg-info text-dark',
    'notice': 'bg-primary',
    'success': 'bg-success',
    'warning': 'bg-warning text-dark',
    'warn': 'bg-warning text-dark',
    'error': 'bg-danger',
    'exception': 'bg-danger',
    'critical': 'bg-dark',
    'fatal': 'bg-dark',
    'alert': 'bg-dark',
    'emergency': 'bg-dark',
}


@register.filter
def sonar_level_badge_class(level):
    normalized_level = str(level or 'info').strip().lower()
    return _LEVEL_BADGE_CLASSES.get(normalized_level, 'bg-secondary')
