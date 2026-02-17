"""
Tests for Auth Routes API Endpoints — Sprint 285

Tests cover:
- POST /auth/register — success, duplicate email, disposable email
- POST /auth/login — success, invalid password, nonexistent email
- POST /auth/logout — success, invalid token
- GET /auth/csrf — token generation, no auth required
- GET /auth/verification-status — verified user, no auth
- Route registration checks
"""

import sys

import httpx
import pytest

sys.path.insert(0, '..')

from auth import create_user, hash_password, require_current_user, UserCreate
from database import get_db
from main import app
from models import User, UserTier

# =============================================================================
# Fixtures
# =============================================================================

TEST_PASSWORD = "TestPass1!"


@pytest.fixture
def registered_user(db_session):
    """Create a user via create_user() with known password for login tests."""
    user_data = UserCreate(email="authtest@example.com", password=TEST_PASSWORD)
    user = create_user(db_session, user_data)
    return user


@pytest.fixture
def override_auth_for_status(db_session):
    """Create verified user + override require_current_user + get_db for verification-status."""
    user = User(
        email="verified_status@example.com",
        name="Verified User",
        hashed_password=hash_password(TEST_PASSWORD),
        tier=UserTier.PROFESSIONAL,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()

    app.dependency_overrides[require_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: db_session
    yield user
    app.dependency_overrides.clear()


@pytest.fixture
def override_db(db_session):
    """Override get_db only (for unauthenticated endpoints like register/login)."""
    app.dependency_overrides[get_db] = lambda: db_session
    yield
    app.dependency_overrides.clear()


# =============================================================================
# POST /auth/register
# =============================================================================

@pytest.mark.usefixtures("bypass_csrf")
class TestRegister:
    """Tests for POST /auth/register endpoint."""

    @pytest.mark.asyncio
    async def test_register_success(self, override_db):
        """POST /auth/register with valid data returns 201 with tokens and user."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post("/auth/register", json={
                "email": "newuser@example.com",
                "password": TEST_PASSWORD,
            })
            assert response.status_code == 201
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["user"]["email"] == "newuser@example.com"

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, override_db, registered_user):
        """POST /auth/register with existing email returns 400."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post("/auth/register", json={
                "email": registered_user.email,
                "password": TEST_PASSWORD,
            })
            assert response.status_code == 400
            assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_disposable_email(self, override_db):
        """POST /auth/register with disposable email returns 400."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post("/auth/register", json={
                "email": "user@mailinator.com",
                "password": TEST_PASSWORD,
            })
            assert response.status_code == 400
            assert "disposable" in response.json()["detail"].lower()


# =============================================================================
# POST /auth/login
# =============================================================================

@pytest.mark.usefixtures("bypass_csrf")
class TestLogin:
    """Tests for POST /auth/login endpoint."""

    @pytest.mark.asyncio
    async def test_login_success(self, override_db, registered_user):
        """POST /auth/login with correct credentials returns 200 with tokens."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post("/auth/login", json={
                "email": registered_user.email,
                "password": TEST_PASSWORD,
            })
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_invalid_password(self, override_db, registered_user):
        """POST /auth/login with wrong password returns 401."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post("/auth/login", json={
                "email": registered_user.email,
                "password": "WrongPassword1!",
            })
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_email(self, override_db):
        """POST /auth/login with unknown email returns 401."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post("/auth/login", json={
                "email": "nonexistent@example.com",
                "password": TEST_PASSWORD,
            })
            assert response.status_code == 401


# =============================================================================
# POST /auth/logout
# =============================================================================

@pytest.mark.usefixtures("bypass_csrf")
class TestLogout:
    """Tests for POST /auth/logout endpoint."""

    @pytest.mark.asyncio
    async def test_logout_success(self, override_db, registered_user):
        """POST /auth/logout with valid refresh token returns success=true."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            # First login to get a refresh token
            login_resp = await client.post("/auth/login", json={
                "email": registered_user.email,
                "password": TEST_PASSWORD,
            })
            refresh_token = login_resp.json()["refresh_token"]

            # Now logout with that token
            response = await client.post("/auth/logout", json={
                "refresh_token": refresh_token,
            })
            assert response.status_code == 200
            assert response.json()["success"] is True

    @pytest.mark.asyncio
    async def test_logout_invalid_token(self, override_db):
        """POST /auth/logout with fake token returns success=false."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post("/auth/logout", json={
                "refresh_token": "fake-token-that-does-not-exist",
            })
            assert response.status_code == 200
            assert response.json()["success"] is False


# =============================================================================
# GET /auth/csrf
# =============================================================================

class TestCsrfToken:
    """Tests for GET /auth/csrf endpoint."""

    @pytest.mark.asyncio
    async def test_csrf_returns_token(self):
        """GET /auth/csrf returns 200 with csrf_token and expires_in_minutes."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/auth/csrf")
            assert response.status_code == 200
            data = response.json()
            assert "csrf_token" in data
            assert "expires_in_minutes" in data

    @pytest.mark.asyncio
    async def test_csrf_no_auth_required(self):
        """GET /auth/csrf works without authentication."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/auth/csrf")
            assert response.status_code == 200


# =============================================================================
# GET /auth/verification-status
# =============================================================================

class TestVerificationStatus:
    """Tests for GET /auth/verification-status endpoint."""

    @pytest.mark.asyncio
    async def test_verification_status_verified_user(self, override_auth_for_status):
        """GET /auth/verification-status returns is_verified=true for verified user."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/auth/verification-status")
            assert response.status_code == 200
            data = response.json()
            assert data["is_verified"] is True

    @pytest.mark.asyncio
    async def test_verification_status_no_auth(self):
        """GET /auth/verification-status without auth returns 401."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/auth/verification-status")
            assert response.status_code == 401


# =============================================================================
# Route Registration
# =============================================================================

class TestAuthRouteRegistration:
    """Verify auth routes are registered in the app."""

    def test_register_route_exists(self):
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/auth/register" in paths

    def test_login_route_exists(self):
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/auth/login" in paths

    def test_logout_route_exists(self):
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/auth/logout" in paths

    def test_csrf_route_exists(self):
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/auth/csrf" in paths

    def test_verification_status_route_exists(self):
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/auth/verification-status" in paths
