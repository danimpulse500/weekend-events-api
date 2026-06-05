from django.contrib import admin
from django.utils.html import format_html
from .models import WebhookLog


@admin.register(WebhookLog)
class WebhookLogAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'tx_ref', 'processed_badge', 'error_preview', 'created_at']
    list_filter = ['processed', 'event_type']
    search_fields = ['tx_ref', 'tx_id']
    readonly_fields = ['id', 'event_type', 'tx_ref', 'tx_id', 'payload', 'processed', 'error', 'created_at']
    ordering = ['-created_at']

    def processed_badge(self, obj):
        if obj.processed:
            return format_html('<span style="color: #28a745; font-weight: bold;">✅ Yes</span>')
        return format_html('<span style="color: #dc3545; font-weight: bold;">❌ No</span>')
    processed_badge.short_description = 'Processed'

    def error_preview(self, obj):
        if obj.error:
            return format_html('<span style="color: #dc3545;">{}</span>', obj.error[:80])
        return '—'
    error_preview.short_description = 'Error'

    def has_add_permission(self, request):
        return False  # Logs are system-generated only
