"""
Tests for Billing Checkout API Endpoints — Route-level integration tests.

Tests cover:
- POST /billing/create-checkout-session — Stripe checkout
- GET /billing/subscription — subscription status
- POST /billing/cancel — cancel subscription
- POST /billing/reactivate — reactivate subscription
- POST /billing/add-seats — add seats
- POST /billing/remove-seats — remove seats
- GET /billing/portal-session — Stripe portal
- GET /billing/usage — usage stats
- Auth enforcement (401)
"""

import sys
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from auth import require_current_user, require_verified_user
from database import get_db
from main import app
from models import User, UserTier

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def verified_user(db_session):
    """Create a verified Professional user."""
    user = User(
        email="checkout_test@example.com",
        name="Checkout User",
        hashed_password="$2b$12$fakehashvalue",
        tier=UserTier.PROFESSIONAL,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def override_verified(db_session, verified_user):
    """Override require_verified_user + get_db."""
    app.dependency_overrides[require_verified_user] = lambda: verified_user
    app.dependency_overrides[get_db] = lambda: db_session
    yield verified_user
    app.dependency_overrides.clear()


@pytest.fixture
def override_current(db_session, verified_user):
    """Override require_current_user + get_db."""
    app.dependency_overrides[require_current_user] = lambda: verified_user
    app.dependency_overrides[get_db] = lambda: db_session
    yield verified_user
    app.dependency_overrides.clear()


# =============================================================================
# GET /billing/subscription
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestGetSubscription:
    """Tests for GET /billing/subscription."""

    @pytest.mark.asyncio
    async def test_subscription_success(self, override_current):
        """Returns subscription status for authenticated user."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/billing/subscription")
            assert response.status_code == 200
            data = response.json()
            assert "tier" in data
            assert "status" in data

    @pytest.mark.asyncio
    async def test_subscription_no_sub_returns_defaults(self, override_current):
        """User with no subscription gets default free-like response."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/billing/subscription")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "active"

    @pytest.mark.asyncio
    async def test_subscription_no_auth_returns_401(self):
        """No auth returns 401."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/billing/subscription")
            assert response.status_code == 401


# =============================================================================
# POST /billing/create-checkout-session
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestCreateCheckout:
    """Tests for POST /billing/create-checkout-session."""

    @pytest.mark.asyncio
    async def test_checkout_no_auth_returns_401(self):
        """POST without auth returns 401."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/billing/create-checkout-session",
                json={"tier": "solo", "interval": "monthly"},
            )
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_checkout_invalid_body_returns_422(self, override_verified):
        """POST with invalid body returns 422."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/billing/create-checkout-session",
                json={},
            )
            assert response.status_code == 422


# =============================================================================
# POST /billing/cancel
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestCancelSubscription:
    """Tests for POST /billing/cancel."""

    @pytest.mark.asyncio
    async def test_cancel_no_subscription_returns_404(self, override_current):
        """Cancel with no subscription returns 404."""
        with (
            patch("billing.stripe_client.is_stripe_enabled", return_value=True),
            patch("billing.subscription_manager.cancel_subscription", return_value=None),
            patch("billing.subscription_manager.get_subscription", return_value=None),
        ):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/billing/cancel")
                assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_cancel_no_auth_returns_401(self):
        """POST without auth returns 401."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/billing/cancel")
            assert response.status_code == 401


# =============================================================================
# POST /billing/reactivate
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestReactivateSubscription:
    """Tests for POST /billing/reactivate."""

    @pytest.mark.asyncio
    async def test_reactivate_no_subscription_returns_404(self, override_current):
        """Reactivate with no subscription returns 404."""
        with (
            patch("billing.stripe_client.is_stripe_enabled", return_value=True),
            patch("billing.subscription_manager.reactivate_subscription", return_value=None),
        ):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/billing/reactivate")
                assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_reactivate_no_auth_returns_401(self):
        """POST without auth returns 401."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/billing/reactivate")
            assert response.status_code == 401


# =============================================================================
# GET /billing/usage
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestGetUsage:
    """Tests for GET /billing/usage."""

    @pytest.mark.asyncio
    async def test_usage_success(self, override_current):
        """Returns usage stats for authenticated user."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/billing/usage")
            assert response.status_code == 200
            data = response.json()
            assert "uploads_used" in data
            assert "uploads_limit" in data
            assert "tier" in data

    @pytest.mark.asyncio
    async def test_usage_no_auth_returns_401(self):
        """GET without auth returns 401."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/billing/usage")
            assert response.status_code == 401


# =============================================================================
# POST /billing/add-seats + /billing/remove-seats
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestSeatManagement:
    """Tests for seat add/remove endpoints."""

    @pytest.mark.asyncio
    async def test_add_seats_no_auth_returns_401(self):
        """POST without auth returns 401."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/billing/add-seats", json={"seats": 2})
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_remove_seats_no_auth_returns_401(self):
        """POST without auth returns 401."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/billing/remove-seats", json={"seats": 1})
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_add_seats_invalid_body_returns_422(self, override_current):
        """POST with invalid body returns 422."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/billing/add-seats", json={})
            assert response.status_code == 422


# =============================================================================
# GET /billing/portal-session
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestPortalSession:
    """Tests for GET /billing/portal-session."""

    @pytest.mark.asyncio
    async def test_portal_no_billing_account_returns_404(self, override_current):
        """User with no billing account gets 404."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/billing/portal-session")
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_portal_no_auth_returns_401(self):
        """GET without auth returns 401."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/billing/portal-session")
            assert response.status_code == 401
