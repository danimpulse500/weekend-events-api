from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.utils.text import slugify
import uuid


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
    entry_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Set to 0 for free events'
    )
    capacity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text='Maximum number of attendees'
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
    def tickets_sold(self):
        return self.tickets.filter(status='confirmed').count()

    @property
    def tickets_remaining(self):
        if self.capacity is None:
            return 0
        return self.capacity - self.tickets_sold

    @property
    def is_available(self):
        return (
            self.status == self.Status.PUBLISHED
            and self.tickets_remaining > 0
            and self.date > timezone.now()
        )

    @property
    def is_free(self):
        return self.entry_fee == 0
