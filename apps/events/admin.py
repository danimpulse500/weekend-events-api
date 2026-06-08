from django.contrib import admin
from django.utils.html import format_html
from .models import Event
from apps.tickets.models import TicketType


class TicketTypeInline(admin.TabularInline):
    model = TicketType
    extra = 1
    # UPDATED: Added tier and seats_per_ticket fields
    fields = ['tier', 'name', 'price', 'capacity', 'seats_per_ticket', 'description', 'order']


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    inlines = [TicketTypeInline]

    # UPDATED: Removed 'entry_fee', added 'min_price_display'
    list_display = [
        'title', 'venue', 'date', 'min_price_display',
        'capacity_display', 'status_badge', 'created_at'
    ]
    list_filter = ['status', 'date']
    search_fields = ['title', 'venue']
    readonly_fields = ['id', 'slug', 'tickets_sold', 'tickets_remaining', 'created_at', 'updated_at', 'flyer_preview']
    ordering = ['-date']
    date_hierarchy = 'date'

    # UPDATED: Removed 'entry_fee' from Logistics
    fieldsets = (
        ('Event Info', {
            'fields': ('id', 'title', 'slug', 'description', 'flyer', 'flyer_preview')
        }),
        ('Logistics', {
            'fields': ('venue', 'date', 'capacity')
        }),
        ('Status & Stats', {
            'fields': ('status', 'tickets_sold', 'tickets_remaining')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def min_price_display(self, obj):
        """Displays the lowest available ticket price on the dashboard."""
        price = obj.min_price
        if price == 0:
            return format_html('<span style="color: #28a745; font-weight: bold;">Free</span>')
        return f"₦{price:,.2f}"
    min_price_display.short_description = 'Starting Price'

    def capacity_display(self, obj):
        # UPDATED: Uses total_seats_booked to respect multi-seat/table ticket data accurately
        booked = obj.total_seats_booked
        pct = (booked / obj.capacity * 100) if obj.capacity else 0
        color = '#28a745' if pct < 75 else '#ffc107' if pct < 95 else '#dc3545'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} / {}</span>',
            color, booked, obj.capacity
        )
    capacity_display.short_description = 'Seats Filled / Capacity'

    def status_badge(self, obj):
        colors = {
            'draft': '#6c757d',
            'published': '#28a745',
            'sold_out': '#dc3545',
            'cancelled': '#343a40',
            'completed': '#17a2b8',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background:{}; color:white; padding:2px 8px; border-radius:10px; font-size:11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def flyer_preview(self, obj):
        if obj.flyer:
            return format_html('<img src="{}" style="max-height: 200px; border-radius: 8px;" />', obj.flyer.url)
        return '—'
    flyer_preview.short_description = 'Flyer Preview'

    # Add this method inside your EventAdmin class (e.g., right under capacity_display)
    def tickets_sold(self, obj):
        """Calculates total raw confirmed ticket transactions issued for this event."""
        return obj.tickets.filter(status='confirmed').count()
    tickets_sold.short_description = 'Tickets Sold (Transactions)'