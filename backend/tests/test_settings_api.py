"""
Tests for Settings API Endpoints — Sprint 242

Tests cover:
- GET /settings/practice — returns practice settings
- PUT /settings/practice — updates practice settings
- GET /clients/{id}/settings — returns client-specific settings
- PUT /clients/{id}/settings — updates client settings
- POST /settings/materiality/preview — materiality calculation preview
- GET /settings/materiality/resolve — cascade resolution
- 401 on missing auth
- 404 on non-existent client
"""

import sys

import httpx
import pytest

sys.path.insert(0, '..')

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
        email="settings_test@example.com",
        name="Settings Test User",
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
def override_auth(mock_user, db_session):
    """Override auth and DB dependencies for route testing."""
    app.dependency_overrides[require_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: db_session
    yield
    app.dependency_overrides.clear()


# =============================================================================
# GET /settings/practice
# =============================================================================

class TestGetPracticeSettings:
    """Tests for GET /settings/practice endpoint."""

    @pytest.mark.asyncio
    async def test_returns_practice_settings(self, override_auth):
        """GET /settings/practice returns default settings for new user."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/settings/practice")
            assert response.status_code == 200
            data = response.json()
            assert "default_materiality" in data
            assert "show_immaterial_by_default" in data
            assert "default_fiscal_year_end" in data
            assert "default_export_format" in data

    @pytest.mark.asyncio
    async def test_401_without_auth(self):
        """GET /settings/practice returns 401 without auth token."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/settings/practice")
            assert response.status_code == 401


# =============================================================================
# PUT /settings/practice
# =============================================================================

@pytest.mark.usefixtures("bypass_csrf")
class TestUpdatePracticeSettings:
    """Tests for PUT /settings/practice endpoint."""

    @pytest.mark.asyncio
    async def test_updates_settings(self, override_auth):
        """PUT /settings/practice updates and returns new settings."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.put(
                "/settings/practice",
                json={
                    "show_immaterial_by_default": True,
                    "default_export_format": "excel",
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["show_immaterial_by_default"] is True
            assert data["default_export_format"] == "excel"

    @pytest.mark.asyncio
    async def test_updates_materiality_formula(self, override_auth):
        """PUT /settings/practice updates materiality formula."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.put(
                "/settings/practice",
                json={
                    "default_materiality": {
                        "type": "fixed",
                        "value": 1000.0,
                    }
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["default_materiality"]["value"] == 1000.0


# =============================================================================
# GET /clients/{id}/settings
# =============================================================================

class TestGetClientSettings:
    """Tests for GET /clients/{id}/settings endpoint."""

    @pytest.mark.asyncio
    async def test_returns_client_settings(self, override_auth, mock_client):
        """GET /clients/{id}/settings returns default client settings."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(f"/clients/{mock_client.id}/settings")
            assert response.status_code == 200
            data = response.json()
            assert "notes" in data
            assert "industry_multiplier" in data
            assert "diagnostic_frequency" in data

    @pytest.mark.asyncio
    async def test_404_nonexistent_client(self, override_auth):
        """GET /clients/99999/settings returns 404 for non-existent client."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/clients/99999/settings")
            assert response.status_code == 404


# =============================================================================
# PUT /clients/{id}/settings
# =============================================================================

@pytest.mark.usefixtures("bypass_csrf")
class TestUpdateClientSettings:
    """Tests for PUT /clients/{id}/settings endpoint."""

    @pytest.mark.asyncio
    async def test_updates_client_settings(self, override_auth, mock_client):
        """PUT /clients/{id}/settings updates and returns new settings."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.put(
                f"/clients/{mock_client.id}/settings",
                json={
                    "notes": "Updated test notes",
                    "diagnostic_frequency": "quarterly",
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["notes"] == "Updated test notes"
            assert data["diagnostic_frequency"] == "quarterly"


# =============================================================================
# POST /settings/materiality/preview
# =============================================================================

@pytest.mark.usefixtures("bypass_csrf")
class TestMaterialityPreview:
    """Tests for POST /settings/materiality/preview endpoint."""

    @pytest.mark.asyncio
    async def test_preview_fixed_formula(self, override_auth):
        """POST /settings/materiality/preview with fixed formula."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.post(
                "/settings/materiality/preview",
                json={
                    "formula": {"type": "fixed", "value": 5000.0},
                    "total_revenue": 1000000.0,
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert "threshold" in data
            assert "formula_display" in data
            assert "explanation" in data


# =============================================================================
# GET /settings/materiality/resolve
# =============================================================================

class TestMaterialityResolve:
    """Tests for GET /settings/materiality/resolve endpoint."""

    @pytest.mark.asyncio
    async def test_resolve_practice_level(self, override_auth):
        """GET /settings/materiality/resolve returns practice-level config."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/settings/materiality/resolve")
            assert response.status_code == 200
            data = response.json()
            assert "formula" in data
            assert "source" in data
            assert data["source"] == "practice"

    @pytest.mark.asyncio
    async def test_resolve_with_session_override(self, override_auth):
        """GET /settings/materiality/resolve with session_threshold returns session source."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get(
                "/settings/materiality/resolve",
                params={"session_threshold": 2500.0}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["source"] == "session"
            assert data["session_override"] == 2500.0
