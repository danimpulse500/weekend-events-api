import qrcode
import json
import os
from io import BytesIO
from django.core.files import File
from django.conf import settings
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Attachment, FileContent, FileName,
    FileType, Disposition, ContentId
)
import base64


def generate_qr_code(ticket):
    """
    Generate a QR code image for a ticket.
    Encodes a JSON payload with enough info to verify offline + online.
    """
    payload = json.dumps({
        'ref': ticket.reference,
        'event': str(ticket.event.id),
        'buyer': ticket.buyer_name,
    })

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(payload)
    qr.make(fit=True)

    img = qr.make_image(fill_color='black', back_color='white')
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    file_name = f'qr_{ticket.reference}.png'
    ticket.qr_code.save(file_name, File(buffer), save=False)


def send_ticket_email(ticket):
    """
    Send ticket confirmation email with QR code attachment via SendGrid.
    """
    if not settings.SENDGRID_API_KEY:
        print(f'[EMAIL SKIPPED] No SendGrid key — ticket {ticket.reference}')
        return

    event = ticket.event

    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #0f0f0f; color: #fff; border-radius: 12px; overflow: hidden;">
        <div style="background: linear-gradient(135deg, #6c3de0, #e040fb); padding: 32px; text-align: center;">
            <h1 style="margin: 0; font-size: 28px; letter-spacing: 1px;">🎟️ Your Ticket is Confirmed!</h1>
        </div>
        <div style="padding: 32px;">
            <p style="font-size: 16px; color: #ccc;">Hey <strong style="color: #fff;">{ticket.buyer_name}</strong>, you're all set!</p>

            <div style="background: #1a1a1a; border-radius: 8px; padding: 20px; margin: 20px 0; border-left: 4px solid #6c3de0;">
                <h2 style="margin: 0 0 16px; color: #e040fb;">{event.title}</h2>
                <p style="margin: 6px 0; color: #ccc;">📍 <strong>{event.venue}</strong></p>
                <p style="margin: 6px 0; color: #ccc;">📅 <strong>{event.date.strftime("%A, %d %B %Y at %I:%M %p")}</strong></p>
                <p style="margin: 6px 0; color: #ccc;">🎫 Ticket Ref: <strong style="color: #fff; font-family: monospace; font-size: 18px;">{ticket.reference}</strong></p>
            </div>

            <div style="text-align: center; margin: 24px 0;">
                <p style="color: #ccc; margin-bottom: 12px;">Show this QR code at the entrance:</p>
                <img src="cid:qrcode" style="width: 200px; height: 200px; border: 4px solid #6c3de0; border-radius: 8px;" alt="QR Code" />
            </div>

            <div style="background: #1a1a1a; border-radius: 8px; padding: 16px; text-align: center; margin-top: 24px;">
                <p style="color: #888; font-size: 13px; margin: 0;">
                    This ticket is non-transferable. Screenshot or print the QR code for offline access.
                    <br/>Questions? Reply to this email.
                </p>
            </div>
        </div>
        <div style="background: #1a1a1a; padding: 16px; text-align: center;">
            <p style="color: #555; font-size: 12px; margin: 0;">{settings.FROM_NAME} · Powered by Weekend Events</p>
        </div>
    </div>
    """

    message = Mail(
        from_email=(settings.DEFAULT_FROM_EMAIL, settings.FROM_NAME),
        to_emails=ticket.buyer_email,
        subject=f'🎟️ Your ticket for {event.title} — {ticket.reference}',
        html_content=html_content,
    )

    # Attach QR code as inline image
    if ticket.qr_code:
        with open(ticket.qr_code.path, 'rb') as f:
            qr_data = f.read()

        encoded = base64.b64encode(qr_data).decode()
        attachment = Attachment(
            FileContent(encoded),
            FileName(f'ticket_{ticket.reference}.png'),
            FileType('image/png'),
            Disposition('inline'),
            ContentId('qrcode'),
        )
        message.attachment = attachment

    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        print(f'[EMAIL SENT] {ticket.buyer_email} — status {response.status_code}')
    except Exception as e:
        print(f'[EMAIL ERROR] {ticket.reference}: {e}')
