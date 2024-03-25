
from django.urls import path, include

from django_sonar import views
from django_sonar.views import SonarLoginView, SonarLogoutView

urlpatterns = [
    path('', views.index, name='sonar_index'),
    path('login/', SonarLoginView.as_view(), name='sonar_login'),
    path('logout/', SonarLogoutView.as_view(), name='sonar_logout'),
]