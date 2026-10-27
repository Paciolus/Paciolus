"""Sprint 819 item 4: ``parse_date(..., formats=...)``.

AR's reference date and the currency rate table accept a deliberately narrow
set of date forms (their error messages name them). They now call the shared
parser with that set instead of hand-rolling ``strptime`` loops — and must not
start accepting the wider default set by accident.
"""

from datetime import date, datetime

import pytest

from currency_engine import RateValidationError, parse_rate_table
from services.audit.ar_aging.analysis import _compute_aging_days
from shared.parsing_helpers import DEFAULT_DATE_FORMATS, parse_date, parse_memo


class TestFormatsParameter:
    def test_default_unchanged(self):
        assert parse_date("31.12.2025") == date(2025, 12, 31)
        assert parse_date("20251231") == date(2025, 12, 31)
        assert DEFAULT_DATE_FORMATS[0] == "%Y-%m-%d"

    def test_restricted_set(self):
        assert parse_date("2025-12-31", formats=("%Y-%m-%d",)) == date(2025, 12, 31)
        assert parse_date("31.12.2025", formats=("%Y-%m-%d",)) is None
        assert parse_date("  2025-12-31 ", formats=("%Y-%m-%d",)) == date(2025, 12, 31)

    def test_order_is_respected(self):
        # Ambiguous 01/02/2025: the first listed form wins.
        assert parse_date("01/02/2025", formats=("%d/%m/%Y", "%m/%d/%Y")) == date(2025, 2, 1)
        assert parse_date("01/02/2025", formats=("%m/%d/%Y", "%d/%m/%Y")) == date(2025, 1, 2)

    def test_memo_is_keyed_by_formats(self):
        with parse_memo():
            assert parse_date("31.12.2025") == date(2025, 12, 31)
            assert parse_date("31.12.2025", formats=("%Y-%m-%d",)) is None
            assert parse_date("31.12.2025") == date(2025, 12, 31)

    def test_date_objects_pass_through(self):
        assert parse_date(datetime(2025, 12, 31, 8, 0), formats=("%Y-%m-%d",)) == date(2025, 12, 31)


class TestCallersKeepTheirNarrowSets:
    @pytest.mark.parametrize("ref", ["2025-12-31", "12/31/2025", "31/12/2025"])
    def test_ar_reference_date_accepted(self, ref):
        assert _compute_aging_days("2025-12-01", ref) == 30

    @pytest.mark.parametrize("ref", ["31.12.2025", "20251231", "Dec 31, 2025", "2025/12/31", "12-31-2025"])
    def test_ar_reference_date_still_rejected(self, ref):
        with pytest.raises(ValueError, match="not in a supported format"):
            _compute_aging_days("2025-12-01", ref)

    @pytest.mark.parametrize("raw", ["2025-12-31", "12/31/2025"])
    def test_rate_table_accepted(self, raw):
        rates = parse_rate_table([{"effective_date": raw, "from_currency": "EUR", "to_currency": "USD", "rate": "1.1"}])
        assert rates[0].effective_date == date(2025, 12, 31)

    @pytest.mark.parametrize(
        ("raw", "message"),
        [
            ("31/12/2025", "Invalid date '31/12/2025'"),
            ("12-31-2025", "Invalid date '12-31-2025'"),
            ("2025-12-31 00:00:00", "Invalid date '2025-12-31 00:00:00'"),
            ("12/31/25", "Invalid date '12/31/25'"),
            ("31.12.2025", "Invalid date format '31.12.2025'"),
        ],
    )
    def test_rate_table_still_rejected(self, raw, message):
        with pytest.raises(RateValidationError, match=message):
            parse_rate_table([{"effective_date": raw, "from_currency": "EUR", "to_currency": "USD", "rate": "1.1"}])
