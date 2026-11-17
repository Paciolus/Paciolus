"""Sprint 879c (review DH-05): an activity summary holds approved aggregates only.

``POST /activity/tool-log`` took ``summary`` as a free 2,000-character query
string and stored it verbatim; ``shared.tool_run_recorder`` serialised any
dict. Now both go through ``shared.activity_summary.validate_activity_summary``
and the API takes a typed JSON body.
"""

from __future__ import annotations

import json
import logging

import pytest

from models import ToolActivity, UserTier
from shared.activity_summary import ActivitySummaryError, validate_activity_summary
from tests.test_firm_owned_records import _auth, api  # noqa: F401 — `api` is a fixture

pytestmark = pytest.mark.usefixtures("bypass_csrf")

M = "MKRSUMZZ9"  # a value that must never be stored or logged

BAD_SUMMARIES = {
    "balance": {"cash_balance": 125_430.55},
    "balance_as_string_in_known_field": {"anomaly_count": "125430.55"},
    "transaction_rows": {"anomaly_count": 1, "rows": [{"date": "2025-01-05", "amount": -45.99, "memo": M}]},
    "payroll_rows": {"employees": [{"name": M, "gross": 5200.0, "ssn_last4": "1234"}]},
    "file_content": {"raw": f"Account,Debit,Credit\nCash {M},1000,0\n"},
    "nested": {"anomaly_count": {"value": 3}},
    "list_value": {"anomaly_count": [3]},
    "bool_as_int": {"was_balanced": 1},
    "negative_count": {"anomaly_count": -1},
    "key_carries_value": {f"Cash {M} 12,400.55": 1},
    "not_an_object": [1, 2, 3],
}


@pytest.mark.parametrize("name", sorted(BAD_SUMMARIES))
def test_validator_rejects(name):
    with pytest.raises(ActivitySummaryError) as exc:
        validate_activity_summary("trial_balance", BAD_SUMMARIES[name])
    assert M not in str(exc.value)


def test_validator_rejects_unknown_tool():
    with pytest.raises(ActivitySummaryError):
        validate_activity_summary("payroll_dump", {"flagged_count": 1})


def test_validator_accepts_approved_aggregates():
    assert validate_activity_summary("trial_balance", {"was_balanced": True, "anomaly_count": 4}) == {
        "was_balanced": True,
        "anomaly_count": 4,
    }
    assert validate_activity_summary("ap_testing", {"flagged_count": 2, "composite_score": 41.5}) == {
        "flagged_count": 2,
        "composite_score": 41.5,
    }
    assert validate_activity_summary("preflight", {"flagged_count": 0}) == {"flagged_count": 0}
    assert validate_activity_summary("trial_balance", None) is None
    assert validate_activity_summary("trial_balance", {}) is None


# --- internal recorder ------------------------------------------------------


@pytest.mark.parametrize("name", ["balance", "transaction_rows", "payroll_rows", "file_content", "nested"])
def test_recorder_refuses_and_stores_nothing(db_session, make_user, name):
    from shared.tool_run_recorder import maybe_record_tool_run

    user = make_user(email=f"rec-{name.replace('_', '-')}@example.com")
    with pytest.raises(ActivitySummaryError):
        maybe_record_tool_run(db_session, None, user.id, "trial_balance", True, summary=BAD_SUMMARIES[name])
    assert db_session.query(ToolActivity).filter(ToolActivity.user_id == user.id).count() == 0


def test_recorder_round_trips_a_valid_summary(db_session, make_user):
    from shared.tool_run_recorder import maybe_record_tool_run

    user = make_user(email="rec-ok@example.com")
    maybe_record_tool_run(
        db_session, None, user.id, "trial_balance", True, summary={"was_balanced": False, "anomaly_count": 3}
    )
    row = db_session.query(ToolActivity).filter(ToolActivity.user_id == user.id).one()
    assert json.loads(row.summary_json) == {"was_balanced": False, "anomaly_count": 3}


# --- API --------------------------------------------------------------------

URL = "/activity/tool-log"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "name", ["balance", "transaction_rows", "payroll_rows", "file_content", "nested", "key_carries_value"]
)
async def test_api_rejects_and_stores_nothing(api, make_user, db_session, caplog, name):  # noqa: ANN001
    user = make_user(email=f"api-{name.replace('_', '-')}@example.com", tier=UserTier.SOLO)
    with caplog.at_level(logging.DEBUG):
        r = await api.post(
            URL, json={"tool_name": "trial_balance", "summary": BAD_SUMMARIES[name]}, headers=_auth(user)
        )
    assert r.status_code == 422, r.text
    assert M not in r.text
    assert db_session.query(ToolActivity).filter(ToolActivity.user_id == user.id).count() == 0
    logged = "\n".join(rec.getMessage() for rec in caplog.records)
    assert M not in logged and "125430.55" not in logged and "125,430.55" not in logged


@pytest.mark.asyncio
async def test_api_rejects_unknown_tool_and_unknown_body_fields(api, make_user):  # noqa: ANN001
    user = make_user(email="api-unknown@example.com", tier=UserTier.SOLO)
    r = await api.post(URL, json={"tool_name": "payroll_dump"}, headers=_auth(user))
    assert r.status_code == 422, r.text
    r = await api.post(URL, json={"tool_name": "ap_testing", "rows": [[M]]}, headers=_auth(user))
    assert r.status_code == 422, r.text


@pytest.mark.asyncio
async def test_api_no_longer_reads_the_query_string(api, make_user, db_session):  # noqa: ANN001
    user = make_user(email="api-query@example.com", tier=UserTier.SOLO)
    r = await api.post(f"{URL}?tool_name=trial_balance&summary=%7B%22raw%22%3A%22{M}%22%7D", headers=_auth(user))
    assert r.status_code == 422, r.text
    assert db_session.query(ToolActivity).filter(ToolActivity.user_id == user.id).count() == 0


@pytest.mark.asyncio
async def test_api_round_trips_a_valid_summary(api, make_user):  # noqa: ANN001
    user = make_user(email="api-ok@example.com", tier=UserTier.SOLO)
    body = {"tool_name": "ap_testing", "record_count": 120, "summary": {"flagged_count": 7, "composite_score": 33.0}}
    r = await api.post(URL, json=body, headers=_auth(user))
    assert r.status_code == 201, r.text
    assert r.json()["summary"] == {"flagged_count": 7, "composite_score": 33.0}
    feed = await api.get("/activity/tool-feed", headers=_auth(user))
    assert feed.json()[0]["summary"] == {"flagged_count": 7, "composite_score": 33.0}


def test_feed_drops_a_stored_summary_that_fails_the_schema(db_session, make_user):
    from shared.activity_summary import load_stored_summary

    assert load_stored_summary("trial_balance", json.dumps({"cash_balance": 1.0})) is None
    assert load_stored_summary("trial_balance", "not json") is None
    assert load_stored_summary("trial_balance", json.dumps({"anomaly_count": 2})) == {"anomaly_count": 2}


def test_migration_clears_stored_summaries_that_fail_the_schema(tmp_path):
    """f879c3e5b7d2 nulls every invalid stored summary and keeps the rows."""
    import importlib.util
    from pathlib import Path

    import sqlalchemy as sa
    from alembic.migration import MigrationContext
    from alembic.operations import Operations

    path = (
        Path(__file__).resolve().parent.parent
        / "migrations/alembic/versions/f879c3e5b7d2_activity_summary_schema_sprint_879.py"
    )
    spec = importlib.util.spec_from_file_location("mig_f879c3", path)
    mig = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mig)

    engine = sa.create_engine(f"sqlite:///{tmp_path / 'm.db'}")
    rows = {
        1: ("trial_balance", json.dumps({"was_balanced": True, "anomaly_count": 2})),  # valid
        2: ("trial_balance", json.dumps({"cash_balance": 125430.55})),
        3: ("ap_testing", json.dumps({"flagged_count": 1, "rows": [[M]]})),
        4: ("payroll_dump", json.dumps({"flagged_count": 1})),
        5: ("ap_testing", f"raw text {M}"),
        6: ("ap_testing", json.dumps({"flagged_count": 3, "composite_score": 12.5})),  # valid
        7: ("trial_balance", None),
    }
    with engine.begin() as conn:
        conn.execute(
            sa.text("CREATE TABLE tool_activities (id INTEGER PRIMARY KEY, tool_name TEXT, summary_json TEXT)")
        )
        for i, (tool, summary) in rows.items():
            conn.execute(sa.text("INSERT INTO tool_activities VALUES (:i, :t, :s)"), {"i": i, "t": tool, "s": summary})
        with Operations.context(MigrationContext.configure(conn)):
            mig.upgrade()
        kept = dict(conn.execute(sa.text("SELECT id, summary_json FROM tool_activities")).all())
    assert set(kept) == set(rows)  # no row deleted
    assert kept[1] == rows[1][1] and kept[6] == rows[6][1]
    assert all(kept[i] is None for i in (2, 3, 4, 5, 7))
