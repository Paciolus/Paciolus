"""
Tests for Password Reset Flow — Sprint 572

Tests cover:
- POST /auth/forgot-password — success, unknown email (no enumeration), inactive user
- POST /auth/reset-password — success, invalid token, expired token, used token, short password
- CSRF exemption verification
- Lockout reset after password reset
"""

import sys
from datetime import UTC, datetime, timedelta

import httpx
import pytest

sys.path.insert(0, "..")

from auth import UserCreate, create_user, hash_token
from database import get_db
from main import app
from models import PasswordResetToken

# =============================================================================
# Fixtures
# =============================================================================

TEST_PASSWORD = "TestPass1!"
NEW_PASSWORD = "NewSecure9!"


@pytest.fixture
def reset_user(db_session):
    """Create a verified, active user for password reset tests."""
    user_data = UserCreate(email="reset@example.com", password=TEST_PASSWORD)
    user = create_user(db_session, user_data)
    user.is_verified = True
    user.is_active = True
    db_session.flush()
    return user


@pytest.fixture
def reset_token(db_session, reset_user):
    """Create a valid password reset token for the test user."""
    from email_service import generate_password_reset_token

    token_result = generate_password_reset_token()
    db_token = PasswordResetToken(
        user_id=reset_user.id,
        token_hash=hash_token(token_result.token),
        expires_at=token_result.expires_at,
    )
    db_session.add(db_token)
    db_session.flush()
    return token_result.token, db_token


@pytest.fixture
def client_with_db(db_session):
    """Override get_db for async test client."""
    app.dependency_overrides[get_db] = lambda: db_session
    yield
    app.dependency_overrides.clear()


# =============================================================================
# POST /auth/forgot-password
# =============================================================================


class TestForgotPassword:
    """Tests for the forgot-password endpoint."""

    @pytest.mark.asyncio
    async def test_forgot_password_known_email(self, db_session, reset_user, client_with_db):
        """Should return success and create a PasswordResetToken."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/auth/forgot-password", json={"email": "reset@example.com"})

        assert response.status_code == 200
        data = response.json()
        assert "if an account" in data["message"].lower()

        token = db_session.query(PasswordResetToken).filter_by(user_id=reset_user.id).first()
        assert token is not None
        assert token.used_at is None

    @pytest.mark.asyncio
    async def test_forgot_password_unknown_email(self, db_session, client_with_db):
        """Should return same success message (prevents enumeration)."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/auth/forgot-password", json={"email": "nonexistent@example.com"})

        assert response.status_code == 200
        data = response.json()
        assert "if an account" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_forgot_password_inactive_user(self, db_session, reset_user, client_with_db):
        """Should return success but NOT create a token for inactive users."""
        reset_user.is_active = False
        db_session.flush()

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/auth/forgot-password", json={"email": "reset@example.com"})

        assert response.status_code == 200
        token = db_session.query(PasswordResetToken).filter_by(user_id=reset_user.id).first()
        assert token is None

    @pytest.mark.asyncio
    async def test_forgot_password_empty_email(self, client_with_db):
        """Should return 422 for empty email."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/auth/forgot-password", json={"email": ""})

        assert response.status_code == 422


# =============================================================================
# POST /auth/reset-password
# =============================================================================


class TestResetPassword:
    """Tests for the reset-password endpoint."""

    @pytest.mark.asyncio
    async def test_reset_password_success(self, db_session, reset_user, reset_token, client_with_db):
        """Should reset password, mark token used, and clear lockout."""
        raw_token, db_token = reset_token

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/auth/reset-password",
                json={"token": raw_token, "new_password": NEW_PASSWORD},
            )

        assert response.status_code == 200
        data = response.json()
        assert "reset successfully" in data["message"].lower()

        db_session.refresh(db_token)
        assert db_token.used_at is not None

        db_session.refresh(reset_user)
        assert reset_user.password_changed_at is not None
        assert reset_user.failed_login_attempts == 0
        assert reset_user.locked_until is None

    @pytest.mark.asyncio
    async def test_reset_password_invalid_token(self, db_session, client_with_db):
        """Should return 400 for an invalid token."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/auth/reset-password",
                json={"token": "completely_invalid_token_value", "new_password": NEW_PASSWORD},
            )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_reset_password_expired_token(self, db_session, reset_user, client_with_db):
        """Should return 400 for an expired token."""
        from email_service import generate_password_reset_token

        token_result = generate_password_reset_token()
        db_token = PasswordResetToken(
            user_id=reset_user.id,
            token_hash=hash_token(token_result.token),
            expires_at=datetime.now(UTC) - timedelta(hours=2),
        )
        db_session.add(db_token)
        db_session.flush()

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/auth/reset-password",
                json={"token": token_result.token, "new_password": NEW_PASSWORD},
            )

        assert response.status_code == 400
        assert "expired" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_reset_password_used_token(self, db_session, reset_user, reset_token, client_with_db):
        """Should return 400 if token was already used."""
        raw_token, db_token = reset_token
        db_token.used_at = datetime.now(UTC)
        db_session.flush()

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/auth/reset-password",
                json={"token": raw_token, "new_password": NEW_PASSWORD},
            )

        assert response.status_code == 400
        assert "already been used" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_reset_password_short_password(self, db_session, reset_user, reset_token, client_with_db):
        """Should return 422 for password shorter than 8 chars."""
        raw_token, _ = reset_token

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/auth/reset-password",
                json={"token": raw_token, "new_password": "short"},
            )

        assert response.status_code == 422


# =============================================================================
# CSRF Exemption
# =============================================================================


class TestPasswordResetCsrf:
    """Verify password reset endpoints are CSRF-exempt."""

    def test_forgot_password_csrf_exempt(self):
        from security_middleware import CSRF_EXEMPT_PATHS

        assert "/auth/forgot-password" in CSRF_EXEMPT_PATHS

    def test_reset_password_csrf_exempt(self):
        from security_middleware import CSRF_EXEMPT_PATHS

        assert "/auth/reset-password" in CSRF_EXEMPT_PATHS


# =============================================================================
# Lockout Reset
# =============================================================================


class TestPasswordResetLockout:
    """Verify password reset clears lockout state."""

    @pytest.mark.asyncio
    async def test_reset_clears_lockout(self, db_session, reset_user, reset_token, client_with_db):
        """A locked-out user should be unlocked after password reset."""
        reset_user.failed_login_attempts = 10
        reset_user.locked_until = datetime.now(UTC) + timedelta(hours=1)
        db_session.flush()

        raw_token, _ = reset_token

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/auth/reset-password",
                json={"token": raw_token, "new_password": NEW_PASSWORD},
            )

        assert response.status_code == 200
        db_session.refresh(reset_user)
        assert reset_user.failed_login_attempts == 0
        assert reset_user.locked_until is None
