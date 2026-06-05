from rest_framework import serializers
from apps.events.models import Event
from .models import Ticket


class InitiateTicketSerializer(serializers.Serializer):
    event_slug = serializers.SlugField()
    buyer_name = serializers.CharField(max_length=255)
    buyer_email = serializers.EmailField()
    buyer_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)

    def validate_event_slug(self, value):
        try:
            event = Event.objects.get(slug=value, status=Event.Status.PUBLISHED)
        except Event.DoesNotExist:
            raise serializers.ValidationError('Event not found or not available.')

        if not event.is_available:
            raise serializers.ValidationError(
                'This event is sold out or no longer accepting tickets.'
            )
        self.context['event'] = event
        return value


class TicketSerializer(serializers.ModelSerializer):
    event_title = serializers.CharField(source='event.title', read_only=True)
    event_slug = serializers.SlugField(source='event.slug', read_only=True)
    event_date = serializers.DateTimeField(source='event.date', read_only=True)
    event_venue = serializers.CharField(source='event.venue', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    qr_code = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = [
            'id', 'reference', 'event_title', 'event_slug', 'event_date', 'event_venue',
            'buyer_name', 'buyer_email', 'amount_paid', 'status', 'status_display',
            'qr_code', 'scanned_at', 'created_at',
        ]
        read_only_fields = fields

    def get_qr_code(self, obj):
        if not obj.qr_code:
            return None
        try:
            url = obj.qr_code.url
        except Exception:
            return None
        if url.startswith('http://') or url.startswith('https://'):
            return url
        request = self.context.get('request')
        return request.build_absolute_uri(url) if request and url else url


class VerifyTicketSerializer(serializers.Serializer):
    reference = serializers.CharField(
        help_text='Ticket reference code scanned from QR (e.g. EVNT-2026-XYZ987)'
    )
