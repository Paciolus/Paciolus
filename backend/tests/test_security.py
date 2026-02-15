"""
Tests for Sprint 49 Security Hardening.

Tests cover:
- Security headers middleware
- CSRF token generation and validation
- Account lockout mechanism
"""

import pytest
import httpx
from datetime import datetime, timedelta, UTC
from unittest.mock import patch, MagicMock

# Import security middleware functions
from security_middleware import (
    generate_csrf_token,
    validate_csrf_token,
    record_failed_login,
    check_lockout_status,
    reset_failed_attempts,
    get_lockout_info,
    hash_ip_address,
    MAX_FAILED_ATTEMPTS,
    LOCKOUT_DURATION_MINUTES,
    CSRF_TOKEN_EXPIRY_MINUTES,
    _csrf_tokens,
    _lockout_tracker,
)


# =============================================================================
# CSRF TOKEN TESTS
# =============================================================================

class TestCSRFTokenGeneration:
    """Tests for CSRF token generation."""

    def setup_method(self):
        """Clear CSRF tokens before each test."""
        _csrf_tokens.clear()

    def test_generate_csrf_token_returns_string(self):
        """Token should be a non-empty string."""
        token = generate_csrf_token()
        assert isinstance(token, str)
        assert len(token) > 0

    def test_generate_csrf_token_is_unique(self):
        """Each generated token should be unique."""
        tokens = [generate_csrf_token() for _ in range(100)]
        assert len(set(tokens)) == 100

    def test_generate_csrf_token_is_stored(self):
        """Generated token should be stored for validation."""
        token = generate_csrf_token()
        assert token in _csrf_tokens

    def test_csrf_token_has_timestamp(self):
        """Stored token should have creation timestamp."""
        token = generate_csrf_token()
        assert isinstance(_csrf_tokens[token], datetime)


class TestCSRFTokenValidation:
    """Tests for CSRF token validation."""

    def setup_method(self):
        """Clear CSRF tokens before each test."""
        _csrf_tokens.clear()

    def test_validate_valid_token(self):
        """Valid token should pass validation."""
        token = generate_csrf_token()
        assert validate_csrf_token(token) is True

    def test_validate_invalid_token(self):
        """Invalid token should fail validation."""
        assert validate_csrf_token("invalid-token-12345") is False

    def test_validate_none_token(self):
        """None token should fail validation."""
        assert validate_csrf_token(None) is False

    def test_validate_empty_token(self):
        """Empty string token should fail validation."""
        assert validate_csrf_token("") is False

    def test_validate_expired_token(self):
        """Expired token should fail validation."""
        token = generate_csrf_token()
        # Manually expire the token
        _csrf_tokens[token] = datetime.now(UTC) - timedelta(minutes=CSRF_TOKEN_EXPIRY_MINUTES + 1)
        assert validate_csrf_token(token) is False
        # Token should be removed after failed validation
        assert token not in _csrf_tokens


# =============================================================================
# ACCOUNT LOCKOUT TESTS
# =============================================================================

class TestAccountLockout:
    """Tests for account lockout mechanism."""

    def setup_method(self):
        """Clear lockout tracker before each test."""
        _lockout_tracker.clear()

    def test_record_first_failed_login(self):
        """First failed login should increment counter."""
        failed_count, locked_until = record_failed_login(user_id=1)
        assert failed_count == 1
        assert locked_until is None

    def test_record_multiple_failed_logins(self):
        """Multiple failed logins should increment counter."""
        for i in range(1, MAX_FAILED_ATTEMPTS):
            failed_count, locked_until = record_failed_login(user_id=1)
            assert failed_count == i
            assert locked_until is None

    def test_lockout_after_max_attempts(self):
        """Account should be locked after max failed attempts."""
        for _ in range(MAX_FAILED_ATTEMPTS - 1):
            record_failed_login(user_id=1)

        # This should trigger lockout
        failed_count, locked_until = record_failed_login(user_id=1)
        assert failed_count == MAX_FAILED_ATTEMPTS
        assert locked_until is not None
        assert locked_until > datetime.now(UTC)

    def test_lockout_duration(self):
        """Lockout should last for the configured duration."""
        for _ in range(MAX_FAILED_ATTEMPTS):
            failed_count, locked_until = record_failed_login(user_id=1)

        expected_lockout = datetime.now(UTC) + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
        # Allow 1 second tolerance
        assert abs((locked_until - expected_lockout).total_seconds()) < 1


class TestCheckLockoutStatus:
    """Tests for checking lockout status."""

    def setup_method(self):
        """Clear lockout tracker before each test."""
        _lockout_tracker.clear()

    def test_no_failed_attempts(self):
        """User with no failed attempts should not be locked."""
        is_locked, locked_until, remaining = check_lockout_status(user_id=1)
        assert is_locked is False
        assert locked_until is None
        assert remaining == MAX_FAILED_ATTEMPTS

    def test_some_failed_attempts(self):
        """User with some failed attempts should show remaining."""
        record_failed_login(user_id=1)
        record_failed_login(user_id=1)

        is_locked, locked_until, remaining = check_lockout_status(user_id=1)
        assert is_locked is False
        assert locked_until is None
        assert remaining == MAX_FAILED_ATTEMPTS - 2

    def test_locked_account(self):
        """Locked account should return locked status."""
        for _ in range(MAX_FAILED_ATTEMPTS):
            record_failed_login(user_id=1)

        is_locked, locked_until, remaining = check_lockout_status(user_id=1)
        assert is_locked is True
        assert locked_until is not None
        assert remaining == 0

    def test_lockout_expires(self):
        """Lockout should expire after duration."""
        for _ in range(MAX_FAILED_ATTEMPTS):
            record_failed_login(user_id=1)

        # Manually expire the lockout
        failed_count, _ = _lockout_tracker[1]
        expired_time = datetime.now(UTC) - timedelta(minutes=1)
        _lockout_tracker[1] = (failed_count, expired_time)

        is_locked, locked_until, remaining = check_lockout_status(user_id=1)
        assert is_locked is False
        assert locked_until is None
        assert remaining == MAX_FAILED_ATTEMPTS


class TestResetFailedAttempts:
    """Tests for resetting failed attempts."""

    def setup_method(self):
        """Clear lockout tracker before each test."""
        _lockout_tracker.clear()

    def test_reset_clears_attempts(self):
        """Reset should clear all failed attempts."""
        record_failed_login(user_id=1)
        record_failed_login(user_id=1)
        reset_failed_attempts(user_id=1)

        is_locked, locked_until, remaining = check_lockout_status(user_id=1)
        assert remaining == MAX_FAILED_ATTEMPTS

    def test_reset_clears_lockout(self):
        """Reset should clear lockout status."""
        for _ in range(MAX_FAILED_ATTEMPTS):
            record_failed_login(user_id=1)

        reset_failed_attempts(user_id=1)

        is_locked, locked_until, remaining = check_lockout_status(user_id=1)
        assert is_locked is False
        assert remaining == MAX_FAILED_ATTEMPTS

    def test_reset_nonexistent_user(self):
        """Reset should not raise for nonexistent user."""
        # Should not raise
        reset_failed_attempts(user_id=999)


class TestGetLockoutInfo:
    """Tests for lockout info API response."""

    def setup_method(self):
        """Clear lockout tracker before each test."""
        _lockout_tracker.clear()

    def test_lockout_info_structure(self):
        """Lockout info should have correct structure."""
        info = get_lockout_info(user_id=1)
        assert "is_locked" in info
        assert "locked_until" in info
        assert "remaining_attempts" in info
        assert "max_attempts" in info
        assert "lockout_duration_minutes" in info

    def test_lockout_info_values(self):
        """Lockout info should have correct values."""
        record_failed_login(user_id=1)
        info = get_lockout_info(user_id=1)

        assert info["is_locked"] is False
        assert info["locked_until"] is None
        assert info["remaining_attempts"] == MAX_FAILED_ATTEMPTS - 1
        assert info["max_attempts"] == MAX_FAILED_ATTEMPTS
        assert info["lockout_duration_minutes"] == LOCKOUT_DURATION_MINUTES


# =============================================================================
# UTILITY FUNCTION TESTS
# =============================================================================

class TestUtilityFunctions:
    """Tests for security utility functions."""

    def test_hash_ip_address(self):
        """IP address should be hashed."""
        ip = "192.168.1.1"
        hashed = hash_ip_address(ip)
        assert hashed != ip
        assert len(hashed) == 16

    def test_hash_ip_is_consistent(self):
        """Same IP should produce same hash."""
        ip = "192.168.1.1"
        hash1 = hash_ip_address(ip)
        hash2 = hash_ip_address(ip)
        assert hash1 == hash2

    def test_different_ips_different_hashes(self):
        """Different IPs should produce different hashes."""
        hash1 = hash_ip_address("192.168.1.1")
        hash2 = hash_ip_address("192.168.1.2")
        assert hash1 != hash2


# =============================================================================
# INTEGRATION TESTS (with FastAPI app)
# =============================================================================

class TestSecurityHeadersIntegration:
    """Integration tests for security headers."""

    @pytest.mark.asyncio
    async def test_security_headers_present(self):
        """Security headers should be present in responses."""
        from main import app
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/")
            headers = response.headers

            assert "x-frame-options" in headers
            assert "x-content-type-options" in headers
            assert "x-xss-protection" in headers
            assert "referrer-policy" in headers
            assert "permissions-policy" in headers

    @pytest.mark.asyncio
    async def test_x_frame_options_deny(self):
        """X-Frame-Options should be DENY."""
        from main import app
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/")
            assert response.headers["x-frame-options"] == "DENY"

    @pytest.mark.asyncio
    async def test_x_content_type_options_nosniff(self):
        """X-Content-Type-Options should be nosniff."""
        from main import app
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/")
            assert response.headers["x-content-type-options"] == "nosniff"

    @pytest.mark.asyncio
    async def test_xss_protection_enabled(self):
        """X-XSS-Protection should be enabled."""
        from main import app
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/")
            assert response.headers["x-xss-protection"] == "1; mode=block"

    @pytest.mark.asyncio
    async def test_referrer_policy(self):
        """Referrer-Policy should be strict."""
        from main import app
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/")
            assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"


class TestCSRFEndpointIntegration:
    """Integration tests for CSRF token endpoint."""

    @pytest.mark.asyncio
    async def test_csrf_endpoint_returns_token(self):
        """CSRF endpoint should return token."""
        from main import app
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
    async def test_csrf_token_is_valid(self):
        """Returned CSRF token should be valid."""
        from main import app
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/auth/csrf")
            token = response.json()["csrf_token"]
            assert validate_csrf_token(token) is True


@pytest.mark.usefixtures("bypass_csrf")
class TestAccountLockoutIntegration:
    """Integration tests for account lockout in login endpoint."""

    def setup_method(self):
        """Clear lockout tracker before each test."""
        _lockout_tracker.clear()

    @pytest.mark.asyncio
    async def test_failed_login_returns_lockout_info(self):
        """Failed login should return lockout info for existing user."""
        import uuid
        from main import app

        unique_email = f"lockout_integration_{uuid.uuid4().hex[:8]}@test.com"
        password = "SecureTestPass123!"

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            # Register a user so they exist in the database
            reg_response = await client.post("/auth/register", json={
                "email": unique_email,
                "password": password,
            })
            assert reg_response.status_code == 201

            # Attempt login with wrong password
            response = await client.post("/auth/login", json={
                "email": unique_email,
                "password": "WrongPassword999!",
            })

            assert response.status_code == 401
            data = response.json()
            # Response detail should be a dict with lockout info
            assert isinstance(data["detail"], dict)
            assert "lockout" in data["detail"]

            lockout = data["detail"]["lockout"]
            assert lockout["is_locked"] is False
            assert lockout["remaining_attempts"] == MAX_FAILED_ATTEMPTS - 1
            assert lockout["max_attempts"] == MAX_FAILED_ATTEMPTS
            assert lockout["lockout_duration_minutes"] == LOCKOUT_DURATION_MINUTES

    @pytest.mark.asyncio
    async def test_nonexistent_user_no_lockout_info(self):
        """Failed login for nonexistent user should not reveal existence."""
        from main import app
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post("/auth/login", json={
                "email": "nonexistent_user_xyz@example.com",
                "password": "SomePassword123!"
            })

            assert response.status_code == 401
            data = response.json()
            # Should be simple error, not lockout info
            if isinstance(data.get("detail"), dict):
                assert "lockout" not in data["detail"]


# =============================================================================
# SPRINT 193: SECURITY_UTILS DTYPE PASSTHROUGH
# =============================================================================

class TestSecurityUtilsDtype:
    """Test dtype parameter passthrough in security_utils reading functions."""

    def test_read_csv_secure_with_dtype(self):
        """read_csv_secure should pass dtype through to pd.read_csv."""
        from security_utils import read_csv_secure
        csv_bytes = b"Account,Amount\n001,100\n002,200\n"

        # Without dtype, Account would be parsed as int (1, 2)
        df_auto = read_csv_secure(csv_bytes)
        # With dtype=str for Account, should preserve "001"
        df_typed = read_csv_secure(csv_bytes, dtype={"Account": str})

        assert df_typed["Account"].iloc[0] == "001"
        assert df_typed["Account"].iloc[1] == "002"
