"""Sprint 872 (AZ-14): every error response has one shape.

Through the real middleware stack (``main.app``), the errors produced by
route handlers *and* by middleware — 401, CSRF 403, impersonation 403, 400/413
from the body-size guard, 422, 429 from both rate-limit paths, and an
unhandled 500 — all carry exactly ``{code, message, request_id, detail}``,
expose a request ID that matches the ``X-Request-ID`` header, and leak no
internals.

Before: the CSRF and body-size middleware returned ``{"detail": ...}``, the
impersonation guard had no ``request_id``, and rate limits went through
SlowAPI's ``{"error": "Rate limit exceeded: ..."}`` handler.
"""

from __future__ import annotations

from collections.abc import Iterator

import httpx
import pytest

from auth import create_access_token
from database import get_db
from main import app
from security_middleware import MAX_REQUEST_BODY_BYTES

ENVELOPE_KEYS = {"code", "message", "request_id", "detail"}
SECRET = "db-password=hunter2 at /srv/app/internal.py line 42"


@pytest.fixture
def client(db_session) -> Iterator[httpx.AsyncClient]:
    app.dependency_overrides[get_db] = lambda: db_session
    try:
        yield httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app, raise_app_exceptions=False),
            base_url="http://test",
        )
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def boom_route() -> Iterator[str]:
    path = "/__test__/boom-872"

    async def boom() -> None:
        raise RuntimeError(SECRET)

    app.add_api_route(path, boom, methods=["GET"])
    try:
        yield path
    finally:
        app.router.routes[:] = [r for r in app.router.routes if getattr(r, "path", None) != path]


def assert_envelope(resp: httpx.Response, status: int) -> dict:
    assert resp.status_code == status, resp.text
    assert resp.headers["content-type"].startswith("application/json")
    body = resp.json()
    assert set(body) == ENVELOPE_KEYS, body
    assert isinstance(body["code"], str) and body["code"]
    assert isinstance(body["message"], str) and body["message"]
    assert isinstance(body["request_id"], str) and body["request_id"] not in ("", "-")
    assert resp.headers.get("X-Request-ID") == body["request_id"]
    text = resp.text
    for leak in ("Traceback", "hunter2", "internal.py", "loc", "RuntimeError"):
        assert leak not in text, f"{leak!r} leaked in {text}"
    return body


@pytest.mark.asyncio
async def test_401(client):
    body = assert_envelope(await client.get("/auth/me"), 401)
    assert body["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_csrf_403(client, make_user, monkeypatch):
    # The session-scoped ``bypass_csrf`` fixture stays active once any earlier
    # test used it; force the real rejection path regardless of test order.
    import security_middleware

    monkeypatch.setattr(security_middleware, "validate_csrf_token", lambda token, expected_user_id=None: False)
    user = make_user(email="envelope-872@example.com")
    token, _ = create_access_token(user.id, user.email)
    resp = await client.post("/clients", json={"name": "x"}, headers={"Authorization": f"Bearer {token}"})
    body = assert_envelope(resp, 403)
    assert body["code"] == "CSRF_FAILED"


@pytest.mark.asyncio
async def test_413_content_length(client):
    resp = await client.post(
        "/auth/login",
        content=b"{}",
        headers={"Content-Length": str(MAX_REQUEST_BODY_BYTES + 1), "Content-Type": "application/json"},
    )
    body = assert_envelope(resp, 413)
    assert body["code"] == "PAYLOAD_TOO_LARGE"


@pytest.mark.asyncio
async def test_400_bad_content_length(client):
    resp = await client.post(
        "/auth/login", content=b"{}", headers={"Content-Length": "abc", "Content-Type": "application/json"}
    )
    assert_envelope(resp, 400)


@pytest.mark.asyncio
async def test_422(client):
    body = assert_envelope(await client.post("/auth/login", json={"email": 12}), 422)
    assert body["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
@pytest.mark.usefixtures("limiter_enabled")
async def test_429_default_limit_middleware(client):
    """Undecorated route: limited by DefaultLimitMiddleware, outside RequestIdMiddleware."""
    statuses = [(await client.get("/auth/me")).status_code for _ in range(61)]
    assert statuses[-1] == 429, statuses
    resp = await client.get("/auth/me")
    body = assert_envelope(resp, 429)
    assert body["code"] == "RATE_LIMITED"


@pytest.mark.asyncio
@pytest.mark.usefixtures("limiter_enabled")
async def test_429_decorated_route(client):
    """Decorated route: RateLimitExceeded raised inside the route."""
    creds = {"email": "nobody-872@example.com", "password": "Wrong-pass-1!"}
    for _ in range(5):
        await client.post("/auth/login", json=creds)
    body = assert_envelope(await client.post("/auth/login", json=creds), 429)
    assert body["code"] == "RATE_LIMITED"


@pytest.mark.asyncio
async def test_unhandled_500(client, boom_route):
    body = assert_envelope(await client.get(boom_route), 500)
    assert body["code"] == "INTERNAL_ERROR"


@pytest.mark.asyncio
async def test_impersonation_read_only_403(client, make_user):
    import jwt

    from config import JWT_ALGORITHM, JWT_SECRET_KEY

    user = make_user(email="imp-envelope-872@example.com")
    token = jwt.encode({"sub": str(user.id), "imp": True}, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    resp = await client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
    body = assert_envelope(resp, 403)
    assert body["code"] == "IMPERSONATION_READ_ONLY"


@pytest.mark.asyncio
async def test_client_request_id_is_echoed(client):
    resp = await client.get("/auth/me", headers={"X-Request-ID": "trace-abc-123"})
    body = assert_envelope(resp, 401)
    assert body["request_id"] == "trace-abc-123"
