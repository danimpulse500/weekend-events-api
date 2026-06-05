from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from rest_framework import generics, filters
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .models import Event
from .serializers import EventListSerializer, EventDetailSerializer


@extend_schema(
    tags=['Events'],
    summary='List all published events',
    description='Returns a paginated list of all published events, ordered by date.',
    parameters=[
        OpenApiParameter('search', str, description='Search by title or venue'),
    ]
)
class EventListView(generics.ListAPIView):
    serializer_class = EventListSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'venue']

    def get_queryset(self):
        return Event.objects.filter(status=Event.Status.PUBLISHED).order_by('date')


@extend_schema(
    tags=['Events'],
    summary='Get event detail by slug',
    description='Returns full detail for a single event including remaining capacity.'
)
class EventDetailView(generics.RetrieveAPIView):
    serializer_class = EventDetailSerializer
    lookup_field = 'slug'

    def get_queryset(self):
        return Event.objects.filter(status=Event.Status.PUBLISHED)


@extend_schema(
    tags=['Events'],
    summary='List all events for the organizer dashboard',
    description='Returns all events, with optional status filtering and search.',
    parameters=[
        OpenApiParameter('status', str, description='Filter by event status'),
        OpenApiParameter('search', str, description='Search by title or venue'),
    ]
)
class EventAdminListView(generics.ListAPIView):
    serializer_class = EventDetailSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'venue']

    def get_queryset(self):
        queryset = Event.objects.all().order_by('-date')
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset


@extend_schema(
    tags=['Events'],
    summary='Create a new event',
    description='Create an event for the dashboard admin.',
    request=EventDetailSerializer,
    responses={201: EventDetailSerializer},
)
class EventCreateView(generics.CreateAPIView):
    serializer_class = EventDetailSerializer
    queryset = Event.objects.all()
    parser_classes = [JSONParser, FormParser, MultiPartParser]


@extend_schema(
    tags=['Events'],
    summary='Retrieve, update, or delete an event by ID',
    description='Manage an event using its UUID.',
)
class EventManageDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = EventDetailSerializer
    queryset = Event.objects.all()
    lookup_field = 'pk'
    parser_classes = [JSONParser, FormParser, MultiPartParser]


@login_required
def dashboard_view(request):
    return render(request, 'dashboard.html')
