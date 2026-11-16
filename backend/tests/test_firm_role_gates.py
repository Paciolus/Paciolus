"""Sprint 853 (review AZ-15): destructive actions on firm records need a role.

CEO decision (2026-11-16): deleting a client, or archiving an engagement,
expectation or misstatement, needs the firm's owner or an admin. Members can
still create and edit. Only the owner can remove an admin.

The gate sits beside the firm check, not in place of it: a user from another
firm still gets 404 (the record is out of reach), a member of the firm gets
403 (in reach, wrong role). Every cell of the role-by-action matrix runs
against fresh records through the real routes with real access tokens.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

import httpx
import pytest
from sqlalchemy.orm import Session

from analytical_expectations_model import AnalyticalExpectation
from engagement_model import Engagement, EngagementStatus
from models import Client, User
from organization_model import Organization, OrganizationMember, OrgRole
from tests.test_firm_owned_records import _auth, _firm, _join, api  # noqa: F401 — `api` is a fixture
from uncorrected_misstatements_model import UncorrectedMisstatement

pytestmark = pytest.mark.usefixtures("bypass_csrf")


class _Firm:
    owner: User
    admin: User
    admin2: User
    member: User
    outsider: User
    org: Organization
    admin2_membership_id: int
    member_membership_id: int
    empty_client_id: int
    client_id: int
    engagement_id: int
    expectation_id: int
    misstatement_id: int


async def _build(api: httpx.AsyncClient, db: Session, make_user) -> _Firm:  # noqa: ANN001
    f = _Firm()
    f.owner = make_user(email="owner@firm.test")
    f.admin = make_user(email="admin@firm.test")
    f.admin2 = make_user(email="admin2@firm.test")
    f.member = make_user(email="member@firm.test")
    f.outsider = make_user(email="owner@other-firm.test")
    f.org = _firm(db, f.owner, "Role Firm")
    _join(db, f.org, f.admin, OrgRole.ADMIN)
    f.admin2_membership_id = _join(db, f.org, f.admin2, OrgRole.ADMIN).id
    f.member_membership_id = _join(db, f.org, f.member).id
    _firm(db, f.outsider, "Other Firm")

    # A plain member creates everything, so no actor is ever "the creator".
    hdr = _auth(f.member)
    r = await api.post("/clients", json={"name": "Empty Co"}, headers=hdr)
    assert r.status_code == 201, r.text
    f.empty_client_id = r.json()["id"]
    r = await api.post("/clients", json={"name": "Busy Co"}, headers=hdr)
    assert r.status_code == 201, r.text
    f.client_id = r.json()["id"]
    r = await api.post(
        "/engagements",
        json={"client_id": f.client_id, "period_start": "2026-01-01T00:00:00", "period_end": "2026-12-31T00:00:00"},
        headers=hdr,
    )
    assert r.status_code == 201, r.text
    f.engagement_id = r.json()["id"]
    r = await api.post(
        f"/engagements/{f.engagement_id}/analytical-expectations",
        json={
            "procedure_target_type": "account",
            "procedure_target_label": "Revenue",
            "expected_value": 1000.0,
            "precision_threshold_amount": 50.0,
            "corroboration_basis_text": "Prior year",
            "corroboration_tags": ["prior_period"],
        },
        headers=hdr,
    )
    assert r.status_code == 201, r.text
    f.expectation_id = r.json()["id"]
    r = await api.post(
        f"/engagements/{f.engagement_id}/uncorrected-misstatements",
        json={
            "source_type": "known_error",
            "source_reference": "JE-1",
            "description": "Duplicate accrual",
            "accounts_affected": [{"account": "Accruals", "debit_credit": "DR", "amount": 10.0}],
            "classification": "factual",
            "fs_impact_net_income": 10.0,
            "fs_impact_net_assets": 10.0,
        },
        headers=hdr,
    )
    assert r.status_code == 201, r.text
    f.misstatement_id = r.json()["id"]
    return f


# ---------------------------------------------------------------------------
# Destructive actions: each returns (response, "still intact?" check)
# ---------------------------------------------------------------------------

Action = Callable[[httpx.AsyncClient, _Firm, dict[str, str]], Awaitable[httpx.Response]]


async def _delete_client(api, f, hdr):  # noqa: ANN001, ANN202
    return await api.delete(f"/clients/{f.empty_client_id}", headers=hdr)


async def _archive_engagement(api, f, hdr):  # noqa: ANN001, ANN202
    return await api.delete(f"/engagements/{f.engagement_id}", headers=hdr)


async def _archive_engagement_via_update(api, f, hdr):  # noqa: ANN001, ANN202
    return await api.put(f"/engagements/{f.engagement_id}", json={"status": "archived"}, headers=hdr)


async def _archive_expectation(api, f, hdr):  # noqa: ANN001, ANN202
    return await api.delete(f"/analytical-expectations/{f.expectation_id}", headers=hdr)


async def _archive_misstatement(api, f, hdr):  # noqa: ANN001, ANN202
    return await api.delete(f"/uncorrected-misstatements/{f.misstatement_id}", headers=hdr)


def _intact(action: str, db: Session, f: _Firm) -> bool:
    db.expire_all()
    if action == "delete_client":
        return db.get(Client, f.empty_client_id) is not None
    if action.startswith("archive_engagement"):
        return db.get(Engagement, f.engagement_id).status != EngagementStatus.ARCHIVED
    if action == "archive_expectation":
        return db.get(AnalyticalExpectation, f.expectation_id).archived_at is None
    return db.get(UncorrectedMisstatement, f.misstatement_id).archived_at is None


ACTIONS: dict[str, Action] = {
    "delete_client": _delete_client,
    "archive_engagement": _archive_engagement,
    "archive_engagement_via_update": _archive_engagement_via_update,
    "archive_expectation": _archive_expectation,
    "archive_misstatement": _archive_misstatement,
}

# owner/admin succeed, a member is refused, another firm cannot see the record.
EXPECTED = {"owner": "allowed", "admin": "allowed", "member": 403, "outsider": 404}


class TestDestructiveActionMatrix:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("role", list(EXPECTED))
    @pytest.mark.parametrize("action", list(ACTIONS))
    async def test_role_by_action(self, api, db_session, make_user, role, action):
        f = await _build(api, db_session, make_user)
        actor = getattr(f, role)
        r = await ACTIONS[action](api, f, _auth(actor))

        if EXPECTED[role] == "allowed":
            assert r.status_code in (200, 204), f"{role} {action} -> {r.status_code}: {r.text[:200]}"
            assert not _intact(action, db_session, f)
        else:
            assert r.status_code == EXPECTED[role], f"{role} {action} -> {r.status_code}: {r.text[:200]}"
            assert _intact(action, db_session, f)


class TestMembersStillCreateAndEdit:
    @pytest.mark.asyncio
    async def test_member_can_edit_every_record(self, api, db_session, make_user):
        f = await _build(api, db_session, make_user)
        hdr = _auth(f.member)
        r = await api.put(f"/clients/{f.client_id}", json={"name": "Busy Co Ltd"}, headers=hdr)
        assert r.status_code == 200, r.text
        r = await api.put(f"/engagements/{f.engagement_id}", json={"materiality_amount": 5000}, headers=hdr)
        assert r.status_code == 200, r.text
        r = await api.patch(f"/analytical-expectations/{f.expectation_id}", json={"cpa_notes": "ok"}, headers=hdr)
        assert r.status_code == 200, r.text
        r = await api.patch(f"/uncorrected-misstatements/{f.misstatement_id}", json={"cpa_notes": "ok"}, headers=hdr)
        assert r.status_code == 200, r.text


class TestPersonalClientsAreTheCreators:
    @pytest.mark.asyncio
    async def test_solo_user_deletes_and_archives_their_own_records(self, api, db_session, make_user):
        solo = make_user(email="solo@example.com")
        hdr = _auth(solo)
        r = await api.post("/clients", json={"name": "Solo Co"}, headers=hdr)
        cid = r.json()["id"]
        r = await api.post(
            "/engagements",
            json={"client_id": cid, "period_start": "2026-01-01T00:00:00", "period_end": "2026-12-31T00:00:00"},
            headers=hdr,
        )
        eid = r.json()["id"]
        assert (await api.delete(f"/engagements/{eid}", headers=hdr)).status_code == 204
        r = await api.post("/clients", json={"name": "Solo Two"}, headers=hdr)
        assert (await api.delete(f"/clients/{r.json()['id']}", headers=hdr)).status_code == 204


class TestOnlyTheOwnerRemovesAnAdmin:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(("role", "expected"), [("owner", 200), ("admin", 403), ("member", 403), ("outsider", 404)])
    async def test_remove_admin(self, api, db_session, make_user, role, expected):
        f = await _build(api, db_session, make_user)
        r = await api.delete(f"/organization/members/{f.admin2_membership_id}", headers=_auth(getattr(f, role)))
        assert r.status_code == expected, r.text
        still_there = db_session.query(OrganizationMember).filter_by(id=f.admin2_membership_id).first() is not None
        assert still_there is (expected != 200)

    @pytest.mark.asyncio
    async def test_admin_can_still_remove_a_member(self, api, db_session, make_user):
        f = await _build(api, db_session, make_user)
        r = await api.delete(f"/organization/members/{f.member_membership_id}", headers=_auth(f.admin))
        assert r.status_code == 200, r.text
