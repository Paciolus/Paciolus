"""
Security Middleware Module
Sprint 49: Security Hardening

Provides security headers, CSRF protection, and account lockout functionality.
"""

import secrets
import hashlib
from datetime import datetime, timedelta, UTC
from typing import Optional, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import HTTPException, status

from security_utils import log_secure_operation


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
# CSRF PROTECTION
# =============================================================================

# In-memory CSRF token storage (for stateless operation)
# In production, consider using signed cookies or JWT-embedded tokens
_csrf_tokens: dict[str, datetime] = {}
CSRF_TOKEN_EXPIRY_MINUTES = 60
CSRF_TOKEN_LENGTH = 32

# Endpoints exempt from CSRF validation
CSRF_EXEMPT_PATHS = {
    "/auth/login",
    "/auth/register",
    "/auth/csrf",
    "/docs",
    "/openapi.json",
    "/redoc",
}

# Methods that require CSRF validation
CSRF_REQUIRED_METHODS = {"POST", "PUT", "DELETE", "PATCH"}


def generate_csrf_token() -> str:
    """Generate a cryptographically secure CSRF token."""
    token = secrets.token_hex(CSRF_TOKEN_LENGTH)
    _csrf_tokens[token] = datetime.now(UTC)

    # Clean up expired tokens periodically
    _cleanup_expired_tokens()

    log_secure_operation("csrf_token_generated", f"Token prefix: {token[:8]}...")
    return token


def validate_csrf_token(token: Optional[str]) -> bool:
    """
    Validate a CSRF token.

    Returns True if valid, False otherwise.
    """
    if not token:
        return False

    created_at = _csrf_tokens.get(token)
    if created_at is None:
        log_secure_operation("csrf_validation_failed", "Token not found")
        return False

    # Check expiration
    if datetime.now(UTC) - created_at > timedelta(minutes=CSRF_TOKEN_EXPIRY_MINUTES):
        del _csrf_tokens[token]
        log_secure_operation("csrf_validation_failed", "Token expired")
        return False

    return True


def _cleanup_expired_tokens() -> None:
    """Remove expired tokens from memory."""
    now = datetime.now(UTC)
    expired = [
        token for token, created in _csrf_tokens.items()
        if now - created > timedelta(minutes=CSRF_TOKEN_EXPIRY_MINUTES)
    ]
    for token in expired:
        del _csrf_tokens[token]

    if expired:
        log_secure_operation("csrf_cleanup", f"Removed {len(expired)} expired tokens")


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    Middleware for CSRF protection using double-submit cookie pattern.

    For state-changing requests (POST/PUT/DELETE/PATCH):
    - Checks X-CSRF-Token header against stored tokens
    - Exempt paths skip validation

    For GET requests to /auth/csrf:
    - Generates and returns a new CSRF token
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
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF validation failed"
            )

        return await call_next(request)


# =============================================================================
# ACCOUNT LOCKOUT
# =============================================================================

# In-memory lockout tracking
# Key: user_id, Value: (failed_count, locked_until)
_lockout_tracker: dict[int, tuple[int, Optional[datetime]]] = {}

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15


def record_failed_login(user_id: int) -> tuple[int, Optional[datetime]]:
    """
    Record a failed login attempt for a user.

    Returns:
        Tuple of (failed_count, locked_until or None)
    """
    current = _lockout_tracker.get(user_id, (0, None))
    failed_count = current[0] + 1
    locked_until = None

    if failed_count >= MAX_FAILED_ATTEMPTS:
        locked_until = datetime.now(UTC) + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
        log_secure_operation(
            "account_locked",
            f"User {user_id} locked until {locked_until.isoformat()}"
        )
    else:
        log_secure_operation(
            "login_failed",
            f"User {user_id} failed attempt {failed_count}/{MAX_FAILED_ATTEMPTS}"
        )

    _lockout_tracker[user_id] = (failed_count, locked_until)
    return (failed_count, locked_until)


def check_lockout_status(user_id: int) -> tuple[bool, Optional[datetime], int]:
    """
    Check if a user account is currently locked.

    Returns:
        Tuple of (is_locked, locked_until or None, remaining_attempts)
    """
    current = _lockout_tracker.get(user_id)

    if current is None:
        return (False, None, MAX_FAILED_ATTEMPTS)

    failed_count, locked_until = current

    # Check if lockout has expired
    if locked_until and datetime.now(UTC) >= locked_until:
        # Lockout expired, reset
        del _lockout_tracker[user_id]
        log_secure_operation("lockout_expired", f"User {user_id} lockout expired")
        return (False, None, MAX_FAILED_ATTEMPTS)

    # Currently locked
    if locked_until:
        return (True, locked_until, 0)

    # Not locked yet, return remaining attempts
    remaining = MAX_FAILED_ATTEMPTS - failed_count
    return (False, None, remaining)


def reset_failed_attempts(user_id: int) -> None:
    """Reset failed login attempts after successful login."""
    if user_id in _lockout_tracker:
        del _lockout_tracker[user_id]
        log_secure_operation("lockout_reset", f"User {user_id} failed attempts reset")


def get_lockout_info(user_id: int) -> dict:
    """Get lockout information for API responses."""
    is_locked, locked_until, remaining = check_lockout_status(user_id)

    return {
        "is_locked": is_locked,
        "locked_until": locked_until.isoformat() if locked_until else None,
        "remaining_attempts": remaining if not is_locked else 0,
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
    """Extract client IP from request, handling proxies."""
    # Check X-Forwarded-For header (set by reverse proxies)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Take the first IP in the chain (original client)
        return forwarded.split(",")[0].strip()

    # Fall back to direct client
    return request.client.host if request.client else "unknown"
