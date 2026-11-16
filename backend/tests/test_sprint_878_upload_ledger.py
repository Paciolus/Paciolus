"""Sprint 878 (review AZ-05): the upload allowance is metered on the server.

A user without an active metered subscription (Free, or a lapsed plan) was
counted from this month's unarchived ``ActivityLog`` rows. The browser writes
those rows itself, in a separate ``POST /activity/log`` after the analysis
(``frontend/src/hooks/useTrialBalanceUpload.ts``), and ``DELETE /activity/clear``
archives them. ``increment_upload_count`` returned early when there was no
subscription row. So skipping the log call, or clearing history, reset the
allowance.

Now each successful metered run writes one row to a server-side usage ledger
(``upload_usage_events``) that the history endpoints never touch. A firm
member with no subscription of their own is metered on the firm's
subscription counter, one allowance shared by the firm (CEO decision).
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from models import UserTier
from tests.test_firm_owned_records import _auth, _firm, _join, api  # noqa: F401 — `api` is a fixture
from tests.test_sprint_790_upload_metering import _counter, _subscribe

pytestmark = pytest.mark.usefixtures("bypass_csrf")

FREE_ALLOWANCE = 10


def _tb(n: int) -> bytes:
    return f"Account,Debit,Credit\nCash {n},{100 + n},0\nRevenue {n},0,{100 + n}\n".encode()


async def _analyse(api, hdr, n: int):  # noqa: ANN001, ANN202
    return await api.post(
        "/audit/trial-balance",
        files={"file": (f"tb_{n}.csv", _tb(n), "text/csv")},
        data={"force_resubmit": "true"},
        headers=hdr,
    )


async def _log_like_the_browser(api, hdr, n: int):  # noqa: ANN001, ANN202
    r = await api.post(
        "/activity/log",
        json={
            "filename": f"tb_{n}.csv",
            "record_count": 2,
            "total_debits": 100 + n,
            "total_credits": 100 + n,
            "materiality_threshold": 0,
            "was_balanced": True,
        },
        headers=hdr,
    )
    assert r.status_code == 201, r.text


def _refused_for_uploads(r) -> bool:  # noqa: ANN001
    return r.status_code == 403 and r.json()["detail"]["resource"] == "uploads"


def _ledger_rows(db: Session, user_id: int) -> int:
    from upload_usage_model import UploadUsageEvent

    db.expire_all()
    return db.query(UploadUsageEvent).filter(UploadUsageEvent.user_id == user_id).count()


@pytest.mark.asyncio
async def test_free_allowance_holds_with_no_client_log_calls(api, make_user, db_session):  # noqa: ANN001
    user = make_user(email="free-nolog@example.com", tier=UserTier.FREE)
    hdr = _auth(user)
    for n in range(FREE_ALLOWANCE):
        r = await _analyse(api, hdr, n)
        assert r.status_code == 200, f"run {n + 1}: {r.status_code} {r.text}"
    r = await _analyse(api, hdr, 99)
    assert _refused_for_uploads(r), f"run 11: {r.status_code} {r.text}"
    assert _ledger_rows(db_session, user.id) == FREE_ALLOWANCE


@pytest.mark.asyncio
async def test_clearing_history_does_not_restore_the_allowance(api, make_user, db_session):  # noqa: ANN001
    from shared.entitlement_checks import uploads_used_this_period

    user = make_user(email="free-clear@example.com", tier=UserTier.FREE)
    hdr = _auth(user)
    for n in range(FREE_ALLOWANCE):
        assert (await _analyse(api, hdr, n)).status_code == 200
        await _log_like_the_browser(api, hdr, n)
    assert _refused_for_uploads(await _analyse(api, hdr, 99))

    r = await api.delete("/activity/clear", headers=hdr)
    assert r.status_code == 204, r.text

    db_session.expire_all()
    assert uploads_used_this_period(db_session, user.id) == FREE_ALLOWANCE
    assert _refused_for_uploads(await _analyse(api, hdr, 100))
    assert _ledger_rows(db_session, user.id) == FREE_ALLOWANCE


@pytest.mark.asyncio
async def test_a_failed_run_consumes_nothing(api, make_user, db_session):  # noqa: ANN001
    from unittest.mock import patch

    user = make_user(email="free-fail@example.com", tier=UserTier.FREE)
    with patch("routes.audit_pipeline.audit_trial_balance_streaming", side_effect=ValueError("bad input")):
        r = await _analyse(api, _auth(user), 1)
    assert r.status_code == 400, r.text
    assert _ledger_rows(db_session, user.id) == 0


def test_lapsed_subscription_is_metered_on_the_ledger(make_user, db_session):  # noqa: ANN001
    from shared.entitlement_checks import increment_upload_count, uploads_used_this_period
    from subscription_model import SubscriptionStatus

    user = make_user(email="lapsed-ledger@example.com", tier=UserTier.SOLO)
    sub = _subscribe(db_session, user, used=3, tier="solo", status=SubscriptionStatus.CANCELED)
    increment_upload_count(db_session, user.id)
    assert _ledger_rows(db_session, user.id) == 1
    assert uploads_used_this_period(db_session, user.id) == 1
    assert _counter(db_session, user.id) == 3, "a lapsed row's frozen counter is not the meter"
    assert sub.status == SubscriptionStatus.CANCELED


@pytest.mark.asyncio
async def test_firm_member_without_a_subscription_is_metered_against_the_firm(api, make_user, db_session):  # noqa: ANN001
    from shared.entitlement_checks import uploads_used_this_period

    owner = make_user(email="owner@meter-firm.test")
    member = make_user(email="member@meter-firm.test")
    org = _firm(db_session, owner, "Meter Firm")
    _join(db_session, org, member)
    from subscription_model import Subscription

    sub = db_session.get(Subscription, org.subscription_id)
    sub.uploads_used_current_period = 498
    sub.current_period_start, sub.current_period_end, sub.uploads_window_start = _subscribe_window()
    db_session.flush()

    owner_hdr, member_hdr = _auth(owner), _auth(member)
    r = await _analyse(api, member_hdr, 1)
    assert r.status_code == 200, r.text
    assert _counter(db_session, owner.id) == 499, "the member's run is counted on the firm's subscription"
    assert _ledger_rows(db_session, member.id) == 0

    r = await _analyse(api, owner_hdr, 2)
    assert r.status_code == 200, r.text
    assert _counter(db_session, owner.id) == 500

    # One allowance, shared: both are now at the firm's 500.
    db_session.expire_all()
    assert uploads_used_this_period(db_session, member.id) == 500
    assert _refused_for_uploads(await _analyse(api, member_hdr, 3))
    assert _refused_for_uploads(await _analyse(api, owner_hdr, 4))


def _subscribe_window():  # noqa: ANN202
    from datetime import UTC, datetime, timedelta

    start = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=1)
    return start, start + timedelta(days=30), start


def test_history_endpoints_never_touch_the_ledger():
    """Structural backstop: nothing under routes/ may archive, delete or update usage rows."""
    import ast
    from pathlib import Path

    backend = Path(__file__).resolve().parent.parent
    offenders = []
    for path in sorted((backend / "routes").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id == "UploadUsageEvent":
                offenders.append(f"{path.name}:{node.lineno}")
    assert not offenders, f"routes reference the usage ledger directly: {offenders}"
