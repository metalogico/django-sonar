from collections import OrderedDict

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string

from .base import SonarPanel
from .builtins import get_builtin_panels

_registry = OrderedDict()
_loaded_custom_paths = None


def _get_custom_panel_paths():
    sonar_settings = getattr(settings, 'DJANGO_SONAR', {})
    custom_paths = sonar_settings.get('custom_panels', [])

    if custom_paths is None:
        return tuple()

    if not isinstance(custom_paths, (list, tuple)):
        raise ImproperlyConfigured('DJANGO_SONAR["custom_panels"] must be a list or tuple of import paths.')

    return tuple(custom_paths)


def register(panel_class):
    """Register a panel class by key."""
    global _loaded_custom_paths

    if not isinstance(panel_class, type) or not issubclass(panel_class, SonarPanel):
        raise ImproperlyConfigured('Panels must be classes inheriting from SonarPanel.')

    if not _registry:
        _loaded_custom_paths = _get_custom_panel_paths()

    panel_class.validate()

    if panel_class.key in _registry:
        raise ImproperlyConfigured(f'Panel key collision detected for "{panel_class.key}".')

    _registry[panel_class.key] = panel_class


def _load_custom_panels(custom_paths):
    for panel_path in custom_paths:
        try:
            panel_class = import_string(panel_path)
        except ImportError as exc:
            raise ImproperlyConfigured(
                f'Unable to import custom panel "{panel_path}": {exc}'
            ) from exc

        register(panel_class)


def _load_registry(force_reload=False):
    global _loaded_custom_paths

    custom_paths = _get_custom_panel_paths()

    if not force_reload and _registry and _loaded_custom_paths == custom_paths:
        return

    _registry.clear()

    for panel_class in get_builtin_panels():
        register(panel_class)

    _load_custom_panels(custom_paths)
    _loaded_custom_paths = custom_paths


def all(force_reload=False, include_disabled=False):
    """Return all registered panels in order."""
    _load_registry(force_reload=force_reload)
    panels = list(_registry.values())

    if include_disabled:
        return panels

    return [panel for panel in panels if panel.is_enabled()]


def get(panel_key, force_reload=False, include_disabled=False):
    """Get a single registered panel by key."""
    for panel in all(force_reload=force_reload, include_disabled=include_disabled):
        if panel.key == panel_key:
            return panel

    return None


def clear():
    """Clear in-memory panel registry cache."""
    global _loaded_custom_paths

    _registry.clear()
    _loaded_custom_paths = None
