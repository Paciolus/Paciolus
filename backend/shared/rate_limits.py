"""
Paciolus API — Rate Limiting Configuration

Sprint 279: Custom key_func that only trusts X-Forwarded-For from
configured proxy IPs, preventing rate-limit bypass via header spoofing.

Sprint 306: User-aware rate limiting with tiered policies.
- Authenticated users keyed by user ID (independent buckets per user)
- Anonymous requests keyed by client IP (existing behavior preserved)
- TieredLimit str subclass: backward-compatible with existing == / .split()
  comparisons while also being callable for slowapi dynamic resolution
- Tier policies: anonymous/free/solo/professional/team/organization x 5 categories

Maintenance Status (Sprint 444):
    slowapi (0.1.9) is unmaintained — last release Oct 2022. However, it is a
    thin wrapper around the `limits` library which IS actively maintained
    (https://github.com/alisaifee/limits). The actual rate-limiting logic
    (token bucket, sliding window, storage backends) lives in `limits`, not
    slowapi. We pin `limits>=3.0.0` explicitly and run canary tests
    (test_rate_limit_slowapi_health.py) in CI.

    Decision: Keep slowapi pinned at 0.1.9. A full migration to a custom
    Starlette middleware wrapping `limits` directly is documented in
    docs/runbooks/rate-limiter-modernization.md but deferred until slowapi
    becomes incompatible with a future Starlette version.

Storage Backend:
    When REDIS_URL is configured, rate-limit counters are persisted in Redis
    and shared across all Gunicorn workers and server instances. This prevents
    counter reset on worker restart and ensures consistent enforcement under
    horizontal scaling.  When REDIS_URL is empty (default), in-memory counters
    are used — suitable for single-instance development.

Storage Outage Behavior (Sprint 774):
    A Redis outage must never take the API down.  The limiter is built with
    ``in_memory_fallback_enabled=True``, so a storage failure degrades to
    in-process counters (same limit values) and self-heals when Redis
    returns.  Before Sprint 774 a storage error propagated out of the limit
    check as HTTP 500 on every rate-limited route — i.e. the entire API,
    health probes included — and strict mode additionally refused to boot,
    leaving no recovery path without operator action.  That combination took
    production down for ~5.5 months in 2026.

    ``RATE_LIMIT_STORAGE_FAILURE_POLICY`` (config.py) selects the boot
    posture: ``degrade`` (default) or ``fail_closed`` (old behavior).
    Live state is reported by get_storage_health() and surfaced on
    /health/ready.
"""

import logging
from contextvars import ContextVar

from slowapi import Limiter
from starlette.requests import Request

from security_middleware import get_client_ip as _canonical_get_client_ip

_logger = logging.getLogger(__name__)

# ContextVar set by RateLimitIdentityMiddleware before slowapi runs
_current_tier: ContextVar[str] = ContextVar("rate_limit_tier", default="anonymous")

# ---------------------------------------------------------------------------
# Tier policy matrix
# ---------------------------------------------------------------------------
# Pattern: RATE_LIMIT_{TIER}_{CATEGORY} env vars override these defaults.
# All values are slowapi rate-limit strings (e.g. "10/minute").

_DEFAULT_POLICIES: dict[str, dict[str, str]] = {
    "anonymous": {
        "auth": "5/minute",
        "audit": "10/minute",
        "export": "20/minute",
        "write": "30/minute",
        "default": "60/minute",
    },
    "free": {
        "auth": "5/minute",
        "audit": "15/minute",
        "export": "30/minute",
        "write": "45/minute",
        "default": "90/minute",
    },
    "solo": {
        "auth": "8/minute",
        "audit": "20/minute",
        "export": "45/minute",
        "write": "60/minute",
        "default": "120/minute",
    },
    # Backward-compat alias: existing JWTs may carry "starter" during the
    # 30-min access token window after migration.
    "starter": {
        "auth": "8/minute",
        "audit": "20/minute",
        "export": "45/minute",
        "write": "60/minute",
        "default": "120/minute",
    },
    "professional": {
        "auth": "10/minute",
        "audit": "30/minute",
        "export": "60/minute",
        "write": "90/minute",
        "default": "180/minute",
    },
    "enterprise": {
        "auth": "20/minute",
        "audit": "60/minute",
        "export": "120/minute",
        "write": "180/minute",
        "default": "300/minute",
    },
    # LEGACY ALIAS: "team" maps to Professional tier. Requires DB migration before rename.
    # Tracked in COHESION_REMEDIATION.md — do not rename without migration.
    "team": {
        "auth": "20/minute",
        "audit": "60/minute",
        "export": "120/minute",
        "write": "180/minute",
        "default": "300/minute",
    },
    # LEGACY ALIAS: "organization" maps to Enterprise tier. Requires DB migration before rename.
    # Tracked in COHESION_REMEDIATION.md — do not rename without migration.
    "organization": {
        "auth": "20/minute",
        "audit": "60/minute",
        "export": "120/minute",
        "write": "180/minute",
        "default": "300/minute",
    },
}


def _load_tier_policies() -> dict[str, dict[str, str]]:
    """Build tier policies, merging env var overrides on top of defaults."""
    from config import _load_optional

    policies: dict[str, dict[str, str]] = {}
    for tier, categories in _DEFAULT_POLICIES.items():
        policies[tier] = {}
        for category, default_val in categories.items():
            env_key = f"RATE_LIMIT_{tier.upper()}_{category.upper()}"
            policies[tier][category] = _load_optional(env_key, default_val)
    return policies


# Lazy-loaded on first access to avoid circular import at module level
_tier_policies: dict[str, dict[str, str]] | None = None


def get_tier_policies() -> dict[str, dict[str, str]]:
    """Return the resolved tier policies (lazy-loaded, cached)."""
    global _tier_policies
    if _tier_policies is None:
        _tier_policies = _load_tier_policies()
    return _tier_policies


# ---------------------------------------------------------------------------
# TieredLimit — str subclass that doubles as a callable for slowapi
# ---------------------------------------------------------------------------


class TieredLimit(str):
    """A rate-limit string that resolves dynamically based on user tier.

    Inherits from str so existing code that does ``==``, ``.split()``,
    ``str()`` comparisons against the anonymous-tier default value keeps
    working unchanged.

    Also implements ``__call__`` so slowapi treats it as a dynamic limit
    (resolved per-request via the _current_tier ContextVar).
    """

    _category: str

    def __new__(cls, category: str, default: str) -> "TieredLimit":
        # The str value is the anonymous-tier default (backward compat)
        instance = super().__new__(cls, default)
        instance._category = category
        return instance

    def __call__(self) -> str:
        """Called by slowapi's LimitGroup.__iter__ to resolve the limit."""
        tier = _current_tier.get()
        policies = get_tier_policies()
        tier_limits = policies.get(tier, policies["anonymous"])
        return tier_limits.get(self._category, str(self))


# ---------------------------------------------------------------------------
# Key function — user-aware
# ---------------------------------------------------------------------------


def _get_rate_limit_key(request: Request) -> str:
    """Extract the rate-limit key: 'user:{id}' for authenticated, IP for anonymous.

    The RateLimitIdentityMiddleware sets request.state.rate_limit_user_id
    when a valid JWT is present. This gives each authenticated user their
    own rate-limit bucket, solving shared-IP / corporate-NAT collisions.
    """
    user_id = getattr(request.state, "rate_limit_user_id", None)
    if user_id is not None:
        return f"user:{user_id}"

    # Fall back to client IP (proxy-aware)
    return _get_client_ip(request)


def _get_client_ip(request: Request) -> str:
    """Delegate to canonical get_client_ip() in security_middleware."""
    return _canonical_get_client_ip(request)


# ---------------------------------------------------------------------------
# Storage backend resolution
# ---------------------------------------------------------------------------


# Records whether the configured backend answered at boot.  Informational
# only — live degradation is read off the limiter itself (see
# get_storage_health), because slowapi recovers without a restart.
_storage_reachable_at_boot: bool = True


def _resolve_storage_uri() -> str:
    """Return the storage URI for the rate limiter.

    When REDIS_URL is configured, returns a ``redis://`` URI so that
    counters are shared across all workers and survive restarts.

    Two failure classes are handled differently, because only one of them
    can ever self-heal:

    - **Unreachable backend** (DNS failure, refused connection, timeout):
      the URI is kept.  slowapi is configured with
      ``in_memory_fallback_enabled=True``, so the first failed request flips
      it to in-process counters and its periodic re-probe restores shared
      Redis counters automatically — no redeploy needed.  Returning
      ``memory://`` here instead would strand the process on per-process
      counters until an operator intervened.
    - **Unusable URI** (malformed, unsupported scheme): slowapi would raise
      the same error while constructing its own storage, crashing the
      process at import.  Degrade to ``memory://`` so the app still serves;
      a bad URI cannot recover on its own anyway.

    Under ``RATE_LIMIT_STORAGE_FAILURE_POLICY=fail_closed`` an unreachable
    backend raises RuntimeError instead (pre-Sprint-774 behavior).
    """
    global _storage_reachable_at_boot

    from config import RATE_LIMIT_STORAGE_FAILURE_POLICY, RATE_LIMIT_STRICT_MODE, REDIS_URL

    if not REDIS_URL:
        # config.py already hard-fails if strict + no URL, so this is dev/test only
        return "memory://"

    from limits.storage import RedisStorage

    # Construct first.  Only a successfully-constructed storage proves that
    # slowapi can build its own from the same URI without crashing.
    try:
        storage = RedisStorage(REDIS_URL)
    except Exception as exc:  # noqa: BLE001
        _storage_reachable_at_boot = False
        if RATE_LIMIT_STORAGE_FAILURE_POLICY == "fail_closed":
            _logger.critical(
                "FAIL-CLOSED: rate-limit storage could not be constructed (%s). "
                "Refusing to start — RATE_LIMIT_STORAGE_FAILURE_POLICY=fail_closed.",
                exc,
            )
            raise RuntimeError(f"Rate-limit storage backend unavailable (fail_closed): {exc}") from exc
        _logger.critical(
            "Rate-limit storage URI could not be used (%s) — falling back to "
            "in-memory counters for this process. This will NOT self-heal; "
            "fix REDIS_URL. strict_mode=%s",
            exc,
            RATE_LIMIT_STRICT_MODE,
        )
        return "memory://"

    # Probe reachability so a dead backend is visible at startup rather than
    # on the first user request.
    #
    # IMPORTANT: limits' Storage.check() signals failure by RETURNING False,
    # not by raising — its body is `try: return ping() except: return False`.
    # Code that only catches exceptions therefore treats a dead backend as
    # healthy. The pre-Sprint-774 implementation made exactly that mistake,
    # so its "fail-closed" guarantee never actually fired: the app booted
    # against a dead Redis and then raised on the first incr(), surfacing as
    # HTTP 500 on every rate-limited route. The old tests passed only because
    # they mocked check() to raise, which real RedisStorage never does.
    try:
        reachable = bool(storage.check())
        probe_error: str = "" if reachable else "storage.check() returned False (ping failed)"
    except Exception as exc:  # noqa: BLE001 — defensive: check() is not supposed to raise
        reachable = False
        probe_error = str(exc)

    if not reachable:
        _storage_reachable_at_boot = False
        if RATE_LIMIT_STORAGE_FAILURE_POLICY == "fail_closed":
            _logger.critical(
                "FAIL-CLOSED: Redis configured but unreachable (%s). "
                "Refusing to start — RATE_LIMIT_STORAGE_FAILURE_POLICY=fail_closed. "
                "Rate limits would not be shared across workers.",
                probe_error,
            )
            raise RuntimeError(f"Rate-limit storage backend unavailable (fail_closed): {probe_error}")
        _logger.critical(
            "DEGRADED: Redis configured but unreachable at boot (%s). Serving with "
            "in-process rate-limit counters; limit VALUES are unchanged but are no "
            "longer shared across workers. slowapi will restore shared counters "
            "automatically once Redis answers. Watch /health/ready "
            "rate_limit_storage. strict_mode=%s",
            probe_error,
            RATE_LIMIT_STRICT_MODE,
        )
        return REDIS_URL

    _logger.info("Rate-limit storage: Redis (%s)", REDIS_URL.split("@")[-1])
    return REDIS_URL


_storage_uri = _resolve_storage_uri()


def _emit_slowapi_unmaintained_warning() -> None:
    """Emit an explicit startup banner about slowapi's unmaintained status.

    Surfaced at module import so the risk is visible in operator logs even
    when no canary test fails. Severity differs by environment:
    - Production: WARNING (operational visibility — investigate during planned
      maintenance, not an incident).
    - Non-production: INFO (developer awareness).

    Migration plan: docs/runbooks/rate-limiter-modernization.md.
    """
    try:
        from config import ENV_MODE as _env_mode
    except Exception:  # noqa: BLE001 — config import must never break startup
        _env_mode = "development"

    message = (
        "rate-limiter dependency notice: slowapi is unmaintained "
        "(last release Oct 2022); the underlying `limits` library is actively "
        "maintained and pinned at >=3.0.0. Migration plan: "
        "docs/runbooks/rate-limiter-modernization.md."
    )
    if _env_mode == "production":
        _logger.warning("PRODUCTION %s", message)
    else:
        _logger.info(message)


_emit_slowapi_unmaintained_warning()

# ---------------------------------------------------------------------------
# Limiter instance + category constants
# ---------------------------------------------------------------------------

limiter = Limiter(
    key_func=_get_rate_limit_key,
    default_limits=["60/minute"],
    storage_uri=_storage_uri,
    # Note: headers_enabled=True requires every rate-limited endpoint to
    # accept a Response parameter. Enabling it would require updating all
    # ~100 endpoint signatures. Left as False for now.
    #
    # Sprint 774: without this, ANY storage-layer error propagates out of the
    # limit check and surfaces as HTTP 500 — on every rate-limited route,
    # which is effectively the whole API including the health probes. With it
    # enabled, slowapi flips to an in-process MemoryStorage on the first
    # failure (same limit values), then re-probes the primary and restores
    # shared counters on its own. Note this is NOT swallow_errors: limits are
    # still enforced while degraded, just not shared across workers.
    in_memory_fallback_enabled=True,
)


def get_storage_backend() -> str:
    """Return the *configured* storage backend identifier ('redis' or 'memory').

    Reflects configuration, not live health — see get_storage_health() for
    whether the limiter is currently running on its fallback.
    """
    if _storage_uri.startswith("redis"):
        return "redis"
    return "memory"


def get_storage_health() -> dict[str, object]:
    """Report configured vs. live rate-limit storage state.

    ``degraded`` is true only when Redis is the configured backend and the
    limiter has flipped to its in-memory fallback.  It is read live off
    slowapi's ``_storage_dead`` flag so it clears by itself once slowapi's
    re-probe succeeds, rather than staying stuck on a boot-time observation.
    """
    configured = get_storage_backend()
    # Private attribute by necessity: slowapi exposes no public accessor for
    # fallback state. Guarded with getattr so a slowapi upgrade that renames
    # it degrades to "not degraded" rather than breaking the health probe.
    storage_dead = bool(getattr(limiter, "_storage_dead", False))
    degraded = configured == "redis" and storage_dead
    return {
        "configured_backend": configured,
        "active_backend": "memory" if (configured == "memory" or storage_dead) else "redis",
        "degraded": degraded,
        "reachable_at_boot": _storage_reachable_at_boot,
    }


RATE_LIMIT_AUDIT = TieredLimit("audit", "10/minute")
RATE_LIMIT_AUTH = TieredLimit("auth", "5/minute")
RATE_LIMIT_EXPORT = TieredLimit("export", "20/minute")
RATE_LIMIT_WRITE = TieredLimit("write", "30/minute")
RATE_LIMIT_DEFAULT = TieredLimit("default", "60/minute")

# Fixed-rate limits for infrastructure endpoints (no tiered escalation)
RATE_LIMIT_WEBHOOK = "10/minute"  # AUDIT-07: unauthenticated, signature-verified
RATE_LIMIT_HEALTH = "60/minute"  # AUDIT-07: health probes
RATE_LIMIT_METRICS = "30/minute"  # AUDIT-07: Prometheus scrape endpoint
