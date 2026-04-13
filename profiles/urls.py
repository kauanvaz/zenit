"""URL patterns for the profiles app."""
from django.urls import path

from profiles.views import ProfileDetailView, ProfileUpdateView

app_name = 'profiles'

urlpatterns = [
    path('', ProfileDetailView.as_view(), name='detail'),
    path('edit/', ProfileUpdateView.as_view(), name='edit'),
]
