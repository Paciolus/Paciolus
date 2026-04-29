"""
Password recovery service (Sprint 746a).

Extracts the password reset lifecycle from `routes/auth_routes.py` so the
route handler is reduced to:

    user, token = initiate_password_reset(db, email)
    if user and token:
        background_tasks.add_task(...)
    return generic_response

and:

    try:
        user = complete_password_reset(db, token, new_password)
    except PasswordResetError as e:
        raise_http_error(400, label="password_reset_invalid", user_message=str(e))
    return ResetPasswordResponse(...)

The service owns: token generation/persistence, token validation
(invalid/used/expired/inactive), password hashing, session revocation, and
the post-reset lockout reset. **Does not** touch cookies or HTTP plumbing.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from auth import _revoke_all_user_tokens, get_user_by_email, hash_password, hash_token
from email_service import VerificationTokenResult, generate_password_reset_token
from models import PasswordResetToken, User
from security_utils import log_secure_operation
from shared.db_unit_of_work import db_transaction
from shared.log_sanitizer import mask_email

logger = logging.getLogger(__name__)


class PasswordResetError(ValueError):
    """Raised by `complete_password_reset` for any token / user invalidity."""


@dataclass(frozen=True)
class PasswordResetInitiation:
    """
    Outcome of `initiate_password_reset`.

    `user` and `token_result` are populated only when the email belongs to
    an active account that should receive a reset email. Otherwise both
    are None and the caller must still return the generic enumeration-safe
    response.
    """

    user: User | None
    token_result: VerificationTokenResult | None


def initiate_password_reset(db: Session, email: str) -> PasswordResetInitiation:
    """
    Look up the email, persist a reset token if the account is eligible.

    Returns a `PasswordResetInitiation`:
      - Both fields populated → caller schedules the email.
      - Both None → unknown email or inactive account; caller still returns
        the generic response (enumeration-safe).

    Sprint 594/595 diagnostic: when the email lookup fails, log the total
    user row count so we can distinguish "DB was wiped" (count=0) from
    "stored email does not match typed email" (count>0). No PII is leaked.
    """
    masked = mask_email(email)
    user = get_user_by_email(db, email)

    if not user:
        try:
            total_users = db.query(User).count()
        except Exception:  # pragma: no cover — diagnostic must never block the response
            total_users = -1
        logger.info(
            "Password reset requested for unknown email: %s (total_users=%d)",
            masked,
            total_users,
        )
        return PasswordResetInitiation(user=None, token_result=None)

    if not user.is_active:
        logger.info("Password reset requested for inactive account: %s", masked)
        return PasswordResetInitiation(user=None, token_result=None)

    token_result = generate_password_reset_token()
    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=hash_token(token_result.token),
        expires_at=token_result.expires_at,
    )
    with db_transaction(
        db,
        log_label="db_password_reset",
        log_message="Database error creating password reset token",
    ):
        db.add(reset_token)

    return PasswordResetInitiation(user=user, token_result=token_result)


def complete_password_reset(db: Session, token: str, new_password: str) -> User:
    """
    Consume a password reset token and set a new password.

    Raises `PasswordResetError` (subclass of `ValueError`) for any of:
      - unknown token
      - token already used
      - token expired
      - associated user missing or inactive

    On success: persists the new password, marks the token used, revokes all
    existing refresh tokens, resets lockout state, and returns the user.
    """
    token_hash = hash_token(token)
    reset_token = db.query(PasswordResetToken).filter(PasswordResetToken.token_hash == token_hash).first()

    if not reset_token:
        log_secure_operation("password_reset_invalid", "Invalid password reset token submitted")
        raise PasswordResetError("Invalid or expired reset link. Please request a new one.")

    if reset_token.is_used:
        log_secure_operation(
            "password_reset_reused",
            f"Attempt to reuse password reset token id={reset_token.id}",
        )
        raise PasswordResetError("This reset link has already been used. Please request a new one.")

    if reset_token.is_expired:
        log_secure_operation(
            "password_reset_expired",
            f"Expired password reset token id={reset_token.id}",
        )
        raise PasswordResetError("This reset link has expired. Please request a new one.")

    user = reset_token.user
    if not user or not user.is_active:
        raise PasswordResetError("Invalid or expired reset link. Please request a new one.")

    user.hashed_password = hash_password(new_password)
    user.password_changed_at = datetime.now(UTC)

    reset_token.used_at = datetime.now(UTC)

    # Revoke all existing refresh tokens (force re-login on all devices)
    _revoke_all_user_tokens(db, user.id)

    # Reset lockout state
    user.failed_login_attempts = 0
    user.locked_until = None

    with db_transaction(
        db,
        log_label="db_reset_password",
        log_message="Database error during password reset",
    ):
        pass  # all mutations above are flushed by db.commit() inside the context

    log_secure_operation("password_reset_success", f"Password reset completed for user {user.id}")
    return user
