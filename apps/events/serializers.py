from rest_framework import serializers
from .models import Event


class EventListSerializer(serializers.ModelSerializer):
    flyer = serializers.SerializerMethodField()
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

    def get_flyer(self, obj):
        if not obj.flyer:
            return None
        try:
            url = obj.flyer.url
        except Exception:
            return None
        if url.startswith('http://') or url.startswith('https://'):
            return url
        request = self.context.get('request')
        return request.build_absolute_uri(url) if request and url else url


class EventDetailSerializer(EventListSerializer):
    tickets_sold = serializers.IntegerField(read_only=True)

    class Meta(EventListSerializer.Meta):
        fields = EventListSerializer.Meta.fields + ['description', 'tickets_sold', 'created_at']
