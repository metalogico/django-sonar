from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic import TemplateView, DetailView, RedirectView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django_sonar.mixins import SuperuserRequiredMixin
from django_sonar.models import SonarRequest, SonarData


class SonarLoginView(LoginView):
    template_name = 'django_sonar/auth/login.html'
    redirect_authenticated_user = True
    next_page = reverse_lazy('sonar_index')


class SonarLogoutView(LogoutView):
    next_page = reverse_lazy('sonar_login')


class SonarDeniedView(TemplateView):
    template_name = 'django_sonar/auth/denied.html'


class SonarHomeView(SuperuserRequiredMixin, TemplateView):
    template_name = 'django_sonar/home/index.html'


class SonarRequestClearView(SuperuserRequiredMixin, RedirectView):
    url = reverse_lazy('sonar_index')

    def get(self, request, *args, **kwargs):
        SonarRequest.objects.all().delete()
        return super().get(request, *args, **kwargs)


#
# SONAR LIST VIEWS
#

class SonarRequestListView(SuperuserRequiredMixin, TemplateView):
    template_name = 'django_sonar/requests/index.html'
    paginate_by = 25

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get filter parameters from request
        verb_filter = self.request.GET.get('verb', '')
        path_filter = self.request.GET.get('path', '')
        status_filter = self.request.GET.get('status', '')
        page = self.request.GET.get('page', 1)
        
        # Start with all requests
        sonar_requests = SonarRequest.objects.all()
        
        # Apply filters
        if verb_filter:
            sonar_requests = sonar_requests.filter(verb__iexact=verb_filter)
        
        if path_filter:
            sonar_requests = sonar_requests.filter(path__icontains=path_filter)
        
        if status_filter:
            sonar_requests = sonar_requests.filter(status=status_filter)
        
        # Order by created_at descending
        sonar_requests = sonar_requests.order_by('-created_at')
        
        # Pagination
        paginator = Paginator(sonar_requests, self.paginate_by)
        try:
            sonar_requests_page = paginator.page(page)
        except PageNotAnInteger:
            sonar_requests_page = paginator.page(1)
        except EmptyPage:
            sonar_requests_page = paginator.page(paginator.num_pages)
        
        context['sonar_requests'] = sonar_requests_page
        context['page_obj'] = sonar_requests_page
        
        # Pass filter values back to template for form persistence
        context['filters'] = {
            'verb': verb_filter,
            'path': path_filter,
            'status': status_filter,
        }
        
        return context


class SonarRequestTableView(SuperuserRequiredMixin, TemplateView):
    template_name = 'django_sonar/requests/table.html'
    paginate_by = 25

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get filter parameters from request
        verb_filter = self.request.GET.get('verb', '')
        path_filter = self.request.GET.get('path', '')
        status_filter = self.request.GET.get('status', '')
        page = self.request.GET.get('page', 1)
        
        # Start with all requests
        sonar_requests = SonarRequest.objects.all()
        
        # Apply filters
        if verb_filter:
            sonar_requests = sonar_requests.filter(verb__iexact=verb_filter)
        
        if path_filter:
            sonar_requests = sonar_requests.filter(path__icontains=path_filter)
        
        if status_filter:
            sonar_requests = sonar_requests.filter(status=status_filter)
        
        # Order by created_at descending
        sonar_requests = sonar_requests.order_by('-created_at')
        
        # Pagination
        paginator = Paginator(sonar_requests, self.paginate_by)
        try:
            sonar_requests_page = paginator.page(page)
        except PageNotAnInteger:
            sonar_requests_page = paginator.page(1)
        except EmptyPage:
            sonar_requests_page = paginator.page(paginator.num_pages)
        
        context['sonar_requests'] = sonar_requests_page
        context['page_obj'] = sonar_requests_page
        
        # Pass filter values back to template for pagination links
        context['filters'] = {
            'verb': verb_filter,
            'path': path_filter,
            'status': status_filter,
        }
        
        return context


class SonarExceptionsListView(SuperuserRequiredMixin, TemplateView):
    template_name = 'django_sonar/exceptions/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['exceptions'] = SonarData.objects.filter(category='exception').order_by('-created_at').all()
        return context


class SonarDumpsListView(SuperuserRequiredMixin, TemplateView):
    template_name = 'django_sonar/dumps/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['dumps'] = SonarData.objects.filter(category='dumps').order_by('-created_at').all()
        return context


class SonarSignalsListView(SuperuserRequiredMixin, TemplateView):
    template_name = 'django_sonar/signals/index.html'


class SonarQueriesListView(SuperuserRequiredMixin, TemplateView):
    template_name = 'django_sonar/queries/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queries = SonarData.objects.filter(category='queries').order_by('-created_at').all()
        # extract queries from SonarData queries
        context['queries'] = []
        for query in queries:
            if 'executed_queries' in query.data:
                for index, executed_query in enumerate(query.data['executed_queries'], start=0):
                    executed_query['created_at'] = query.created_at
                    executed_query['sonar_request_id'] = query.sonar_request_id
                    executed_query['index'] = index
                    context['queries'].append(executed_query)
        return context


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
        queries = SonarData.objects.filter(category='queries',
                                           sonar_request_id=self.kwargs.get('uuid')).first()
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
