"""
Tests for Contact API Endpoints — Sprint 244

Tests cover:
- POST /contact/submit — valid submission
- POST /contact/submit — honeypot field → silent rejection
- POST /contact/submit — missing required fields → 422
- Contact form dev fallback log redaction (Packet 2)
"""

import pytest
import httpx
from unittest.mock import patch

import sys
sys.path.insert(0, '..')

from main import app
from email_service import send_contact_form_email


# =============================================================================
# POST /contact/submit
# =============================================================================

@pytest.mark.usefixtures("bypass_csrf")
class TestContactSubmit:
    """Tests for POST /contact/submit endpoint."""

    @pytest.mark.asyncio
    async def test_valid_submission(self):
        """POST /contact/submit with valid data returns success."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post("/contact/submit", json={
                "name": "Test User",
                "email": "test@example.com",
                "company": "Test Corp",
                "inquiry_type": "General",
                "message": "This is a test contact form submission for testing purposes.",
            })
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "received" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_honeypot_silent_rejection(self):
        """POST /contact/submit with honeypot filled returns 200 but doesn't send."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post("/contact/submit", json={
                "name": "Bot User",
                "email": "bot@spam.com",
                "inquiry_type": "General",
                "message": "This should be silently rejected by the honeypot.",
                "honeypot": "I am a bot filling hidden fields",
            })
            # Returns 200 success to not tip off bots
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    @pytest.mark.asyncio
    async def test_missing_required_fields(self):
        """POST /contact/submit with missing fields returns 422."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post("/contact/submit", json={
                "name": "Test User",
                # Missing email, inquiry_type, message
            })
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_message_too_short(self):
        """POST /contact/submit with short message returns 422."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post("/contact/submit", json={
                "name": "Test",
                "email": "test@example.com",
                "inquiry_type": "General",
                "message": "Short",  # min_length=10
            })
            assert response.status_code == 422


# =============================================================================
# CONTACT FORM LOG REDACTION TESTS (Packet 2)
# =============================================================================

class TestContactFormLogRedaction:
    """Verify dev/fallback logs never contain PII or full message bodies."""

    @patch('email_service.SENDGRID_API_KEY', None)
    def test_no_api_key_fallback_does_not_log_message_body(self):
        """No-API-key fallback must not log the full message body."""
        secret_message = "This is confidential client financial information"
        with patch('email_service.log_secure_operation') as mock_log:
            send_contact_form_email(
                name="Jane Doe",
                email="jane@example.com",
                company="Acme Corp",
                inquiry_type="General",
                message=secret_message,
            )
            for call in mock_log.call_args_list:
                logged_detail = call[0][1] if len(call[0]) > 1 else ""
                assert secret_message not in logged_detail, (
                    f"Full message body leaked in log: {logged_detail}"
                )

    @patch('email_service.SENDGRID_AVAILABLE', False)
    def test_no_sendgrid_fallback_does_not_log_message_body(self):
        """SendGrid-unavailable fallback must not log the full message body."""
        secret_message = "Sensitive details about a merger and acquisition"
        with patch('email_service.log_secure_operation') as mock_log:
            send_contact_form_email(
                name="John Smith",
                email="john@example.com",
                company="BigCo",
                inquiry_type="Partnership",
                message=secret_message,
            )
            for call in mock_log.call_args_list:
                logged_detail = call[0][1] if len(call[0]) > 1 else ""
                assert secret_message not in logged_detail, (
                    f"Full message body leaked in log: {logged_detail}"
                )

    @patch('email_service.SENDGRID_API_KEY', None)
    def test_no_api_key_fallback_does_not_log_sender_email(self):
        """No-API-key fallback must not log the sender's full email."""
        sender_email = "confidential.sender@privatecompany.com"
        with patch('email_service.log_secure_operation') as mock_log:
            send_contact_form_email(
                name="Jane Doe",
                email=sender_email,
                company="",
                inquiry_type="General",
                message="A sufficiently long test message for validation.",
            )
            for call in mock_log.call_args_list:
                logged_detail = call[0][1] if len(call[0]) > 1 else ""
                assert sender_email not in logged_detail, (
                    f"Sender email leaked in log: {logged_detail}"
                )

    @patch('email_service.SENDGRID_API_KEY', None)
    def test_fallback_logs_safe_metadata(self):
        """Fallback should log inquiry type and message length for debugging."""
        with patch('email_service.log_secure_operation') as mock_log:
            send_contact_form_email(
                name="Test",
                email="test@example.com",
                company="",
                inquiry_type="Demo Request",
                message="A test message that is long enough.",
            )
            logged_details = [
                call[0][1] for call in mock_log.call_args_list if len(call[0]) > 1
            ]
            metadata_logged = any(
                "inquiry_type=Demo Request" in d and "message_length=" in d
                for d in logged_details
            )
            assert metadata_logged, (
                f"Expected safe metadata in logs, got: {logged_details}"
            )
