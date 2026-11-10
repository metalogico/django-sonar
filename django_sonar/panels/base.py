from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.urls import reverse

from django_sonar.conf import get_sonar_setting
from django_sonar.models import SonarData


class SonarPanel:
    """Base panel contract for Sonar list/detail rendering."""

    key = None
    label = None
    icon = 'bi-card-list'
    category = None
    list_template = None
    detail_template = None
    list_context_name = 'entries'
    detail_context_name = 'entry'
    list_url_name = None
    detail_url_name = None
    enabled = True
    order = 100

    @classmethod
    def validate(cls):
        """Validate panel contract for registration."""
        if not cls.key:
            raise ImproperlyConfigured(f'Panel "{cls.__name__}" must define a non-empty "key".')

        if not cls.label:
            raise ImproperlyConfigured(f'Panel "{cls.__name__}" must define a non-empty "label".')

        if not cls.list_template:
            raise ImproperlyConfigured(f'Panel "{cls.__name__}" must define a non-empty "list_template".')

    @classmethod
    def is_enabled(cls):
        """Return whether the panel should be visible/accessible."""
        enabled_value = cls.enabled
        if callable(enabled_value):
            sonar_settings = getattr(settings, 'DJANGO_SONAR', {})
            return bool(enabled_value(sonar_settings))
        return bool(enabled_value)

    @classmethod
    def supports_detail(cls):
        """Whether this panel supports the generic detail endpoint."""
        return bool(cls.detail_template)

    @classmethod
    def get_list_url(cls):
        """Resolve panel list URL."""
        if cls.list_url_name:
            return reverse(cls.list_url_name)

        return reverse('sonar_panel_list', kwargs={'panel_key': cls.key})

    @classmethod
    def get_detail_url(cls, uuid_value):
        """Resolve panel detail URL."""
        if not cls.supports_detail():
            return ''

        if cls.detail_url_name:
            return reverse(cls.detail_url_name, kwargs={'uuid': uuid_value})

        return reverse('sonar_panel_detail', kwargs={'panel_key': cls.key, 'uuid': uuid_value})

    @classmethod
    def get_queryset(cls, request):
        """Return base queryset for the panel."""
        if not cls.category:
            return SonarData.objects.none()

        return SonarData.objects.filter(category=cls.category).order_by('-created_at').all()

    @classmethod
    def get_list_context(cls, request):
        """Build context for list rendering."""
        return {
            cls.list_context_name: cls.get_queryset(request),
        }

    @classmethod
    def get_detail_context(cls, request, uuid_value):
        """Build context for detail rendering."""
        entry = get_object_or_404(cls.get_queryset(request), sonar_request_id=uuid_value)
        return {
            cls.detail_context_name: entry,
        }


class PaginatedSonarPanel(SonarPanel):
    """Opt-in panel base that returns a bounded page of entries."""

    @classmethod
    def get_list_context(cls, request):
        paginator = Paginator(cls.get_queryset(request), get_sonar_setting('page_size'))
        page_obj = paginator.get_page(request.GET.get('page', 1))
        return {
            cls.list_context_name: page_obj,
            'page_obj': page_obj,
        }
