"""
Tests for billing webhook route error classification.

Sprint 564: Verifies that the webhook endpoint returns the correct HTTP
status codes for different error categories:
- 400 for data validation errors (bad payload, missing fields)
- 500 for operational errors (DB failures, Stripe API timeouts)
- 200 for duplicate events and unknown event types
"""

from unittest.mock import MagicMock, patch

import httpx
import pytest


@pytest.fixture
def mock_stripe():
    """Create a mock Stripe module with error classes."""
    stripe = MagicMock()
    stripe.error.SignatureVerificationError = type("SignatureVerificationError", (Exception,), {})
    return stripe


def _make_event(event_id="evt_test_123", event_type="checkout.session.completed"):
    """Build a minimal Stripe event dict."""
    return {
        "id": event_id,
        "type": event_type,
        "created": 1711036800,
        "data": {
            "object": {
                "id": "cs_test",
                "customer": "cus_test",
                "subscription": "sub_test",
            },
        },
    }


class TestWebhookErrorClassification:
    """Verify correct HTTP status codes for webhook error scenarios."""

    @pytest.mark.asyncio
    async def test_invalid_json_payload_returns_400(self, mock_stripe):
        """ValueError from construct_event (malformed JSON) returns 400."""
        from main import app

        mock_stripe.Webhook.construct_event.side_effect = ValueError("Invalid JSON")

        with (
            patch("billing.stripe_client.is_stripe_enabled", return_value=True),
            patch("billing.stripe_client.get_stripe", return_value=mock_stripe),
            patch("config.STRIPE_WEBHOOK_SECRET", "FAKE_WEBHOOK_SECRET_FOR_TESTING"),
        ):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/billing/webhook",
                    content=b"not valid json",
                    headers={
                        "stripe-signature": "t=123,v1=sig",
                        "content-type": "application/json",
                    },
                )

        assert response.status_code == 400
        assert "Invalid payload" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_handler_value_error_returns_400(self, mock_stripe):
        """ValueError from process_webhook_event returns 400 (data error, not retryable)."""
        from main import app

        mock_stripe.Webhook.construct_event.return_value = _make_event()

        with (
            patch("billing.stripe_client.is_stripe_enabled", return_value=True),
            patch("billing.stripe_client.get_stripe", return_value=mock_stripe),
            patch("config.STRIPE_WEBHOOK_SECRET", "FAKE_WEBHOOK_SECRET_FOR_TESTING"),
            patch(
                "billing.webhook_handler.process_webhook_event",
                side_effect=ValueError("Unknown price_id"),
            ),
        ):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/billing/webhook",
                    content=b'{"type":"checkout.session.completed"}',
                    headers={
                        "stripe-signature": "t=123,v1=sig",
                        "content-type": "application/json",
                    },
                )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_handler_key_error_returns_400(self, mock_stripe):
        """KeyError from process_webhook_event returns 400 (missing field, not retryable)."""
        from main import app

        mock_stripe.Webhook.construct_event.return_value = _make_event()

        with (
            patch("billing.stripe_client.is_stripe_enabled", return_value=True),
            patch("billing.stripe_client.get_stripe", return_value=mock_stripe),
            patch("config.STRIPE_WEBHOOK_SECRET", "FAKE_WEBHOOK_SECRET_FOR_TESTING"),
            patch(
                "billing.webhook_handler.process_webhook_event",
                side_effect=KeyError("subscription"),
            ),
        ):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/billing/webhook",
                    content=b'{"type":"checkout.session.completed"}',
                    headers={
                        "stripe-signature": "t=123,v1=sig",
                        "content-type": "application/json",
                    },
                )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_handler_operational_error_returns_500(self, mock_stripe):
        """Generic exception from process_webhook_event returns 500 (operational, retryable)."""
        from main import app

        mock_stripe.Webhook.construct_event.return_value = _make_event()

        with (
            patch("billing.stripe_client.is_stripe_enabled", return_value=True),
            patch("billing.stripe_client.get_stripe", return_value=mock_stripe),
            patch("config.STRIPE_WEBHOOK_SECRET", "FAKE_WEBHOOK_SECRET_FOR_TESTING"),
            patch(
                "billing.webhook_handler.process_webhook_event",
                side_effect=ConnectionError("DB connection lost"),
            ),
        ):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/billing/webhook",
                    content=b'{"type":"checkout.session.completed"}',
                    headers={
                        "stripe-signature": "t=123,v1=sig",
                        "content-type": "application/json",
                    },
                )

        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_missing_signature_header_returns_400(self, mock_stripe):
        """POST without ``stripe-signature`` header returns 400 (bad request,
        not retryable). Sprint 733: explicit unit coverage for the early-return
        branch at ``billing.py:365``. Previously only exercised by integration-level
        tests; this asserts ``construct_event`` is never even called when the
        header is absent (signature is the gate, not an after-the-fact check).
        """
        from main import app

        with (
            patch("billing.stripe_client.is_stripe_enabled", return_value=True),
            patch("billing.stripe_client.get_stripe", return_value=mock_stripe),
            patch("config.STRIPE_WEBHOOK_SECRET", "FAKE_WEBHOOK_SECRET_FOR_TESTING"),
        ):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/billing/webhook",
                    content=b'{"type":"checkout.session.completed"}',
                    headers={"content-type": "application/json"},
                    # No stripe-signature header
                )

        assert response.status_code == 400
        assert "Missing stripe-signature header" in response.json()["detail"]
        # construct_event must NOT be called when sig header is absent —
        # signature verification is the gate, not an after-the-fact check.
        mock_stripe.Webhook.construct_event.assert_not_called()

    @pytest.mark.asyncio
    async def test_duplicate_event_returns_200_without_double_processing(self, mock_stripe, db_session):
        """Duplicate webhook event ID returns 200 silently and does NOT invoke
        ``process_webhook_event`` a second time.

        Sprint 733: critical for Stripe retry semantics. The dedup INSERT is
        wrapped in ``try: db.flush() except IntegrityError`` (``billing.py:402-408``);
        if this regresses, duplicate Stripe deliveries get processed twice and
        side effects (subscription updates, refunds, etc.) double-run. The
        existing ``test_db_dedup_error_returns_500`` covers the *generic* DB
        error path; this one covers the specifically-handled IntegrityError
        path that should return success-without-action.
        """
        from sqlalchemy.exc import IntegrityError

        from database import get_db
        from main import app

        mock_stripe.Webhook.construct_event.return_value = _make_event(event_id="evt_dup_test_733")

        with (
            patch("billing.stripe_client.is_stripe_enabled", return_value=True),
            patch("billing.stripe_client.get_stripe", return_value=mock_stripe),
            patch("config.STRIPE_WEBHOOK_SECRET", "FAKE_WEBHOOK_SECRET_FOR_TESTING"),
            patch("billing.webhook_handler.process_webhook_event", return_value=True) as mock_process,
            patch.object(db_session, "flush", side_effect=IntegrityError("duplicate", {}, Exception("orig"))),
        ):
            app.dependency_overrides[get_db] = lambda: db_session
            try:
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.post(
                        "/billing/webhook",
                        content=b'{"type":"checkout.session.completed"}',
                        headers={
                            "stripe-signature": "t=123,v1=sig",
                            "content-type": "application/json",
                        },
                    )
            finally:
                app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 200
        # Critical assertion: process_webhook_event must NOT be called when
        # the dedup INSERT detects a duplicate. If this assertion regresses,
        # Stripe retries cause double-processing of subscription/payment events.
        mock_process.assert_not_called()

    @pytest.mark.asyncio
    async def test_stripe_disabled_returns_200_short_circuit(self):
        """When ``is_stripe_enabled()`` returns False, the webhook short-circuits
        to 200 without any verification or processing.

        Sprint 733 (bonus): documents the production safe-mode where Stripe is
        intentionally disabled (e.g., during the pre-cutover window). Returns
        200 so Stripe doesn't mark the endpoint unreachable and back off.
        """
        from main import app

        with patch("billing.stripe_client.is_stripe_enabled", return_value=False):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/billing/webhook",
                    content=b'{"type":"anything"}',
                    headers={"content-type": "application/json"},
                )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_db_dedup_error_returns_500(self, mock_stripe, db_session):
        """DB error during dedup insert returns 500 (operational, retryable)."""
        from database import get_db
        from main import app

        mock_stripe.Webhook.construct_event.return_value = _make_event(event_id="evt_dedup_error")

        # Make db.flush() raise a generic error (not IntegrityError)
        original_flush = db_session.flush

        def bad_flush(*args, **kwargs):
            raise RuntimeError("Connection reset")

        with (
            patch("billing.stripe_client.is_stripe_enabled", return_value=True),
            patch("billing.stripe_client.get_stripe", return_value=mock_stripe),
            patch("config.STRIPE_WEBHOOK_SECRET", "FAKE_WEBHOOK_SECRET_FOR_TESTING"),
        ):
            app.dependency_overrides[get_db] = lambda: db_session

            # Patch flush at session level to simulate DB failure during dedup
            with patch.object(db_session, "flush", side_effect=RuntimeError("Connection reset")):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.post(
                        "/billing/webhook",
                        content=b'{"type":"checkout.session.completed"}',
                        headers={
                            "stripe-signature": "t=123,v1=sig",
                            "content-type": "application/json",
                        },
                    )

            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 500
