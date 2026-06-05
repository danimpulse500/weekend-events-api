from django.contrib import admin
from django.utils.html import format_html
from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'venue', 'date', 'entry_fee',
        'capacity_display', 'status_badge', 'created_at'
    ]
    list_filter = ['status', 'date']
    search_fields = ['title', 'venue']
    readonly_fields = ['id', 'slug', 'tickets_sold', 'tickets_remaining', 'created_at', 'updated_at', 'flyer_preview']
    ordering = ['-date']
    date_hierarchy = 'date'

    fieldsets = (
        ('Event Info', {
            'fields': ('id', 'title', 'slug', 'description', 'flyer', 'flyer_preview')
        }),
        ('Logistics', {
            'fields': ('venue', 'date', 'entry_fee', 'capacity')
        }),
        ('Status & Stats', {
            'fields': ('status', 'tickets_sold', 'tickets_remaining')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def capacity_display(self, obj):
        sold = obj.tickets_sold
        pct = (sold / obj.capacity * 100) if obj.capacity else 0
        color = '#28a745' if pct < 75 else '#ffc107' if pct < 95 else '#dc3545'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} / {}</span>',
            color, sold, obj.capacity
        )
    capacity_display.short_description = 'Sold / Capacity'

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
