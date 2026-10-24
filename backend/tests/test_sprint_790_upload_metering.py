"""
Sprint 790 — the monthly upload allowance is metered on every paid tier.

``check_upload_limit`` read ``Subscription.uploads_used_current_period`` on
every gated route, but only bulk upload ever advanced it — for files it never
analysed — so the paid caps
(100 Solo / 500 Professional) were never enforced.

Metering unit: **one successful analysis run is one upload.** A run that takes
two files costs one; a failed run costs nothing. The increment lives in
``maybe_record_tool_run``'s success path behind ``consumes_upload=True``, which
only gated routes pass. ``TestCheckAndIncrementAreSymmetric`` holds that
pairing mechanically, in both directions — its absence is what let the gap sit.
"""

from __future__ import annotations

import ast
import io
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest

_BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BACKEND))


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _subscribe(db_session, user, *, used: int = 0, status=None, tier: str = "professional"):
    from subscription_model import BillingInterval, Subscription, SubscriptionStatus

    sub = Subscription(
        user_id=user.id,
        tier=tier,
        status=status or SubscriptionStatus.ACTIVE,
        billing_interval=BillingInterval.MONTHLY,
        uploads_used_current_period=used,
        **_current_window(),
    )
    db_session.add(sub)
    db_session.flush()
    return sub


def _naive_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _current_window() -> dict:
    """A monthly period that started yesterday, with the counter's window open on it."""
    start = _naive_now() - timedelta(days=1)
    return {
        "current_period_start": start,
        "current_period_end": start + timedelta(days=30),
        "uploads_window_start": start,
    }


def _counter(db_session, user_id: int) -> int:
    from sqlalchemy import text

    return db_session.execute(
        text("SELECT uploads_used_current_period FROM subscriptions WHERE user_id = :u"), {"u": user_id}
    ).scalar_one()


def _override(user, db_session):
    from auth import require_current_user, require_verified_user
    from database import get_db
    from main import app

    app.dependency_overrides[require_current_user] = lambda: user
    app.dependency_overrides[require_verified_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: db_session
    return app


def _book_to_tax_payload() -> dict:
    return {
        "tax_year": 2025,
        "book_pretax_income": "500000.00",
        "total_assets": "5000000.00",
        "federal_tax_rate": "0.21",
        "state_tax_rate": "0.05",
        "adjustments": [
            {"label": "Meals (50%)", "amount": "10000.00", "difference_type": "permanent", "direction": "add"},
        ],
        "rollforward": {"beginning_dta": "0", "beginning_dtl": "0"},
    }


def _xlsx() -> bytes:
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.append(["Account", "Debit", "Credit"])
    ws.append(["1000 Cash", 10000, 0])
    ws.append(["2000 AP", 0, 10000])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


@dataclass
class _FakeFlux:
    items: list = field(default_factory=list)

    def to_dict(self):
        return {
            "items": self.items,
            "summary": {
                "total_items": 0,
                "high_risk_count": 0,
                "medium_risk_count": 0,
                "new_accounts": 0,
                "removed_accounts": 0,
                "reclassification_count": 0,
                "threshold": 5000.0,
            },
        }


@dataclass
class _FakeRecon:
    def to_dict(self):
        return {"scores": [], "stats": {"high": 0, "medium": 0, "low": 0}}


# ---------------------------------------------------------------------------
# the recorder
# ---------------------------------------------------------------------------


class TestRecorderMeters:
    def test_success_with_flag_advances_the_counter_once(self, make_user, db_session):
        from shared.tool_run_recorder import maybe_record_tool_run

        user = make_user(email="m790-a@example.com")
        _subscribe(db_session, user, used=4)
        maybe_record_tool_run(db_session, None, user.id, "ap_testing", True, consumes_upload=True)
        assert _counter(db_session, user.id) == 5

    def test_failure_never_consumes(self, make_user, db_session):
        from shared.tool_run_recorder import maybe_record_tool_run

        user = make_user(email="m790-b@example.com")
        _subscribe(db_session, user, used=4)
        maybe_record_tool_run(db_session, None, user.id, "ap_testing", False, consumes_upload=True)
        assert _counter(db_session, user.id) == 4

    def test_unflagged_success_does_not_consume(self, make_user, db_session):
        """An ungated side-analysis must not draw down a quota it was never checked against."""
        from shared.tool_run_recorder import maybe_record_tool_run

        user = make_user(email="m790-c@example.com")
        _subscribe(db_session, user, used=4)
        maybe_record_tool_run(db_session, None, user.id, "preflight", True)
        assert _counter(db_session, user.id) == 4

    def test_free_user_without_a_subscription_is_not_double_counted(self, make_user, db_session):
        """Free is metered from ActivityLog; the recorder must neither error nor create a row."""
        from models import ActivityLog, UserTier
        from shared.entitlement_checks import uploads_used_this_period
        from shared.tool_run_recorder import maybe_record_tool_run
        from subscription_model import Subscription

        user = make_user(email="m790-d@example.com", tier=UserTier.FREE)
        before = uploads_used_this_period(db_session, user.id)
        maybe_record_tool_run(db_session, None, user.id, "flux_analysis", True, consumes_upload=True)
        assert db_session.query(Subscription).filter_by(user_id=user.id).count() == 0
        assert db_session.query(ActivityLog).filter_by(user_id=user.id).count() == 0
        assert uploads_used_this_period(db_session, user.id) == before

    def test_a_counter_failure_does_not_fail_the_run(self, make_user, db_session):
        from shared.tool_run_recorder import maybe_record_tool_run

        user = make_user(email="m790-e@example.com")
        _subscribe(db_session, user, used=1)
        with patch("shared.entitlement_checks.increment_upload_count", side_effect=RuntimeError("db down")):
            maybe_record_tool_run(db_session, None, user.id, "ap_testing", True, consumes_upload=True)

    def test_increment_is_visible_to_the_next_limit_check(self, make_user, db_session):
        from fastapi import HTTPException

        from models import UserTier
        from shared.entitlement_checks import check_upload_limit
        from shared.tool_run_recorder import maybe_record_tool_run

        user = make_user(email="m790-f@example.com", tier=UserTier.SOLO)
        _subscribe(db_session, user, used=99, tier="solo")
        check_upload_limit(user=user, db=db_session)  # 99/100: allowed, and caches the row
        maybe_record_tool_run(db_session, None, user.id, "ap_testing", True, consumes_upload=True)
        with pytest.raises(HTTPException) as exc:
            check_upload_limit(user=user, db=db_session)
        assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# through the real routes
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("bypass_csrf")
class TestRoutesMeter:
    @pytest.mark.asyncio
    async def test_each_successful_run_counts_once(self, make_user, db_session):
        user = make_user(email="m790-r1@example.com")
        _subscribe(db_session, user)
        app = _override(user, db_session)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                for expected in (1, 2):
                    response = await client.post("/audit/book-to-tax", json=_book_to_tax_payload())
                    assert response.status_code == 200, response.text
                    assert _counter(db_session, user.id) == expected
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_a_400_does_not_consume(self, make_user, db_session):
        user = make_user(email="m790-r2@example.com")
        _subscribe(db_session, user, used=7)
        app = _override(user, db_session)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                with patch("routes.book_to_tax.calculate_book_to_tax", side_effect=ValueError("bad input")):
                    response = await client.post("/audit/book-to-tax", json=_book_to_tax_payload())
            assert response.status_code == 400, response.text
            assert _counter(db_session, user.id) == 7
        finally:
            app.dependency_overrides.clear()

    async def _flux(self, db_session, user, **engine):
        app = _override(user, db_session)
        xlsx = _xlsx()
        try:
            with (
                patch("routes.audit_flux.run_flux_analysis", **engine),
                patch("routes.audit_flux.resolve_materiality", return_value=(0.0, "default")),
                patch("routes.audit_flux.extract_flux_accounts", return_value=[]),
            ):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                    return await client.post(
                        "/audit/flux",
                        files={
                            "current_file": ("curr.xlsx", xlsx, "application/octet-stream"),
                            "prior_file": ("prior.xlsx", xlsx, "application/octet-stream"),
                        },
                    )
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_a_two_file_run_counts_once(self, make_user, db_session):
        user = make_user(email="m790-r3@example.com")
        _subscribe(db_session, user, used=2)
        response = await self._flux(db_session, user, return_value=(_FakeFlux(), _FakeRecon()))
        assert response.status_code == 200, response.text
        assert _counter(db_session, user.id) == 3

    @pytest.mark.asyncio
    async def test_an_engine_error_does_not_consume(self, make_user, db_session):
        user = make_user(email="m790-r4@example.com")
        _subscribe(db_session, user, used=2)
        response = await self._flux(db_session, user, side_effect=ValueError("bad data"))
        assert response.status_code >= 400
        assert _counter(db_session, user.id) == 2

    @pytest.mark.asyncio
    async def test_a_refused_run_does_not_consume(self, make_user, db_session):
        from models import UserTier

        user = make_user(email="m790-r5@example.com", tier=UserTier.SOLO)
        _subscribe(db_session, user, used=100, tier="solo")
        app = _override(user, db_session)
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/audit/book-to-tax", json=_book_to_tax_payload())
            assert response.status_code == 403
            assert response.json()["detail"]["resource"] == "uploads"
            assert _counter(db_session, user.id) == 100
        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# count source: no stale counter locks anyone out
# ---------------------------------------------------------------------------


class TestCountSource:
    def test_lapsed_subscription_is_metered_like_free_not_by_its_frozen_counter(self, make_user, db_session):
        """A CANCELED row is never reset again; its counter must not be the meter."""
        from models import UserTier
        from shared.entitlement_checks import check_upload_limit, uploads_used_this_period
        from subscription_model import SubscriptionStatus

        user = make_user(email="m790-s1@example.com", tier=UserTier.FREE)
        _subscribe(db_session, user, used=250, status=SubscriptionStatus.CANCELED)
        assert uploads_used_this_period(db_session, user.id) == 0
        check_upload_limit(user=user, db=db_session)  # does not raise

    def test_usage_display_uses_the_gate_s_number(self, make_user, db_session):
        from billing.usage_service import get_usage_stats
        from subscription_model import SubscriptionStatus

        active = make_user(email="m790-s2@example.com")
        _subscribe(db_session, active, used=12)
        assert get_usage_stats(db_session, active.id, "professional").uploads_used == 12

        lapsed = make_user(email="m790-s3@example.com")
        _subscribe(db_session, lapsed, used=12, status=SubscriptionStatus.PAST_DUE)
        assert get_usage_stats(db_session, lapsed.id, "free").uploads_used == 0


class TestPeriodRolloverResets:
    def _stripe_sub(self, start: datetime) -> dict:
        end = start + timedelta(days=30)
        return {
            "id": "sub_790",
            "status": "active",
            "current_period_start": int(start.timestamp()),
            "current_period_end": int(end.timestamp()),
            "items": {"data": [{"plan": {"interval": "month"}, "quantity": 1}]},
        }

    def test_renewal_zeroes_the_counter_and_a_repeat_event_does_not(self, make_user, db_session):
        from billing.subscription_manager import sync_subscription_from_stripe

        user = make_user(email="m790-p1@example.com")
        first = datetime(2026, 9, 1, tzinfo=UTC)
        sync_subscription_from_stripe(db_session, user.id, self._stripe_sub(first), "cus_790", "professional")
        sub = _subscribe_lookup(db_session, user.id)
        sub.uploads_used_current_period = 40
        db_session.flush()

        # Same period re-delivered (or any non-renewal update): keep the count.
        sync_subscription_from_stripe(db_session, user.id, self._stripe_sub(first), "cus_790", "professional")
        assert sub.uploads_used_current_period == 40

        # Renewal: a new allowance.
        renewed = first + timedelta(days=30)
        sync_subscription_from_stripe(db_session, user.id, self._stripe_sub(renewed), "cus_790", "professional")
        assert sub.uploads_used_current_period == 0

        # An out-of-order older event does not reset again.
        sub.uploads_used_current_period = 5
        sync_subscription_from_stripe(db_session, user.id, self._stripe_sub(first), "cus_790", "professional")
        assert sub.uploads_used_current_period == 5


def _subscribe_lookup(db_session, user_id):
    from subscription_model import Subscription

    return db_session.query(Subscription).filter_by(user_id=user_id).one()


# ---------------------------------------------------------------------------
# the deploy-time reset migration
# ---------------------------------------------------------------------------


def _alembic_upgrade(db_url: str, target: str) -> None:
    from alembic import command
    from alembic.config import Config

    import config

    original = config.DATABASE_URL
    config.DATABASE_URL = db_url
    try:
        cfg = Config(str(_BACKEND / "alembic.ini"))
        cfg.set_main_option("sqlalchemy.url", db_url)
        cfg.set_main_option("script_location", str(_BACKEND / "migrations" / "alembic"))
        cfg.config_file_name = None  # keep pytest's logging handlers (see test_alembic_models_parity)
        command.upgrade(cfg, target)
    finally:
        config.DATABASE_URL = original


def test_migration_resets_every_counter(tmp_path):
    from sqlalchemy import create_engine, text

    url = f"sqlite:///{(tmp_path / 'm790.db').as_posix()}"
    _alembic_upgrade(url, "c9e4a1b73f20")

    engine = create_engine(url)
    with engine.begin() as conn:
        for user_id, used in ((1, 42), (2, 0), (3, 7)):
            conn.execute(
                text(
                    "INSERT INTO subscriptions (user_id, tier, status, seat_count, additional_seats, "
                    "uploads_used_current_period, seat_version, cancel_at_period_end, created_at, updated_at) "
                    "VALUES (:u, 'professional', 'active', 1, 0, :n, 0, 0, :ts, :ts)"
                ),
                {"u": user_id, "n": used, "ts": datetime(2026, 10, 1)},
            )

    _alembic_upgrade(url, "e7a90c3d5b18")

    with engine.connect() as conn:
        values = conn.execute(text("SELECT uploads_used_current_period FROM subscriptions")).scalars().all()
    engine.dispose()
    assert values == [0, 0, 0]


def test_sprint_790_migrations_are_the_single_head():
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    cfg = Config(str(_BACKEND / "alembic.ini"))
    cfg.set_main_option("script_location", str(_BACKEND / "migrations" / "alembic"))
    assert ScriptDirectory.from_config(cfg).get_heads() == ["f3b81d6e2a47"]


# ---------------------------------------------------------------------------
# PR #227 review, P1 #1: metering must not move the webhook-ordering timestamp
# ---------------------------------------------------------------------------


def _pin_updated_at(db_session, user_id: int, when: datetime) -> None:
    from sqlalchemy import text

    db_session.execute(text("UPDATE subscriptions SET updated_at = :w WHERE user_id = :u"), {"w": when, "u": user_id})
    db_session.commit()
    db_session.expire_all()


def _updated_at(db_session, user_id: int) -> datetime:
    from sqlalchemy import text

    raw = db_session.execute(
        text("SELECT updated_at FROM subscriptions WHERE user_id = :u"), {"u": user_id}
    ).scalar_one()
    return raw if isinstance(raw, datetime) else datetime.fromisoformat(str(raw))


class TestMeteringLeavesUpdatedAtAlone:
    def test_an_increment_does_not_move_updated_at(self, make_user, db_session):
        from shared.entitlement_checks import increment_upload_count

        user = make_user(email="m790-u1@example.com")
        _subscribe(db_session, user, used=3)
        pinned = datetime(2026, 1, 2, 3, 4, 5)
        _pin_updated_at(db_session, user.id, pinned)

        increment_upload_count(db_session, user.id)

        assert _counter(db_session, user.id) == 4
        assert _updated_at(db_session, user.id) == pinned

    def test_the_hourly_quota_reset_does_not_move_updated_at(self, make_user, db_session):
        from cleanup_scheduler import reset_upload_quotas

        user = make_user(email="m790-u2@example.com")
        sub = _subscribe(db_session, user, used=9)
        sub.current_period_end = _naive_now() - timedelta(days=1)
        db_session.flush()
        pinned = datetime(2026, 1, 2, 3, 4, 5)
        _pin_updated_at(db_session, user.id, pinned)

        assert reset_upload_quotas(db_session) >= 1

        assert _counter(db_session, user.id) == 0
        assert _updated_at(db_session, user.id) == pinned

    def test_an_older_undelivered_webhook_is_still_processed_after_an_upload(self, make_user, db_session):
        """Stripe creates the event, an upload lands, then the event is delivered."""
        from unittest.mock import MagicMock

        import billing.webhook_handler as wh
        from shared.tool_run_recorder import maybe_record_tool_run

        user = make_user(email="m790-u3@example.com")
        sub = _subscribe(db_session, user)
        sub.stripe_customer_id = "cus_m790_u3"
        db_session.flush()
        _pin_updated_at(db_session, user.id, _naive_now() - timedelta(hours=1))

        event_created = int((datetime.now(UTC) - timedelta(minutes=5)).timestamp())
        maybe_record_tool_run(db_session, None, user.id, "ap_testing", True, consumes_upload=True)
        assert _counter(db_session, user.id) == 1

        handler = MagicMock()
        with patch.dict(wh.WEBHOOK_HANDLERS, {"customer.subscription.updated": handler}):
            wh.process_webhook_event(
                db_session,
                "customer.subscription.updated",
                {"customer": "cus_m790_u3", "metadata": {"paciolus_user_id": str(user.id)}},
                event_created=event_created,
            )
        handler.assert_called_once()


# ---------------------------------------------------------------------------
# PR #227 review, P1 #2: the allowance is monthly on every billing interval
# ---------------------------------------------------------------------------


class TestUploadWindow:
    def _sub(self, start=None, end=None, created=None):
        from types import SimpleNamespace

        return SimpleNamespace(current_period_start=start, current_period_end=end, created_at=created)

    def test_monthly_period_is_its_own_window(self):
        from shared.entitlement_checks import upload_window_start

        start = datetime(2026, 3, 31, 9, 0)
        sub = self._sub(start, datetime(2026, 4, 30, 9, 0))
        # Even past the 30th of April (a clamped anniversary would be Apr 30),
        # a monthly plan's window does not move until the period does.
        assert upload_window_start(sub, datetime(2026, 4, 30, 8, 0)) == start
        assert upload_window_start(sub, datetime(2026, 4, 3)) == start

    def test_annual_plan_rolls_monthly_on_the_anchor_day(self):
        from shared.entitlement_checks import upload_window_start

        sub = self._sub(datetime(2026, 1, 15, 12, 0), datetime(2027, 1, 15, 12, 0))
        assert upload_window_start(sub, datetime(2026, 1, 20)) == datetime(2026, 1, 15, 12, 0)
        assert upload_window_start(sub, datetime(2026, 2, 15, 11, 59)) == datetime(2026, 1, 15, 12, 0)
        assert upload_window_start(sub, datetime(2026, 2, 15, 12, 0)) == datetime(2026, 2, 15, 12, 0)
        assert upload_window_start(sub, datetime(2026, 12, 31)) == datetime(2026, 12, 15, 12, 0)

    def test_jan_31_anchor_clamps_to_month_end(self):
        from shared.entitlement_checks import upload_window_start

        sub = self._sub(datetime(2026, 1, 31), datetime(2027, 1, 31))
        assert upload_window_start(sub, datetime(2026, 2, 28, 1)) == datetime(2026, 2, 28)
        assert upload_window_start(sub, datetime(2026, 3, 30)) == datetime(2026, 2, 28)
        assert upload_window_start(sub, datetime(2026, 3, 31)) == datetime(2026, 3, 31)
        assert upload_window_start(sub, datetime(2026, 4, 30, 5)) == datetime(2026, 4, 30)
        leap = self._sub(datetime(2028, 1, 31), datetime(2029, 1, 31))
        assert upload_window_start(leap, datetime(2028, 2, 29, 1)) == datetime(2028, 2, 29)

    def test_no_period_on_record_anchors_on_created_at(self):
        from shared.entitlement_checks import upload_window_start

        sub = self._sub(created=datetime(2026, 5, 10, 8, 0))
        assert upload_window_start(sub, datetime(2026, 8, 9)) == datetime(2026, 7, 10, 8, 0)

    def test_aware_and_naive_inputs_agree(self):
        from shared.entitlement_checks import upload_window_start

        sub = self._sub(datetime(2026, 1, 15, 12, 0, tzinfo=UTC), datetime(2027, 1, 15, 12, 0, tzinfo=UTC))
        assert upload_window_start(sub, datetime(2026, 3, 1, tzinfo=UTC)) == datetime(2026, 2, 15, 12, 0)


def _annual(db_session, user, *, used: int, window_months_ago: int, tier: str = "solo"):
    """An annual subscription that started 70 days ago; counter window N months back."""
    from shared.entitlement_checks import upload_window_start
    from subscription_model import BillingInterval, Subscription, SubscriptionStatus

    start = _naive_now() - timedelta(days=70)
    sub = Subscription(
        user_id=user.id,
        tier=tier,
        status=SubscriptionStatus.ACTIVE,
        billing_interval=BillingInterval.ANNUAL,
        current_period_start=start,
        current_period_end=start + timedelta(days=365),
        uploads_used_current_period=used,
    )
    db_session.add(sub)
    db_session.flush()
    current = upload_window_start(sub)
    sub.uploads_window_start = current if window_months_ago == 0 else start
    db_session.flush()
    return sub, current


class TestAnnualSubscribers:
    def test_capped_in_an_earlier_month_is_allowed_again(self, make_user, db_session):
        from models import UserTier
        from shared.entitlement_checks import check_upload_limit, uploads_used_this_period

        user = make_user(email="m790-a1@example.com", tier=UserTier.SOLO)
        _annual(db_session, user, used=100, window_months_ago=2)
        assert uploads_used_this_period(db_session, user.id) == 0
        check_upload_limit(user=user, db=db_session)  # does not raise

    def test_capped_in_the_current_month_is_refused(self, make_user, db_session):
        from fastapi import HTTPException

        from models import UserTier
        from shared.entitlement_checks import check_upload_limit

        user = make_user(email="m790-a2@example.com", tier=UserTier.SOLO)
        _annual(db_session, user, used=100, window_months_ago=0)
        with pytest.raises(HTTPException) as exc:
            check_upload_limit(user=user, db=db_session)
        assert exc.value.status_code == 403

    def test_the_first_run_of_a_new_month_restarts_the_count_at_one(self, make_user, db_session):
        from shared.entitlement_checks import increment_upload_count

        user = make_user(email="m790-a3@example.com")
        sub, current = _annual(db_session, user, used=100, window_months_ago=2)
        increment_upload_count(db_session, user.id)
        db_session.refresh(sub)
        assert sub.uploads_used_current_period == 1
        assert sub.uploads_window_start == current
        increment_upload_count(db_session, user.id)
        db_session.refresh(sub)
        assert sub.uploads_used_current_period == 2

    def test_a_null_window_reads_as_an_untouched_allowance(self, make_user, db_session):
        from models import UserTier
        from shared.entitlement_checks import uploads_used_this_period

        user = make_user(email="m790-a4@example.com", tier=UserTier.SOLO)
        sub = _subscribe(db_session, user, used=100, tier="solo")
        sub.uploads_window_start = None
        db_session.flush()
        assert uploads_used_this_period(db_session, user.id) == 0

    def test_monthly_plan_keeps_its_count_for_the_whole_period(self, make_user, db_session):
        """Monthly behaviour is unchanged: the count holds until the period rolls."""
        from fastapi import HTTPException

        from models import UserTier
        from shared.entitlement_checks import check_upload_limit, increment_upload_count

        user = make_user(email="m790-a5@example.com", tier=UserTier.SOLO)
        sub = _subscribe(db_session, user, used=99, tier="solo")
        sub.current_period_start = _naive_now() - timedelta(days=29, hours=23)
        sub.current_period_end = sub.current_period_start + timedelta(days=31)
        sub.uploads_window_start = sub.current_period_start
        db_session.flush()
        increment_upload_count(db_session, user.id)
        assert _counter(db_session, user.id) == 100
        with pytest.raises(HTTPException):
            check_upload_limit(user=user, db=db_session)

    def test_renewal_opens_the_new_window(self, make_user, db_session):
        from billing.subscription_manager import sync_subscription_from_stripe

        user = make_user(email="m790-a6@example.com")
        first = datetime.now(UTC) - timedelta(days=400)
        renewed = datetime.now(UTC) - timedelta(days=35)

        def _event(start):
            return {
                "id": "sub_m790_a6",
                "status": "active",
                "current_period_start": int(start.timestamp()),
                "current_period_end": int((start + timedelta(days=365)).timestamp()),
                "items": {"data": [{"plan": {"interval": "year"}, "quantity": 1}]},
            }

        sync_subscription_from_stripe(db_session, user.id, _event(first), "cus_m790_a6", "solo")
        sub = _subscribe_lookup(db_session, user.id)
        sub.uploads_used_current_period = 80
        db_session.flush()
        sync_subscription_from_stripe(db_session, user.id, _event(renewed), "cus_m790_a6", "solo")
        assert sub.uploads_used_current_period == 0
        # 35 days into an annual period, the current window is the first monthly anniversary.
        start = renewed.replace(tzinfo=None, microsecond=0)
        assert sub.uploads_window_start > start


def test_concurrent_increments_do_not_lose_counts(tmp_path):
    """Eight threads, five runs each, starting from a NULL window: exactly 40."""
    import threading

    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker

    from shared.entitlement_checks import increment_upload_count
    from subscription_model import Subscription

    engine = create_engine(
        f"sqlite:///{(tmp_path / 'race.db').as_posix()}",
        connect_args={"check_same_thread": False, "timeout": 30},
        isolation_level="AUTOCOMMIT",
    )
    # Only the subscriptions table: SQLite does not enforce the users FK here.
    Subscription.__table__.create(engine)
    with engine.connect() as conn:
        conn.execute(
            text(
                "INSERT INTO subscriptions (user_id, tier, status, seat_count, additional_seats, "
                "uploads_used_current_period, seat_version, cancel_at_period_end, created_at, updated_at) "
                "VALUES (1, 'solo', 'ACTIVE', 1, 0, 0, 0, 0, :ts, :ts)"
            ),
            {"ts": _naive_now() - timedelta(days=3)},
        )

    Session = sessionmaker(bind=engine)
    errors: list[BaseException] = []

    def _worker():
        try:
            for _ in range(5):
                s = Session()
                try:
                    increment_upload_count(s, 1)
                finally:
                    s.close()
        except BaseException as exc:  # pragma: no cover - surfaced below
            errors.append(exc)

    threads = [threading.Thread(target=_worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    with engine.connect() as conn:
        total = conn.execute(text("SELECT uploads_used_current_period FROM subscriptions")).scalar_one()
    engine.dispose()
    assert not errors, errors
    assert total == 40


def test_window_migration_adds_the_column(tmp_path):
    from sqlalchemy import create_engine, inspect

    url = f"sqlite:///{(tmp_path / 'm790w.db').as_posix()}"
    _alembic_upgrade(url, "f3b81d6e2a47")
    engine = create_engine(url)
    cols = {c["name"]: c for c in inspect(engine).get_columns("subscriptions")}
    engine.dispose()
    assert "uploads_window_start" in cols
    assert cols["uploads_window_start"]["nullable"] is True


# ---------------------------------------------------------------------------
# the symmetry guard
# ---------------------------------------------------------------------------

_GATES = {"check_upload_limit", "check_diagnostic_limit"}

# Gated functions deliberately allowed to meter nothing. Each entry must say why,
# and test_exemptions_are_still_true fails the moment the reason stops holding.
#
# bulk upload: _process_bulk_files runs no engine — it marks each file
# "complete" with only its name and size. There is no analysis run to charge
# for, so it consumes nothing (lead/CEO decision, Sprint 790). Its quota check
# is kept: harmless (Enterprise is unlimited) and it refuses a capped user
# before work starts once real analysis is wired in.
_EXEMPT = {"routes/bulk_upload.py::start_bulk_upload"}
_SCAN_DIRS = ("routes", "shared", "services")


def _name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _is_true(node: ast.AST | None) -> bool:
    return isinstance(node, ast.Constant) and node.value is True


def _recorder_success(call: ast.Call) -> bool:
    """A maybe_record_tool_run call whose ``success`` argument is literally True."""
    if len(call.args) >= 5:
        return _is_true(call.args[4])
    return any(kw.arg == "success" and _is_true(kw.value) for kw in call.keywords)


def _consumes(call: ast.Call) -> bool:
    return any(kw.arg == "consumes_upload" and _is_true(kw.value) for kw in call.keywords)


def _functions(tree: ast.Module) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    return [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]


def _is_gated(fn) -> bool:
    for node in ast.walk(fn):
        if isinstance(node, ast.Call):
            if _name(node.func) in _GATES:
                return True
            # Depends(check_upload_limit) as a parameter default
            if _name(node.func) == "Depends" and node.args and _name(node.args[0]) in _GATES:
                return True
    return False


def _meters_directly(fn) -> bool:
    for node in ast.walk(fn):
        if not isinstance(node, ast.Call):
            continue
        name = _name(node.func)
        if name == "increment_upload_count":
            return True
        if name == "maybe_record_tool_run" and _recorder_success(node) and _consumes(node):
            return True
    return False


def _module_functions():
    for sub in _SCAN_DIRS:
        for path in sorted((_BACKEND / sub).rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            yield path.relative_to(_BACKEND).as_posix(), tree


def _meters(fn, by_name: dict, seen: set | None = None) -> bool:
    """Does ``fn`` reach an increment — itself, or via a same-module function it calls?"""
    seen = seen if seen is not None else set()
    if fn.name in seen:
        return False
    seen.add(fn.name)
    if _meters_directly(fn):
        return True
    called = {_name(n.func) for n in ast.walk(fn) if isinstance(n, ast.Call)}
    return any(_meters(by_name[c], by_name, seen) for c in called if c in by_name and by_name[c] is not fn)


class TestCheckAndIncrementAreSymmetric:
    def test_every_gated_endpoint_reaches_an_increment_on_success(self):
        gated: list[str] = []
        unmetered: list[str] = []
        for rel, tree in _module_functions():
            fns = _functions(tree)
            by_name = {f.name: f for f in fns}
            for fn in fns:
                if rel == "shared/entitlement_checks.py" or not _is_gated(fn):
                    continue
                gated.append(f"{rel}::{fn.name}")
                if f"{rel}::{fn.name}" in _EXEMPT:
                    continue
                if not _meters(fn, by_name):
                    unmetered.append(f"{rel}::{fn.name}")

        # The scan must actually be finding the gate, or this test proves nothing.
        assert len(gated) >= 14, gated
        assert "routes/audit_pipeline.py::audit_trial_balance" in gated  # the Depends() form
        assert "shared/testing_route.py::run_single_file_testing" in gated  # the six testing tools
        assert not unmetered, (
            "These functions call check_upload_limit but never advance the counter on success, "
            "so the quota is inert for paid tiers there. Pass consumes_upload=True on the success "
            f"maybe_record_tool_run call: {unmetered}"
        )

    def test_exemptions_are_still_true(self):
        """An exempt function must still be gated and must still meter nothing.

        If bulk upload starts running analysis (and metering it), or stops
        checking the quota, the exemption is stale and must be removed.
        """
        found: dict[str, tuple[bool, bool]] = {}
        for rel, tree in _module_functions():
            fns = _functions(tree)
            by_name = {f.name: f for f in fns}
            for fn in fns:
                key = f"{rel}::{fn.name}"
                if key in _EXEMPT:
                    found[key] = (_is_gated(fn), _meters(fn, by_name))
        assert set(found) == _EXEMPT, f"exempt functions not found: {_EXEMPT - set(found)}"
        for key, (gated, meters) in found.items():
            assert gated, f"{key} no longer checks the quota; drop it from _EXEMPT"
            assert not meters, f"{key} now meters; drop it from _EXEMPT so the guard covers it"

    def test_bulk_upload_consumes_nothing(self):
        source = (_BACKEND / "routes" / "bulk_upload.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        names = {_name(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)}
        assert "increment_upload_count" not in names
        assert "maybe_record_tool_run" not in names

    def test_every_success_record_in_a_gated_function_consumes(self):
        """A gated function with two success records must not leave one unmetered."""
        offenders: list[str] = []
        for rel, tree in _module_functions():
            for fn in _functions(tree):
                if not _is_gated(fn):
                    continue
                for node in ast.walk(fn):
                    if (
                        isinstance(node, ast.Call)
                        and _name(node.func) == "maybe_record_tool_run"
                        and _recorder_success(node)
                        and not _consumes(node)
                    ):
                        offenders.append(f"{rel}::{fn.name}:{node.lineno}")
        assert not offenders, offenders

    def test_only_gated_functions_consume(self):
        """The converse: metering a run that was never checked would spend allowance unchecked."""
        offenders: list[str] = []
        for rel, tree in _module_functions():
            for fn in _functions(tree):
                if _is_gated(fn):
                    continue
                for node in ast.walk(fn):
                    if isinstance(node, ast.Call) and _name(node.func) == "maybe_record_tool_run" and _consumes(node):
                        offenders.append(f"{rel}::{fn.name}:{node.lineno}")
        assert not offenders, offenders

    def test_failure_records_never_consume(self):
        offenders: list[str] = []
        for rel, tree in _module_functions():
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Call)
                    and _name(node.func) == "maybe_record_tool_run"
                    and _consumes(node)
                    and not _recorder_success(node)
                ):
                    offenders.append(f"{rel}:{node.lineno}")
        assert not offenders, offenders
