"""Sprint 878 (review AZ-02, ST-04): the engagement workspace is a paid feature.

``check_workspace_access`` denied Free, but no route called it: every
workspace route depended only on ``require_current_user``, so a Free account
could create and run an engagement.

Decisions (CEO): the workspace is Solo and above. An account that drops to
Free keeps read access to its existing engagements and workpapers but cannot
create or change them. Ownership checks are unchanged.

Every workspace write runs here, through the real routes with real access
tokens, for three plan states of the same records' owner:

* ``solo``   - an active Solo subscription: every write succeeds;
* ``lapsed`` - a Solo subscription now CANCELED: every write is 403;
* ``free``   - the account is now Free with no subscription: every write is 403.

The records are created while the owner is on active Solo, then the plan
changes, so "existing own records" are real records. Reads of them succeed in
all three states. Another firm's ids stay out of reach in every state.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

import httpx
import pytest
from sqlalchemy.orm import Session

from analytical_expectations_model import AnalyticalExpectation
from engagement_model import Engagement
from follow_up_items_model import FollowUpItem, FollowUpItemComment
from models import User, UserTier
from subscription_model import Subscription, SubscriptionStatus
from tests.test_firm_owned_records import _auth, _firm, _subscribe, api  # noqa: F401 — `api` is a fixture
from uncorrected_misstatements_model import UncorrectedMisstatement

pytestmark = pytest.mark.usefixtures("bypass_csrf")

PLAN_STATES = ("solo", "lapsed", "free")

_ENGAGEMENT = {"period_start": "2026-01-01T00:00:00", "period_end": "2026-12-31T00:00:00"}
_EXPECTATION = {
    "procedure_target_type": "account",
    "procedure_target_label": "Revenue",
    "expected_value": 1000.0,
    "precision_threshold_amount": 50.0,
    "corroboration_basis_text": "Prior year",
    "corroboration_tags": ["prior_period"],
}
_MISSTATEMENT = {
    "source_type": "known_error",
    "source_reference": "JE-1",
    "description": "Duplicate accrual",
    "accounts_affected": [{"account": "Accruals", "debit_credit": "DR", "amount": 10.0}],
    "classification": "factual",
    "fs_impact_net_income": 10.0,
    "fs_impact_net_assets": 10.0,
}


@dataclass
class _Records:
    client_id: int
    engagement_id: int
    item_id: int
    comment_id: int
    expectation_id: int
    misstatement_id: int


async def _make_records(api: httpx.AsyncClient, hdr: dict[str, str]) -> _Records:
    r = await api.post("/clients", json={"name": "Owner Co"}, headers=hdr)
    assert r.status_code == 201, r.text
    client_id = r.json()["id"]
    r = await api.post("/engagements", json={"client_id": client_id, **_ENGAGEMENT}, headers=hdr)
    assert r.status_code == 201, r.text
    eid = r.json()["id"]
    r = await api.post(
        f"/engagements/{eid}/follow-up-items",
        json={"description": "Check cut-off", "tool_source": "trial_balance"},
        headers=hdr,
    )
    assert r.status_code == 201, r.text
    item_id = r.json()["id"]
    r = await api.post(f"/follow-up-items/{item_id}/comments", json={"comment_text": "Looked at it"}, headers=hdr)
    assert r.status_code == 201, r.text
    comment_id = r.json()["id"]
    r = await api.post(f"/engagements/{eid}/analytical-expectations", json=_EXPECTATION, headers=hdr)
    assert r.status_code == 201, r.text
    expectation_id = r.json()["id"]
    r = await api.post(f"/engagements/{eid}/uncorrected-misstatements", json=_MISSTATEMENT, headers=hdr)
    assert r.status_code == 201, r.text
    return _Records(client_id, eid, item_id, comment_id, expectation_id, r.json()["id"])


def _set_plan(db: Session, user: User, sub: Subscription, state: str) -> None:
    if state == "lapsed":
        sub.status = SubscriptionStatus.CANCELED
    elif state == "free":
        db.delete(sub)
        user.tier = UserTier.FREE
    db.flush()
    db.expire_all()


@dataclass
class _World:
    owner: User
    hdr: dict[str, str]
    mine: _Records
    theirs: _Records  # another firm's records
    state: str


@pytest.fixture
def world_factory(api: httpx.AsyncClient, db_session: Session, make_user):  # noqa: ANN001, ANN201
    async def _build(state: str) -> _World:
        other = make_user(email=f"owner-{state}@other-firm.test")
        _firm(db_session, other, f"Other Firm {state}")
        theirs = await _make_records(api, _auth(other))

        owner = make_user(email=f"owner-{state}@solo.test", tier=UserTier.SOLO)
        sub = _subscribe(db_session, owner, tier="solo")
        hdr = _auth(owner)
        mine = await _make_records(api, hdr)
        _set_plan(db_session, owner, sub, state)
        return _World(owner, hdr, mine, theirs, state)

    return _build


# ---------------------------------------------------------------------------
# Writes
# ---------------------------------------------------------------------------

Write = Callable[[httpx.AsyncClient, _Records, dict[str, str]], Awaitable[httpx.Response]]

WRITES: dict[str, Write] = {
    "create_engagement": lambda api, r, h: api.post(
        "/engagements", json={"client_id": r.client_id, **_ENGAGEMENT}, headers=h
    ),
    "update_engagement": lambda api, r, h: api.put(
        f"/engagements/{r.engagement_id}", json={"materiality_amount": 5000.0}, headers=h
    ),
    "archive_engagement": lambda api, r, h: api.delete(f"/engagements/{r.engagement_id}", headers=h),
    "create_follow_up_item": lambda api, r, h: api.post(
        f"/engagements/{r.engagement_id}/follow-up-items",
        json={"description": "Another", "tool_source": "trial_balance"},
        headers=h,
    ),
    "update_follow_up_item": lambda api, r, h: api.put(
        f"/follow-up-items/{r.item_id}", json={"auditor_notes": "changed"}, headers=h
    ),
    "delete_follow_up_item": lambda api, r, h: api.delete(f"/follow-up-items/{r.item_id}", headers=h),
    "create_comment": lambda api, r, h: api.post(
        f"/follow-up-items/{r.item_id}/comments", json={"comment_text": "More"}, headers=h
    ),
    "update_comment": lambda api, r, h: api.patch(
        f"/comments/{r.comment_id}", json={"comment_text": "Edited"}, headers=h
    ),
    "delete_comment": lambda api, r, h: api.delete(f"/comments/{r.comment_id}", headers=h),
    "create_expectation": lambda api, r, h: api.post(
        f"/engagements/{r.engagement_id}/analytical-expectations", json=_EXPECTATION, headers=h
    ),
    "update_expectation": lambda api, r, h: api.patch(
        f"/analytical-expectations/{r.expectation_id}", json={"cpa_notes": "changed"}, headers=h
    ),
    "archive_expectation": lambda api, r, h: api.delete(f"/analytical-expectations/{r.expectation_id}", headers=h),
    "create_misstatement": lambda api, r, h: api.post(
        f"/engagements/{r.engagement_id}/uncorrected-misstatements", json=_MISSTATEMENT, headers=h
    ),
    "update_misstatement": lambda api, r, h: api.patch(
        f"/uncorrected-misstatements/{r.misstatement_id}", json={"cpa_notes": "changed"}, headers=h
    ),
    "archive_misstatement": lambda api, r, h: api.delete(f"/uncorrected-misstatements/{r.misstatement_id}", headers=h),
    # Sprint 879b: saving a run's proposed actual into the expectation.
    "capture_actuals": lambda api, r, h: api.post(
        f"/engagements/{r.engagement_id}/analytical-expectations/capture-actuals",
        json={"capture_tokens": [_capture_token(r, h)]},
        headers=h,
    ),
}


def _capture_token(r: _Records, h: dict[str, str]) -> str:
    """A valid proposal for the caller (the bearer token's subject) on these records."""
    import jwt

    from shared.expectation_capture import sign_capture

    caller = int(jwt.decode(h["Authorization"].split()[1], options={"verify_signature": False})["sub"])
    return sign_capture(
        user_id=caller,
        engagement_id=r.engagement_id,
        expectation_id=r.expectation_id,
        actual=1000,
        source="multi_period",
        tool_run_id=None,
    )


def _snapshot(db: Session, r: _Records) -> tuple:
    """Everything a write could change, so a refused write is shown to change nothing."""
    db.expire_all()
    eng = db.get(Engagement, r.engagement_id)
    item = db.get(FollowUpItem, r.item_id)
    comment = db.get(FollowUpItemComment, r.comment_id)
    exp = db.get(AnalyticalExpectation, r.expectation_id)
    mis = db.get(UncorrectedMisstatement, r.misstatement_id)
    return (
        db.query(Engagement).filter(Engagement.client_id == r.client_id).count(),
        eng.status,
        eng.materiality_amount,
        db.query(FollowUpItem).filter(FollowUpItem.engagement_id == r.engagement_id).count(),
        item.auditor_notes,
        item.archived_at,
        comment.comment_text,
        comment.archived_at,
        db.query(FollowUpItemComment).filter(FollowUpItemComment.follow_up_item_id == r.item_id).count(),
        db.query(AnalyticalExpectation).filter(AnalyticalExpectation.engagement_id == r.engagement_id).count(),
        exp.cpa_notes,
        exp.archived_at,
        exp.result_actual_value,
        db.query(UncorrectedMisstatement).filter(UncorrectedMisstatement.engagement_id == r.engagement_id).count(),
        mis.cpa_notes,
        mis.archived_at,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("state", PLAN_STATES)
@pytest.mark.parametrize("op", sorted(WRITES))
async def test_workspace_write_needs_a_live_paid_plan(world_factory, api, db_session, state, op):  # noqa: ANN001
    w = await world_factory(state)
    before = _snapshot(db_session, w.mine)
    r = await WRITES[op](api, w.mine, w.hdr)
    if state == "solo":
        assert r.status_code in (200, 201, 204), f"{op}: {r.status_code} {r.text}"
        assert _snapshot(db_session, w.mine) != before, f"{op} succeeded but changed nothing"
    else:
        assert r.status_code == 403, f"{op} as {state}: {r.status_code} {r.text}"
        body = r.json()
        assert "workspace" in str(body), body
        assert _snapshot(db_session, w.mine) == before, f"{op} as {state} was refused but changed state"


@pytest.mark.asyncio
@pytest.mark.parametrize("state", PLAN_STATES)
@pytest.mark.parametrize("op", sorted(WRITES))
async def test_another_firms_records_stay_out_of_reach(world_factory, api, db_session, state, op):  # noqa: ANN001
    w = await world_factory(state)
    before = _snapshot(db_session, w.theirs)
    r = await WRITES[op](api, w.theirs, w.hdr)
    # Solo is refused by the firm check (404); Free/lapsed by the plan gate (403).
    # Either way, nothing of theirs moves.
    assert r.status_code in (403, 404), f"{op} as {state} on another firm: {r.status_code} {r.text}"
    if state == "solo":
        assert r.status_code == 404, f"{op}: {r.status_code} {r.text}"
    assert _snapshot(db_session, w.theirs) == before


# ---------------------------------------------------------------------------
# Reads
# ---------------------------------------------------------------------------


def _reads(r: _Records) -> list[str]:
    e = r.engagement_id
    return [
        "/engagements",
        f"/engagements/{e}",
        f"/engagements/{e}/materiality",
        f"/engagements/{e}/tool-runs",
        f"/engagements/{e}/workpaper-index",
        f"/engagements/{e}/convergence",
        f"/engagements/{e}/tool-run-trends",
        f"/engagements/{e}/follow-up-items",
        f"/engagements/{e}/follow-up-items/summary",
        f"/engagements/{e}/follow-up-items/my-items",
        f"/engagements/{e}/follow-up-items/unassigned",
        f"/follow-up-items/{r.item_id}/comments",
        f"/engagements/{e}/analytical-expectations",
        f"/analytical-expectations/{r.expectation_id}",
        f"/engagements/{e}/uncorrected-misstatements",
        f"/engagements/{e}/sum-schedule",
        f"/uncorrected-misstatements/{r.misstatement_id}",
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("state", PLAN_STATES)
async def test_own_records_stay_readable_after_a_downgrade(world_factory, api, state):  # noqa: ANN001
    w = await world_factory(state)
    failures = []
    for path in _reads(w.mine):
        r = await api.get(path, headers=w.hdr)
        if r.status_code != 200:
            failures.append(f"{path}: {r.status_code} {r.text[:200]}")
    assert not failures, "\n".join(failures)
    listed = await api.get("/engagements", headers=w.hdr)
    assert w.mine.engagement_id in {row["id"] for row in listed.json()["items"]}


@pytest.mark.asyncio
@pytest.mark.parametrize("state", PLAN_STATES)
async def test_another_firms_records_are_not_readable(world_factory, api, state):  # noqa: ANN001
    w = await world_factory(state)
    leaks = []
    for path in _reads(w.theirs)[1:]:  # "/engagements" is the caller's own list
        r = await api.get(path, headers=w.hdr)
        if r.status_code != 404:
            leaks.append(f"{path}: {r.status_code}")
    assert not leaks, "\n".join(leaks)
    listed = await api.get("/engagements", headers=w.hdr)
    assert w.theirs.engagement_id not in {row["id"] for row in listed.json()["items"]}


def test_every_workspace_write_route_is_gated():
    """Structural backstop: a new write route on these routers must carry the gate."""
    import importlib

    from shared.entitlement_checks import check_workspace_access
    from tests.helpers.route_inventory import all_routes

    modules = [
        "routes.engagements",
        "routes.engagements_analytics",
        "routes.follow_up_items",
        "routes.analytical_expectations",
        "routes.uncorrected_misstatements",
    ]
    writes, ungated = 0, []
    for name in modules:
        for route in all_routes(importlib.import_module(name).router):
            methods = getattr(route, "methods", set()) or set()
            if not methods & {"POST", "PUT", "PATCH", "DELETE"}:
                continue
            # routes.engagements also mounts the engagement export router; those
            # POSTs are downloads gated by check_export_access, not workspace writes.
            if route.endpoint.__module__ != name:
                continue
            writes += 1
            deps = [d.dependency for d in getattr(route, "dependencies", []) or []]
            if check_workspace_access not in deps:
                ungated.append(f"{name} {sorted(methods)} {route.path}")
    assert writes == len(WRITES), f"{writes} write routes found, {len(WRITES)} exercised above"
    assert not ungated, ungated
