from django.urls import path
from .views import InitiateTicketView, VerifyTicketView, TicketDetailView, TicketListView

urlpatterns = [
    path('tickets/', TicketListView.as_view(), name='ticket-list'),
    path('tickets/purchase/', InitiateTicketView.as_view(), name='ticket-purchase'),
    path('tickets/verify/', VerifyTicketView.as_view(), name='ticket-verify'),
    path('tickets/<str:reference>/', TicketDetailView.as_view(), name='ticket-detail'),
]
