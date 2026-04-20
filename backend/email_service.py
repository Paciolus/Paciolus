"""
Paciolus Email Service
Sprint 57: Verified-Account-Only Model

SendGrid integration for transactional emails.
Currently supports:
- Email verification
- Resend verification (with cooldown)

All emails use Oat & Obsidian branding.
"""

import logging
import os
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# SendGrid is optional - gracefully handle when not installed
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Content, Email, HtmlContent, Mail, To

    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False

from config import FRONTEND_URL
from security_utils import log_secure_operation
from shared.log_sanitizer import mask_email, sanitize_exception, token_fingerprint

# =============================================================================
# CONFIGURATION
# =============================================================================

# Environment variables
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "noreply@paciolus.com")
SENDGRID_FROM_NAME = os.getenv("SENDGRID_FROM_NAME", "Paciolus")

# Token configuration
VERIFICATION_TOKEN_LENGTH = 64  # Characters (32 bytes hex encoded)
VERIFICATION_TOKEN_EXPIRY_HOURS = 24
RESEND_COOLDOWN_MINUTES = 5
PASSWORD_RESET_TOKEN_EXPIRY_HOURS = 1


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


def can_resend_verification(last_sent_at: Optional[datetime]) -> tuple[bool, int]:
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
    import html as html_mod

    # SECURITY: HTML-escape user name to prevent injection in email body
    safe_name = html_mod.escape(user_name) if user_name else None
    greeting = f"Hello {safe_name}," if safe_name else "Hello,"
    template = _load_template("verification_email.html")
    # Use safe substitution: escape any stray braces in greeting to prevent format-string errors
    return template.format(greeting=greeting, verification_url=verification_url)


def _get_verification_email_text(verification_url: str, user_name: Optional[str] = None) -> str:
    """Generate plain text version of verification email."""
    greeting = f"Hello {user_name}," if user_name else "Hello,"
    template = _load_template("verification_email.txt")
    return template.format(greeting=greeting, verification_url=verification_url)


# =============================================================================
# EMAIL SENDING
# =============================================================================


def send_verification_email(to_email: str, token: str, user_name: Optional[str] = None) -> EmailResult:
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
        log_secure_operation(
            "verification_token", f"DEV MODE: token={token_fingerprint(token)} for {mask_email(to_email)}"
        )
        return EmailResult(success=True, message="Email sending skipped (SendGrid not installed).")

    if not SENDGRID_API_KEY:
        log_secure_operation("email_skipped", "SendGrid API key not configured")
        log_secure_operation(
            "verification_token", f"DEV MODE: token={token_fingerprint(token)} for {mask_email(to_email)}"
        )
        return EmailResult(success=True, message="Email sending skipped (no API key).")

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
            log_secure_operation("email_sent", f"Verification email sent to {mask_email(to_email)}")
            return EmailResult(
                success=True, message="Verification email sent", message_id=response.headers.get("X-Message-Id")
            )
        else:
            log_secure_operation("email_failed", f"SendGrid returned {response.status_code}")
            return EmailResult(success=False, message=f"Failed to send email (status {response.status_code})")

    except (OSError, ValueError, RuntimeError) as e:
        logger.exception("Verification email send failed")
        log_secure_operation("email_error", sanitize_exception(e, context="email delivery"))
        return EmailResult(success=False, message="Email delivery failed. Please try again later.")


# =============================================================================
# PASSWORD RESET
# =============================================================================


def generate_password_reset_token() -> VerificationTokenResult:
    """Generate a secure password reset token (1-hour expiry)."""
    token = secrets.token_hex(VERIFICATION_TOKEN_LENGTH // 2)
    expires_at = datetime.now(UTC) + timedelta(hours=PASSWORD_RESET_TOKEN_EXPIRY_HOURS)
    return VerificationTokenResult(token=token, expires_at=expires_at)


def _get_password_reset_email_html(reset_url: str, user_name: Optional[str] = None) -> str:
    """Generate HTML content for password reset email (Oat & Obsidian branding)."""
    import html as html_mod

    safe_name = html_mod.escape(user_name) if user_name else None
    greeting = f"Hello {safe_name}," if safe_name else "Hello,"
    template = _load_template("password_reset_email.html")
    return template.format(greeting=greeting, reset_url=reset_url)


def _get_password_reset_email_text(reset_url: str, user_name: Optional[str] = None) -> str:
    """Generate plain text version of password reset email."""
    greeting = f"Hello {user_name}," if user_name else "Hello,"
    template = _load_template("password_reset_email.txt")
    return template.format(greeting=greeting, reset_url=reset_url)


def send_password_reset_email(to_email: str, token: str, user_name: Optional[str] = None) -> EmailResult:
    """Send a password reset email with a one-time reset link."""
    if not SENDGRID_AVAILABLE:
        log_secure_operation("email_skipped", "SendGrid library not installed")
        log_secure_operation(
            "password_reset_token", f"DEV MODE: token={token_fingerprint(token)} for {mask_email(to_email)}"
        )
        return EmailResult(success=True, message="Email sending skipped (SendGrid not installed).")

    if not SENDGRID_API_KEY:
        log_secure_operation("email_skipped", "SendGrid API key not configured")
        log_secure_operation(
            "password_reset_token", f"DEV MODE: token={token_fingerprint(token)} for {mask_email(to_email)}"
        )
        return EmailResult(success=True, message="Email sending skipped (no API key).")

    try:
        reset_url = f"{FRONTEND_URL}/reset-password?token={token}"

        message = Mail(
            from_email=Email(SENDGRID_FROM_EMAIL, SENDGRID_FROM_NAME),
            to_emails=To(to_email),
            subject="Reset Your Paciolus Password",
        )

        message.add_content(Content("text/plain", _get_password_reset_email_text(reset_url, user_name)))
        message.add_content(HtmlContent(_get_password_reset_email_html(reset_url, user_name)))

        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)

        if response.status_code in (200, 201, 202):
            log_secure_operation("email_sent", f"Password reset email sent to {mask_email(to_email)}")
            return EmailResult(
                success=True, message="Password reset email sent", message_id=response.headers.get("X-Message-Id")
            )
        else:
            log_secure_operation("email_failed", f"SendGrid returned {response.status_code}")
            return EmailResult(success=False, message=f"Failed to send email (status {response.status_code})")

    except (OSError, ValueError, RuntimeError) as e:
        logger.exception("Password reset email send failed")
        log_secure_operation("email_error", sanitize_exception(e, context="password reset email"))
        return EmailResult(success=False, message="Email delivery failed. Please try again later.")


# =============================================================================
# CONTACT FORM
# =============================================================================

CONTACT_EMAIL = os.getenv("CONTACT_EMAIL", "contact@paciolus.com")


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
        log_secure_operation("contact_form", f"DEV MODE — inquiry_type={inquiry_type}, message_length={len(message)}")
        return EmailResult(success=True, message="Contact form logged (SendGrid not installed).")

    if not SENDGRID_API_KEY:
        log_secure_operation("contact_email_skipped", "SendGrid API key not configured")
        log_secure_operation("contact_form", f"DEV MODE — inquiry_type={inquiry_type}, message_length={len(message)}")
        return EmailResult(success=True, message="Contact form logged (no API key).")

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
            log_secure_operation("contact_email_sent", f"Contact form from {mask_email(email)}")
            return EmailResult(
                success=True, message="Contact form email sent", message_id=response.headers.get("X-Message-Id")
            )
        else:
            log_secure_operation("contact_email_failed", f"SendGrid returned {response.status_code}")
            return EmailResult(success=False, message=f"Failed to send contact email (status {response.status_code})")

    except (OSError, ValueError, RuntimeError) as e:
        logger.exception("Contact email send failed")
        log_secure_operation("contact_email_error", sanitize_exception(e, context="contact email delivery"))
        return EmailResult(success=False, message="Email delivery failed. Please try again later.")


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
        log_secure_operation(
            "email_change_notification", f"DEV MODE: notifying {mask_email(to_email)} about change to {masked}"
        )
        return EmailResult(
            success=True, message="Email change notification logged (SendGrid not installed). Check server logs."
        )

    if not SENDGRID_API_KEY:
        log_secure_operation("email_change_notification_skipped", "SendGrid API key not configured")
        log_secure_operation(
            "email_change_notification", f"DEV MODE: notifying {mask_email(to_email)} about change to {masked}"
        )
        return EmailResult(success=True, message="Email change notification logged (no API key). Check server logs.")

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
            log_secure_operation("email_change_notification_sent", f"Notification sent to {mask_email(to_email)}")
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

    except (OSError, ValueError, RuntimeError) as e:
        logger.exception("Email change notification send failed")
        log_secure_operation(
            "email_change_notification_error", sanitize_exception(e, context="email change notification")
        )
        return EmailResult(
            success=False,
            message="Email delivery failed. Please try again later.",
        )


# =============================================================================
# SERVICE STATUS
# =============================================================================


def is_email_service_configured() -> bool:
    """Check if email service is properly configured."""
    return SENDGRID_AVAILABLE and bool(SENDGRID_API_KEY)


# =============================================================================
# DUNNING EMAILS (Sprint 591)
# =============================================================================


def _send_dunning_email(
    to_email: str,
    subject: str,
    html_body: str,
    plain_body: str,
) -> EmailResult:
    """Internal helper for dunning emails — fire-and-forget with error logging."""
    if not SENDGRID_AVAILABLE or not SENDGRID_API_KEY:
        log_secure_operation("dunning_email_skipped", f"to={mask_email(to_email)} subj={subject[:40]}")
        return EmailResult(success=True, message="Email sending skipped (not configured).")

    try:
        message = Mail(
            from_email=Email(SENDGRID_FROM_EMAIL, SENDGRID_FROM_NAME),
            to_emails=To(to_email),
            subject=subject,
        )
        message.add_content(Content("text/plain", plain_body))
        message.add_content(HtmlContent(html_body))

        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)

        if response.status_code in (200, 201, 202):
            log_secure_operation("dunning_email_sent", f"to={mask_email(to_email)} subj={subject[:40]}")
            return EmailResult(
                success=True, message="Dunning email sent", message_id=response.headers.get("X-Message-Id")
            )
        else:
            log_secure_operation("dunning_email_failed", f"SendGrid {response.status_code}")
            return EmailResult(success=False, message=f"Failed (status {response.status_code})")

    except (OSError, ValueError, RuntimeError) as e:
        from shared.log_sanitizer import sanitize_exception

        log_secure_operation("dunning_email_error", sanitize_exception(e, context="dunning email"))
        return EmailResult(success=False, message="Email send error")


def _dunning_html(title: str, body: str, cta_url: str, cta_text: str) -> str:
    """Generate Oat & Obsidian branded dunning email HTML."""
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"></head>
<body style="margin:0;padding:0;background-color:#EBE9E4;font-family:Lato,Arial,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color:#EBE9E4;padding:40px 20px">
<tr><td align="center">
<table width="560" cellpadding="0" cellspacing="0" style="background-color:#fff;border-radius:8px;overflow:hidden">
<tr><td style="background-color:#212121;padding:24px 32px">
<h1 style="margin:0;color:#EBE9E4;font-family:Merriweather,Georgia,serif;font-size:20px">{title}</h1>
</td></tr>
<tr><td style="padding:32px">
{body}
<table width="100%" cellpadding="0" cellspacing="0" style="margin-top:24px">
<tr><td align="center">
<a href="{cta_url}" style="display:inline-block;padding:12px 28px;background-color:#4A7C59;color:#fff;text-decoration:none;border-radius:6px;font-weight:600;font-size:14px">{cta_text}</a>
</td></tr>
</table>
</td></tr>
<tr><td style="padding:16px 32px;background-color:#f5f4f1;border-top:1px solid #e0ddd8;text-align:center;color:#888;font-size:12px">
Paciolus — Professional Audit Intelligence
</td></tr>
</table>
</td></tr></table>
</body></html>"""


def send_dunning_first_failure(to_email: str, amount: str, plan_name: str, portal_url: str) -> EmailResult:
    """First payment failure — friendly, informational."""
    body = f'<p style="color:#212121;font-size:15px;line-height:1.6">Your payment of <strong>{amount}</strong> for <strong>{plan_name}</strong> didn\'t go through. This can happen — we\'ll try again in a few days.</p><p style="color:#212121;font-size:15px;line-height:1.6">If you\'d like to update your payment method now, click below:</p>'
    plain = f"Your payment of {amount} for {plan_name} didn't go through. We'll try again in a few days. Update your payment method: {portal_url}"
    return _send_dunning_email(
        to_email,
        "We couldn't process your Paciolus payment",
        _dunning_html("Payment Issue", body, portal_url, "Update Payment Method"),
        plain,
    )


def send_dunning_second_failure(to_email: str, amount: str, portal_url: str) -> EmailResult:
    """Second failure — urgent."""
    body = f'<p style="color:#212121;font-size:15px;line-height:1.6">We\'ve tried twice to process your <strong>{amount}</strong> payment. To avoid service interruption, please update your payment method.</p>'
    plain = f"We've tried twice to process your {amount} payment. Update your payment method to avoid interruption: {portal_url}"
    return _send_dunning_email(
        to_email,
        "Action needed: Update your Paciolus payment method",
        _dunning_html("Payment Action Needed", body, portal_url, "Update Payment Method"),
        plain,
    )


def send_dunning_final_notice(to_email: str, suspension_date: str, portal_url: str) -> EmailResult:
    """Final notice — last chance before suspension."""
    body = f'<p style="color:#212121;font-size:15px;line-height:1.6">We haven\'t been able to collect your payment after multiple attempts.</p><p style="color:#BC4749;font-size:15px;line-height:1.6;font-weight:600">Your account will be suspended on {suspension_date} unless payment is received.</p>'
    plain = f"Your Paciolus account will be suspended on {suspension_date} unless payment is received. Update your payment method: {portal_url}"
    return _send_dunning_email(
        to_email,
        "Final notice: Your Paciolus account will be suspended in 7 days",
        _dunning_html("Final Payment Notice", body, portal_url, "Update Payment Method"),
        plain,
    )


def send_dunning_suspended(to_email: str, reactivation_url: str) -> EmailResult:
    """Account suspended due to non-payment."""
    body = '<p style="color:#212121;font-size:15px;line-height:1.6">Your subscription has been canceled due to non-payment. Your data will be retained for 30 days.</p><p style="color:#212121;font-size:15px;line-height:1.6">To reactivate your account, click below:</p>'
    plain = f"Your Paciolus subscription has been canceled due to non-payment. Data retained for 30 days. Reactivate: {reactivation_url}"
    return _send_dunning_email(
        to_email,
        "Your Paciolus account has been suspended",
        _dunning_html("Account Suspended", body, reactivation_url, "Reactivate Account"),
        plain,
    )


def send_dunning_recovered(to_email: str, amount: str) -> EmailResult:
    """Payment recovered — all clear."""
    body = f'<p style="color:#212121;font-size:15px;line-height:1.6">Great news — your payment of <strong>{amount}</strong> has been processed successfully. Your Paciolus account is fully active.</p><p style="color:#4A7C59;font-size:15px;line-height:1.6;font-weight:600">No action needed.</p>'
    plain = f"Your payment of {amount} has been processed. Your Paciolus account is fully active. No action needed."
    return _send_dunning_email(
        to_email,
        "Payment received — you're all set!",
        _dunning_html("Payment Received", body, f"{FRONTEND_URL}/dashboard", "Go to Dashboard"),
        plain,
    )


def send_trial_ending_email(
    to_email: str,
    days_remaining: int,
    plan_name: str,
    portal_url: str,
) -> EmailResult:
    """Sprint 690: 3-day trial-ending notice.

    Fired by the ``customer.subscription.trial_will_end`` Stripe webhook
    (which delivers 3 days before the trial converts). Reuses the dunning
    email infrastructure (Oat & Obsidian branded, same deliverability path)
    because the shape — single CTA, friendly tone, informational — matches.

    ``days_remaining`` is accepted from the webhook's trial_end timestamp
    so the copy adapts if Stripe's notice window shifts.
    """
    day_word = "day" if days_remaining == 1 else "days"
    body = (
        f'<p style="color:#212121;font-size:15px;line-height:1.6">Heads up — your Paciolus free trial '
        f"ends in <strong>{days_remaining} {day_word}</strong>.</p>"
        f'<p style="color:#212121;font-size:15px;line-height:1.6">After the trial, your <strong>{plan_name}</strong> '
        "subscription will activate automatically using the payment method on file. You don't need to do "
        "anything to continue.</p>"
        '<p style="color:#212121;font-size:15px;line-height:1.6">If you\'d like to change plans, update '
        "your payment method, or cancel before the trial converts, you can manage everything in the billing portal.</p>"
    )
    plain = (
        f"Your Paciolus free trial ends in {days_remaining} {day_word}. "
        f"Your {plan_name} subscription will activate automatically. "
        f"Manage, change, or cancel at: {portal_url}"
    )
    return _send_dunning_email(
        to_email,
        f"Your Paciolus trial ends in {days_remaining} {day_word}",
        _dunning_html("Trial Ending Soon", body, portal_url, "Manage Subscription"),
        plain,
    )


def get_service_status() -> dict:
    """Get email service configuration status (for admin/debug)."""
    return {
        "configured": is_email_service_configured(),
        "from_email": SENDGRID_FROM_EMAIL,
        "from_name": SENDGRID_FROM_NAME,
        "token_expiry_hours": VERIFICATION_TOKEN_EXPIRY_HOURS,
        "resend_cooldown_minutes": RESEND_COOLDOWN_MINUTES,
    }
