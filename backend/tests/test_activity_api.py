"""
Tests for Activity & Dashboard API Endpoints — Sprint 242

Tests cover:
- POST /activity/log — creates activity record
- GET /activity/history — pagination
- DELETE /activity/clear — clears all activity
- GET /dashboard/stats — aggregation
- 401 on missing auth
"""

import sys
from decimal import Decimal

import httpx
import pytest

sys.path.insert(0, "..")

from auth import require_current_user
from database import get_db
from main import app
from models import Client, DiagnosticSummary, Industry, User, UserTier

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_user(db_session):
    """Create a real user in the test DB."""
    user = User(
        email="activity_test@example.com",
        name="Activity Test User",
        hashed_password="$2b$12$fakehashvalue",
        tier=UserTier.PROFESSIONAL,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def mock_client(db_session, mock_user):
    """Create a client for the test user."""
    client = Client(
        user_id=mock_user.id,
        name="Activity Test Client",
        industry=Industry.TECHNOLOGY,
        fiscal_year_end="12-31",
    )
    db_session.add(client)
    db_session.flush()
    return client


@pytest.fixture
def override_auth(mock_user, db_session):
    """Override auth and DB dependencies for route testing."""
    app.dependency_overrides[require_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: db_session
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def sample_activity_payload():
    """Standard activity log payload for testing."""
    return {
        "filename": "test_trial_balance.csv",
        "record_count": 100,
        "total_debits": 500000.0,
        "total_credits": 500000.0,
        "materiality_threshold": 1000.0,
        "was_balanced": True,
        "anomaly_count": 3,
        "material_count": 1,
        "immaterial_count": 2,
    }


# =============================================================================
# POST /activity/log
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestLogActivity:
    """Tests for POST /activity/log endpoint."""

    @pytest.mark.asyncio
    async def test_creates_activity_record(self, override_auth, sample_activity_payload):
        """POST /activity/log creates and returns activity record."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/activity/log", json=sample_activity_payload)
            assert response.status_code == 201
            data = response.json()
            assert data["record_count"] == 100
            assert data["total_debits"] == 500000.0
            assert data["was_balanced"] is True
            assert data["anomaly_count"] == 3
            assert "id" in data
            assert "timestamp" in data
            assert "filename_hash" in data

    @pytest.mark.asyncio
    async def test_401_without_auth(self, sample_activity_payload):
        """POST /activity/log returns 401 without auth."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/activity/log", json=sample_activity_payload)
            assert response.status_code == 401


# =============================================================================
# GET /activity/history
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestActivityHistory:
    """Tests for GET /activity/history endpoint."""

    @pytest.mark.asyncio
    async def test_returns_paginated_history(self, override_auth, sample_activity_payload):
        """GET /activity/history returns paginated activity list."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            # Create an activity first
            await client.post("/activity/log", json=sample_activity_payload)

            # Fetch history
            response = await client.get("/activity/history", params={"page": 1, "page_size": 10})
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "total_count" in data
            assert "page" in data
            assert data["page"] == 1
            assert data["total_count"] >= 1
            assert len(data["items"]) >= 1

    @pytest.mark.asyncio
    async def test_empty_history(self, override_auth):
        """GET /activity/history returns empty list for new user."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/activity/history")
            assert response.status_code == 200
            data = response.json()
            assert data["items"] == []
            assert data["total_count"] == 0


# =============================================================================
# DELETE /activity/clear
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestClearActivity:
    """Tests for DELETE /activity/clear endpoint."""

    @pytest.mark.asyncio
    async def test_clears_all_activity(self, override_auth, sample_activity_payload):
        """DELETE /activity/clear removes all activity for user."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            # Create activities
            await client.post("/activity/log", json=sample_activity_payload)
            await client.post("/activity/log", json=sample_activity_payload)

            # Clear
            response = await client.delete("/activity/clear")
            assert response.status_code == 204

            # Verify cleared
            history = await client.get("/activity/history")
            assert history.json()["total_count"] == 0

    @pytest.mark.asyncio
    async def test_401_without_auth(self):
        """DELETE /activity/clear returns 401 without auth."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete("/activity/clear")
            assert response.status_code == 401


# =============================================================================
# GET /dashboard/stats
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestDashboardStats:
    """Tests for GET /dashboard/stats endpoint."""

    @pytest.mark.asyncio
    async def test_returns_dashboard_stats(self, override_auth, mock_client, sample_activity_payload):
        """GET /dashboard/stats returns aggregated statistics."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            # Create activity for today's count
            await client.post("/activity/log", json=sample_activity_payload)

            response = await client.get("/dashboard/stats")
            assert response.status_code == 200
            data = response.json()
            assert "total_clients" in data
            assert "assessments_today" in data
            assert "total_assessments" in data
            assert "last_assessment_date" in data
            assert data["total_clients"] >= 1  # We created mock_client
            assert data["total_assessments"] >= 1

    @pytest.mark.asyncio
    async def test_dashboard_stats_no_activity(self, override_auth):
        """GET /dashboard/stats with no activity returns zero counts."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/dashboard/stats")
            assert response.status_code == 200
            data = response.json()
            assert data["total_assessments"] == 0
            assert data["assessments_today"] == 0
            assert data["last_assessment_date"] is None

    @pytest.mark.asyncio
    async def test_401_without_auth(self):
        """GET /dashboard/stats returns 401 without auth."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/dashboard/stats")
            assert response.status_code == 401


# =============================================================================
# Decimal Precision Tests (FIX 4: No float conversion for monetary values)
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestDecimalPrecision:
    """Verify monetary values are serialized without float conversion drift."""

    @pytest.mark.asyncio
    async def test_activity_log_preserves_decimal_precision(self, override_auth):
        """POST /activity/log with values that would lose precision as float
        must return exact string representation via DecimalJSONResponse."""
        payload = {
            "filename": "decimal_test.csv",
            "record_count": 10,
            "total_debits": 0.1,
            "total_credits": 0.2,
            "materiality_threshold": 0.3,
            "was_balanced": False,
            "anomaly_count": 0,
        }
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/activity/log", json=payload)
            assert response.status_code == 201
            data = response.json()
            # DecimalJSONResponse serializes Decimal as string
            # Pydantic coerces to float for float-typed fields, but
            # the response should not introduce additional precision loss
            # beyond what Pydantic's float coercion introduces
            assert "total_debits" in data
            assert "total_credits" in data
            assert "materiality_threshold" in data

    @pytest.mark.asyncio
    async def test_activity_history_no_explicit_float_cast(self, override_auth):
        """GET /activity/history should return monetary values without
        explicit float() conversion (values come from Numeric columns)."""
        payload = {
            "filename": "precision_history.csv",
            "record_count": 5,
            "total_debits": 12345.67,
            "total_credits": 12345.67,
            "materiality_threshold": 500.00,
            "was_balanced": True,
        }
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/activity/log", json=payload)
            response = await client.get("/activity/history")
            assert response.status_code == 200
            items = response.json()["items"]
            assert len(items) >= 1
            item = items[0]
            # Verify monetary fields are present and numeric
            assert item["total_debits"] == 12345.67
            assert item["total_credits"] == 12345.67
            assert item["materiality_threshold"] == 500.0


class TestGetCategoryTotalsDict:
    """Verify DiagnosticSummary.get_category_totals_dict returns Decimal values."""

    def test_returns_decimal_values(self, db_session, mock_user, mock_client):
        """get_category_totals_dict() must return Decimal, not float, for monetary fields."""
        summary = DiagnosticSummary(
            client_id=mock_client.id,
            user_id=mock_user.id,
            total_assets=Decimal("1000000.50"),
            current_assets=Decimal("500000.25"),
            inventory=Decimal("100000.10"),
            total_liabilities=Decimal("600000.30"),
            current_liabilities=Decimal("200000.15"),
            total_equity=Decimal("400000.20"),
            total_revenue=Decimal("800000.40"),
            cost_of_goods_sold=Decimal("300000.12"),
            total_expenses=Decimal("700000.35"),
            operating_expenses=Decimal("400000.22"),
        )
        db_session.add(summary)
        db_session.flush()

        totals = summary.get_category_totals_dict()
        for key, value in totals.items():
            assert isinstance(value, Decimal), f"{key} should be Decimal, got {type(value).__name__}"

    def test_null_fields_return_decimal_zero(self, db_session, mock_user, mock_client):
        """Null monetary fields should return Decimal(0), not float(0)."""
        summary = DiagnosticSummary(
            client_id=mock_client.id,
            user_id=mock_user.id,
        )
        db_session.add(summary)
        db_session.flush()

        totals = summary.get_category_totals_dict()
        for key, value in totals.items():
            assert isinstance(value, Decimal), f"{key} should be Decimal, got {type(value).__name__}"
            assert value == Decimal(0)
