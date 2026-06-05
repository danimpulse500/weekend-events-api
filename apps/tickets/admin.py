from django.contrib import admin
from django.utils.html import format_html
from .models import Ticket


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = [
        'reference', 'buyer_name', 'buyer_email',
        'event', 'amount_paid', 'status_badge', 'created_at'
    ]
    list_filter = ['status', 'event', 'created_at']
    search_fields = ['reference', 'buyer_name', 'buyer_email', 'flutterwave_tx_ref']
    readonly_fields = [
        'id', 'reference', 'flutterwave_tx_ref', 'flutterwave_tx_id',
        'qr_preview', 'scanned_at', 'created_at', 'updated_at'
    ]
    ordering = ['-created_at']

    fieldsets = (
        ('Ticket', {
            'fields': ('id', 'reference', 'event', 'status')
        }),
        ('Buyer', {
            'fields': ('buyer_name', 'buyer_email', 'buyer_phone')
        }),
        ('Payment', {
            'fields': ('amount_paid', 'flutterwave_tx_ref', 'flutterwave_tx_id')
        }),
        ('QR Code', {
            'fields': ('qr_code', 'qr_preview')
        }),
        ('Scan Info', {
            'fields': ('scanned_at',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'confirmed': '#28a745',
            'scanned': '#17a2b8',
            'cancelled': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background:{}; color:white; padding:2px 8px; border-radius:10px; font-size:11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def qr_preview(self, obj):
        if obj.qr_code:
            return format_html('<img src="{}" style="width:150px; height:150px;" />', obj.qr_code.url)
        return '—'
    qr_preview.short_description = 'QR Code Preview'
