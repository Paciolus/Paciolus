"""Exact amounts in Excel workbooks — Sprint 884 (TQ-12 / OUT-19).

Two things lost money digits on the way into a workbook:

1. Callers converted Decimals to float before writing a cell.
2. openpyxl itself writes every number with ``"%.16g"``, so even a Decimal
   cell was rounded to 16 significant digits in the file
   (Decimal("9007199254740993.01") was written as 9007199254740994).

``install_exact_decimal_writer()`` makes openpyxl write a Decimal cell with its
exact digits; floats and ints are written exactly as before. It is installed
when this module is imported.

Excel itself keeps 15 significant digits. When an amount has more, the number
Excel shows is approximate, so the workbook says so and keeps an exact text
copy beside it (``approximate_note``).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import openpyxl.cell._writer as _openpyxl_writer

from shared.monetary import ensure_supported_amount, excel_holds_exactly, quantize_monetary

APPROXIMATE_HEADER = "Exact amounts (where Excel's number is approximate)"

_original_safe_string = _openpyxl_writer.safe_string


def _exact_safe_string(value: Any) -> str:
    if isinstance(value, Decimal) and value.is_finite():
        return format(value, "f")
    return str(_original_safe_string(value))


def install_exact_decimal_writer() -> None:
    """Write Decimal cells with their exact digits (idempotent)."""
    _openpyxl_writer.safe_string = _exact_safe_string  # type: ignore[assignment]


install_exact_decimal_writer()


def money(value: Any) -> Decimal | None:
    """A cell value for an amount: a Decimal at cents, half-up; None stays None."""
    if value is None or value == "":
        return None
    return ensure_supported_amount(quantize_monetary(value))


def approximate_note(items: list[tuple[str, Any]]) -> str | None:
    """Text for the cell beside a row whose amounts Excel cannot hold exactly.

    ``items`` are (label, amount) pairs for the row; returns None when Excel
    holds every one of them exactly.
    """
    inexact = [(label, Decimal(value)) for label, value in items if value is not None and value != ""]
    inexact = [(label, value) for label, value in inexact if not excel_holds_exactly(value)]
    if not inexact:
        return None
    exact = "; ".join(f"{label} {value:,}" for label, value in inexact)
    return f"Exact: {exact}. Excel holds 15 significant digits, so the number shown is approximate."
