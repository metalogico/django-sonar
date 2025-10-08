from django.urls import path, include

from django_sonar.views import SonarHomeView, SonarLoginView, SonarLogoutView, SonarRequestListView, \
    SonarExceptionsListView, SonarDumpsListView, SonarSignalsListView, SonarQueriesListView, SonarRequestDetailView, \
    SonarRequestClearView, SonarDetailPayloadView, SonarDetailHeadersView, SonarDetailSessionView, \
    SonarDetailMiddlewaresView, SonarDetailQueriesView, SonarDetailDumpsView, SonarDetailExceptionView, SonarDeniedView, \
    SonarQueriesDetailView, SonarRequestTableView

urlpatterns = [
    # general
    path('', SonarHomeView.as_view(), name='sonar_index'),
    path('login/', SonarLoginView.as_view(), name='sonar_login'),
    path('logout/', SonarLogoutView.as_view(), name='sonar_logout'),
    path('denied/', SonarDeniedView.as_view(), name='sonar_denied'),

    # navigations
    path('requests/', SonarRequestListView.as_view(), name='sonar_requests'),
    path('requests/table/', SonarRequestTableView.as_view(), name='sonar_requests_table'),
    path('requests/<uuid:uuid>/', SonarRequestDetailView.as_view(), name='sonar_request_detail'),
    path('exceptions/', SonarExceptionsListView.as_view(), name='sonar_exceptions'),
    path('queries/', SonarQueriesListView.as_view(), name='sonar_queries'),
    path('dumps/', SonarDumpsListView.as_view(), name='sonar_dumps'),
    path('signals/', SonarSignalsListView.as_view(), name='sonar_signals'),

    # queries detail
    path('queries/<uuid:uuid>/q/<int:index>/', SonarQueriesDetailView.as_view(), name='sonar_queries_detail'),

    # request details
    path('requests/<uuid:uuid>/payload/', SonarDetailPayloadView.as_view(), name='sonar_detail_payload'),
    path('requests/<uuid:uuid>/headers/', SonarDetailHeadersView.as_view(), name='sonar_detail_headers'),
    path('requests/<uuid:uuid>/queries/', SonarDetailQueriesView.as_view(), name='sonar_detail_queries'),
    path('requests/<uuid:uuid>/session/', SonarDetailSessionView.as_view(), name='sonar_detail_session'),
    path('requests/<uuid:uuid>/dumps/', SonarDetailDumpsView.as_view(), name='sonar_detail_dumps'),
    path('requests/<uuid:uuid>/middlewares/', SonarDetailMiddlewaresView.as_view(), name='sonar_detail_middlewares'),
    path('requests/<uuid:uuid>/exception/', SonarDetailExceptionView.as_view(), name='sonar_detail_exception'),

    # clear
    path('clear/', SonarRequestClearView.as_view(), name='sonar_request_clear'),
]
