"""
Tests for ImpersonationMiddleware — Sprint 598 hardening.

Covers:
1. Non-mutation methods (GET/HEAD/OPTIONS) pass through without any JWT check.
2. Missing Authorization header → pass through.
3. Valid non-impersonation token → pass through.
4. Valid impersonation token (imp: true) on mutation → 403 with IMPERSONATION_READ_ONLY code.
5. Malformed JWT on mutation → pass through to downstream (auth dependency handles it).
6. Expired impersonation token still blocks mutations (verify_exp=False in middleware).
"""

import os
import sys
import time
from typing import Any

import httpx
import jwt as pyjwt
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


async def _echo_app(scope: dict, receive: Any, send: Any) -> None:
    """Minimal ASGI app that returns 200 OK."""
    from starlette.responses import Response

    response = Response("ok", media_type="text/plain")
    await response(scope, receive, send)


def _build_middleware():
    from security_middleware import ImpersonationMiddleware

    return ImpersonationMiddleware(_echo_app)


def _encode(payload: dict) -> str:
    from config import JWT_ALGORITHM, JWT_SECRET_KEY

    return pyjwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


class TestImpersonationMiddleware:
    @pytest.mark.asyncio
    async def test_get_passes_through_without_auth(self):
        middleware = _build_middleware()
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=middleware),
            base_url="http://test",
        ) as client:
            r = await client.get("/anything")
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_post_without_auth_passes_through(self):
        """No Authorization header on a mutation → downstream handles auth (401)."""
        middleware = _build_middleware()
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=middleware),
            base_url="http://test",
        ) as client:
            r = await client.post("/anything")
        assert r.status_code == 200  # echo app returns 200; middleware did not block

    @pytest.mark.asyncio
    async def test_post_with_valid_non_imp_token_passes_through(self):
        token = _encode(
            {
                "sub": "42",
                "email": "user@example.com",
                "tier": "professional",
                "exp": int(time.time()) + 3600,
            }
        )
        middleware = _build_middleware()
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=middleware),
            base_url="http://test",
        ) as client:
            r = await client.post("/anything", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_post_with_imp_token_is_blocked(self):
        token = _encode(
            {
                "sub": "42",
                "email": "user@example.com",
                "imp": True,
                "exp": int(time.time()) + 3600,
            }
        )
        middleware = _build_middleware()
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=middleware),
            base_url="http://test",
        ) as client:
            r = await client.post("/anything", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 403
        body = r.json()
        assert body["code"] == "IMPERSONATION_READ_ONLY"

    @pytest.mark.asyncio
    async def test_put_with_imp_token_is_blocked(self):
        token = _encode(
            {
                "sub": "42",
                "email": "user@example.com",
                "imp": True,
                "exp": int(time.time()) + 3600,
            }
        )
        middleware = _build_middleware()
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=middleware),
            base_url="http://test",
        ) as client:
            r = await client.put("/anything", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_with_imp_token_is_blocked(self):
        token = _encode(
            {
                "sub": "42",
                "email": "user@example.com",
                "imp": True,
                "exp": int(time.time()) + 3600,
            }
        )
        middleware = _build_middleware()
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=middleware),
            base_url="http://test",
        ) as client:
            r = await client.delete("/anything", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 403

    @pytest.mark.asyncio
    async def test_expired_imp_token_still_blocks(self):
        """Middleware uses verify_exp=False — expired imp tokens are still read-only."""
        token = _encode(
            {
                "sub": "42",
                "email": "user@example.com",
                "imp": True,
                "exp": int(time.time()) - 3600,  # expired 1h ago
            }
        )
        middleware = _build_middleware()
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=middleware),
            base_url="http://test",
        ) as client:
            r = await client.post("/anything", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 403

    @pytest.mark.asyncio
    async def test_malformed_jwt_falls_through_to_downstream(self):
        """Sprint 598: PyJWTError → pass through (downstream auth returns 401).

        Previously used bare `except Exception: pass`. Now narrowed to
        jwt.PyJWTError — unexpected exception types surface instead of being
        silently swallowed.
        """
        middleware = _build_middleware()
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=middleware),
            base_url="http://test",
        ) as client:
            r = await client.post("/anything", headers={"Authorization": "Bearer total.garbage.token"})
        # Echo app returns 200 — middleware passed through rather than raising
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_non_bearer_auth_header_passes_through(self):
        middleware = _build_middleware()
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=middleware),
            base_url="http://test",
        ) as client:
            r = await client.post("/anything", headers={"Authorization": "Basic dXNlcjpwYXNz"})
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_revoked_imp_token_stops_blocking_mutations(self):
        """Sprint 661: revoking the jti releases the mutation block."""
        from shared.impersonation_revocation import _reset_for_tests, revoke

        _reset_for_tests()

        jti = "revoked-jti-abc"
        token = _encode(
            {
                "sub": "42",
                "email": "user@example.com",
                "imp": True,
                "jti": jti,
                "exp": int(time.time()) + 3600,
            }
        )

        middleware = _build_middleware()
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=middleware),
            base_url="http://test",
        ) as client:
            r = await client.post("/anything", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 403

        revoke(jti, ttl_seconds=3600)

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=middleware),
            base_url="http://test",
        ) as client:
            r = await client.post("/anything", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200

        _reset_for_tests()
