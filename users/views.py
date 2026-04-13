from django.contrib.auth import login
from django.views.generic import CreateView
from django.urls import reverse_lazy

from users.forms import RegisterForm


class RegisterView(CreateView):
    """View for new user registration.

    On successful registration, automatically logs the user in
    and redirects to the dashboard.
    """

    form_class = RegisterForm
    template_name = 'auth/register.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response
