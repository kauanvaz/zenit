from django.urls import path

from .views import TriggerAnalysisView

app_name = 'ai'

urlpatterns = [
    path('analyze/', TriggerAnalysisView.as_view(), name='analyze'),
]
