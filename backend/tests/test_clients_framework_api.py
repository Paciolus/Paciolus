"""
Tests for Client Framework Metadata API — Sprint 1

Tests cover:
- POST /clients with new framework metadata fields
- PUT /clients/{id} updating framework metadata
- GET /clients/{id} returning framework metadata
- GET /clients/{id}/resolved-framework endpoint
- Validation: invalid enum values rejected
"""

import sys

import httpx
import pytest

sys.path.insert(0, "..")

from auth import require_current_user
from database import get_db
from main import app
from models import Client, EntityType, Industry, ReportingFramework, User, UserTier

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_user(db_session):
    """Create a real user in the test DB."""
    user = User(
        email="framework_test@example.com",
        name="Framework Test User",
        hashed_password="$2b$12$fakehashvalue",
        tier=UserTier.TEAM,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def override_auth(mock_user, db_session):
    """Override auth and DB dependencies."""
    app.dependency_overrides[require_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: db_session
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def governmental_client(db_session, mock_user):
    """Create a governmental client for framework resolution tests."""
    client = Client(
        user_id=mock_user.id,
        name="City of Springfield",
        industry=Industry.OTHER,
        fiscal_year_end="06-30",
        reporting_framework=ReportingFramework.AUTO,
        entity_type=EntityType.GOVERNMENTAL,
        jurisdiction_country="US",
        jurisdiction_state="Illinois",
    )
    db_session.add(client)
    db_session.flush()
    return client


@pytest.fixture
def for_profit_client(db_session, mock_user):
    """Create a for-profit client."""
    client = Client(
        user_id=mock_user.id,
        name="Acme Corp",
        industry=Industry.TECHNOLOGY,
        fiscal_year_end="12-31",
        reporting_framework=ReportingFramework.AUTO,
        entity_type=EntityType.FOR_PROFIT,
        jurisdiction_country="US",
        jurisdiction_state="Delaware",
    )
    db_session.add(client)
    db_session.flush()
    return client


# =============================================================================
# POST /clients — Create with Framework Metadata
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestCreateClientFramework:
    """Tests for creating clients with framework metadata."""

    @pytest.mark.asyncio
    async def test_create_with_defaults(self, override_auth):
        """POST /clients without framework fields uses defaults."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/clients",
                json={
                    "name": "Default Client",
                },
            )
            assert response.status_code == 201
            data = response.json()
            assert data["reporting_framework"] == "auto"
            assert data["entity_type"] == "other"
            assert data["jurisdiction_country"] == "US"
            assert data["jurisdiction_state"] is None

    @pytest.mark.asyncio
    async def test_create_governmental(self, override_auth):
        """POST /clients with governmental entity creates GASB-ready client."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/clients",
                json={
                    "name": "City of Springfield",
                    "entity_type": "governmental",
                    "reporting_framework": "auto",
                    "jurisdiction_country": "US",
                    "jurisdiction_state": "Illinois",
                },
            )
            assert response.status_code == 201
            data = response.json()
            assert data["entity_type"] == "governmental"
            assert data["jurisdiction_state"] == "Illinois"

    @pytest.mark.asyncio
    async def test_create_explicit_gasb(self, override_auth):
        """POST /clients with explicit GASB framework."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/clients",
                json={
                    "name": "County Hospital",
                    "entity_type": "governmental",
                    "reporting_framework": "gasb",
                    "jurisdiction_country": "US",
                },
            )
            assert response.status_code == 201
            data = response.json()
            assert data["reporting_framework"] == "gasb"
            assert data["entity_type"] == "governmental"

    @pytest.mark.asyncio
    async def test_create_invalid_framework_rejected(self, override_auth):
        """POST /clients with invalid reporting_framework returns 400."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/clients",
                json={
                    "name": "Bad Client",
                    "reporting_framework": "ifrs",  # not a valid option
                },
            )
            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_invalid_entity_type_rejected(self, override_auth):
        """POST /clients with invalid entity_type returns 400."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/clients",
                json={
                    "name": "Bad Client",
                    "entity_type": "partnership",  # not a valid option
                },
            )
            assert response.status_code == 400


# =============================================================================
# PUT /clients/{id} — Update Framework Metadata
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestUpdateClientFramework:
    """Tests for updating client framework metadata."""

    @pytest.mark.asyncio
    async def test_update_entity_type(self, override_auth, for_profit_client):
        """PUT /clients/{id} can change entity_type."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.put(f"/clients/{for_profit_client.id}", json={"entity_type": "governmental"})
            assert response.status_code == 200
            data = response.json()
            assert data["entity_type"] == "governmental"

    @pytest.mark.asyncio
    async def test_update_framework(self, override_auth, for_profit_client):
        """PUT /clients/{id} can change reporting_framework."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.put(f"/clients/{for_profit_client.id}", json={"reporting_framework": "fasb"})
            assert response.status_code == 200
            data = response.json()
            assert data["reporting_framework"] == "fasb"

    @pytest.mark.asyncio
    async def test_update_jurisdiction(self, override_auth, for_profit_client):
        """PUT /clients/{id} can change jurisdiction fields."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.put(
                f"/clients/{for_profit_client.id}",
                json={
                    "jurisdiction_country": "CA",
                    "jurisdiction_state": "Ontario",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["jurisdiction_country"] == "CA"
            assert data["jurisdiction_state"] == "Ontario"

    @pytest.mark.asyncio
    async def test_partial_update_preserves_fields(self, override_auth, governmental_client):
        """PUT /clients/{id} with only name preserves framework fields."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.put(f"/clients/{governmental_client.id}", json={"name": "Renamed City"})
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Renamed City"
            assert data["entity_type"] == "governmental"
            assert data["jurisdiction_state"] == "Illinois"


# =============================================================================
# GET /clients/{id} — Read Framework Metadata
# =============================================================================


class TestGetClientFramework:
    """Tests for reading client framework metadata."""

    @pytest.mark.asyncio
    async def test_returns_framework_fields(self, override_auth, governmental_client):
        """GET /clients/{id} includes new framework fields."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/clients/{governmental_client.id}")
            assert response.status_code == 200
            data = response.json()
            assert data["reporting_framework"] == "auto"
            assert data["entity_type"] == "governmental"
            assert data["jurisdiction_country"] == "US"
            assert data["jurisdiction_state"] == "Illinois"


# =============================================================================
# GET /clients/{id}/resolved-framework — Framework Resolution
# =============================================================================


class TestResolvedFramework:
    """Tests for the framework resolution endpoint."""

    @pytest.mark.asyncio
    async def test_governmental_resolves_gasb(self, override_auth, governmental_client):
        """Governmental AUTO client resolves to GASB."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/clients/{governmental_client.id}/resolved-framework")
            assert response.status_code == 200
            data = response.json()
            assert data["framework"] == "gasb"
            assert data["resolution_reason"] == "entity_type_governmental"
            assert data["warnings"] == []

    @pytest.mark.asyncio
    async def test_for_profit_resolves_fasb(self, override_auth, for_profit_client):
        """For-profit AUTO client resolves to FASB."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/clients/{for_profit_client.id}/resolved-framework")
            assert response.status_code == 200
            data = response.json()
            assert data["framework"] == "fasb"
            assert data["resolution_reason"] == "entity_type_for_profit"
            assert data["warnings"] == []

    @pytest.mark.asyncio
    async def test_404_nonexistent_client(self, override_auth):
        """GET /clients/99999/resolved-framework returns 404."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/clients/99999/resolved-framework")
            assert response.status_code == 404
