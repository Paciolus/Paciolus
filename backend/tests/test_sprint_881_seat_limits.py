"""Sprint 881 (6E) — request seat limits come from the configured maximums.

The checkout request capped add-on seats at a literal 60, the seat-change request at 22,
and the add-seats error said "contact sales for 26+ seats", while the configured
maximums are 20 total seats for Professional and 100 for Enterprise
(``billing/price_config.py``) with 7 and 20 included (``shared/entitlements.py``).
Every bound and the message are now derived from those.
"""

import pytest
from pydantic import ValidationError

from billing.price_config import (
    MAX_SELF_SERVE_SEATS_ENTERPRISE,
    MAX_SELF_SERVE_SEATS_PROFESSIONAL,
    max_additional_seats,
)
from models import UserTier
from schemas.billing_schemas import CheckoutRequest, SeatChangeRequest
from shared.entitlements import get_entitlements

PRO_ADDONS = MAX_SELF_SERVE_SEATS_PROFESSIONAL - get_entitlements(UserTier.PROFESSIONAL).seats_included
ENT_ADDONS = MAX_SELF_SERVE_SEATS_ENTERPRISE - get_entitlements(UserTier.ENTERPRISE).seats_included


def test_configured_add_on_maximums():
    assert (PRO_ADDONS, ENT_ADDONS) == (13, 80)
    assert max_additional_seats("professional") == 13
    assert max_additional_seats("enterprise") == 80
    assert max_additional_seats("solo") == 0
    assert max_additional_seats("free") == 0


@pytest.mark.parametrize("model", ["checkout", "seat_change"])
def test_request_bound_is_the_largest_configured_add_on_count(model):
    def build(n):
        if model == "checkout":
            return CheckoutRequest(tier="enterprise", interval="monthly", seat_count=n)
        return SeatChangeRequest(seats=n)

    build(ENT_ADDONS)
    with pytest.raises(ValidationError):
        build(ENT_ADDONS + 1)


@pytest.mark.parametrize(
    ("tier", "max_total"),
    [("professional", MAX_SELF_SERVE_SEATS_PROFESSIONAL), ("enterprise", MAX_SELF_SERVE_SEATS_ENTERPRISE)],
)
@pytest.mark.usefixtures("bypass_csrf")
@pytest.mark.anyio
async def test_add_seats_refusal_names_the_tiers_sales_threshold(db_session, make_user, monkeypatch, tier, max_total):
    from unittest.mock import patch

    import httpx

    import billing.price_config as price_config
    from auth import require_current_user
    from database import get_db
    from main import app
    from subscription_model import BillingInterval, Subscription, SubscriptionStatus

    monkeypatch.setattr(price_config, "SELF_SERVE_TEAM_TIERS_ENABLED", True)
    user = make_user(email=f"6e_{tier}@example.com", tier=UserTier(tier))
    db_session.add(
        Subscription(
            user_id=user.id,
            tier=tier,
            status=SubscriptionStatus.ACTIVE,
            billing_interval=BillingInterval.MONTHLY,
            stripe_subscription_id=f"sub_6e_{tier}",
            seat_count=get_entitlements(UserTier(tier)).seats_included,
            additional_seats=0,
        )
    )
    db_session.flush()

    app.dependency_overrides[require_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: db_session
    try:
        with (
            patch("billing.stripe_client.is_stripe_enabled", return_value=True),
            patch("billing.subscription_manager.add_seats", return_value=None),
        ):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post("/billing/add-seats", json={"seats": 1})
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 400
    detail = resp.json()["detail"]
    assert f"{max_total + 1}+" in detail
    assert "26+" not in detail
