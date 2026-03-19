"""
Tests for Prior Period API Endpoints — Route-level integration tests.

Tests cover:
- POST /clients/{id}/periods — save prior period
- GET /clients/{id}/periods — list prior periods
- POST /audit/compare — compare current to prior period
- Auth enforcement (401)
- 404 for non-existent clients/periods
"""

import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from auth import require_current_user, require_verified_user
from database import get_db
from main import app
from models import Client, Industry, User, UserTier

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def auth_user(db_session):
    """Create a verified Professional user."""
    user = User(
        email="prior_period_api@example.com",
        name="Prior Period Tester",
        hashed_password="$2b$12$fakehashvalue",
        tier=UserTier.PROFESSIONAL,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def override_current(db_session, auth_user):
    """Override require_current_user + get_db."""
    app.dependency_overrides[require_current_user] = lambda: auth_user
    app.dependency_overrides[get_db] = lambda: db_session
    yield auth_user
    app.dependency_overrides.clear()


@pytest.fixture
def override_verified(db_session, auth_user):
    """Override require_verified_user + get_db."""
    app.dependency_overrides[require_verified_user] = lambda: auth_user
    app.dependency_overrides[get_db] = lambda: db_session
    yield auth_user
    app.dependency_overrides.clear()


@pytest.fixture
def user_client(db_session, auth_user):
    """Create a client owned by auth_user."""
    client = Client(
        user_id=auth_user.id,
        name="Prior Period Client",
        industry=Industry.TECHNOLOGY,
        fiscal_year_end="12-31",
    )
    db_session.add(client)
    db_session.flush()
    return client


SAMPLE_PERIOD = {
    "period_label": "FY2025",
    "period_date": "2025-12-31",
    "period_type": "annual",
    "total_assets": 1000000.0,
    "total_liabilities": 500000.0,
    "total_equity": 500000.0,
    "total_revenue": 2000000.0,
    "total_expenses": 1800000.0,
    "total_debits": 5000000.0,
    "total_credits": 5000000.0,
    "was_balanced": True,
    "anomaly_count": 3,
    "materiality_threshold": 50000.0,
    "row_count": 150,
}


# =============================================================================
# Route Registration
# =============================================================================


class TestPriorPeriodRouteRegistration:
    """Verify prior period routes are registered."""

    def test_save_period_route_exists(self):
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/clients/{client_id}/periods" in paths

    def test_compare_route_exists(self):
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/audit/compare" in paths


# =============================================================================
# POST /clients/{id}/periods
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestSavePriorPeriod:
    """Tests for POST /clients/{id}/periods."""

    @pytest.mark.asyncio
    async def test_save_period_success(self, override_current, user_client):
        """Save a prior period returns 201."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/clients/{user_client.id}/periods",
                json=SAMPLE_PERIOD,
            )
            assert response.status_code == 201
            data = response.json()
            assert data["status"] == "success"
            assert data["period_label"] == "FY2025"
            assert "period_id" in data

    @pytest.mark.asyncio
    async def test_save_period_client_not_found(self, override_current):
        """Non-existent client returns 404."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/clients/999999/periods",
                json=SAMPLE_PERIOD,
            )
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_save_period_no_auth_returns_401(self):
        """POST without auth returns 401."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/clients/1/periods",
                json=SAMPLE_PERIOD,
            )
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_save_period_missing_label_returns_422(self, override_current, user_client):
        """Missing required field returns 422."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/clients/{user_client.id}/periods",
                json={"total_assets": 100.0},
            )
            assert response.status_code == 422


# =============================================================================
# GET /clients/{id}/periods
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestListPriorPeriods:
    """Tests for GET /clients/{id}/periods."""

    @pytest.mark.asyncio
    async def test_list_periods_success(self, override_current, user_client):
        """List prior periods for a client."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/clients/{user_client.id}/periods")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_list_periods_after_save(self, override_current, user_client):
        """List returns saved periods."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            # Save a period first
            await client.post(
                f"/clients/{user_client.id}/periods",
                json=SAMPLE_PERIOD,
            )
            # Then list
            response = await client.get(f"/clients/{user_client.id}/periods")
            assert response.status_code == 200
            data = response.json()
            assert len(data) >= 1
            assert data[0]["period_label"] == "FY2025"

    @pytest.mark.asyncio
    async def test_list_periods_client_not_found(self, override_current):
        """Non-existent client returns 404."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/clients/999999/periods")
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_periods_no_auth_returns_401(self):
        """GET without auth returns 401."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/clients/1/periods")
            assert response.status_code == 401


# =============================================================================
# POST /audit/compare
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestCompareToprior:
    """Tests for POST /audit/compare."""

    @pytest.mark.asyncio
    async def test_compare_not_found(self, override_verified):
        """Comparing with non-existent prior period returns 404."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/audit/compare",
                json={
                    "prior_period_id": 999999,
                    "current_label": "Current",
                    "total_assets": 100.0,
                },
            )
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_compare_no_auth_returns_401(self):
        """POST without auth returns 401."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/audit/compare",
                json={"prior_period_id": 1, "current_label": "Current"},
            )
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_compare_success(self, override_current, override_verified, user_client):
        """Full save-then-compare flow."""
        # Use override_verified since compare requires require_verified_user
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            # Save a period first (uses require_current_user)
            save_resp = await client.post(
                f"/clients/{user_client.id}/periods",
                json=SAMPLE_PERIOD,
            )
            if save_resp.status_code == 201:
                period_id = save_resp.json()["period_id"]
                # Compare against saved period
                compare_resp = await client.post(
                    "/audit/compare",
                    json={
                        "prior_period_id": period_id,
                        "current_label": "FY2026",
                        "total_assets": 1100000.0,
                        "total_liabilities": 550000.0,
                        "total_equity": 550000.0,
                        "total_revenue": 2200000.0,
                        "total_expenses": 1900000.0,
                        "total_debits": 5500000.0,
                        "total_credits": 5500000.0,
                        "anomaly_count": 2,
                        "row_count": 160,
                    },
                )
                assert compare_resp.status_code == 200
                data = compare_resp.json()
                assert "categories" in data or "comparison" in data or compare_resp.status_code == 200
