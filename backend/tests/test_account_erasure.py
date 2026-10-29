"""Sprint 844: self-service account deletion and data export.

The Privacy Policy promised deletion "immediate and irreversible" and it did
not exist. These tests build an account with data in every table the user
owns, erase it, and check that nothing owned survives while unrelated users,
anonymised billing history and the security log do.
"""

from typing import Any

import httpx
import pytest
from sqlalchemy import func, select

from auth import create_access_token, hash_password
from database import Base, get_db
from main import app
from models import ActivityLog, DiagnosticSummary, User
from security_event_model import SecurityEvent
from services.account_erasure import (
    ErasureBlocked,
    ErasureProviderError,
    check_erasable,
    erase_account,
    export_account,
)
from subscription_model import BillingEvent, BillingEventType

PASSWORD = "Correct-Horse-Battery-9"


def _count(db, table: str, **where: Any) -> int:
    t = Base.metadata.tables[table]
    q = select(func.count()).select_from(t)
    for col, val in where.items():
        q = q.where(t.c[col] == val)
    return int(db.execute(q).scalar() or 0)


@pytest.fixture
def populated(
    db_session,
    make_user,
    make_client,
    make_engagement,
    make_tool_run,
    make_follow_up_item,
    make_comment,
    make_refresh_token,
):
    user = make_user(email="erase_me@example.com", hashed_password=hash_password(PASSWORD))
    bystander = make_user(email="bystander@example.com")
    client = make_client(user=user, name="Erase Me Client")
    engagement = make_engagement(client=client, user=user)
    run = make_tool_run(engagement=engagement)
    item = make_follow_up_item(engagement=engagement, tool_run=run)
    make_comment(follow_up_item=item, user=user)
    make_refresh_token(user=user)
    db_session.add(DiagnosticSummary(client_id=client.id, user_id=user.id))
    db_session.add(
        ActivityLog(
            user_id=user.id,
            filename_hash="abc",
            record_count=1,
            total_debits=1,
            total_credits=1,
            materiality_threshold=1,
            was_balanced=True,
        )
    )
    db_session.add(BillingEvent(user_id=user.id, event_type=BillingEventType.SUBSCRIPTION_CREATED))
    db_session.commit()
    return {"user": user, "bystander": bystander, "client": client, "engagement": engagement}


class TestErase:
    def test_everything_owned_is_gone(self, db_session, populated):
        user_id = populated["user"].id
        engagement_id = populated["engagement"].id
        erase_account(db_session, populated["user"])
        assert _count(db_session, "users", id=user_id) == 0
        for table in ("clients", "diagnostic_summaries", "activity_logs", "refresh_tokens", "tool_activities"):
            assert _count(db_session, table, user_id=user_id) == 0, table
        for table in ("tool_runs", "follow_up_items", "analytical_expectations", "uncorrected_misstatements"):
            assert _count(db_session, table, engagement_id=engagement_id) == 0, table
        assert _count(db_session, "engagements", id=engagement_id) == 0
        assert _count(db_session, "follow_up_item_comments", user_id=user_id) == 0

    def test_billing_history_is_kept_but_unlinked(self, db_session, populated):
        before = _count(db_session, "billing_events")
        user_id = populated["user"].id
        erase_account(db_session, populated["user"])
        assert _count(db_session, "billing_events") == before
        assert _count(db_session, "billing_events", user_id=user_id) == 0

    def test_other_users_are_untouched(self, db_session, populated):
        bystander_id = populated["bystander"].id
        erase_account(db_session, populated["user"])
        assert _count(db_session, "users", id=bystander_id) == 1

    def test_the_erasure_is_recorded_without_the_user(self, db_session, populated):
        erase_account(db_session, populated["user"])
        events = db_session.query(SecurityEvent).filter(SecurityEvent.event_type == "account_erased").all()
        assert len(events) == 1 and events[0].user_id is None

    def test_stripe_failure_deletes_nothing(self, db_session, populated, monkeypatch):
        import services.account_erasure as mod

        def boom(*_a, **_k):
            raise ErasureProviderError("stripe down")

        monkeypatch.setattr(mod, "_cancel_stripe", boom)
        user_id = populated["user"].id
        with pytest.raises(ErasureProviderError):
            erase_account(db_session, populated["user"])
        assert _count(db_session, "users", id=user_id) == 1
        assert _count(db_session, "clients", user_id=user_id) == 1


class TestStripeLinkage:
    def test_live_subscription_with_stripe_disabled_deletes_nothing(self, db_session, populated, monkeypatch):
        """PR #236 review: Stripe unconfigured is not a cancellation."""
        from subscription_model import BillingInterval, Subscription, SubscriptionStatus

        user_id = populated["user"].id
        db_session.add(
            Subscription(
                user_id=user_id,
                tier="solo",
                status=SubscriptionStatus.ACTIVE,
                billing_interval=BillingInterval.MONTHLY,
                stripe_subscription_id="sub_live_123",
            )
        )
        db_session.commit()
        monkeypatch.setattr("billing.stripe_client.is_stripe_enabled", lambda: False)
        with pytest.raises(ErasureProviderError):
            erase_account(db_session, populated["user"])
        assert _count(db_session, "users", id=user_id) == 1
        assert _count(db_session, "subscriptions", user_id=user_id) == 1


class TestRefusals:
    def test_superadmin_is_refused(self, db_session, make_user):
        admin = make_user(email="erase_admin@example.com")
        admin.is_superadmin = True
        db_session.commit()
        with pytest.raises(ErasureBlocked) as exc:
            check_erasable(db_session, admin)
        assert exc.value.code == "ERASURE_SUPERADMIN"

    def test_owner_of_an_org_with_members_is_refused(self, db_session, make_user):
        from organization_model import Organization, OrganizationMember, OrgRole

        owner = make_user(email="erase_owner@example.com")
        member = make_user(email="erase_member@example.com")
        org = Organization(name="Firm", slug="firm-erase", owner_user_id=owner.id)
        db_session.add(org)
        db_session.flush()
        db_session.add(OrganizationMember(organization_id=org.id, user_id=owner.id, role=OrgRole.OWNER))
        db_session.add(OrganizationMember(organization_id=org.id, user_id=member.id, role=OrgRole.MEMBER))
        db_session.commit()
        with pytest.raises(ErasureBlocked, match="other members") as exc:
            check_erasable(db_session, owner)
        assert exc.value.code == "ERASURE_ORG_HAS_MEMBERS"

    def test_sole_owner_takes_the_org_with_them(self, db_session, make_user):
        from organization_model import Organization, OrganizationMember, OrgRole

        owner = make_user(email="erase_solo_owner@example.com")
        org = Organization(name="Solo Firm", slug="solo-firm-erase", owner_user_id=owner.id)
        db_session.add(org)
        db_session.flush()
        db_session.add(OrganizationMember(organization_id=org.id, user_id=owner.id, role=OrgRole.OWNER))
        owner.organization_id = org.id
        db_session.commit()
        org_id = org.id
        erase_account(db_session, owner)
        assert _count(db_session, "organizations", id=org_id) == 0


class TestExport:
    def test_export_contains_the_data_and_no_secrets(self, db_session, populated):
        data = export_account(db_session, populated["user"])
        assert data["account"][0]["email"] == "erase_me@example.com"
        assert "hashed_password" not in data["account"][0]
        assert data["clients"][0]["name"] == "Erase Me Client"
        assert len(data["engagements"]) == 1
        assert all("token_hash" not in s for s in data["sessions"])
        assert "tool_sessions" in data


@pytest.mark.usefixtures("bypass_csrf")
class TestRoutes:
    @pytest.fixture(autouse=True)
    def _db(self, db_session):
        app.dependency_overrides[get_db] = lambda: db_session
        yield
        app.dependency_overrides.clear()

    def _headers(self, user: User) -> dict[str, str]:
        token, _ = create_access_token(user.id, user.email)
        return {"Authorization": f"Bearer {token}"}

    @pytest.mark.asyncio
    async def test_wrong_password_is_refused(self, populated):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post(
                "/auth/account/delete",
                json={"password": "wrong", "confirm": "DELETE"},
                headers=self._headers(populated["user"]),
            )
        assert r.status_code == 400

    @pytest.mark.asyncio
    async def test_confirmation_word_is_required(self, populated):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post(
                "/auth/account/delete",
                json={"password": PASSWORD, "confirm": "yes"},
                headers=self._headers(populated["user"]),
            )
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_refusal_carries_a_code_the_ui_can_explain(self, db_session, populated):
        """PR #254 review: the transport shows no raw backend text, so a refusal
        must carry a stable code for the UI to map to an explanation."""
        populated["user"].is_superadmin = True
        db_session.commit()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post(
                "/auth/account/delete",
                json={"password": PASSWORD, "confirm": "DELETE"},
                headers=self._headers(populated["user"]),
            )
        assert r.status_code == 409
        assert r.json()["detail"]["code"] == "ERASURE_SUPERADMIN"

    @pytest.mark.asyncio
    async def test_delete_then_token_is_dead(self, db_session, populated):
        headers = self._headers(populated["user"])
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post("/auth/account/delete", json={"password": PASSWORD, "confirm": "DELETE"}, headers=headers)
            assert r.status_code == 204
            assert (await c.get("/auth/me", headers=headers)).status_code == 401

    @pytest.mark.asyncio
    async def test_export_downloads_json(self, populated):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
            r = await c.get("/auth/account/export", headers=self._headers(populated["user"]))
        assert r.status_code == 200
        assert "attachment" in r.headers["content-disposition"]
        assert r.json()["account"][0]["email"] == "erase_me@example.com"

    @pytest.mark.asyncio
    async def test_superadmin_can_erase_on_request(self, db_session, populated, make_user):
        admin = make_user(email="erase_route_admin@example.com")
        admin.is_superadmin = True
        db_session.commit()
        target_id = populated["user"].id
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post(f"/internal/admin/users/{target_id}/erase", headers=self._headers(admin))
        assert r.status_code == 200, r.text
        assert _count(db_session, "users", id=target_id) == 0
        assert _count(db_session, "admin_audit_logs", action_type="ACCOUNT_ERASED") == 1

    @pytest.mark.asyncio
    async def test_customer_cannot_use_the_admin_erase_route(self, populated):
        bystander = populated["bystander"]
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post(f"/internal/admin/users/{populated['user'].id}/erase", headers=self._headers(bystander))
        assert r.status_code == 403


class TestPartialProviderCleanup:
    """PR #237 review: R2 deletions cannot be rolled back."""

    def _shares(self, db_session, user, n):
        from datetime import UTC, datetime, timedelta

        from export_share_model import ExportShare

        for i in range(n):
            db_session.add(
                ExportShare(
                    user_id=user.id,
                    share_token_hash=f"{i:064d}",
                    tool_name="trial_balance",
                    export_format="pdf",
                    object_key=f"shares/{i}",
                    expires_at=datetime.now(UTC) + timedelta(hours=1),
                )
            )
        db_session.commit()

    def test_a_failure_part_way_removes_only_the_rows_whose_objects_are_gone(self, db_session, populated, monkeypatch):
        from shared import export_share_storage

        user_id = populated["user"].id
        self._shares(db_session, populated["user"], 3)
        calls = []

        def flaky(key):
            calls.append(key)
            return len(calls) < 2  # first succeeds, second fails

        monkeypatch.setattr(export_share_storage, "delete", flaky)
        with pytest.raises(ErasureProviderError, match="1 shared link") as exc:
            erase_account(db_session, populated["user"])
        assert exc.value.code == "ERASURE_PARTIAL_CLEANUP"
        assert _count(db_session, "export_shares", user_id=user_id) == 2
        assert _count(db_session, "users", id=user_id) == 1

    def test_stripe_failure_after_shares_says_what_was_removed(self, db_session, populated, monkeypatch):
        import services.account_erasure as mod
        from shared import export_share_storage

        self._shares(db_session, populated["user"], 1)
        monkeypatch.setattr(export_share_storage, "delete", lambda key: True)

        def boom(*_a, **_k):
            raise ErasureProviderError("Stripe down.")

        monkeypatch.setattr(mod, "_cancel_stripe", boom)
        with pytest.raises(
            ErasureProviderError, match="shared link.*were removed; your subscription and account were not changed"
        ) as exc:
            erase_account(db_session, populated["user"])
        assert exc.value.code == "ERASURE_PARTIAL_CLEANUP"
