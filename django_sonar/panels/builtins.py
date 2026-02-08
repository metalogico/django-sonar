from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator

from django_sonar.models import SonarRequest
from .base import SonarPanel


class RequestsPanel(SonarPanel):
    key = 'requests'
    label = 'Requests'
    icon = 'bi-arrow-left-right'
    list_template = 'django_sonar/requests/index.html'
    list_url_name = 'sonar_requests'
    order = 10
    paginate_by = 25

    @classmethod
    def get_list_context(cls, request):
        verb_filter = request.GET.get('verb', '')
        path_filter = request.GET.get('path', '')
        status_filter = request.GET.get('status', '')
        page = request.GET.get('page', 1)

        sonar_requests = SonarRequest.objects.all()

        if verb_filter:
            sonar_requests = sonar_requests.filter(verb__iexact=verb_filter)

        if path_filter:
            sonar_requests = sonar_requests.filter(path__icontains=path_filter)

        if status_filter:
            sonar_requests = sonar_requests.filter(status=status_filter)

        sonar_requests = sonar_requests.order_by('-created_at')

        paginator = Paginator(sonar_requests, cls.paginate_by)
        try:
            sonar_requests_page = paginator.page(page)
        except PageNotAnInteger:
            sonar_requests_page = paginator.page(1)
        except EmptyPage:
            sonar_requests_page = paginator.page(paginator.num_pages)

        filters = {
            'verb': verb_filter,
            'path': path_filter,
            'status': status_filter,
        }

        return {
            'sonar_requests': sonar_requests_page,
            'page_obj': sonar_requests_page,
            'filters': filters,
        }


class ExceptionsPanel(SonarPanel):
    key = 'exceptions'
    label = 'Exceptions'
    icon = 'bi-exclamation-triangle'
    category = 'exception'
    list_template = 'django_sonar/exceptions/index.html'
    list_context_name = 'exceptions'
    list_url_name = 'sonar_exceptions'
    order = 20


class DumpsPanel(SonarPanel):
    key = 'dumps'
    label = 'Dumps'
    icon = 'bi-terminal-fill'
    category = 'dumps'
    list_template = 'django_sonar/dumps/index.html'
    list_context_name = 'dumps'
    list_url_name = 'sonar_dumps'
    order = 30


class QueriesPanel(SonarPanel):
    key = 'queries'
    label = 'Queries'
    icon = 'bi-database'
    category = 'queries'
    list_template = 'django_sonar/queries/index.html'
    list_context_name = 'queries'
    list_url_name = 'sonar_queries'
    order = 40

    @classmethod
    def get_list_context(cls, request):
        queries = cls.get_queryset(request)
        executed = []

        for query in queries:
            query_rows = query.data.get('executed_queries', [])
            for index, executed_query in enumerate(query_rows, start=0):
                row = dict(executed_query)
                row['created_at'] = query.created_at
                row['sonar_request_id'] = query.sonar_request_id
                row['index'] = index
                executed.append(row)

        return {
            'queries': executed,
        }


class SignalsPanel(SonarPanel):
    key = 'signals'
    label = 'Signals'
    icon = 'bi-diagram-3'
    list_template = 'django_sonar/signals/index.html'
    list_url_name = 'sonar_signals'
    order = 70


class EventsPanel(SonarPanel):
    key = 'events'
    label = 'Events'
    icon = 'bi-calendar-event'
    category = 'events'
    list_template = 'django_sonar/events/index.html'
    list_context_name = 'events'
    order = 50


class LogsPanel(SonarPanel):
    key = 'logs'
    label = 'Logs'
    icon = 'bi-journal-text'
    category = 'logs'
    list_template = 'django_sonar/logs/index.html'
    list_context_name = 'logs'
    order = 60


def get_builtin_panels():
    """Return built-in panel classes in sidebar order."""
    return [
        RequestsPanel,
        ExceptionsPanel,
        DumpsPanel,
        QueriesPanel,
        EventsPanel,
        LogsPanel,
        SignalsPanel,
    ]
