from django.contrib.auth.views import LoginView, LogoutView
from django.http import Http404
from django.urls import reverse_lazy
from django.views.generic import DetailView, RedirectView, TemplateView

from django_sonar.mixins import SuperuserRequiredMixin
from django_sonar.models import SonarData, SonarRequest
from django_sonar.panels import registry as panel_registry
from django_sonar.panels.builtins import RequestsPanel


class SonarPanelsContextMixin:
    """Expose registered panels and active panel to templates."""

    active_panel_key = None

    def get_sonar_panels(self):
        return panel_registry.all()

    def get_active_panel_key(self):
        return self.active_panel_key

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        panels = self.get_sonar_panels()
        active_key = self.get_active_panel_key() or (panels[0].key if panels else '')
        active_panel_url = ''

        for panel in panels:
            if panel.key == active_key:
                active_panel_url = panel.get_list_url()
                break

        context['sonar_panels'] = panels
        context['active_panel_key'] = active_key
        context['active_panel_url'] = active_panel_url
        return context


class GenericPanelMixin:
    """Resolve panel metadata from URL kwargs or class-level key."""

    panel_key = None
    panel = None

    def get_panel_key(self):
        return self.kwargs.get('panel_key') or self.panel_key

    def get_panel(self):
        if self.panel is None:
            panel_key = self.get_panel_key()
            panel = panel_registry.get(panel_key)

            if panel is None:
                raise Http404(f'Unknown panel key: {panel_key}')

            self.panel = panel

        return self.panel


class SonarLoginView(LoginView):
    template_name = 'django_sonar/auth/login.html'
    redirect_authenticated_user = True
    next_page = reverse_lazy('sonar_index')


class SonarLogoutView(LogoutView):
    next_page = reverse_lazy('sonar_login')


class SonarDeniedView(TemplateView):
    template_name = 'django_sonar/auth/denied.html'


class SonarHomeView(SuperuserRequiredMixin, SonarPanelsContextMixin, TemplateView):
    template_name = 'django_sonar/home/index.html'
    active_panel_key = 'requests'


class SonarRequestClearView(SuperuserRequiredMixin, RedirectView):
    url = reverse_lazy('sonar_index')

    def get(self, request, *args, **kwargs):
        SonarRequest.objects.all().delete()
        return super().get(request, *args, **kwargs)


#
# SONAR LIST VIEWS
#

class GenericPanelListView(SuperuserRequiredMixin, GenericPanelMixin, TemplateView):
    """Generic list renderer for registered panels."""

    def dispatch(self, request, *args, **kwargs):
        self.get_panel()
        return super().dispatch(request, *args, **kwargs)

    def get_template_names(self):
        return [self.get_panel().list_template]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        panel = self.get_panel()

        context['panel'] = panel
        context['active_panel_key'] = panel.key
        context.update(panel.get_list_context(self.request))
        return context


class GenericPanelDetailView(SuperuserRequiredMixin, GenericPanelMixin, TemplateView):
    """Generic detail renderer for registered panels."""

    def dispatch(self, request, *args, **kwargs):
        panel = self.get_panel()
        if not panel.supports_detail():
            raise Http404(f'Panel "{panel.key}" does not support detail view.')
        return super().dispatch(request, *args, **kwargs)

    def get_template_names(self):
        return [self.get_panel().detail_template]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        panel = self.get_panel()

        context['panel'] = panel
        context.update(panel.get_detail_context(self.request, self.kwargs.get('uuid')))
        return context


class SonarRequestListView(SuperuserRequiredMixin, TemplateView):
    template_name = 'django_sonar/requests/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(RequestsPanel.get_list_context(self.request))
        return context


class SonarRequestTableView(SuperuserRequiredMixin, TemplateView):
    template_name = 'django_sonar/requests/table.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(RequestsPanel.get_list_context(self.request))
        return context


class SonarExceptionsListView(GenericPanelListView):
    panel_key = 'exceptions'


class SonarDumpsListView(GenericPanelListView):
    panel_key = 'dumps'


class SonarSignalsListView(GenericPanelListView):
    panel_key = 'signals'


class SonarQueriesListView(GenericPanelListView):
    panel_key = 'queries'


#
# SONAR Detail Views
#


class SonarRequestDetailView(SuperuserRequiredMixin, DetailView):
    context_object_name = 'sonar_request'
    template_name = 'django_sonar/requests/detail.html'

    def get_object(self):
        record = SonarRequest.objects.get(uuid=self.kwargs.get('uuid'))
        record.is_read = True
        record.save()

        # get details from SonarData
        details = SonarData.objects.filter(sonar_request_id=record.uuid, category='details').first()
        record.details = details.data if details else {}
        return record


class SonarQueriesDetailView(SuperuserRequiredMixin, DetailView):
    context_object_name = 'sonar_query'
    template_name = 'django_sonar/queries/detail.html'

    def get_object(self):
        queries = SonarData.objects.filter(
            category='queries',
            sonar_request_id=self.kwargs.get('uuid'),
        ).first()
        executed_queries = queries.data['executed_queries'] if queries else []
        single_query = executed_queries[self.kwargs.get('index')] or {}
        single_query['sonar_request_id'] = self.kwargs.get('uuid')
        return single_query


class SonarDetailPayloadView(SuperuserRequiredMixin, TemplateView):
    template_name = 'django_sonar/requests/detail_payload.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payload = SonarData.objects.filter(sonar_request_id=self.kwargs.get('uuid'), category='payload').first()
        context['payload'] = payload.data if payload else {}
        return context


class SonarDetailHeadersView(SuperuserRequiredMixin, TemplateView):
    template_name = 'django_sonar/requests/detail_headers.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        headers = SonarData.objects.filter(sonar_request_id=self.kwargs.get('uuid'), category='headers').first()
        context['headers'] = headers.data if headers else {}
        return context


class SonarDetailQueriesView(SuperuserRequiredMixin, TemplateView):
    template_name = 'django_sonar/requests/detail_queries.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queries = SonarData.objects.filter(sonar_request_id=self.kwargs.get('uuid'), category='queries').first()
        context['queries'] = queries.data if queries else {}
        return context


class SonarDetailSessionView(SuperuserRequiredMixin, TemplateView):
    template_name = 'django_sonar/requests/detail_session.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session = SonarData.objects.filter(sonar_request_id=self.kwargs.get('uuid'), category='session').first()
        context['session'] = session.data if session else {}
        return context


class SonarDetailMiddlewaresView(SuperuserRequiredMixin, TemplateView):
    template_name = 'django_sonar/requests/detail_middlewares.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        middlewares = SonarData.objects.filter(sonar_request_id=self.kwargs.get('uuid'), category='details').first()
        context['middlewares'] = middlewares.data if middlewares else {}
        return context


class SonarDetailDumpsView(SuperuserRequiredMixin, TemplateView):
    template_name = 'django_sonar/requests/detail_dumps.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['dumps'] = []
        dumps = SonarData.objects.filter(sonar_request_id=self.kwargs.get('uuid'), category='dumps').all()
        for dump in dumps:
            context['dumps'] += [dump.data]

        return context


class SonarDetailExceptionView(SuperuserRequiredMixin, TemplateView):
    template_name = 'django_sonar/requests/detail_exception.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exception = SonarData.objects.filter(sonar_request_id=self.kwargs.get('uuid'), category='exception').first()
        context['exception'] = exception.data if exception else {}
        return context
