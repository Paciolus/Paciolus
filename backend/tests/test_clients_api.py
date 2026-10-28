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

import sys

import httpx
import pytest

sys.path.insert(0, "..")

from auth import require_current_user
from database import get_db
from main import app
from models import Client, Industry, User, UserTier

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
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/clients")
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "total_count" in data
            assert data["total_count"] >= 1
            assert data["page"] == 1

    @pytest.mark.asyncio
    async def test_search_query(self, override_auth, mock_client):
        """GET /clients?search=Test returns matching clients."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/clients", params={"search": "Test Client"})
            assert response.status_code == 200
            data = response.json()
            assert data["total_count"] >= 1

    @pytest.mark.asyncio
    async def test_401_without_auth(self):
        """GET /clients returns 401 without auth."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/clients")
            assert response.status_code == 401


# =============================================================================
# POST /clients
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestCreateClient:
    """Tests for POST /clients endpoint."""

    @pytest.mark.asyncio
    async def test_creates_client(self, override_auth):
        """POST /clients creates and returns new client."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/clients",
                json={
                    "name": "New Test Client",
                    "industry": "technology",
                    "fiscal_year_end": "12-31",
                },
            )
            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "New Test Client"
            assert data["industry"] == "technology"
            assert "id" in data


@pytest.fixture
def free_user(db_session):
    """A FREE-tier user (max_clients=3) for the client-limit tests."""
    user = User(
        email="clients_free@example.com",
        name="Free Tier User",
        hashed_password="$2b$12$fakehashvalue",
        tier=UserTier.FREE,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def override_auth_free(free_user, db_session):
    app.dependency_overrides[require_current_user] = lambda: free_user
    app.dependency_overrides[get_db] = lambda: db_session
    yield
    app.dependency_overrides.clear()


def _seed_clients(db_session, user, n):
    for i in range(n):
        db_session.add(Client(user_id=user.id, name=f"Seed {i}", industry=Industry.OTHER, fiscal_year_end="12-31"))
    db_session.flush()


_NEW_CLIENT = {"name": "Limit Probe", "industry": "technology", "fiscal_year_end": "12-31"}


@pytest.mark.usefixtures("bypass_csrf")
class TestCreateClientLimit:
    """Sprint 817: POST /clients enforces the tier client limit.

    Pins the HTTP contract of the limit so the route can delegate to
    ``shared.entitlement_checks.check_client_limit`` (one implementation)
    without any change in what a caller sees.
    """

    @pytest.mark.asyncio
    async def test_under_limit_creates(self, override_auth_free, free_user, db_session):
        _seed_clients(db_session, free_user, 2)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/clients", json=_NEW_CLIENT)
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_at_limit_returns_exact_403(self, override_auth_free, free_user, db_session):
        _seed_clients(db_session, free_user, 3)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/clients", json=_NEW_CLIENT)
        assert response.status_code == 403
        assert response.json()["detail"] == {
            "code": "TIER_LIMIT_EXCEEDED",
            "message": "Client limit reached (3/3). Upgrade your plan to add more clients.",
            "resource": "clients",
            "current_tier": "free",
            "upgrade_url": "/pricing",
        }
        assert db_session.query(Client).filter(Client.user_id == free_user.id).count() == 3

    @pytest.mark.asyncio
    async def test_soft_mode_at_limit_creates(self, override_auth_free, free_user, db_session, monkeypatch):
        import config
        import shared.entitlement_checks as ec

        # Both enforcement-mode readers (the pre-817 inline check read the
        # config constant; the shared check reads _get_enforcement_mode).
        monkeypatch.setattr(config, "ENTITLEMENT_ENFORCEMENT", "soft")
        monkeypatch.setattr(ec, "_get_enforcement_mode", lambda: "soft")
        _seed_clients(db_session, free_user, 3)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/clients", json=_NEW_CLIENT)
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_unlimited_tier_ignores_count(self, override_auth, mock_user, db_session):
        _seed_clients(db_session, mock_user, 5)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/clients", json=_NEW_CLIENT)
        assert response.status_code == 201


# =============================================================================
# GET /clients/{id}
# =============================================================================


class TestGetClient:
    """Tests for GET /clients/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_returns_single_client(self, override_auth, mock_client):
        """GET /clients/{id} returns client details."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/clients/{mock_client.id}")
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Test Client Corp"
            assert data["id"] == mock_client.id

    @pytest.mark.asyncio
    async def test_404_nonexistent_client(self, override_auth):
        """GET /clients/99999 returns 404."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/clients/99999")
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_cross_user_access_404(self, override_auth, other_user_client):
        """User A cannot access User B's client — returns 404."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/clients/{other_user_client.id}")
            assert response.status_code == 404


# =============================================================================
# PUT /clients/{id}
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestUpdateClient:
    """Tests for PUT /clients/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_updates_client(self, override_auth, mock_client):
        """PUT /clients/{id} updates and returns client."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.put(
                f"/clients/{mock_client.id}", json={"name": "Updated Name", "industry": "healthcare"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Updated Name"
            assert data["industry"] == "healthcare"

    @pytest.mark.asyncio
    async def test_404_nonexistent_client(self, override_auth):
        """PUT /clients/99999 returns 404."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.put("/clients/99999", json={"name": "Nope"})
            assert response.status_code == 404


# =============================================================================
# DELETE /clients/{id}
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestDeleteClient:
    """Tests for DELETE /clients/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_deletes_client(self, override_auth, mock_client):
        """DELETE /clients/{id} removes client and returns 204."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete(f"/clients/{mock_client.id}")
            assert response.status_code == 204

            # Verify deleted
            get_response = await client.get(f"/clients/{mock_client.id}")
            assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_404_nonexistent_client(self, override_auth):
        """DELETE /clients/99999 returns 404."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete("/clients/99999")
            assert response.status_code == 404
