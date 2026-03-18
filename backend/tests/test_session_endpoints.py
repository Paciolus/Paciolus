"""
Tests for AUDIT-02 FIX 2: Session Inventory & Revocation Endpoints

Tests cover:
- GET /auth/sessions — returns active sessions, does not leak token hashes
- DELETE /auth/sessions/{session_id} — revokes only caller's own session
- DELETE /auth/sessions — revokes all caller's sessions
- Ownership enforcement: cannot revoke another user's session
"""

import hashlib
import secrets
import sys
from datetime import UTC, datetime, timedelta

import httpx
import pytest

sys.path.insert(0, "..")

from auth import hash_password, require_current_user
from database import get_db
from main import app
from models import RefreshToken, User, UserTier

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def user_a(db_session):
    """Create User A for session tests."""
    user = User(
        email="session_a@example.com",
        hashed_password=hash_password("TestPass1!"),
        tier=UserTier.PROFESSIONAL,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def user_b(db_session):
    """Create User B for ownership tests."""
    user = User(
        email="session_b@example.com",
        hashed_password=hash_password("TestPass1!"),
        tier=UserTier.PROFESSIONAL,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def override_auth_a(db_session, user_a):
    """Override auth + DB for User A."""
    app.dependency_overrides[require_current_user] = lambda: user_a
    app.dependency_overrides[get_db] = lambda: db_session
    yield user_a
    app.dependency_overrides.clear()


@pytest.fixture
def override_auth_b(db_session, user_b):
    """Override auth + DB for User B."""
    app.dependency_overrides[require_current_user] = lambda: user_b
    app.dependency_overrides[get_db] = lambda: db_session
    yield user_b
    app.dependency_overrides.clear()


def _create_token(db_session, user_id, user_agent=None, ip_address=None):
    """Helper: create a refresh token row directly in the DB."""
    raw = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    rt = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=datetime.now(UTC) + timedelta(days=7),
        user_agent=user_agent,
        ip_address=ip_address,
    )
    db_session.add(rt)
    db_session.flush()
    return rt


# =============================================================================
# GET /auth/sessions
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestListSessions:
    """Tests for GET /auth/sessions."""

    @pytest.mark.asyncio
    async def test_list_sessions_returns_active_only(self, db_session, override_auth_a, user_a):
        """GET /auth/sessions returns only non-revoked tokens for the caller."""
        # Create 2 active + 1 revoked token for User A
        _create_token(db_session, user_a.id, user_agent="Firefox", ip_address="1.2.3.4")
        _create_token(db_session, user_a.id, user_agent="Chrome", ip_address="5.6.7.8")
        revoked = _create_token(db_session, user_a.id)
        revoked.revoked_at = datetime.now(UTC)
        db_session.flush()

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/auth/sessions")
            assert resp.status_code == 200
            data = resp.json()
            assert "sessions" in data
            assert len(data["sessions"]) == 2

    @pytest.mark.asyncio
    async def test_list_sessions_does_not_leak_token_hash(self, db_session, override_auth_a, user_a):
        """GET /auth/sessions must never return token_hash."""
        _create_token(db_session, user_a.id)

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/auth/sessions")
            assert resp.status_code == 200
            data = resp.json()
            for session in data["sessions"]:
                assert "token_hash" not in session
                assert "session_id" in session

    @pytest.mark.asyncio
    async def test_list_sessions_includes_metadata(self, db_session, override_auth_a, user_a):
        """GET /auth/sessions returns user_agent and ip_address."""
        _create_token(db_session, user_a.id, user_agent="TestAgent/1.0", ip_address="10.0.0.1")

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/auth/sessions")
            assert resp.status_code == 200
            sessions = resp.json()["sessions"]
            assert len(sessions) >= 1
            session = sessions[0]
            assert session["user_agent"] == "TestAgent/1.0"
            assert session["ip_address"] == "10.0.0.1"

    @pytest.mark.asyncio
    async def test_list_sessions_requires_auth(self):
        """GET /auth/sessions without auth returns 401."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/auth/sessions")
            assert resp.status_code == 401


# =============================================================================
# DELETE /auth/sessions/{session_id} — Single session revocation
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestRevokeSession:
    """Tests for DELETE /auth/sessions/{session_id}."""

    @pytest.mark.asyncio
    async def test_revoke_own_session(self, db_session, override_auth_a, user_a):
        """DELETE /auth/sessions/{id} revokes the caller's own session → 204."""
        token = _create_token(db_session, user_a.id)

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.delete(f"/auth/sessions/{token.id}")
            assert resp.status_code == 204

        # Verify it's revoked in DB
        db_session.refresh(token)
        assert token.revoked_at is not None

    @pytest.mark.asyncio
    async def test_revoke_other_users_session_returns_404(self, db_session, override_auth_a, user_b):
        """DELETE /auth/sessions/{id} for another user's session → 404."""
        token_b = _create_token(db_session, user_b.id)

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.delete(f"/auth/sessions/{token_b.id}")
            assert resp.status_code == 404

        # Verify it's NOT revoked
        db_session.refresh(token_b)
        assert token_b.revoked_at is None

    @pytest.mark.asyncio
    async def test_revoke_nonexistent_session_returns_404(self, override_auth_a):
        """DELETE /auth/sessions/99999 → 404."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.delete("/auth/sessions/99999")
            assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_revoke_already_revoked_session_returns_404(self, db_session, override_auth_a, user_a):
        """DELETE /auth/sessions/{id} for already-revoked session → 404."""
        token = _create_token(db_session, user_a.id)
        token.revoked_at = datetime.now(UTC)
        db_session.flush()

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.delete(f"/auth/sessions/{token.id}")
            assert resp.status_code == 404


# =============================================================================
# DELETE /auth/sessions — Revoke all sessions
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestRevokeAllSessions:
    """Tests for DELETE /auth/sessions (revoke all)."""

    @pytest.mark.asyncio
    async def test_revoke_all_sessions(self, db_session, override_auth_a, user_a):
        """DELETE /auth/sessions revokes all active sessions for the caller → 204."""
        t1 = _create_token(db_session, user_a.id)
        t2 = _create_token(db_session, user_a.id)

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.delete("/auth/sessions")
            assert resp.status_code == 204

        db_session.refresh(t1)
        db_session.refresh(t2)
        assert t1.revoked_at is not None
        assert t2.revoked_at is not None

    @pytest.mark.asyncio
    async def test_revoke_all_does_not_affect_other_users(self, db_session, override_auth_a, user_a, user_b):
        """DELETE /auth/sessions only revokes the caller's sessions, not other users'."""
        _create_token(db_session, user_a.id)
        token_b = _create_token(db_session, user_b.id)

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.delete("/auth/sessions")
            assert resp.status_code == 204

        db_session.refresh(token_b)
        assert token_b.revoked_at is None  # User B's session untouched


# =============================================================================
# Route Registration
# =============================================================================


class TestSessionRouteRegistration:
    """Verify session routes are registered."""

    def test_get_sessions_route_exists(self):
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/auth/sessions" in paths

    def test_delete_session_route_exists(self):
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/auth/sessions/{session_id}" in paths
