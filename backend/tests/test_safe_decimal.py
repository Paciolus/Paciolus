"""
Monetary parsing in ``shared.parsing_helpers`` — every engine reads amounts
through these two functions.

Sprint 824 (from Sprint 823 discovery): "$(2,000.00)" parsed as +2,000 because
the parenthetical check ran before the "$" was stripped, and "Infinity" parsed
as a non-finite Decimal because the guard only knew "inf".
"""

import sys
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.parsing_helpers import safe_decimal, safe_float


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("$(2,000.00)", Decimal("-2000.00")),
        ("($2,000.00)", Decimal("-2000.00")),
        ("(2,000.00)", Decimal("-2000.00")),
        ("$ (2,000.00)", Decimal("-2000.00")),
        ("-$5", Decimal("-5")),
        ("$5-", Decimal("-5")),
        ("$1,234.56", Decimal("1234.56")),
        ("12.5", Decimal("12.5")),
    ],
)
def test_signs_and_currency_formats(raw, expected):
    assert safe_decimal(raw) == expected
    assert safe_float(raw) == float(expected)


@pytest.mark.parametrize("raw", ["Infinity", "-Infinity", "infinity", "inf", "NaN", "sNaN", "see note", ""])
def test_non_numeric_and_non_finite_fall_back_to_the_default(raw):
    assert safe_decimal(raw, default=None) is None
    assert safe_decimal(raw) == Decimal("0")
    assert safe_float(raw) == 0.0
