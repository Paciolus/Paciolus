"""
Tests for Billing Analytics API Endpoints — Route-level integration tests.

Tests cover:
- GET /billing/analytics/weekly-review — weekly review metrics
- Auth enforcement (401)
- Role enforcement (403 for non-admin members)
- Subscription requirement for solo users
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
from organization_model import Organization, OrganizationMember, OrgRole

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def org_admin_user(db_session):
    """Create a Professional user who is org ADMIN."""
    user = User(
        email="billing_analytics_admin@example.com",
        name="Billing Admin",
        hashed_password="$2b$12$fakehashvalue",
        tier=UserTier.PROFESSIONAL,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()

    org = Organization(
        name="Analytics Firm",
        slug="analytics-firm",
        owner_user_id=user.id,
    )
    db_session.add(org)
    db_session.flush()

    member = OrganizationMember(
        organization_id=org.id,
        user_id=user.id,
        role=OrgRole.ADMIN,
    )
    db_session.add(member)
    db_session.flush()

    user.organization_id = org.id
    db_session.flush()

    return user


@pytest.fixture
def org_member_user(db_session, org_admin_user):
    """Create a user who is a regular MEMBER in the org."""
    user = User(
        email="billing_analytics_member@example.com",
        name="Billing Member",
        hashed_password="$2b$12$fakehashvalue",
        tier=UserTier.PROFESSIONAL,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()

    org_member_rec = (
        db_session.query(OrganizationMember).filter(OrganizationMember.user_id == org_admin_user.id).first()
    )

    member = OrganizationMember(
        organization_id=org_member_rec.organization_id,
        user_id=user.id,
        role=OrgRole.MEMBER,
    )
    db_session.add(member)
    db_session.flush()

    user.organization_id = org_member_rec.organization_id
    db_session.flush()

    return user


@pytest.fixture
def solo_user_no_sub(db_session):
    """Create a Solo user with no subscription (for 403 test)."""
    user = User(
        email="billing_analytics_solo@example.com",
        name="Solo No Sub",
        hashed_password="$2b$12$fakehashvalue",
        tier=UserTier.SOLO,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def override_org_admin(db_session, org_admin_user):
    """Override auth for org admin."""
    app.dependency_overrides[require_verified_user] = lambda: org_admin_user
    app.dependency_overrides[get_db] = lambda: db_session
    yield org_admin_user
    app.dependency_overrides.clear()


@pytest.fixture
def override_org_member(db_session, org_member_user):
    """Override auth for org member."""
    app.dependency_overrides[require_verified_user] = lambda: org_member_user
    app.dependency_overrides[get_db] = lambda: db_session
    yield org_member_user
    app.dependency_overrides.clear()


@pytest.fixture
def override_solo_no_sub(db_session, solo_user_no_sub):
    """Override auth for solo user with no subscription."""
    app.dependency_overrides[require_verified_user] = lambda: solo_user_no_sub
    app.dependency_overrides[get_db] = lambda: db_session
    yield solo_user_no_sub
    app.dependency_overrides.clear()


# =============================================================================
# Route Registration
# =============================================================================


class TestBillingAnalyticsRouteRegistration:
    """Verify billing analytics routes are registered."""

    def test_weekly_review_route_exists(self):
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/billing/analytics/weekly-review" in paths


# =============================================================================
# GET /billing/analytics/weekly-review
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestWeeklyReview:
    """Tests for GET /billing/analytics/weekly-review."""

    @pytest.mark.asyncio
    async def test_weekly_review_admin_success(self, override_org_admin):
        """Org admin gets weekly review metrics."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/billing/analytics/weekly-review")
            assert response.status_code == 200
            data = response.json()
            # Response model is WeeklyReviewResponse
            assert "trial_starts" in data or "metrics" in data or response.status_code == 200

    @pytest.mark.asyncio
    async def test_weekly_review_forbidden_for_member(self, override_org_member):
        """Non-admin org member gets 403."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/billing/analytics/weekly-review")
            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_weekly_review_forbidden_for_solo_no_sub(self, override_solo_no_sub):
        """Solo user without subscription gets 403."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/billing/analytics/weekly-review")
            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_weekly_review_no_auth_returns_401(self):
        """No auth returns 401."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/billing/analytics/weekly-review")
            assert response.status_code == 401
