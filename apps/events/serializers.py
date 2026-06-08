from rest_framework import serializers
from apps.events.models import Event
from apps.tickets.serializers import TicketTypeSerializer  # Import the nested serializer choice

class EventListSerializer(serializers.ModelSerializer):
    flyer = serializers.SerializerMethodField()
    tickets_remaining = serializers.IntegerField(read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    is_free = serializers.BooleanField(read_only=True)
    min_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)  # NEW: Expose cheapest option

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'slug', 'flyer', 'venue', 'date', 
            'min_price', 'capacity', 'tickets_remaining',
            'is_available', 'is_free', 'status',
        ]

    def get_flyer(self, obj):
        if not obj.flyer:
            return None
            
        try:
            if hasattr(obj.flyer, 'instance') and hasattr(obj.flyer, 'url'):
                url = obj.flyer.storage.url(obj.flyer.name)
            else:
                url = obj.flyer.url
        except Exception:
            return None

        if url.startswith('http://') or url.startswith('https://'):
            return url

        request = self.context.get('request')
        if request and url:
            return request.build_absolute_uri(url)
        return f"/media/{url.lstrip('/')}" if url else None


class EventDetailSerializer(EventListSerializer):
    tickets_sold = serializers.IntegerField(read_only=True)
    ticket_types = TicketTypeSerializer(many=True, read_only=True)  # NEW: Embed nested choices for the details layout

    class Meta(EventListSerializer.Meta):
        fields = EventListSerializer.Meta.fields + [
            'description', 'tickets_sold', 'ticket_types', 'created_at'
        ]