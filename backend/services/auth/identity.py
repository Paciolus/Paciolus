"""
Identity service (Sprint 746b).

Extracts the login / refresh / logout business logic from
`routes/auth_routes.py`. Cookie writes (`_set_refresh_cookie`,
`_set_access_cookie`, `_clear_*`) and HTTP plumbing (Request, Response,
HTTPException-with-headers) stay in the route layer per the boundary
established in ADR-015 — those are security-sensitive primitives that
should not be touched without a specific audit finding.

The service produces an `IdentityIssuance` value object with everything
the route needs to write cookies and build the `AuthResponse`. The route
remains responsible for:

  - Cookie writes (refresh cookie SameSite/Secure semantics differ between
    login `remember_me=True/False` and refresh, by design).
  - `AuthResponse` model assembly.
  - Pre-handler concerns: rate limiting (decorator), `X-Requested-With`
    enforcement on `/auth/refresh`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from auth import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_user_by_email,
    revoke_refresh_token,
    rotate_refresh_token,
)
from config import JWT_EXPIRATION_MINUTES
from models import User
from security_middleware import (
    check_ip_blocked,
    check_lockout_status,
    generate_csrf_token,
    hash_ip_address,
    record_failed_login,
    record_ip_failure,
    reset_failed_attempts,
    reset_ip_failures,
)
from security_utils import log_secure_operation
from services.auth.security_responses import raise_invalid_credentials


@dataclass(frozen=True)
class IdentityIssuance:
    """
    Result of `authenticate_login` or `refresh_session`.

    Carries everything the route needs to write cookies and assemble the
    `AuthResponse` payload.
    """

    user: User
    access_token: str
    raw_refresh_token: str
    expires_in: int
    csrf_token: str


def authenticate_login(
    db: Session,
    *,
    email: str,
    password: str,
    client_ip: str,
    user_agent: str | None,
    request_host: str | None,
) -> IdentityIssuance:
    """
    Run the full login pipeline and return tokens for cookie + response.

    Pipeline (AUDIT-07 F2 + F4):
      1. Per-IP brute-force gate (`check_ip_blocked`).
      2. Lockout check on the resolved user (if email exists).
      3. Authenticate via `authenticate_user`.
      4. On any failure: record per-IP + per-user failure counters; raise
         the enumeration-safe 401 (`raise_invalid_credentials`).
      5. On success: reset failure counters, mint access + refresh tokens,
         generate CSRF.

    Cookies are NOT written here — the caller does that with the returned
    `raw_refresh_token` and `access_token` (the route owns `remember_me`
    semantics on the refresh cookie).
    """
    if check_ip_blocked(client_ip):
        log_secure_operation("ip_blocked", f"IP {hash_ip_address(client_ip)} blocked: threshold exceeded")
        raise_invalid_credentials()

    existing_user = get_user_by_email(db, email)

    if existing_user is not None:
        is_locked, _locked_until, _remaining = check_lockout_status(db, existing_user.id)
        if is_locked:
            record_ip_failure(client_ip)
            raise_invalid_credentials()

    user = authenticate_user(db, email, password)
    if user is None:
        if existing_user is not None:
            record_failed_login(db, existing_user.id)
        record_ip_failure(client_ip)
        raise_invalid_credentials()

    reset_failed_attempts(db, user.id)
    reset_ip_failures(client_ip)

    access_token, expires = create_access_token(user.id, user.email, user.password_changed_at, tier=user.tier.value)
    expires_in = int((expires - datetime.now(UTC)).total_seconds())

    raw_refresh_token, _ = create_refresh_token(
        db,
        user.id,
        user_agent=user_agent,
        ip_address=request_host,
    )

    csrf_token_value = generate_csrf_token(user_id=str(user.id))

    return IdentityIssuance(
        user=user,
        access_token=access_token,
        raw_refresh_token=raw_refresh_token,
        expires_in=expires_in,
        csrf_token=csrf_token_value,
    )


def refresh_session(
    db: Session,
    *,
    raw_refresh_token: str,
) -> IdentityIssuance:
    """
    Rotate the refresh token and mint a fresh access + refresh pair.

    Delegates to `auth.rotate_refresh_token` for the validation +
    revoke-old + issue-new sequence. Generates a new CSRF token tied to
    the user.

    Raises:
        HTTPException: as raised by `rotate_refresh_token` for invalid /
            expired / revoked tokens.
    """
    access_token, new_refresh_token, user = rotate_refresh_token(db, raw_refresh_token)
    expires_in = JWT_EXPIRATION_MINUTES * 60
    csrf_token_value = generate_csrf_token(user_id=str(user.id))

    return IdentityIssuance(
        user=user,
        access_token=access_token,
        raw_refresh_token=new_refresh_token,
        expires_in=expires_in,
        csrf_token=csrf_token_value,
    )


def revoke_session_token(db: Session, raw_refresh_token: str) -> bool:
    """
    Revoke a refresh token (logout).

    Idempotent — returns `False` if the token was unknown or already revoked.
    The caller is responsible for clearing the cookies regardless of the
    result, so logout always succeeds from the client's perspective.
    """
    return revoke_refresh_token(db, raw_refresh_token)
