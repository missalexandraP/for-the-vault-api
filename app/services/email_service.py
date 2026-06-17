"""Email notification service for transactional emails.

Supports SMTP-based sending with templated HTML emails.
In dev mode, prints to console instead of sending.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime
from string import Template

from app.config import settings

logger = logging.getLogger(__name__)


# --- HTML Email Templates ---

WELCOME_EMAIL_TEMPLATE = """
<html>
<body style="font-family: 'Playfair Display', Georgia, serif; color: #1A1A1A; background: #F9F6F0; padding: 40px;">
    <div style="max-width: 600px; margin: 0 auto; background: #FFFFFF; border-radius: 8px; overflow: hidden;">
        <div style="background: #1A1A1A; padding: 30px; text-align: center;">
            <h1 style="color: #D4AF37; margin: 0; font-size: 24px;">The Vault</h1>
            <p style="color: #F9F6F0; margin: 5px 0 0; font-size: 14px;">Luxury Handbag Rentals</p>
        </div>
        <div style="padding: 40px 30px;">
            <h2 style="color: #1A1A1A; font-size: 22px;">Welcome to The Vault, $name!</h2>
            <p style="color: #707070; line-height: 1.6; font-size: 15px;">
                You've been granted access to the world's most extraordinary collection of designer handbags.
                From Hermès to Chanel, each piece in our collection has been rigorously authenticated
                and prepared for your enjoyment.
            </p>
            <div style="background: #F9F6F0; padding: 20px; border-radius: 6px; margin: 20px 0;">
                <p style="margin: 0; color: #1A1A1A; font-size: 14px;">
                    <strong>Your Invitation Code:</strong><br/>
                    <span style="font-size: 20px; color: #D4AF37; letter-spacing: 3px;">$invite_code</span>
                </p>
            </div>
            <p style="color: #707070; line-height: 1.6; font-size: 15px;">
                Start browsing our collection and book your first rental when you're ready.
            </p>
            <a href="$browse_url" style="display: inline-block; background: #1A1A1A; color: #FFFFFF; 
               text-decoration: none; padding: 14px 32px; border-radius: 4px; margin-top: 20px;
               font-family: 'Inter', sans-serif; font-size: 14px; letter-spacing: 1px;">
                BROWSE THE COLLECTION
            </a>
        </div>
        <div style="background: #1A1A1A; padding: 20px; text-align: center;">
            <p style="color: #707070; font-size: 12px; margin: 0;">
                The Vault — Luxury Handbag Rentals<br/>
                <span style="color: #D4AF37;">Access the Extraordinary.</span>
            </p>
        </div>
    </div>
</body>
</html>
"""

BOOKING_CONFIRMATION_TEMPLATE = """
<html>
<body style="font-family: 'Playfair Display', Georgia, serif; color: #1A1A1A; background: #F9F6F0; padding: 40px;">
    <div style="max-width: 600px; margin: 0 auto; background: #FFFFFF; border-radius: 8px; overflow: hidden;">
        <div style="background: #1A1A1A; padding: 30px; text-align: center;">
            <h1 style="color: #D4AF37; margin: 0; font-size: 24px;">The Vault</h1>
        </div>
        <div style="padding: 40px 30px;">
            <h2 style="color: #1A1A1A; font-size: 22px;">Your Booking is Confirmed!</h2>
            <p style="color: #707070; line-height: 1.6; font-size: 15px;">Dear $name,</p>
            <p style="color: #707070; line-height: 1.6; font-size: 15px;">
                Your rental of the <strong>$bag_name</strong> has been confirmed.
            </p>
            <table style="width: 100%; margin: 20px 0; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid #E0D8D0;">
                    <td style="padding: 10px; color: #707070;">Rental Period</td>
                    <td style="padding: 10px; text-align: right; color: #1A1A1A;">$start_date – $end_date</td>
                </tr>
                <tr style="border-bottom: 1px solid #E0D8D0;">
                    <td style="padding: 10px; color: #707070;">Duration</td>
                    <td style="padding: 10px; text-align: right; color: #1A1A1A;">$duration days</td>
                </tr>
                <tr style="border-bottom: 1px solid #E0D8D0;">
                    <td style="padding: 10px; color: #707070;">Total Charged</td>
                    <td style="padding: 10px; text-align: right; color: #1A1A1A; font-weight: bold;">$$total_amount</td>
                </tr>
                <tr>
                    <td style="padding: 10px; color: #707070;">Order #</td>
                    <td style="padding: 10px; text-align: right; color: #707070; font-size: 13px;">$booking_id</td>
                </tr>
            </table>
            <p style="color: #707070; line-height: 1.6; font-size: 15px;">
                Your bag will be authenticated, prepared, and shipped with white-glove delivery.
                You'll receive a tracking number once it's on its way.
            </p>
            <a href="$orders_url" style="display: inline-block; background: #1A1A1A; color: #FFFFFF; 
               text-decoration: none; padding: 14px 32px; border-radius: 4px; margin-top: 20px;
               font-family: 'Inter', sans-serif; font-size: 14px; letter-spacing: 1px;">
                VIEW ORDER DETAILS
            </a>
        </div>
    </div>
</body>
</html>
"""

WAITLIST_NOTIFICATION_TEMPLATE = """
<html>
<body style="font-family: 'Playfair Display', Georgia, serif; color: #1A1A1A; background: #F9F6F0; padding: 40px;">
    <div style="max-width: 600px; margin: 0 auto; background: #FFFFFF; border-radius: 8px; overflow: hidden;">
        <div style="background: #1A1A1A; padding: 30px; text-align: center;">
            <h1 style="color: #D4AF37; margin: 0; font-size: 24px;">The Vault</h1>
        </div>
        <div style="padding: 40px 30px;">
            <h2 style="color: #1A1A1A; font-size: 22px;">Good News — It's Available!</h2>
            <p style="color: #707070; line-height: 1.6; font-size: 15px;">Dear $name,</p>
            <p style="color: #707070; line-height: 1.6; font-size: 15px;">
                The <strong>$bag_name</strong> you've been waiting for is now available for booking.
            </p>
            <p style="color: #707070; line-height: 1.6; font-size: 15px;">
                At $$rental_price/day, this bag tends to book quickly. Don't wait too long.
            </p>
            <a href="$booking_url" style="display: inline-block; background: #D4AF37; color: #1A1A1A; 
               text-decoration: none; padding: 14px 32px; border-radius: 4px; margin-top: 20px;
               font-family: 'Inter', sans-serif; font-size: 14px; letter-spacing: 1px; font-weight: bold;">
                BOOK NOW
            </a>
        </div>
    </div>
</body>
</html>
"""

RETURN_REMINDER_TEMPLATE = """
<html>
<body style="font-family: 'Playfair Display', Georgia, serif; color: #1A1A1A; background: #F9F6F0; padding: 40px;">
    <div style="max-width: 600px; margin: 0 auto; background: #FFFFFF; border-radius: 8px; overflow: hidden;">
        <div style="padding: 40px 30px;">
            <h2 style="color: #1A1A1A; font-size: 22px;">Return Reminder</h2>
            <p style="color: #707070; line-height: 1.6; font-size: 15px;">Dear $name,</p>
            <p style="color: #707070; line-height: 1.6; font-size: 15px;">
                Your rental of the <strong>$bag_name</strong> is due for return on <strong>$return_date</strong>.
            </p>
            <p style="color: #707070; line-height: 1.6; font-size: 15px;">
                Please ensure the bag is carefully packed in its original dust bag and box.
                Your pre-paid return label will be emailed separately.
            </p>
        </div>
    </div>
</body>
</html>
"""


class EmailService:
    """Transactional email service with HTML templates and SMTP delivery."""

    FROM_NAME = "The Vault"
    FROM_EMAIL = "noreply@thevault.com"

    @staticmethod
    def _get_smtp_settings() -> tuple:
        """Get SMTP settings from config or return None for dev mode."""
        smtp_host = getattr(settings, "SMTP_HOST", None)
        smtp_port = getattr(settings, "SMTP_PORT", 587)
        smtp_user = getattr(settings, "SMTP_USER", None)
        smtp_password = getattr(settings, "SMTP_PASSWORD", None)
        return smtp_host, smtp_port, smtp_user, smtp_password

    @staticmethod
    def _render_template(template: str, **kwargs) -> str:
        """Render an HTML template with variables."""
        t = Template(template)
        return t.safe_substitute(**kwargs)

    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        html_body: str,
        to_name: Optional[str] = None,
    ) -> bool:
        """Send an email. In dev mode, log instead of sending."""
        smtp_host, smtp_port, smtp_user, smtp_password = EmailService._get_smtp_settings()

        if not smtp_host:
            # Dev mode — log to console
            logger.info(f"📧 [EMAIL] To: {to_email} | Subject: {subject}")
            logger.info(f"📧 [EMAIL] Body preview: {html_body[:200]}...")
            return True

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{EmailService.FROM_NAME} <{EmailService.FROM_EMAIL}>"
            msg["To"] = to_email

            # Plain text fallback
            text_part = MIMEText(f"Please enable HTML to view this email from {EmailService.FROM_NAME}.", "plain")
            html_part = MIMEText(html_body, "html")

            msg.attach(text_part)
            msg.attach(html_part)

            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                if smtp_user and smtp_password:
                    server.login(smtp_user, smtp_password)
                server.send_message(msg)

            logger.info(f"✅ Email sent to {to_email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to send email to {to_email}: {e}")
            return False

    # --- Specific transactional emails ---

    @staticmethod
    def send_welcome_email(to_email: str, name: str, invite_code: str = "") -> bool:
        """Send welcome email after registration."""
        subject = "Welcome to The Vault — Access the Extraordinary"
        html = EmailService._render_template(
            WELCOME_EMAIL_TEMPLATE,
            name=name,
            invite_code=invite_code or "VAULT-WELCOME",
            browse_url=f"{getattr(settings, 'APP_URL', 'http://localhost:3000')}/inventory",
        )
        return EmailService.send_email(to_email, subject, html, name)

    @staticmethod
    def send_booking_confirmation(
        to_email: str, name: str, bag_name: str,
        start_date: str, end_date: str, duration: int,
        total_amount: float, booking_id: str,
    ) -> bool:
        """Send booking confirmation email."""
        subject = "Your Vault Booking is Confirmed"
        html = EmailService._render_template(
            BOOKING_CONFIRMATION_TEMPLATE,
            name=name,
            bag_name=bag_name,
            start_date=start_date,
            end_date=end_date,
            duration=str(duration),
            total_amount=f"{total_amount:.2f}",
            booking_id=booking_id[:8],
            orders_url=f"{getattr(settings, 'APP_URL', 'http://localhost:3000')}/bookings/{booking_id}",
        )
        return EmailService.send_email(to_email, subject, html, name)

    @staticmethod
    def send_waitlist_notification(
        to_email: str, name: str, bag_name: str,
        rental_price: float, booking_url: str = "",
    ) -> bool:
        """Send waitlist availability notification."""
        subject = f"The {bag_name} is Now Available"
        html = EmailService._render_template(
            WAITLIST_NOTIFICATION_TEMPLATE,
            name=name,
            bag_name=bag_name,
            rental_price=f"{rental_price:.2f}",
            booking_url=booking_url or f"{getattr(settings, 'APP_URL', 'http://localhost:3000')}/bookings",
        )
        return EmailService.send_email(to_email, subject, html, name)

    @staticmethod
    def send_return_reminder(
        to_email: str, name: str, bag_name: str, return_date: str,
    ) -> bool:
        """Send return reminder email."""
        subject = f"Reminder: Return Your {bag_name} by {return_date}"
        html = EmailService._render_template(
            RETURN_REMINDER_TEMPLATE,
            name=name,
            bag_name=bag_name,
            return_date=return_date,
        )
        return EmailService.send_email(to_email, subject, html, name)