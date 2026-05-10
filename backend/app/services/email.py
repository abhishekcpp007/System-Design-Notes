"""
Email service for sending notifications.
Uses SMTP for free tier compatibility (Gmail, SendGrid free, etc.)
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Handles all email sending operations."""

    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL
        self.admin_email = settings.ADMIN_EMAIL

    def _create_connection(self) -> smtplib.SMTP:
        """Create SMTP connection with TLS."""
        server = smtplib.SMTP(self.smtp_host, self.smtp_port)
        server.starttls()
        server.login(self.smtp_user, self.smtp_password)
        return server

    def _send(self, to_email: str, subject: str, html_body: str, text_body: Optional[str] = None) -> bool:
        """Send an email. Returns True on success, False on failure."""
        if not all([self.smtp_host, self.smtp_user, self.smtp_password]):
            logger.warning("Email not configured, skipping send")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = self.from_email or self.smtp_user
            msg["To"] = to_email
            msg["Subject"] = subject

            if text_body:
                msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            with self._create_connection() as server:
                server.sendmail(msg["From"], to_email, msg.as_string())

            logger.info(f"Email sent to {to_email}: {subject}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def send_contact_notification(self, name: str, email: str, subject: str, message: str) -> bool:
        """Notify admin of new contact form submission."""
        html_body = f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #6366f1;">New Contact Form Submission</h2>
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 8px; font-weight: bold; border-bottom: 1px solid #e5e7eb;">Name</td>
                    <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">{name}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold; border-bottom: 1px solid #e5e7eb;">Email</td>
                    <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">{email}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold; border-bottom: 1px solid #e5e7eb;">Subject</td>
                    <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">{subject}</td>
                </tr>
            </table>
            <div style="margin-top: 16px; padding: 16px; background: #f9fafb; border-radius: 8px;">
                <p style="margin: 0; white-space: pre-wrap;">{message}</p>
            </div>
        </div>
        """
        return self._send(
            to_email=self.admin_email,
            subject=f"[Portfolio] New message from {name}: {subject}",
            html_body=html_body,
            text_body=f"From: {name} ({email})\nSubject: {subject}\n\n{message}",
        )

    def send_contact_confirmation(self, to_email: str, name: str) -> bool:
        """Send auto-reply to person who submitted contact form."""
        html_body = f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #6366f1;">Thanks for reaching out, {name}!</h2>
            <p>I've received your message and will get back to you as soon as possible,
            typically within 24-48 hours.</p>
            <p>In the meantime, feel free to check out my latest work on my portfolio.</p>
            <br/>
            <p>Best regards,<br/>Abhishek Verma</p>
        </div>
        """
        return self._send(
            to_email=to_email,
            subject="Thanks for your message!",
            html_body=html_body,
            text_body=f"Hi {name},\n\nThanks for reaching out! I'll get back to you within 24-48 hours.\n\nBest regards",
        )


# Singleton instance
email_service = EmailService()
