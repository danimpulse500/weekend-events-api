from django.urls import path
from .views import (
    EventListView,
    EventDetailView,
    EventAdminListView,
    EventCreateView,
    EventManageDetailView,
)

urlpatterns = [
    path('events/', EventListView.as_view(), name='event-list'),
    path('events/admin/', EventAdminListView.as_view(), name='event-admin-list'),
    path('events/admin/create/', EventCreateView.as_view(), name='event-create'),
    path('events/admin/<uuid:pk>/', EventManageDetailView.as_view(), name='event-manage-detail'),
    path('events/<slug:slug>/', EventDetailView.as_view(), name='event-detail'),
]
