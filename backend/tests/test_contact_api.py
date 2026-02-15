"""
Tests for Contact API Endpoints — Sprint 244

Tests cover:
- POST /contact/submit — valid submission
- POST /contact/submit — honeypot field → silent rejection
- POST /contact/submit — missing required fields → 422
"""

import pytest
import httpx

import sys
sys.path.insert(0, '..')

from main import app


# =============================================================================
# POST /contact/submit
# =============================================================================

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
