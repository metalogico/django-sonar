from django.contrib.auth.mixins import AccessMixin
from django.http import HttpResponseForbidden
from django.shortcuts import redirect


class SuperuserRequiredMixin(AccessMixin):
    """
    Ensure that the user is logged in and is a superuser.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('sonar_login')

        if not request.user.is_superuser:
            return redirect('sonar_denied')

        return super().dispatch(request, *args, **kwargs)
