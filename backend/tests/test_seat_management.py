"""
Seat management tests — Phase LIX Sprint E.

Covers:
1. Route registration for add-seats / remove-seats
2. Checkout seat_count field validation
3. Subscription model seat fields and total_seats
4. add_seats / remove_seats subscription_manager logic
5. Billing route schema validation (SeatChangeRequest/Response)
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from models import UserTier
from subscription_model import BillingInterval, Subscription, SubscriptionStatus

# ---------------------------------------------------------------------------
# Route registration
# ---------------------------------------------------------------------------


class TestSeatRouteRegistration:
    """Verify seat management routes are registered."""

    def test_add_seats_route_exists(self):
        from main import app

        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/billing/add-seats" in paths

    def test_remove_seats_route_exists(self):
        from main import app

        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/billing/remove-seats" in paths


# ---------------------------------------------------------------------------
# Subscription model seat fields
# ---------------------------------------------------------------------------


class TestSubscriptionSeatFields:
    """Verify Subscription model seat columns and total_seats property."""

    def test_default_seat_count_is_1(self, db_session, make_user):
        user = make_user(email="seat_default@example.com")
        sub = Subscription(
            user_id=user.id,
            tier=UserTier.TEAM,
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            stripe_customer_id="cus_seat1",
            stripe_subscription_id="sub_seat1",
            seat_count=1,
            additional_seats=0,
        )
        db_session.add(sub)
        db_session.flush()
        assert sub.seat_count == 1
        assert sub.additional_seats == 0

    def test_total_seats_computed(self, db_session, make_user):
        user = make_user(email="seat_total@example.com")
        sub = Subscription(
            user_id=user.id,
            tier=UserTier.TEAM,
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            stripe_customer_id="cus_seat2",
            stripe_subscription_id="sub_seat2",
            seat_count=3,
            additional_seats=5,
        )
        db_session.add(sub)
        db_session.flush()
        assert sub.total_seats == 8

    def test_total_seats_with_zero_additional(self, db_session, make_user):
        user = make_user(email="seat_zero@example.com")
        sub = Subscription(
            user_id=user.id,
            tier=UserTier.TEAM,
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            stripe_customer_id="cus_seat3",
            stripe_subscription_id="sub_seat3",
            seat_count=3,
            additional_seats=0,
        )
        db_session.add(sub)
        db_session.flush()
        assert sub.total_seats == 3

    def test_seat_fields_in_to_dict(self, db_session, make_user):
        user = make_user(email="seat_dict@example.com")
        sub = Subscription(
            user_id=user.id,
            tier=UserTier.TEAM,
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            stripe_customer_id="cus_seat4",
            stripe_subscription_id="sub_seat4",
            seat_count=3,
            additional_seats=2,
        )
        db_session.add(sub)
        db_session.flush()
        d = sub.to_dict()
        assert d["seat_count"] == 3
        assert d["additional_seats"] == 2
        assert d["total_seats"] == 5


# ---------------------------------------------------------------------------
# Checkout seat_count schema validation
# ---------------------------------------------------------------------------


class TestCheckoutSeatCount:
    """Verify CheckoutRequest seat_count field constraints."""

    def test_checkout_request_accepts_seat_count(self):
        from routes.billing import CheckoutRequest

        req = CheckoutRequest(
            tier="team",
            interval="monthly",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
            seat_count=5,
        )
        assert req.seat_count == 5

    def test_checkout_request_default_seat_count_zero(self):
        from routes.billing import CheckoutRequest

        req = CheckoutRequest(
            tier="team",
            interval="monthly",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
        )
        assert req.seat_count == 0

    def test_checkout_request_rejects_negative_seats(self):
        from pydantic import ValidationError

        from routes.billing import CheckoutRequest

        with pytest.raises(ValidationError):
            CheckoutRequest(
                tier="team",
                interval="monthly",
                success_url="https://example.com/success",
                cancel_url="https://example.com/cancel",
                seat_count=-1,
            )

    def test_checkout_request_rejects_seats_over_max(self):
        from pydantic import ValidationError

        from routes.billing import CheckoutRequest

        with pytest.raises(ValidationError):
            CheckoutRequest(
                tier="team",
                interval="monthly",
                success_url="https://example.com/success",
                cancel_url="https://example.com/cancel",
                seat_count=23,  # max is 22
            )


# ---------------------------------------------------------------------------
# SeatChangeRequest / SeatChangeResponse schema validation
# ---------------------------------------------------------------------------


class TestSeatChangeSchemas:
    """Verify seat change Pydantic schemas."""

    def test_seat_change_request_valid(self):
        from routes.billing import SeatChangeRequest

        req = SeatChangeRequest(seats=3)
        assert req.seats == 3

    def test_seat_change_request_rejects_zero(self):
        from pydantic import ValidationError

        from routes.billing import SeatChangeRequest

        with pytest.raises(ValidationError):
            SeatChangeRequest(seats=0)

    def test_seat_change_request_rejects_negative(self):
        from pydantic import ValidationError

        from routes.billing import SeatChangeRequest

        with pytest.raises(ValidationError):
            SeatChangeRequest(seats=-1)

    def test_seat_change_request_rejects_over_max(self):
        from pydantic import ValidationError

        from routes.billing import SeatChangeRequest

        with pytest.raises(ValidationError):
            SeatChangeRequest(seats=23)

    def test_seat_change_response_fields(self):
        from routes.billing import SeatChangeResponse

        resp = SeatChangeResponse(
            message="Added 2 seats",
            seat_count=3,
            additional_seats=2,
            total_seats=5,
        )
        assert resp.seat_count == 3
        assert resp.additional_seats == 2
        assert resp.total_seats == 5


# ---------------------------------------------------------------------------
# Subscription manager: add_seats / remove_seats logic
# ---------------------------------------------------------------------------


class TestAddSeatsManager:
    """Test add_seats function in subscription_manager."""

    def test_add_seats_returns_none_without_subscription(self, db_session, make_user):
        from billing.subscription_manager import add_seats

        user = make_user(email="no_sub_add@example.com")
        result = add_seats(db_session, user.id, 1)
        assert result is None

    def test_add_seats_returns_none_without_stripe_id(self, db_session, make_user):
        from billing.subscription_manager import add_seats

        user = make_user(email="no_stripe_add@example.com")
        sub = Subscription(
            user_id=user.id,
            tier=UserTier.TEAM,
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            stripe_customer_id="cus_add1",
            stripe_subscription_id=None,  # No Stripe subscription
            seat_count=3,
            additional_seats=0,
        )
        db_session.add(sub)
        db_session.flush()
        result = add_seats(db_session, user.id, 1)
        assert result is None

    @patch("billing.subscription_manager.get_stripe")
    def test_add_seats_exceeding_max_returns_none(self, mock_get_stripe, db_session, make_user):
        from billing.subscription_manager import add_seats

        user = make_user(email="max_seats_add@example.com")
        sub = Subscription(
            user_id=user.id,
            tier=UserTier.TEAM,
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            stripe_customer_id="cus_add2",
            stripe_subscription_id="sub_add2",
            seat_count=3,
            additional_seats=20,
        )
        db_session.add(sub)
        db_session.flush()
        # 3 base + 20 additional + 5 new = 28 > MAX_SELF_SERVE_SEATS (25)
        result = add_seats(db_session, user.id, 5)
        assert result is None

    @patch("billing.subscription_manager.get_stripe")
    def test_add_seats_success(self, mock_get_stripe, db_session, make_user):
        from billing.subscription_manager import add_seats

        mock_stripe = MagicMock()
        mock_get_stripe.return_value = mock_stripe
        mock_stripe.Subscription.retrieve.return_value = {"items": {"data": [{"id": "si_test", "quantity": 3}]}}

        user = make_user(email="add_seats_ok@example.com")
        sub = Subscription(
            user_id=user.id,
            tier=UserTier.TEAM,
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            stripe_customer_id="cus_add3",
            stripe_subscription_id="sub_add3",
            seat_count=3,
            additional_seats=0,
        )
        db_session.add(sub)
        db_session.flush()

        result = add_seats(db_session, user.id, 2)
        assert result is not None
        assert result.additional_seats == 2
        mock_stripe.SubscriptionItem.modify.assert_called_once_with("si_test", quantity=5)


class TestRemoveSeatsManager:
    """Test remove_seats function in subscription_manager."""

    def test_remove_seats_returns_none_without_subscription(self, db_session, make_user):
        from billing.subscription_manager import remove_seats

        user = make_user(email="no_sub_rm@example.com")
        result = remove_seats(db_session, user.id, 1)
        assert result is None

    def test_remove_seats_returns_none_below_zero(self, db_session, make_user):
        from billing.subscription_manager import remove_seats

        user = make_user(email="below_zero_rm@example.com")
        sub = Subscription(
            user_id=user.id,
            tier=UserTier.TEAM,
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            stripe_customer_id="cus_rm1",
            stripe_subscription_id="sub_rm1",
            seat_count=3,
            additional_seats=1,
        )
        db_session.add(sub)
        db_session.flush()
        # Trying to remove 2 when only 1 additional
        result = remove_seats(db_session, user.id, 2)
        assert result is None

    @patch("billing.subscription_manager.get_stripe")
    def test_remove_seats_success(self, mock_get_stripe, db_session, make_user):
        from billing.subscription_manager import remove_seats

        mock_stripe = MagicMock()
        mock_get_stripe.return_value = mock_stripe
        mock_stripe.Subscription.retrieve.return_value = {"items": {"data": [{"id": "si_test", "quantity": 5}]}}

        user = make_user(email="rm_seats_ok@example.com")
        sub = Subscription(
            user_id=user.id,
            tier=UserTier.TEAM,
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            stripe_customer_id="cus_rm2",
            stripe_subscription_id="sub_rm2",
            seat_count=3,
            additional_seats=2,
        )
        db_session.add(sub)
        db_session.flush()

        result = remove_seats(db_session, user.id, 1)
        assert result is not None
        assert result.additional_seats == 1
        mock_stripe.SubscriptionItem.modify.assert_called_once_with("si_test", quantity=4)

    @patch("billing.subscription_manager.get_stripe")
    def test_remove_all_additional_seats(self, mock_get_stripe, db_session, make_user):
        from billing.subscription_manager import remove_seats

        mock_stripe = MagicMock()
        mock_get_stripe.return_value = mock_stripe
        mock_stripe.Subscription.retrieve.return_value = {"items": {"data": [{"id": "si_test", "quantity": 5}]}}

        user = make_user(email="rm_all_seats@example.com")
        sub = Subscription(
            user_id=user.id,
            tier=UserTier.TEAM,
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            stripe_customer_id="cus_rm3",
            stripe_subscription_id="sub_rm3",
            seat_count=3,
            additional_seats=2,
        )
        db_session.add(sub)
        db_session.flush()

        result = remove_seats(db_session, user.id, 2)
        assert result is not None
        assert result.additional_seats == 0
        mock_stripe.SubscriptionItem.modify.assert_called_once_with("si_test", quantity=3)


# ---------------------------------------------------------------------------
# Checkout seat quantity wiring
# ---------------------------------------------------------------------------


class TestCheckoutSeatQuantity:
    """Test that checkout.py passes seat_quantity correctly."""

    @patch("billing.checkout.get_stripe")
    def test_checkout_with_seat_quantity(self, mock_get_stripe):
        from billing.checkout import create_checkout_session

        mock_stripe = MagicMock()
        mock_get_stripe.return_value = mock_stripe
        mock_session = MagicMock()
        mock_session.id = "cs_test"
        mock_session.url = "https://checkout.stripe.com/test"
        mock_stripe.checkout.Session.create.return_value = mock_session

        url = create_checkout_session(
            customer_id="cus_test",
            price_id="price_test",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
            user_id=1,
            seat_quantity=5,
        )

        assert url == "https://checkout.stripe.com/test"
        call_kwargs = mock_stripe.checkout.Session.create.call_args[1]
        assert call_kwargs["line_items"] == [{"price": "price_test", "quantity": 5}]

    @patch("billing.checkout.get_stripe")
    def test_checkout_default_quantity_is_1(self, mock_get_stripe):
        from billing.checkout import create_checkout_session

        mock_stripe = MagicMock()
        mock_get_stripe.return_value = mock_stripe
        mock_session = MagicMock()
        mock_session.id = "cs_test"
        mock_session.url = "https://checkout.stripe.com/test"
        mock_stripe.checkout.Session.create.return_value = mock_session

        create_checkout_session(
            customer_id="cus_test",
            price_id="price_test",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
            user_id=1,
        )

        call_kwargs = mock_stripe.checkout.Session.create.call_args[1]
        assert call_kwargs["line_items"] == [{"price": "price_test", "quantity": 1}]

    @patch("billing.checkout.get_stripe")
    def test_checkout_zero_quantity_becomes_1(self, mock_get_stripe):
        from billing.checkout import create_checkout_session

        mock_stripe = MagicMock()
        mock_get_stripe.return_value = mock_stripe
        mock_session = MagicMock()
        mock_session.id = "cs_test"
        mock_session.url = "https://checkout.stripe.com/test"
        mock_stripe.checkout.Session.create.return_value = mock_session

        create_checkout_session(
            customer_id="cus_test",
            price_id="price_test",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
            user_id=1,
            seat_quantity=0,
        )

        call_kwargs = mock_stripe.checkout.Session.create.call_args[1]
        assert call_kwargs["line_items"] == [{"price": "price_test", "quantity": 1}]


# ---------------------------------------------------------------------------
# Subscription response seat fields
# ---------------------------------------------------------------------------


class TestSubscriptionResponseSeatFields:
    """Verify SubscriptionResponse includes seat fields."""

    def test_subscription_response_defaults(self):
        from routes.billing import SubscriptionResponse

        resp = SubscriptionResponse(tier="free", status="active")
        assert resp.seat_count == 1
        assert resp.additional_seats == 0
        assert resp.total_seats == 1

    def test_subscription_response_with_seats(self):
        from routes.billing import SubscriptionResponse

        resp = SubscriptionResponse(
            tier="team",
            status="active",
            seat_count=3,
            additional_seats=4,
            total_seats=7,
        )
        assert resp.seat_count == 3
        assert resp.additional_seats == 4
        assert resp.total_seats == 7
