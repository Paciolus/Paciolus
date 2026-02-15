"""
Tests for Health & Waitlist API Endpoints — Sprint 244

Tests cover:
- GET /health — returns 200 with status
- POST /waitlist — valid email submission
"""

import pytest
import httpx

import sys
sys.path.insert(0, '..')

from main import app


# =============================================================================
# GET /health
# =============================================================================

class TestHealthCheck:
    """Tests for GET /health endpoint."""

    @pytest.mark.asyncio
    async def test_returns_healthy(self):
        """GET /health returns 200 with healthy status."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "timestamp" in data
            assert "version" in data

    @pytest.mark.asyncio
    async def test_no_auth_required(self):
        """GET /health works without authentication."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/health")
            assert response.status_code == 200


# =============================================================================
# POST /waitlist
# =============================================================================

@pytest.mark.usefixtures("bypass_csrf")
class TestWaitlist:
    """Tests for POST /waitlist endpoint."""

    @pytest.mark.asyncio
    async def test_valid_email_submission(self, tmp_path, monkeypatch):
        """POST /waitlist with valid email returns 201."""
        # Override waitlist file to tmp_path to avoid side effects
        import routes.health as health_mod
        monkeypatch.setattr(health_mod, "WAITLIST_FILE", tmp_path / "waitlist.csv")

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post("/waitlist", json={
                "email": "waitlist_test@example.com",
            })
            assert response.status_code == 201
            data = response.json()
            assert data["success"] is True

    @pytest.mark.asyncio
    async def test_invalid_email_422(self):
        """POST /waitlist with invalid email returns 422."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post("/waitlist", json={
                "email": "not-an-email",
            })
            assert response.status_code == 422
