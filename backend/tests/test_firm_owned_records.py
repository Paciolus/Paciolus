"""Sprint 853 (review AZ-01, DH-02, TQ-05): firm records belong to the firm.

Before this sprint a client was owned by the person who created it
(``Client.user_id``) and firm sharing was derived from that person's
*current* membership. Removing them from the firm took the firm's clients
with them, and admitting them to another firm exposed those clients to the
new firm.

These tests run end-to-end through the real routes with real access tokens
(only ``get_db`` is overridden, to share the test transaction):

* firm A's creator makes a client + engagement; another A member adds
  workpaper content (follow-up item, comment, expectation, misstatement);
* the creator is removed through ``DELETE /organization/members/{id}`` and
  then reuses their existing token: every A record answers 404, while A's
  remaining members keep access;
* the creator joins firm B through the real invite flow: every B member
  (and the creator) gets 404 on A's records through direct reads, lists,
  exports and shared links;
* the creator's personal client stays readable by the creator throughout.
"""

from __future__ import annotations

import hashlib
import secrets
from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta

import httpx
import pytest
from sqlalchemy.orm import Session

from auth import create_access_token
from database import get_db
from engagement_model import ToolName, ToolRun, ToolRunStatus
from export_share_model import ExportShare
from main import app
from models import Client, DiagnosticSummary, User
from organization_model import (
    INVITE_EXPIRY_HOURS,
    Organization,
    OrganizationInvite,
    OrganizationMember,
    OrgRole,
)
from subscription_model import BillingInterval, Subscription, SubscriptionStatus

pytestmark = pytest.mark.usefixtures("bypass_csrf")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _subscribe(db: Session, user: User, tier: str = "professional") -> Subscription:
    sub = Subscription(
        user_id=user.id,
        tier=tier,
        status=SubscriptionStatus.ACTIVE,
        billing_interval=BillingInterval.MONTHLY,
        seat_count=7,
        additional_seats=0,
    )
    db.add(sub)
    db.flush()
    return sub


def _firm(db: Session, owner: User, name: str) -> Organization:
    """A firm with ``owner`` as OWNER and a live Professional subscription."""
    sub = _subscribe(db, owner)
    org = Organization(
        name=name, slug=f"{name.lower().replace(' ', '-')}-{secrets.token_hex(3)}", owner_user_id=owner.id
    )
    org.subscription_id = sub.id
    db.add(org)
    db.flush()
    db.add(OrganizationMember(organization_id=org.id, user_id=owner.id, role=OrgRole.OWNER))
    owner.organization_id = org.id
    db.flush()
    return org


def _join(db: Session, org: Organization, user: User, role: OrgRole = OrgRole.MEMBER) -> OrganizationMember:
    member = OrganizationMember(organization_id=org.id, user_id=user.id, role=role)
    db.add(member)
    user.organization_id = org.id
    db.flush()
    return member


def _invite(db: Session, org: Organization, email: str, invited_by: User) -> str:
    raw = secrets.token_urlsafe(32)
    db.add(
        OrganizationInvite(
            organization_id=org.id,
            invite_token_hash=hashlib.sha256(raw.encode()).hexdigest(),
            invitee_email=email,
            role=OrgRole.MEMBER,
            invited_by_user_id=invited_by.id,
            expires_at=datetime.now(UTC) + timedelta(hours=INVITE_EXPIRY_HOURS),
        )
    )
    db.flush()
    return raw


def _auth(user: User) -> dict[str, str]:
    token, _ = create_access_token(user.id, user.email, user.password_changed_at)
    return {"Authorization": f"Bearer {token}"}


def _ids(payload: object) -> set[int]:
    items = payload["items"] if isinstance(payload, dict) else payload
    return {row["id"] for row in items}  # type: ignore[index]


@pytest.fixture
def api(db_session: Session) -> Iterator[httpx.AsyncClient]:
    app.dependency_overrides[get_db] = lambda: db_session
    try:
        yield httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Scenario
# ---------------------------------------------------------------------------


class _World:
    """Firms A and B, the creator, and every A record the creator made."""

    def __init__(self) -> None:
        self.a_owner: User
        self.a_member: User
        self.creator: User
        self.b_owner: User
        self.b_member: User
        self.firm_a: Organization
        self.firm_b: Organization
        self.creator_membership_id: int
        self.personal_client_id: int
        self.client_id: int
        self.engagement_id: int
        self.item_id: int
        self.comment_id: int
        self.expectation_id: int
        self.misstatement_id: int
        self.share_token: str


async def _build(api: httpx.AsyncClient, db: Session, make_user) -> _World:  # noqa: ANN001
    w = _World()
    w.a_owner = make_user(email="a-owner@firm-a.test")
    w.a_member = make_user(email="a-member@firm-a.test")
    w.creator = make_user(email="creator@firm-a.test")
    w.b_owner = make_user(email="b-owner@firm-b.test")
    w.b_member = make_user(email="b-member@firm-b.test")
    # The creator pays for a plan of their own, so after leaving A they keep
    # export access: an export that still answers 404 is then the access
    # rule, not an entitlement gate.
    _subscribe(db, w.creator)

    w.firm_a = _firm(db, w.a_owner, "Firm A")
    _join(db, w.firm_a, w.a_member)
    w.firm_b = _firm(db, w.b_owner, "Firm B")
    _join(db, w.firm_b, w.b_member)

    # A personal client, made before the creator joined any firm.
    r = await api.post("/clients", json={"name": "Creator Personal Co"}, headers=_auth(w.creator))
    assert r.status_code == 201, r.text
    w.personal_client_id = r.json()["id"]

    w.creator_membership_id = _join(db, w.firm_a, w.creator).id

    # The creator makes a firm client and an engagement.
    r = await api.post("/clients", json={"name": "Firm A Client"}, headers=_auth(w.creator))
    assert r.status_code == 201, r.text
    w.client_id = r.json()["id"]
    r = await api.post(
        "/engagements",
        json={"client_id": w.client_id, "period_start": "2026-01-01T00:00:00", "period_end": "2026-12-31T00:00:00"},
        headers=_auth(w.creator),
    )
    assert r.status_code == 201, r.text
    w.engagement_id = r.json()["id"]

    # Another A member adds workpaper content.
    eid = w.engagement_id
    hdr = _auth(w.a_member)
    r = await api.post(
        f"/engagements/{eid}/follow-up-items",
        json={"description": "Confirm cut-off", "tool_source": "je_testing"},
        headers=hdr,
    )
    assert r.status_code == 201, r.text
    w.item_id = r.json()["id"]
    r = await api.post(f"/follow-up-items/{w.item_id}/comments", json={"comment_text": "On it"}, headers=hdr)
    assert r.status_code == 201, r.text
    w.comment_id = r.json()["id"]
    r = await api.post(
        f"/engagements/{eid}/analytical-expectations",
        json={
            "procedure_target_type": "account",
            "procedure_target_label": "Revenue",
            "expected_value": 1000.0,
            "precision_threshold_amount": 50.0,
            "corroboration_basis_text": "Prior year adjusted for price changes",
            "corroboration_tags": ["prior_period"],
        },
        headers=hdr,
    )
    assert r.status_code == 201, r.text
    w.expectation_id = r.json()["id"]
    r = await api.post(
        f"/engagements/{eid}/uncorrected-misstatements",
        json={
            "source_type": "known_error",
            "source_reference": "JE-14",
            "description": "Duplicate accrual",
            "accounts_affected": [{"account": "Accrued Expenses", "debit_credit": "DR", "amount": 120.0}],
            "classification": "factual",
            "fs_impact_net_income": 120.0,
            "fs_impact_net_assets": 120.0,
        },
        headers=hdr,
    )
    assert r.status_code == 201, r.text
    w.misstatement_id = r.json()["id"]

    # A tool run, a saved summary and a shared export link made by the creator.
    db.add(
        ToolRun(
            engagement_id=eid,
            tool_name=ToolName.JOURNAL_ENTRY_TESTING,
            run_number=1,
            status=ToolRunStatus.COMPLETED,
            composite_score=12.0,
            flagged_accounts='["Cash"]',
        )
    )
    db.add(
        DiagnosticSummary(client_id=w.client_id, user_id=w.creator.id, period_date=date(2026, 12, 31), total_assets=100)
    )
    w.share_token = secrets.token_urlsafe(32)
    db.add(
        ExportShare(
            user_id=w.creator.id,
            organization_id=w.firm_a.id,
            share_token_hash=hashlib.sha256(w.share_token.encode()).hexdigest(),
            tool_name="anomaly_summary",
            export_format="csv",
            export_data=b"account,amount\nCash,1\n",
            expires_at=datetime.now(UTC) + timedelta(hours=24),
        )
    )
    db.flush()
    return w


def _record_reads(w: _World) -> list[str]:
    """Every direct read of an A record (GET)."""
    e = w.engagement_id
    return [
        f"/clients/{w.client_id}",
        f"/clients/{w.client_id}/resolved-framework",
        f"/clients/{w.client_id}/settings",
        f"/clients/{w.client_id}/periods",
        f"/clients/{w.client_id}/trends",
        f"/diagnostics/summary/{w.client_id}/history",
        f"/engagements/{e}",
        f"/engagements/{e}/materiality",
        f"/engagements/{e}/tool-runs",
        f"/engagements/{e}/convergence",
        f"/engagements/{e}/tool-run-trends",
        f"/engagements/{e}/workpaper-index",
        f"/engagements/{e}/follow-up-items",
        f"/engagements/{e}/follow-up-items/summary",
        f"/follow-up-items/{w.item_id}/comments",
        f"/engagements/{e}/analytical-expectations",
        f"/analytical-expectations/{w.expectation_id}",
        f"/engagements/{e}/uncorrected-misstatements",
        f"/engagements/{e}/sum-schedule",
        f"/uncorrected-misstatements/{w.misstatement_id}",
    ]


def _exports(w: _World) -> list[str]:
    e = w.engagement_id
    return [
        f"/engagements/{e}/export/anomaly-summary",
        f"/engagements/{e}/export/package",
        f"/engagements/{e}/export/convergence-csv",
        f"/engagements/{e}/export/analytical-expectations",
        f"/engagements/{e}/export/sum-schedule",
    ]


# Routes a member can read but that a saved summary scopes to its author.
_AUTHOR_ONLY = ("/periods", "/trends", "/diagnostics/summary/")


async def _assert_locked_out(api: httpx.AsyncClient, w: _World, user: User, *, share_revoked: bool = True) -> None:
    hdr = _auth(user)
    wrong = []
    for path in _record_reads(w):
        r = await api.get(path, headers=hdr)
        if r.status_code != 404:
            wrong.append(f"GET {path} -> {r.status_code}")
    for path in _exports(w):
        r = await api.post(path, headers=hdr)
        if r.status_code != 404:
            wrong.append(f"POST {path} -> {r.status_code}")
    assert not wrong, f"{user.email} reached firm A records: {wrong}"

    r = await api.get("/clients", params={"page_size": 100}, headers=hdr)
    assert r.status_code == 200
    assert w.client_id not in _ids(r.json())
    r = await api.get("/clients/with-engagement-summary", params={"page_size": 100}, headers=hdr)
    assert r.status_code == 200
    assert w.client_id not in {row["id"] for row in r.json()["items"]}
    r = await api.get("/engagements", params={"page_size": 100}, headers=hdr)
    assert r.status_code == 200
    assert w.engagement_id not in _ids(r.json())

    if share_revoked:
        # A share link is open to whoever holds the token, by design, so it
        # is only closed once the creator has left the firm.
        r = await api.get(f"/export-sharing/{w.share_token}", headers=hdr)
        assert r.status_code == 404, f"{user.email} shared link -> {r.status_code}"


async def _assert_has_access(api: httpx.AsyncClient, w: _World, user: User) -> None:
    hdr = _auth(user)
    for path in _record_reads(w):
        if any(marker in path for marker in _AUTHOR_ONLY):
            continue
        r = await api.get(path, headers=hdr)
        assert r.status_code == 200, f"{user.email} GET {path} -> {r.status_code}: {r.text[:200]}"
    r = await api.get("/clients", params={"page_size": 100}, headers=hdr)
    assert w.client_id in _ids(r.json())
    r = await api.get("/engagements", params={"page_size": 100}, headers=hdr)
    assert w.engagement_id in _ids(r.json())


async def _remove_creator(api: httpx.AsyncClient, w: _World) -> None:
    r = await api.delete(f"/organization/members/{w.creator_membership_id}", headers=_auth(w.a_owner))
    assert r.status_code == 200, r.text


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestFirmOwnedRecords:
    @pytest.mark.asyncio
    async def test_new_client_belongs_to_the_creators_firm(self, api, db_session, make_user):
        w = await _build(api, db_session, make_user)
        firm_client = db_session.get(Client, w.client_id)
        personal_client = db_session.get(Client, w.personal_client_id)
        assert firm_client.organization_id == w.firm_a.id
        assert personal_client.organization_id is None

    @pytest.mark.asyncio
    async def test_firm_members_share_records_before_removal(self, api, db_session, make_user):
        w = await _build(api, db_session, make_user)
        await _assert_has_access(api, w, w.a_owner)
        await _assert_has_access(api, w, w.a_member)
        await _assert_has_access(api, w, w.creator)
        await _assert_locked_out(api, w, w.b_member, share_revoked=False)

    @pytest.mark.asyncio
    async def test_removed_creator_loses_firm_records_with_existing_token(self, api, db_session, make_user):
        w = await _build(api, db_session, make_user)
        await _remove_creator(api, w)

        await _assert_locked_out(api, w, w.creator)

        # A's remaining members keep everything.
        await _assert_has_access(api, w, w.a_owner)
        await _assert_has_access(api, w, w.a_member)

        # The creator's personal client is untouched.
        r = await api.get(f"/clients/{w.personal_client_id}", headers=_auth(w.creator))
        assert r.status_code == 200
        assert db_session.get(Client, w.client_id).organization_id == w.firm_a.id

    @pytest.mark.asyncio
    async def test_creators_new_firm_cannot_reach_old_firm_records(self, api, db_session, make_user):
        w = await _build(api, db_session, make_user)
        await _remove_creator(api, w)

        token = _invite(db_session, w.firm_b, w.creator.email, w.b_owner)
        r = await api.post(f"/organization/invite/accept/{token}", headers=_auth(w.creator))
        assert r.status_code == 200, r.text

        for user in (w.b_owner, w.b_member, w.creator):
            await _assert_locked_out(api, w, user)

        # Joining B does not move the creator's personal client either.
        r = await api.get(f"/clients/{w.personal_client_id}", headers=_auth(w.creator))
        assert r.status_code == 200
        r = await api.get(f"/clients/{w.personal_client_id}", headers=_auth(w.b_member))
        assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_removal_revokes_the_members_shared_links_for_firm_records(self, api, db_session, make_user):
        w = await _build(api, db_session, make_user)
        r = await api.get(f"/export-sharing/{w.share_token}")
        assert r.status_code == 200

        await _remove_creator(api, w)

        r = await api.get(f"/export-sharing/{w.share_token}")
        assert r.status_code == 404
        share = db_session.query(ExportShare).filter(ExportShare.user_id == w.creator.id).one()
        assert share.revoked_at is not None


class TestCachedAuthorizationDoesNotSurviveRemoval:
    """TQ-05: the earlier removal tests only checked ``user.organization_id``.

    The engagement analytics cache is keyed by engagement, not by user. Warm
    it as the creator, remove them, and ask again with the same token: the
    cached result must not be served.
    """

    @pytest.mark.asyncio
    async def test_warm_analytics_cache_is_not_served_after_removal(self, api, db_session, make_user):
        from engagement_manager import _convergence_cache, _trend_cache

        w = await _build(api, db_session, make_user)
        hdr = _auth(w.creator)
        for path in ("convergence", "tool-run-trends"):
            r = await api.get(f"/engagements/{w.engagement_id}/{path}", headers=hdr)
            assert r.status_code == 200, r.text
        assert len(_convergence_cache._store) == 1
        assert len(_trend_cache._store) == 1

        await _remove_creator(api, w)

        for path in ("convergence", "tool-run-trends"):
            r = await api.get(f"/engagements/{w.engagement_id}/{path}", headers=hdr)
            assert r.status_code == 404, f"{path} served from cache after removal"
            r = await api.post(f"/engagements/{w.engagement_id}/export/convergence-csv", headers=hdr)
            assert r.status_code == 404
