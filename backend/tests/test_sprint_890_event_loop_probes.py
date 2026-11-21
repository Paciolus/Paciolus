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


@pytest.mark.asyncio
@pytest.mark.usefixtures("bypass_csrf")
async def test_upload_validation_leaves_the_loop_free(override_auth_verified):
    """Step 3: the ZIP / XML bomb scan of an uploaded workbook runs in the thread pool."""
    import io

    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.append(["Account Name", "Debit", "Credit"])
    ws.append(["Cash", 100, 0])
    ws.append(["Common Stock", 0, 100])
    buf = io.BytesIO()
    wb.save(buf)
    stand_in = blocking_stand_in(result=None)
    with patch("shared.upload_pipeline._validate_xlsx_archive", side_effect=stand_in):
        response = await run_probe(
            stand_in,
            lambda c: c.post(
                "/audit/trial-balance",
                files={
                    "file": (
                        "tb.xlsx",
                        buf.getvalue(),
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                },
                data={"force_resubmit": "true"},
            ),
        )
    assert response.status_code == 200, response.text[:300]


@pytest.mark.asyncio
@pytest.mark.usefixtures("bypass_csrf")
async def test_file_tool_database_checks_leave_the_loop_free(override_auth_verified):
    """Step 4: the tier/quota check (and the run recording) of a testing tool run in the thread pool."""
    csv = b"Vendor Name,Amount,Payment Date\nAcme,100.00,2026-01-05\nBeta,250.00,2026-01-06\n"
    stand_in = blocking_stand_in(result=None)
    with patch("shared.testing_route.check_upload_limit", side_effect=stand_in):
        response = await run_probe(
            stand_in,
            lambda c: c.post("/audit/ap-payments", files={"file": ("ap.csv", csv, "text/csv")}),
        )
    assert response.status_code in (200, 400), response.text[:300]


@pytest.mark.asyncio
@pytest.mark.usefixtures("bypass_csrf")
async def test_diagnostic_file_tool_recording_leaves_the_loop_free(override_auth_verified):
    """Step 4: execute_file_tool records the run in the thread pool."""
    csv = b"Account Name,Debit,Credit\nCash,100.00,0\nCommon Stock,0,100.00\n"
    stand_in = blocking_stand_in(result=None)
    with patch("services.audit.file_tool_scaffold.maybe_record_tool_run", side_effect=stand_in):
        response = await run_probe(
            stand_in,
            lambda c: c.post("/audit/preflight", files={"file": ("tb.csv", csv, "text/csv")}),
        )
    assert response.status_code == 200, response.text[:300]
