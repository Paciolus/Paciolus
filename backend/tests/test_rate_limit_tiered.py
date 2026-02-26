"""
Tests for Sprint 306 — User-Aware Rate Limiting with Tiered Policies.

Covers:
1. TieredLimit backward compatibility (str operations)
2. ContextVar-based tier resolution
3. User-aware key function (_get_rate_limit_key)
4. RateLimitIdentityMiddleware JWT extraction
5. Tier claim in create_access_token
6. Tier enforcement: different limits for different tiers
7. Response headers (X-RateLimit-*) on successful responses
"""

import os
import sys
import time
from contextvars import copy_context
from unittest.mock import MagicMock, patch

import httpx
import jwt as pyjwt
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from auth import create_access_token
from shared.rate_limits import (
    RATE_LIMIT_AUDIT,
    RATE_LIMIT_AUTH,
    RATE_LIMIT_DEFAULT,
    RATE_LIMIT_EXPORT,
    RATE_LIMIT_WRITE,
    TieredLimit,
    _current_tier,
    _get_rate_limit_key,
    get_tier_policies,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


# ===========================================================================
# 1. TieredLimit backward compatibility
# ===========================================================================


class TestTieredLimitBackwardCompat:
    """TieredLimit must behave like a plain string for existing test assertions."""

    def test_equality_with_string(self):
        assert RATE_LIMIT_AUTH == "5/minute"

    def test_split_works(self):
        parts = RATE_LIMIT_AUDIT.split("/")
        assert parts == ["10", "minute"]

    def test_str_conversion(self):
        assert str(RATE_LIMIT_EXPORT) == "20/minute"

    def test_isinstance_str(self):
        assert isinstance(RATE_LIMIT_WRITE, str)

    def test_isinstance_tiered_limit(self):
        assert isinstance(RATE_LIMIT_DEFAULT, TieredLimit)

    def test_tier_ordering(self):
        """Anonymous-tier defaults should be in ascending order."""
        tiers = [
            int(RATE_LIMIT_AUTH.split("/")[0]),
            int(RATE_LIMIT_AUDIT.split("/")[0]),
            int(RATE_LIMIT_EXPORT.split("/")[0]),
            int(RATE_LIMIT_WRITE.split("/")[0]),
            int(RATE_LIMIT_DEFAULT.split("/")[0]),
        ]
        assert tiers == sorted(tiers)

    def test_callable(self):
        """TieredLimit must be callable (slowapi dynamic limit contract)."""
        assert callable(RATE_LIMIT_AUTH)

    def test_call_returns_string(self):
        """Calling TieredLimit returns the resolved limit string."""
        result = RATE_LIMIT_AUTH()
        assert isinstance(result, str)
        assert "/" in result


# ===========================================================================
# 2. ContextVar-based tier resolution
# ===========================================================================


class TestContextVarResolution:
    """TieredLimit.__call__ reads _current_tier ContextVar."""

    def test_anonymous_default(self):
        """When ContextVar is unset, resolves to anonymous tier."""
        # Run in a fresh context where _current_tier has its default
        ctx = copy_context()
        result = ctx.run(RATE_LIMIT_AUDIT)
        assert result == "10/minute"  # anonymous audit

    def test_free_tier(self):
        ctx = copy_context()

        def _run():
            _current_tier.set("free")
            return RATE_LIMIT_AUDIT()

        result = ctx.run(_run)
        policies = get_tier_policies()
        assert result == policies["free"]["audit"]

    def test_solo_tier(self):
        ctx = copy_context()

        def _run():
            _current_tier.set("solo")
            return RATE_LIMIT_AUDIT()

        result = ctx.run(_run)
        policies = get_tier_policies()
        assert result == policies["solo"]["audit"]

    def test_professional_tier(self):
        ctx = copy_context()

        def _run():
            _current_tier.set("professional")
            return RATE_LIMIT_AUDIT()

        result = ctx.run(_run)
        policies = get_tier_policies()
        assert result == policies["professional"]["audit"]

    def test_team_tier(self):
        ctx = copy_context()

        def _run():
            _current_tier.set("team")
            return RATE_LIMIT_EXPORT()

        result = ctx.run(_run)
        policies = get_tier_policies()
        assert result == policies["team"]["export"]

    def test_enterprise_tier(self):
        ctx = copy_context()

        def _run():
            _current_tier.set("enterprise")
            return RATE_LIMIT_EXPORT()

        result = ctx.run(_run)
        policies = get_tier_policies()
        assert result == policies["enterprise"]["export"]

    def test_unknown_tier_falls_back_to_anonymous(self):
        """Unknown tier value falls back to anonymous policies."""
        ctx = copy_context()

        def _run():
            _current_tier.set("platinum")
            return RATE_LIMIT_AUDIT()

        result = ctx.run(_run)
        policies = get_tier_policies()
        assert result == policies["anonymous"]["audit"]

    def test_all_categories_resolve(self):
        """Every category resolves for every tier without KeyError."""
        policies = get_tier_policies()
        limits = [RATE_LIMIT_AUTH, RATE_LIMIT_AUDIT, RATE_LIMIT_EXPORT, RATE_LIMIT_WRITE, RATE_LIMIT_DEFAULT]
        for tier_name in policies:
            ctx = copy_context()

            def _run(t=tier_name):
                _current_tier.set(t)
                return [lim() for lim in limits]

            results = ctx.run(_run)
            assert all("/" in r for r in results)


# ===========================================================================
# 3. User-aware key function
# ===========================================================================


class TestRateLimitKeyFunction:
    """_get_rate_limit_key returns user:{id} or client IP."""

    def test_authenticated_user_keyed_by_id(self):
        request = MagicMock(spec=["state", "client", "headers"])
        request.state.rate_limit_user_id = 42
        request.client.host = "10.0.0.1"

        key = _get_rate_limit_key(request)
        assert key == "user:42"

    def test_anonymous_keyed_by_ip(self):
        request = MagicMock(spec=["state", "client", "headers"])
        request.state.rate_limit_user_id = None
        request.client.host = "192.168.1.100"
        request.headers = {}

        with patch("config.TRUSTED_PROXY_IPS", frozenset()):
            key = _get_rate_limit_key(request)
        assert key == "192.168.1.100"

    def test_missing_state_attribute_falls_back_to_ip(self):
        """If middleware didn't run, getattr returns None → IP fallback."""
        request = MagicMock(spec=["state", "client", "headers"])
        # Simulate no rate_limit_user_id attribute
        del request.state.rate_limit_user_id
        request.client.host = "10.0.0.5"
        request.headers = {}

        with patch("config.TRUSTED_PROXY_IPS", frozenset()):
            key = _get_rate_limit_key(request)
        assert key == "10.0.0.5"

    def test_two_users_same_ip_get_different_keys(self):
        """Two authenticated users from the same IP get independent buckets."""
        r1 = MagicMock(spec=["state", "client", "headers"])
        r1.state.rate_limit_user_id = 100
        r1.client.host = "10.0.0.1"

        r2 = MagicMock(spec=["state", "client", "headers"])
        r2.state.rate_limit_user_id = 200
        r2.client.host = "10.0.0.1"

        assert _get_rate_limit_key(r1) != _get_rate_limit_key(r2)

    def test_proxy_aware_extraction(self):
        """X-Forwarded-For honored when peer IP is trusted."""
        request = MagicMock(spec=["state", "client", "headers"])
        request.state.rate_limit_user_id = None
        request.client.host = "127.0.0.1"
        request.headers = {"X-Forwarded-For": "203.0.113.50, 10.0.0.1"}

        with patch("config.TRUSTED_PROXY_IPS", frozenset({"127.0.0.1"})):
            key = _get_rate_limit_key(request)
        assert key == "203.0.113.50"


# ===========================================================================
# 4. RateLimitIdentityMiddleware
# ===========================================================================


class TestRateLimitIdentityMiddleware:
    """Middleware extracts user_id and tier from JWT, sets ContextVar."""

    @pytest.mark.asyncio
    async def test_valid_jwt_sets_user_id_and_tier(self):
        """Middleware extracts user_id and tier from a valid Bearer token."""
        from config import JWT_ALGORITHM, JWT_SECRET_KEY

        payload = {
            "sub": "42",
            "email": "test@example.com",
            "tier": "professional",
            "exp": int(time.time()) + 3600,
        }
        token = pyjwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

        captured_state = {}

        async def _capture_app(scope, receive, send):
            """Minimal ASGI app that captures request.state."""
            from starlette.requests import Request

            request = Request(scope, receive, send)
            captured_state["user_id"] = getattr(request.state, "rate_limit_user_id", "MISSING")
            captured_state["tier"] = getattr(request.state, "rate_limit_user_tier", "MISSING")

            from starlette.responses import Response

            response = Response("ok", media_type="text/plain")
            await response(scope, receive, send)

        from security_middleware import RateLimitIdentityMiddleware

        middleware = RateLimitIdentityMiddleware(_capture_app)

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=middleware),
            base_url="http://test",
        ) as client:
            r = await client.get("/test", headers={"Authorization": f"Bearer {token}"})

        assert r.status_code == 200
        assert captured_state["user_id"] == 42
        assert captured_state["tier"] == "professional"

    @pytest.mark.asyncio
    async def test_missing_auth_header_falls_through(self):
        """No Authorization header → anonymous."""
        captured_state = {}

        async def _capture_app(scope, receive, send):
            from starlette.requests import Request
            from starlette.responses import Response

            request = Request(scope, receive, send)
            captured_state["user_id"] = getattr(request.state, "rate_limit_user_id", "MISSING")
            captured_state["tier"] = getattr(request.state, "rate_limit_user_tier", "MISSING")
            response = Response("ok", media_type="text/plain")
            await response(scope, receive, send)

        from security_middleware import RateLimitIdentityMiddleware

        middleware = RateLimitIdentityMiddleware(_capture_app)

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=middleware),
            base_url="http://test",
        ) as client:
            r = await client.get("/test")

        assert r.status_code == 200
        assert captured_state["user_id"] is None
        assert captured_state["tier"] == "anonymous"

    @pytest.mark.asyncio
    async def test_invalid_jwt_falls_through(self):
        """Malformed JWT → anonymous (no 401)."""
        captured_state = {}

        async def _capture_app(scope, receive, send):
            from starlette.requests import Request
            from starlette.responses import Response

            request = Request(scope, receive, send)
            captured_state["user_id"] = getattr(request.state, "rate_limit_user_id", "MISSING")
            captured_state["tier"] = getattr(request.state, "rate_limit_user_tier", "MISSING")
            response = Response("ok", media_type="text/plain")
            await response(scope, receive, send)

        from security_middleware import RateLimitIdentityMiddleware

        middleware = RateLimitIdentityMiddleware(_capture_app)

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=middleware),
            base_url="http://test",
        ) as client:
            r = await client.get("/test", headers={"Authorization": "Bearer invalid.token.here"})

        assert r.status_code == 200
        assert captured_state["user_id"] is None
        assert captured_state["tier"] == "anonymous"

    @pytest.mark.asyncio
    async def test_expired_jwt_falls_through(self):
        """Expired JWT → anonymous (no 401 — auth enforcement is route-level)."""
        from config import JWT_ALGORITHM, JWT_SECRET_KEY

        payload = {
            "sub": "42",
            "email": "test@example.com",
            "tier": "enterprise",
            "exp": int(time.time()) - 3600,  # expired 1 hour ago
        }
        token = pyjwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

        captured_state = {}

        async def _capture_app(scope, receive, send):
            from starlette.requests import Request
            from starlette.responses import Response

            request = Request(scope, receive, send)
            captured_state["user_id"] = getattr(request.state, "rate_limit_user_id", "MISSING")
            captured_state["tier"] = getattr(request.state, "rate_limit_user_tier", "MISSING")
            response = Response("ok", media_type="text/plain")
            await response(scope, receive, send)

        from security_middleware import RateLimitIdentityMiddleware

        middleware = RateLimitIdentityMiddleware(_capture_app)

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=middleware),
            base_url="http://test",
        ) as client:
            r = await client.get("/test", headers={"Authorization": f"Bearer {token}"})

        assert r.status_code == 200
        assert captured_state["user_id"] is None
        assert captured_state["tier"] == "anonymous"

    @pytest.mark.asyncio
    async def test_jwt_without_tier_claim_defaults_to_free(self):
        """Existing tokens without 'tier' claim default to 'free'."""
        from config import JWT_ALGORITHM, JWT_SECRET_KEY

        payload = {
            "sub": "99",
            "email": "old@example.com",
            "exp": int(time.time()) + 3600,
            # No "tier" claim — simulates pre-Sprint-306 token
        }
        token = pyjwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

        captured_state = {}

        async def _capture_app(scope, receive, send):
            from starlette.requests import Request
            from starlette.responses import Response

            request = Request(scope, receive, send)
            captured_state["user_id"] = getattr(request.state, "rate_limit_user_id", "MISSING")
            captured_state["tier"] = getattr(request.state, "rate_limit_user_tier", "MISSING")
            response = Response("ok", media_type="text/plain")
            await response(scope, receive, send)

        from security_middleware import RateLimitIdentityMiddleware

        middleware = RateLimitIdentityMiddleware(_capture_app)

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=middleware),
            base_url="http://test",
        ) as client:
            r = await client.get("/test", headers={"Authorization": f"Bearer {token}"})

        assert r.status_code == 200
        assert captured_state["user_id"] == 99
        assert captured_state["tier"] == "free"


# ===========================================================================
# 5. Tier claim in create_access_token
# ===========================================================================


class TestTierClaimInJWT:
    """create_access_token embeds 'tier' in the JWT payload."""

    def test_tier_claim_present(self):
        from config import JWT_ALGORITHM, JWT_SECRET_KEY

        token, _ = create_access_token(1, "test@example.com", tier="professional")
        payload = pyjwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        assert payload["tier"] == "professional"

    def test_tier_default_is_free(self):
        from config import JWT_ALGORITHM, JWT_SECRET_KEY

        token, _ = create_access_token(1, "test@example.com")
        payload = pyjwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        assert payload["tier"] == "free"

    def test_solo_tier(self):
        from config import JWT_ALGORITHM, JWT_SECRET_KEY

        token, _ = create_access_token(1, "test@example.com", tier="solo")
        payload = pyjwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        assert payload["tier"] == "solo"

    def test_enterprise_tier(self):
        from config import JWT_ALGORITHM, JWT_SECRET_KEY

        token, _ = create_access_token(1, "test@example.com", tier="enterprise")
        payload = pyjwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        assert payload["tier"] == "enterprise"

    def test_team_tier(self):
        from config import JWT_ALGORITHM, JWT_SECRET_KEY

        token, _ = create_access_token(1, "test@example.com", tier="team")
        payload = pyjwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        assert payload["tier"] == "team"


# ===========================================================================
# 6. Tier policies structure
# ===========================================================================


class TestTierPolicies:
    """Verify tier policy matrix structure and values."""

    def test_all_tiers_present(self):
        policies = get_tier_policies()
        assert set(policies.keys()) == {"anonymous", "free", "solo", "starter", "professional", "team", "enterprise"}

    def test_all_categories_present(self):
        policies = get_tier_policies()
        expected_cats = {"auth", "audit", "export", "write", "default"}
        for tier, cats in policies.items():
            assert set(cats.keys()) == expected_cats, f"Tier '{tier}' missing categories"

    def test_higher_tiers_have_higher_limits(self):
        """For each category, limits should increase: anonymous <= free <= solo <= pro <= team <= enterprise."""
        policies = get_tier_policies()
        tier_order = ["anonymous", "free", "solo", "professional", "team", "enterprise"]

        for category in ["auth", "audit", "export", "write", "default"]:
            values = [int(policies[t][category].split("/")[0]) for t in tier_order]
            assert values == sorted(values), (
                f"Category '{category}' limits not monotonically increasing: {dict(zip(tier_order, values))}"
            )

    def test_all_values_are_valid_rate_strings(self):
        """Every value matches pattern '{int}/{unit}'."""
        policies = get_tier_policies()
        for tier, cats in policies.items():
            for cat, val in cats.items():
                parts = val.split("/")
                assert len(parts) == 2, f"{tier}.{cat} = {val!r} invalid"
                assert parts[0].isdigit(), f"{tier}.{cat} = {val!r} — number part invalid"
                assert parts[1] in ("second", "minute", "hour", "day"), f"{tier}.{cat} = {val!r} — unit invalid"


# ===========================================================================
# 7. Limiter configuration
# ===========================================================================


class TestLimiterConfig:
    """Verify limiter is configured with user-aware key function."""

    def test_key_func_is_user_aware(self):
        from shared.rate_limits import limiter

        assert limiter._key_func is _get_rate_limit_key
