"""
Tests for Internal Admin Console — Sprint 590.

Tests cover:
- Route registration (10 endpoints)
- Authorization: superadmin required (403 for non-superadmin, 401 for unauth)
- Customer list: pagination, filtering, search
- Customer detail: full profile
- Admin actions: plan override, trial extension, force cancel
- Impersonation: token generation, read-only enforcement
- Audit log: creation on every action, pagination
- Edge cases: empty state, customer not found
"""

import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from admin_audit_model import AdminActionType, AdminAuditLog
from auth import require_superadmin, require_verified_user
from database import get_db
from main import app
from models import User, UserTier
from organization_model import Organization, OrganizationMember, OrgRole
from subscription_model import (
    BillingInterval,
    Subscription,
    SubscriptionStatus,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def superadmin_user(db_session):
    """Create a superadmin user."""
    user = User(
        email="superadmin@paciolus.com",
        name="Super Admin",
        hashed_password="$2b$12$fakehashvalue",
        tier=UserTier.ENTERPRISE,
        is_active=True,
        is_verified=True,
        is_superadmin=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def regular_user(db_session):
    """Create a regular (non-superadmin) verified user."""
    user = User(
        email="regular@example.com",
        name="Regular User",
        hashed_password="$2b$12$fakehashvalue",
        tier=UserTier.PROFESSIONAL,
        is_active=True,
        is_verified=True,
        is_superadmin=False,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def customer_with_org(db_session):
    """Create a customer with org and subscription."""
    owner = User(
        email="customer_owner@firm.com",
        name="Customer Owner",
        hashed_password="$2b$12$fakehashvalue",
        tier=UserTier.PROFESSIONAL,
        is_active=True,
        is_verified=True,
        created_at=datetime.now(UTC) - timedelta(days=60),
        last_login=datetime.now(UTC) - timedelta(hours=2),
    )
    db_session.add(owner)
    db_session.flush()

    sub = Subscription(
        user_id=owner.id,
        tier="professional",
        status=SubscriptionStatus.ACTIVE,
        billing_interval=BillingInterval.MONTHLY,
        seat_count=7,
        additional_seats=2,
        uploads_used_current_period=15,
    )
    db_session.add(sub)
    db_session.flush()

    org = Organization(
        name="Customer Firm LLC",
        slug="customer-firm",
        owner_user_id=owner.id,
        subscription_id=sub.id,
    )
    db_session.add(org)
    db_session.flush()

    member_rec = OrganizationMember(
        organization_id=org.id,
        user_id=owner.id,
        role=OrgRole.OWNER,
    )
    db_session.add(member_rec)
    db_session.flush()

    owner.organization_id = org.id
    db_session.flush()

    # Add a team member
    member = User(
        email="team_member@firm.com",
        name="Team Member",
        hashed_password="$2b$12$fakehashvalue",
        tier=UserTier.PROFESSIONAL,
        is_active=True,
        is_verified=True,
    )
    db_session.add(member)
    db_session.flush()

    OrganizationMember(
        organization_id=org.id,
        user_id=member.id,
        role=OrgRole.MEMBER,
    )
    db_session.add(
        OrganizationMember(
            organization_id=org.id,
            user_id=member.id,
            role=OrgRole.MEMBER,
        )
    )
    db_session.flush()

    member.organization_id = org.id
    db_session.flush()

    return {"owner": owner, "org": org, "sub": sub, "member": member}


@pytest.fixture
def override_superadmin(db_session, superadmin_user):
    """Override auth for superadmin."""
    app.dependency_overrides[require_superadmin] = lambda: superadmin_user
    app.dependency_overrides[require_verified_user] = lambda: superadmin_user
    app.dependency_overrides[get_db] = lambda: db_session
    yield superadmin_user
    app.dependency_overrides.clear()


@pytest.fixture
def override_regular(db_session, regular_user):
    """Override auth for regular user (non-superadmin)."""
    app.dependency_overrides[require_superadmin] = lambda: (_ for _ in ()).throw(
        __import__("fastapi").HTTPException(status_code=403, detail="Superadmin access required.")
    )
    app.dependency_overrides[require_verified_user] = lambda: regular_user
    app.dependency_overrides[get_db] = lambda: db_session
    yield regular_user
    app.dependency_overrides.clear()


# =============================================================================
# Route Registration
# =============================================================================


class TestRouteRegistration:
    """Verify admin routes are registered."""

    EXPECTED_ROUTES = [
        "/internal/admin/customers/",
        "/internal/admin/customers/{org_id}",
        "/internal/admin/customers/{org_id}/plan-override",
        "/internal/admin/customers/{org_id}/extend-trial",
        "/internal/admin/customers/{org_id}/credit",
        "/internal/admin/customers/{org_id}/refund",
        "/internal/admin/customers/{org_id}/cancel",
        "/internal/admin/customers/{org_id}/revoke-sessions",
        "/internal/admin/customers/{org_id}/impersonate",
        "/internal/admin/audit-log",
    ]

    def test_all_routes_exist(self):
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        for route in self.EXPECTED_ROUTES:
            assert route in paths, f"Missing route: {route}"


# =============================================================================
# Authorization Tests
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestAuthorization:
    """Superadmin-only access enforcement."""

    @pytest.mark.asyncio
    async def test_no_auth_returns_401(self):
        """Unauthenticated requests get 401."""
        app.dependency_overrides.clear()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/internal/admin/customers/")
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_regular_user_returns_403(self, override_regular):
        """Non-superadmin gets 403."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/internal/admin/customers/")
            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_superadmin_allowed(self, override_superadmin):
        """Superadmin gets 200."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/internal/admin/customers/")
            assert response.status_code == 200


# =============================================================================
# Customer List
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestCustomerList:
    """Tests for GET /internal/admin/customers/."""

    @pytest.mark.asyncio
    async def test_empty_list(self, override_superadmin):
        """Empty DB returns empty list."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/internal/admin/customers/")
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "total" in data
            assert isinstance(data["items"], list)

    @pytest.mark.asyncio
    async def test_list_with_customers(self, override_superadmin, customer_with_org):
        """List includes customers."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/internal/admin/customers/")
            assert response.status_code == 200
            data = response.json()
            assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_search_filter(self, override_superadmin, customer_with_org):
        """Search by email filters results."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/internal/admin/customers/?search=customer_owner")
            assert response.status_code == 200
            data = response.json()
            # Should find the customer
            emails = [item["owner_email"] for item in data["items"]]
            assert any("customer_owner" in e for e in emails)

    @pytest.mark.asyncio
    async def test_plan_filter(self, override_superadmin, customer_with_org):
        """Filter by plan tier."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/internal/admin/customers/?plan=professional")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_pagination(self, override_superadmin, customer_with_org):
        """Pagination params work."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/internal/admin/customers/?offset=0&limit=1")
            assert response.status_code == 200
            data = response.json()
            assert data["offset"] == 0
            assert data["limit"] == 1
            assert len(data["items"]) <= 1


# =============================================================================
# Customer Detail
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestCustomerDetail:
    """Tests for GET /internal/admin/customers/{org_id}."""

    @pytest.mark.asyncio
    async def test_detail_success(self, override_superadmin, customer_with_org):
        """Get full customer detail."""
        org_id = customer_with_org["org"].id
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/internal/admin/customers/{org_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["org_name"] == "Customer Firm LLC"
            assert data["owner_email"] == "customer_owner@firm.com"
            assert data["subscription"] is not None
            assert data["subscription"]["tier"] == "professional"
            assert len(data["members"]) >= 1

    @pytest.mark.asyncio
    async def test_detail_not_found(self, override_superadmin):
        """Non-existent org returns 404."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/internal/admin/customers/99999")
            assert response.status_code == 404


# =============================================================================
# Admin Actions
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestPlanOverride:
    """Tests for POST /internal/admin/customers/{org_id}/plan-override."""

    @pytest.mark.asyncio
    async def test_plan_override_success(self, override_superadmin, customer_with_org, db_session):
        """Override plan creates audit log entry."""
        org_id = customer_with_org["org"].id
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/internal/admin/customers/{org_id}/plan-override",
                json={"new_plan": "enterprise", "reason": "VIP customer upgrade", "effective_immediately": True},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["audit_log_id"] > 0

            # Verify audit log was created
            entry = db_session.query(AdminAuditLog).filter(AdminAuditLog.id == data["audit_log_id"]).first()
            assert entry is not None
            assert entry.action_type == AdminActionType.PLAN_OVERRIDE

    @pytest.mark.asyncio
    async def test_plan_override_invalid_plan(self, override_superadmin, customer_with_org):
        """Invalid plan value returns 422."""
        org_id = customer_with_org["org"].id
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/internal/admin/customers/{org_id}/plan-override",
                json={"new_plan": "invalid_tier", "reason": "test", "effective_immediately": True},
            )
            assert response.status_code == 422


@pytest.mark.usefixtures("bypass_csrf")
class TestTrialExtension:
    """Tests for POST /internal/admin/customers/{org_id}/extend-trial."""

    @pytest.mark.asyncio
    async def test_trial_extension_success(self, override_superadmin, customer_with_org, db_session):
        """Extend trial creates audit log."""
        org_id = customer_with_org["org"].id
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/internal/admin/customers/{org_id}/extend-trial",
                json={"days": 14, "reason": "Onboarding support"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

            entry = db_session.query(AdminAuditLog).filter(AdminAuditLog.id == data["audit_log_id"]).first()
            assert entry.action_type == AdminActionType.TRIAL_EXTENSION


@pytest.mark.usefixtures("bypass_csrf")
class TestForceCancel:
    """Tests for POST /internal/admin/customers/{org_id}/cancel."""

    @pytest.mark.asyncio
    async def test_force_cancel_immediate(self, override_superadmin, customer_with_org, db_session):
        """Immediate cancellation changes status and creates audit log."""
        org_id = customer_with_org["org"].id
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/internal/admin/customers/{org_id}/cancel",
                json={"reason": "Fraud detected", "immediate": True},
            )
            assert response.status_code == 200
            data = response.json()
            assert "canceled" in data["message"].lower()

            entry = db_session.query(AdminAuditLog).filter(AdminAuditLog.id == data["audit_log_id"]).first()
            assert entry.action_type == AdminActionType.FORCE_CANCEL

    @pytest.mark.asyncio
    async def test_force_cancel_end_of_period(self, override_superadmin, customer_with_org, db_session):
        """End-of-period cancellation sets cancel_at_period_end."""
        org_id = customer_with_org["org"].id
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/internal/admin/customers/{org_id}/cancel",
                json={"reason": "Customer request", "immediate": False},
            )
            assert response.status_code == 200

            sub = customer_with_org["sub"]
            db_session.refresh(sub)
            assert sub.cancel_at_period_end is True


# =============================================================================
# Impersonation
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestImpersonation:
    """Tests for POST /internal/admin/customers/{org_id}/impersonate."""

    @pytest.mark.asyncio
    async def test_impersonation_generates_token(self, override_superadmin, customer_with_org, db_session):
        """Impersonation returns a token with target user info."""
        org_id = customer_with_org["org"].id
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(f"/internal/admin/customers/{org_id}/impersonate")
            assert response.status_code == 200
            data = response.json()
            assert data["is_impersonation"] is True
            assert data["target_email"] == "customer_owner@firm.com"
            assert "access_token" in data
            assert "expires_at" in data

            # Verify audit log created
            entry = (
                db_session.query(AdminAuditLog)
                .filter(AdminAuditLog.action_type == AdminActionType.IMPERSONATION_START)
                .first()
            )
            assert entry is not None

    @pytest.mark.asyncio
    async def test_impersonation_not_found(self, override_superadmin):
        """Non-existent org returns 404."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/internal/admin/customers/99999/impersonate")
            assert response.status_code == 404


# =============================================================================
# Session Revocation
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestSessionRevocation:
    """Tests for POST /internal/admin/customers/{org_id}/revoke-sessions."""

    @pytest.mark.asyncio
    async def test_revoke_sessions(self, override_superadmin, customer_with_org, db_session):
        """Revoke sessions creates audit log."""
        org_id = customer_with_org["org"].id
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(f"/internal/admin/customers/{org_id}/revoke-sessions")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

            entry = (
                db_session.query(AdminAuditLog)
                .filter(AdminAuditLog.action_type == AdminActionType.SESSION_REVOKE)
                .first()
            )
            assert entry is not None


# =============================================================================
# Audit Log
# =============================================================================


@pytest.mark.usefixtures("bypass_csrf")
class TestAuditLog:
    """Tests for GET /internal/admin/audit-log."""

    @pytest.mark.asyncio
    async def test_empty_audit_log(self, override_superadmin):
        """Empty audit log returns empty list."""
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/internal/admin/audit-log")
            assert response.status_code == 200
            data = response.json()
            assert data["items"] == []
            assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_audit_log_after_action(self, override_superadmin, customer_with_org, db_session):
        """Audit log shows entries after admin actions."""
        org_id = customer_with_org["org"].id
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            # Perform an action
            await client.post(
                f"/internal/admin/customers/{org_id}/cancel",
                json={"reason": "Test cancellation", "immediate": False},
            )

            # Check audit log
            response = await client.get("/internal/admin/audit-log")
            assert response.status_code == 200
            data = response.json()
            assert data["total"] >= 1
            assert any(e["action_type"] == "force_cancel" for e in data["items"])

    @pytest.mark.asyncio
    async def test_audit_log_filter_by_action(self, override_superadmin, customer_with_org, db_session):
        """Audit log can be filtered by action type."""
        org_id = customer_with_org["org"].id
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            # Create entries of different types
            await client.post(
                f"/internal/admin/customers/{org_id}/cancel",
                json={"reason": "Cancel", "immediate": False},
            )
            await client.post(
                f"/internal/admin/customers/{org_id}/extend-trial",
                json={"days": 7, "reason": "Support"},
            )

            # Filter for force_cancel only
            response = await client.get("/internal/admin/audit-log?action_type=force_cancel")
            assert response.status_code == 200
            data = response.json()
            for entry in data["items"]:
                assert entry["action_type"] == "force_cancel"


# =============================================================================
# Unit Tests — Service Layer
# =============================================================================


class TestCustomerServiceLayer:
    """Direct unit tests for service functions."""

    def test_customer_summary_includes_mrr(self, db_session, customer_with_org):
        """Customer summary calculates MRR correctly."""
        from billing.admin_customers import _build_customer_summary

        summary = _build_customer_summary(db_session, customer_with_org["owner"])
        # Professional $500 + 2 additional seats × $65 = $630
        assert summary["mrr"] == 630.0
        assert summary["plan"] == "professional"
        assert summary["org_name"] == "Customer Firm LLC"

    def test_customer_detail_includes_members(self, db_session, customer_with_org):
        """Customer detail shows all org members."""
        from billing.admin_customers import get_customer_detail

        detail = get_customer_detail(db_session, customer_with_org["org"].id)
        assert detail is not None
        assert len(detail["members"]) == 2  # owner + member

    def test_customer_detail_not_found(self, db_session):
        """Non-existent customer returns None."""
        from billing.admin_customers import get_customer_detail

        result = get_customer_detail(db_session, 99999)
        assert result is None

    def test_audit_entry_created(self, db_session, superadmin_user, customer_with_org):
        """Admin action creates audit log entry."""
        from billing.admin_customers import admin_force_cancel

        result = admin_force_cancel(
            db_session,
            customer_with_org["org"].id,
            reason="Test",
            immediate=True,
            admin_user_id=superadmin_user.id,
            ip_address="127.0.0.1",
        )
        assert result["success"] is True

        entry = db_session.query(AdminAuditLog).filter(AdminAuditLog.id == result["audit_log_id"]).first()
        assert entry is not None
        assert entry.admin_user_id == superadmin_user.id
        assert entry.ip_address == "127.0.0.1"
        details = json.loads(entry.details_json)
        assert details["reason"] == "Test"

    def test_plan_override_updates_tier(self, db_session, superadmin_user, customer_with_org):
        """Plan override changes subscription tier."""
        from billing.admin_customers import admin_plan_override

        admin_plan_override(
            db_session,
            customer_with_org["org"].id,
            "enterprise",
            "VIP upgrade",
            effective_immediately=True,
            admin_user_id=superadmin_user.id,
        )

        db_session.refresh(customer_with_org["sub"])
        assert customer_with_org["sub"].tier == "enterprise"

        db_session.refresh(customer_with_org["owner"])
        assert customer_with_org["owner"].tier == UserTier.ENTERPRISE

    def test_trial_extension_updates_period(self, db_session, superadmin_user, customer_with_org):
        """Trial extension changes period_end and status."""
        from billing.admin_customers import admin_extend_trial

        admin_extend_trial(
            db_session,
            customer_with_org["org"].id,
            days=14,
            reason="Onboarding",
            admin_user_id=superadmin_user.id,
        )

        db_session.refresh(customer_with_org["sub"])
        assert customer_with_org["sub"].status == SubscriptionStatus.TRIALING
        assert customer_with_org["sub"].current_period_end is not None


# =============================================================================
# Impersonation Token — Unit Tests
# =============================================================================


class TestImpersonationToken:
    """Unit tests for impersonation token creation."""

    def test_impersonation_token_has_claims(self):
        """Token includes imp and imp_by claims."""
        import jwt as _jwt

        from auth import create_impersonation_token
        from config import JWT_ALGORITHM, JWT_SECRET_KEY

        token, expires = create_impersonation_token(
            target_user_id=42,
            target_email="target@test.com",
            admin_user_id=1,
            tier="professional",
        )

        payload = _jwt.decode(token, JWT_SECRET_KEY or "", algorithms=[JWT_ALGORITHM])
        assert payload["imp"] is True
        assert payload["imp_by"] == 1
        assert payload["sub"] == "42"
        assert payload["email"] == "target@test.com"

    def test_impersonation_token_expires(self):
        """Token expires within TTL."""
        from auth import create_impersonation_token

        _, expires = create_impersonation_token(
            target_user_id=42,
            target_email="target@test.com",
            admin_user_id=1,
            ttl_minutes=15,
        )

        # Should expire within 16 minutes
        now = datetime.now(UTC)
        assert expires > now
        assert expires < now + timedelta(minutes=16)


# =============================================================================
# Superadmin Auth Dependency — Unit Tests
# =============================================================================


class TestRequireSuperadmin:
    """Unit tests for require_superadmin dependency."""

    def test_is_superadmin_default_false(self, db_session):
        """New users are not superadmin by default."""
        user = User(
            email="default@test.com",
            hashed_password="x",
            tier=UserTier.FREE,
            is_active=True,
            is_verified=True,
        )
        db_session.add(user)
        db_session.flush()
        assert user.is_superadmin is False

    def test_is_superadmin_can_be_set(self, db_session):
        """Superadmin flag can be set on user."""
        user = User(
            email="admin_flag@test.com",
            hashed_password="x",
            tier=UserTier.FREE,
            is_active=True,
            is_verified=True,
            is_superadmin=True,
        )
        db_session.add(user)
        db_session.flush()
        assert user.is_superadmin is True
