import qrcode
import json
import base64
import io
from io import BytesIO
from django.core.files import File
from django.conf import settings
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Attachment, FileContent, FileName,
    FileType, Disposition, ContentId
)


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


def _qr_to_data_uri(reference: str) -> str:
    """
    Generate a QR code from the ticket reference and return it as a
    base64 data URI suitable for embedding directly in HTML email.
    Avoids cid: inline attachment issues in Gmail and other clients.
    """
    payload = json.dumps({'ref': reference})

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    qr.add_data(payload)
    qr.make(fit=True)

    img = qr.make_image(fill_color='black', back_color='white')
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    encoded = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{encoded}"


def send_ticket_email(ticket):
    """
    Send ticket confirmation email with QR code embedded as a data URI
    (renders inline in all major clients) plus a downloadable PNG attachment.
    """
    if not settings.SENDGRID_API_KEY:
        print(f'[EMAIL SKIPPED] No SendGrid key — ticket {ticket.reference}')
        return

    event = ticket.event
    qr_data_uri = _qr_to_data_uri(ticket.reference)
    ticket_id = ticket.reference.split('-')[-1]

    html_content = f"""
    <div style="font-family: 'Helvetica Neue', Arial, sans-serif; max-width: 520px; margin: 0 auto; background: #0f0f0f; border-radius: 16px; overflow: hidden; color: #fff;">

        <!-- Top confirmation header -->
        <div style="padding: 28px 32px 0; text-align: center;">
            <div style="display: inline-block; width: 48px; height: 48px; border-radius: 50%; border: 2px solid #b39753; line-height: 44px; font-size: 22px; color: #b39753; margin-bottom: 12px;">&#10003;</div>
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
                <table style="width: 100%; margin-top: 16px; border-collapse: collapse;">
                    <tr>
                        <td style="height: 1px; background: rgba(255,255,255,0.25);"></td>
                        <td style="width: 14px; text-align: center; font-size: 8px; color: rgba(255,255,255,0.55);">&#9670;</td>
                        <td style="height: 1px; background: rgba(255,255,255,0.25);"></td>
                    </tr>
                </table>
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

            <!-- TC Divider -->
            <div style="border-top: 1px dashed #2e2e2e;"></div>

            <!-- TC Bottom — Ticket ID + QR -->
            <div style="padding: 20px 24px; text-align: center;">
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 16px;">
                    <tr>
                        <td style="text-align: left; vertical-align: middle;">
                            <div style="font-size: 9px; letter-spacing: 2px; color: #555; text-transform: uppercase; font-family: 'Courier New', monospace; margin-bottom: 4px;">Ticket ID</div>
                            <div style="font-size: 26px; font-weight: 700; color: #b39753; letter-spacing: 2px;">{ticket_id}</div>
                        </td>
                        <td style="text-align: right; vertical-align: middle; font-size: 10px; color: #444; text-transform: uppercase; letter-spacing: 1px; font-family: 'Courier New', monospace; line-height: 1.5;">Scan at<br>check-in</td>
                    </tr>
                </table>

                <!-- QR Code — embedded as data URI, renders in all clients -->
                <div style="display: inline-block; border: 2px solid #b39753; border-radius: 8px; padding: 4px; background: #fff; margin-bottom: 12px;">
                    <img src="{qr_data_uri}" width="148" height="148" style="display: block;" alt="QR Code for {ticket.reference}" />
                </div>

                <div style="font-family: 'Courier New', monospace; font-size: 11px; color: #444; letter-spacing: 2px; margin-bottom: 0;">{ticket.reference}</div>
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

    # Attach QR as a downloadable file (separate from the embedded one above)
    if ticket.qr_code:
        with open(ticket.qr_code.path, 'rb') as f:
            qr_bytes = f.read()

        encoded = base64.b64encode(qr_bytes).decode()
        attachment = Attachment(
            FileContent(encoded),
            FileName(f'ticket_{ticket.reference}.png'),
            FileType('image/png'),
            Disposition('attachment'),  # downloadable, not inline
        )
        message.attachment = attachment

    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        print(f'[EMAIL SENT] {ticket.buyer_email} — status {response.status_code}')
    except Exception as e:
        print(f'[EMAIL ERROR] {ticket.reference}: {e}')