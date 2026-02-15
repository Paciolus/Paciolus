"""
Tests for Currency Routes — Sprint 258
Sprint 262: Updated for DB-backed sessions (ToolSession).

Validates route registration, DB session storage, and response models.
"""

import pytest
import sys
from datetime import datetime, UTC, date
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from routes.currency import (
    get_user_rate_table,
    set_user_rate_table,
    clear_user_rate_table,
    RateTableUploadResponse,
    SingleRateResponse,
    RateTableStatusResponse,
    SingleRateRequest,
)
from currency_engine import CurrencyRateTable, ExchangeRate


# =============================================================================
# DB-Backed Session Storage (Sprint 262)
# =============================================================================

class TestSessionStorage:
    """Tests for DB-backed currency rate session storage."""

    def _make_table(self, currency="USD"):
        return CurrencyRateTable(
            rates=[ExchangeRate(date(2026, 1, 31), "EUR", "USD", Decimal("1.05"))],
            uploaded_at=datetime.now(UTC),
            presentation_currency=currency,
        )

    def test_set_and_get(self, db_session, make_user):
        user = make_user(email="curr_sess1@test.com")
        table = self._make_table()
        set_user_rate_table(db_session, user.id, table)
        result = get_user_rate_table(db_session, user.id)
        assert result is not None
        assert result.presentation_currency == "USD"
        assert len(result.rates) == 1

    def test_get_nonexistent_returns_none(self, db_session, make_user):
        user = make_user(email="curr_sess2@test.com")
        assert get_user_rate_table(db_session, user.id) is None

    def test_clear(self, db_session, make_user):
        user = make_user(email="curr_sess3@test.com")
        set_user_rate_table(db_session, user.id, self._make_table())
        assert clear_user_rate_table(db_session, user.id) is True
        assert get_user_rate_table(db_session, user.id) is None

    def test_clear_nonexistent(self, db_session, make_user):
        user = make_user(email="curr_sess4@test.com")
        assert clear_user_rate_table(db_session, user.id) is False

    def test_overwrite_existing(self, db_session, make_user):
        user = make_user(email="curr_sess5@test.com")
        set_user_rate_table(db_session, user.id, self._make_table("USD"))
        set_user_rate_table(db_session, user.id, self._make_table("EUR"))
        result = get_user_rate_table(db_session, user.id)
        assert result is not None
        assert result.presentation_currency == "EUR"

    def test_multiple_users(self, db_session, make_user):
        u1 = make_user(email="curr_multi1@test.com")
        u2 = make_user(email="curr_multi2@test.com")
        set_user_rate_table(db_session, u1.id, self._make_table("USD"))
        set_user_rate_table(db_session, u2.id, self._make_table("EUR"))
        assert get_user_rate_table(db_session, u1.id) is not None
        assert get_user_rate_table(db_session, u2.id) is not None
        assert get_user_rate_table(db_session, u1.id).presentation_currency == "USD"
        assert get_user_rate_table(db_session, u2.id).presentation_currency == "EUR"

    def test_rate_data_preserved(self, db_session, make_user):
        """Full round-trip: rate data (Decimal, date) survives JSON serialization."""
        user = make_user(email="curr_data@test.com")
        table = CurrencyRateTable(
            rates=[
                ExchangeRate(date(2026, 1, 31), "EUR", "USD", Decimal("1.0523")),
                ExchangeRate(date(2026, 1, 31), "GBP", "USD", Decimal("1.2650")),
                ExchangeRate(date(2026, 2, 1), "JPY", "USD", Decimal("0.0067")),
            ],
            uploaded_at=datetime(2026, 2, 15, 10, 0, 0, tzinfo=UTC),
            presentation_currency="USD",
        )
        set_user_rate_table(db_session, user.id, table)
        result = get_user_rate_table(db_session, user.id)
        assert len(result.rates) == 3
        assert result.rates[0].rate == Decimal("1.0523")
        assert result.rates[2].from_currency == "JPY"
        assert result.rates[0].effective_date == date(2026, 1, 31)


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
