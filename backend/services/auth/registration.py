"""
Registration service (Sprint 746c).

Extracts the registration / email verification / resend lifecycle from
`routes/auth_routes.py`. Cookies + HTTP-shaped 429 detail dicts stay in
the route layer per the boundary established in ADR-015.

Routes call:
  - `register_user` → returns `RegistrationResult` (user + initial-session
    issuance + optional verification_token for the email task).
  - `complete_email_verification` → returns updated `User`; raises
    `EmailVerificationError` for unknown / used / expired tokens.
  - `resend_verification_email` → returns the new token + target email;
    raises `EmailAlreadyVerifiedError` or `VerificationCooldownError`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from auth import (
    UserCreate,
    create_access_token,
    create_refresh_token,
    create_user,
    get_user_by_email,
    hash_token,
)
from config import ENV_MODE
from disposable_email import is_disposable_email
from email_service import (
    can_resend_verification,
    generate_verification_token,
    is_email_service_configured,
)
from models import EmailVerificationToken, User
from security_middleware import generate_csrf_token
from security_utils import log_secure_operation
from services.auth.identity import IdentityIssuance
from shared.db_unit_of_work import db_transaction
from shared.log_sanitizer import mask_email


class RegistrationError(ValueError):
    """Raised by `register_user` for disposable / duplicate-email rejection."""


class EmailAlreadyVerifiedError(ValueError):
    """Raised by `resend_verification_email` when the user is already verified
    and has no pending email change pending."""


class VerificationCooldownError(ValueError):
    """Raised by `resend_verification_email` while the resend cooldown is
    still active. `seconds_remaining` carries the cooldown delta for the
    route to surface in the 429 detail."""

    def __init__(self, seconds_remaining: int) -> None:
        super().__init__("Please wait before requesting another verification email")
        self.seconds_remaining = seconds_remaining


class EmailVerificationError(ValueError):
    """Raised by `complete_email_verification` for unknown / used / expired
    tokens."""


@dataclass(frozen=True)
class RegistrationResult:
    """
    Outcome of `register_user`.

    `verification_token` is populated only when the email service is
    configured (otherwise the user was auto-verified in development mode
    or left unverified in production). The route schedules the verification
    email background task using this token if non-None.
    """

    user: User
    issuance: IdentityIssuance
    verification_token: str | None


def register_user(
    db: Session,
    *,
    user_data: UserCreate,
    user_agent: str | None,
    request_host: str | None,
) -> RegistrationResult:
    """
    Run the full registration pipeline:
      1. Reject disposable emails.
      2. Reject duplicate emails (enumeration-safe message).
      3. Create the user.
      4. Set verification token OR auto-verify in development.
      5. Commit (via `db_transaction`).
      6. Mint the initial access + refresh + CSRF (no `remember_me`).

    Cookies are not written here — the caller does that with the returned
    `IdentityIssuance`.
    """
    masked = mask_email(user_data.email)

    if is_disposable_email(user_data.email):
        log_secure_operation("auth_register_blocked", f"Disposable email blocked: {masked}")
        raise RegistrationError(
            "Temporary or disposable email addresses are not allowed. Please use a permanent email address."
        )

    if get_user_by_email(db, user_data.email) is not None:
        # Generic message to defeat account enumeration.
        raise RegistrationError("Unable to create account. Please check your information or try logging in.")

    user = create_user(db, user_data)

    verification_token: str | None = None
    if not is_email_service_configured():
        if ENV_MODE == "development":
            user.is_verified = True
            user.email_verified_at = datetime.now(UTC)
            log_secure_operation(
                "auto_verified",
                f"Email service unavailable — auto-verified {masked}",
            )
        else:
            log_secure_operation(
                "auto_verify_skipped",
                f"Email service unavailable in {ENV_MODE} — user left unverified: {masked}",
            )
    else:
        token_result = generate_verification_token()
        db.add(
            EmailVerificationToken(
                user_id=user.id,
                token_hash=hash_token(token_result.token),
                expires_at=token_result.expires_at,
            )
        )
        user.email_verification_sent_at = datetime.now(UTC)
        verification_token = token_result.token

    with db_transaction(
        db,
        log_label="db_register",
        log_message="Database error during user registration commit",
    ):
        pass

    # Initial session — registration always issues a session-only login (no
    # "remember me"). create_refresh_token commits internally; that's fine
    # because the registration commit above is already durable.
    access_token, expires = create_access_token(user.id, user.email, user.password_changed_at, tier=user.tier.value)
    expires_in = int((expires - datetime.now(UTC)).total_seconds())

    raw_refresh_token, _ = create_refresh_token(db, user.id, user_agent=user_agent, ip_address=request_host)
    csrf_token_value = generate_csrf_token(user_id=str(user.id))

    issuance = IdentityIssuance(
        user=user,
        access_token=access_token,
        raw_refresh_token=raw_refresh_token,
        expires_in=expires_in,
        csrf_token=csrf_token_value,
    )

    return RegistrationResult(
        user=user,
        issuance=issuance,
        verification_token=verification_token,
    )


def complete_email_verification(db: Session, token: str) -> User:
    """
    Consume an email verification token.

    Raises `EmailVerificationError` for unknown / used / expired tokens.
    Handles the Sprint 203 pending-email swap (when a verified user
    initiates an email change, the new email is held in `pending_email`
    until verification consumes the token).
    """
    verification = (
        db.query(EmailVerificationToken).filter(EmailVerificationToken.token_hash == hash_token(token)).first()
    )

    if verification is None:
        raise EmailVerificationError("Invalid verification token")
    if verification.is_used:
        raise EmailVerificationError("This verification link has already been used")
    if verification.is_expired:
        raise EmailVerificationError("This verification link has expired. Please request a new one.")

    verification.used_at = datetime.now(UTC)
    user = verification.user

    # Sprint 203: pending email swap on verification.
    if user.pending_email:
        user.email = user.pending_email
        user.pending_email = None
        log_secure_operation("email_changed", f"User {user.id} email swapped from pending")

    user.is_verified = True
    user.email_verified_at = datetime.now(UTC)

    with db_transaction(
        db,
        log_label="db_verify_email",
        log_message="Database error during email verification commit",
    ):
        pass

    log_secure_operation("email_verified", f"User {user.id} email verified")
    return user


@dataclass(frozen=True)
class ResendVerificationResult:
    """Outcome of `resend_verification_email` — caller schedules the email
    using `token` and routes it to `target_email` (handles Sprint 203's
    pending-email override)."""

    token: str
    target_email: str


def resend_verification_email(db: Session, current_user: User) -> ResendVerificationResult:
    """
    Generate a fresh verification token for the calling user.

    - Already-verified user without pending email change → `EmailAlreadyVerifiedError`.
    - Cooldown still active → `VerificationCooldownError(seconds_remaining)`.
    - Otherwise: invalidates outstanding tokens, mints a new one, commits,
      and returns the token + target email.

    Sprint 203: when `pending_email` is set, the verification email goes to
    the pending address (the address being verified into).
    """
    if current_user.is_verified and not current_user.pending_email:
        raise EmailAlreadyVerifiedError("Email is already verified")

    can_resend, seconds_remaining = can_resend_verification(current_user.email_verification_sent_at)
    if not can_resend:
        raise VerificationCooldownError(seconds_remaining)

    # Invalidate any outstanding tokens for this user.
    db.query(EmailVerificationToken).filter(
        EmailVerificationToken.user_id == current_user.id,
        EmailVerificationToken.used_at.is_(None),
    ).update({"used_at": datetime.now(UTC)})

    token_result = generate_verification_token()
    db.add(
        EmailVerificationToken(
            user_id=current_user.id,
            token_hash=hash_token(token_result.token),
            expires_at=token_result.expires_at,
        )
    )
    current_user.email_verification_sent_at = datetime.now(UTC)

    with db_transaction(
        db,
        log_label="db_resend_verify",
        log_message="Database error during resend verification commit",
    ):
        pass

    target_email = current_user.pending_email or current_user.email
    return ResendVerificationResult(token=token_result.token, target_email=target_email)
