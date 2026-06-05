from rest_framework import serializers
from .models import Event


class EventListSerializer(serializers.ModelSerializer):
    tickets_remaining = serializers.IntegerField(read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    is_free = serializers.BooleanField(read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'slug', 'flyer', 'venue',
            'date', 'entry_fee', 'capacity', 'tickets_remaining',
            'is_available', 'is_free', 'status',
        ]


class EventDetailSerializer(EventListSerializer):
    tickets_sold = serializers.IntegerField(read_only=True)

    class Meta(EventListSerializer.Meta):
        fields = EventListSerializer.Meta.fields + ['description', 'tickets_sold', 'created_at']
