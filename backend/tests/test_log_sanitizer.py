"""
Test Suite: Shared Log Sanitizer — Sprint 300

Tests for:
- token_fingerprint(): 8-char prefix + SHA-256 hash, never full token
- mask_email(): consistent masking for various email formats
- sanitize_exception(): strips raw message, returns class name only
- Integration: exception handlers never leak PII in logs or API responses
"""

from unittest.mock import patch

import pytest

from shared.log_sanitizer import mask_email, sanitize_exception, token_fingerprint


# =============================================================================
# token_fingerprint()
# =============================================================================

class TestTokenFingerprint:
    """Unit tests for token_fingerprint()."""

    def test_returns_8_char_prefix_plus_hash(self):
        """Should return first 8 chars + SHA-256 hash prefix in brackets."""
        token = "abc12345def67890abc12345def67890abc12345def67890abc12345def67890"
        result = token_fingerprint(token)
        assert result.startswith("abc12345...")
        assert "[" in result and "]" in result
        # Hash bracket should contain 8 hex chars
        hash_part = result.split("[")[1].rstrip("]")
        assert len(hash_part) == 8
        int(hash_part, 16)  # Should be valid hex

    def test_never_contains_full_token(self):
        """Result must never contain the full token string."""
        token = "abc12345def67890abc12345def67890abc12345def67890abc12345def67890"
        result = token_fingerprint(token)
        assert token not in result

    def test_short_token_returns_stars(self):
        """Tokens <= 8 chars should return '***' for safety."""
        assert token_fingerprint("short") == "***"
        assert token_fingerprint("12345678") == "***"

    def test_9_char_token_returns_fingerprint(self):
        """A 9-char token should produce a fingerprint (just over threshold)."""
        result = token_fingerprint("123456789")
        assert result.startswith("12345678...")
        assert "[" in result

    def test_deterministic(self):
        """Same token should always produce the same fingerprint."""
        token = "abc12345def67890abc12345def67890"
        assert token_fingerprint(token) == token_fingerprint(token)

    def test_different_tokens_produce_different_hashes(self):
        """Different tokens should produce different hash prefixes."""
        r1 = token_fingerprint("aaaaaaaabbbbbbbbccccccccdddddddd")
        r2 = token_fingerprint("eeeeeeeeffffffffgggggggghhhhhhhh")
        hash1 = r1.split("[")[1].rstrip("]")
        hash2 = r2.split("[")[1].rstrip("]")
        assert hash1 != hash2


# =============================================================================
# mask_email()
# =============================================================================

class TestMaskEmail:
    """Unit tests for mask_email()."""

    def test_standard_email(self):
        """Should mask local part, preserving first 3 chars + domain."""
        assert mask_email("john.doe@example.com") == "joh***@example.com"

    def test_short_local_part(self):
        """Short local parts (<=3 chars) should return full mask."""
        assert mask_email("ab@example.com") == "***@***"
        assert mask_email("abc@example.com") == "***@***"

    def test_exactly_4_char_local(self):
        """4-char local part should show first 3 chars masked."""
        assert mask_email("abcd@example.com") == "abc***@example.com"

    def test_no_at_sign(self):
        """Malformed input without @ should return full mask."""
        assert mask_email("noemail") == "***@***"

    def test_empty_string(self):
        """Empty string should return full mask."""
        assert mask_email("") == "***@***"

    def test_preserves_domain(self):
        """Domain part should always be visible."""
        assert mask_email("longusername@corporate.co.uk") == "lon***@corporate.co.uk"

    def test_never_exposes_full_local_part(self):
        """Result should never contain the full local part."""
        email = "sensitiveuser@domain.com"
        result = mask_email(email)
        assert "sensitiveuser" not in result


# =============================================================================
# sanitize_exception()
# =============================================================================

class TestSanitizeException:
    """Unit tests for sanitize_exception()."""

    def test_returns_class_name(self):
        """Should include the exception class name."""
        e = OSError("Connection refused to smtp.sendgrid.net")
        result = sanitize_exception(e)
        assert "OSError" in result

    def test_strips_raw_message(self):
        """Must not contain the raw exception message."""
        e = ValueError("Invalid API key: SG.abcdef123456.xyz789")
        result = sanitize_exception(e)
        assert "SG.abcdef123456" not in result
        assert "Invalid API key" not in result

    def test_runtime_error(self):
        """RuntimeError should show class name, not message."""
        e = RuntimeError("Failed to deliver to user@secret.com")
        result = sanitize_exception(e)
        assert "RuntimeError" in result
        assert "user@secret.com" not in result

    def test_generic_message(self):
        """Should contain a generic safe message."""
        e = OSError("anything")
        result = sanitize_exception(e)
        assert "email delivery failed" in result

    def test_exception_with_email_in_message(self):
        """Exception messages containing emails must not leak them."""
        e = OSError("550 5.1.1 <admin@privatecompany.org>: Recipient address rejected")
        result = sanitize_exception(e)
        assert "admin@privatecompany.org" not in result

    def test_exception_with_api_key_in_message(self):
        """Exception messages containing API keys must not leak them."""
        e = ValueError("Unauthorized: Bearer SG.xyztoken123.secret456")
        result = sanitize_exception(e)
        assert "SG.xyztoken123" not in result
        assert "secret456" not in result


# =============================================================================
# INTEGRATION: email_service exception handlers don't leak PII
# =============================================================================

class TestEmailServiceExceptionSanitization:
    """Integration tests verifying exception handlers use sanitize_exception."""

    @patch('email_service.SENDGRID_API_KEY', 'fake-key')
    @patch('email_service.SENDGRID_AVAILABLE', True)
    def test_verification_email_exception_does_not_leak_in_log(self):
        """SendGrid exception in send_verification_email must not leak raw error."""
        from email_service import send_verification_email

        pii_message = "550 <secret@private.org> rejected"
        with patch('email_service.SendGridAPIClient') as mock_sg:
            mock_sg.return_value.send.side_effect = OSError(pii_message)
            with patch('email_service.log_secure_operation') as mock_log:
                result = send_verification_email(
                    to_email="test@example.com",
                    token="a" * 64,
                )
                assert result.success is False
                # API response must not contain raw error
                assert pii_message not in result.message
                assert "secret@private.org" not in result.message
                # Logs must not contain raw error
                for call in mock_log.call_args_list:
                    detail = call[0][1] if len(call[0]) > 1 else ""
                    assert pii_message not in detail
                    assert "secret@private.org" not in detail

    @patch('email_service.SENDGRID_API_KEY', 'fake-key')
    @patch('email_service.SENDGRID_AVAILABLE', True)
    def test_contact_email_exception_does_not_leak_in_log(self):
        """SendGrid exception in send_contact_form_email must not leak raw error."""
        from email_service import send_contact_form_email

        pii_message = "Unauthorized: key=SG.leaked_api_key_here"
        with patch('email_service.SendGridAPIClient') as mock_sg:
            mock_sg.return_value.send.side_effect = ValueError(pii_message)
            with patch('email_service.log_secure_operation') as mock_log:
                result = send_contact_form_email(
                    name="Test",
                    email="test@example.com",
                    company="",
                    inquiry_type="General",
                    message="A long enough message for testing.",
                )
                assert result.success is False
                assert "SG.leaked_api_key_here" not in result.message
                for call in mock_log.call_args_list:
                    detail = call[0][1] if len(call[0]) > 1 else ""
                    assert "SG.leaked_api_key_here" not in detail

    @patch('email_service.SENDGRID_API_KEY', 'fake-key')
    @patch('email_service.SENDGRID_AVAILABLE', True)
    def test_email_change_notification_exception_does_not_leak(self):
        """SendGrid exception in send_email_change_notification must not leak raw error."""
        from email_service import send_email_change_notification

        pii_message = "Rejected: admin@secret-corp.com not allowed"
        with patch('email_service.SendGridAPIClient') as mock_sg:
            mock_sg.return_value.send.side_effect = RuntimeError(pii_message)
            with patch('email_service.log_secure_operation') as mock_log:
                result = send_email_change_notification(
                    to_email="old@example.com",
                    new_email="new@example.com",
                )
                assert result.success is False
                assert "admin@secret-corp.com" not in result.message
                for call in mock_log.call_args_list:
                    detail = call[0][1] if len(call[0]) > 1 else ""
                    assert "admin@secret-corp.com" not in detail


# =============================================================================
# INTEGRATION: auth.py token decode doesn't leak JWT details
# =============================================================================

class TestAuthTokenDecodeSanitization:
    """Verify decode_access_token doesn't leak JWT error details."""

    def test_decode_invalid_token_does_not_leak_error(self):
        """Invalid JWT should log class name, not raw error message."""
        from auth import decode_access_token

        with patch('auth.log_secure_operation') as mock_log:
            result = decode_access_token("invalid.jwt.token")
            assert result is None
            # Find the token_decode_failed call
            decode_calls = [
                c for c in mock_log.call_args_list
                if c[0][0] == "token_decode_failed"
            ]
            assert len(decode_calls) == 1
            detail = decode_calls[0][0][1]
            # Should not contain raw PyJWT error message
            assert "invalid.jwt.token" not in detail
            # Should contain class name pattern
            assert "token validation failed" in detail
