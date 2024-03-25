import uuid

from django.contrib.auth import authenticate, login
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy


def index(request):

    # if the user is not a superuser redirect to login view
    if not request.user.is_superuser:
        return redirect('sonar_login')

    requests = [
        {
            'id': uuid.uuid4(),
            'method': 'GET',
            'url': 'https://example.com',
            'status': 200,
            'time': '2022-01-01 00:00:00',
            'is_read': False
        },
        {
            'id': uuid.uuid4(),
            'method': 'POST',
            'url': 'https://example.com',
            'status': 200,
            'time': '2022-01-01 00:00:00',
            'is_read': True
        },
        {
            'id': uuid.uuid4(),
            'method': 'PUT',
            'url': 'https://example.com',
            'status': 500,
            'time': '2022-01-01 00:00:00',
            'is_read': False
        }
    ]
    return render(request, 'django-sonar/requests/index.html',
                  {'requests': requests}
                  )


class SonarLoginView(LoginView):
    template_name = 'django-sonar/auth/login.html'
    redirect_authenticated_user = True
    next_page = reverse_lazy('sonar_index')

class SonarLogoutView(LogoutView):
    next_page = reverse_lazy('sonar_login')
