"""Sprint 879b (review DH-04): analysis proposes actuals; the auditor captures them.

Flux, multi-period and industry-ratio runs with an ``engagement_id`` used to
write every matching account's balance into ``result_actual_value`` with no
action from the auditor. Now a run returns ``proposed_actuals`` and saves
nothing; ``POST /engagements/{id}/analytical-expectations/capture-actuals``
saves one proposal or a whole run's, recording the run each came from. An
expectation with no captured actual prints "not captured" in the memo.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from analytical_expectations_manager import AnalyticalExpectationsManager
from analytical_expectations_model import AnalyticalExpectation, ExpectationResultStatus, ExpectationTargetType
from engagement_manager import EngagementManager
from models import UserTier
from tests.test_firm_owned_records import _auth, _subscribe, api  # noqa: F401 — `api` is a fixture

pytestmark = pytest.mark.usefixtures("bypass_csrf")

PRIOR = [
    {"account": "Revenue", "debit": 0, "credit": 1000, "type": "revenue"},
    {"account": "Cash", "debit": 5000, "credit": 0, "type": "asset"},
]
CURRENT = [
    {"account": "Revenue", "debit": 0, "credit": 1020, "type": "revenue"},
    {"account": "Cash", "debit": 5500, "credit": 0, "type": "asset"},
]
CAPTURE = "/engagements/{eid}/analytical-expectations/capture-actuals"


def _world(db_session, make_user, make_client, email: str):  # noqa: ANN001, ANN202
    user = make_user(email=email, tier=UserTier.SOLO)
    _subscribe(db_session, user, tier="solo")
    client = make_client(user=user)
    eng = EngagementManager(db_session).create_engagement(
        user.id,
        client.id,
        datetime(2025, 1, 1, tzinfo=UTC),
        datetime(2025, 12, 31, tzinfo=UTC),
        materiality_amount=100000.0,
    )
    mgr = AnalyticalExpectationsManager(db_session)
    common = {
        "precision_threshold_amount": 50.0,
        "corroboration_basis_text": "Prior",
        "corroboration_tags": ["prior_period"],
    }
    cash = mgr.create_expectation(
        user_id=user.id,
        engagement_id=eng.id,
        procedure_target_type=ExpectationTargetType.ACCOUNT,
        procedure_target_label="Cash",
        expected_value=5500.0,
        **common,
    )
    rev = mgr.create_expectation(
        user_id=user.id,
        engagement_id=eng.id,
        procedure_target_type=ExpectationTargetType.BALANCE,
        procedure_target_label="Revenue",
        expected_value=-1000.0,
        **common,
    )
    return user, eng, cash, rev


def _row(db_session, exp_id: int) -> AnalyticalExpectation:
    db_session.expire_all()
    return db_session.query(AnalyticalExpectation).filter(AnalyticalExpectation.id == exp_id).one()


def _untouched(row: AnalyticalExpectation) -> bool:
    return (
        row.result_actual_value is None
        and row.result_variance_amount is None
        and row.result_status == ExpectationResultStatus.NOT_EVALUATED
        and row.actual_source is None
        and row.actual_source_tool_run_id is None
    )


async def _compare(api, user, eng):  # noqa: ANN001, ANN202
    return await api.post(
        "/audit/compare-periods",
        json={"prior_accounts": PRIOR, "current_accounts": CURRENT, "engagement_id": eng.id},
        headers=_auth(user),
    )


@pytest.mark.asyncio
async def test_a_run_proposes_but_saves_nothing_and_reruns_save_nothing(api, make_user, make_client, db_session):  # noqa: ANN001
    user, eng, cash, rev = _world(db_session, make_user, make_client, "propose@example.com")
    for _ in range(2):
        r = await _compare(api, user, eng)
        assert r.status_code == 200, r.text
        body = r.json()
        assert "expectations_evaluated" not in body
        proposals = {p["expectation_id"]: p for p in body["proposed_actuals"]}
        assert proposals[cash.id]["actual"] == 5500.0
        assert proposals[cash.id]["target_label"] == "Cash"
        assert proposals[cash.id]["capture_token"]
        assert _untouched(_row(db_session, cash.id)) and _untouched(_row(db_session, rev.id))


@pytest.mark.asyncio
async def test_a_failed_analysis_saves_nothing(api, make_user, make_client, db_session):  # noqa: ANN001
    from unittest.mock import patch

    user, eng, cash, _ = _world(db_session, make_user, make_client, "fail@example.com")
    with patch("routes.multi_period.compare_trial_balances", side_effect=ValueError("engine failed")):
        try:
            await _compare(api, user, eng)
        except Exception:  # noqa: BLE001 — an unhandled engine error surfaces through ASGITransport
            pass
    assert _untouched(_row(db_session, cash.id))


@pytest.mark.asyncio
async def test_capture_one_saves_only_that_account_and_records_the_run(api, make_user, make_client, db_session):  # noqa: ANN001
    from engagement_model import ToolRun

    user, eng, cash, rev = _world(db_session, make_user, make_client, "capture-one@example.com")
    body = (await _compare(api, user, eng)).json()
    token = next(p["capture_token"] for p in body["proposed_actuals"] if p["expectation_id"] == cash.id)
    r = await api.post(CAPTURE.format(eid=eng.id), json={"capture_tokens": [token]}, headers=_auth(user))
    assert r.status_code == 200, r.text
    assert r.json()["results"] == [{"expectation_id": cash.id, "status": "captured", "reason": None}]

    row = _row(db_session, cash.id)
    assert row.result_actual_value == Decimal("5500.00")
    assert row.result_status == ExpectationResultStatus.WITHIN_THRESHOLD
    assert row.actual_source == "multi_period"
    run = db_session.query(ToolRun).filter(ToolRun.id == row.actual_source_tool_run_id).one()
    assert run.engagement_id == eng.id and run.tool_name.value == "multi_period"
    assert row.actual_captured_by == user.id and row.actual_captured_at is not None
    assert _untouched(_row(db_session, rev.id))


@pytest.mark.asyncio
async def test_capture_all_from_a_run(api, make_user, make_client, db_session):  # noqa: ANN001
    user, eng, cash, rev = _world(db_session, make_user, make_client, "capture-all@example.com")
    body = (await _compare(api, user, eng)).json()
    tokens = [p["capture_token"] for p in body["proposed_actuals"]]
    r = await api.post(CAPTURE.format(eid=eng.id), json={"capture_tokens": tokens}, headers=_auth(user))
    assert r.status_code == 200, r.text
    assert {x["expectation_id"] for x in r.json()["results"] if x["status"] == "captured"} == {cash.id, rev.id}
    run_ids = {_row(db_session, cash.id).actual_source_tool_run_id, _row(db_session, rev.id).actual_source_tool_run_id}
    assert len(run_ids) == 1 and None not in run_ids
    # Capturing again does not overwrite.
    r = await api.post(CAPTURE.format(eid=eng.id), json={"capture_tokens": tokens}, headers=_auth(user))
    assert all(x["status"] == "skipped" for x in r.json()["results"])


@pytest.mark.asyncio
async def test_a_forged_token_saves_nothing(api, make_user, make_client, db_session):  # noqa: ANN001
    user, eng, cash, _ = _world(db_session, make_user, make_client, "forged@example.com")
    body = (await _compare(api, user, eng)).json()
    good = next(p["capture_token"] for p in body["proposed_actuals"] if p["expectation_id"] == cash.id)
    payload, sig = good.split(".")
    import base64
    import json

    claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    claims["a"] = "1.00"
    forged = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode() + "." + sig
    r = await api.post(CAPTURE.format(eid=eng.id), json={"capture_tokens": [good, forged]}, headers=_auth(user))
    assert r.status_code == 400, r.text
    assert _untouched(_row(db_session, cash.id))


@pytest.mark.asyncio
async def test_another_user_cannot_use_the_token(api, make_user, make_client, db_session):  # noqa: ANN001
    user, eng, cash, _ = _world(db_session, make_user, make_client, "owner-tok@example.com")
    other, other_eng, _, _ = _world(db_session, make_user, make_client, "thief-tok@example.com")
    token = (await _compare(api, user, eng)).json()["proposed_actuals"][0]["capture_token"]
    r = await api.post(CAPTURE.format(eid=other_eng.id), json={"capture_tokens": [token]}, headers=_auth(other))
    assert r.status_code == 400, r.text
    r = await api.post(CAPTURE.format(eid=eng.id), json={"capture_tokens": [token]}, headers=_auth(other))
    assert r.status_code in (400, 404), r.text
    assert _untouched(_row(db_session, cash.id))


@pytest.mark.asyncio
async def test_free_cannot_capture(api, make_user, make_client, db_session):  # noqa: ANN001
    from shared.expectation_capture import sign_capture

    user, eng, cash, _ = _world(db_session, make_user, make_client, "free-cap@example.com")
    free = make_user(email="free-cap-2@example.com", tier=UserTier.FREE)
    token = sign_capture(
        user_id=free.id,
        engagement_id=eng.id,
        expectation_id=cash.id,
        actual=5500,
        source="multi_period",
        tool_run_id=None,
    )
    r = await api.post(CAPTURE.format(eid=eng.id), json={"capture_tokens": [token]}, headers=_auth(free))
    assert r.status_code == 403, r.text
    assert _untouched(_row(db_session, cash.id))


def test_flux_and_ratio_helpers_never_write(db_session, make_user, make_client):
    """The shared helper the flux and industry-ratio routes call only reads."""
    from shared.expectation_evaluation import extract_flux_measurements, propose_expectation_actuals

    user, eng, cash, _ = _world(db_session, make_user, make_client, "helper@example.com")
    flux = {"items": [{"account": "Cash", "current": 5500.0, "delta_amount": 500.0}]}
    out = propose_expectation_actuals(
        db_session, user.id, eng.id, extract_flux_measurements(flux), source="flux_analysis", tool_run_id=None
    )
    assert [p["expectation_id"] for p in out] == [cash.id]
    assert not db_session.dirty and not db_session.new
    assert _untouched(_row(db_session, cash.id))


def test_manual_capture_is_recorded_as_manual(db_session, make_user, make_client):
    user, eng, cash, _ = _world(db_session, make_user, make_client, "manual@example.com")
    AnalyticalExpectationsManager(db_session).update_expectation(user.id, cash.id, result_actual_value=5400.0)
    row = _row(db_session, cash.id)
    assert row.actual_source == "manual" and row.actual_source_tool_run_id is None
    AnalyticalExpectationsManager(db_session).update_expectation(user.id, cash.id, clear_result=True)
    assert _untouched(_row(db_session, cash.id))


def test_memo_prints_not_captured(db_session, make_user, make_client):
    import io

    from pypdf import PdfReader

    from analytical_expectation_memo_generator import AnalyticalExpectationMemoGenerator

    user, eng, cash, rev = _world(db_session, make_user, make_client, "memo@example.com")
    AnalyticalExpectationsManager(db_session).update_expectation(user.id, rev.id, result_actual_value=0)

    pdf = AnalyticalExpectationMemoGenerator(db_session).generate_pdf(user.id, eng.id)
    text = " ".join(" ".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(pdf)).pages).split())
    # Cash has no actual: its row says so (actual and variance), never blank or $0.00.
    cash_row = text[text.index("Cash") : text.index("Cash") + 200]
    assert cash_row.count("not captured") >= 2, cash_row
    # Revenue's captured zero is a real zero.
    assert "$0.00" in text
