"""
Tests for Sprint 49 Security Hardening.
Sprint 261: Updated for stateless HMAC CSRF + DB-backed account lockout.

Tests cover:
- Security headers middleware
- CSRF token generation and validation (stateless HMAC)
- Account lockout mechanism (DB-backed)
- Multi-worker simulation (statelessness proof)
"""

import time
from datetime import UTC, datetime, timedelta

import httpx
import pytest

# Import security middleware functions
from security_middleware import (
    CSRF_TOKEN_EXPIRY_MINUTES,
    LOCKOUT_DURATION_MINUTES,
    MAX_FAILED_ATTEMPTS,
    check_lockout_status,
    generate_csrf_token,
    get_fake_lockout_info,
    get_lockout_info,
    hash_ip_address,
    record_failed_login,
    reset_failed_attempts,
    validate_csrf_token,
)

# =============================================================================
# CSRF TOKEN TESTS (Sprint 261: Stateless HMAC)
# =============================================================================


class TestCSRFTokenGeneration:
    """Tests for CSRF token generation (stateless HMAC, user-bound)."""

    def test_generate_csrf_token_returns_string(self):
        """Token should be a non-empty string."""
        token = generate_csrf_token("test-uid")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_generate_csrf_token_is_unique(self):
        """Each generated token should be unique (different nonces)."""
        tokens = [generate_csrf_token("test-uid") for _ in range(100)]
        assert len(set(tokens)) == 100

    def test_generate_csrf_token_format(self):
        """Token should have nonce:timestamp:user_id:signature format (4 parts)."""
        token = generate_csrf_token("test-uid")
        parts = token.split(":")
        assert len(parts) == 4
        nonce, timestamp, user_id, signature = parts
        # Nonce is 16 bytes = 32 hex chars
        assert len(nonce) == 32
        int(nonce, 16)  # Should not raise
        # Timestamp is a valid integer
        int(timestamp)  # Should not raise
        # user_id matches what was passed
        assert user_id == "test-uid"
        # Signature is SHA-256 hex = 64 chars
        assert len(signature) == 64
        int(signature, 16)  # Should not raise

    def test_csrf_token_has_recent_timestamp(self):
        """Token timestamp should be within 1 second of now."""
        token = generate_csrf_token("test-uid")
        timestamp = int(token.split(":")[1])
        assert abs(time.time() - timestamp) < 2


class TestCSRFTokenValidation:
    """Tests for CSRF token validation (stateless HMAC, user-bound)."""

    def test_validate_valid_token(self):
        """Valid token should pass validation."""
        token = generate_csrf_token("test-uid")
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
        # Create a 4-part token with an old timestamp and valid CSRF_SECRET_KEY HMAC
        import hashlib
        import hmac as _hmac

        from config import CSRF_SECRET_KEY

        nonce = "a" * 32
        old_ts = str(int(time.time()) - (CSRF_TOKEN_EXPIRY_MINUTES + 1) * 60)
        payload = f"{nonce}:{old_ts}:test-uid"
        sig = _hmac.new(CSRF_SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
        expired_token = f"{nonce}:{old_ts}:test-uid:{sig}"
        assert validate_csrf_token(expired_token) is False

    def test_validate_tampered_signature(self):
        """Token with tampered signature should fail."""
        token = generate_csrf_token("test-uid")
        nonce, timestamp, uid, _sig = token.split(":")
        tampered = f"{nonce}:{timestamp}:{uid}:{'a' * 64}"
        assert validate_csrf_token(tampered) is False

    def test_validate_tampered_nonce(self):
        """Token with tampered nonce should fail (signature mismatch)."""
        token = generate_csrf_token("test-uid")
        _, timestamp, uid, signature = token.split(":")
        tampered = f"{'b' * 32}:{timestamp}:{uid}:{signature}"
        assert validate_csrf_token(tampered) is False

    def test_validate_future_timestamp(self):
        """Token with future timestamp should fail."""
        import hashlib
        import hmac as _hmac

        from config import CSRF_SECRET_KEY

        nonce = "a" * 32
        future_ts = str(int(time.time()) + 3600)
        payload = f"{nonce}:{future_ts}:test-uid"
        sig = _hmac.new(CSRF_SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()
        future_token = f"{nonce}:{future_ts}:test-uid:{sig}"
        assert validate_csrf_token(future_token) is False

    def test_validate_wrong_part_count(self):
        """Token with wrong number of parts should fail."""
        assert validate_csrf_token("onlyone") is False
        assert validate_csrf_token("two:parts") is False
        assert validate_csrf_token("three:part:token") is False
        assert validate_csrf_token("too:many:parts:here:now") is False  # 5 parts

    def test_validate_non_integer_timestamp(self):
        """Token with non-integer timestamp should fail."""
        # 4-part token with non-integer in timestamp position
        assert validate_csrf_token("abc:notanumber:uid:def") is False

    def test_stateless_multi_worker_simulation(self):
        """Token generated by one 'worker' should validate on another.

        This proves statelessness — no in-memory dict lookup needed.
        The HMAC signature is self-contained.
        """
        token = generate_csrf_token("test-uid")
        # Simulate worker switch: there's no state to clear since HMAC is stateless
        # Just verify it works without any prior generate call in this 'worker'
        assert validate_csrf_token(token) is True


# =============================================================================
# ACCOUNT LOCKOUT TESTS (Sprint 261: DB-backed)
# =============================================================================


class TestAccountLockout:
    """Tests for account lockout mechanism (DB-backed)."""

    def test_record_first_failed_login(self, db_session):
        """First failed login should increment counter."""
        user = db_session.query(__import__("models").User).first()
        if not user:
            user = _create_test_user(db_session)
        # Reset any prior state
        user.failed_login_attempts = 0
        user.locked_until = None
        db_session.commit()

        failed_count, locked_until = record_failed_login(db_session, user.id)
        assert failed_count == 1
        assert locked_until is None

    def test_record_multiple_failed_logins(self, db_session):
        """Multiple failed logins should increment counter."""
        user = _create_test_user(db_session)

        for i in range(1, MAX_FAILED_ATTEMPTS):
            failed_count, locked_until = record_failed_login(db_session, user.id)
            assert failed_count == i
            assert locked_until is None

    def test_lockout_after_max_attempts(self, db_session):
        """Account should be locked after max failed attempts."""
        user = _create_test_user(db_session)

        for _ in range(MAX_FAILED_ATTEMPTS - 1):
            record_failed_login(db_session, user.id)

        # This should trigger lockout
        failed_count, locked_until = record_failed_login(db_session, user.id)
        assert failed_count == MAX_FAILED_ATTEMPTS
        assert locked_until is not None
        # Compare as naive datetimes (SQLite strips tzinfo)
        locked_naive = locked_until.replace(tzinfo=None) if locked_until.tzinfo else locked_until
        now_naive = datetime.now(UTC).replace(tzinfo=None)
        assert locked_naive > now_naive

    def test_lockout_duration(self, db_session):
        """Lockout should last for the configured duration."""
        user = _create_test_user(db_session)

        for _ in range(MAX_FAILED_ATTEMPTS):
            failed_count, locked_until = record_failed_login(db_session, user.id)

        expected_lockout = datetime.now(UTC)
        # Allow 2 second tolerance (locked_until is tz-aware, compare carefully)
        locked_naive = locked_until.replace(tzinfo=None) if locked_until.tzinfo else locked_until
        expected_naive = expected_lockout.replace(tzinfo=None) + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
        assert abs((locked_naive - expected_naive).total_seconds()) < 2


class TestCheckLockoutStatus:
    """Tests for checking lockout status (DB-backed)."""

    def test_no_failed_attempts(self, db_session):
        """User with no failed attempts should not be locked."""
        user = _create_test_user(db_session)
        is_locked, locked_until, remaining = check_lockout_status(db_session, user.id)
        assert is_locked is False
        assert locked_until is None
        assert remaining == MAX_FAILED_ATTEMPTS

    def test_some_failed_attempts(self, db_session):
        """User with some failed attempts should show remaining."""
        user = _create_test_user(db_session)
        record_failed_login(db_session, user.id)
        record_failed_login(db_session, user.id)

        is_locked, locked_until, remaining = check_lockout_status(db_session, user.id)
        assert is_locked is False
        assert locked_until is None
        assert remaining == MAX_FAILED_ATTEMPTS - 2

    def test_locked_account(self, db_session):
        """Locked account should return locked status."""
        user = _create_test_user(db_session)
        for _ in range(MAX_FAILED_ATTEMPTS):
            record_failed_login(db_session, user.id)

        is_locked, locked_until, remaining = check_lockout_status(db_session, user.id)
        assert is_locked is True
        assert locked_until is not None
        assert remaining == 0

    def test_lockout_expires(self, db_session):
        """Lockout should expire after duration."""
        user = _create_test_user(db_session)
        for _ in range(MAX_FAILED_ATTEMPTS):
            record_failed_login(db_session, user.id)

        # Manually expire the lockout
        expired_time = datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=1)
        user.locked_until = expired_time
        db_session.commit()

        is_locked, locked_until, remaining = check_lockout_status(db_session, user.id)
        assert is_locked is False
        assert locked_until is None
        assert remaining == MAX_FAILED_ATTEMPTS

    def test_nonexistent_user(self, db_session):
        """Checking lockout for non-existent user should return clean state."""
        is_locked, locked_until, remaining = check_lockout_status(db_session, 999999)
        assert is_locked is False
        assert locked_until is None
        assert remaining == MAX_FAILED_ATTEMPTS


class TestResetFailedAttempts:
    """Tests for resetting failed attempts (DB-backed)."""

    def test_reset_clears_attempts(self, db_session):
        """Reset should clear all failed attempts."""
        user = _create_test_user(db_session)
        record_failed_login(db_session, user.id)
        record_failed_login(db_session, user.id)
        reset_failed_attempts(db_session, user.id)

        is_locked, locked_until, remaining = check_lockout_status(db_session, user.id)
        assert remaining == MAX_FAILED_ATTEMPTS

    def test_reset_clears_lockout(self, db_session):
        """Reset should clear lockout status."""
        user = _create_test_user(db_session)
        for _ in range(MAX_FAILED_ATTEMPTS):
            record_failed_login(db_session, user.id)

        reset_failed_attempts(db_session, user.id)

        is_locked, locked_until, remaining = check_lockout_status(db_session, user.id)
        assert is_locked is False
        assert remaining == MAX_FAILED_ATTEMPTS

    def test_reset_nonexistent_user(self, db_session):
        """Reset should not raise for nonexistent user."""
        reset_failed_attempts(db_session, 999999)  # Should not raise

    def test_lockout_persists_across_sessions(self, db_session):
        """Lockout state should persist across DB sessions (multi-worker proof)."""
        user = _create_test_user(db_session)
        record_failed_login(db_session, user.id)
        record_failed_login(db_session, user.id)
        record_failed_login(db_session, user.id)

        # Simulate different worker by expunging cached objects
        db_session.expire_all()

        is_locked, _, remaining = check_lockout_status(db_session, user.id)
        assert remaining == MAX_FAILED_ATTEMPTS - 3


class TestGetLockoutInfo:
    """Tests for lockout info API response (DB-backed)."""

    def test_lockout_info_structure(self, db_session):
        """Lockout info should have correct structure."""
        user = _create_test_user(db_session)
        info = get_lockout_info(db_session, user.id)
        assert "is_locked" in info
        assert "locked_until" in info
        assert "remaining_attempts" in info
        assert "max_attempts" in info
        assert "lockout_duration_minutes" in info

    def test_lockout_info_values(self, db_session):
        """Lockout info should have correct values."""
        user = _create_test_user(db_session)
        record_failed_login(db_session, user.id)
        info = get_lockout_info(db_session, user.id)

        assert info["is_locked"] is False
        assert info["locked_until"] is None
        assert info["remaining_attempts"] == MAX_FAILED_ATTEMPTS - 1
        assert info["max_attempts"] == MAX_FAILED_ATTEMPTS
        assert info["lockout_duration_minutes"] == LOCKOUT_DURATION_MINUTES


class TestGetFakeLockoutInfo:
    """Tests for fake lockout info (account enumeration prevention)."""

    def test_fake_lockout_info_structure(self):
        """Fake lockout info should have the same structure as real."""
        fake = get_fake_lockout_info()
        assert "is_locked" in fake
        assert "locked_until" in fake
        assert "remaining_attempts" in fake
        assert "max_attempts" in fake
        assert "lockout_duration_minutes" in fake

    def test_fake_matches_real_first_failure(self, db_session):
        """Fake lockout info should match real info after first failure."""
        fake = get_fake_lockout_info()
        user = _create_test_user(db_session)
        record_failed_login(db_session, user.id)
        real = get_lockout_info(db_session, user.id)

        assert fake["is_locked"] == real["is_locked"]
        assert fake["locked_until"] == real["locked_until"]
        assert fake["remaining_attempts"] == real["remaining_attempts"]
        assert fake["max_attempts"] == real["max_attempts"]
        assert fake["lockout_duration_minutes"] == real["lockout_duration_minutes"]


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

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
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

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/")
            assert response.headers["x-frame-options"] == "DENY"

    @pytest.mark.asyncio
    async def test_x_content_type_options_nosniff(self):
        """X-Content-Type-Options should be nosniff."""
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/")
            assert response.headers["x-content-type-options"] == "nosniff"

    @pytest.mark.asyncio
    async def test_xss_protection_enabled(self):
        """X-XSS-Protection should be enabled."""
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/")
            assert response.headers["x-xss-protection"] == "1; mode=block"

    @pytest.mark.asyncio
    async def test_referrer_policy(self):
        """Referrer-Policy should be strict."""
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/")
            assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"


class TestCSRFEndpointIntegration:
    """Integration tests for CSRF token endpoint (requires authentication)."""

    @pytest.mark.asyncio
    async def test_csrf_endpoint_requires_auth(self):
        """CSRF endpoint must return 401 when no auth provided."""
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/auth/csrf")
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_csrf_endpoint_returns_token_when_authenticated(self):
        """CSRF endpoint returns token + expires_in_minutes when authenticated."""
        from auth import hash_password, require_current_user
        from main import app
        from models import User, UserTier

        # Override require_current_user with a synthetic user
        fake_user = User(
            id=9999,
            email="csrf_integration@example.com",
            hashed_password=hash_password("Irrelevant1!"),
            tier=UserTier.TEAM,
            is_active=True,
            is_verified=True,
        )
        app.dependency_overrides[require_current_user] = lambda: fake_user
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/auth/csrf")
                assert response.status_code == 200
                data = response.json()
                assert "csrf_token" in data
                assert "expires_in_minutes" in data
                assert data["expires_in_minutes"] == 30
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_csrf_token_is_valid_when_authenticated(self):
        """Returned CSRF token must pass validate_csrf_token."""
        from auth import hash_password, require_current_user
        from main import app
        from models import User, UserTier

        fake_user = User(
            id=9998,
            email="csrf_valid@example.com",
            hashed_password=hash_password("Irrelevant1!"),
            tier=UserTier.TEAM,
            is_active=True,
            is_verified=True,
        )
        app.dependency_overrides[require_current_user] = lambda: fake_user
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/auth/csrf")
                token = response.json()["csrf_token"]
                assert validate_csrf_token(token) is True
        finally:
            app.dependency_overrides.clear()


@pytest.mark.usefixtures("bypass_csrf")
class TestAccountLockoutIntegration:
    """Integration tests for account lockout in login endpoint."""

    @pytest.mark.asyncio
    async def test_failed_login_returns_lockout_info(self):
        """Failed login should return lockout info for existing user."""
        import uuid

        from main import app

        unique_email = f"lockout_integration_{uuid.uuid4().hex[:8]}@test.com"
        password = "SecureTestPass123!"

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            # Register a user so they exist in the database
            reg_response = await client.post(
                "/auth/register",
                json={
                    "email": unique_email,
                    "password": password,
                },
            )
            assert reg_response.status_code == 201

            # Attempt login with wrong password
            response = await client.post(
                "/auth/login",
                json={
                    "email": unique_email,
                    "password": "WrongPassword999!",
                },
            )

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
    async def test_nonexistent_user_returns_same_shape(self):
        """Failed login for nonexistent user should return same response shape.

        Sprint 261: Prevents account enumeration through response structure.
        """
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/auth/login", json={"email": "nonexistent_user_xyz@example.com", "password": "SomePassword123!"}
            )

            assert response.status_code == 401
            data = response.json()
            # Sprint 261: Should have the SAME structure as existing user
            assert isinstance(data["detail"], dict)
            assert "lockout" in data["detail"]
            lockout = data["detail"]["lockout"]
            assert lockout["is_locked"] is False
            assert lockout["remaining_attempts"] == MAX_FAILED_ATTEMPTS - 1
            assert lockout["max_attempts"] == MAX_FAILED_ATTEMPTS


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


# =============================================================================
# HELPERS
# =============================================================================

_test_user_counter = 0


def _create_test_user(db_session):
    """Create a fresh test user for lockout tests."""
    global _test_user_counter
    _test_user_counter += 1
    from models import User

    user = User(
        email=f"lockout_test_{_test_user_counter}_{time.time_ns()}@test.com",
        hashed_password="$2b$12$fakehashfakehashfakehashfakehashfakehashfakehashfakeh",
        is_active=True,
        is_verified=True,
        failed_login_attempts=0,
        locked_until=None,
    )
    db_session.add(user)
    db_session.commit()
    return user
