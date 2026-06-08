import requests
import uuid
from django.conf import settings

FLUTTERWAVE_BASE_URL = settings.FLUTTERWAVE_BASE_URL


def initialize_payment(ticket, redirect_url: str) -> dict:
    """
    Initialize a Flutterwave payment for a ticket.
    Returns the payment link or raises on failure.
    """
    tx_ref = f'EVT-{ticket.reference}-{uuid.uuid4().hex[:8].upper()}'

    # CRITICAL FIX: Ensure a ticket type exists, otherwise default price calculation to 0.00
    if not ticket.ticket_type:
        raise ValueError(f"Ticket {ticket.reference} is missing a assigned Ticket Type tier configuration.")

    payload = {
        'tx_ref': tx_ref,
        'amount': str(ticket.ticket_type.price),  # Cleaned: Pulled directly from the selected tier
        'currency': 'NGN',
        'redirect_url': redirect_url,
        'customer': {
            'email': ticket.buyer_email,
            'name': ticket.buyer_name,
            'phonenumber': ticket.buyer_phone or '',
        },
        'meta': {
            'ticket_id': str(ticket.id),
            'event_id': str(ticket.event.id),
            'ticket_type_id': str(ticket.ticket_type.id),  # Added to meta tracking logs
        },
        'customizations': {
            'title': ticket.event.title,
            'description': f'{ticket.ticket_type.name} Ticket for {ticket.event.title}',  # Dynamic description
            'logo': '',
        },
    }

    headers = {
        'Authorization': f'Bearer {settings.FLUTTERWAVE_SECRET_KEY}',
        'Content-Type': 'application/json',
    }

    response = requests.post(
        f'{FLUTTERWAVE_BASE_URL}/payments',
        json=payload,
        headers=headers,
        timeout=15,
    )
    data = response.json()

    if data.get('status') != 'success':
        raise ValueError(f'Flutterwave error: {data.get("message", "Unknown error")}')

    return {
        'tx_ref': tx_ref,
        'payment_link': data['data']['link'],
    }


def verify_transaction(tx_id: str) -> dict:
    """
    Verify a Flutterwave transaction by ID.
    Returns transaction data dict or raises on failure.
    """
    headers = {
        'Authorization': f'Bearer {settings.FLUTTERWAVE_SECRET_KEY}',
        'Content-Type': 'application/json',
    }

    response = requests.get(
        f'{FLUTTERWAVE_BASE_URL}/transactions/{tx_id}/verify',
        headers=headers,
        timeout=15,
    )
    data = response.json()

    if data.get('status') != 'success':
        raise ValueError(f'Verification failed: {data.get("message", "Unknown error")}')

    return data['data']