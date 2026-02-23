"""
Tests for Sprint 363 — Subscription Model.

Covers:
1. Model creation and defaults
2. Enum values
3. to_dict serialization
4. Unique constraint on user_id
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from subscription_model import BillingInterval, Subscription, SubscriptionStatus


class TestSubscriptionStatus:
    """SubscriptionStatus enum values match Stripe lifecycle."""

    def test_all_values(self):
        assert set(s.value for s in SubscriptionStatus) == {
            "active", "past_due", "canceled", "trialing",
        }

    def test_str_subclass(self):
        assert isinstance(SubscriptionStatus.ACTIVE, str)
        assert SubscriptionStatus.ACTIVE == "active"


class TestBillingInterval:
    """BillingInterval enum values."""

    def test_all_values(self):
        assert set(i.value for i in BillingInterval) == {"monthly", "annual"}


class TestSubscriptionModel:
    """Subscription SQLAlchemy model structure."""

    def test_tablename(self):
        assert Subscription.__tablename__ == "subscriptions"

    def test_columns_exist(self):
        col_names = {c.name for c in Subscription.__table__.columns}
        expected = {
            "id", "user_id", "tier", "status", "billing_interval",
            "stripe_customer_id", "stripe_subscription_id",
            "current_period_start", "current_period_end",
            "cancel_at_period_end", "created_at", "updated_at",
        }
        assert expected.issubset(col_names)

    def test_user_id_unique(self):
        user_id_col = Subscription.__table__.c.user_id
        assert user_id_col.unique

    def test_stripe_customer_id_unique(self):
        col = Subscription.__table__.c.stripe_customer_id
        assert col.unique

    def test_stripe_subscription_id_unique(self):
        col = Subscription.__table__.c.stripe_subscription_id
        assert col.unique

    def test_to_dict(self):
        sub = Subscription()
        sub.id = 1
        sub.user_id = 42
        sub.tier = "starter"
        sub.status = SubscriptionStatus.ACTIVE
        sub.billing_interval = BillingInterval.MONTHLY
        sub.cancel_at_period_end = False

        d = sub.to_dict()
        assert d["id"] == 1
        assert d["user_id"] == 42
        assert d["tier"] == "starter"
        assert d["status"] == "active"
        assert d["billing_interval"] == "monthly"
        assert d["cancel_at_period_end"] is False

    def test_to_dict_nullable_fields(self):
        sub = Subscription()
        sub.id = 2
        sub.user_id = 99
        sub.tier = "free"
        sub.status = SubscriptionStatus.ACTIVE
        sub.cancel_at_period_end = False

        d = sub.to_dict()
        assert d["billing_interval"] is None
        assert d["stripe_customer_id"] is None
        assert d["current_period_start"] is None
        assert d["current_period_end"] is None

    def test_repr(self):
        sub = Subscription()
        sub.id = 1
        sub.user_id = 42
        sub.tier = "professional"
        sub.status = SubscriptionStatus.ACTIVE
        r = repr(sub)
        assert "Subscription" in r
        assert "42" in r
