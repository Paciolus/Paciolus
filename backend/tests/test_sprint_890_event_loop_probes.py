"""Sprint 890 (CEO brief 15E, review ST-03): blocking work runs off the event loop.

One probe per step: a blocking dependency is held open while ``GET /health/live`` must complete.
See ``tests/helpers/event_loop_probe.py``.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tests.helpers.event_loop_probe import blocking_stand_in, run_probe


def _stripe():
    stripe = MagicMock()
    stripe.error.SignatureVerificationError = type("SignatureVerificationError", (Exception,), {})
    stripe.Webhook.construct_event.return_value = {
        "id": "evt_probe_1",
        "type": "invoice.paid",
        "created": 1711036800,
        "data": {"object": {"id": "in_1", "customer": "cus_probe"}},
    }
    return stripe


@pytest.mark.asyncio
async def test_webhook_processing_leaves_the_loop_free(db_session):
    from database import get_db
    from main import app

    stand_in = blocking_stand_in(result=True)
    app.dependency_overrides[get_db] = lambda: db_session
    try:
        with (
            patch("billing.stripe_client.is_stripe_enabled", return_value=True),
            patch("billing.stripe_client.get_stripe", return_value=_stripe()),
            patch("config.STRIPE_WEBHOOK_SECRET", "FAKE_WEBHOOK_SECRET_FOR_TESTING"),
            patch("billing.webhook_handler.process_webhook_event", side_effect=stand_in),
        ):
            response = await run_probe(
                stand_in,
                lambda c: c.post(
                    "/billing/webhook",
                    content=b"{}",
                    headers={"stripe-signature": "t=1,v1=sig", "content-type": "application/json"},
                ),
            )
    finally:
        app.dependency_overrides.pop(get_db, None)
    assert response.status_code == 200


@pytest.mark.asyncio
@pytest.mark.usefixtures("bypass_csrf")
async def test_logo_storage_leaves_the_loop_free(db_session):
    """Step 2: the S3 put (and the image checks and commit) run in the thread pool."""
    import io

    from PIL import Image

    from auth import require_current_user
    from database import get_db
    from main import app
    from tests.test_branding_api import enterprise_user_with_org

    user = enterprise_user_with_org.__wrapped__(db_session)
    buf = io.BytesIO()
    Image.new("RGB", (120, 40)).save(buf, format="PNG")
    stand_in = blocking_stand_in(result=True)
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[require_current_user] = lambda: user
    try:
        with patch("shared.storage_client.upload_bytes", side_effect=stand_in):
            response = await run_probe(
                stand_in,
                lambda c: c.post("/branding/logo", files={"file": ("logo.png", buf.getvalue(), "image/png")}),
            )
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(require_current_user, None)
    assert response.status_code == 200, response.text
    assert response.json()["logo_size_bytes"] == len(buf.getvalue())
