from django.urls import path, include

from django_sonar.views import SonarHomeView, SonarLoginView, SonarLogoutView, SonarRequestListView, \
    SonarExceptionsListView, SonarDumpsListView, SonarSignalsListView, SonarQueriesListView, SonarRequestDetailView, \
    SonarRequestClearView

urlpatterns = [
    path('', SonarHomeView.as_view(), name='sonar_index'),
    path('login/', SonarLoginView.as_view(), name='sonar_login'),
    path('logout/', SonarLogoutView.as_view(), name='sonar_logout'),

    path('requests/', SonarRequestListView.as_view(), name='sonar_requests'),
    path('requests/<uuid:uuid>/', SonarRequestDetailView.as_view(), name='sonar_request_detail'),
    path('exceptions/', SonarExceptionsListView.as_view(), name='sonar_exceptions'),
    path('queries/', SonarQueriesListView.as_view(), name='sonar_queries'),
    path('dumps/', SonarDumpsListView.as_view(), name='sonar_dumps'),
    path('signals/', SonarSignalsListView.as_view(), name='sonar_signals'),

    path('clear/', SonarRequestClearView.as_view(), name='sonar_request_clear'),
]
