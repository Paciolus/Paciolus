"""
Sprint 774: a rate-limit storage outage must not take the API down.

Production incident this guards against (2026-05 → 2026-10): the configured
Upstash Redis host stopped resolving. Every rate-limited route — i.e. the
whole API, health probes included — returned HTTP 500 for ~5.5 months,
because a storage error propagated straight out of slowapi's limit check.

Covers:
1.  End-to-end: a rate-limited route served through a DEAD Redis returns 200
    when ``in_memory_fallback_enabled=True`` ...
2.  ... and fails hard without it (control — proves the test exercises the
    real failure path, and that the flag is what prevents the outage).
3.  Limits are still ENFORCED while degraded (fallback != no rate limiting).
4.  _resolve_storage_uri keeps the Redis URI on an unreachable backend so
    slowapi's re-probe can self-heal, rather than stranding on memory://.
5.  A falsy check() (the real limits contract) is treated as unreachable.
6.  fail_closed policy still refuses to start.
7.  get_storage_health reports configured vs. live backend.
"""

import os
import sys

import httpx
import pytest
from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Port 1 on loopback: connection refused immediately, no DNS wait. Using an
# unresolvable hostname instead would make these tests pay a DNS timeout.
DEAD_REDIS = "redis://127.0.0.1:1/0"


def _build_app(*, fallback: bool, limit: str = "100/minute") -> FastAPI:
    """Minimal app with one rate-limited route backed by a dead Redis."""
    limiter = Limiter(
        key_func=lambda request: "fixed-test-key",
        storage_uri=DEAD_REDIS,
        in_memory_fallback_enabled=fallback,
    )
    app = FastAPI()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    @app.get("/probe")
    @limiter.limit(limit)
    async def probe(request: Request) -> dict:  # noqa: ARG001
        return {"ok": True}

    return app


async def _get(app: FastAPI, path: str = "/probe") -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get(path)


class TestStorageOutageDoesNotBreakRequests:
    """The regression that matters: dead cache must not mean dead API."""

    @pytest.mark.asyncio
    async def test_dead_redis_with_fallback_returns_200(self):
        """Dead Redis + in-memory fallback → request succeeds."""
        response = await _get(_build_app(fallback=True))
        assert response.status_code == 200, response.text
        assert response.json() == {"ok": True}

    @pytest.mark.asyncio
    async def test_dead_redis_without_fallback_fails_hard(self):
        """Control: without the fallback, the storage error escapes the app.

        This is the pre-Sprint-774 production behavior. Under uvicorn the
        unhandled ConnectionError is rendered as HTTP 500 by the server's
        error middleware (what users actually saw); under ASGITransport
        there is no such middleware, so it propagates to the caller. Either
        way the request fails.

        If this test ever stops raising, the dead-Redis simulation has
        stopped working and test_dead_redis_with_fallback_returns_200 would
        be proving nothing.
        """
        import redis.exceptions

        with pytest.raises(redis.exceptions.ConnectionError):
            await _get(_build_app(fallback=False))

    @pytest.mark.asyncio
    async def test_limits_still_enforced_while_degraded(self):
        """Degrading to in-memory must not mean limits stop applying.

        Distinguishes the fallback from slowapi's swallow_errors, which would
        let unlimited traffic through during an outage.
        """
        app = _build_app(fallback=True, limit="3/minute")
        statuses = [(await _get(app)).status_code for _ in range(5)]
        assert statuses[:3] == [200, 200, 200], statuses
        assert 429 in statuses[3:], f"expected a 429 after the limit, got {statuses}"


class TestResolveStorageUriOutagePosture:
    """_resolve_storage_uri must keep a recoverable URI and detect falsy check()."""

    def test_unreachable_redis_keeps_uri_for_self_heal(self):
        """Degrade policy returns the Redis URI, not memory://.

        Returning memory:// would strand the process on per-process counters
        until someone redeployed; keeping the URI lets slowapi's periodic
        re-probe restore shared counters on its own.
        """
        from shared import rate_limits

        with _patched(
            REDIS_URL=DEAD_REDIS,
            RATE_LIMIT_STORAGE_FAILURE_POLICY="degrade",
            RATE_LIMIT_STRICT_MODE=True,
        ):
            assert rate_limits._resolve_storage_uri() == DEAD_REDIS

    def test_falsy_check_treated_as_unreachable(self):
        """check() returning False (the real limits contract) must degrade.

        limits' Storage.check() is `try: return ping() except: return False`,
        so it never raises. Catching exceptions alone silently treats a dead
        backend as healthy — the original bug.
        """
        from shared import rate_limits

        class _FalsyCheckStorage:
            def __init__(self, *_a, **_kw):
                pass

            def check(self) -> bool:
                return False

        with (
            _patched(
                REDIS_URL="redis://pretend:6379/0",
                RATE_LIMIT_STORAGE_FAILURE_POLICY="fail_closed",
                RATE_LIMIT_STRICT_MODE=True,
            ),
            pytest.MonkeyPatch.context() as mp,
        ):
            mp.setattr("limits.storage.RedisStorage", _FalsyCheckStorage)
            with pytest.raises(RuntimeError, match="fail_closed"):
                rate_limits._resolve_storage_uri()

    def test_fail_closed_policy_still_refuses_to_start(self):
        """The old posture remains available for operators who want it."""
        from shared import rate_limits

        with _patched(
            REDIS_URL=DEAD_REDIS,
            RATE_LIMIT_STORAGE_FAILURE_POLICY="fail_closed",
            RATE_LIMIT_STRICT_MODE=True,
        ):
            with pytest.raises(RuntimeError, match="fail_closed"):
                rate_limits._resolve_storage_uri()

    def test_unconstructable_uri_degrades_to_memory(self):
        """A URI slowapi could not build from must not crash the process."""
        from shared import rate_limits

        class _BoomStorage:
            def __init__(self, *_a, **_kw):
                raise ValueError("Redis URL must specify one of the following schemes")

        with (
            _patched(
                REDIS_URL="not-a-redis-url",
                RATE_LIMIT_STORAGE_FAILURE_POLICY="degrade",
                RATE_LIMIT_STRICT_MODE=True,
            ),
            pytest.MonkeyPatch.context() as mp,
        ):
            mp.setattr("limits.storage.RedisStorage", _BoomStorage)
            assert rate_limits._resolve_storage_uri() == "memory://"


class TestStorageHealthReporting:
    """Degradation must be observable, so an outage is never silent again."""

    def test_reports_configured_and_active_backend(self):
        from shared.rate_limits import get_storage_health

        health = get_storage_health()
        assert set(health) == {
            "configured_backend",
            "active_backend",
            "degraded",
            "reachable_at_boot",
        }
        assert health["configured_backend"] in ("redis", "memory")
        assert health["active_backend"] in ("redis", "memory")

    def test_degraded_tracks_live_fallback_state(self):
        """degraded follows slowapi's live flag, so it clears on recovery."""
        from shared import rate_limits

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(rate_limits, "_storage_uri", "redis://example:6379/0")
            mp.setattr(rate_limits.limiter, "_storage_dead", True, raising=False)
            health = rate_limits.get_storage_health()
            assert health["degraded"] is True
            assert health["active_backend"] == "memory"

            mp.setattr(rate_limits.limiter, "_storage_dead", False, raising=False)
            recovered = rate_limits.get_storage_health()
            assert recovered["degraded"] is False
            assert recovered["active_backend"] == "redis"

    def test_memory_backend_is_not_degraded(self):
        """Intentional memory:// (dev default) is healthy, not degraded."""
        from shared import rate_limits

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(rate_limits, "_storage_uri", "memory://")
            mp.setattr(rate_limits.limiter, "_storage_dead", False, raising=False)
            health = rate_limits.get_storage_health()
            assert health["configured_backend"] == "memory"
            assert health["degraded"] is False


def _patched(**values):
    """Patch config attributes read by _resolve_storage_uri."""
    from contextlib import ExitStack
    from unittest.mock import patch

    class _Ctx:
        def __enter__(self):
            self._stack = ExitStack()
            for key, value in values.items():
                self._stack.enter_context(patch(f"config.{key}", value))
            return self

        def __exit__(self, *exc):
            self._stack.close()
            return False

    return _Ctx()
