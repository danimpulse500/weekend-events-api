import uuid
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class Event(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
        SOLD_OUT = 'sold_out', 'Sold Out'
        CANCELLED = 'cancelled', 'Cancelled'
        COMPLETED = 'completed', 'Completed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=300, unique=True, blank=True)
    description = models.TextField(blank=True)
    flyer = models.ImageField(upload_to='event_flyers/', null=True, blank=True)
    venue = models.CharField(max_length=255)
    date = models.DateTimeField()
    
    capacity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text='Maximum number of physical individual attendees the venue can hold'
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        verbose_name = 'Event'
        verbose_name_plural = 'Events'

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Event.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.title} — {self.date.strftime("%d %b %Y")}'

    @property
    def total_seats_booked(self):
        """Sums up actual individual headcount filled across all ticket tiers."""
        return sum(tier.total_seats_occupied for tier in self.ticket_types.all())

    @property
    def tickets_remaining(self):
        """Returns remaining physical seat capacity for the venue."""
        if self.capacity is None:
            return 0
        return max(0, self.capacity - self.total_seats_booked)

    @property
    def is_available(self):
        return (
            self.status == self.Status.PUBLISHED
            and self.tickets_remaining > 0
            and self.date > timezone.now()
        )

    @property
    def min_price(self):
        """Dynamically fetches the lowest ticket price option available for this event."""
        cheapest = self.ticket_types.order_by('price').first()
        return cheapest.price if cheapest else 0

    @property
    def is_free(self):
        """Returns True if the cheapest ticket type is 0, or if no tickets exist yet."""
        cheapest = self.ticket_types.order_by('price').first()
        if cheapest:
            return cheapest.price == 0
        return True