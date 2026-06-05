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

    payload = {
        'tx_ref': tx_ref,
        'amount': str(ticket.event.entry_fee),
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
        },
        'customizations': {
            'title': ticket.event.title,
            'description': f'Ticket for {ticket.event.title}',
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
