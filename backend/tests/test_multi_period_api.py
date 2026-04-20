"""
Tests for Multi-Period TB Comparison API Endpoints — Route-level integration tests.

Tests cover:
- POST /audit/compare-periods — two-period comparison
- POST /audit/compare-three-way — three-period comparison
- POST /export/csv/movements — CSV export
- Auth enforcement (401)
- Validation (422 for bad input)
"""

import sys
from pathlib import Path

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
def auth_user(db_session):
    """Create a verified Professional user."""
    user = User(
        email="multi_period_api@example.com",
        name="Multi-Period Tester",
        hashed_password="$2b$12$fakehashvalue",
        tier=UserTier.PROFESSIONAL,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def override_verified(db_session, auth_user):
    """Override auth + db."""
    app.dependency_overrides[require_verified_user] = lambda: auth_user
    app.dependency_overrides[require_current_user] = lambda: auth_user
    app.dependency_overrides[get_db] = lambda: db_session
    yield auth_user
    app.dependency_overrides.clear()


SAMPLE_ACCOUNTS = [
    {"account": "Cash", "debit": 10000, "credit": 0, "type": "asset"},
    {"account": "Revenue", "debit": 0, "credit": 10000, "type": "income"},
]


# =============================================================================
# Route Registration
# =============================================================================


class TestMultiPeriodRouteRegistration:
    """Verify multi-period routes are registered."""

    def test_compare_periods_route_exists(self):
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/audit/compare-periods" in paths

    def test_compare_three_way_route_exists(self):
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/audit/compare-three-way" in paths

    def test_export_movements_csv_route_exists(self):
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/export/csv/movements" in paths


# =============================================================================
# POST /audit/compare-periods
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestComparePeriods:
    """Tests for POST /audit/compare-periods."""

    @pytest.mark.asyncio
    async def test_compare_periods_success(self, override_verified):
        """Compare two trial balance periods."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/audit/compare-periods",
                json={
                    "prior_accounts": SAMPLE_ACCOUNTS,
                    "current_accounts": [
                        {"account": "Cash", "debit": 12000, "credit": 0, "type": "asset"},
                        {"account": "Revenue", "debit": 0, "credit": 12000, "type": "income"},
                    ],
                    "prior_label": "FY2024",
                    "current_label": "FY2025",
                    "materiality_threshold": 500.0,
                },
            )
            assert response.status_code == 200
            data = response.json()
            # MovementSummaryResponse structure
            assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_compare_periods_no_auth_returns_401(self):
        """POST without auth returns 401."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/audit/compare-periods",
                json={
                    "prior_accounts": [],
                    "current_accounts": [],
                },
            )
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_compare_periods_empty_body_returns_422(self, override_verified):
        """POST with empty body returns 422."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/audit/compare-periods", json={})
            assert response.status_code == 422


# =============================================================================
# POST /audit/compare-three-way
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestCompareThreeWay:
    """Tests for POST /audit/compare-three-way."""

    @pytest.mark.asyncio
    async def test_compare_three_way_success(self, override_verified):
        """Compare three trial balance periods."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/audit/compare-three-way",
                json={
                    "prior_accounts": SAMPLE_ACCOUNTS,
                    "current_accounts": SAMPLE_ACCOUNTS,
                    "budget_accounts": SAMPLE_ACCOUNTS,
                    "prior_label": "Prior",
                    "current_label": "Current",
                    "budget_label": "Budget",
                    "materiality_threshold": 500.0,
                },
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_compare_three_way_no_auth_returns_401(self):
        """POST without auth returns 401."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/audit/compare-three-way",
                json={
                    "prior_accounts": [],
                    "current_accounts": [],
                    "budget_accounts": [],
                },
            )
            assert response.status_code == 401


# =============================================================================
# POST /export/csv/movements
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestExportMovementsCsv:
    """Tests for POST /export/csv/movements."""

    @pytest.mark.asyncio
    async def test_export_csv_success(self, override_verified):
        """Export movement comparison as CSV."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/export/csv/movements",
                json={
                    "prior_accounts": SAMPLE_ACCOUNTS,
                    "current_accounts": SAMPLE_ACCOUNTS,
                    "prior_label": "Prior",
                    "current_label": "Current",
                    "budget_label": "Budget",
                    "materiality_threshold": 500.0,
                },
            )
            assert response.status_code == 200
            assert "text/csv" in response.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_export_csv_no_auth_returns_401(self):
        """POST without auth returns 401."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/export/csv/movements",
                json={
                    "prior_accounts": [],
                    "current_accounts": [],
                },
            )
            assert response.status_code == 401
