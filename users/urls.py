"""
URL patterns for the users app - authentication routes.
"""
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from users.forms import CustomAuthenticationForm
from users.views import RegisterView

app_name = 'users'

urlpatterns = [
    path(
        'register/',
        RegisterView.as_view(),
        name='register',
    ),
    path(
        'login/',
        LoginView.as_view(
            form_class=CustomAuthenticationForm,
            template_name='auth/login.html',
        ),
        name='login',
    ),
    path(
        'logout/',
        LogoutView.as_view(),
        name='logout',
    ),
]
