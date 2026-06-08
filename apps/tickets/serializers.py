from rest_framework import serializers
from apps.events.models import Event
from .models import Ticket, TicketType

class TicketTypeSerializer(serializers.ModelSerializer):
    tickets_remaining = serializers.IntegerField(read_only=True)
    is_available = serializers.BooleanField(read_only=True)
    tier_display = serializers.CharField(source='get_tier_display', read_only=True)

    class Meta:
        model = TicketType
        fields = [
            'id', 'tier', 'tier_display', 'name', 'price', 'capacity', 
            'seats_per_ticket', 'description', 'tickets_remaining', 
            'is_available', 'order'
        ]


class InitiateTicketSerializer(serializers.Serializer):
    event_slug = serializers.SlugField()
    buyer_name = serializers.CharField(max_length=255)
    buyer_email = serializers.EmailField()
    buyer_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    
    # Changed to Field to dynamically handle either UUID or Integer depending on your DB setup
    ticket_type_id = serializers.UUIDField(help_text='ID of the ticket type selected')

    def validate(self, data):
        event = self.context.get('event')
        if not event:
            raise serializers.ValidationError({'event_slug': 'Event context missing.'})
            
        ticket_type_id = data.get('ticket_type_id')

        # 1. Verify the ticket type belongs to this specific event
        try:
            ticket_type = TicketType.objects.get(id=ticket_type_id, event=event)
        except TicketType.DoesNotExist:
            raise serializers.ValidationError({'ticket_type_id': 'Invalid ticket type for this event.'})

        # 2. Check if this specific tier choice is sold out
        if not ticket_type.is_available:
            raise serializers.ValidationError({'ticket_type_id': f'{ticket_type.name} tickets are sold out.'})

        # 3. CRITICAL: Verify if the venue capacity can handle this ticket's seat weight
        if event.tickets_remaining < ticket_type.seats_per_ticket:
            raise serializers.ValidationError({
                'ticket_type_id': f'Cannot issue ticket. Only {event.tickets_remaining} seats remaining at the venue.'
            })

        self.context['ticket_type'] = ticket_type
        return data


class TicketSerializer(serializers.ModelSerializer):
    ticket_type_name = serializers.CharField(source='ticket_type.name', read_only=True)
    ticket_type_tier = serializers.CharField(source='ticket_type.tier', read_only=True)
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
            'buyer_name', 'buyer_email', 'buyer_phone', 'amount_paid', 'status', 'status_display',
            'ticket_type_tier', 'ticket_type_name', 'qr_code', 'scanned_at', 'created_at',
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