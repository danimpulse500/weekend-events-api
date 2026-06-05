from celery import shared_task
from django.db import transaction


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def process_confirmed_ticket(self, ticket_id):
    """
    After payment is confirmed:
    1. Generate QR code
    2. Save ticket
    3. Send email
    """
    from apps.tickets.models import Ticket
    from apps.tickets.utils import generate_qr_code, send_ticket_email

    try:
        ticket = Ticket.objects.select_related('event').get(id=ticket_id)

        with transaction.atomic():
            generate_qr_code(ticket)
            ticket.save(update_fields=['qr_code'])

        send_ticket_email(ticket)

    except Ticket.DoesNotExist:
        print(f'[TASK ERROR] Ticket {ticket_id} not found')
    except Exception as exc:
        raise self.retry(exc=exc)
