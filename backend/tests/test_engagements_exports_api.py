"""
Tests for Engagement Export API Endpoints — Route-level integration tests.

Tests cover:
- POST /engagements/{id}/export/anomaly-summary — PDF export
- POST /engagements/{id}/export/package — ZIP export
- POST /engagements/{id}/export/convergence-csv — CSV export
- Auth enforcement (401)
- 400/404 for invalid engagements
"""

import sys
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from auth import require_current_user, require_verified_user
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
        email="eng_exports@example.com",
        name="Export Tester",
        hashed_password="$2b$12$fakehashvalue",
        tier=UserTier.PROFESSIONAL,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def override_verified(db_session, auth_user):
    """Override require_verified_user + get_db."""
    app.dependency_overrides[require_verified_user] = lambda: auth_user
    # Sprint 678: export gate (check_export_access) pulls require_current_user
    app.dependency_overrides[require_current_user] = lambda: auth_user
    app.dependency_overrides[get_db] = lambda: db_session
    yield auth_user
    app.dependency_overrides.clear()


@pytest.fixture
def override_current(db_session, auth_user):
    """Override require_current_user + get_db."""
    app.dependency_overrides[require_current_user] = lambda: auth_user
    app.dependency_overrides[get_db] = lambda: db_session
    yield auth_user
    app.dependency_overrides.clear()


@pytest.fixture
def user_engagement(db_session, auth_user, make_engagement):
    """Create an engagement owned by auth_user."""
    client = Client(
        user_id=auth_user.id,
        name="Export Client",
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


class TestEngagementExportRouteRegistration:
    """Verify engagement export routes are registered."""

    def test_anomaly_summary_route_exists(self):
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/engagements/{engagement_id}/export/anomaly-summary" in paths

    def test_package_route_exists(self):
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/engagements/{engagement_id}/export/package" in paths

    def test_convergence_csv_route_exists(self):
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/engagements/{engagement_id}/export/convergence-csv" in paths


# =============================================================================
# POST /engagements/{id}/export/convergence-csv
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestConvergenceCsvExport:
    """Tests for POST /engagements/{id}/export/convergence-csv."""

    @pytest.mark.asyncio
    async def test_convergence_csv_success(self, override_current, user_engagement):
        """Export convergence index as CSV."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(f"/engagements/{user_engagement.id}/export/convergence-csv")
            assert response.status_code == 200
            assert "text/csv" in response.headers.get("content-type", "")
            content = response.text
            assert "Account" in content
            assert "Convergence Count" in content

    @pytest.mark.asyncio
    async def test_convergence_csv_not_found(self, override_current):
        """Non-existent engagement returns 404."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/engagements/999999/export/convergence-csv")
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_convergence_csv_no_auth_returns_401(self):
        """POST without auth returns 401."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/engagements/1/export/convergence-csv")
            assert response.status_code == 401


# =============================================================================
# POST /engagements/{id}/export/anomaly-summary
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestAnomalySummaryExport:
    """Tests for POST /engagements/{id}/export/anomaly-summary."""

    @pytest.mark.asyncio
    async def test_anomaly_summary_no_auth_returns_401(self):
        """POST without auth returns 401."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/engagements/1/export/anomaly-summary")
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_anomaly_summary_invalid_engagement(self, override_verified):
        """Non-existent engagement returns 404 (not found or access denied)."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/engagements/999999/export/anomaly-summary")
            assert response.status_code == 404


# =============================================================================
# POST /engagements/{id}/export/package
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestPackageExport:
    """Tests for POST /engagements/{id}/export/package."""

    @pytest.mark.asyncio
    async def test_package_no_auth_returns_401(self):
        """POST without auth returns 401."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/engagements/1/export/package")
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_package_invalid_engagement(self, override_verified):
        """Non-existent engagement returns 404 (not found or access denied)."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/engagements/999999/export/package")
            assert response.status_code == 404
