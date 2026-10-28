"""Sprint 848 (security review M8, M9, L1, L5): authorization gaps.

- M8: only the owner or an admin can change firm branding.
- M9: an impersonation session cannot open the Stripe billing portal.
- L1: ``POST /activity/tool-log`` attaches only an engagement the caller can see.
- L5: admin billing actions refuse a customer ID that resolves to a different
  user than the one the admin named.
"""

import io
from unittest.mock import patch

import httpx
import pytest
from fastapi import HTTPException
from starlette.requests import Request

from admin_audit_model import AdminAuditLog
from auth import (
    create_access_token,
    create_impersonation_token,
    reject_impersonation,
    require_current_user,
    require_superadmin,
    require_verified_user,
)
from database import get_db
from main import app
from models import ToolActivity, UserTier
from organization_model import Organization, OrganizationMember, OrgRole
from shared.impersonation_revocation import _reset_for_tests
from subscription_model import BillingInterval, Subscription, SubscriptionStatus


def _get() -> Request:
    return Request({"type": "http", "method": "GET", "headers": [], "path": "/", "query_string": b""})


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


@pytest.fixture
def firm(db_session, make_user):
    """An Enterprise firm with an owner, an admin and a plain member."""
    owner = make_user(email="brand_owner@firm.com", tier=UserTier.ENTERPRISE)
    org = Organization(name="Brand Firm", slug="brand-firm", owner_user_id=owner.id)
    db_session.add(org)
    db_session.flush()

    people = {"owner": owner}
    for role, email in ((OrgRole.ADMIN, "brand_admin@firm.com"), (OrgRole.MEMBER, "brand_member@firm.com")):
        people[role.value] = make_user(email=email, tier=UserTier.ENTERPRISE)
    for role, user in ((OrgRole.OWNER, owner), (OrgRole.ADMIN, people["admin"]), (OrgRole.MEMBER, people["member"])):
        db_session.add(OrganizationMember(organization_id=org.id, user_id=user.id, role=role))
        user.organization_id = org.id
    db_session.flush()
    return {"org": org, **people}


@pytest.fixture
def as_user(db_session):
    def _as(user):
        app.dependency_overrides[require_current_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session

    yield _as
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# M8: branding writes
# ---------------------------------------------------------------------------


def _png() -> bytes:
    # A real image: since Sprint 852 the logo route reads dimensions with Pillow.
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (4, 4)).save(buf, format="PNG")
    return buf.getvalue()


_PNG = _png()


async def _branding_writes(client: httpx.AsyncClient) -> list[int]:
    put = await client.put("/branding/", json={"header_text": "Not our firm"})
    with patch("shared.storage_client.upload_bytes", return_value=True):
        post = await client.post("/branding/logo", files={"file": ("logo.png", _PNG, "image/png")})
    delete = await client.delete("/branding/logo")
    return [put.status_code, post.status_code, delete.status_code]


@pytest.mark.usefixtures("bypass_csrf")
class TestBrandingWritesNeedAdmin:
    @pytest.mark.asyncio
    async def test_member_can_read_but_not_write(self, firm, as_user):
        as_user(firm["member"])
        with patch("routes.branding.check_custom_branding_access"):
            async with _client() as client:
                assert (await client.get("/branding/")).status_code == 200
                assert await _branding_writes(client) == [403, 403, 403]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("who", ["owner", "admin"])
    async def test_owner_and_admin_can_write(self, firm, as_user, who):
        as_user(firm[who])
        with patch("routes.branding.check_custom_branding_access"):
            async with _client() as client:
                assert await _branding_writes(client) == [200, 200, 200]


# ---------------------------------------------------------------------------
# M9: impersonation and the billing portal
# ---------------------------------------------------------------------------


class TestPortalRefusesImpersonation:
    @pytest.fixture(autouse=True)
    def _clean(self, db_session):
        _reset_for_tests()
        app.dependency_overrides[get_db] = lambda: db_session
        yield
        app.dependency_overrides.clear()
        _reset_for_tests()

    @pytest.fixture
    def customer(self, db_session, make_user):
        user = make_user(email="portal_customer@example.com")
        db_session.add(
            Subscription(
                user_id=user.id,
                tier="professional",
                status=SubscriptionStatus.ACTIVE,
                billing_interval=BillingInterval.MONTHLY,
                stripe_customer_id="cus_portal_test",
            )
        )
        db_session.commit()
        return user

    def test_dependency_refuses_an_impersonation_token(self, db_session, customer):
        token, _ = create_impersonation_token(customer.id, customer.email, admin_user_id=999)
        request = _get()
        user = require_current_user(request, token, db_session)
        with pytest.raises(HTTPException) as exc:
            reject_impersonation(request, user)
        assert exc.value.status_code == 403
        assert exc.value.detail["code"] == "IMPERSONATION_READ_ONLY"

    def test_dependency_allows_an_ordinary_token(self, db_session, customer):
        token, _ = create_access_token(customer.id, customer.email)
        request = _get()
        user = require_current_user(request, token, db_session)
        assert reject_impersonation(request, user).id == customer.id

    @pytest.mark.asyncio
    async def test_portal_route_refuses_impersonation(self, customer):
        token, _ = create_impersonation_token(customer.id, customer.email, admin_user_id=999)
        with patch("billing.subscription_manager.create_portal_session") as portal:
            async with _client() as client:
                r = await client.get("/billing/portal-session", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 403
        portal.assert_not_called()

    @pytest.mark.asyncio
    async def test_portal_route_still_works_for_the_customer(self, customer):
        token, _ = create_access_token(customer.id, customer.email)
        with (
            patch("billing.stripe_client.is_stripe_enabled", return_value=True),  # CI has no Stripe key
            patch("billing.subscription_manager.create_portal_session", return_value="https://billing.example/p"),
        ):
            async with _client() as client:
                r = await client.get("/billing/portal-session", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200, r.text
        assert r.json()["portal_url"] == "https://billing.example/p"


# ---------------------------------------------------------------------------
# L1: tool-log engagement_id
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("bypass_csrf")
class TestToolLogEngagement:
    async def _log(self, engagement_id: int) -> int:
        async with _client() as client:
            r = await client.post(
                "/activity/tool-log", params={"tool_name": "journal_entry_testing", "engagement_id": engagement_id}
            )
        assert r.status_code == 201, r.text
        return r.json()["id"]

    @pytest.mark.asyncio
    async def test_another_users_engagement_is_not_attached(self, db_session, make_user, make_engagement, as_user):
        me = make_user(email="toollog_me@example.com")
        other = make_user(email="toollog_other@example.com")
        theirs = make_engagement(user=other)
        as_user(me)

        row = db_session.get(ToolActivity, await self._log(theirs.id))
        assert row.engagement_id is None

    @pytest.mark.asyncio
    async def test_nonexistent_engagement_is_201_not_500(self, db_session, make_user, as_user):
        as_user(make_user(email="toollog_ghost@example.com"))
        row = db_session.get(ToolActivity, await self._log(987654))
        assert row.engagement_id is None

    @pytest.mark.asyncio
    async def test_own_engagement_is_attached(self, db_session, make_user, make_engagement, as_user):
        me = make_user(email="toollog_own@example.com")
        mine = make_engagement(user=me)
        as_user(me)

        row = db_session.get(ToolActivity, await self._log(mine.id))
        assert row.engagement_id == mine.id


# ---------------------------------------------------------------------------
# L5: admin actions name their target
# ---------------------------------------------------------------------------

_ACTIONS = [
    ("plan-override", {"new_plan": "enterprise", "reason": "r", "effective_immediately": True}),
    ("extend-trial", {"days": 7, "reason": "r"}),
    ("credit", {"amount_cents": 100, "reason": "r"}),
    ("refund", {"payment_intent_id": "pi_test", "amount_cents": 100, "reason": "r"}),
    ("cancel", {"reason": "r", "immediate": True}),
    ("revoke-sessions", {}),
]


@pytest.mark.usefixtures("bypass_csrf")
class TestAdminActionsRefuseTheWrongCustomer:
    @pytest.fixture(autouse=True)
    def _admin(self, db_session, make_user):
        admin = make_user(email="l5_admin@paciolus.com")
        admin.is_superadmin = True
        app.dependency_overrides[require_superadmin] = lambda: admin
        app.dependency_overrides[require_verified_user] = lambda: admin
        app.dependency_overrides[get_db] = lambda: db_session
        yield
        app.dependency_overrides.clear()

    @pytest.fixture
    def solo(self, db_session, make_user):
        """A solo customer (no org) plus an unrelated user whose ID is a dead org ID."""
        user = make_user(email="l5_solo@example.com", tier=UserTier.SOLO)
        sub = Subscription(
            user_id=user.id,
            tier="solo",
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
        )
        db_session.add(sub)
        db_session.commit()
        return user, sub

    @pytest.mark.asyncio
    @pytest.mark.parametrize(("action", "body"), _ACTIONS, ids=[a for a, _ in _ACTIONS])
    async def test_mismatch_is_409_and_changes_nothing(self, db_session, solo, action, body):
        # The admin meant some other customer (stale org ID 'user.id'), but
        # that ID resolves to this solo user.
        user, sub = solo
        async with _client() as client:
            r = await client.post(
                f"/internal/admin/customers/{user.id}/{action}", json={**body, "target_user_id": user.id + 1000}
            )
        assert r.status_code == 409, r.text
        assert db_session.query(AdminAuditLog).count() == 0
        db_session.refresh(sub)
        db_session.refresh(user)
        assert sub.status == SubscriptionStatus.ACTIVE
        assert user.tier == UserTier.SOLO

    @pytest.mark.asyncio
    @pytest.mark.parametrize(("action", "body"), _ACTIONS, ids=[a for a, _ in _ACTIONS])
    async def test_target_user_id_is_required(self, solo, action, body):
        user, _ = solo
        async with _client() as client:
            r = await client.post(f"/internal/admin/customers/{user.id}/{action}", json=body)
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_solo_customer_by_user_id_still_works(self, db_session, solo):
        user, _ = solo
        async with _client() as client:
            r = await client.post(
                f"/internal/admin/customers/{user.id}/plan-override",
                json={
                    "new_plan": "professional",
                    "reason": "r",
                    "effective_immediately": True,
                    "target_user_id": user.id,
                },
            )
        assert r.status_code == 200, r.text
        db_session.refresh(user)
        assert user.tier == UserTier.PROFESSIONAL
