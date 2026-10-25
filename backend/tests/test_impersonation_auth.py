"""Sprint 840 (claims review S3): impersonation is read-only in the auth layer itself.

ImpersonationMiddleware only looked at a header starting with "Bearer ", let
writes through once a token was revoked, and the stop endpoint read the admin's
own Authorization header as the impersonation token — so it could never
succeed. These tests run real tokens through ``require_current_user`` and the
real app.
"""

import httpx
import pytest
from fastapi import HTTPException
from starlette.requests import Request

from auth import create_access_token, create_impersonation_token, require_current_user
from database import get_db
from main import app
from shared.impersonation_revocation import _reset_for_tests, is_revoked


def _request(method: str) -> Request:
    return Request({"type": "http", "method": method, "headers": [], "path": "/", "query_string": b""})


@pytest.fixture(autouse=True)
def _clean_revocations():
    _reset_for_tests()
    yield
    _reset_for_tests()


@pytest.fixture
def target(make_user):
    return make_user(email="imp_target@example.com")


@pytest.fixture
def admin(db_session, make_user):
    user = make_user(email="imp_admin@example.com")
    user.is_superadmin = True
    db_session.commit()
    return user


def _imp_token(target, admin):
    token, _ = create_impersonation_token(target.id, target.email, admin.id)
    return token


class TestDependency:
    def test_read_is_allowed(self, db_session, target, admin):
        user = require_current_user(_request("GET"), _imp_token(target, admin), db_session)
        assert user.id == target.id

    @pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
    def test_writes_are_refused(self, db_session, target, admin, method):
        with pytest.raises(HTTPException) as exc:
            require_current_user(_request(method), _imp_token(target, admin), db_session)
        assert exc.value.status_code == 403

    def test_revoked_token_is_dead_for_reads_too(self, db_session, target, admin):
        import jwt

        from config import JWT_ALGORITHM, JWT_SECRET_KEY
        from shared.impersonation_revocation import revoke

        token = _imp_token(target, admin)
        revoke(jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])["jti"], 3600)
        with pytest.raises(HTTPException) as exc:
            require_current_user(_request("GET"), token, db_session)
        assert exc.value.status_code == 401

    def test_ordinary_token_can_still_write(self, db_session, target):
        token, _ = create_access_token(target.id, target.email)
        assert require_current_user(_request("POST"), token, db_session).id == target.id


@pytest.mark.usefixtures("bypass_csrf")
class TestApp:
    @pytest.fixture(autouse=True)
    def _db(self, db_session):
        app.dependency_overrides[get_db] = lambda: db_session
        yield
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_lowercase_bearer_write_is_refused(self, target, admin):
        token = _imp_token(target, admin)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            r = await client.post("/auth/logout", headers={"Authorization": f"bearer {token}"})
        assert r.status_code == 403

    @pytest.mark.asyncio
    async def test_stop_endpoint_revokes_the_token(self, target, admin):
        import jwt

        from config import JWT_ALGORITHM, JWT_SECRET_KEY

        imp = _imp_token(target, admin)
        admin_token, _ = create_access_token(admin.id, admin.email)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            r = await client.post(
                "/internal/admin/impersonate/stop",
                json={"token": imp},
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert r.status_code == 200, r.text
            assert is_revoked(jwt.decode(imp, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])["jti"])

            # The impersonation token now fails on reads as well.
            r = await client.get("/auth/me", headers={"Authorization": f"Bearer {imp}"})
            assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_stop_endpoint_requires_a_superadmin(self, target, admin):
        imp = _imp_token(target, admin)
        user_token, _ = create_access_token(target.id, target.email)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            r = await client.post(
                "/internal/admin/impersonate/stop",
                json={"token": imp},
                headers={"Authorization": f"Bearer {user_token}"},
            )
        assert r.status_code == 403
