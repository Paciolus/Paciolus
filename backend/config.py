"""
Paciolus Configuration Module
Hard fails if required variables are not set in any secrets backend.

Secret resolution priority: env vars (.env if present) > Docker secrets > cloud providers.
Cloud platforms (Render, etc.) inject env vars directly — .env file is optional.
"""

import sys
from pathlib import Path

from dotenv import load_dotenv

from secrets_manager import get_secret as _resolve_secret
from secrets_manager import get_secrets_manager

# Determine the .env file path
ENV_FILE = Path(__file__).parent / ".env"


import logging as _logging

_config_logger = _logging.getLogger("paciolus.config")


def _hard_fail(message: str) -> None:
    """Log error message and exit with failure code."""
    _config_logger.critical(
        "CONFIGURATION ERROR - Paciolus cannot start: %s | "
        "Please create a .env file based on .env.example. Expected location: %s",
        message,
        ENV_FILE,
    )
    sys.exit(1)


def _load_required(var_name: str) -> str:
    """Load a required config value (env > Docker secrets > cloud) or hard fail."""
    value = _resolve_secret(var_name)
    if value is None or value.strip() == "":
        _hard_fail(f"Required configuration '{var_name}' is not set in any secrets backend.")
        raise SystemExit(1)  # unreachable, but satisfies mypy
    return value.strip()


def _load_optional(var_name: str, default: str) -> str:
    """Load an optional config value (env > Docker secrets > cloud) with a default."""
    value = _resolve_secret(var_name)
    if value is None or value.strip() == "":
        return default
    return value.strip()


# Load environment variables from .env file if present.
# Cloud platforms (Render, etc.) inject env vars directly — no .env file needed.
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    load_dotenv()  # Still pick up any .env in parent dirs or pre-set env vars

# =============================================================================
# REQUIRED CONFIGURATION
# =============================================================================

# Environment mode (development/production)
ENV_MODE = _load_optional("ENV_MODE", "development")

# API URL that the backend is served from (used for CORS)
API_HOST = _load_required("API_HOST")
API_PORT = int(_load_required("API_PORT"))

# Allowed frontend origins for CORS (comma-separated)
_cors_raw = _load_required("CORS_ORIGINS")
CORS_ORIGINS = [
    origin.strip()
    for origin in _cors_raw.split(",")
    if origin.strip()  # Filter empty strings
]

# Production CORS validation (Sprint 24)
if ENV_MODE == "production":
    # Validate no wildcards in production
    if "*" in _cors_raw:
        _hard_fail(
            "Wildcard (*) CORS origins are not allowed in production mode.\n"
            "Please specify explicit origins in CORS_ORIGINS."
        )
    # Validate HTTPS in production — hard fail on non-HTTPS origins
    for origin in CORS_ORIGINS:
        if not origin.startswith("https://"):
            _hard_fail(
                f"Non-HTTPS CORS origin in production: {origin}\nAll CORS_ORIGINS must use https:// in production mode."
            )

# =============================================================================
# OPTIONAL CONFIGURATION
# =============================================================================

# Debug mode (enables detailed error messages)
DEBUG = _load_optional("DEBUG", "false").lower() == "true"

# Cookie security — HttpOnly cookies use Secure flag in production
COOKIE_SECURE = ENV_MODE == "production"
REFRESH_COOKIE_NAME = "paciolus_refresh"
ACCESS_COOKIE_NAME = "paciolus_access"

# =============================================================================
# AUTHENTICATION CONFIGURATION (Day 13)
# =============================================================================

# JWT Secret Key - REQUIRED for production, auto-generated for development
_jwt_secret = _resolve_secret("JWT_SECRET_KEY")
_using_generated_jwt = False

if _jwt_secret is None or _jwt_secret.strip() == "":
    if ENV_MODE == "production":
        _hard_fail("JWT_SECRET_KEY is required in production mode.")
    else:
        # Development fallback - generate a random key (not for production!)
        import secrets

        _jwt_secret = secrets.token_hex(32)
        _using_generated_jwt = True
        _config_logger.warning("JWT_SECRET_KEY not set. Using auto-generated key for development.")

# Sprint 25: Additional security validation
# Warn if using auto-generated key while bound to public interfaces
if _using_generated_jwt and API_HOST in ("0.0.0.0", "::"):  # nosec B104 — comparison check, not a bind
    _config_logger.warning(
        "SECURITY: Auto-generated JWT key with public binding to '%s'. "
        "JWT tokens can be forged and sessions will be invalidated on restart. "
        "Set JWT_SECRET_KEY in your .env file.",
        API_HOST,
    )

JWT_SECRET_KEY = _jwt_secret

# Validate JWT secret strength (minimum 32 characters for HS256)
if not _using_generated_jwt and JWT_SECRET_KEY is not None and len(JWT_SECRET_KEY) < 32:
    if ENV_MODE == "production":
        _hard_fail(
            f"JWT_SECRET_KEY is too short ({len(JWT_SECRET_KEY)} chars).\n"
            "For HS256, use at least 32 characters (64 hex chars recommended).\n"
            f'Generate a secure key with: python -c "import secrets; print(secrets.token_hex(32))"'
        )
    else:
        _config_logger.warning(
            "JWT_SECRET_KEY is short (%d chars). Use at least 32 characters for production.",
            len(JWT_SECRET_KEY),
        )

# Hardcoded — only HS256 is supported. Operator-configurable algorithms
# risk downgrade attacks (e.g., "none" algorithm). Sprint 279.
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = int(
    _load_optional("JWT_EXPIRATION_MINUTES", "15")
)  # 15 minutes default (reduced from 30 to limit XSS blast radius)
REFRESH_TOKEN_EXPIRATION_DAYS = int(_load_optional("REFRESH_TOKEN_EXPIRATION_DAYS", "7"))

# =============================================================================
# CSRF SECRET (Packet 6: Separate from JWT secret)
# =============================================================================

# CSRF Secret Key - REQUIRED for production, auto-generated for development
# Used exclusively for HMAC-signing stateless CSRF tokens. Must differ from JWT secret.
_csrf_secret = _resolve_secret("CSRF_SECRET_KEY")
_using_generated_csrf = False

if _csrf_secret is None or _csrf_secret.strip() == "":
    if ENV_MODE == "production":
        _hard_fail(
            "CSRF_SECRET_KEY is required in production mode.\n"
            'Generate a secure key with: python -c "import secrets; print(secrets.token_hex(32))"'
        )
    else:
        import secrets as _csrf_secrets_mod

        _csrf_secret = _csrf_secrets_mod.token_hex(32)
        _using_generated_csrf = True
        _config_logger.warning("CSRF_SECRET_KEY not set. Using auto-generated key for development.")

CSRF_SECRET_KEY = _csrf_secret

# Validate CSRF secret strength (minimum 32 characters)
if not _using_generated_csrf and CSRF_SECRET_KEY is not None and len(CSRF_SECRET_KEY) < 32:
    if ENV_MODE == "production":
        _hard_fail(
            f"CSRF_SECRET_KEY is too short ({len(CSRF_SECRET_KEY)} chars).\n"
            "Use at least 32 characters (64 hex chars recommended).\n"
            f'Generate a secure key with: python -c "import secrets; print(secrets.token_hex(32))"'
        )
    else:
        _config_logger.warning(
            "CSRF_SECRET_KEY is short (%d chars). Use at least 32 characters for production.",
            len(CSRF_SECRET_KEY),
        )

# Production guardrail: CSRF and JWT secrets must differ
if (
    ENV_MODE == "production"
    and not _using_generated_jwt
    and not _using_generated_csrf
    and CSRF_SECRET_KEY == JWT_SECRET_KEY
):
    _hard_fail(
        "CSRF_SECRET_KEY must differ from JWT_SECRET_KEY in production.\n"
        "Using the same key for both weakens the security boundary.\n"
        'Generate a separate key with: python -c "import secrets; print(secrets.token_hex(32))"'
    )

# =============================================================================
# AUDIT CHAIN SECRET (Secret domain separation — independent from JWT)
# =============================================================================

# Audit Chain Secret Key — HMAC key for audit log chain integrity (SOC 2 CC7.4).
# Falls back to JWT_SECRET_KEY if unset for backward compatibility.
# In production, set a dedicated key so JWT rotation doesn't break audit chains.
_audit_chain_secret = _resolve_secret("AUDIT_CHAIN_SECRET_KEY")

if _audit_chain_secret is None or _audit_chain_secret.strip() == "":
    _audit_chain_secret = JWT_SECRET_KEY
    if ENV_MODE == "production" and not _using_generated_jwt:
        _config_logger.warning(
            "AUDIT_CHAIN_SECRET_KEY not set — falling back to JWT_SECRET_KEY. "
            "Set a dedicated key for independent rotation."
        )

AUDIT_CHAIN_SECRET_KEY = _audit_chain_secret

# Validate strength when explicitly set (not falling back to JWT)
if AUDIT_CHAIN_SECRET_KEY != JWT_SECRET_KEY and AUDIT_CHAIN_SECRET_KEY is not None and len(AUDIT_CHAIN_SECRET_KEY) < 32:
    if ENV_MODE == "production":
        _hard_fail(
            f"AUDIT_CHAIN_SECRET_KEY is too short ({len(AUDIT_CHAIN_SECRET_KEY)} chars).\n"
            "Use at least 32 characters (64 hex chars recommended).\n"
            'Generate a secure key with: python -c "import secrets; print(secrets.token_hex(32))"'
        )
    else:
        _config_logger.warning(
            "AUDIT_CHAIN_SECRET_KEY is short (%d chars). Use at least 32 characters for production.",
            len(AUDIT_CHAIN_SECRET_KEY),
        )

# =============================================================================
# PROXY TRUST (Sprint 279 — X-Forwarded-For spoofing protection)
# =============================================================================

# Comma-separated list of trusted reverse proxy IPs.
# Only X-Forwarded-For from these IPs is honored for rate limiting.
# Default: empty (trust direct connection IP only).
# Typical: "127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"
_trusted_raw = _load_optional("TRUSTED_PROXY_IPS", "")
TRUSTED_PROXY_IPS: frozenset[str] = frozenset(ip.strip() for ip in _trusted_raw.split(",") if ip.strip())

# =============================================================================
# REDIS (Optional — shared rate-limit storage)
# =============================================================================
# When set, rate-limit counters are stored in Redis and shared across all
# Gunicorn workers and server instances.  When empty, in-memory counters
# are used (reset on restart, not shared across workers).
REDIS_URL = _load_optional("REDIS_URL", "")

# Fail-closed mode: refuse to start if Redis is unavailable.
# Default: true in production, false in development/test.
_strict_default = "true" if ENV_MODE == "production" else "false"
RATE_LIMIT_STRICT_MODE = _load_optional("RATE_LIMIT_STRICT_MODE", _strict_default).lower() == "true"

# Production guardrail: strict mode requires REDIS_URL to be configured
if RATE_LIMIT_STRICT_MODE and not REDIS_URL:
    _hard_fail(
        "RATE_LIMIT_STRICT_MODE is enabled but REDIS_URL is not set.\n"
        "Rate limiting requires shared Redis storage in strict mode to prevent\n"
        "per-worker counter isolation under multi-instance deployments.\n"
        "Either set REDIS_URL or disable strict mode: RATE_LIMIT_STRICT_MODE=false"
    )

# =============================================================================
# RATE LIMIT TIER OVERRIDES (Sprint 306 — tiered rate limiting)
# =============================================================================

# Per-tier, per-category limits.  Override any cell in the matrix via env var:
#   RATE_LIMIT_{TIER}_{CATEGORY}  (e.g. RATE_LIMIT_PROFESSIONAL_AUDIT=50/minute)
# Defaults are defined in shared/rate_limits.py _DEFAULT_POLICIES.
# No variables are loaded here — _load_optional is called lazily from
# rate_limits._load_tier_policies() to keep config.py free of 20 entries.

# Frontend URL for email verification links and CORS
FRONTEND_URL = _load_optional("FRONTEND_URL", "http://localhost:3000")

# Database URL - SQLite by default for local development
DATABASE_URL = _load_optional("DATABASE_URL", f"sqlite:///{Path(__file__).parent / 'paciolus.db'}")

# Production guardrail: SQLite is not suitable for production deployments
if ENV_MODE == "production" and DATABASE_URL.startswith("sqlite"):
    _hard_fail(
        "SQLite is not supported in production mode.\n"
        "Configure a PostgreSQL DATABASE_URL in your .env file.\n"
        "Example: DATABASE_URL=postgresql://user:password@host:5432/paciolus_db"
    )

# DB TLS enforcement: require TLS at both connection-string and session level.
# Default: true in production, false in dev/test.
_db_tls_default = "true" if ENV_MODE == "production" else "false"
DB_TLS_REQUIRED = _load_optional("DB_TLS_REQUIRED", _db_tls_default).lower() == "true"

# Break-glass exception: TICKET_ID:YYYY-MM-DD (e.g., "SEC-1234:2026-04-15").
# Allows temporary TLS bypass with documented approval and expiration.
DB_TLS_OVERRIDE = _load_optional("DB_TLS_OVERRIDE", "")

# Validate override format and expiration if provided
_db_tls_override_valid = False
_db_tls_override_ticket = ""
if DB_TLS_OVERRIDE:
    _override_parts = DB_TLS_OVERRIDE.split(":", 1)
    if len(_override_parts) != 2:
        _config_logger.warning(
            "DB_TLS_OVERRIDE malformed (expected TICKET_ID:YYYY-MM-DD): %r — override ignored",
            DB_TLS_OVERRIDE,
        )
    else:
        _db_tls_override_ticket = _override_parts[0].strip()
        _override_expiry_str = _override_parts[1].strip()
        try:
            from datetime import date as _date_cls

            _override_expiry = _date_cls.fromisoformat(_override_expiry_str)
            if _override_expiry < _date_cls.today():
                _config_logger.warning(
                    "DB_TLS_OVERRIDE expired on %s (ticket %s) — override ignored",
                    _override_expiry_str,
                    _db_tls_override_ticket,
                )
            elif not _db_tls_override_ticket:
                _config_logger.warning("DB_TLS_OVERRIDE has empty ticket ID — override ignored")
            else:
                _db_tls_override_valid = True
                _config_logger.warning(
                    "DB_TLS_OVERRIDE active: ticket=%s, expires=%s. "
                    "TLS enforcement bypassed under documented exception.",
                    _db_tls_override_ticket,
                    _override_expiry_str,
                )
        except ValueError:
            _config_logger.warning(
                "DB_TLS_OVERRIDE has invalid date (expected YYYY-MM-DD): %r — override ignored",
                _override_expiry_str,
            )

DB_TLS_OVERRIDE_VALID = _db_tls_override_valid
DB_TLS_OVERRIDE_TICKET = _db_tls_override_ticket

# Production guardrail: PostgreSQL connections must use TLS in connection string
if DB_TLS_REQUIRED and not DATABASE_URL.startswith("sqlite") and not DB_TLS_OVERRIDE_VALID:
    from urllib.parse import parse_qs as _parse_qs
    from urllib.parse import urlparse as _urlparse_db

    _db_params = _parse_qs(_urlparse_db(DATABASE_URL).query)
    _ssl_mode = (_db_params.get("sslmode") or ["disable"])[0]
    _SECURE_SSL_MODES = {"require", "verify-ca", "verify-full"}
    if _ssl_mode not in _SECURE_SSL_MODES:
        _hard_fail(
            "Insecure PostgreSQL transport — DB_TLS_REQUIRED is enabled.\n"
            "DATABASE_URL must include ?sslmode=require (or verify-ca / verify-full).\n"
            "Example: postgresql://user:password@host:5432/db?sslmode=require\n"
            f"Current sslmode: {_ssl_mode!r}\n"
            "To temporarily bypass, set DB_TLS_OVERRIDE=TICKET_ID:YYYY-MM-DD"
        )

# =============================================================================
# PostgreSQL CONNECTION POOL TUNING (Sprint 274)
# =============================================================================
# These only apply when DATABASE_URL is PostgreSQL.
# SQLite uses NullPool (single-threaded) and ignores these settings.


def _load_optional_int(var_name: str, default: int) -> int:
    """Load an optional integer config value with a default."""
    raw = _resolve_secret(var_name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw.strip())
    except ValueError:
        _config_logger.warning("%s=%r is not a valid integer, using default %d", var_name, raw, default)
        return default


DB_POOL_SIZE = _load_optional_int("DB_POOL_SIZE", 10)
DB_MAX_OVERFLOW = _load_optional_int("DB_MAX_OVERFLOW", 20)
DB_POOL_RECYCLE = _load_optional_int("DB_POOL_RECYCLE", 3600)

# =============================================================================
# SENTRY APM (Sprint 275 — optional, disabled by default)
# =============================================================================

SENTRY_DSN = _load_optional("SENTRY_DSN", "")


def _load_optional_float(var_name: str, default: float) -> float:
    """Load an optional float config value with a default."""
    raw = _resolve_secret(var_name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw.strip())
    except ValueError:
        _config_logger.warning("%s=%r is not a valid float, using default %s", var_name, raw, default)
        return default


SENTRY_TRACES_SAMPLE_RATE = _load_optional_float("SENTRY_TRACES_SAMPLE_RATE", 0.1)

# =============================================================================
# CLEANUP SCHEDULER (Sprint 307 — recurring background cleanup)
# =============================================================================

# =============================================================================
# STRIPE BILLING (Sprint 364 — optional, disabled by default)
# =============================================================================

STRIPE_SECRET_KEY = _load_optional("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = _load_optional("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_WEBHOOK_SECRET = _load_optional("STRIPE_WEBHOOK_SECRET", "")
STRIPE_ENABLED = bool(STRIPE_SECRET_KEY)

# Production guardrail: Stripe keys required in production if billing is expected
if ENV_MODE == "production" and not STRIPE_SECRET_KEY:
    _config_logger.warning("STRIPE_SECRET_KEY not set in production. Billing features disabled.")

# Stripe Coupon IDs for promotional pricing (Phase LIX Sprint C)
# Create these in Stripe Dashboard, then set the IDs here.
# MONTHLY_20: 20% off first 3 months (duration=repeating, duration_in_months=3, percent_off=20)
# ANNUAL_10: 10% off first annual invoice (duration=once, percent_off=10)
STRIPE_COUPON_MONTHLY_20 = _load_optional("STRIPE_COUPON_MONTHLY_20", "")
STRIPE_COUPON_ANNUAL_10 = _load_optional("STRIPE_COUPON_ANNUAL_10", "")

# =============================================================================
# ENTITLEMENT ENFORCEMENT (Sprint 363 — tier-based feature gating)
# =============================================================================

# "hard" = block requests exceeding tier limits (default)
# "soft" = log warnings only (useful during rollout)
ENTITLEMENT_ENFORCEMENT = _load_optional("ENTITLEMENT_ENFORCEMENT", "hard")

# Production guardrail: soft enforcement bypasses all tier restrictions
if ENV_MODE == "production" and ENTITLEMENT_ENFORCEMENT == "soft":
    _config_logger.warning(
        "ENTITLEMENT_ENFORCEMENT=soft in production. "
        "All tier restrictions are logged but NOT enforced. "
        "Set ENTITLEMENT_ENFORCEMENT=hard for production deployments."
    )

# Seat enforcement mode (Phase LIX Sprint B)
# "hard" = block requests when team exceeds seat allocation (default)
# "soft" = log seat limit violations but allow (only for rollout debugging)
SEAT_ENFORCEMENT_MODE = _load_optional("SEAT_ENFORCEMENT_MODE", "hard")

if ENV_MODE == "production" and SEAT_ENFORCEMENT_MODE == "soft":
    _config_logger.warning(
        "SEAT_ENFORCEMENT_MODE=soft in production. "
        "Seat limits are logged but NOT enforced. "
        "Set SEAT_ENFORCEMENT_MODE=hard for production deployments."
    )

# PRICING_V2_ENABLED retired (Phase LXIX) — all V2 features merged into main path.
PRICING_V2_ENABLED = True  # Always enabled; retained for backward compat during transition

# =============================================================================
# ANALYTICS (Sprint 375 — billing telemetry)
# =============================================================================

ANALYTICS_WRITE_KEY = _load_optional("ANALYTICS_WRITE_KEY", "")

# =============================================================================
# EMAIL SERVICE (Sprint 571 — production guardrail)
# =============================================================================
# SendGrid API key is loaded in email_service.py from os.getenv, not config.py.
# This guardrail validates that it is set in production so user registration
# and email verification work correctly.

_sendgrid_key = _resolve_secret("SENDGRID_API_KEY")
if ENV_MODE == "production" and (not _sendgrid_key or not _sendgrid_key.strip()):
    _hard_fail(
        "SENDGRID_API_KEY is required in production mode.\n"
        "Without it, user registration succeeds but verification emails are never sent,\n"
        "leaving users permanently unverified. Set SENDGRID_API_KEY in your environment."
    )

# =============================================================================
# PER-FORMAT FEATURE FLAGS (Sprint 436 — format rollout control)
# =============================================================================

# Set to "false" to disable a format. Restart required to apply.
FORMAT_ODS_ENABLED = _load_optional("FORMAT_ODS_ENABLED", "false").lower() == "true"
FORMAT_PDF_ENABLED = _load_optional("FORMAT_PDF_ENABLED", "true").lower() == "true"
FORMAT_IIF_ENABLED = _load_optional("FORMAT_IIF_ENABLED", "true").lower() == "true"
FORMAT_OFX_ENABLED = _load_optional("FORMAT_OFX_ENABLED", "true").lower() == "true"
FORMAT_QBO_ENABLED = _load_optional("FORMAT_QBO_ENABLED", "true").lower() == "true"
FORMAT_DOCX_ENABLED = _load_optional("FORMAT_DOCX_ENABLED", "true").lower() == "true"

CLEANUP_SCHEDULER_ENABLED = _load_optional("CLEANUP_SCHEDULER_ENABLED", "true").lower() == "true"
CLEANUP_REFRESH_TOKEN_INTERVAL_MINUTES = _load_optional_int("CLEANUP_REFRESH_TOKEN_INTERVAL_MINUTES", 60)
CLEANUP_VERIFICATION_TOKEN_INTERVAL_MINUTES = _load_optional_int("CLEANUP_VERIFICATION_TOKEN_INTERVAL_MINUTES", 60)
CLEANUP_TOOL_SESSION_INTERVAL_MINUTES = _load_optional_int("CLEANUP_TOOL_SESSION_INTERVAL_MINUTES", 30)
CLEANUP_RETENTION_INTERVAL_HOURS = _load_optional_int("CLEANUP_RETENTION_INTERVAL_HOURS", 24)

# =============================================================================
# CONFIGURATION SUMMARY (logged at startup)
# =============================================================================


def _mask_database_url(url: str) -> str:
    """Mask credentials in DATABASE_URL for safe logging.

    Replaces user:password with user:*** in PostgreSQL URLs.
    SQLite URLs have no credentials and are returned as-is.
    """
    if url.startswith("sqlite"):
        return url
    from urllib.parse import urlparse as _urlparse_mask

    try:
        parsed = _urlparse_mask(url)
        if parsed.password:
            masked = url.replace(f":{parsed.password}@", ":***@", 1)
            return masked
    except Exception:
        pass
    return url[:20] + "..."


def print_config_summary() -> None:
    """Log configuration summary for verification."""
    _config_logger.info(
        "Paciolus Configuration Loaded: env=%s, secrets=%s, host=%s:%s, "
        "cors=%s, debug=%s, jwt_algo=%s, jwt_exp=%dm, refresh_exp=%dd, "
        "csrf=%s, db=%s, db_tls=%s, redis=%s, rate_limit_strict=%s, stripe=%s, entitlement=%s",
        ENV_MODE,
        get_secrets_manager().get_provider(),
        API_HOST,
        API_PORT,
        CORS_ORIGINS,
        DEBUG,
        JWT_ALGORITHM,
        JWT_EXPIRATION_MINUTES,
        REFRESH_TOKEN_EXPIRATION_DAYS,
        "[auto-generated]" if _using_generated_csrf else "[configured]",
        _mask_database_url(DATABASE_URL),
        f"required{f' (override:{DB_TLS_OVERRIDE_TICKET})' if DB_TLS_OVERRIDE_VALID else ''}"
        if DB_TLS_REQUIRED
        else "not-required",
        REDIS_URL.split("@")[-1] if REDIS_URL else "disabled",
        RATE_LIMIT_STRICT_MODE,
        "enabled" if STRIPE_ENABLED else "disabled",
        ENTITLEMENT_ENFORCEMENT,
    )
