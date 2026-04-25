"""
Security Middleware Module
Sprint 49: Security Hardening
Sprint 261: Stateless HMAC CSRF + DB-backed account lockout
Sprint 306: RateLimitIdentityMiddleware for user-aware rate limiting

Provides security headers, CSRF protection, request ID correlation,
rate-limit identity resolution, and account lockout functionality.
"""

import hashlib
import hmac
import ipaddress
import logging
import re
import secrets
import time
import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any, Optional

from fastapi import HTTPException
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

    def __init__(self, app: Any, production_mode: bool = False) -> None:
        super().__init__(app)
        self.production_mode = production_mode

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response: Response = await call_next(request)

        # Always add these headers
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
            "magnetometer=(), microphone=(), payment=(), usb=()"
        )

        # Production-only headers
        if self.production_mode:
            # HSTS: 1 year, include subdomains, allow preload
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
            # CSP: Strict content policy (API serves JSON, no inline scripts needed)
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self'; "
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

# Alphanumeric + hyphens, 1-64 chars — rejects log injection payloads
_REQUEST_ID_RE = re.compile(r"^[a-zA-Z0-9\-]{1,64}$")


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Generate a unique request ID for log correlation.

    Sets a UUID in contextvars for the duration of each request.
    Exposes the ID via the X-Request-ID response header.
    Validates client-supplied IDs against a strict charset/length pattern.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_rid = request.headers.get("X-Request-ID")
        rid = client_rid if client_rid and _REQUEST_ID_RE.match(client_rid) else uuid.uuid4().hex[:12]
        request_id_var.set(rid)
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response


# =============================================================================
# REQUEST BODY SIZE LIMIT
# =============================================================================

# 110 MB — slightly above the per-file 100 MB limit to allow multipart overhead
MAX_REQUEST_BODY_BYTES = 110 * 1024 * 1024


class MaxBodySizeMiddleware:
    """Reject requests whose body exceeds a global threshold.

    Two-layer enforcement:
    1. Content-Length fast-reject — catches oversized requests before any
       body bytes are read.
    2. Streaming byte counter — wraps the ASGI ``receive`` callable to count
       bytes as they arrive, enforcing the limit even when Content-Length is
       absent (e.g., chunked transfer encoding).
    """

    def __init__(self, app: Any, max_bytes: int = MAX_REQUEST_BODY_BYTES) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # --- Layer 1: Content-Length fast-reject (unchanged) ---
        headers = dict(
            (k.lower(), v) for k, v in ((k.decode("latin-1"), v.decode("latin-1")) for k, v in scope.get("headers", []))
        )
        content_length = headers.get("content-length")
        path = scope.get("path", "")
        method = scope.get("method", "")

        if content_length:
            try:
                length = int(content_length)
            except ValueError:
                log_secure_operation(
                    "malformed_content_length",
                    f"Rejected {method} {path}: non-numeric Content-Length {content_length!r}",
                )
                await self._send_json(send, 400, '{"detail":"Invalid Content-Length header"}')
                return
            if length < 0:
                log_secure_operation(
                    "negative_content_length",
                    f"Rejected {method} {path}: negative Content-Length {length}",
                )
                await self._send_json(send, 400, '{"detail":"Invalid Content-Length header"}')
                return
            if length > self.max_bytes:
                log_secure_operation(
                    "request_body_too_large",
                    f"Rejected {method} {path}: Content-Length {content_length} exceeds {self.max_bytes}",
                )
                await self._send_json(send, 413, '{"detail":"Request body too large"}')
                return

        # --- Layer 2: Streaming byte counter ---
        bytes_received = 0
        max_bytes = self.max_bytes
        exceeded = False

        async def checked_receive() -> dict:
            nonlocal bytes_received, exceeded
            message: dict = dict(await receive())
            if message.get("type") == "http.request":
                chunk = message.get("body", b"")
                bytes_received += len(chunk)
                if bytes_received > max_bytes:
                    exceeded = True
                    log_secure_operation(
                        "streaming_body_too_large",
                        f"Rejected {method} {path}: streamed body ({bytes_received} bytes) exceeds {max_bytes}",
                    )
                    raise HTTPException(
                        status_code=413,
                        detail=f"Request body exceeds maximum allowed size of {max_bytes // (1024 * 1024)} MB.",
                    )
            return message

        try:
            await self.app(scope, checked_receive, send)
        except HTTPException as exc:
            if exc.status_code == 413 and exceeded:
                await self._send_json(send, 413, '{"detail":"Request body too large"}')
            else:
                raise

    @staticmethod
    async def _send_json(send: Any, status: int, body: str) -> None:
        """Send a complete JSON error response via raw ASGI."""
        body_bytes = body.encode("utf-8")
        await send(
            {
                "type": "http.response.start",
                "status": status,
                "headers": [
                    [b"content-type", b"application/json"],
                    [b"content-length", str(len(body_bytes)).encode()],
                ],
            }
        )
        await send({"type": "http.response.body", "body": body_bytes})


# =============================================================================
# RATE LIMIT IDENTITY MIDDLEWARE (Sprint 306)
# =============================================================================


class RateLimitIdentityMiddleware(BaseHTTPMiddleware):
    """Resolve authenticated user identity for rate-limit keying.

    Performs a lightweight JWT decode (no DB query) to extract user_id and
    tier from the Authorization header. Sets:
      - request.state.rate_limit_user_id  (int or None)
      - request.state.rate_limit_user_tier (str, default "anonymous")
      - shared.rate_limits._current_tier ContextVar

    On any decode failure (missing, expired, malformed), silently falls
    through to anonymous — no 401 is raised. Authentication enforcement
    remains the responsibility of route-level dependencies.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        from shared.rate_limits import _current_tier

        user_id = None
        tier = "anonymous"

        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer ") and len(auth_header) > 7:
            token = auth_header[7:]
            import jwt as _pyjwt

            from config import JWT_ALGORITHM, JWT_SECRET_KEY

            try:
                payload = _pyjwt.decode(token, JWT_SECRET_KEY or "", algorithms=[JWT_ALGORITHM])
                sub = payload.get("sub")
                if sub is not None:
                    user_id = int(sub)
                    tier = payload.get("tier", "free")
            except _pyjwt.PyJWTError:
                # Expected decode failure (malformed / expired / bad sig) → anonymous
                pass
            except (TypeError, ValueError) as exc:
                # Payload shape anomaly (non-int 'sub', etc.) → anonymous, log for visibility
                logger.warning(
                    "rate_limit_identity: unexpected payload shape, downgrading to anonymous: %s",
                    exc.__class__.__name__,
                )

        request.state.rate_limit_user_id = user_id
        request.state.rate_limit_user_tier = tier
        _current_tier.set(tier)

        response: Response = await call_next(request)
        return response


# =============================================================================
# CSRF PROTECTION (Sprint 261: Stateless HMAC — no server-side storage)
# =============================================================================

CSRF_TOKEN_EXPIRY_MINUTES = 30

# Endpoints exempt from CSRF validation
# ---------------------------------------------------------------------------
# POLICY: These paths are exempt because they are either:
#   1. Pre-authentication (no CSRF token available):
#      /auth/login, /auth/register
#   2. Public forms with alternative protection (honeypot + rate limiting):
#      /contact/submit, /waitlist
#   3. Email-link triggered (no session context):
#      /auth/verify-email
#   4. Documentation/schema endpoints (read-only):
#      /docs, /openapi.json, /redoc, /auth/csrf
#
# NOTE: /auth/refresh is NOT exempt — it uses cookie-based auth and must
# be CSRF-protected. The refresh endpoint accepts either a valid CSRF token
# or the X-Requested-With custom header as a bootstrap-safe CSRF mitigation
# (see CSRF_CUSTOM_HEADER_PATHS).
#
# NOTE: /auth/logout is NOT exempt — it is cookie-authenticated and
# accepts the same custom-header fallback as /auth/refresh (Sprint 653).
# ---------------------------------------------------------------------------
CSRF_EXEMPT_PATHS = {
    "/auth/login",
    "/auth/register",
    "/auth/verify-email",
    "/auth/forgot-password",  # Sprint 572: Pre-auth, no CSRF token available
    "/auth/reset-password",  # Sprint 572: Pre-auth, token-authenticated via email link
    "/auth/csrf",
    "/billing/webhook",  # Sprint 366: Stripe signature verification, not cookie-authenticated
    "/contact/submit",
    "/waitlist",
    "/docs",
    "/openapi.json",
    "/redoc",
}

# Paths that historically accepted X-Requested-With as an alternative CSRF
# proof for cookie-authenticated bootstrap requests.
#
# 2026-04-20 hardening: in **production**, this fallback is no longer
# accepted — callers must provide a valid ``X-CSRF-Token``.  The dev/test
# path still honours it so local tooling that cannot mint a CSRF token
# (e.g. quick curl requests during local development) keeps working.
#
# The fetch frontend already mints a CSRF token on every refresh/logout
# (see ``useAuth`` / ``authFetch``); this change removes the server-side
# softening, not the client-side happy path.
CSRF_CUSTOM_HEADER_PATHS = {
    "/auth/refresh",
    "/auth/logout",
}

# Methods that require CSRF validation
CSRF_REQUIRED_METHODS = {"POST", "PUT", "DELETE", "PATCH"}

# Sec-Fetch-Site values that are considered *safe* for mutation requests.
# Browsers (Chrome, Firefox, Safari, Edge) send this header automatically
# on every request originating from the browser.  ``same-origin`` and
# ``same-site`` are safe; ``cross-site`` and ``none`` are not.  Non-browser
# clients (server-to-server, CLI tools) typically omit the header entirely.
_SAFE_FETCH_SITES = frozenset({"same-origin", "same-site"})


def _get_csrf_secret() -> str:
    """Get the HMAC signing secret for CSRF tokens (separate from JWT)."""
    from config import CSRF_SECRET_KEY

    return CSRF_SECRET_KEY or ""


def generate_csrf_token(user_id: str) -> str:
    """Generate a stateless HMAC-signed, user-bound CSRF token.

    Token format: {nonce}:{unix_timestamp}:{user_id}:{hmac_hex}

    No server-side storage needed — the HMAC signature proves the token
    was generated by this server, the timestamp proves it hasn't expired,
    and the user_id binds the token to the authenticated user.
    Works across multiple Gunicorn workers without shared state.
    """
    nonce = secrets.token_hex(16)
    timestamp = str(int(time.time()))
    payload = f"{nonce}:{timestamp}:{user_id}"
    signature = hmac.new(
        _get_csrf_secret().encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()

    token = f"{nonce}:{timestamp}:{user_id}:{signature}"
    log_secure_operation("csrf_token_generated", f"Token prefix: {nonce[:8]}..., user: {user_id[:8]}...")
    return token


def validate_csrf_token(token: Optional[str], expected_user_id: Optional[str] = None) -> bool:
    """Validate a stateless HMAC-signed, user-bound CSRF token.

    Verifies the HMAC signature, checks the timestamp hasn't expired,
    and optionally verifies the token was issued for the expected user.
    No server-side storage lookup needed.
    """
    if not token:
        return False

    parts = token.split(":")
    if len(parts) != 4:
        log_secure_operation("csrf_validation_failed", "Invalid token format")
        return False

    nonce, timestamp_str, user_id, provided_sig = parts

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
    payload = f"{nonce}:{timestamp_str}:{user_id}"
    expected_sig = hmac.new(
        _get_csrf_secret().encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(provided_sig, expected_sig):
        log_secure_operation("csrf_validation_failed", "Signature mismatch")
        return False

    # User binding: if expected_user_id supplied, reject on mismatch
    if expected_user_id is not None and user_id != expected_user_id:
        log_secure_operation("csrf_validation_failed", "User ID mismatch")
        return False

    return True


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    Middleware for CSRF protection using stateless HMAC-signed tokens.

    For state-changing requests (POST/PUT/DELETE/PATCH):
    - Validates Origin/Referer header against CORS_ORIGINS allow-list
    - Checks X-CSRF-Token header via HMAC signature verification
    - Binds token to the authenticated user extracted from the Bearer token
    - Exempt paths skip validation

    Sprint 261: Migrated from in-memory dict to stateless HMAC.
    Tokens are self-contained — no shared state between workers.
    Security Sprint: Added Origin/Referer enforcement and user binding.
    """

    def _validate_request_origin(self, request: Request) -> bool:
        """Return True if the request origin policy is satisfied.

        Policy (2026-04-20 hardening):

        1. If ``Origin`` or ``Referer`` is present, it must prefix-match a
           configured origin in ``CORS_ORIGINS``.  A mismatch is a hard reject.
        2. If both headers are absent but ``Sec-Fetch-Site`` indicates the
           request came from a browser (``cross-site`` or ``none``), reject —
           this catches the rare browser that suppresses Origin/Referer on a
           cross-origin request (e.g. strict Referer-Policy on the attacker
           page).
        3. If both Origin/Referer and Sec-Fetch-Site are absent, allow.  This
           covers genuine non-browser clients (CLI, server-to-server, mobile
           apps that omit both).  These clients are already authenticated via
           Bearer token which is itself not auto-attached by browsers.
        """
        from config import CORS_ORIGINS

        origin = request.headers.get("Origin")
        referer = request.headers.get("Referer")
        check = origin or referer
        if check:
            return any(check == allowed or check.startswith(allowed + "/") for allowed in CORS_ORIGINS)

        # Origin and Referer both absent — consult Sec-Fetch-Site.
        fetch_site = request.headers.get("Sec-Fetch-Site")
        if fetch_site:
            # A browser is telling us explicitly this is a cross-site or
            # navigation-initiated request — block it.  Only same-origin /
            # same-site are safe.
            return fetch_site.lower() in _SAFE_FETCH_SITES

        # Neither Origin/Referer nor Sec-Fetch-Site — treat as non-browser.
        return True

    def _extract_user_id_from_auth(self, request: Request) -> Optional[str]:
        """Decode access token to extract sub (user_id) for CSRF binding check.

        Reads the token from Authorization: Bearer (API clients) OR the
        ACCESS_COOKIE_NAME HttpOnly cookie (production browser path) — the
        same precedence used by `auth.resolve_access_token`. Sprint 718
        fix: pre-Sprint-718 this function read only the Authorization header,
        which made `expected_user_id=None` for every browser POST/PUT/DELETE/
        PATCH and silently disabled the CSRF user-binding check.

        Auth dependency handles expiry enforcement; we use verify_exp=False
        here to extract the user_id even for tokens approaching expiry within
        the request window. Any decode failure silently returns None.
        """
        import jwt as _jwt

        from config import ACCESS_COOKIE_NAME, JWT_ALGORITHM, JWT_SECRET_KEY

        token: Optional[str] = None
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
        else:
            # Sprint 718: production browser path uses HttpOnly cookies.
            cookie_token = request.cookies.get(ACCESS_COOKIE_NAME)
            if cookie_token:
                token = cookie_token
        if not token:
            return None
        try:
            payload = _jwt.decode(
                token,
                JWT_SECRET_KEY or "",
                algorithms=[JWT_ALGORITHM],
                options={"verify_exp": False},  # auth dependency handles expiry
            )
            sub = payload.get("sub")
            return str(sub) if sub else None
        except Exception:
            return None

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        method = request.method

        # Skip validation for exempt paths
        if path in CSRF_EXEMPT_PATHS:
            response: Response = await call_next(request)
            return response

        # Skip validation for safe methods
        if method not in CSRF_REQUIRED_METHODS:
            response = await call_next(request)
            return response

        # Origin/Referer enforcement — blocks cross-origin mutation requests
        if not self._validate_request_origin(request):
            log_secure_operation("csrf_blocked", f"Origin mismatch for {method} {path}")
            return Response(
                content='{"detail":"CSRF validation failed"}',
                status_code=403,
                media_type="application/json",
            )

        # Validate CSRF token for state-changing requests
        csrf_token = request.headers.get("X-CSRF-Token")
        # Extract user from Authorization header for binding check
        expected_user_id = self._extract_user_id_from_auth(request)

        # Sprint 653: /auth/refresh and /auth/logout historically ran a
        # per-request DB lookup to recover the user_id from the refresh
        # cookie for CSRF binding. Those paths are now handled by the
        # custom-header branch below (signature + origin + X-Requested-With
        # proof), which avoids opening a fresh SessionLocal() outside the
        # `get_db()` lifecycle and bypassing connection-pool accounting.

        # Cookie-auth mutation paths (refresh/logout).
        #
        # Policy (2026-04-20 hardening):
        #   * In production, a valid X-CSRF-Token is MANDATORY — the old
        #     X-Requested-With-only fallback is removed.  The frontend has
        #     been minting CSRF tokens for every refresh/logout call for
        #     months so this is a no-op for legitimate traffic.
        #   * In development/test, X-Requested-With is still accepted as a
        #     bootstrap convenience for local tooling.  This mirrors the
        #     "fail-closed in production, permissive in dev" pattern used
        #     elsewhere (rate limits, DB TLS, …).
        if path in CSRF_CUSTOM_HEADER_PATHS:
            from config import ENV_MODE

            if csrf_token:
                # Token provided — validate it
                if not validate_csrf_token(csrf_token, expected_user_id=expected_user_id):
                    log_secure_operation("csrf_blocked", f"Blocked {method} to {path} - invalid CSRF token")
                    return Response(
                        content='{"detail":"CSRF validation failed"}',
                        status_code=403,
                        media_type="application/json",
                    )
            else:
                if ENV_MODE == "production":
                    log_secure_operation(
                        "csrf_blocked",
                        f"Blocked {method} to {path} - missing CSRF token in production (X-Requested-With fallback removed)",
                    )
                    return Response(
                        content='{"detail":"CSRF validation failed"}',
                        status_code=403,
                        media_type="application/json",
                    )
                # Dev/test: X-Requested-With fallback still accepted.
                xrw = request.headers.get("X-Requested-With")
                if xrw != "XMLHttpRequest":
                    log_secure_operation(
                        "csrf_blocked", f"Blocked {method} to {path} - missing CSRF token and X-Requested-With header"
                    )
                    return Response(
                        content='{"detail":"CSRF validation failed"}',
                        status_code=403,
                        media_type="application/json",
                    )
            # Passed validation — proceed
            final_response = await call_next(request)
            return final_response

        if not validate_csrf_token(csrf_token, expected_user_id=expected_user_id):
            log_secure_operation("csrf_blocked", f"Blocked {method} to {path} - invalid/missing CSRF token")
            # Return a Response instead of raising HTTPException
            # (BaseHTTPMiddleware doesn't propagate exceptions cleanly)
            return Response(
                content='{"detail":"CSRF validation failed"}',
                status_code=403,
                media_type="application/json",
            )

        final_response: Response = await call_next(request)
        return final_response


# =============================================================================
# ACCOUNT LOCKOUT (Sprint 261: DB-backed via User model columns)
# Sprint AUDIT-07: Configurable thresholds via environment
# =============================================================================

from config import _load_optional_int

MAX_FAILED_ATTEMPTS = _load_optional_int("LOCKOUT_MAX_FAILED_ATTEMPTS", 5)
LOCKOUT_DURATION_MINUTES = _load_optional_int("LOCKOUT_DURATION_MINUTES", 15)

# =============================================================================
# PER-IP FAILURE TRACKING (AUDIT-07 Phase 4: Finding #2)
# Sprint 718: backend now lives in `shared/ip_failure_tracker.py` with a
# Redis-first / memory-fallback storage strategy. Public API preserved for
# call-site stability — `record_ip_failure`, `check_ip_blocked`,
# `reset_ip_failures` are the names touched across the codebase.
#
# Why the Redis upgrade: pre-Sprint-718 storage was a process-local dict.
# Multi-worker Render meant attackers could distribute attempts across
# workers to evade the threshold; every deploy reset the counters. The
# 2026-04-24 security review (M-03) flagged the gap — this module closes
# it by delegating to the Redis-backed shared store while preserving the
# in-memory fallback for local dev / single-worker deploys.
# =============================================================================

from shared import ip_failure_tracker as _ip_tracker

IP_FAILURE_WINDOW_SECONDS = _load_optional_int("IP_FAILURE_WINDOW_SECONDS", 900)  # 15 min
IP_FAILURE_THRESHOLD = _load_optional_int("IP_FAILURE_THRESHOLD", 20)


def record_ip_failure(ip: str) -> None:
    """Record a failed auth attempt from an IP address."""
    _ip_tracker.record_failure(ip, window_seconds=IP_FAILURE_WINDOW_SECONDS)


def check_ip_blocked(ip: str) -> bool:
    """Return True if the IP has exceeded the failure threshold within the window."""
    return _ip_tracker.is_blocked(
        ip,
        window_seconds=IP_FAILURE_WINDOW_SECONDS,
        threshold=IP_FAILURE_THRESHOLD,
    )


def reset_ip_failures(ip: str) -> None:
    """Clear failure history for an IP (e.g. after successful login)."""
    _ip_tracker.reset(ip)


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
        log_secure_operation("account_locked", f"User {user_id} locked until {locked_until.isoformat()}")
    else:
        log_secure_operation("login_failed", f"User {user_id} failed attempt {failed_count}/{MAX_FAILED_ATTEMPTS}")

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
        "lockout_duration_minutes": LOCKOUT_DURATION_MINUTES,
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
        "lockout_duration_minutes": LOCKOUT_DURATION_MINUTES,
    }


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def hash_ip_address(ip: str) -> str:
    """Hash an IP address for privacy-compliant logging."""
    return hashlib.sha256(ip.encode()).hexdigest()[:16]


def is_trusted_proxy(peer_ip: str, trusted: frozenset[str]) -> bool:
    """Return True if peer_ip matches any entry in trusted (exact IP or CIDR).

    Entries may be:
    - Exact IPv4/IPv6 addresses: "127.0.0.1", "::1"
    - CIDR networks:  "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"

    Invalid entries are silently skipped so a misconfigured env var cannot
    cause startup failures — the result is simply "not trusted".
    """
    if not trusted:
        return False
    try:
        addr = ipaddress.ip_address(peer_ip)
    except ValueError:
        return False
    for entry in trusted:
        try:
            if "/" in entry:
                if addr in ipaddress.ip_network(entry, strict=False):
                    return True
            else:
                if addr == ipaddress.ip_address(entry):
                    return True
        except ValueError:
            continue
    return False


def get_client_ip(request: Request) -> str:
    """Extract client IP from request, respecting proxy trust.

    Sprint 279: Only trusts X-Forwarded-For when the direct peer is
    in TRUSTED_PROXY_IPS.  Prevents IP spoofing via header injection.
    CIDR ranges and exact IPs are both supported (is_trusted_proxy).
    """
    from config import TRUSTED_PROXY_IPS

    peer_ip = request.client.host if request.client else "unknown"

    if is_trusted_proxy(peer_ip, TRUSTED_PROXY_IPS):
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

    return peer_ip


# =============================================================================
# IMPERSONATION READ-ONLY MIDDLEWARE (Sprint 590)
# =============================================================================

_MUTATION_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


class ImpersonationMiddleware(BaseHTTPMiddleware):
    """Block mutations when the request carries an impersonation JWT.

    Impersonation tokens include an `imp: true` claim. When detected,
    all state-changing HTTP methods are rejected with 403.

    This middleware runs early (before route dispatch) so it catches
    all mutation attempts regardless of endpoint.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.method not in _MUTATION_METHODS:
            return await call_next(request)

        # Check for impersonation token in Authorization header
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return await call_next(request)

        token_str = auth_header[7:]
        import jwt as _jwt

        from config import JWT_ALGORITHM, JWT_SECRET_KEY

        try:
            payload = _jwt.decode(
                token_str,
                JWT_SECRET_KEY or "",
                algorithms=[JWT_ALGORITHM],
                options={"verify_exp": False},  # Just checking the flag, not validating
            )
        except _jwt.PyJWTError:
            # Not a valid JWT — let downstream auth dependency return 401
            return await call_next(request)

        if payload.get("imp"):
            # Sprint 661: Revoked impersonation tokens stop blocking mutations
            # so an admin can end a session immediately rather than waiting
            # for the 15-minute `exp`. Since the middleware uses
            # verify_exp=False, revocation is the only server-side way to
            # release the block after issuance.
            from shared.impersonation_revocation import is_revoked

            if is_revoked(payload.get("jti")):
                return await call_next(request)

            from starlette.responses import JSONResponse

            return JSONResponse(
                status_code=403,
                content={
                    "code": "IMPERSONATION_READ_ONLY",
                    "message": "Impersonation sessions are read-only.",
                    "detail": "Impersonation sessions are read-only.",
                },
            )

        return await call_next(request)
