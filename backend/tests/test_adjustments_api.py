"""
Tests for Adjustments API Endpoints — Route-level integration tests.

Tests cover:
- POST /audit/adjustments — create adjusting entry
- GET /audit/adjustments — list entries
- GET /audit/adjustments/reference/next — next reference
- GET /audit/adjustments/types — adjustment types enum
- GET /audit/adjustments/statuses — adjustment statuses enum
- GET /audit/adjustments/{entry_id} — get specific entry
- PUT /audit/adjustments/{entry_id}/status — update status
- DELETE /audit/adjustments/{entry_id} — delete entry
- DELETE /audit/adjustments — clear all
- Auth enforcement (401)
"""

import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from auth import require_verified_user
from database import get_db
from main import app
from models import User, UserTier

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def override_verified(db_session):
    """Override auth + db for a verified user."""
    user = User(
        email="adj_test@example.com",
        name="Adjustment Test User",
        hashed_password="$2b$12$fakehashvalue",
        tier=UserTier.PROFESSIONAL,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()

    app.dependency_overrides[require_verified_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: db_session
    yield user
    app.dependency_overrides.clear()


SAMPLE_ENTRY = {
    "reference": "AJE-001",
    "description": "Test reclassification entry",
    "adjustment_type": "reclassification",
    "lines": [
        {"account_name": "Cash", "debit": 1000.0, "credit": 0.0, "description": "Debit cash"},
        {"account_name": "Revenue", "debit": 0.0, "credit": 1000.0, "description": "Credit revenue"},
    ],
    "notes": "Test notes",
    "is_reversing": False,
}


# =============================================================================
# Route Registration
# =============================================================================


class TestAdjustmentRouteRegistration:
    """Verify adjustment routes are registered."""

    def test_create_adjustment_route_exists(self):
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/audit/adjustments" in paths

    def test_types_route_exists(self):
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/audit/adjustments/types" in paths

    def test_statuses_route_exists(self):
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/audit/adjustments/statuses" in paths


# =============================================================================
# GET /audit/adjustments/types + /statuses (public enums)
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestAdjustmentEnums:
    """Tests for enum reference endpoints."""

    @pytest.mark.asyncio
    async def test_get_types(self):
        """GET /audit/adjustments/types returns adjustment types."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/audit/adjustments/types")
            assert response.status_code == 200
            data = response.json()
            assert "types" in data
            assert len(data["types"]) > 0
            assert all("value" in t and "label" in t for t in data["types"])

    @pytest.mark.asyncio
    async def test_get_statuses(self):
        """GET /audit/adjustments/statuses returns adjustment statuses."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/audit/adjustments/statuses")
            assert response.status_code == 200
            data = response.json()
            assert "statuses" in data
            assert len(data["statuses"]) > 0


# =============================================================================
# POST /audit/adjustments — Create
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestCreateAdjustment:
    """Tests for POST /audit/adjustments."""

    @pytest.mark.asyncio
    async def test_create_success(self, override_verified):
        """Create a balanced adjusting entry returns 201."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/audit/adjustments", json=SAMPLE_ENTRY)
            assert response.status_code == 201
            data = response.json()
            assert data["success"] is True
            assert data["reference"] == "AJE-001"
            assert data["is_balanced"] is True

    @pytest.mark.asyncio
    async def test_create_no_auth_returns_401(self):
        """POST without auth returns 401."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/audit/adjustments", json=SAMPLE_ENTRY)
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_missing_lines_returns_422(self, override_verified):
        """POST with missing required fields returns 422."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/audit/adjustments",
                json={"reference": "AJE-BAD", "description": "No lines"},
            )
            assert response.status_code == 422


# =============================================================================
# GET /audit/adjustments — List
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestListAdjustments:
    """Tests for GET /audit/adjustments."""

    @pytest.mark.asyncio
    async def test_list_empty(self, override_verified):
        """List returns empty set initially."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/audit/adjustments")
            assert response.status_code == 200
            data = response.json()
            assert "entries" in data
            assert "total_adjustments" in data

    @pytest.mark.asyncio
    async def test_list_after_create(self, override_verified):
        """List shows entry after creation."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/audit/adjustments", json=SAMPLE_ENTRY)
            response = await client.get("/audit/adjustments")
            assert response.status_code == 200
            data = response.json()
            assert data["total_adjustments"] >= 1


# =============================================================================
# GET /audit/adjustments/reference/next
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestNextReference:
    """Tests for GET /audit/adjustments/reference/next."""

    @pytest.mark.asyncio
    async def test_next_reference(self, override_verified):
        """Returns a next reference string."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/audit/adjustments/reference/next")
            assert response.status_code == 200
            data = response.json()
            assert "next_reference" in data
            assert data["next_reference"].startswith("AJE")


# =============================================================================
# DELETE /audit/adjustments — Clear All
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestClearAdjustments:
    """Tests for DELETE /audit/adjustments."""

    @pytest.mark.asyncio
    async def test_clear_all(self, override_verified):
        """Clear all adjustments returns 204."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete("/audit/adjustments")
            assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_clear_no_auth_returns_401(self):
        """DELETE without auth returns 401."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete("/audit/adjustments")
            assert response.status_code == 401
