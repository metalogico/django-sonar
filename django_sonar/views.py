import json

import uuid

from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic import TemplateView, DetailView, ListView, RedirectView

from django_sonar.models import SonarRequest, SonarData


class SonarLoginView(LoginView):
    template_name = 'django_sonar/auth/login.html'
    redirect_authenticated_user = True
    next_page = reverse_lazy('sonar_index')


class SonarLogoutView(LogoutView):
    next_page = reverse_lazy('sonar_login')


class SonarHomeView(TemplateView):
    template_name = 'django_sonar/home/index.html'


class SonarRequestClearView(RedirectView):
    url = reverse_lazy('sonar_index')

    def get(self, request, *args, **kwargs):
        SonarRequest.objects.all().delete()
        return super().get(request, *args, **kwargs)


#
# SONAR LIST VIEWS
#

class SonarRequestListView(TemplateView):
    template_name = 'django_sonar/requests/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sonar_requests'] = SonarRequest.objects.order_by('-created_at').all()
        return context


class SonarExceptionsListView(TemplateView):
    template_name = 'django_sonar/exceptions/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['exceptions'] = SonarData.objects.filter(category='exception').order_by('-created_at').all()
        return context


class SonarDumpsListView(TemplateView):
    template_name = 'django_sonar/dumps/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['dumps'] = SonarData.objects.filter(category='dumps').order_by('-created_at').all()
        return context


class SonarSignalsListView(TemplateView):
    template_name = 'django_sonar/signals/index.html'


class SonarQueriesListView(TemplateView):
    template_name = 'django_sonar/queries/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queries = SonarData.objects.filter(category='queries').order_by('-created_at').all()
        # extract queries from SonarData queries
        context['queries'] = []
        for query in queries:
            if 'executed_queries' in query.data:
                for executed_query in query.data['executed_queries']:
                    executed_query['created_at'] = query.created_at
                    context['queries'].append(executed_query)
        return context


#
# SONAR Detail Views
#


class SonarRequestDetailView(DetailView):
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


class SonarDetailPayloadView(TemplateView):
    template_name = 'django_sonar/requests/detail_payload.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payload = SonarData.objects.filter(sonar_request_id=self.kwargs.get('uuid'), category='payload').first()
        context['payload'] = payload.data if payload else {}
        return context


class SonarDetailHeadersView(TemplateView):
    template_name = 'django_sonar/requests/detail_headers.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        headers = SonarData.objects.filter(sonar_request_id=self.kwargs.get('uuid'), category='headers').first()
        context['headers'] = headers.data if headers else {}
        return context


class SonarDetailQueriesView(TemplateView):
    template_name = 'django_sonar/requests/detail_queries.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queries = SonarData.objects.filter(sonar_request_id=self.kwargs.get('uuid'), category='queries').first()
        context['queries'] = queries.data if queries else {}
        return context


class SonarDetailSessionView(TemplateView):
    template_name = 'django_sonar/requests/detail_session.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        session = SonarData.objects.filter(sonar_request_id=self.kwargs.get('uuid'), category='session').first()
        context['session'] = session.data if session else {}
        return context


class SonarDetailMiddlewaresView(TemplateView):
    template_name = 'django_sonar/requests/detail_middlewares.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        middlewares = SonarData.objects.filter(sonar_request_id=self.kwargs.get('uuid'), category='details').first()
        context['middlewares'] = middlewares.data if middlewares else {}
        return context


class SonarDetailDumpsView(TemplateView):
    template_name = 'django_sonar/requests/detail_dumps.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['dumps'] = []
        dumps = SonarData.objects.filter(sonar_request_id=self.kwargs.get('uuid'), category='dumps').all()
        for dump in dumps:
            context['dumps'] += [dump.data]

        return context


class SonarDetailExceptionView(TemplateView):
    template_name = 'django_sonar/requests/detail_exception.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        exception = SonarData.objects.filter(sonar_request_id=self.kwargs.get('uuid'), category='exception').first()
        context['exception'] = exception.data if exception else {}
        return context