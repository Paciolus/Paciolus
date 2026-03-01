"""
Paciolus API — Rate Limiting Configuration

Sprint 279: Custom key_func that only trusts X-Forwarded-For from
configured proxy IPs, preventing rate-limit bypass via header spoofing.

Sprint 306: User-aware rate limiting with tiered policies.
- Authenticated users keyed by user ID (independent buckets per user)
- Anonymous requests keyed by client IP (existing behavior preserved)
- TieredLimit str subclass: backward-compatible with existing == / .split()
  comparisons while also being callable for slowapi dynamic resolution
- Tier policies: anonymous/free/solo/professional/team x 5 categories

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
"""

from contextvars import ContextVar

from slowapi import Limiter
from starlette.requests import Request

from security_middleware import is_trusted_proxy

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
    "team": {
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
    """Extract the real client IP for rate limiting.

    Trusts X-Forwarded-For ONLY when the direct peer matches TRUSTED_PROXY_IPS.
    Supports exact IPs and CIDR ranges via is_trusted_proxy().
    Falls back to the direct socket address otherwise.
    """
    from config import TRUSTED_PROXY_IPS

    peer_ip = request.client.host if request.client else "127.0.0.1"

    if is_trusted_proxy(peer_ip, TRUSTED_PROXY_IPS):
        forwarded: str | None = request.headers.get("X-Forwarded-For")
        if forwarded:
            # First entry is the original client
            return str(forwarded.split(",")[0].strip())

    return peer_ip


# ---------------------------------------------------------------------------
# Limiter instance + category constants
# ---------------------------------------------------------------------------

limiter = Limiter(
    key_func=_get_rate_limit_key,
    default_limits=["60/minute"],
    # Note: headers_enabled=True requires every rate-limited endpoint to
    # accept a Response parameter. Enabling it would require updating all
    # ~100 endpoint signatures. Left as False for now.
)

RATE_LIMIT_AUDIT = TieredLimit("audit", "10/minute")
RATE_LIMIT_AUTH = TieredLimit("auth", "5/minute")
RATE_LIMIT_EXPORT = TieredLimit("export", "20/minute")
RATE_LIMIT_WRITE = TieredLimit("write", "30/minute")
RATE_LIMIT_DEFAULT = TieredLimit("default", "60/minute")
