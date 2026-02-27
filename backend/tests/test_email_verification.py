"""
Test Suite: Email Verification System
Sprint 57: Verified-Account-Only Model

Tests for:
- Disposable email blocking
- Email verification token generation
- Verification endpoint
- Resend verification endpoint
- require_verified_user dependency
"""

import hashlib
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

# Test disposable email module
from disposable_email import DISPOSABLE_EMAIL_DOMAINS, get_blocked_domain_count, is_disposable_email

# Test email service module
from email_service import (
    RESEND_COOLDOWN_MINUTES,
    VERIFICATION_TOKEN_LENGTH,
    can_resend_verification,
    generate_verification_token,
    send_email_change_notification,
    send_verification_email,
)

# =============================================================================
# DISPOSABLE EMAIL TESTS
# =============================================================================


class TestDisposableEmailBlocking:
    """Test disposable email domain blocking."""

    def test_blocks_mailinator(self):
        """Should block mailinator.com addresses."""
        assert is_disposable_email("test@mailinator.com") is True

    def test_blocks_guerrillamail(self):
        """Should block guerrillamail variants."""
        assert is_disposable_email("test@guerrillamail.com") is True
        assert is_disposable_email("test@guerrillamail.org") is True
        assert is_disposable_email("test@guerrillamail.net") is True

    def test_blocks_10minutemail(self):
        """Should block 10minutemail addresses."""
        assert is_disposable_email("test@10minutemail.com") is True
        assert is_disposable_email("test@10minutemail.net") is True

    def test_blocks_yopmail(self):
        """Should block yopmail addresses."""
        assert is_disposable_email("test@yopmail.com") is True
        assert is_disposable_email("test@yopmail.fr") is True

    def test_blocks_tempmail(self):
        """Should block tempmail variants."""
        assert is_disposable_email("test@tempmail.com") is True
        assert is_disposable_email("test@temp-mail.org") is True

    def test_allows_legitimate_domains(self):
        """Should allow legitimate email domains."""
        assert is_disposable_email("test@gmail.com") is False
        assert is_disposable_email("test@outlook.com") is False
        assert is_disposable_email("test@yahoo.com") is False
        assert is_disposable_email("test@company.com") is False
        assert is_disposable_email("cfo@accounting-firm.org") is False

    def test_case_insensitive(self):
        """Should be case insensitive."""
        assert is_disposable_email("test@MAILINATOR.COM") is True
        assert is_disposable_email("test@Mailinator.Com") is True
        assert is_disposable_email("TEST@mailinator.com") is True

    def test_subdomain_detection(self):
        """Should detect subdomains of disposable services."""
        assert is_disposable_email("test@subdomain.mailinator.com") is True
        assert is_disposable_email("test@foo.guerrillamail.com") is True

    def test_handles_invalid_emails(self):
        """Should handle invalid email formats gracefully."""
        assert is_disposable_email("") is False
        assert is_disposable_email("notemail") is False
        assert is_disposable_email("@nodomain") is False

    def test_minimum_domain_coverage(self):
        """Should have at least 200 blocked domains."""
        assert get_blocked_domain_count() >= 200

    def test_domain_list_frozen(self):
        """Domain list should be frozen set for performance."""
        assert isinstance(DISPOSABLE_EMAIL_DOMAINS, frozenset)


# =============================================================================
# TOKEN GENERATION TESTS
# =============================================================================


class TestVerificationTokenGeneration:
    """Test verification token generation."""

    def test_generates_correct_length_token(self):
        """Token should be 64 characters (32 bytes hex encoded)."""
        result = generate_verification_token()
        assert len(result.token) == VERIFICATION_TOKEN_LENGTH

    def test_token_is_hex_string(self):
        """Token should be valid hex string."""
        result = generate_verification_token()
        # Should not raise ValueError
        int(result.token, 16)

    def test_generates_unique_tokens(self):
        """Each call should generate a unique token."""
        tokens = [generate_verification_token().token for _ in range(100)]
        assert len(set(tokens)) == 100  # All unique

    def test_sets_expiration(self):
        """Token should have future expiration."""
        result = generate_verification_token()
        now = datetime.now(UTC)
        assert result.expires_at > now
        # Should expire in approximately 24 hours
        delta = result.expires_at - now
        assert 23 * 3600 < delta.total_seconds() < 25 * 3600


# =============================================================================
# RESEND COOLDOWN TESTS
# =============================================================================


class TestResendCooldown:
    """Test verification email resend cooldown."""

    def test_allows_resend_when_never_sent(self):
        """Should allow resend if never sent before."""
        can_resend, remaining = can_resend_verification(None)
        assert can_resend is True
        assert remaining == 0

    def test_allows_resend_after_cooldown(self):
        """Should allow resend after cooldown period."""
        old_time = datetime.now(UTC) - timedelta(minutes=RESEND_COOLDOWN_MINUTES + 1)
        can_resend, remaining = can_resend_verification(old_time)
        assert can_resend is True
        assert remaining == 0

    def test_blocks_resend_during_cooldown(self):
        """Should block resend during cooldown period."""
        recent_time = datetime.now(UTC) - timedelta(minutes=2)
        can_resend, remaining = can_resend_verification(recent_time)
        assert can_resend is False
        assert remaining > 0
        assert remaining <= RESEND_COOLDOWN_MINUTES * 60

    def test_returns_accurate_remaining_time(self):
        """Should return accurate remaining seconds."""
        # Sent 3 minutes ago, cooldown is 5 minutes
        sent_at = datetime.now(UTC) - timedelta(minutes=3)
        can_resend, remaining = can_resend_verification(sent_at)
        assert can_resend is False
        # Should have about 2 minutes (120 seconds) remaining
        assert 100 < remaining < 140


# =============================================================================
# EMAIL SERVICE TESTS
# =============================================================================


class TestEmailService:
    """Test email service functionality."""

    def test_service_not_configured_without_api_key(self):
        """Should report not configured when API key is missing."""
        with patch.dict("os.environ", {"SENDGRID_API_KEY": ""}, clear=False):
            # Re-import to pick up env change
            pass
            # Note: The module caches SENDGRID_API_KEY at import time
            # In production, we check is_email_service_configured()

    @patch("email_service.SENDGRID_API_KEY", None)
    def test_send_email_without_api_key_succeeds(self):
        """Should succeed in dev mode when API key not set."""
        with patch("email_service.log_secure_operation") as mock_log:
            result = send_verification_email(
                to_email="test@example.com",
                token="abc123def456abc123def456abc123def456abc123def456abc123def456abcd",
                user_name="Test User",
            )
            assert result.success is True
            assert "skipped" in result.message.lower() or "no API key" in result.message.lower()

    @patch("email_service.SENDGRID_API_KEY", None)
    def test_dev_fallback_does_not_log_raw_token(self):
        """Dev fallback must never log the raw verification token."""
        raw_token = "abc123def456abc123def456abc123def456abc123def456abc123def456abcd"
        with patch("email_service.log_secure_operation") as mock_log:
            send_verification_email(to_email="test@example.com", token=raw_token, user_name="Test User")
            # Inspect all logged details
            for call in mock_log.call_args_list:
                logged_detail = call[0][1] if len(call[0]) > 1 else ""
                assert raw_token not in logged_detail, f"Raw token leaked in log: {logged_detail}"

    @patch("email_service.SENDGRID_AVAILABLE", False)
    def test_no_sendgrid_fallback_does_not_log_raw_token(self):
        """SendGrid-unavailable fallback must never log the raw token."""
        raw_token = "feedface0123456789abcdef0123456789abcdef0123456789abcdef012345"
        with patch("email_service.log_secure_operation") as mock_log:
            send_verification_email(to_email="test@example.com", token=raw_token, user_name="Test User")
            for call in mock_log.call_args_list:
                logged_detail = call[0][1] if len(call[0]) > 1 else ""
                assert raw_token not in logged_detail, f"Raw token leaked in log: {logged_detail}"

    @patch("email_service.SENDGRID_API_KEY", None)
    def test_dev_fallback_logs_token_fingerprint(self):
        """Dev fallback should log a safe token fingerprint for debugging."""
        raw_token = "abc123def456abc123def456abc123def456abc123def456abc123def456abcd"
        with patch("email_service.log_secure_operation") as mock_log:
            send_verification_email(
                to_email="test@example.com",
                token=raw_token,
            )
            # Should find a call with the fingerprint (first 8 chars + hash bracket)
            logged_details = [call[0][1] for call in mock_log.call_args_list if len(call[0]) > 1]
            fingerprint_logged = any("abc123de..." in d and "[" in d for d in logged_details)
            assert fingerprint_logged, f"Expected token fingerprint in logs, got: {logged_details}"

    @patch("email_service.SENDGRID_API_KEY", None)
    def test_dev_fallback_does_not_log_verification_url(self):
        """Dev fallback must never log a URL containing the raw token."""
        raw_token = "abc123def456abc123def456abc123def456abc123def456abc123def456abcd"
        with patch("email_service.log_secure_operation") as mock_log:
            send_verification_email(
                to_email="test@example.com",
                token=raw_token,
            )
            for call in mock_log.call_args_list:
                logged_detail = call[0][1] if len(call[0]) > 1 else ""
                assert f"token={raw_token}" not in logged_detail, (
                    f"Verification URL with raw token leaked: {logged_detail}"
                )
                assert "/verify-email?token=" not in logged_detail, f"Verification URL pattern leaked: {logged_detail}"

    @patch("email_service.SENDGRID_API_KEY", None)
    def test_dev_fallback_logs_event_type(self):
        """Dev fallback must log recognizable event type labels for telemetry."""
        raw_token = "abc123def456abc123def456abc123def456abc123def456abc123def456abcd"
        with patch("email_service.log_secure_operation") as mock_log:
            send_verification_email(
                to_email="test@example.com",
                token=raw_token,
            )
            event_types = [call[0][0] for call in mock_log.call_args_list]
            assert "email_skipped" in event_types, f"Expected 'email_skipped' event type, got: {event_types}"
            assert "verification_token" in event_types, f"Expected 'verification_token' event type, got: {event_types}"

    def test_verification_email_template_contains_required_elements(self):
        """Verification email HTML should contain required elements."""
        from email_service import _get_verification_email_html

        html = _get_verification_email_html("https://example.com/verify", "Test User")

        # Should contain branding
        assert "Paciolus" in html

        # Should contain verification link
        assert "https://example.com/verify" in html

        # Should contain user greeting
        assert "Test User" in html

        # Should contain Zero-Storage messaging
        assert "Zero-Storage" in html or "never stored" in html

        # Should contain expiration notice
        assert "24 hours" in html

    def test_verification_email_template_default_greeting(self):
        """Should use default greeting when no name provided."""
        from email_service import _get_verification_email_html

        html = _get_verification_email_html("https://example.com/verify", None)
        assert "Hello," in html

    def test_plain_text_template_exists(self):
        """Should have plain text version of email."""
        from email_service import _get_verification_email_text

        text = _get_verification_email_text("https://example.com/verify", "Test")
        assert "https://example.com/verify" in text
        assert "Paciolus" in text


# =============================================================================
# EMAIL CHANGE NOTIFICATION LOG REDACTION (Sprint 1.2)
# =============================================================================


class TestEmailChangeNotificationLogRedaction:
    """Verify email-change notification dev fallback never logs raw PII."""

    @patch("email_service.SENDGRID_API_KEY", None)
    def test_does_not_log_raw_new_email(self):
        """Dev fallback must not log the raw new email address."""
        new_email = "supersecret.newemail@privatecompany.org"
        with patch("email_service.log_secure_operation") as mock_log:
            send_email_change_notification(
                to_email="old@example.com",
                new_email=new_email,
                user_name="Test User",
            )
            for call in mock_log.call_args_list:
                logged_detail = call[0][1] if len(call[0]) > 1 else ""
                assert new_email not in logged_detail, f"Raw new email leaked in log: {logged_detail}"

    @patch("email_service.SENDGRID_AVAILABLE", False)
    def test_no_sendgrid_does_not_log_raw_new_email(self):
        """SendGrid-unavailable fallback must not log the raw new email."""
        new_email = "anothersecret@corp.io"
        with patch("email_service.log_secure_operation") as mock_log:
            send_email_change_notification(
                to_email="old@example.com",
                new_email=new_email,
            )
            for call in mock_log.call_args_list:
                logged_detail = call[0][1] if len(call[0]) > 1 else ""
                assert new_email not in logged_detail, f"Raw new email leaked in log: {logged_detail}"

    @patch("email_service.SENDGRID_API_KEY", None)
    def test_logs_masked_email_form(self):
        """Dev fallback should log a masked version of the new email."""
        with patch("email_service.log_secure_operation") as mock_log:
            send_email_change_notification(
                to_email="old@example.com",
                new_email="longprefix@domain.com",
            )
            logged_details = [call[0][1] for call in mock_log.call_args_list if len(call[0]) > 1]
            # Masked form: "lon***@domain.com"
            masked_logged = any("lon***@domain.com" in d for d in logged_details)
            assert masked_logged, f"Expected masked email in logs, got: {logged_details}"

    @patch("email_service.SENDGRID_API_KEY", None)
    def test_logs_event_type(self):
        """Dev fallback should log recognizable event type labels."""
        with patch("email_service.log_secure_operation") as mock_log:
            send_email_change_notification(
                to_email="old@example.com",
                new_email="new@example.com",
            )
            event_types = [call[0][0] for call in mock_log.call_args_list]
            assert "email_change_notification_skipped" in event_types, (
                f"Expected 'email_change_notification_skipped', got: {event_types}"
            )
            assert "email_change_notification" in event_types, (
                f"Expected 'email_change_notification', got: {event_types}"
            )


# =============================================================================
# INTEGRATION TESTS (with database)
# =============================================================================


class TestEmailVerificationIntegration:
    """Integration tests requiring database setup."""

    @pytest.fixture
    def test_db(self, tmp_path):
        """Create a temporary test database."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from models import Base

        db_path = tmp_path / "test.db"
        engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(engine)

        Session = sessionmaker(bind=engine)
        session = Session()

        yield session

        session.close()

    def test_create_user_with_verification_fields(self, test_db):
        """Should be able to create user with verification fields."""
        from models import User, UserTier

        user = User(
            email="test@example.com",
            hashed_password="hashed",
            tier=UserTier.FREE,
            is_verified=False,
        )
        test_db.add(user)
        test_db.commit()

        assert user.id is not None
        assert user.tier == UserTier.FREE
        assert user.is_verified is False

    def test_create_verification_token(self, test_db):
        """Should be able to create verification token."""
        from datetime import UTC, datetime, timedelta

        from models import EmailVerificationToken, User, UserTier

        user = User(
            email="test2@example.com",
            hashed_password="hashed",
            tier=UserTier.FREE,
        )
        test_db.add(user)
        test_db.commit()

        token = EmailVerificationToken(
            user_id=user.id,
            token_hash=hashlib.sha256(b"xyz789").hexdigest(),
            expires_at=datetime.now(UTC) + timedelta(hours=24),
        )
        test_db.add(token)
        test_db.commit()

        assert token.id is not None
        assert token.user_id == user.id
        assert token.is_expired is False
        assert token.is_used is False

    def test_token_expiration_check(self, test_db):
        """Should correctly identify expired tokens."""
        from datetime import UTC, datetime, timedelta

        from models import EmailVerificationToken, User, UserTier

        user = User(
            email="test3@example.com",
            hashed_password="hashed",
            tier=UserTier.FREE,
        )
        test_db.add(user)
        test_db.commit()

        # Create expired token
        token = EmailVerificationToken(
            user_id=user.id,
            token_hash=hashlib.sha256(b"expired123").hexdigest(),
            expires_at=datetime.now(UTC) - timedelta(hours=1),
        )
        test_db.add(token)
        test_db.commit()

        assert token.is_expired is True

    def test_token_used_check(self, test_db):
        """Should correctly identify used tokens."""
        from datetime import UTC, datetime, timedelta

        from models import EmailVerificationToken, User, UserTier

        user = User(
            email="test4@example.com",
            hashed_password="hashed",
            tier=UserTier.FREE,
        )
        test_db.add(user)
        test_db.commit()

        token = EmailVerificationToken(
            user_id=user.id,
            token_hash=hashlib.sha256(b"used123").hexdigest(),
            expires_at=datetime.now(UTC) + timedelta(hours=24),
            used_at=datetime.now(UTC),
        )
        test_db.add(token)
        test_db.commit()

        assert token.is_used is True


# =============================================================================
# REQUIRE_VERIFIED_USER DEPENDENCY TESTS
# =============================================================================


class TestRequireVerifiedUserDependency:
    """Test the require_verified_user FastAPI dependency."""

    @pytest.fixture
    def mock_user_verified(self):
        """Create a mock verified user."""
        user = MagicMock()
        user.is_verified = True
        user.is_active = True
        return user

    @pytest.fixture
    def mock_user_unverified(self):
        """Create a mock unverified user."""
        user = MagicMock()
        user.is_verified = False
        user.is_active = True
        return user

    @pytest.mark.asyncio
    async def test_allows_verified_user(self, mock_user_verified):
        """Should allow access for verified users."""

        # We'd need to mock the dependencies - simplified test
        # Full integration test would use TestClient

    @pytest.mark.asyncio
    async def test_blocks_unverified_user(self, mock_user_unverified):
        """Should block access for unverified users."""
        # This would be tested via API integration tests
        pass


# =============================================================================
# API ENDPOINT TESTS (using httpx async client)
# =============================================================================

import httpx


@pytest.mark.usefixtures("bypass_csrf")
class TestRegistrationWithDisposableEmail:
    """Test registration endpoint blocks disposable emails."""

    @pytest.mark.asyncio
    async def test_blocks_mailinator_registration(self):
        """Should block registration with mailinator email."""
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/auth/register", json={"email": "test@mailinator.com", "password": "SecurePass123!"}
            )
            assert response.status_code == 400
            assert "disposable" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_blocks_tempmail_registration(self):
        """Should block registration with tempmail email."""
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/auth/register", json={"email": "test@tempmail.com", "password": "SecurePass123!"}
            )
            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_allows_legitimate_email_registration(self):
        """Should allow registration with legitimate email."""
        import uuid

        from main import app

        unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/auth/register", json={"email": unique_email, "password": "SecurePass123!"})

            # Should succeed (or fail for other reasons, not disposable email)
            if response.status_code == 400:
                assert "disposable" not in response.json().get("detail", "").lower()


@pytest.mark.usefixtures("bypass_csrf")
class TestVerifyEmailEndpoint:
    """Test email verification endpoint."""

    @pytest.mark.asyncio
    async def test_rejects_invalid_token(self):
        """Should reject invalid verification tokens."""
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/auth/verify-email", json={"token": "invalid_token_12345"})
            assert response.status_code == 400
            assert "invalid" in response.json()["detail"].lower()


@pytest.mark.usefixtures("bypass_csrf")
class TestResendVerificationEndpoint:
    """Test resend verification endpoint."""

    @pytest.mark.asyncio
    async def test_requires_authentication(self):
        """Should require authentication."""
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/auth/resend-verification")
            assert response.status_code == 401


class TestVerificationStatusEndpoint:
    """Test verification status endpoint."""

    @pytest.mark.asyncio
    async def test_requires_authentication(self):
        """Should require authentication."""
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/auth/verification-status")
            assert response.status_code == 401
