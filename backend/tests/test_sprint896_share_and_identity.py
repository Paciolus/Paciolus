"""Sprint 896 (council 2026-11-25): G-01 passcode share downloads, G-02 rate-limit identity.

G-01: the passcode POST was CSRF-checked, and an anonymous recipient cannot get a
CSRF token, so every passcode-protected share failed for the person it was sent
to. Every earlier download test used ``bypass_csrf``; these do not.

G-02: the rate-limit identity read only a Bearer header. Browsers authenticate
with the HttpOnly access cookie, so signed-in users were limited as anonymous,
by IP.
"""

from __future__ import annotations

import httpx
import pytest
from starlette.requests import Request

from security_middleware import CSRF_EXEMPT_PATTERNS, RateLimitIdentityMiddleware


@pytest.mark.parametrize(
    "path, exempt",
    [
        ("/export-sharing/AbC_-123xyz/download", True),
        ("/export-sharing/AbC_-123xyz", False),
        ("/export-sharing/create", False),
        ("/export-sharing/a/b/download", False),
        ("/export-sharing/tok/download/extra", False),
        ("/export-sharing/../auth/download", False),
    ],
)
def test_only_the_public_download_path_is_exempt(path, exempt):
    assert any(p.match(path) for p in CSRF_EXEMPT_PATTERNS) is exempt


@pytest.mark.anyio
async def test_passcode_post_reaches_the_route_without_a_csrf_token(db_session):
    """No bypass_csrf: the middleware lets the anonymous POST through; the route answers 404."""
    from database import get_db
    from main import app

    app.dependency_overrides[get_db] = lambda: db_session
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/export-sharing/not-a-real-token-0123456789/download",
                json={"passcode": "whatever"},
                headers={"Origin": "http://localhost:3000"},
            )
        assert resp.status_code == 404, resp.text
    finally:
        app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_other_share_mutations_still_need_csrf(db_session):
    from database import get_db
    from main import app

    app.dependency_overrides[get_db] = lambda: db_session
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/export-sharing/create",
                json={},
                headers={"Origin": "http://localhost:3000"},
            )
        assert resp.status_code == 403, resp.text
    finally:
        app.dependency_overrides.clear()


def _request(headers: dict[str, str]) -> Request:
    raw = [(k.lower().encode(), v.encode()) for k, v in headers.items()]
    return Request(
        {"type": "http", "method": "GET", "path": "/x", "headers": raw, "client": ("1.2.3.4", 1), "state": {}}
    )


async def _identity(request: Request) -> tuple[object, object]:
    middleware = RateLimitIdentityMiddleware(app=lambda *_: None)

    async def call_next(req):  # noqa: ANN001
        return None

    await middleware.dispatch(request, call_next)
    return request.state.rate_limit_user_id, request.state.rate_limit_user_tier


@pytest.mark.anyio
async def test_cookie_authenticated_browser_gets_its_own_bucket_and_tier():
    from auth import create_access_token
    from config import ACCESS_COOKIE_NAME

    token, _ = create_access_token(42, "u42@example.com", tier="professional")
    user_id, tier = await _identity(_request({"cookie": f"{ACCESS_COOKIE_NAME}={token}"}))
    assert (user_id, tier) == (42, "professional")


@pytest.mark.anyio
async def test_bearer_still_works_and_garbage_is_anonymous():
    from auth import create_access_token

    token, _ = create_access_token(7, "u7@example.com", tier="solo")
    assert await _identity(_request({"authorization": f"Bearer {token}"})) == (7, "solo")
    assert await _identity(_request({"cookie": "paciolus_access=not-a-jwt"})) == (None, "anonymous")
    assert await _identity(_request({})) == (None, "anonymous")
