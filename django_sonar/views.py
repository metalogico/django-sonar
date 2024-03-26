import json

import uuid

from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic import TemplateView, DetailView, ListView

from django_sonar.models import SonarRequest, SonarData


class SonarLoginView(LoginView):
    template_name = 'django_sonar/auth/login.html'
    redirect_authenticated_user = True
    next_page = reverse_lazy('sonar_index')


class SonarLogoutView(LogoutView):
    next_page = reverse_lazy('sonar_login')


class SonarRequestListView(TemplateView):
    template_name = 'django_sonar/requests/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['requests'] = SonarRequest.objects.order_by('-created_at').all()
        return context


class SonarRequestDetailView(DetailView):
    context_object_name = 'sonar_request'
    template_name = 'django_sonar/requests/detail.html'

    def get_object(self):
        record = SonarRequest.objects.get(uuid=self.kwargs.get('uuid'))
        record.is_read = True
        record.save()
        return record


class SonarHomeView(TemplateView):
    template_name = 'django_sonar/home/index.html'


class SonarExceptionsListView(TemplateView):
    template_name = 'django_sonar/exceptions/index.html'


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


class SonarRequestClearView(TemplateView):
    template_name = 'django_sonar/home/index.html'

    def get(self, request, *args, **kwargs):
        SonarRequest.objects.all().delete()
        return super().get(request, *args, **kwargs)