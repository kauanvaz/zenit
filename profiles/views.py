from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import DetailView, UpdateView

from profiles.models import Profile


class ProfileDetailView(LoginRequiredMixin, DetailView):
    """Display the authenticated user's profile."""

    model = Profile
    template_name = 'profiles/detail.html'

    def get_object(self, queryset=None):
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        return profile


class ProfileUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """Allow the authenticated user to update their profile."""

    model = Profile
    template_name = 'profiles/update.html'
    fields = ['phone', 'avatar']
    success_url = reverse_lazy('profiles:detail')
    success_message = 'Perfil atualizado com sucesso.'

    def get_object(self, queryset=None):
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        return profile
