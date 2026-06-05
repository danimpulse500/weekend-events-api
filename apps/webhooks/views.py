import hashlib
import hmac
import json
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from apps.tickets.models import Ticket
from apps.tickets.payment import verify_transaction
from apps.tickets.tasks import process_confirmed_ticket
from .models import WebhookLog


@method_decorator(csrf_exempt, name='dispatch')
class FlutterwaveWebhookView(APIView):
    """
    Receives Flutterwave payment events.
    Validates the secret hash header, verifies the transaction server-side,
    then confirms the ticket and triggers QR + email delivery.
    """
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        tags=['Webhooks'],
        summary='Flutterwave payment webhook',
        description=(
            'Called by Flutterwave after payment. Validates `verif-hash` header, '
            'verifies transaction with Flutterwave API, confirms ticket, '
            'generates QR code, and sends email. **Do not call this manually.**'
        ),
        responses={200: None, 400: None}
    )
    def post(self, request):
        # 1. Validate secret hash
        secret_hash = settings.FLUTTERWAVE_SECRET_HASH
        signature = request.headers.get('verif-hash', '')

        if secret_hash and not hmac.compare_digest(signature, secret_hash):
            return Response({'error': 'Invalid signature'}, status=status.HTTP_401_UNAUTHORIZED)

        payload = request.data
        tx_ref = payload.get('data', {}).get('tx_ref', '')
        tx_id = str(payload.get('data', {}).get('id', ''))
        event_type = payload.get('event', 'unknown')

        # Log it regardless
        log = WebhookLog.objects.create(
            event_type=event_type,
            tx_ref=tx_ref,
            tx_id=tx_id,
            payload=payload,
        )

        # We only care about successful charges
        if event_type != 'charge.completed':
            log.error = f'Ignored event type: {event_type}'
            log.save(update_fields=['error'])
            return Response({'message': 'Event ignored'}, status=status.HTTP_200_OK)

        try:
            with transaction.atomic():
                # Find the pending ticket
                ticket = Ticket.objects.select_for_update().get(
                    flutterwave_tx_ref=tx_ref,
                    status=Ticket.Status.PENDING,
                )

                # Verify with Flutterwave (never trust the webhook payload alone)
                tx_data = verify_transaction(tx_id)

                if tx_data.get('status') != 'successful':
                    raise ValueError(f'Transaction not successful: {tx_data.get("status")}')

                # Confirm ticket
                ticket.status = Ticket.Status.CONFIRMED
                ticket.flutterwave_tx_id = tx_id
                ticket.amount_paid = tx_data.get('amount', 0)
                ticket.save(update_fields=['status', 'flutterwave_tx_id', 'amount_paid'])

                log.processed = True
                log.save(update_fields=['processed'])

            # Trigger async: QR generation + email (outside transaction)
            process_confirmed_ticket.delay(str(ticket.id))

        except Ticket.DoesNotExist:
            log.error = f'No pending ticket found for tx_ref: {tx_ref}'
            log.save(update_fields=['error'])
            # Return 200 so Flutterwave doesn't retry infinitely
            return Response({'message': 'Ticket not found or already processed'}, status=status.HTTP_200_OK)

        except Exception as e:
            log.error = str(e)
            log.save(update_fields=['error'])
            return Response({'error': 'Processing failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'message': 'Ticket confirmed'}, status=status.HTTP_200_OK)
