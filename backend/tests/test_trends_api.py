"""
Tests for Trends API Endpoints — Sprint 243

Tests cover:
- GET /clients/{id}/trends — trend analysis
- GET /clients/{id}/trends with <2 periods — 422
- GET /clients/{id}/industry-ratios — industry comparison
- GET /clients/{id}/industry-ratios with no summary — 422
- GET /clients/{id}/rolling-analysis — rolling window
- 401 on missing auth, 404 on non-existent client
"""

import sys
from datetime import date

import httpx
import pytest

sys.path.insert(0, "..")

from auth import require_current_user, require_verified_user
from database import get_db
from main import app
from models import Client, DiagnosticSummary, Industry, PeriodType, User, UserTier

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_user(db_session):
    """Create a real user in the test DB."""
    user = User(
        email="trends_test@example.com",
        name="Trends Test User",
        hashed_password="$2b$12$fakehashvalue",
        tier=UserTier.TEAM,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def mock_client(db_session, mock_user):
    """Create a real client in the test DB."""
    client = Client(
        user_id=mock_user.id,
        name="Trends Test Client",
        industry=Industry.TECHNOLOGY,
        fiscal_year_end="12-31",
    )
    db_session.add(client)
    db_session.flush()
    return client


@pytest.fixture
def override_auth(mock_user, db_session):
    """Override auth and DB dependencies."""
    app.dependency_overrides[require_current_user] = lambda: mock_user
    app.dependency_overrides[require_verified_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: db_session
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def two_summaries(db_session, mock_user, mock_client):
    """Create two diagnostic summaries for trend analysis."""
    s1 = DiagnosticSummary(
        client_id=mock_client.id,
        user_id=mock_user.id,
        period_date=date(2025, 3, 31),
        period_type=PeriodType.QUARTERLY,
        total_assets=900000.0,
        current_assets=300000.0,
        total_liabilities=200000.0,
        current_liabilities=100000.0,
        total_equity=700000.0,
        total_revenue=400000.0,
        cost_of_goods_sold=150000.0,
        total_expenses=300000.0,
        current_ratio=3.0,
        total_debits=450000.0,
        total_credits=450000.0,
        was_balanced=True,
        anomaly_count=1,
        materiality_threshold=500.0,
        row_count=40,
    )
    s2 = DiagnosticSummary(
        client_id=mock_client.id,
        user_id=mock_user.id,
        period_date=date(2025, 6, 30),
        period_type=PeriodType.QUARTERLY,
        total_assets=1000000.0,
        current_assets=400000.0,
        total_liabilities=300000.0,
        current_liabilities=150000.0,
        total_equity=700000.0,
        total_revenue=500000.0,
        cost_of_goods_sold=200000.0,
        total_expenses=350000.0,
        current_ratio=2.67,
        total_debits=500000.0,
        total_credits=500000.0,
        was_balanced=True,
        anomaly_count=2,
        materiality_threshold=1000.0,
        row_count=50,
    )
    db_session.add_all([s1, s2])
    db_session.flush()
    return [s1, s2]


# =============================================================================
# GET /clients/{id}/trends
# =============================================================================


class TestGetClientTrends:
    """Tests for GET /clients/{id}/trends endpoint."""

    @pytest.mark.asyncio
    async def test_returns_trend_analysis(self, override_auth, mock_client, two_summaries):
        """GET /clients/{id}/trends returns analysis with sufficient data."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/clients/{mock_client.id}/trends")
            assert response.status_code == 200
            data = response.json()
            assert data["client_id"] == mock_client.id
            assert data["periods_analyzed"] == 2
            assert "analysis" in data

    @pytest.mark.asyncio
    async def test_422_fewer_than_2_periods(self, override_auth, mock_client):
        """GET /clients/{id}/trends returns 422 with <2 summaries."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/clients/{mock_client.id}/trends")
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_404_nonexistent_client(self, override_auth):
        """GET /clients/99999/trends returns 404."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/clients/99999/trends")
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_401_without_auth(self, mock_client):
        """GET /clients/{id}/trends returns 401 without auth."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/clients/{mock_client.id}/trends")
            assert response.status_code == 401


# =============================================================================
# GET /clients/{id}/industry-ratios
# =============================================================================


class TestGetIndustryRatios:
    """Tests for GET /clients/{id}/industry-ratios endpoint."""

    @pytest.mark.asyncio
    async def test_returns_industry_ratios(self, override_auth, mock_client, two_summaries):
        """GET /clients/{id}/industry-ratios returns comparison data."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/clients/{mock_client.id}/industry-ratios")
            assert response.status_code == 200
            data = response.json()
            assert data["client_id"] == mock_client.id
            assert "ratios" in data
            assert "available_industries" in data

    @pytest.mark.asyncio
    async def test_422_no_summary(self, override_auth, mock_client):
        """GET /clients/{id}/industry-ratios returns 422 with no summary data."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/clients/{mock_client.id}/industry-ratios")
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_404_nonexistent_client(self, override_auth):
        """GET /clients/99999/industry-ratios returns 404."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/clients/99999/industry-ratios")
            assert response.status_code == 404


# =============================================================================
# GET /clients/{id}/rolling-analysis
# =============================================================================


class TestGetRollingAnalysis:
    """Tests for GET /clients/{id}/rolling-analysis endpoint."""

    @pytest.mark.asyncio
    async def test_returns_rolling_analysis(self, override_auth, mock_client, two_summaries):
        """GET /clients/{id}/rolling-analysis returns rolling window data."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/clients/{mock_client.id}/rolling-analysis")
            assert response.status_code == 200
            data = response.json()
            assert data["client_id"] == mock_client.id
            assert data["periods_analyzed"] == 2
            assert "analysis" in data

    @pytest.mark.asyncio
    async def test_422_insufficient_data(self, override_auth, mock_client):
        """GET /clients/{id}/rolling-analysis returns 422 with <2 summaries."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/clients/{mock_client.id}/rolling-analysis")
            assert response.status_code == 422
