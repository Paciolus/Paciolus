"""
Sprint 858 — Solo-only checkout gating.

Launch sells Solo only. Until Sprint 853 makes clients firm-owned,
``billing.price_config.SELF_SERVE_TEAM_TIERS_ENABLED`` is off and every
self-serve path onto Professional/Enterprise is refused:

- POST /billing/create-checkout-session (new purchase or upgrade) → 403
- POST /billing/add-seats on a Professional/Enterprise subscription → 403
- Stripe webhooks still sync what Stripe billed, but log a warning.
"""

import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import billing.price_config as price_config
from auth import require_current_user, require_verified_user
from billing.checkout_orchestrator import CheckoutTierNotSelfServeError, orchestrate_checkout
from database import get_db
from main import app
from models import User, UserTier
from subscription_model import Subscription, SubscriptionStatus


@pytest.fixture
def user(db_session):
    u = User(
        email="sales_only_gate@example.com",
        name="Gate User",
        hashed_password="$2b$12$fakehashvalue",
        tier=UserTier.FREE,
        is_active=True,
        is_verified=True,
    )
    db_session.add(u)
    db_session.flush()
    return u


@pytest.fixture
def overrides(db_session, user):
    app.dependency_overrides[require_verified_user] = lambda: user
    app.dependency_overrides[require_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: db_session
    yield user
    app.dependency_overrides.clear()


@pytest.fixture
def stripe_mocks():
    """Stub every Stripe touchpoint the orchestrator reaches."""
    with (
        patch("billing.stripe_client.is_stripe_enabled", return_value=True),
        patch("billing.price_config.get_stripe_price_id", side_effect=lambda t, i: f"price_{t}_{i}"),
        patch("billing.checkout.create_or_get_stripe_customer", return_value="cus_test") as customer,
        patch("billing.checkout.create_checkout_session", return_value="https://checkout.stripe.test/s") as session,
    ):
        yield customer, session


async def _post_checkout(tier: str, **extra):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        return await client.post(
            "/billing/create-checkout-session",
            json={"tier": tier, "interval": "monthly", **extra},
        )


def test_flag_defaults_off():
    """Sprint 853 flips this; until then it must ship off."""
    assert price_config.SELF_SERVE_TEAM_TIERS_ENABLED is False
    assert price_config.is_self_serve_purchasable("solo")
    assert not price_config.is_self_serve_purchasable("professional")
    assert not price_config.is_self_serve_purchasable("enterprise")


def test_flag_on_opens_every_tier(monkeypatch):
    monkeypatch.setattr(price_config, "SELF_SERVE_TEAM_TIERS_ENABLED", True)
    for tier in ("solo", "professional", "enterprise"):
        assert price_config.is_self_serve_purchasable(tier)


@pytest.mark.usefixtures("bypass_csrf")
class TestCheckoutGate:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("tier", ["professional", "enterprise"])
    async def test_team_tier_checkout_is_refused(self, overrides, stripe_mocks, tier):
        customer, session = stripe_mocks
        response = await _post_checkout(tier, dpa_accepted=True)
        assert response.status_code == 403
        assert "sales@paciolus.com" in response.json()["detail"]
        # Refused before any Stripe call — no orphan customer is created.
        customer.assert_not_called()
        session.assert_not_called()

    @pytest.mark.asyncio
    async def test_team_tier_with_seats_is_refused(self, overrides, stripe_mocks):
        response = await _post_checkout("professional", seat_count=3, dpa_accepted=True)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_solo_checkout_still_works(self, overrides, stripe_mocks):
        _, session = stripe_mocks
        response = await _post_checkout("solo")
        assert response.status_code == 201
        assert response.json()["checkout_url"] == "https://checkout.stripe.test/s"
        session.assert_called_once()

    @pytest.mark.asyncio
    async def test_solo_to_professional_upgrade_is_refused(self, overrides, stripe_mocks, db_session, user):
        """An existing Solo subscriber cannot upgrade self-serve either."""
        db_session.add(Subscription(user_id=user.id, tier="solo", status=SubscriptionStatus.ACTIVE))
        db_session.flush()
        response = await _post_checkout("professional", dpa_accepted=True)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_flag_on_allows_professional(self, overrides, stripe_mocks, monkeypatch):
        monkeypatch.setattr(price_config, "SELF_SERVE_TEAM_TIERS_ENABLED", True)
        response = await _post_checkout("professional", dpa_accepted=True)
        assert response.status_code == 201

    @pytest.mark.parametrize("tier", ["professional", "enterprise"])
    def test_orchestrator_refuses_even_when_billing_is_off(self, tier):
        """The gate is a product rule, checked ahead of the billing-enabled 503."""
        with patch("billing.stripe_client.is_stripe_enabled", return_value=False):
            with pytest.raises(CheckoutTierNotSelfServeError):
                orchestrate_checkout(
                    tier=tier,
                    interval="monthly",
                    seat_count=0,
                    promo_code=None,
                    dpa_accepted=True,
                    user_id=1,
                    user_email="x@example.com",
                    db=MagicMock(),
                )


@pytest.mark.usefixtures("bypass_csrf")
class TestAddSeatsGate:
    async def _post_add_seats(self):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            return await client.post("/billing/add-seats", json={"seats": 1})

    @pytest.mark.asyncio
    @pytest.mark.parametrize("tier", ["professional", "enterprise"])
    async def test_seat_add_on_is_refused(self, overrides, db_session, user, tier):
        db_session.add(
            Subscription(
                user_id=user.id,
                tier=tier,
                status=SubscriptionStatus.ACTIVE,
                stripe_subscription_id=f"sub_{tier}",
                seat_count=7,
            )
        )
        db_session.flush()
        with patch("billing.subscription_manager.add_seats") as add_seats:
            response = await self._post_add_seats()
        assert response.status_code == 403
        assert "sales@paciolus.com" in response.json()["detail"]
        add_seats.assert_not_called()

    @pytest.mark.asyncio
    async def test_flag_on_allows_seat_add_on(self, overrides, db_session, user, monkeypatch):
        monkeypatch.setattr(price_config, "SELF_SERVE_TEAM_TIERS_ENABLED", True)
        db_session.add(
            Subscription(
                user_id=user.id,
                tier="professional",
                status=SubscriptionStatus.ACTIVE,
                stripe_subscription_id="sub_pro_on",
                seat_count=7,
            )
        )
        db_session.flush()
        result = MagicMock(seat_count=7, additional_seats=1, total_seats=8)
        with (
            patch("billing.stripe_client.is_stripe_enabled", return_value=True),
            patch("billing.subscription_manager.add_seats", return_value=result),
        ):
            response = await self._post_add_seats()
        assert response.status_code == 200
        assert response.json()["total_seats"] == 8


class TestWebhookFlag:
    def test_sales_only_tier_from_stripe_is_logged(self, caplog):
        from billing.webhook_handler import _flag_sales_only_tier

        with caplog.at_level(logging.WARNING, logger="billing.webhook_handler"):
            _flag_sales_only_tier("customer.subscription.updated", 7, "professional")
            _flag_sales_only_tier("customer.subscription.updated", 8, "solo")
        messages = [r.getMessage() for r in caplog.records]
        assert len(messages) == 1
        assert "sales-only tier professional" in messages[0]
