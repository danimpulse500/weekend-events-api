from django.conf import settings
from django.db import models
from apps.events.models import Event
import uuid
import random
import string


def get_storage_image_field(name, upload_to=None, folder=None):
    if getattr(settings, 'USE_CLOUDINARY', False):
        from cloudinary.models import CloudinaryField
        return CloudinaryField(name, folder=folder, null=True, blank=True)
    return models.ImageField(upload_to=upload_to, null=True, blank=True)


def generate_ticket_ref():
    """Generate a human-readable ticket reference like EVNT-2026-XYZ987"""
    chars = string.ascii_uppercase + string.digits
    suffix = ''.join(random.choices(chars, k=6))
    from django.utils import timezone
    year = timezone.now().year
    return f'EVNT-{year}-{suffix}'


class TicketType(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='ticket_types')
    name = models.CharField(max_length=100)  # e.g. "Gold", "Elite Table"
    price = models.DecimalField(max_digits=10, decimal_places=2)
    capacity = models.PositiveIntegerField(help_text='Max tickets for this type')
    description = models.TextField(blank=True, help_text='Perks, inclusions, etc.')
    order = models.PositiveIntegerField(default=0, help_text='Display order (lowest first)')

    class Meta:
        ordering = ['order', 'price']
        verbose_name = 'Ticket Type'
        verbose_name_plural = 'Ticket Types'

    def __str__(self):
        return f'{self.name} — {self.event.title}'

    @property
    def tickets_sold(self):
        return self.tickets.filter(status='confirmed').count()

    @property
    def tickets_remaining(self):
        return self.capacity - self.tickets_sold

    @property
    def is_available(self):
        return self.tickets_remaining > 0


class Ticket(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending Payment'
        CONFIRMED = 'confirmed', 'Confirmed'
        SCANNED = 'scanned', 'Scanned at Door'
        CANCELLED = 'cancelled', 'Cancelled'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference = models.CharField(max_length=20, unique=True, default=generate_ticket_ref, editable=False)
    event = models.ForeignKey(Event, on_delete=models.PROTECT, related_name='tickets')

    # Buyer info
    buyer_name = models.CharField(max_length=255)
    buyer_email = models.EmailField()
    buyer_phone = models.CharField(max_length=20, blank=True)

    # Add this field to Ticket, after buyer_phone
    ticket_type = models.ForeignKey(
        'TicketType',
        on_delete=models.PROTECT,
        related_name='tickets',
        null=True, blank=True
    )

    # Payment
    flutterwave_tx_ref = models.CharField(max_length=255, blank=True, db_index=True)
    flutterwave_tx_id = models.CharField(max_length=255, blank=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # QR
    qr_code = get_storage_image_field('qr_code', upload_to='qr_codes/', folder='qr_codes')

    # Status
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    scanned_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'

    def __str__(self):
        return f'{self.reference} — {self.buyer_name} ({self.event.title})'
