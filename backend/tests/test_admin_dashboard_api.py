"""
Tests for Admin Dashboard API Endpoints — Route-level integration tests.

Tests cover:
- GET /admin/overview — org overview stats
- GET /admin/team-activity — filterable team activity
- GET /admin/usage-by-member — per-member upload counts
- GET /admin/export-activity-csv — CSV export of team activity
- Auth/role/entitlement enforcement (401, 403)
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
from organization_model import Organization, OrganizationMember, OrgRole

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def admin_user(db_session):
    """Create a Professional-tier user who is an org OWNER."""
    user = User(
        email="admin_dash@example.com",
        name="Admin User",
        hashed_password="$2b$12$fakehashvalue",
        tier=UserTier.PROFESSIONAL,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()

    org = Organization(
        name="Test Firm",
        slug="test-firm",
        owner_user_id=user.id,
    )
    db_session.add(org)
    db_session.flush()

    member = OrganizationMember(
        organization_id=org.id,
        user_id=user.id,
        role=OrgRole.OWNER,
    )
    db_session.add(member)
    db_session.flush()

    user.organization_id = org.id
    db_session.flush()

    return user


@pytest.fixture
def member_user(db_session, admin_user):
    """Create a user who is a regular MEMBER (not admin/owner)."""
    user = User(
        email="member_dash@example.com",
        name="Member User",
        hashed_password="$2b$12$fakehashvalue",
        tier=UserTier.PROFESSIONAL,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()

    # Get the org from admin_user
    org_member = db_session.query(OrganizationMember).filter(OrganizationMember.user_id == admin_user.id).first()

    member = OrganizationMember(
        organization_id=org_member.organization_id,
        user_id=user.id,
        role=OrgRole.MEMBER,
    )
    db_session.add(member)
    db_session.flush()

    return user


@pytest.fixture
def free_user(db_session):
    """Create a free-tier user with no org."""
    user = User(
        email="free_dash@example.com",
        name="Free User",
        hashed_password="$2b$12$fakehashvalue",
        tier=UserTier.FREE,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def override_admin(db_session, admin_user):
    """Override auth + db to return admin_user."""
    app.dependency_overrides[require_current_user] = lambda: admin_user
    app.dependency_overrides[get_db] = lambda: db_session
    yield admin_user
    app.dependency_overrides.clear()


@pytest.fixture
def override_member(db_session, member_user):
    """Override auth + db to return member_user (non-admin)."""
    app.dependency_overrides[require_current_user] = lambda: member_user
    app.dependency_overrides[get_db] = lambda: db_session
    yield member_user
    app.dependency_overrides.clear()


@pytest.fixture
def override_free(db_session, free_user):
    """Override auth + db to return free-tier user."""
    app.dependency_overrides[require_current_user] = lambda: free_user
    app.dependency_overrides[get_db] = lambda: db_session
    yield free_user
    app.dependency_overrides.clear()


# =============================================================================
# Route Registration
# =============================================================================


class TestAdminDashboardRouteRegistration:
    """Verify admin dashboard routes are registered."""

    def test_overview_route_exists(self):
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/admin/overview" in paths

    def test_team_activity_route_exists(self):
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/admin/team-activity" in paths

    def test_usage_by_member_route_exists(self):
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/admin/usage-by-member" in paths

    def test_export_activity_csv_route_exists(self):
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/admin/export-activity-csv" in paths


# =============================================================================
# GET /admin/overview
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestAdminOverview:
    """Tests for GET /admin/overview."""

    @pytest.mark.asyncio
    async def test_overview_success(self, override_admin):
        """Admin/owner gets overview stats."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/admin/overview")
            assert response.status_code == 200
            data = response.json()
            assert "total_members" in data
            assert "uploads_this_month" in data
            assert "active_members_30d" in data
            assert "tool_usage" in data
            assert "organization_name" in data
            assert data["organization_name"] == "Test Firm"

    @pytest.mark.asyncio
    async def test_overview_forbidden_for_member(self, override_member):
        """Regular member gets 403."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/admin/overview")
            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_overview_forbidden_for_free_tier(self, override_free):
        """Free-tier user with no org gets 403."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/admin/overview")
            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_overview_no_auth_returns_401(self):
        """No auth override => 401."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/admin/overview")
            assert response.status_code == 401


# =============================================================================
# GET /admin/team-activity
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestAdminTeamActivity:
    """Tests for GET /admin/team-activity."""

    @pytest.mark.asyncio
    async def test_team_activity_success(self, override_admin):
        """Admin gets team activity list."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/admin/team-activity")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_team_activity_with_filters(self, override_admin):
        """Admin can filter by days and tool_name."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/admin/team-activity", params={"days": 7, "tool_name": "trial_balance"})
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_team_activity_forbidden_for_member(self, override_member):
        """Regular member gets 403."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/admin/team-activity")
            assert response.status_code == 403


# =============================================================================
# GET /admin/usage-by-member
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestAdminUsageByMember:
    """Tests for GET /admin/usage-by-member."""

    @pytest.mark.asyncio
    async def test_usage_by_member_success(self, override_admin):
        """Admin gets per-member usage."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/admin/usage-by-member")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_usage_by_member_forbidden_for_member(self, override_member):
        """Regular member gets 403."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/admin/usage-by-member")
            assert response.status_code == 403


# =============================================================================
# GET /admin/export-activity-csv
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestAdminExportActivityCsv:
    """Tests for GET /admin/export-activity-csv."""

    @pytest.mark.asyncio
    async def test_export_csv_success(self, override_admin):
        """Admin can export CSV."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/admin/export-activity-csv")
            assert response.status_code == 200
            assert "text/csv" in response.headers.get("content-type", "")
            # CSV should have header row
            content = response.text
            assert "Date" in content
            assert "User" in content

    @pytest.mark.asyncio
    async def test_export_csv_with_days_filter(self, override_admin):
        """Admin can filter CSV export by days."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/admin/export-activity-csv", params={"days": 30})
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_export_csv_forbidden_for_member(self, override_member):
        """Regular member gets 403."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/admin/export-activity-csv")
            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_export_csv_invalid_days_param(self, override_admin):
        """Invalid days param (> 90) returns 422."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/admin/export-activity-csv", params={"days": 999})
            assert response.status_code == 422
