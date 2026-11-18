"""Sprint 881 — checkout can no longer create a second subscription (AZ-09).

``orchestrate_checkout`` loaded the user's subscription only to reuse the customer and
decide the trial, then opened another ``mode: subscription`` session. An active
subscriber who checked out again could be billed for two subscriptions while the app
tracked one: sync overwrote the single local row's ``stripe_subscription_id``.

Now:
* a new-subscription checkout is refused (409) while a non-terminal subscription
  exists locally or in Stripe;
* plan and interval changes update the existing Stripe subscription
  (``POST /billing/change-plan``, effective now, prorated — CEO 2026-11-18);
* purchase admission is serialized on the user row and every checkout has a durable
  ``checkout_attempts`` row; opening a new checkout expires any earlier session still
  payable, so at most one can complete;
* sync never overwrites a live stored subscription ID with a different one — it
  records the other ID on the row and logs it for an operator.

The concurrent-purchase test on PostgreSQL is in ``test_sprint_881_checkout_race_pg.py``.
"""

import logging
from unittest.mock import patch

import pytest

from billing.checkout_orchestrator import CheckoutConflictError, orchestrate_checkout
from subscription_model import (
    BillingInterval,
    CheckoutAttempt,
    CheckoutAttemptStatus,
    Subscription,
    SubscriptionStatus,
)
from tests.helpers.fake_stripe import FakeStripe

SOLO_MONTHLY = "price_1QpSoloMonthly000000000a"
SOLO_ANNUAL = "price_1QpSoloAnnual0000000000a"


@pytest.fixture
def fake_stripe():
    fake = FakeStripe(price_intervals={SOLO_MONTHLY: "month", SOLO_ANNUAL: "year"})
    with (
        patch(
            "billing.price_config._load_stripe_price_ids",
            return_value={"solo": {"monthly": SOLO_MONTHLY, "annual": SOLO_ANNUAL}},
        ),
        patch("billing.price_config._load_pro_seat_price_ids", return_value={"monthly": "", "annual": ""}),
        patch("billing.price_config._load_ent_seat_price_ids", return_value={"monthly": "", "annual": ""}),
        patch("billing.stripe_client.is_stripe_enabled", return_value=True),
        patch("billing.stripe_client.get_stripe", return_value=fake),
        patch("billing.checkout.get_stripe", return_value=fake),
        patch("billing.subscription_manager.get_stripe", return_value=fake),
        patch("config.FRONTEND_URL", "https://app.example.test"),
    ):
        yield fake


def _checkout(db_session, user, interval="monthly"):
    return orchestrate_checkout(
        tier="solo",
        interval=interval,
        seat_count=0,
        promo_code=None,
        dpa_accepted=False,
        user_id=user.id,
        user_email=user.email,
        db=db_session,
    )


def _local_sub(db_session, user, status, stripe_sub_id="sub_existing0001", customer="cus_existing0001"):
    sub = Subscription(
        user_id=user.id,
        tier="solo",
        status=status,
        billing_interval=BillingInterval.MONTHLY,
        stripe_customer_id=customer,
        stripe_subscription_id=stripe_sub_id,
        seat_count=1,
        additional_seats=0,
    )
    db_session.add(sub)
    db_session.flush()
    return sub


class TestRefuseSecondSubscription:
    @pytest.mark.parametrize(
        "status",
        [
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.TRIALING,
            SubscriptionStatus.PAST_DUE,
            SubscriptionStatus.UNPAID,
            SubscriptionStatus.PAUSED,
            SubscriptionStatus.INCOMPLETE,
        ],
    )
    def test_non_terminal_subscription_refused(self, db_session, make_user, fake_stripe, status):
        user = make_user(email=f"az09_{status.value}@example.com")
        _local_sub(db_session, user, status)
        with pytest.raises(CheckoutConflictError):
            _checkout(db_session, user)
        assert fake_stripe.created_sessions == []

    @pytest.mark.parametrize("status", [SubscriptionStatus.CANCELED, SubscriptionStatus.INCOMPLETE_EXPIRED])
    def test_terminal_subscription_may_buy_again(self, db_session, make_user, fake_stripe, status):
        user = make_user(email=f"az09_term_{status.value}@example.com")
        _local_sub(db_session, user, status, customer="cus_term")
        fake_stripe.customers["cus_term"] = {"id": "cus_term"}
        url = _checkout(db_session, user)
        assert url.startswith("https://checkout.stripe.com/")
        assert len(fake_stripe.created_sessions) == 1

    def test_live_stripe_subscription_refused_before_webhook_arrives(self, db_session, make_user, fake_stripe):
        """The local row is still canceled, but Stripe already has a new live subscription."""
        user = make_user(email="az09_lag@example.com")
        _local_sub(db_session, user, SubscriptionStatus.CANCELED, customer="cus_lag")
        fake_stripe.add_subscription("cus_lag", SOLO_MONTHLY, status="active")
        with pytest.raises(CheckoutConflictError):
            _checkout(db_session, user)
        assert fake_stripe.created_sessions == []

    @pytest.mark.usefixtures("bypass_csrf")
    @pytest.mark.anyio
    async def test_route_answers_409(self, db_session, make_user, fake_stripe):
        import httpx

        from auth import require_verified_user
        from database import get_db
        from main import app

        user = make_user(email="az09_route@example.com")
        _local_sub(db_session, user, SubscriptionStatus.ACTIVE)
        app.dependency_overrides[require_verified_user] = lambda: user
        app.dependency_overrides[get_db] = lambda: db_session
        try:
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post(
                    "/billing/create-checkout-session", json={"tier": "solo", "interval": "annual"}
                )
        finally:
            app.dependency_overrides.clear()
        assert resp.status_code == 409
        assert fake_stripe.created_sessions == []


class TestOneOpenCheckoutPerAccount:
    def test_new_checkout_expires_the_earlier_session(self, db_session, make_user, fake_stripe):
        user = make_user(email="az09_twice@example.com")
        _checkout(db_session, user)
        _checkout(db_session, user, interval="annual")

        first, second = fake_stripe.created_sessions
        assert fake_stripe.expired_sessions == [first]
        attempts = db_session.query(CheckoutAttempt).filter_by(user_id=user.id).order_by(CheckoutAttempt.id).all()
        assert [a.status for a in attempts] == [CheckoutAttemptStatus.EXPIRED.value, CheckoutAttemptStatus.OPEN.value]
        assert attempts[1].stripe_checkout_session_id == second
        # One Stripe customer for the account, reused by the second attempt
        assert len(fake_stripe.customers) == 1
        assert attempts[0].stripe_customer_id == attempts[1].stripe_customer_id

    def test_expired_session_cannot_be_paid(self, db_session, make_user, fake_stripe):
        from tests.helpers.fake_stripe import FakeStripeError

        user = make_user(email="az09_pay_old@example.com")
        _checkout(db_session, user)
        _checkout(db_session, user)
        first = fake_stripe.created_sessions[0]
        with pytest.raises(FakeStripeError):
            fake_stripe.complete_session(first, SOLO_MONTHLY)

    def test_session_already_paid_refuses_new_checkout(self, db_session, make_user, fake_stripe):
        """The first session was paid but its webhook has not arrived: the second checkout is refused."""
        user = make_user(email="az09_paid@example.com")
        _checkout(db_session, user)
        fake_stripe.complete_session(fake_stripe.created_sessions[0], SOLO_MONTHLY)
        with pytest.raises(CheckoutConflictError):
            _checkout(db_session, user)
        assert len(fake_stripe.created_sessions) == 1

    def test_attempt_identity_is_sent_to_stripe(self, db_session, make_user, fake_stripe):
        user = make_user(email="az09_identity@example.com")
        _checkout(db_session, user)
        attempt = db_session.query(CheckoutAttempt).filter_by(user_id=user.id).one()
        session = fake_stripe.sessions[attempt.stripe_checkout_session_id]
        assert session["client_reference_id"] == str(attempt.id)
        assert session["metadata"]["paciolus_checkout_attempt_id"] == str(attempt.id)
        assert session["expires_at"] is not None
        assert f"checkout-attempt-{attempt.id}" in fake_stripe.idempotent

    def test_completion_webhook_marks_the_attempt(self, db_session, make_user, fake_stripe):
        from billing.webhook_handler import handle_checkout_completed

        user = make_user(email="az09_complete@example.com")
        _checkout(db_session, user)
        attempt = db_session.query(CheckoutAttempt).filter_by(user_id=user.id).one()
        session = fake_stripe.complete_session(attempt.stripe_checkout_session_id, SOLO_MONTHLY)
        with patch("billing.webhook_handler._resolve_tier_from_price", return_value="solo"):
            handle_checkout_completed(db_session, session)
        db_session.refresh(attempt)
        assert attempt.status == CheckoutAttemptStatus.COMPLETED.value
        assert attempt.stripe_subscription_id == session["subscription"]


class TestCheckoutBeingOpened:
    """An attempt committed as ``opening`` whose Stripe session may not exist yet.

    The attempt row is committed (releasing the purchaser lock) before Stripe is
    called. A second checkout arriving in that window cannot see the first session
    to expire it, so it must not open its own: two payable sessions would follow.
    """

    def _opening(self, db_session, user, age):
        from datetime import UTC, datetime

        attempt = CheckoutAttempt(
            user_id=user.id,
            status=CheckoutAttemptStatus.OPENING.value,
            tier="solo",
            billing_interval="monthly",
            stripe_customer_id="cus_inflight",
            created_at=datetime.now(UTC) - age,
        )
        db_session.add(attempt)
        # Committed, as the real first request's row is: a refused checkout rolls back.
        db_session.commit()
        return attempt

    def test_recent_opening_attempt_refuses_a_second_checkout(self, db_session, make_user, fake_stripe):
        from datetime import timedelta

        user = make_user(email="az09_inflight@example.com")
        fake_stripe.customers["cus_inflight"] = {"id": "cus_inflight"}
        attempt = self._opening(db_session, user, timedelta(seconds=5))
        with pytest.raises(CheckoutConflictError):
            _checkout(db_session, user)
        assert fake_stripe.created_sessions == []
        db_session.refresh(attempt)
        assert attempt.status == CheckoutAttemptStatus.OPENING.value

    def test_stale_opening_attempt_is_closed_and_its_session_expired(self, db_session, make_user, fake_stripe):
        """A crash after Stripe created the session: the stale row's customer leads to it."""
        from datetime import timedelta

        user = make_user(email="az09_stale@example.com")
        fake_stripe.customers["cus_inflight"] = {"id": "cus_inflight"}
        orphan = fake_stripe.checkout.Session.create(customer="cus_inflight", metadata={})
        attempt = self._opening(db_session, user, timedelta(minutes=10))

        _checkout(db_session, user)

        assert fake_stripe.expired_sessions == [orphan.id]
        db_session.refresh(attempt)
        assert attempt.status == CheckoutAttemptStatus.FAILED.value
        assert len(fake_stripe.created_sessions) == 2


class TestSyncFlagsConflictingSubscription:
    def test_live_stored_id_is_not_overwritten(self, db_session, make_user, caplog):
        from billing.subscription_manager import sync_subscription_from_stripe

        user = make_user(email="az09_conflict@example.com")
        _local_sub(db_session, user, SubscriptionStatus.ACTIVE, stripe_sub_id="sub_original", customer="cus_c")
        duplicate = FakeStripe().add_subscription("cus_c", SOLO_ANNUAL, status="active", interval="year")

        with caplog.at_level(logging.CRITICAL):
            sub = sync_subscription_from_stripe(db_session, user.id, duplicate, "cus_c", "solo")

        assert sub.stripe_subscription_id == "sub_original"
        assert sub.billing_interval == BillingInterval.MONTHLY
        assert sub.conflicting_stripe_subscription_id == duplicate["id"]
        assert sub.conflict_detected_at is not None
        assert "sub_original" in caplog.text and duplicate["id"] in caplog.text

    def test_replacing_a_canceled_subscription_is_not_a_conflict(self, db_session, make_user):
        from billing.subscription_manager import sync_subscription_from_stripe

        user = make_user(email="az09_replace@example.com")
        _local_sub(db_session, user, SubscriptionStatus.CANCELED, stripe_sub_id="sub_old", customer="cus_r")
        new = FakeStripe().add_subscription("cus_r", SOLO_MONTHLY, status="active")
        sub = sync_subscription_from_stripe(db_session, user.id, new, "cus_r", "solo")
        assert sub.stripe_subscription_id == new["id"]
        assert sub.status == SubscriptionStatus.ACTIVE
        assert sub.conflicting_stripe_subscription_id is None

    def test_conflicting_checkout_does_not_create_org_or_events(self, db_session, make_user, fake_stripe):
        from billing.webhook_handler import handle_checkout_completed
        from subscription_model import BillingEvent

        user = make_user(email="az09_conflict_wh@example.com")
        _local_sub(db_session, user, SubscriptionStatus.ACTIVE, stripe_sub_id="sub_kept", customer="cus_wh")
        fake_stripe.customers["cus_wh"] = {"id": "cus_wh"}
        dup = fake_stripe.add_subscription("cus_wh", SOLO_MONTHLY)
        event = {
            "id": "cs_dup",
            "customer": "cus_wh",
            "subscription": dup["id"],
            "metadata": {"paciolus_user_id": str(user.id)},
        }
        with patch("billing.webhook_handler._resolve_tier_from_price", return_value="solo"):
            handle_checkout_completed(db_session, event)
        sub = db_session.query(Subscription).filter_by(user_id=user.id).one()
        assert sub.stripe_subscription_id == "sub_kept"
        assert sub.conflicting_stripe_subscription_id == dup["id"]
        assert db_session.query(BillingEvent).filter_by(user_id=user.id).count() == 0


class TestChangePlanUpdatesTheExistingSubscription:
    def _subscribed(self, db_session, make_user, fake_stripe, email):
        from billing.subscription_manager import sync_subscription_from_stripe

        user = make_user(email=email)
        fake_stripe.customers["cus_cp"] = {"id": "cus_cp"}
        stripe_sub = fake_stripe.add_subscription("cus_cp", SOLO_MONTHLY)
        sync_subscription_from_stripe(db_session, user.id, stripe_sub, "cus_cp", "solo")
        return user, stripe_sub

    def test_monthly_to_annual_swaps_the_price_now_with_proration(self, db_session, make_user, fake_stripe):
        from billing.checkout_orchestrator import change_plan

        user, stripe_sub = self._subscribed(db_session, make_user, fake_stripe, "az09_cp@example.com")
        sub = change_plan(db_session, user.id, tier="solo", interval="annual")

        ((sub_id, params),) = fake_stripe.modifications
        assert sub_id == stripe_sub["id"]
        assert params["proration_behavior"] == "create_prorations"
        assert params["items"] == [{"id": stripe_sub["items"]["data"][0]["id"], "price": SOLO_ANNUAL}]
        assert sub.stripe_subscription_id == stripe_sub["id"]
        assert sub.billing_interval == BillingInterval.ANNUAL
        assert fake_stripe.created_sessions == []

    def test_same_plan_refused(self, db_session, make_user, fake_stripe):
        from billing.checkout_orchestrator import CheckoutValidationError, change_plan

        user, _ = self._subscribed(db_session, make_user, fake_stripe, "az09_cp_same@example.com")
        with pytest.raises(CheckoutValidationError):
            change_plan(db_session, user.id, tier="solo", interval="monthly")
        assert fake_stripe.modifications == []

    def test_sales_only_tier_refused(self, db_session, make_user, fake_stripe):
        from billing.checkout_orchestrator import CheckoutTierNotSelfServeError, change_plan

        user, _ = self._subscribed(db_session, make_user, fake_stripe, "az09_cp_pro@example.com")
        with pytest.raises(CheckoutTierNotSelfServeError):
            change_plan(db_session, user.id, tier="professional", interval="monthly")
        assert fake_stripe.modifications == []

    def test_no_live_subscription_refused(self, db_session, make_user, fake_stripe):
        from billing.checkout_orchestrator import CheckoutValidationError, change_plan

        user = make_user(email="az09_cp_none@example.com")
        _local_sub(db_session, user, SubscriptionStatus.CANCELED)
        with pytest.raises(CheckoutValidationError):
            change_plan(db_session, user.id, tier="solo", interval="annual")
