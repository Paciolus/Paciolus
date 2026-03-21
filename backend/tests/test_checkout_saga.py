"""
Tests for checkout saga rollback behavior — Sprint 564.

Validates that the checkout orchestrator properly cleans up Stripe resources
when later steps fail (saga compensating actions).
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from billing.checkout_orchestrator import (
    CheckoutProviderError,
    CheckoutValidationError,
    _rollback_stripe_customer,
    orchestrate_checkout,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_db_session(*, has_subscription: bool = False) -> MagicMock:
    """Create a mock SQLAlchemy session."""
    session = MagicMock()
    session.rollback = MagicMock()
    session.commit = MagicMock()
    return session


# Common patches applied to every saga test
_COMMON_PATCHES = {
    "billing.stripe_client.is_stripe_enabled": True,
    "billing.price_config.get_stripe_price_id": "price_solo_monthly",
    "billing.price_config.TRIAL_ELIGIBLE_TIERS": {"solo"},
    "billing.price_config.TRIAL_PERIOD_DAYS": 7,
    "billing.price_config.get_max_self_serve_seats": 1,
    "billing.price_config.get_stripe_seat_price_id": None,
    "billing.price_config.get_stripe_coupon_id": None,
    "billing.price_config.validate_promo_for_interval": None,
    "billing.subscription_manager.get_subscription": None,
}


def _apply_patches(overrides: dict | None = None):
    """Build a list of mock.patch context managers for common billing deps."""
    patches = dict(_COMMON_PATCHES)
    if overrides:
        patches.update(overrides)

    managers = []
    for target, value in patches.items():
        if callable(value) and not isinstance(value, bool):
            managers.append(patch(target, side_effect=value))
        else:
            managers.append(patch(target, return_value=value))
    return managers


# ---------------------------------------------------------------------------
# _rollback_stripe_customer
# ---------------------------------------------------------------------------


class TestRollbackStripeCustomer:
    """Tests for the compensating action helper."""

    def test_successful_rollback(self):
        """Customer.delete is called and logged."""
        mock_stripe = MagicMock()
        with patch("billing.stripe_client.get_stripe", return_value=mock_stripe):
            _rollback_stripe_customer("cus_orphan123", user_id=42)

        mock_stripe.Customer.delete.assert_called_once_with("cus_orphan123")

    def test_rollback_failure_logs_critical(self, caplog):
        """If Customer.delete fails, a CRITICAL log is emitted."""
        mock_stripe = MagicMock()
        mock_stripe.Customer.delete.side_effect = Exception("Stripe API down")

        with patch("billing.stripe_client.get_stripe", return_value=mock_stripe):
            import logging

            with caplog.at_level(logging.CRITICAL):
                _rollback_stripe_customer("cus_orphan456", user_id=99)

        assert "MANUAL RECONCILIATION REQUIRED" in caplog.text
        assert "cus_orphan456" in caplog.text


# ---------------------------------------------------------------------------
# Saga: checkout session failure rolls back new customer
# ---------------------------------------------------------------------------


class TestSagaCheckoutSessionFailure:
    """If checkout session creation fails after creating a new customer,
    the new Stripe customer should be deleted."""

    def test_new_customer_deleted_on_session_failure(self):
        """New Stripe customer is deleted when checkout session creation fails."""
        mock_stripe = MagicMock()
        mock_stripe.Customer.create.return_value = MagicMock(id="cus_new_123")

        db = _mock_db_session()

        with (
            patch("billing.stripe_client.is_stripe_enabled", return_value=True),
            patch("billing.price_config.get_stripe_price_id", return_value="price_solo_monthly"),
            patch("billing.price_config.TRIAL_ELIGIBLE_TIERS", {"solo"}),
            patch("billing.price_config.TRIAL_PERIOD_DAYS", 7),
            patch("billing.price_config.get_max_self_serve_seats", return_value=1),
            patch("billing.subscription_manager.get_subscription", return_value=None),
            patch("billing.checkout.create_or_get_stripe_customer", return_value="cus_new_123"),
            patch(
                "billing.checkout.create_checkout_session",
                side_effect=Exception("Stripe session error"),
            ),
            patch("billing.checkout_orchestrator._rollback_stripe_customer") as mock_rollback,
        ):
            with pytest.raises(CheckoutProviderError):
                orchestrate_checkout(
                    tier="solo",
                    interval="monthly",
                    seat_count=0,
                    promo_code=None,
                    dpa_accepted=False,
                    user_id=1,
                    user_email="test@example.com",
                    db=db,
                )

            mock_rollback.assert_called_once_with("cus_new_123", 1)
            db.rollback.assert_called()

    def test_existing_customer_not_deleted_on_session_failure(self):
        """Existing Stripe customer is NOT deleted when session creation fails."""
        existing_sub = MagicMock()
        existing_sub.stripe_customer_id = "cus_existing_456"
        existing_sub.status.value = "active"

        db = _mock_db_session()

        with (
            patch("billing.stripe_client.is_stripe_enabled", return_value=True),
            patch("billing.price_config.get_stripe_price_id", return_value="price_solo_monthly"),
            patch("billing.price_config.TRIAL_ELIGIBLE_TIERS", {"solo"}),
            patch("billing.price_config.TRIAL_PERIOD_DAYS", 7),
            patch("billing.price_config.get_max_self_serve_seats", return_value=1),
            patch("billing.subscription_manager.get_subscription", return_value=existing_sub),
            patch(
                "billing.checkout.create_or_get_stripe_customer",
                return_value="cus_existing_456",
            ),
            patch(
                "billing.checkout.create_checkout_session",
                side_effect=Exception("Stripe session error"),
            ),
            patch("billing.checkout_orchestrator._rollback_stripe_customer") as mock_rollback,
        ):
            with pytest.raises(CheckoutProviderError):
                orchestrate_checkout(
                    tier="solo",
                    interval="monthly",
                    seat_count=0,
                    promo_code=None,
                    dpa_accepted=False,
                    user_id=1,
                    user_email="test@example.com",
                    db=db,
                )

            mock_rollback.assert_not_called()


# ---------------------------------------------------------------------------
# Saga: DB commit failure logs for manual reconciliation
# ---------------------------------------------------------------------------


class TestSagaDBCommitFailure:
    """If DB commit fails after Stripe resources were created,
    we log for manual reconciliation (don't auto-delete)."""

    def test_db_commit_failure_logs_critical(self, caplog):
        """DB commit failure emits CRITICAL log with Stripe resource IDs."""
        db = _mock_db_session()
        db.commit.side_effect = Exception("DB connection lost")

        with (
            patch("billing.stripe_client.is_stripe_enabled", return_value=True),
            patch("billing.price_config.get_stripe_price_id", return_value="price_solo_monthly"),
            patch("billing.price_config.TRIAL_ELIGIBLE_TIERS", {"solo"}),
            patch("billing.price_config.TRIAL_PERIOD_DAYS", 7),
            patch("billing.price_config.get_max_self_serve_seats", return_value=1),
            patch("billing.subscription_manager.get_subscription", return_value=None),
            patch("billing.checkout.create_or_get_stripe_customer", return_value="cus_abc"),
            patch(
                "billing.checkout.create_checkout_session",
                return_value="https://checkout.stripe.com/session123",
            ),
        ):
            import logging

            with caplog.at_level(logging.CRITICAL):
                with pytest.raises(CheckoutProviderError):
                    orchestrate_checkout(
                        tier="solo",
                        interval="monthly",
                        seat_count=0,
                        promo_code=None,
                        dpa_accepted=False,
                        user_id=7,
                        user_email="dbfail@example.com",
                        db=db,
                    )

        assert "MANUAL RECONCILIATION REQUIRED" in caplog.text
        assert "cus_abc" in caplog.text
        assert "user_id=7" in caplog.text
        db.rollback.assert_called()

    def test_db_commit_failure_does_not_delete_stripe_resources(self):
        """On DB commit failure, Stripe customer is NOT auto-deleted."""
        db = _mock_db_session()
        db.commit.side_effect = Exception("DB connection lost")

        with (
            patch("billing.stripe_client.is_stripe_enabled", return_value=True),
            patch("billing.price_config.get_stripe_price_id", return_value="price_solo_monthly"),
            patch("billing.price_config.TRIAL_ELIGIBLE_TIERS", {"solo"}),
            patch("billing.price_config.TRIAL_PERIOD_DAYS", 7),
            patch("billing.price_config.get_max_self_serve_seats", return_value=1),
            patch("billing.subscription_manager.get_subscription", return_value=None),
            patch("billing.checkout.create_or_get_stripe_customer", return_value="cus_xyz"),
            patch(
                "billing.checkout.create_checkout_session",
                return_value="https://checkout.stripe.com/session456",
            ),
            patch("billing.checkout_orchestrator._rollback_stripe_customer") as mock_rollback,
        ):
            with pytest.raises(CheckoutProviderError):
                orchestrate_checkout(
                    tier="solo",
                    interval="monthly",
                    seat_count=0,
                    promo_code=None,
                    dpa_accepted=False,
                    user_id=7,
                    user_email="dbfail@example.com",
                    db=db,
                )

            # Must NOT auto-delete — user might complete the checkout session
            mock_rollback.assert_not_called()


# ---------------------------------------------------------------------------
# Saga: validation failure after customer creation rolls back
# ---------------------------------------------------------------------------


class TestSagaValidationFailureRollback:
    """Validation failures (promo, seats) after customer creation
    should clean up the new Stripe customer."""

    def test_promo_validation_failure_deletes_new_customer(self):
        """Invalid promo code after new customer creation triggers rollback."""
        db = _mock_db_session()

        with (
            patch("billing.stripe_client.is_stripe_enabled", return_value=True),
            patch("billing.price_config.get_stripe_price_id", return_value="price_pro_monthly"),
            patch("billing.price_config.TRIAL_ELIGIBLE_TIERS", set()),
            patch("billing.price_config.TRIAL_PERIOD_DAYS", 0),
            patch("billing.price_config.get_max_self_serve_seats", return_value=10),
            patch("billing.subscription_manager.get_subscription", return_value=None),
            patch("billing.checkout.create_or_get_stripe_customer", return_value="cus_new_promo"),
            patch(
                "billing.price_config.validate_promo_for_interval",
                return_value="Promo not valid for monthly",
            ),
            patch("billing.checkout_orchestrator._rollback_stripe_customer") as mock_rollback,
        ):
            with pytest.raises(CheckoutValidationError, match="Promo not valid"):
                orchestrate_checkout(
                    tier="professional",
                    interval="monthly",
                    seat_count=0,
                    promo_code="BADCODE",
                    dpa_accepted=False,
                    user_id=5,
                    user_email="promo@example.com",
                    db=db,
                )

            mock_rollback.assert_called_once_with("cus_new_promo", 5)

    def test_seat_validation_failure_deletes_new_customer(self):
        """Solo plan with seats after new customer creation triggers rollback."""
        db = _mock_db_session()

        with (
            patch("billing.stripe_client.is_stripe_enabled", return_value=True),
            patch("billing.price_config.get_stripe_price_id", return_value="price_solo_monthly"),
            patch("billing.price_config.TRIAL_ELIGIBLE_TIERS", set()),
            patch("billing.price_config.TRIAL_PERIOD_DAYS", 0),
            patch("billing.price_config.get_max_self_serve_seats", return_value=1),
            patch("billing.subscription_manager.get_subscription", return_value=None),
            patch("billing.checkout.create_or_get_stripe_customer", return_value="cus_new_seat"),
            patch("billing.checkout_orchestrator._rollback_stripe_customer") as mock_rollback,
        ):
            with pytest.raises(CheckoutValidationError, match="Solo plan"):
                orchestrate_checkout(
                    tier="solo",
                    interval="monthly",
                    seat_count=2,
                    promo_code=None,
                    dpa_accepted=False,
                    user_id=8,
                    user_email="seats@example.com",
                    db=db,
                )

            mock_rollback.assert_called_once_with("cus_new_seat", 8)


# ---------------------------------------------------------------------------
# Happy path: no rollback when everything succeeds
# ---------------------------------------------------------------------------


class TestSagaHappyPath:
    """When all steps succeed, no rollback is triggered."""

    def test_successful_checkout_no_rollback(self):
        """Full success path: no rollback, commit called."""
        db = _mock_db_session()

        with (
            patch("billing.stripe_client.is_stripe_enabled", return_value=True),
            patch("billing.price_config.get_stripe_price_id", return_value="price_solo_monthly"),
            patch("billing.price_config.TRIAL_ELIGIBLE_TIERS", {"solo"}),
            patch("billing.price_config.TRIAL_PERIOD_DAYS", 7),
            patch("billing.price_config.get_max_self_serve_seats", return_value=1),
            patch("billing.subscription_manager.get_subscription", return_value=None),
            patch("billing.checkout.create_or_get_stripe_customer", return_value="cus_happy"),
            patch(
                "billing.checkout.create_checkout_session",
                return_value="https://checkout.stripe.com/happy",
            ),
            patch("billing.checkout_orchestrator._rollback_stripe_customer") as mock_rollback,
        ):
            url = orchestrate_checkout(
                tier="solo",
                interval="monthly",
                seat_count=0,
                promo_code=None,
                dpa_accepted=False,
                user_id=1,
                user_email="happy@example.com",
                db=db,
            )

        assert url == "https://checkout.stripe.com/happy"
        mock_rollback.assert_not_called()
        db.commit.assert_called_once()
        db.rollback.assert_not_called()
