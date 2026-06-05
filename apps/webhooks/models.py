from django.db import models
import uuid


class WebhookLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=100, blank=True)
    tx_ref = models.CharField(max_length=255, blank=True)
    tx_id = models.CharField(max_length=255, blank=True)
    payload = models.JSONField(default=dict)
    processed = models.BooleanField(default=False)
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Webhook Log'
        verbose_name_plural = 'Webhook Logs'

    def __str__(self):
        status = '✅' if self.processed else '❌'
        return f'{status} {self.event_type} — {self.tx_ref}'
