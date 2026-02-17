"""
Security Middleware Module
Sprint 49: Security Hardening
Sprint 261: Stateless HMAC CSRF + DB-backed account lockout

Provides security headers, CSRF protection, request ID correlation,
and account lockout functionality.
"""

import hashlib
import hmac
import logging
import secrets
import time
import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from logging_config import request_id_var
from security_utils import log_secure_operation

logger = logging.getLogger(__name__)


# =============================================================================
# SECURITY HEADERS MIDDLEWARE
# =============================================================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.

    Headers added:
    - X-Frame-Options: DENY (prevent clickjacking)
    - X-Content-Type-Options: nosniff (prevent MIME sniffing)
    - X-XSS-Protection: 1; mode=block (legacy XSS protection)
    - Referrer-Policy: strict-origin-when-cross-origin
    - Permissions-Policy: Restrict browser features
    - Content-Security-Policy: Restrict content sources (production only)
    - Strict-Transport-Security: HSTS (production only)
    """

    def __init__(self, app, production_mode: bool = False):
        super().__init__(app)
        self.production_mode = production_mode

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Always add these headers
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
            "magnetometer=(), microphone=(), payment=(), usb=()"
        )

        # Production-only headers
        if self.production_mode:
            # HSTS: 1 year, include subdomains, allow preload
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
            # CSP: Strict content policy
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )

        return response


# =============================================================================
# REQUEST ID MIDDLEWARE (Sprint 211)
# =============================================================================

class RequestIdMiddleware(BaseHTTPMiddleware):
    """Generate a unique request ID for log correlation.

    Sets a UUID in contextvars for the duration of each request.
    Exposes the ID via the X-Request-ID response header.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
        request_id_var.set(rid)
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response


# =============================================================================
# REQUEST BODY SIZE LIMIT
# =============================================================================

# 110 MB — slightly above the per-file 100 MB limit to allow multipart overhead
MAX_REQUEST_BODY_BYTES = 110 * 1024 * 1024


class MaxBodySizeMiddleware(BaseHTTPMiddleware):
    """Reject requests whose Content-Length exceeds a global threshold.

    This catches oversized payloads *before* the framework reads the full body,
    acting as a coarse safety net alongside the per-route validate_file_size().
    """

    def __init__(self, app, max_bytes: int = MAX_REQUEST_BODY_BYTES):
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_bytes:
            log_secure_operation(
                "request_body_too_large",
                f"Rejected {request.method} {request.url.path}: "
                f"Content-Length {content_length} exceeds {self.max_bytes}"
            )
            return Response(
                content='{"detail":"Request body too large"}',
                status_code=413,
                media_type="application/json",
            )
        return await call_next(request)


# =============================================================================
# CSRF PROTECTION (Sprint 261: Stateless HMAC — no server-side storage)
# =============================================================================

CSRF_TOKEN_EXPIRY_MINUTES = 60

# Endpoints exempt from CSRF validation
# ---------------------------------------------------------------------------
# POLICY: These paths are exempt because they are either:
#   1. Pre-authentication (no CSRF token available):
#      /auth/login, /auth/register
#   2. Token-authenticated via Authorization header (not cookie-authenticated):
#      /auth/refresh, /auth/logout
#   3. Public forms with alternative protection (honeypot + rate limiting):
#      /contact/submit, /waitlist
#   4. Email-link triggered (no session context):
#      /auth/verify-email
#   5. Documentation/schema endpoints (read-only):
#      /docs, /openapi.json, /redoc, /auth/csrf
#
# IMPORTANT: /auth/refresh and /auth/logout are exempt ONLY because they
# use the Authorization header (Bearer token), NOT cookies. If cookie-based
# refresh is ever introduced, CSRF MUST be enforced on those paths.
# ---------------------------------------------------------------------------
CSRF_EXEMPT_PATHS = {
    "/auth/login",
    "/auth/register",
    "/auth/refresh",
    "/auth/logout",
    "/auth/verify-email",
    "/auth/csrf",
    "/contact/submit",
    "/waitlist",
    "/docs",
    "/openapi.json",
    "/redoc",
}

# Methods that require CSRF validation
CSRF_REQUIRED_METHODS = {"POST", "PUT", "DELETE", "PATCH"}


def _get_csrf_secret() -> str:
    """Get the HMAC signing secret for CSRF tokens (separate from JWT)."""
    from config import CSRF_SECRET_KEY
    return CSRF_SECRET_KEY


def generate_csrf_token() -> str:
    """Generate a stateless HMAC-signed CSRF token.

    Token format: {nonce}:{unix_timestamp}:{hmac_hex}

    No server-side storage needed — the HMAC signature proves the token
    was generated by this server and the timestamp proves it hasn't expired.
    Works across multiple Gunicorn workers without shared state.
    """
    nonce = secrets.token_hex(16)
    timestamp = str(int(time.time()))
    payload = f"{nonce}:{timestamp}"
    signature = hmac.new(
        _get_csrf_secret().encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()

    token = f"{nonce}:{timestamp}:{signature}"
    log_secure_operation("csrf_token_generated", f"Token prefix: {nonce[:8]}...")
    return token


def validate_csrf_token(token: Optional[str]) -> bool:
    """Validate a stateless HMAC-signed CSRF token.

    Verifies the HMAC signature and checks the timestamp hasn't expired.
    No server-side storage lookup needed.
    """
    if not token:
        return False

    parts = token.split(":")
    if len(parts) != 3:
        log_secure_operation("csrf_validation_failed", "Invalid token format")
        return False

    nonce, timestamp_str, provided_sig = parts

    # Verify timestamp is a valid integer
    try:
        token_time = int(timestamp_str)
    except ValueError:
        log_secure_operation("csrf_validation_failed", "Invalid timestamp")
        return False

    # Check expiration
    age_seconds = time.time() - token_time
    if age_seconds > CSRF_TOKEN_EXPIRY_MINUTES * 60:
        log_secure_operation("csrf_validation_failed", "Token expired")
        return False

    if age_seconds < 0:
        log_secure_operation("csrf_validation_failed", "Token timestamp in future")
        return False

    # Recompute HMAC and compare (constant-time)
    payload = f"{nonce}:{timestamp_str}"
    expected_sig = hmac.new(
        _get_csrf_secret().encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(provided_sig, expected_sig):
        log_secure_operation("csrf_validation_failed", "Signature mismatch")
        return False

    return True


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    Middleware for CSRF protection using stateless HMAC-signed tokens.

    For state-changing requests (POST/PUT/DELETE/PATCH):
    - Checks X-CSRF-Token header via HMAC signature verification
    - Exempt paths skip validation

    Sprint 261: Migrated from in-memory dict to stateless HMAC.
    Tokens are self-contained — no shared state between workers.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        method = request.method

        # Skip validation for exempt paths
        if path in CSRF_EXEMPT_PATHS:
            return await call_next(request)

        # Skip validation for safe methods
        if method not in CSRF_REQUIRED_METHODS:
            return await call_next(request)

        # Validate CSRF token for state-changing requests
        csrf_token = request.headers.get("X-CSRF-Token")

        if not validate_csrf_token(csrf_token):
            log_secure_operation(
                "csrf_blocked",
                f"Blocked {method} to {path} - invalid/missing CSRF token"
            )
            # Return a Response instead of raising HTTPException
            # (BaseHTTPMiddleware doesn't propagate exceptions cleanly)
            return Response(
                content='{"detail":"CSRF validation failed"}',
                status_code=403,
                media_type="application/json",
            )

        return await call_next(request)


# =============================================================================
# ACCOUNT LOCKOUT (Sprint 261: DB-backed via User model columns)
# =============================================================================

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15


def record_failed_login(db: Session, user_id: int) -> tuple[int, Optional[datetime]]:
    """
    Record a failed login attempt for a user (DB-backed).

    Returns:
        Tuple of (failed_count, locked_until or None)
    """
    from models import User

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        # Should not happen — caller should verify user exists
        return (1, None)

    failed_count = (user.failed_login_attempts or 0) + 1
    user.failed_login_attempts = failed_count
    locked_until = None

    if failed_count >= MAX_FAILED_ATTEMPTS:
        locked_until = datetime.now(UTC) + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
        user.locked_until = locked_until
        log_secure_operation(
            "account_locked",
            f"User {user_id} locked until {locked_until.isoformat()}"
        )
    else:
        log_secure_operation(
            "login_failed",
            f"User {user_id} failed attempt {failed_count}/{MAX_FAILED_ATTEMPTS}"
        )

    db.commit()
    return (failed_count, locked_until)


def check_lockout_status(db: Session, user_id: int) -> tuple[bool, Optional[datetime], int]:
    """
    Check if a user account is currently locked (DB-backed).

    Returns:
        Tuple of (is_locked, locked_until or None, remaining_attempts)
    """
    from models import User

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        return (False, None, MAX_FAILED_ATTEMPTS)

    failed_count = user.failed_login_attempts or 0
    locked_until = user.locked_until

    # Handle timezone-naive datetimes from SQLite
    if locked_until and locked_until.tzinfo is None:
        from datetime import timezone
        locked_until = locked_until.replace(tzinfo=timezone.utc)

    # Check if lockout has expired
    if locked_until and datetime.now(UTC) >= locked_until:
        # Lockout expired, reset
        user.failed_login_attempts = 0
        user.locked_until = None
        db.commit()
        log_secure_operation("lockout_expired", f"User {user_id} lockout expired")
        return (False, None, MAX_FAILED_ATTEMPTS)

    # Currently locked
    if locked_until:
        return (True, locked_until, 0)

    # Not locked yet, return remaining attempts
    remaining = MAX_FAILED_ATTEMPTS - failed_count
    return (False, None, remaining)


def reset_failed_attempts(db: Session, user_id: int) -> None:
    """Reset failed login attempts after successful login (DB-backed)."""
    from models import User

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        return

    if user.failed_login_attempts or user.locked_until:
        user.failed_login_attempts = 0
        user.locked_until = None
        db.commit()
        log_secure_operation("lockout_reset", f"User {user_id} failed attempts reset")


def get_lockout_info(db: Session, user_id: int) -> dict:
    """Get lockout information for API responses (DB-backed)."""
    is_locked, locked_until, remaining = check_lockout_status(db, user_id)

    return {
        "is_locked": is_locked,
        "locked_until": locked_until.isoformat() if locked_until else None,
        "remaining_attempts": remaining if not is_locked else 0,
        "max_attempts": MAX_FAILED_ATTEMPTS,
        "lockout_duration_minutes": LOCKOUT_DURATION_MINUTES
    }


def get_fake_lockout_info() -> dict:
    """Return lockout info for non-existent users (prevents account enumeration).

    Returns the same structure as get_lockout_info() for a fresh account,
    so the response shape doesn't reveal whether the email exists.
    """
    return {
        "is_locked": False,
        "locked_until": None,
        "remaining_attempts": MAX_FAILED_ATTEMPTS - 1,
        "max_attempts": MAX_FAILED_ATTEMPTS,
        "lockout_duration_minutes": LOCKOUT_DURATION_MINUTES
    }


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def hash_ip_address(ip: str) -> str:
    """Hash an IP address for privacy-compliant logging."""
    return hashlib.sha256(ip.encode()).hexdigest()[:16]


def get_client_ip(request: Request) -> str:
    """Extract client IP from request, respecting proxy trust.

    Sprint 279: Only trusts X-Forwarded-For when the direct peer is
    in TRUSTED_PROXY_IPS.  Prevents IP spoofing via header injection.
    """
    from config import TRUSTED_PROXY_IPS

    peer_ip = request.client.host if request.client else "unknown"

    if TRUSTED_PROXY_IPS and peer_ip in TRUSTED_PROXY_IPS:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

    return peer_ip
