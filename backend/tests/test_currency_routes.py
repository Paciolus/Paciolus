"""
Tests for Currency Routes — Sprint 258

Validates route registration, session storage, and response models.
Note: TestClient incompatibility means we test via route inspection
and unit-test session storage directly.
"""

import pytest
import time
from datetime import datetime, UTC
from decimal import Decimal

from routes.currency import (
    get_user_rate_table,
    set_user_rate_table,
    clear_user_rate_table,
    _rate_sessions,
    _rate_timestamps,
    _cleanup_expired_sessions,
    _SESSION_TTL_SECONDS,
    _MAX_SESSIONS,
    RateTableUploadResponse,
    SingleRateResponse,
    RateTableStatusResponse,
    SingleRateRequest,
)
from currency_engine import CurrencyRateTable, ExchangeRate
from datetime import date


# =============================================================================
# Session Storage
# =============================================================================

class TestSessionStorage:
    def setup_method(self):
        """Clear session storage before each test."""
        _rate_sessions.clear()
        _rate_timestamps.clear()

    def _make_table(self, currency="USD"):
        return CurrencyRateTable(
            rates=[ExchangeRate(date(2026, 1, 31), "EUR", "USD", Decimal("1.05"))],
            uploaded_at=datetime.now(UTC),
            presentation_currency=currency,
        )

    def test_set_and_get(self):
        table = self._make_table()
        set_user_rate_table(1, table)
        result = get_user_rate_table(1)
        assert result is not None
        assert result.presentation_currency == "USD"
        assert len(result.rates) == 1

    def test_get_nonexistent_returns_none(self):
        assert get_user_rate_table(999) is None

    def test_clear(self):
        set_user_rate_table(1, self._make_table())
        assert clear_user_rate_table(1) is True
        assert get_user_rate_table(1) is None

    def test_clear_nonexistent(self):
        assert clear_user_rate_table(999) is False

    def test_overwrite_existing(self):
        set_user_rate_table(1, self._make_table("USD"))
        set_user_rate_table(1, self._make_table("EUR"))
        result = get_user_rate_table(1)
        assert result is not None
        assert result.presentation_currency == "EUR"

    def test_multiple_users(self):
        set_user_rate_table(1, self._make_table("USD"))
        set_user_rate_table(2, self._make_table("EUR"))
        assert get_user_rate_table(1) is not None
        assert get_user_rate_table(2) is not None
        assert get_user_rate_table(1).presentation_currency == "USD"
        assert get_user_rate_table(2).presentation_currency == "EUR"


# =============================================================================
# Route Registration
# =============================================================================

class TestRouteRegistration:
    def test_currency_routes_registered(self):
        from main import app
        route_paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/audit/currency-rates" in route_paths
        assert "/audit/currency-rate" in route_paths

    def test_currency_router_tags(self):
        from routes.currency import router
        assert "currency" in router.tags


# =============================================================================
# Response Models
# =============================================================================

class TestResponseModels:
    def test_rate_table_upload_response(self):
        resp = RateTableUploadResponse(
            rate_count=5,
            presentation_currency="USD",
            currency_pairs=["EUR/USD", "GBP/USD"],
            uploaded_at="2026-02-15T10:00:00",
        )
        assert resp.rate_count == 5
        assert resp.presentation_currency == "USD"

    def test_single_rate_response(self):
        resp = SingleRateResponse(
            from_currency="EUR",
            to_currency="USD",
            rate="1.0523",
            presentation_currency="USD",
            total_rates=1,
        )
        assert resp.from_currency == "EUR"
        assert resp.rate == "1.0523"

    def test_rate_table_status_no_rates(self):
        resp = RateTableStatusResponse(has_rates=False)
        assert resp.has_rates is False
        assert resp.rate_count == 0

    def test_rate_table_status_with_rates(self):
        resp = RateTableStatusResponse(
            has_rates=True,
            rate_count=3,
            presentation_currency="EUR",
            currency_pairs=["USD/EUR"],
        )
        assert resp.has_rates is True
        assert resp.rate_count == 3


# =============================================================================
# Request Validation
# =============================================================================

class TestRequestValidation:
    def test_single_rate_request_valid(self):
        req = SingleRateRequest(
            from_currency="EUR",
            to_currency="USD",
            rate="1.05",
        )
        assert req.from_currency == "EUR"

    def test_single_rate_request_with_presentation(self):
        req = SingleRateRequest(
            from_currency="EUR",
            to_currency="USD",
            rate="1.05",
            presentation_currency="GBP",
        )
        assert req.presentation_currency == "GBP"

    def test_single_rate_request_short_currency_rejected(self):
        with pytest.raises(Exception):
            SingleRateRequest(
                from_currency="EU",  # too short
                to_currency="USD",
                rate="1.05",
            )
