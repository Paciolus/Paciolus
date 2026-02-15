"""
Tests for Clients API Endpoints — Sprint 243

Tests cover:
- GET /clients — pagination + search
- POST /clients — create client, 201
- GET /clients/{id} — retrieve single client
- PUT /clients/{id} — update client
- DELETE /clients/{id} — delete client, 204
- Cross-user access prevention
- 401 on missing auth
"""

import pytest
import httpx

import sys
sys.path.insert(0, '..')

from main import app
from auth import require_current_user
from database import get_db
from models import User, Client, Industry, UserTier


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_user(db_session):
    """Create a real user in the test DB."""
    user = User(
        email="clients_test@example.com",
        name="Clients Test User",
        hashed_password="$2b$12$fakehashvalue",
        tier=UserTier.PROFESSIONAL,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def other_user(db_session):
    """Create a second user for cross-user access tests."""
    user = User(
        email="other_user@example.com",
        name="Other User",
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
        name="Test Client Corp",
        industry=Industry.TECHNOLOGY,
        fiscal_year_end="12-31",
    )
    db_session.add(client)
    db_session.flush()
    return client


@pytest.fixture
def other_user_client(db_session, other_user):
    """Create a client owned by the other user."""
    client = Client(
        user_id=other_user.id,
        name="Other User Client",
        industry=Industry.HEALTHCARE,
        fiscal_year_end="06-30",
    )
    db_session.add(client)
    db_session.flush()
    return client


@pytest.fixture
def override_auth(mock_user, db_session):
    """Override auth and DB dependencies."""
    app.dependency_overrides[require_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: db_session
    yield
    app.dependency_overrides.clear()


# =============================================================================
# GET /clients
# =============================================================================

class TestGetClients:
    """Tests for GET /clients endpoint."""

    @pytest.mark.asyncio
    async def test_returns_paginated_list(self, override_auth, mock_client):
        """GET /clients returns paginated client list."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/clients")
            assert response.status_code == 200
            data = response.json()
            assert "clients" in data
            assert "total_count" in data
            assert data["total_count"] >= 1
            assert data["page"] == 1

    @pytest.mark.asyncio
    async def test_search_query(self, override_auth, mock_client):
        """GET /clients?search=Test returns matching clients."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/clients", params={"search": "Test Client"})
            assert response.status_code == 200
            data = response.json()
            assert data["total_count"] >= 1

    @pytest.mark.asyncio
    async def test_401_without_auth(self):
        """GET /clients returns 401 without auth."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/clients")
            assert response.status_code == 401


# =============================================================================
# POST /clients
# =============================================================================

class TestCreateClient:
    """Tests for POST /clients endpoint."""

    @pytest.mark.asyncio
    async def test_creates_client(self, override_auth):
        """POST /clients creates and returns new client."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post("/clients", json={
                "name": "New Test Client",
                "industry": "technology",
                "fiscal_year_end": "12-31",
            })
            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "New Test Client"
            assert data["industry"] == "technology"
            assert "id" in data


# =============================================================================
# GET /clients/{id}
# =============================================================================

class TestGetClient:
    """Tests for GET /clients/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_returns_single_client(self, override_auth, mock_client):
        """GET /clients/{id} returns client details."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(f"/clients/{mock_client.id}")
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Test Client Corp"
            assert data["id"] == mock_client.id

    @pytest.mark.asyncio
    async def test_404_nonexistent_client(self, override_auth):
        """GET /clients/99999 returns 404."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/clients/99999")
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_cross_user_access_404(self, override_auth, other_user_client):
        """User A cannot access User B's client — returns 404."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(f"/clients/{other_user_client.id}")
            assert response.status_code == 404


# =============================================================================
# PUT /clients/{id}
# =============================================================================

class TestUpdateClient:
    """Tests for PUT /clients/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_updates_client(self, override_auth, mock_client):
        """PUT /clients/{id} updates and returns client."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.put(
                f"/clients/{mock_client.id}",
                json={"name": "Updated Name", "industry": "healthcare"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Updated Name"
            assert data["industry"] == "healthcare"

    @pytest.mark.asyncio
    async def test_404_nonexistent_client(self, override_auth):
        """PUT /clients/99999 returns 404."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.put("/clients/99999", json={"name": "Nope"})
            assert response.status_code == 404


# =============================================================================
# DELETE /clients/{id}
# =============================================================================

class TestDeleteClient:
    """Tests for DELETE /clients/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_deletes_client(self, override_auth, mock_client):
        """DELETE /clients/{id} removes client and returns 204."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.delete(f"/clients/{mock_client.id}")
            assert response.status_code == 204

            # Verify deleted
            get_response = await client.get(f"/clients/{mock_client.id}")
            assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_404_nonexistent_client(self, override_auth):
        """DELETE /clients/99999 returns 404."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.delete("/clients/99999")
            assert response.status_code == 404
