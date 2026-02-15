"""
Tests for Diagnostics API Endpoints — Sprint 243

Tests cover:
- POST /diagnostics/summary — saves diagnostic summary
- GET /diagnostics/summary/{id}/previous — retrieves most recent
- GET /diagnostics/summary/{id}/history — pagination of historical
- 401 on missing auth, 404 on non-existent client
"""

import pytest
import httpx

import sys
sys.path.insert(0, '..')

from main import app
from auth import require_current_user, require_verified_user
from database import get_db
from models import User, Client, Industry, UserTier


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_user(db_session):
    """Create a real user in the test DB."""
    user = User(
        email="diagnostics_test@example.com",
        name="Diagnostics Test User",
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
    """Create a real client in the test DB."""
    client = Client(
        user_id=mock_user.id,
        name="Diagnostics Test Client",
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
    app.dependency_overrides[require_verified_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: db_session
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def summary_payload(mock_client):
    """Standard diagnostic summary payload."""
    return {
        "client_id": mock_client.id,
        "filename": "test_tb.csv",
        "total_assets": 1000000.0,
        "current_assets": 400000.0,
        "total_liabilities": 300000.0,
        "current_liabilities": 150000.0,
        "total_equity": 700000.0,
        "total_revenue": 500000.0,
        "cost_of_goods_sold": 200000.0,
        "total_expenses": 350000.0,
        "current_ratio": 2.67,
        "total_debits": 500000.0,
        "total_credits": 500000.0,
        "was_balanced": True,
        "anomaly_count": 2,
        "materiality_threshold": 1000.0,
        "row_count": 50,
    }


# =============================================================================
# POST /diagnostics/summary
# =============================================================================

@pytest.mark.usefixtures("bypass_csrf")
class TestSaveDiagnosticSummary:
    """Tests for POST /diagnostics/summary endpoint."""

    @pytest.mark.asyncio
    async def test_saves_summary(self, override_auth, summary_payload):
        """POST /diagnostics/summary saves and returns summary."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post("/diagnostics/summary", json=summary_payload)
            assert response.status_code == 201
            data = response.json()
            assert data["total_assets"] == 1000000.0
            assert data["was_balanced"] is True
            assert data["anomaly_count"] == 2
            assert "id" in data
            assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_404_nonexistent_client(self, override_auth):
        """POST /diagnostics/summary returns 404 for non-existent client."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post("/diagnostics/summary", json={
                "client_id": 99999,
                "filename": "test.csv",
                "total_debits": 100.0,
                "total_credits": 100.0,
                "was_balanced": True,
                "anomaly_count": 0,
                "materiality_threshold": 0.0,
                "row_count": 1,
            })
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_401_without_auth(self, summary_payload):
        """POST /diagnostics/summary returns 401 without auth."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post("/diagnostics/summary", json=summary_payload)
            assert response.status_code == 401


# =============================================================================
# GET /diagnostics/summary/{client_id}/previous
# =============================================================================

@pytest.mark.usefixtures("bypass_csrf")
class TestGetPreviousSummary:
    """Tests for GET /diagnostics/summary/{client_id}/previous endpoint."""

    @pytest.mark.asyncio
    async def test_returns_most_recent(self, override_auth, summary_payload):
        """GET /diagnostics/summary/{id}/previous returns the most recent."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            # Create a summary first
            await client.post("/diagnostics/summary", json=summary_payload)

            # Fetch previous
            response = await client.get(
                f"/diagnostics/summary/{summary_payload['client_id']}/previous"
            )
            assert response.status_code == 200
            data = response.json()
            assert data["total_assets"] == 1000000.0

    @pytest.mark.asyncio
    async def test_returns_null_when_none(self, override_auth, mock_client):
        """GET /diagnostics/summary/{id}/previous returns null when no summaries."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                f"/diagnostics/summary/{mock_client.id}/previous"
            )
            assert response.status_code == 200
            # Response should be null/None
            assert response.json() is None

    @pytest.mark.asyncio
    async def test_404_nonexistent_client(self, override_auth):
        """GET /diagnostics/summary/99999/previous returns 404."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/diagnostics/summary/99999/previous")
            assert response.status_code == 404


# =============================================================================
# GET /diagnostics/summary/{client_id}/history
# =============================================================================

@pytest.mark.usefixtures("bypass_csrf")
class TestGetDiagnosticHistory:
    """Tests for GET /diagnostics/summary/{client_id}/history endpoint."""

    @pytest.mark.asyncio
    async def test_returns_history(self, override_auth, summary_payload):
        """GET /diagnostics/summary/{id}/history returns summary list."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            # Create two summaries
            await client.post("/diagnostics/summary", json=summary_payload)
            await client.post("/diagnostics/summary", json=summary_payload)

            response = await client.get(
                f"/diagnostics/summary/{summary_payload['client_id']}/history"
            )
            assert response.status_code == 200
            data = response.json()
            assert data["total_count"] >= 2
            assert len(data["summaries"]) >= 2
            assert data["client_name"] == "Diagnostics Test Client"

    @pytest.mark.asyncio
    async def test_404_nonexistent_client(self, override_auth):
        """GET /diagnostics/summary/99999/history returns 404."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/diagnostics/summary/99999/history")
            assert response.status_code == 404
