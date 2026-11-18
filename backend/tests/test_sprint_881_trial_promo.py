"""Sprint 881 — one trial per account, each promo code once per account (AZ-16).

``orchestrate_checkout`` granted ``TRIAL_PERIOD_DAYS`` whenever the account had no
subscription or a cancelled one, so cancelling and buying again restarted the trial.
Promo validation checked only the code and the billing interval, never earlier use.

Trial use (``users.trial_used_at``) and promo redemptions (``promo_redemptions``) are
now stored independently of the subscription's current status and checked before a
Checkout Session is created. Both are recorded when Stripe confirms the subscription
(sync from the webhook), not when checkout opens (CEO 2026-11-18): an abandoned
checkout uses neither.
"""

from unittest.mock import patch

import pytest

from billing.checkout_orchestrator import CheckoutValidationError, orchestrate_checkout
from models import User
from subscription_model import PromoRedemption, Subscription, SubscriptionStatus
from tests.helpers.fake_stripe import FakeStripe

SOLO_MONTHLY = "price_1QpSoloMonthly000000000a"
COUPON_MONTHLY = "coupon_fake_monthly20"


@pytest.fixture
def fake_stripe():
    fake = FakeStripe(price_intervals={SOLO_MONTHLY: "month"})
    with (
        patch("billing.price_config._load_stripe_price_ids", return_value={"solo": {"monthly": SOLO_MONTHLY}}),
        patch("billing.price_config._load_pro_seat_price_ids", return_value={"monthly": "", "annual": ""}),
        patch("billing.price_config._load_ent_seat_price_ids", return_value={"monthly": "", "annual": ""}),
        patch("billing.price_config._load_coupon_ids", return_value={"monthly": COUPON_MONTHLY, "annual": ""}),
        patch("billing.stripe_client.is_stripe_enabled", return_value=True),
        patch("billing.stripe_client.get_stripe", return_value=fake),
        patch("billing.checkout.get_stripe", return_value=fake),
        patch("billing.subscription_manager.get_stripe", return_value=fake),
        patch("billing.webhook_handler._resolve_tier_from_price", return_value="solo"),
        patch("config.FRONTEND_URL", "https://app.example.test"),
    ):
        yield fake


def _checkout(db_session, user, promo_code=None):
    orchestrate_checkout(
        tier="solo",
        interval="monthly",
        seat_count=0,
        promo_code=promo_code,
        dpa_accepted=False,
        user_id=user.id,
        user_email=user.email,
        db=db_session,
    )


def _last_session(fake):
    return fake.sessions[fake.created_sessions[-1]]


def _pay_last_session(db_session, fake):
    """The customer pays and Stripe sends checkout.session.completed."""
    from billing.webhook_handler import handle_checkout_completed

    session = fake.complete_session(fake.created_sessions[-1], SOLO_MONTHLY)
    handle_checkout_completed(db_session, session)
    return session


def _cancel(db_session, fake, user):
    """Stripe ends the subscription and the deletion webhook arrives."""
    from billing.webhook_handler import handle_subscription_deleted

    sub = db_session.query(Subscription).filter_by(user_id=user.id).one()
    fake.subscriptions[sub.stripe_subscription_id]["status"] = "canceled"
    handle_subscription_deleted(
        db_session, {"id": sub.stripe_subscription_id, "metadata": {"paciolus_user_id": str(user.id)}}
    )
    assert sub.status == SubscriptionStatus.CANCELED


class TestOneTrialPerAccount:
    def test_first_checkout_offers_the_trial(self, db_session, make_user, fake_stripe):
        user = make_user(email="az16_first@example.com")
        _checkout(db_session, user)
        assert _last_session(fake_stripe)["subscription_data"].get("trial_period_days") == 7

    def test_cancelled_account_that_had_a_trial_gets_none(self, db_session, make_user, fake_stripe):
        user = make_user(email="az16_again@example.com")
        _checkout(db_session, user)
        _pay_last_session(db_session, fake_stripe)  # subscription starts trialing
        assert db_session.get(User, user.id).trial_used_at is not None

        _cancel(db_session, fake_stripe, user)
        _checkout(db_session, user)
        assert "trial_period_days" not in _last_session(fake_stripe)["subscription_data"]

    def test_trial_use_survives_without_any_subscription_row(self, db_session, make_user, fake_stripe):
        """Trial use is stored on the account, not derived from the subscription's status."""
        from datetime import UTC, datetime

        user = make_user(email="az16_norow@example.com")
        user.trial_used_at = datetime.now(UTC)
        db_session.flush()
        _checkout(db_session, user)
        assert "trial_period_days" not in _last_session(fake_stripe)["subscription_data"]

    def test_abandoned_checkout_does_not_use_the_trial(self, db_session, make_user, fake_stripe):
        user = make_user(email="az16_abandon@example.com")
        _checkout(db_session, user)  # never paid
        _checkout(db_session, user)  # expires the first, opens a second
        assert db_session.get(User, user.id).trial_used_at is None
        assert _last_session(fake_stripe)["subscription_data"].get("trial_period_days") == 7


class TestPromoOncePerAccount:
    def test_promo_code_used_on_the_account_is_not_honored_again(self, db_session, make_user, fake_stripe):
        user = make_user(email="az16_promo@example.com")
        _checkout(db_session, user, promo_code="MONTHLY20")
        assert _last_session(fake_stripe)["discounts"] == [{"coupon": COUPON_MONTHLY}]
        _pay_last_session(db_session, fake_stripe)
        assert db_session.query(PromoRedemption).filter_by(user_id=user.id, promo_code="MONTHLY20").count() == 1

        _cancel(db_session, fake_stripe, user)
        sessions_before = len(fake_stripe.created_sessions)
        with pytest.raises(CheckoutValidationError, match="already been used"):
            _checkout(db_session, user, promo_code="monthly20")
        assert len(fake_stripe.created_sessions) == sessions_before

    def test_abandoned_promo_checkout_does_not_use_the_code(self, db_session, make_user, fake_stripe):
        user = make_user(email="az16_promo_abandon@example.com")
        _checkout(db_session, user, promo_code="MONTHLY20")
        _checkout(db_session, user, promo_code="MONTHLY20")
        assert _last_session(fake_stripe)["discounts"] == [{"coupon": COUPON_MONTHLY}]
        assert db_session.query(PromoRedemption).filter_by(user_id=user.id).count() == 0

    def test_another_account_may_use_the_code(self, db_session, make_user, fake_stripe):
        first = make_user(email="az16_promo_a@example.com")
        _checkout(db_session, first, promo_code="MONTHLY20")
        _pay_last_session(db_session, fake_stripe)

        second = make_user(email="az16_promo_b@example.com")
        _checkout(db_session, second, promo_code="MONTHLY20")
        assert _last_session(fake_stripe)["discounts"] == [{"coupon": COUPON_MONTHLY}]

    def test_redemption_recorded_once_across_webhook_replays(self, db_session, make_user, fake_stripe):
        from billing.subscription_manager import sync_subscription_from_stripe

        user = make_user(email="az16_promo_replay@example.com")
        _checkout(db_session, user, promo_code="MONTHLY20")
        session = _pay_last_session(db_session, fake_stripe)
        stripe_sub = fake_stripe.subscriptions[session["subscription"]]
        sync_subscription_from_stripe(db_session, user.id, stripe_sub, stripe_sub["customer"], "solo")
        assert db_session.query(PromoRedemption).filter_by(user_id=user.id).count() == 1
