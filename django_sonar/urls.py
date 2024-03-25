
from django.urls import path, include

from django_sonar import views

urlpatterns = [
    path('', views.index, name='sonar_index'),
]