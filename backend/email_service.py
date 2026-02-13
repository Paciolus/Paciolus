"""
Paciolus Email Service
Sprint 57: Verified-Account-Only Model

SendGrid integration for transactional emails.
Currently supports:
- Email verification
- Resend verification (with cooldown)

All emails use Oat & Obsidian branding.
"""

import os
import secrets
from datetime import datetime, timedelta, UTC
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass

# SendGrid is optional - gracefully handle when not installed
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, To, Content, HtmlContent
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False

from security_utils import log_secure_operation


# =============================================================================
# CONFIGURATION
# =============================================================================

# Environment variables
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "noreply@paciolus.io")
SENDGRID_FROM_NAME = os.getenv("SENDGRID_FROM_NAME", "Paciolus")

# Token configuration
VERIFICATION_TOKEN_LENGTH = 64  # Characters (32 bytes hex encoded)
VERIFICATION_TOKEN_EXPIRY_HOURS = 24
RESEND_COOLDOWN_MINUTES = 5

# Frontend URL for verification links
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class EmailResult:
    """Result of an email send operation."""
    success: bool
    message: str
    message_id: Optional[str] = None


@dataclass
class VerificationTokenResult:
    """Result of token generation."""
    token: str
    expires_at: datetime


# =============================================================================
# TOKEN GENERATION
# =============================================================================

def generate_verification_token() -> VerificationTokenResult:
    """
    Generate a secure verification token.

    Returns:
        VerificationTokenResult with token and expiration time
    """
    # Generate 32 random bytes, hex encode to 64 characters
    token = secrets.token_hex(VERIFICATION_TOKEN_LENGTH // 2)
    expires_at = datetime.now(UTC) + timedelta(hours=VERIFICATION_TOKEN_EXPIRY_HOURS)

    return VerificationTokenResult(token=token, expires_at=expires_at)


def can_resend_verification(last_sent_at: Optional[datetime]) -> Tuple[bool, int]:
    """
    Check if a verification email can be resent (cooldown check).

    Args:
        last_sent_at: Timestamp of the last verification email

    Returns:
        Tuple of (can_resend, seconds_remaining)
    """
    if last_sent_at is None:
        return True, 0

    cooldown_end = last_sent_at + timedelta(minutes=RESEND_COOLDOWN_MINUTES)
    now = datetime.now(UTC)

    if now >= cooldown_end:
        return True, 0

    remaining = (cooldown_end - now).total_seconds()
    return False, int(remaining)


# =============================================================================
# EMAIL TEMPLATES
# =============================================================================

_TEMPLATES_DIR = Path(__file__).parent / "templates"


def _load_template(name: str) -> str:
    """Load an email template from the templates directory."""
    return (_TEMPLATES_DIR / name).read_text(encoding="utf-8")


def _get_verification_email_html(verification_url: str, user_name: Optional[str] = None) -> str:
    """
    Generate HTML content for verification email.

    Uses Oat & Obsidian branding:
    - Obsidian (#212121) for dark elements
    - Oatmeal (#EBE9E4) for backgrounds
    - Sage (#4A7C59) for success/action elements
    """
    greeting = f"Hello {user_name}," if user_name else "Hello,"
    template = _load_template("verification_email.html")
    return template.format(greeting=greeting, verification_url=verification_url)


def _get_verification_email_text(verification_url: str, user_name: Optional[str] = None) -> str:
    """Generate plain text version of verification email."""
    greeting = f"Hello {user_name}," if user_name else "Hello,"
    template = _load_template("verification_email.txt")
    return template.format(greeting=greeting, verification_url=verification_url)


# =============================================================================
# EMAIL SENDING
# =============================================================================

def send_verification_email(
    to_email: str,
    token: str,
    user_name: Optional[str] = None
) -> EmailResult:
    """
    Send an email verification message.

    Args:
        to_email: Recipient email address
        token: Verification token to include in the link
        user_name: Optional user name for personalization

    Returns:
        EmailResult indicating success/failure
    """
    if not SENDGRID_AVAILABLE:
        log_secure_operation("email_skipped", "SendGrid library not installed")
        verification_url = f"{FRONTEND_URL}/verify-email?token={token}"
        log_secure_operation("verification_url", f"DEV MODE: {verification_url}")
        return EmailResult(
            success=True,
            message="Email sending skipped (SendGrid not installed). Check server logs for verification URL."
        )

    if not SENDGRID_API_KEY:
        log_secure_operation("email_skipped", "SendGrid API key not configured")
        # In development, log the token for testing
        verification_url = f"{FRONTEND_URL}/verify-email?token={token}"
        log_secure_operation("verification_url", f"DEV MODE: {verification_url}")
        return EmailResult(
            success=True,
            message="Email sending skipped (no API key). Check server logs for verification URL."
        )

    try:
        verification_url = f"{FRONTEND_URL}/verify-email?token={token}"

        message = Mail(
            from_email=Email(SENDGRID_FROM_EMAIL, SENDGRID_FROM_NAME),
            to_emails=To(to_email),
            subject="Verify Your Paciolus Account",
        )

        # Add both HTML and plain text versions
        message.add_content(Content("text/plain", _get_verification_email_text(verification_url, user_name)))
        message.add_content(HtmlContent(_get_verification_email_html(verification_url, user_name)))

        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)

        if response.status_code in (200, 201, 202):
            log_secure_operation("email_sent", f"Verification email sent to {to_email[:10]}...")
            return EmailResult(
                success=True,
                message="Verification email sent",
                message_id=response.headers.get("X-Message-Id")
            )
        else:
            log_secure_operation("email_failed", f"SendGrid returned {response.status_code}")
            return EmailResult(
                success=False,
                message=f"Failed to send email (status {response.status_code})"
            )

    except Exception as e:
        log_secure_operation("email_error", str(e))
        return EmailResult(
            success=False,
            message=f"Email service error: {str(e)}"
        )


# =============================================================================
# CONTACT FORM
# =============================================================================

CONTACT_EMAIL = os.getenv("CONTACT_EMAIL", "contact@paciolus.io")


def send_contact_form_email(
    name: str,
    email: str,
    company: str,
    inquiry_type: str,
    message: str,
) -> EmailResult:
    """
    Send a contact form submission to the team inbox.

    Args:
        name: Sender's name
        email: Sender's email address
        company: Sender's company (optional)
        inquiry_type: Category of inquiry
        message: Message body

    Returns:
        EmailResult indicating success/failure
    """
    subject = f"[Paciolus Contact] {inquiry_type} — {name}"
    company_line = f"Company: {company}\n" if company else ""
    body_text = (
        f"New contact form submission\n"
        f"{'=' * 40}\n\n"
        f"Name: {name}\n"
        f"Email: {email}\n"
        f"{company_line}"
        f"Inquiry Type: {inquiry_type}\n\n"
        f"Message:\n{message}\n"
    )

    if not SENDGRID_AVAILABLE:
        log_secure_operation("contact_email_skipped", "SendGrid library not installed")
        log_secure_operation("contact_form", f"DEV MODE — {subject}\n{body_text}")
        return EmailResult(
            success=True,
            message="Contact form logged (SendGrid not installed). Check server logs."
        )

    if not SENDGRID_API_KEY:
        log_secure_operation("contact_email_skipped", "SendGrid API key not configured")
        log_secure_operation("contact_form", f"DEV MODE — {subject}\n{body_text}")
        return EmailResult(
            success=True,
            message="Contact form logged (no API key). Check server logs."
        )

    try:
        mail_message = Mail(
            from_email=Email(SENDGRID_FROM_EMAIL, SENDGRID_FROM_NAME),
            to_emails=To(CONTACT_EMAIL),
            subject=subject,
        )
        mail_message.add_content(Content("text/plain", body_text))

        # Reply-to the sender so team can respond directly
        mail_message.reply_to = Email(email, name)

        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(mail_message)

        if response.status_code in (200, 201, 202):
            log_secure_operation("contact_email_sent", f"Contact form from {email[:10]}...")
            return EmailResult(
                success=True,
                message="Contact form email sent",
                message_id=response.headers.get("X-Message-Id")
            )
        else:
            log_secure_operation("contact_email_failed", f"SendGrid returned {response.status_code}")
            return EmailResult(
                success=False,
                message=f"Failed to send contact email (status {response.status_code})"
            )

    except Exception as e:
        log_secure_operation("contact_email_error", str(e))
        return EmailResult(
            success=False,
            message=f"Email service error: {str(e)}"
        )


# =============================================================================
# EMAIL CHANGE NOTIFICATION (Sprint 203)
# =============================================================================


def send_email_change_notification(
    to_email: str,
    new_email: str,
    user_name: Optional[str] = None,
) -> EmailResult:
    """
    Send a security notification to the OLD email address when an email change
    is requested.

    Args:
        to_email: The user's current (old) email address
        new_email: The new email address (masked in the notification)
        user_name: Optional user name for personalization

    Returns:
        EmailResult indicating success/failure
    """
    # Mask the new email for security (show first 3 chars + domain)
    parts = new_email.split("@")
    if len(parts) == 2 and len(parts[0]) > 3:
        masked = parts[0][:3] + "***@" + parts[1]
    else:
        masked = "***@***"

    greeting = f"Hello {user_name}," if user_name else "Hello,"
    body_text = (
        f"{greeting}\n\n"
        f"An email address change was requested for your Paciolus account.\n\n"
        f"New email: {masked}\n\n"
        f"A verification email has been sent to the new address. "
        f"Your current email will remain active until the new one is verified.\n\n"
        f"If you did not request this change, please change your password immediately.\n\n"
        f"— The Paciolus Team\n"
    )

    if not SENDGRID_AVAILABLE:
        log_secure_operation("email_change_notification_skipped", "SendGrid library not installed")
        log_secure_operation("email_change_notification", f"DEV MODE: notifying {to_email[:10]}... about change to {masked}")
        return EmailResult(
            success=True,
            message="Email change notification logged (SendGrid not installed). Check server logs."
        )

    if not SENDGRID_API_KEY:
        log_secure_operation("email_change_notification_skipped", "SendGrid API key not configured")
        log_secure_operation("email_change_notification", f"DEV MODE: notifying {to_email[:10]}... about change to {masked}")
        return EmailResult(
            success=True,
            message="Email change notification logged (no API key). Check server logs."
        )

    try:
        message = Mail(
            from_email=Email(SENDGRID_FROM_EMAIL, SENDGRID_FROM_NAME),
            to_emails=To(to_email),
            subject="Paciolus — Email Address Change Requested",
        )
        message.add_content(Content("text/plain", body_text))

        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)

        if response.status_code in (200, 201, 202):
            log_secure_operation("email_change_notification_sent", f"Notification sent to {to_email[:10]}...")
            return EmailResult(
                success=True,
                message="Email change notification sent",
                message_id=response.headers.get("X-Message-Id"),
            )
        else:
            log_secure_operation("email_change_notification_failed", f"SendGrid returned {response.status_code}")
            return EmailResult(
                success=False,
                message=f"Failed to send notification (status {response.status_code})",
            )

    except Exception as e:
        log_secure_operation("email_change_notification_error", str(e))
        return EmailResult(
            success=False,
            message=f"Email service error: {str(e)}",
        )


# =============================================================================
# SERVICE STATUS
# =============================================================================

def is_email_service_configured() -> bool:
    """Check if email service is properly configured."""
    return SENDGRID_AVAILABLE and bool(SENDGRID_API_KEY)


def get_service_status() -> dict:
    """Get email service configuration status (for admin/debug)."""
    return {
        "configured": is_email_service_configured(),
        "from_email": SENDGRID_FROM_EMAIL,
        "from_name": SENDGRID_FROM_NAME,
        "token_expiry_hours": VERIFICATION_TOKEN_EXPIRY_HOURS,
        "resend_cooldown_minutes": RESEND_COOLDOWN_MINUTES,
    }
