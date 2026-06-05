from django.urls import path
from .views import FlutterwaveWebhookView

urlpatterns = [
    path('webhooks/flutterwave/', FlutterwaveWebhookView.as_view(), name='flw-webhook'),
]
