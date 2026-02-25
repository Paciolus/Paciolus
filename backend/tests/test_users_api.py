"""
Tests for Users API Endpoints — Sprint 285

Tests cover:
- PUT /users/me — update name
- PUT /users/me/password — change password
- Route registration checks
- 401 on missing auth
"""

import sys

import httpx
import pytest

sys.path.insert(0, "..")

from auth import hash_password, require_current_user
from database import get_db
from main import app
from models import User, UserTier

# =============================================================================
# Fixtures
# =============================================================================

TEST_PASSWORD = "TestPass1!"


@pytest.fixture
def mock_user(db_session):
    """Create a real user in the test DB with a valid bcrypt hash."""
    user = User(
        email="users_test@example.com",
        name="Users Test User",
        hashed_password=hash_password(TEST_PASSWORD),
        tier=UserTier.TEAM,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def override_auth(mock_user, db_session):
    """Override auth and DB dependencies for route testing."""
    app.dependency_overrides[require_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: db_session
    yield
    app.dependency_overrides.clear()


# =============================================================================
# PUT /users/me — Profile Update
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestUpdateProfile:
    """Tests for PUT /users/me endpoint."""

    @pytest.mark.asyncio
    async def test_update_name_success(self, override_auth):
        """PUT /users/me with valid name returns 200 and updated name."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.put("/users/me", json={"name": "New Name"})
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "New Name"

    @pytest.mark.asyncio
    async def test_update_name_too_long_rejected(self, override_auth):
        """PUT /users/me with name exceeding max_length returns 422."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.put("/users/me", json={"name": "X" * 201})
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_profile_no_auth(self):
        """PUT /users/me without auth returns 401."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.put("/users/me", json={"name": "No Auth"})
            assert response.status_code == 401


# =============================================================================
# PUT /users/me/password — Password Change
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestChangePassword:
    """Tests for PUT /users/me/password endpoint."""

    @pytest.mark.asyncio
    async def test_change_password_success(self, override_auth):
        """PUT /users/me/password with valid current + new returns 200."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.put(
                "/users/me/password",
                json={
                    "current_password": TEST_PASSWORD,
                    "new_password": "NewSecure1!",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    @pytest.mark.asyncio
    async def test_change_password_wrong_current(self, override_auth):
        """PUT /users/me/password with wrong current password returns 400."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.put(
                "/users/me/password",
                json={
                    "current_password": "WrongPassword1!",
                    "new_password": "NewSecure1!",
                },
            )
            assert response.status_code == 400
            assert "Current password is incorrect" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_change_password_no_auth(self):
        """PUT /users/me/password without auth returns 401."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.put(
                "/users/me/password",
                json={
                    "current_password": "Whatever1!",
                    "new_password": "NewSecure1!",
                },
            )
            assert response.status_code == 401


# =============================================================================
# Route Registration
# =============================================================================


class TestUserRouteRegistration:
    """Verify user routes are registered in the app."""

    def test_users_me_route_exists(self):
        """PUT /users/me route is registered."""
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/users/me" in paths

    def test_users_me_password_route_exists(self):
        """PUT /users/me/password route is registered."""
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/users/me/password" in paths
