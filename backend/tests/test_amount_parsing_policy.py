"""Sprint 883 (review ST-01): one amount-parsing policy for every path.

The testing engines (``safe_decimal``), preflight's balance check, the intake
totals-row detector and the trial balance's pandas ingestion each parsed
amounts their own way, so the same cell could be -2000 in one place and 0 in
another — and preflight sums its values into the balance check. Every path
must now read a cell the same way.

Decided (CEO, 2026-11-18): "$(2,000.00)" is -2000, "1,234.56-" is -1234.56,
"€1,234.56" is 1234.56, and "Infinity" / "NaN" are invalid, never numbers.
"""

from __future__ import annotations

from decimal import Decimal

import pandas as pd
import pytest

from audit.ingestion import check_balance
from audit.streaming_auditor import StreamingAuditor
from preflight_engine import run_preflight
from security_utils import _strip_currency_formatting
from shared.intake_utils import detect_totals_row
from shared.parsing_helpers import InvalidAmountError, parse_amount, safe_decimal

# (cell, value every path must read). Invalid cells read as 0 in the default
# "invalid means zero" mode.
AMOUNT_TABLE: list[tuple[object, Decimal]] = [
    # plain numbers and negatives
    ("2000", Decimal("2000")),
    ("-2000", Decimal("-2000")),
    ("+2000", Decimal("2000")),
    (" 100 ", Decimal("100")),
    ("1,234.56", Decimal("1234.56")),
    (".5", Decimal("0.5")),
    ("1e3", Decimal("1000")),
    # parentheses
    ("(2,000.00)", Decimal("-2000")),
    ("$(2,000.00)", Decimal("-2000")),
    ("($2,000.00)", Decimal("-2000")),
    # trailing minus
    ("1,234.56-", Decimal("-1234.56")),
    ("$1,234.56-", Decimal("-1234.56")),
    # currency symbols, with leading signs either side of the symbol
    ("$1,234.56", Decimal("1234.56")),
    ("€1,234.56", Decimal("1234.56")),
    ("£1,234.56", Decimal("1234.56")),
    ("-$2,000.00", Decimal("-2000")),
    ("$-2,000.00", Decimal("-2000")),
    # accounting-format zero
    ("-", Decimal("0")),
    # blanks
    ("", Decimal("0")),
    ("   ", Decimal("0")),
    (None, Decimal("0")),
    # non-finite values are invalid, never numbers
    ("Infinity", Decimal("0")),
    ("-Infinity", Decimal("0")),
    ("inf", Decimal("0")),
    ("NaN", Decimal("0")),
    ("sNaN", Decimal("0")),
    (float("inf"), Decimal("0")),
    (Decimal("Infinity"), Decimal("0")),
    (Decimal("NaN"), Decimal("0")),
    # other invalid text
    ("abc", Decimal("0")),
    ("12abc", Decimal("0")),
    # native numbers
    (1500, Decimal("1500")),
    (1234.5, Decimal("1234.5")),
    (Decimal("-7.25"), Decimal("-7.25")),
]

_IDS = [repr(cell) for cell, _ in AMOUNT_TABLE]


def _via_preflight(cell: object) -> Decimal:
    report = run_preflight(["Account", "Debit", "Credit"], [{"Account": "Cash", "Debit": cell, "Credit": ""}], "t.csv")
    assert report.balance_check is not None
    return Decimal(str(report.balance_check.total_debits))


def _via_streaming(cell: object) -> Decimal:
    auditor = StreamingAuditor()
    auditor.process_chunk(pd.DataFrame({"Account": ["Cash"], "Debit": [cell], "Credit": [""]}, dtype=object), 1)
    return Decimal(auditor.get_balance_result()["total_debits"])


def _via_legacy_check_balance(cell: object) -> Decimal:
    result = check_balance(pd.DataFrame({"Account": ["Cash"], "Debit": [cell], "Credit": [""]}, dtype=object))
    return Decimal(result["total_debits"])


def _intake_reads_nonzero(cell: object) -> bool:
    """The totals detector needs a non-zero debit; it reads the cell with the policy."""
    rows = [
        {"Account": "Cash", "Debit": "1", "Credit": ""},
        {"Account": "", "Debit": cell, "Credit": "1"},
    ]
    return detect_totals_row(rows, ["Account", "Debit", "Credit"], "Debit", "Credit") is not None


@pytest.mark.parametrize(("cell", "expected"), AMOUNT_TABLE, ids=_IDS)
class TestEveryPathReadsTheSameValue:
    def test_policy(self, cell, expected):
        assert parse_amount(cell) == expected

    def test_testing_engines_safe_decimal(self, cell, expected):
        assert safe_decimal(cell) == expected

    def test_preflight_balance_check(self, cell, expected):
        assert _via_preflight(cell) == expected

    def test_intake_totals_detector(self, cell, expected):
        assert _intake_reads_nonzero(cell) == (expected != 0)

    def test_streaming_trial_balance(self, cell, expected):
        assert _via_streaming(cell) == expected

    def test_legacy_check_balance(self, cell, expected):
        assert _via_legacy_check_balance(cell) == expected

    def test_pdf_docx_prepass_does_not_change_the_value(self, cell, expected):
        # The PDF/DOCX dispatch strips formatting from every cell before
        # analysis; whatever it produces must still read as the same amount.
        assert parse_amount(_strip_currency_formatting(cell)) == expected


class TestInvalidIsAnErrorOption:
    @pytest.mark.parametrize(
        "cell", ["Infinity", "-Infinity", "NaN", "abc", "12abc", float("inf"), Decimal("NaN"), Decimal("Infinity")]
    )
    def test_invalid_raises(self, cell):
        with pytest.raises(InvalidAmountError):
            parse_amount(cell, on_invalid="error")

    @pytest.mark.parametrize("cell", ["", "   ", None, float("nan"), "-"])
    def test_blank_is_zero_not_an_error(self, cell):
        assert parse_amount(cell, on_invalid="error") == Decimal("0")

    def test_valid_value_returned(self):
        assert parse_amount("$(2,000.00)", on_invalid="error") == Decimal("-2000")

    def test_safe_decimal_default_applies_to_blank_and_invalid(self):
        assert safe_decimal("Infinity", default=None) is None
        assert safe_decimal("", default=None) is None
        assert safe_decimal("1,234.56-", default=None) == Decimal("-1234.56")


class TestPreflightAndStreamingAgreeOnAFile:
    """The review's case: one file, every format, one balance result."""

    CELLS = [
        ("Cash", "$(2,000.00)", ""),
        ("AR", "1,234.56-", ""),
        ("Revenue", "", "€1,234.56"),
        ("Other", "Infinity", ""),
    ]

    def test_same_totals(self):
        rows = [{"Account": a, "Debit": d, "Credit": c} for a, d, c in self.CELLS]
        pre = run_preflight(["Account", "Debit", "Credit"], rows, "t.csv").balance_check
        auditor = StreamingAuditor()
        auditor.process_chunk(pd.DataFrame(rows, dtype=object), len(rows))
        stream = auditor.get_balance_result()
        assert pre is not None
        assert Decimal(str(pre.total_debits)) == Decimal(stream["total_debits"]) == Decimal("-3234.56")
        assert Decimal(str(pre.total_credits)) == Decimal(stream["total_credits"]) == Decimal("1234.56")
