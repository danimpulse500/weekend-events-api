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
        <div style="font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 520px; margin: 0 auto; background: #0f0f0f; border-radius: 16px; overflow: hidden; color: #fff;">

        <!-- Top confirmation header -->
        <div style="padding: 28px 32px 0; text-align: center;">
            <div style="display: inline-block; width: 48px; height: 48px; border-radius: 50%; border: 2px solid #b39753; line-height: 44px; font-size: 22px; color: #b39753; margin-bottom: 12px;">✓</div>
            <h1 style="margin: 0 0 4px; font-size: 20px; font-weight: 700; color: #fff; letter-spacing: 0.3px;">Booking Confirmed</h1>
            <p style="margin: 0 0 28px; font-size: 14px; color: #666;">Your ticket has been reserved</p>
        </div>

        <!-- Ticket Card -->
        <div style="margin: 0 24px 24px; border-radius: 12px; overflow: hidden; border: 1px solid #2a2a2a; background: #1a1a1a;">

            <!-- TC Top — Gold header -->
            <div style="background: linear-gradient(135deg, #b39753 0%, #8b7641 60%, #6b5930 100%); padding: 24px;">
            <div style="font-size: 10px; letter-spacing: 3px; color: rgba(255,255,255,0.6); text-transform: uppercase; font-family: 'Courier New', monospace; margin-bottom: 8px;">CONFIRMED TICKET</div>
            <div style="font-size: 21px; font-weight: 700; color: #fff; line-height: 1.2; margin-bottom: 6px;">{event.title}</div>
            <div style="font-size: 13px; color: rgba(255,255,255,0.7);">{event.date.strftime("%A, %d %B %Y")} &middot; {event.venue}</div>
            <!-- Decorative rule -->
            <div style="display: flex; align-items: center; gap: 8px; margin-top: 16px;">
                <div style="flex: 1; height: 1px; background: rgba(255,255,255,0.25);"></div>
                <div style="width: 7px; height: 7px; background: rgba(255,255,255,0.55); transform: rotate(45deg);"></div>
                <div style="flex: 1; height: 1px; background: rgba(255,255,255,0.25);"></div>
            </div>
            </div>

            <!-- TC Mid — Attendee + ref grid -->
            <div style="padding: 20px 24px; border-bottom: 1px solid #2a2a2a;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                <td style="padding: 0 0 16px; width: 50%; vertical-align: top;">
                    <div style="font-size: 10px; letter-spacing: 2px; color: #555; text-transform: uppercase; font-family: 'Courier New', monospace; margin-bottom: 4px;">Attendee</div>
                    <div style="font-size: 14px; color: #e8dcc8; font-weight: 500;">{ticket.buyer_name}</div>
                </td>
                <td style="padding: 0 0 16px; width: 50%; vertical-align: top;">
                    <div style="font-size: 10px; letter-spacing: 2px; color: #555; text-transform: uppercase; font-family: 'Courier New', monospace; margin-bottom: 4px;">Ticket Ref</div>
                    <div style="font-size: 12px; color: #b39753; font-family: 'Courier New', monospace; word-break: break-all;">{ticket.reference}</div>
                </td>
                </tr>
                <tr>
                <td style="padding: 0; vertical-align: top;">
                    <div style="font-size: 10px; letter-spacing: 2px; color: #555; text-transform: uppercase; font-family: 'Courier New', monospace; margin-bottom: 4px;">Date</div>
                    <div style="font-size: 14px; color: #e8dcc8; font-weight: 500;">{event.date.strftime("%a, %d %b %Y")}</div>
                </td>
                <td style="padding: 0; vertical-align: top;">
                    <div style="font-size: 10px; letter-spacing: 2px; color: #555; text-transform: uppercase; font-family: 'Courier New', monospace; margin-bottom: 4px;">Status</div>
                    <div style="display: inline-block; background: rgba(74,222,128,0.10); color: #4ade80; border: 1px solid rgba(74,222,128,0.25); border-radius: 20px; font-size: 11px; padding: 2px 10px; font-family: 'Courier New', monospace; letter-spacing: 1px; text-transform: uppercase;">Confirmed</div>
                </td>
                </tr>
            </table>
            </div>

            <!-- TC Divider notch row (simulated with border only — email-safe) -->
            <div style="border-top: 1px dashed #2e2e2e; margin: 0 0;"></div>

            <!-- TC Bottom — Ticket ID + QR -->
            <div style="padding: 20px 24px; text-align: center;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;">
                <div style="text-align: left;">
                <div style="font-size: 9px; letter-spacing: 2px; color: #555; text-transform: uppercase; font-family: 'Courier New', monospace; margin-bottom: 4px;">Ticket ID</div>
                <div style="font-size: 26px; font-weight: 700; color: #b39753; letter-spacing: 2px;">{ticket.reference.split('-')[-1]}</div>
                </div>
                <div style="font-size: 10px; color: #444; text-align: right; text-transform: uppercase; letter-spacing: 1px; font-family: 'Courier New', monospace; line-height: 1.5;">Scan at<br>check-in</div>
            </div>

            <!-- QR Code (inline attachment) -->
            <div style="display: inline-block; border: 2px solid #b39753; border-radius: 8px; padding: 4px; background: #fff; margin-bottom: 12px;">
                <img src="cid:qrcode" width="148" height="148" style="display: block;" alt="QR Code" />
            </div>

            <div style="font-family: 'Courier New', monospace; font-size: 11px; color: #444; letter-spacing: 2px; margin-bottom: 20px;">{ticket.reference}</div>

            <!-- CTA Button -->
            <a href="#" style="display: inline-block; border: 1px solid #b39753; color: #b39753; border-radius: 6px; padding: 10px 28px; font-size: 13px; text-decoration: none; letter-spacing: 0.5px;">View / Download Ticket</a>
            </div>
        </div>

        <!-- Footer notice -->
        <div style="padding: 0 24px 24px;">
            <div style="background: #141414; border-radius: 8px; padding: 14px 16px; text-align: center; border: 1px solid #1e1e1e;">
            <p style="margin: 0; font-size: 12px; color: #555; line-height: 1.6;">
                This ticket is non-transferable. Screenshot or print the QR code for offline access.<br/>
                Questions? Reply to this email.
            </p>
            </div>
            <p style="margin: 16px 0 0; text-align: center; font-size: 11px; color: #333;">{settings.FROM_NAME} &middot; Powered by Weekend Events</p>
        </div>

        </div>
        """
    
    message = Mail(
        from_email=(settings.DEFAULT_FROM_EMAIL, settings.FROM_NAME),
        to_emails=ticket.buyer_email,
        subject=f'See you at {event.title} — {ticket.reference}',
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
