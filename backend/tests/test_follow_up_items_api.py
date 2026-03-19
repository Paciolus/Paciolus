"""
Tests for Follow-Up Items API Endpoints — Route-level integration tests.

Tests cover:
- POST /engagements/{id}/follow-up-items — create item
- GET /engagements/{id}/follow-up-items — list items
- GET /engagements/{id}/follow-up-items/summary — summary stats
- PUT /follow-up-items/{id} — update item
- DELETE /follow-up-items/{id} — delete item
- GET /engagements/{id}/follow-up-items/my-items — assigned items
- GET /engagements/{id}/follow-up-items/unassigned — unassigned items
- POST /follow-up-items/{id}/comments — create comment
- GET /follow-up-items/{id}/comments — list comments
- Auth enforcement (401)
"""

import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from auth import require_current_user
from database import get_db
from main import app
from models import User, UserTier

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def auth_user(db_session):
    """Create a verified user for follow-up item tests."""
    user = User(
        email="followup_api@example.com",
        name="Follow-Up Tester",
        hashed_password="$2b$12$fakehashvalue",
        tier=UserTier.PROFESSIONAL,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def override_auth(db_session, auth_user):
    """Override auth + db."""
    app.dependency_overrides[require_current_user] = lambda: auth_user
    app.dependency_overrides[get_db] = lambda: db_session
    yield auth_user
    app.dependency_overrides.clear()


@pytest.fixture
def engagement_with_item(db_session, auth_user, make_engagement, make_follow_up_item):
    """Create an engagement with a follow-up item owned by auth_user."""
    from models import Client, Industry

    client = Client(
        user_id=auth_user.id,
        name="Follow-Up Client",
        industry=Industry.TECHNOLOGY,
        fiscal_year_end="12-31",
    )
    db_session.add(client)
    db_session.flush()

    engagement = make_engagement(client=client, user=auth_user)
    item = make_follow_up_item(engagement=engagement)
    return engagement, item


# =============================================================================
# Route Registration
# =============================================================================


class TestFollowUpRouteRegistration:
    """Verify follow-up item routes are registered."""

    def test_create_route_exists(self):
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/engagements/{engagement_id}/follow-up-items" in paths

    def test_summary_route_exists(self):
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/engagements/{engagement_id}/follow-up-items/summary" in paths

    def test_update_route_exists(self):
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/follow-up-items/{item_id}" in paths

    def test_comments_route_exists(self):
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/follow-up-items/{item_id}/comments" in paths


# =============================================================================
# POST /engagements/{id}/follow-up-items
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestCreateFollowUpItem:
    """Tests for POST /engagements/{id}/follow-up-items."""

    @pytest.mark.asyncio
    async def test_create_success(self, override_auth, engagement_with_item):
        """Create a follow-up item returns 201."""
        engagement, _ = engagement_with_item
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/engagements/{engagement.id}/follow-up-items",
                json={
                    "description": "New follow-up item via API",
                    "tool_source": "trial_balance",
                    "severity": "medium",
                },
            )
            assert response.status_code == 201
            data = response.json()
            assert data["description"] == "New follow-up item via API"
            assert data["engagement_id"] == engagement.id

    @pytest.mark.asyncio
    async def test_create_no_auth_returns_401(self):
        """POST without auth returns 401."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/engagements/1/follow-up-items",
                json={"description": "Test", "tool_source": "trial_balance"},
            )
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_invalid_engagement(self, override_auth):
        """POST with non-existent engagement returns 400 (ValueError from manager)."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/engagements/999999/follow-up-items",
                json={"description": "Test", "tool_source": "trial_balance"},
            )
            assert response.status_code == 400


# =============================================================================
# GET /engagements/{id}/follow-up-items
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestListFollowUpItems:
    """Tests for GET /engagements/{id}/follow-up-items."""

    @pytest.mark.asyncio
    async def test_list_success(self, override_auth, engagement_with_item):
        """List follow-up items for an engagement."""
        engagement, _ = engagement_with_item
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/engagements/{engagement.id}/follow-up-items")
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "total_count" in data

    @pytest.mark.asyncio
    async def test_list_no_auth_returns_401(self):
        """GET without auth returns 401."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/engagements/1/follow-up-items")
            assert response.status_code == 401


# =============================================================================
# GET /engagements/{id}/follow-up-items/summary
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestFollowUpSummary:
    """Tests for GET /engagements/{id}/follow-up-items/summary."""

    @pytest.mark.asyncio
    async def test_summary_success(self, override_auth, engagement_with_item):
        """Get summary stats for follow-up items."""
        engagement, _ = engagement_with_item
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/engagements/{engagement.id}/follow-up-items/summary")
            assert response.status_code == 200
            data = response.json()
            assert "total_count" in data


# =============================================================================
# GET /engagements/{id}/follow-up-items/my-items
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestMyItems:
    """Tests for GET /engagements/{id}/follow-up-items/my-items."""

    @pytest.mark.asyncio
    async def test_my_items_success(self, override_auth, engagement_with_item):
        """Get items assigned to current user."""
        engagement, _ = engagement_with_item
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/engagements/{engagement.id}/follow-up-items/my-items")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)


# =============================================================================
# GET /engagements/{id}/follow-up-items/unassigned
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestUnassignedItems:
    """Tests for GET /engagements/{id}/follow-up-items/unassigned."""

    @pytest.mark.asyncio
    async def test_unassigned_items_success(self, override_auth, engagement_with_item):
        """Get unassigned items for an engagement."""
        engagement, _ = engagement_with_item
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/engagements/{engagement.id}/follow-up-items/unassigned")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)


# =============================================================================
# DELETE /follow-up-items/{id}
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestDeleteFollowUpItem:
    """Tests for DELETE /follow-up-items/{id}."""

    @pytest.mark.asyncio
    async def test_delete_not_found(self, override_auth):
        """Delete non-existent item returns 404."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete("/follow-up-items/999999")
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_no_auth_returns_401(self):
        """DELETE without auth returns 401."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete("/follow-up-items/1")
            assert response.status_code == 401
