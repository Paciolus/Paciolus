"""Sprint 872 (AZ-10): CSRF on /auth/refresh and /auth/logout is bound to the
owner of the refresh cookie.

Before: with no bearer token and no access cookie, the CSRF middleware had no
user to compare against (`expected_user_id = None`), so any validly signed
CSRF token — e.g. the attacker's own — passed, and the handlers then rotated
or revoked whichever refresh token the victim's browser sent.

These tests go through the real middleware stack and the real database; the
CSRF bypass fixture is deliberately not used.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx
import jwt
import pytest

from config import ACCESS_COOKIE_NAME, JWT_ALGORITHM, JWT_SECRET_KEY, REFRESH_COOKIE_NAME
from database import get_db
from main import app
from models import RefreshToken
from security_middleware import generate_csrf_token

PATHS = ["/auth/refresh", "/auth/logout"]


@pytest.fixture()
def override_db(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    yield
    app.dependency_overrides.clear()


@pytest.fixture()
def two_users(make_user, make_refresh_token):
    user_a = make_user(email="csrf-owner-a@example.com")
    user_b = make_user(email="csrf-owner-b@example.com")
    raw_b, row_b = make_refresh_token(user=user_b)
    return user_a, user_b, raw_b, row_b


def _expired_access_token(user) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": str(user.id),
            "email": user.email,
            "exp": now - timedelta(minutes=5),
            "iat": now - timedelta(minutes=20),
            "jti": "expired-test",
        },
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


async def _post(path: str, *, csrf: str, cookies: dict[str, str]) -> httpx.Response:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test", cookies=cookies
    ) as client:
        return await client.post(
            path,
            headers={"X-CSRF-Token": csrf, "X-Requested-With": "XMLHttpRequest"},
        )


def _is_revoked(db_session, row: RefreshToken) -> bool:
    db_session.expire_all()
    return db_session.get(RefreshToken, row.id).revoked_at is not None


@pytest.mark.asyncio
@pytest.mark.parametrize("path", PATHS)
async def test_other_users_csrf_with_victims_refresh_cookie_is_403(path, override_db, db_session, two_users):
    user_a, _user_b, raw_b, row_b = two_users
    resp = await _post(path, csrf=generate_csrf_token(str(user_a.id)), cookies={REFRESH_COOKIE_NAME: raw_b})
    assert resp.status_code == 403
    assert not _is_revoked(db_session, row_b), "victim's refresh token must not be rotated or revoked"


@pytest.mark.asyncio
@pytest.mark.parametrize("path", PATHS)
async def test_mismatch_is_403_with_an_expired_access_cookie(path, override_db, db_session, two_users):
    """An expired access cookie for A (matching A's CSRF token) must not lend
    A's identity to B's refresh cookie."""
    user_a, _user_b, raw_b, row_b = two_users
    resp = await _post(
        path,
        csrf=generate_csrf_token(str(user_a.id)),
        cookies={REFRESH_COOKIE_NAME: raw_b, ACCESS_COOKIE_NAME: _expired_access_token(user_a)},
    )
    assert resp.status_code == 403
    assert not _is_revoked(db_session, row_b)


@pytest.mark.asyncio
async def test_owner_can_refresh(override_db, db_session, two_users):
    _user_a, user_b, raw_b, row_b = two_users
    resp = await _post("/auth/refresh", csrf=generate_csrf_token(str(user_b.id)), cookies={REFRESH_COOKIE_NAME: raw_b})
    assert resp.status_code == 200, resp.text
    assert resp.json()["user"]["id"] == user_b.id
    assert _is_revoked(db_session, row_b), "rotation revokes the presented token"


@pytest.mark.asyncio
async def test_owner_can_logout(override_db, db_session, two_users):
    _user_a, user_b, raw_b, row_b = two_users
    resp = await _post("/auth/logout", csrf=generate_csrf_token(str(user_b.id)), cookies={REFRESH_COOKIE_NAME: raw_b})
    assert resp.status_code == 200, resp.text
    assert _is_revoked(db_session, row_b)
