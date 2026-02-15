"""
Tests for Currency Conversion Engine — Sprint 257

Covers: rate table parsing, validation, rate lookup, currency detection,
TB conversion, unconverted item flagging, edge cases.
"""

import pytest
from datetime import date, datetime, UTC
from decimal import Decimal

from currency_engine import (
    validate_currency_code,
    parse_rate_table,
    parse_single_rate,
    find_rate,
    detect_currency_column,
    detect_currencies_in_tb,
    convert_trial_balance,
    ExchangeRate,
    CurrencyRateTable,
    ConversionFlag,
    ConversionResult,
    RateValidationError,
    _build_rate_lookup,
    _find_best_rate,
    _recalculate_flag_severity,
    MAX_RATE_TABLE_ROWS,
    STALE_RATE_DAYS,
)
import pandas as pd


# =============================================================================
# Currency Code Validation
# =============================================================================

class TestValidateCurrencyCode:
    def test_valid_code(self):
        assert validate_currency_code("USD") == "USD"

    def test_lowercase_normalized(self):
        assert validate_currency_code("usd") == "USD"

    def test_whitespace_stripped(self):
        assert validate_currency_code("  EUR  ") == "EUR"

    def test_invalid_length(self):
        with pytest.raises(RateValidationError, match="3 uppercase letters"):
            validate_currency_code("US")

    def test_invalid_code_not_iso(self):
        with pytest.raises(RateValidationError, match="not a recognized ISO 4217"):
            validate_currency_code("XYZ")

    def test_numeric_code_rejected(self):
        with pytest.raises(RateValidationError, match="3 uppercase letters"):
            validate_currency_code("123")


# =============================================================================
# Rate Table Parsing
# =============================================================================

class TestParseRateTable:
    def test_valid_table(self):
        rows = [
            {"effective_date": "2026-01-31", "from_currency": "EUR", "to_currency": "USD", "rate": "1.0523"},
            {"effective_date": "2026-01-31", "from_currency": "GBP", "to_currency": "USD", "rate": "1.2634"},
        ]
        rates = parse_rate_table(rows)
        assert len(rates) == 2
        assert rates[0].from_currency == "EUR"
        assert rates[0].to_currency == "USD"
        assert rates[0].rate == Decimal("1.0523")
        assert rates[0].effective_date == date(2026, 1, 31)

    def test_us_date_format(self):
        rows = [
            {"effective_date": "01/31/2026", "from_currency": "EUR", "to_currency": "USD", "rate": "1.05"},
        ]
        rates = parse_rate_table(rows)
        assert rates[0].effective_date == date(2026, 1, 31)

    def test_empty_table_rejected(self):
        with pytest.raises(RateValidationError, match="empty"):
            parse_rate_table([])

    def test_missing_columns(self):
        rows = [{"date": "2026-01-31", "currency": "EUR"}]
        with pytest.raises(RateValidationError, match="missing required columns"):
            parse_rate_table(rows)

    def test_negative_rate_rejected(self):
        rows = [
            {"effective_date": "2026-01-31", "from_currency": "EUR", "to_currency": "USD", "rate": "-1.05"},
        ]
        with pytest.raises(RateValidationError, match="positive"):
            parse_rate_table(rows)

    def test_zero_rate_rejected(self):
        rows = [
            {"effective_date": "2026-01-31", "from_currency": "EUR", "to_currency": "USD", "rate": "0"},
        ]
        with pytest.raises(RateValidationError, match="positive"):
            parse_rate_table(rows)

    def test_same_currency_rejected(self):
        rows = [
            {"effective_date": "2026-01-31", "from_currency": "USD", "to_currency": "USD", "rate": "1.0"},
        ]
        with pytest.raises(RateValidationError, match="same"):
            parse_rate_table(rows)

    def test_duplicate_pair_rejected(self):
        rows = [
            {"effective_date": "2026-01-31", "from_currency": "EUR", "to_currency": "USD", "rate": "1.05"},
            {"effective_date": "2026-01-31", "from_currency": "EUR", "to_currency": "USD", "rate": "1.06"},
        ]
        with pytest.raises(RateValidationError, match="Duplicate"):
            parse_rate_table(rows)

    def test_invalid_date_format(self):
        rows = [
            {"effective_date": "Jan 31 2026", "from_currency": "EUR", "to_currency": "USD", "rate": "1.05"},
        ]
        with pytest.raises(RateValidationError, match="Invalid date"):
            parse_rate_table(rows)

    def test_max_rows_exceeded(self):
        rows = [
            {"effective_date": f"2026-01-{str(i % 28 + 1).zfill(2)}", "from_currency": "EUR", "to_currency": "USD", "rate": "1.05"}
            for i in range(MAX_RATE_TABLE_ROWS + 1)
        ]
        with pytest.raises(RateValidationError, match="exceeds maximum"):
            parse_rate_table(rows)

    def test_case_insensitive_column_names(self):
        rows = [
            {"Effective_Date": "2026-01-31", "FROM_CURRENCY": "EUR", "To_Currency": "USD", "RATE": "1.05"},
        ]
        rates = parse_rate_table(rows)
        assert len(rates) == 1

    def test_invalid_rate_value(self):
        rows = [
            {"effective_date": "2026-01-31", "from_currency": "EUR", "to_currency": "USD", "rate": "abc"},
        ]
        with pytest.raises(RateValidationError, match="Invalid rate"):
            parse_rate_table(rows)


# =============================================================================
# Single Rate Parsing
# =============================================================================

class TestParseSingleRate:
    def test_valid_single_rate(self):
        rate = parse_single_rate("EUR", "USD", "1.0523")
        assert rate.from_currency == "EUR"
        assert rate.to_currency == "USD"
        assert rate.rate == Decimal("1.0523")
        assert rate.effective_date == date.today()

    def test_same_currency_rejected(self):
        with pytest.raises(RateValidationError, match="cannot be the same"):
            parse_single_rate("USD", "USD", "1.0")

    def test_negative_rate_rejected(self):
        with pytest.raises(RateValidationError, match="positive"):
            parse_single_rate("EUR", "USD", "-1.0")

    def test_invalid_rate(self):
        with pytest.raises(RateValidationError, match="Invalid rate"):
            parse_single_rate("EUR", "USD", "not-a-number")


# =============================================================================
# Rate Lookup
# =============================================================================

class TestFindRate:
    def _make_lookup(self, rates: list[ExchangeRate]):
        return _build_rate_lookup(rates)

    def test_exact_match(self):
        rates = [ExchangeRate(date(2026, 1, 31), "EUR", "USD", Decimal("1.05"))]
        lookup = self._make_lookup(rates)
        rate, issue = find_rate(lookup, "EUR", "USD", date(2026, 1, 31))
        assert rate == Decimal("1.05")
        assert issue is None

    def test_same_currency_returns_one(self):
        rate, issue = find_rate({}, "USD", "USD")
        assert rate == Decimal("1")
        assert issue is None

    def test_missing_rate(self):
        rate, issue = find_rate({}, "EUR", "USD")
        assert rate is None
        assert issue == "missing_rate"

    def test_nearest_prior_date_fallback(self):
        rates = [
            ExchangeRate(date(2026, 1, 15), "EUR", "USD", Decimal("1.04")),
            ExchangeRate(date(2026, 1, 31), "EUR", "USD", Decimal("1.05")),
        ]
        lookup = self._make_lookup(rates)
        # Query for Jan 20 — should get Jan 15 rate (nearest prior)
        rate, issue = find_rate(lookup, "EUR", "USD", date(2026, 1, 20))
        assert rate == Decimal("1.04")
        assert issue is None

    def test_stale_rate_flagged(self):
        rates = [ExchangeRate(date(2025, 6, 1), "EUR", "USD", Decimal("1.05"))]
        lookup = self._make_lookup(rates)
        rate, issue = find_rate(lookup, "EUR", "USD", date(2026, 1, 31))
        assert rate == Decimal("1.05")
        assert issue == "stale_rate"

    def test_inverse_rate_used(self):
        """If EUR/USD is not available but USD/EUR is, compute inverse."""
        rates = [ExchangeRate(date(2026, 1, 31), "USD", "EUR", Decimal("0.95"))]
        lookup = self._make_lookup(rates)
        rate, issue = find_rate(lookup, "EUR", "USD", date(2026, 1, 31))
        assert rate is not None
        # 1 / 0.95 ≈ 1.0526
        assert abs(rate - Decimal("1.0526")) < Decimal("0.001")
        assert issue is None

    def test_no_target_date_uses_latest(self):
        rates = [
            ExchangeRate(date(2026, 1, 15), "EUR", "USD", Decimal("1.04")),
            ExchangeRate(date(2026, 1, 31), "EUR", "USD", Decimal("1.05")),
        ]
        lookup = self._make_lookup(rates)
        rate, issue = find_rate(lookup, "EUR", "USD")
        assert rate == Decimal("1.05")  # Latest rate


# =============================================================================
# Currency Column Detection
# =============================================================================

class TestDetectCurrencyColumn:
    def test_detects_currency_column(self):
        cols = ["Account Number", "Account Name", "Currency", "Amount"]
        result = detect_currency_column(cols)
        assert result == "Currency"

    def test_detects_ccy(self):
        cols = ["Account", "CCY", "Debit", "Credit"]
        result = detect_currency_column(cols)
        assert result == "CCY"

    def test_no_currency_column(self):
        cols = ["Account Number", "Account Name", "Debit", "Credit"]
        result = detect_currency_column(cols)
        assert result is None

    def test_detects_currency_code(self):
        cols = ["Account", "Currency Code", "Amount"]
        result = detect_currency_column(cols)
        assert result == "Currency Code"


class TestDetectCurrenciesInTb:
    def test_finds_currencies(self):
        df = pd.DataFrame({"Currency": ["USD", "EUR", "usd", "GBP", None]})
        result = detect_currencies_in_tb(df, "Currency")
        assert result == ["EUR", "GBP", "USD"]

    def test_missing_column_returns_empty(self):
        df = pd.DataFrame({"Amount": [100, 200]})
        result = detect_currencies_in_tb(df, "Currency")
        assert result == []


# =============================================================================
# TB Conversion
# =============================================================================

class TestConvertTrialBalance:
    def _make_rate_table(self, rates=None, currency="USD"):
        return CurrencyRateTable(
            rates=rates or [],
            uploaded_at=datetime.now(UTC),
            presentation_currency=currency,
        )

    def test_empty_tb(self):
        result = convert_trial_balance([], self._make_rate_table(), "Amount")
        assert result.conversion_performed is False
        assert result.total_accounts == 0

    def test_no_currency_column_passes_through(self):
        rows = [
            {"Account": "1000", "Amount": 100},
            {"Account": "2000", "Amount": 200},
        ]
        result = convert_trial_balance(rows, self._make_rate_table(), "Amount")
        assert result.conversion_performed is False
        assert result.total_accounts == 2
        assert result.converted_count == 2
        assert result.conversion_summary.startswith("No currency column detected")

    def test_single_currency_no_conversion_needed(self):
        rates = [ExchangeRate(date(2026, 1, 31), "EUR", "USD", Decimal("1.05"))]
        rate_table = self._make_rate_table(rates, "USD")
        rows = [
            {"Account": "1000", "Name": "Cash", "Currency": "USD", "Amount": 1000},
            {"Account": "2000", "Name": "AR", "Currency": "USD", "Amount": 2000},
        ]
        result = convert_trial_balance(
            rows, rate_table, "Amount",
            currency_column="Currency",
            account_number_column="Account",
            account_name_column="Name",
        )
        assert result.conversion_performed is True
        assert result.converted_count == 2
        assert result.unconverted_count == 0

    def test_multi_currency_conversion(self):
        rates = [ExchangeRate(date(2026, 1, 31), "EUR", "USD", Decimal("1.05"))]
        rate_table = self._make_rate_table(rates, "USD")
        rows = [
            {"Account": "1000", "Name": "Cash", "Currency": "USD", "Amount": 1000},
            {"Account": "1100", "Name": "AR EUR", "Currency": "EUR", "Amount": 500},
        ]
        result = convert_trial_balance(
            rows, rate_table, "Amount",
            currency_column="Currency",
            account_number_column="Account",
            account_name_column="Name",
        )
        assert result.conversion_performed is True
        assert result.converted_count == 2
        assert result.unconverted_count == 0
        assert "EUR/USD" in result.rates_applied

        # Check converted amounts
        usd_row = result.converted_rows[0]
        eur_row = result.converted_rows[1]
        assert usd_row["converted_amount_usd"] == 1000.0  # 1:1
        assert eur_row["converted_amount_usd"] == 525.0  # 500 * 1.05

    def test_missing_rate_flagged(self):
        rate_table = self._make_rate_table([], "USD")  # No rates at all
        rows = [
            {"Account": "1000", "Name": "Cash JPY", "Currency": "JPY", "Amount": 100000},
        ]
        result = convert_trial_balance(
            rows, rate_table, "Amount",
            currency_column="Currency",
            account_number_column="Account",
            account_name_column="Name",
        )
        assert result.unconverted_count == 1
        assert len(result.unconverted_items) == 1
        assert result.unconverted_items[0].issue == "missing_rate"

    def test_missing_currency_code_flagged(self):
        rate_table = self._make_rate_table([], "USD")
        rows = [
            {"Account": "1000", "Name": "Cash", "Currency": "", "Amount": 500},
        ]
        result = convert_trial_balance(
            rows, rate_table, "Amount",
            currency_column="Currency",
            account_number_column="Account",
            account_name_column="Name",
        )
        assert result.unconverted_count == 1
        assert result.unconverted_items[0].issue == "missing_currency_code"

    def test_currencies_found_populated(self):
        rates = [
            ExchangeRate(date(2026, 1, 31), "EUR", "USD", Decimal("1.05")),
            ExchangeRate(date(2026, 1, 31), "GBP", "USD", Decimal("1.26")),
        ]
        rate_table = self._make_rate_table(rates, "USD")
        rows = [
            {"Account": "1000", "Currency": "USD", "Amount": 100},
            {"Account": "1100", "Currency": "EUR", "Amount": 200},
            {"Account": "1200", "Currency": "GBP", "Amount": 300},
        ]
        result = convert_trial_balance(
            rows, rate_table, "Amount",
            currency_column="Currency",
        )
        assert sorted(result.currencies_found) == ["EUR", "GBP", "USD"]

    def test_conversion_result_to_dict(self):
        result = ConversionResult(
            conversion_performed=True,
            presentation_currency="USD",
            total_accounts=10,
            converted_count=8,
            unconverted_count=2,
        )
        d = result.to_dict()
        assert d["conversion_performed"] is True
        assert d["total_accounts"] == 10

    def test_zero_amount_with_missing_currency_not_flagged(self):
        """Zero-amount rows with missing currency should not generate flags."""
        rate_table = self._make_rate_table([], "USD")
        rows = [
            {"Account": "1000", "Name": "Closed", "Currency": "", "Amount": 0},
        ]
        result = convert_trial_balance(
            rows, rate_table, "Amount",
            currency_column="Currency",
            account_number_column="Account",
            account_name_column="Name",
        )
        assert result.unconverted_count == 0
        assert len(result.unconverted_items) == 0

    def test_auto_detect_currency_column(self):
        """Currency column detection should work when not explicitly provided."""
        rates = [ExchangeRate(date(2026, 1, 31), "EUR", "USD", Decimal("1.05"))]
        rate_table = self._make_rate_table(rates, "USD")
        rows = [
            {"Account Number": "1000", "Account Name": "Cash", "Currency": "EUR", "Amount": 100},
        ]
        result = convert_trial_balance(rows, rate_table, "Amount")
        assert result.conversion_performed is True
        assert result.converted_count == 1


# =============================================================================
# Edge Cases
# =============================================================================

class TestEdgeCases:
    def _make_rate_table(self, rates=None, currency="USD"):
        return CurrencyRateTable(
            rates=rates or [],
            uploaded_at=datetime.now(UTC),
            presentation_currency=currency,
        )

    def test_large_amount_precision(self):
        """Large amounts should maintain precision."""
        rates = [ExchangeRate(date(2026, 1, 31), "EUR", "USD", Decimal("1.05234"))]
        rate_table = self._make_rate_table(rates, "USD")
        rows = [
            {"Account": "1000", "Currency": "EUR", "Amount": 9999999.99},
        ]
        result = convert_trial_balance(
            rows, rate_table, "Amount",
            currency_column="Currency",
        )
        assert result.converted_count == 1
        converted = result.converted_rows[0]["converted_amount_usd"]
        assert converted is not None
        # 9999999.99 * 1.05234 ≈ 10523399.9895
        assert abs(converted - 10523399.9895) < 0.01

    def test_none_amount_treated_as_zero(self):
        rates = [ExchangeRate(date(2026, 1, 31), "EUR", "USD", Decimal("1.05"))]
        rate_table = self._make_rate_table(rates, "USD")
        rows = [
            {"Account": "1000", "Currency": "EUR", "Amount": None},
        ]
        result = convert_trial_balance(
            rows, rate_table, "Amount",
            currency_column="Currency",
        )
        assert result.converted_count == 1
        assert result.converted_rows[0]["converted_amount_usd"] == 0.0

    def test_negative_amount_converted(self):
        """Negative amounts (credits) should be converted correctly."""
        rates = [ExchangeRate(date(2026, 1, 31), "EUR", "USD", Decimal("1.05"))]
        rate_table = self._make_rate_table(rates, "USD")
        rows = [
            {"Account": "3000", "Currency": "EUR", "Amount": -1000},
        ]
        result = convert_trial_balance(
            rows, rate_table, "Amount",
            currency_column="Currency",
        )
        assert result.converted_count == 1
        assert result.converted_rows[0]["converted_amount_usd"] == -1050.0

    def test_exchange_rate_to_dict(self):
        rate = ExchangeRate(date(2026, 1, 31), "EUR", "USD", Decimal("1.05"))
        d = rate.to_dict()
        assert d["effective_date"] == "2026-01-31"
        assert d["rate"] == "1.05"

    def test_conversion_flag_to_dict(self):
        flag = ConversionFlag("1000", "Cash", 500.0, "JPY", "missing_rate", "high")
        d = flag.to_dict()
        assert d["account_number"] == "1000"
        assert d["issue"] == "missing_rate"
        assert d["severity"] == "high"

    def test_rate_table_to_dict(self):
        rate_table = CurrencyRateTable(
            rates=[ExchangeRate(date(2026, 1, 31), "EUR", "USD", Decimal("1.05"))],
            uploaded_at=datetime(2026, 2, 15, 10, 0, 0, tzinfo=UTC),
            presentation_currency="USD",
        )
        d = rate_table.to_dict()
        assert d["rate_count"] == 1
        assert d["presentation_currency"] == "USD"
        assert "EUR/USD" in d["currency_pairs"]

    def test_partial_conversion_summary(self):
        """When some accounts can't be converted, summary reflects this."""
        rates = [ExchangeRate(date(2026, 1, 31), "EUR", "USD", Decimal("1.05"))]
        rate_table = self._make_rate_table(rates, "USD")
        rows = [
            {"Account": "1000", "Currency": "EUR", "Amount": 100},
            {"Account": "2000", "Currency": "JPY", "Amount": 200},
        ]
        result = convert_trial_balance(
            rows, rate_table, "Amount",
            currency_column="Currency",
        )
        assert result.converted_count == 1
        assert result.unconverted_count == 1
        assert "could not be converted" in result.conversion_summary


# =============================================================================
# Severity Recalculation
# =============================================================================

class TestSeverityRecalculation:
    def test_high_severity_for_large_amount(self):
        """Account > 5% of total should be high severity."""
        df = pd.DataFrame({"Amount": [100, 200, 300, 400]})
        flags = [
            ConversionFlag("1000", "Cash", 200.0, "JPY", "missing_rate", "medium"),
        ]
        _recalculate_flag_severity(flags, df, "Amount")
        # 200 / 1000 = 20% > 5%
        assert flags[0].severity == "high"

    def test_low_severity_for_small_amount(self):
        """Account < 1% of total should be low severity."""
        df = pd.DataFrame({"Amount": [10000, 20000, 30000]})
        flags = [
            ConversionFlag("1000", "Petty", 5.0, "JPY", "missing_rate", "medium"),
        ]
        _recalculate_flag_severity(flags, df, "Amount")
        # 5 / 60000 = 0.008% < 1%
        assert flags[0].severity == "low"

    def test_stale_rate_severity_not_recalculated(self):
        """Stale rate flags keep their original severity."""
        df = pd.DataFrame({"Amount": [100]})
        flags = [
            ConversionFlag("1000", "Cash", 100.0, "EUR", "stale_rate", "low"),
        ]
        _recalculate_flag_severity(flags, df, "Amount")
        assert flags[0].severity == "low"
