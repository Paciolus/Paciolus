"""
Tests for Engagement Analytics API Endpoints — Route-level integration tests.

Tests cover:
- GET /engagements/{id}/materiality — materiality cascade
- GET /engagements/{id}/tool-runs — tool run list
- GET /engagements/{id}/workpaper-index — workpaper index
- GET /engagements/{id}/convergence — convergence index
- GET /engagements/{id}/tool-run-trends — tool run trends
- Auth enforcement (401)
- 404 for non-existent engagements
"""

import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from auth import require_current_user
from database import get_db
from main import app
from models import Client, Industry, User, UserTier

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def auth_user(db_session):
    """Create a verified Professional user."""
    user = User(
        email="eng_analytics@example.com",
        name="Analytics Tester",
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
def user_engagement(db_session, auth_user, make_engagement):
    """Create an engagement owned by auth_user."""
    client = Client(
        user_id=auth_user.id,
        name="Analytics Client",
        industry=Industry.TECHNOLOGY,
        fiscal_year_end="12-31",
    )
    db_session.add(client)
    db_session.flush()

    engagement = make_engagement(client=client, user=auth_user)
    return engagement


# =============================================================================
# Route Registration
# =============================================================================


class TestEngagementAnalyticsRouteRegistration:
    """Verify engagement analytics routes are registered."""

    def test_materiality_route_exists(self):
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/engagements/{engagement_id}/materiality" in paths

    def test_tool_runs_route_exists(self):
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/engagements/{engagement_id}/tool-runs" in paths

    def test_workpaper_index_route_exists(self):
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/engagements/{engagement_id}/workpaper-index" in paths

    def test_convergence_route_exists(self):
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/engagements/{engagement_id}/convergence" in paths

    def test_tool_run_trends_route_exists(self):
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/engagements/{engagement_id}/tool-run-trends" in paths


# =============================================================================
# GET /engagements/{id}/materiality
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestMateriality:
    """Tests for GET /engagements/{id}/materiality."""

    @pytest.mark.asyncio
    async def test_materiality_success(self, override_auth, user_engagement):
        """Get materiality cascade for engagement."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/engagements/{user_engagement.id}/materiality")
            assert response.status_code == 200
            data = response.json()
            assert "overall_materiality" in data
            assert "performance_materiality" in data
            assert "trivial_threshold" in data

    @pytest.mark.asyncio
    async def test_materiality_not_found(self, override_auth):
        """Non-existent engagement returns 404."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/engagements/999999/materiality")
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_materiality_no_auth_returns_401(self):
        """No auth returns 401."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/engagements/1/materiality")
            assert response.status_code == 401


# =============================================================================
# GET /engagements/{id}/tool-runs
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestToolRuns:
    """Tests for GET /engagements/{id}/tool-runs."""

    @pytest.mark.asyncio
    async def test_tool_runs_success(self, override_auth, user_engagement):
        """Get tool runs for engagement (may be empty)."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/engagements/{user_engagement.id}/tool-runs")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_tool_runs_not_found(self, override_auth):
        """Non-existent engagement returns 404."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/engagements/999999/tool-runs")
            assert response.status_code == 404


# =============================================================================
# GET /engagements/{id}/convergence
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestConvergence:
    """Tests for GET /engagements/{id}/convergence."""

    @pytest.mark.asyncio
    async def test_convergence_success(self, override_auth, user_engagement):
        """Get convergence index for engagement."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/engagements/{user_engagement.id}/convergence")
            assert response.status_code == 200
            data = response.json()
            assert "engagement_id" in data
            assert "total_accounts" in data
            assert "tools_covered" in data
            assert "items" in data

    @pytest.mark.asyncio
    async def test_convergence_not_found(self, override_auth):
        """Non-existent engagement returns 404."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/engagements/999999/convergence")
            assert response.status_code == 404


# =============================================================================
# GET /engagements/{id}/tool-run-trends
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestToolRunTrends:
    """Tests for GET /engagements/{id}/tool-run-trends."""

    @pytest.mark.asyncio
    async def test_trends_success(self, override_auth, user_engagement):
        """Get tool run trends for engagement."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/engagements/{user_engagement.id}/tool-run-trends")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_trends_not_found(self, override_auth):
        """Non-existent engagement returns 404."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/engagements/999999/tool-run-trends")
            assert response.status_code == 404
