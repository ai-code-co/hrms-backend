from django.urls import path
from .views import SlackInteractionsView

urlpatterns = [
    # Empty path because the full path is defined in config/urls.py
    path('', SlackInteractionsView.as_view(), name='slack-interactions'),
]
