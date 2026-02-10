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

def _get_verification_email_html(verification_url: str, user_name: Optional[str] = None) -> str:
    """
    Generate HTML content for verification email.

    Uses Oat & Obsidian branding:
    - Obsidian (#212121) for dark elements
    - Oatmeal (#EBE9E4) for backgrounds
    - Sage (#4A7C59) for success/action elements
    """
    greeting = f"Hello {user_name}," if user_name else "Hello,"

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verify Your Paciolus Account</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Helvetica Neue', Arial, sans-serif; background-color: #EBE9E4;">
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #EBE9E4;">
        <tr>
            <td style="padding: 40px 20px;">
                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width: 600px; margin: 0 auto; background-color: #FFFFFF; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="background-color: #212121; padding: 30px 40px; border-radius: 8px 8px 0 0;">
                            <h1 style="margin: 0; color: #EBE9E4; font-family: Georgia, 'Times New Roman', serif; font-size: 28px; font-weight: normal;">
                                Paciolus
                            </h1>
                            <p style="margin: 5px 0 0 0; color: #9CA3AF; font-size: 14px;">
                                Trial Balance Intelligence
                            </p>
                        </td>
                    </tr>

                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px;">
                            <h2 style="margin: 0 0 20px 0; color: #212121; font-family: Georgia, 'Times New Roman', serif; font-size: 24px; font-weight: normal;">
                                Verify Your Email
                            </h2>

                            <p style="margin: 0 0 20px 0; color: #374151; font-size: 16px; line-height: 1.6;">
                                {greeting}
                            </p>

                            <p style="margin: 0 0 30px 0; color: #374151; font-size: 16px; line-height: 1.6;">
                                Thank you for creating a Paciolus account. To complete your registration and access our trial balance diagnostic tools, please verify your email address.
                            </p>

                            <!-- CTA Button -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="margin: 0 auto 30px auto;">
                                <tr>
                                    <td style="background-color: #4A7C59; border-radius: 6px;">
                                        <a href="{verification_url}" target="_blank" style="display: inline-block; padding: 16px 32px; color: #FFFFFF; text-decoration: none; font-size: 16px; font-weight: 600;">
                                            Verify Email Address
                                        </a>
                                    </td>
                                </tr>
                            </table>

                            <p style="margin: 0 0 20px 0; color: #6B7280; font-size: 14px; line-height: 1.6;">
                                Or copy and paste this link into your browser:
                            </p>
                            <p style="margin: 0 0 30px 0; color: #4A7C59; font-size: 14px; word-break: break-all;">
                                {verification_url}
                            </p>

                            <p style="margin: 0 0 10px 0; color: #6B7280; font-size: 14px; line-height: 1.6;">
                                This link will expire in 24 hours.
                            </p>

                            <p style="margin: 0; color: #6B7280; font-size: 14px; line-height: 1.6;">
                                If you didn't create a Paciolus account, you can safely ignore this email.
                            </p>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #F3F4F6; padding: 20px 40px; border-radius: 0 0 8px 8px; border-top: 1px solid #E5E7EB;">
                            <p style="margin: 0 0 10px 0; color: #6B7280; font-size: 12px; text-align: center;">
                                <strong>Zero-Storage Architecture</strong> - Your financial data is never stored.
                            </p>
                            <p style="margin: 0; color: #9CA3AF; font-size: 12px; text-align: center;">
                                &copy; 2026 Paciolus. All rights reserved.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""


def _get_verification_email_text(verification_url: str, user_name: Optional[str] = None) -> str:
    """Generate plain text version of verification email."""
    greeting = f"Hello {user_name}," if user_name else "Hello,"

    return f"""
Verify Your Paciolus Account

{greeting}

Thank you for creating a Paciolus account. To complete your registration and access our trial balance diagnostic tools, please verify your email address by clicking the link below:

{verification_url}

This link will expire in 24 hours.

If you didn't create a Paciolus account, you can safely ignore this email.

---
Zero-Storage Architecture - Your financial data is never stored.
(c) 2026 Paciolus. All rights reserved.
"""


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
