"""One typed writer for every Excel cell — Sprint 885 (review OUT-02).

openpyxl decides a cell's type from its value: any string that starts with
"=" becomes a formula. The workpaper wrote ``workpaper_date`` — an
unrestricted string — straight into a cell, so "=1+1" was saved as a live
formula, and other generators relied on each caller remembering to escape.

Here the *Python type* decides, never the content:

- ``str`` is written as text (``t="s"``), never a formula. Text that starts
  with a formula trigger also gets Excel's ``quotePrefix`` style, the same
  invisible mark Excel sets when a user types ``'=1+1``, so the cell stays
  text if someone edits it. The text itself is unchanged — no visible ``'``.
- ``int``, ``float`` and ``Decimal`` are numbers (non-finite values refused).
- ``date`` / ``datetime`` are dates.
- ``bool`` and ``None`` as openpyxl writes them.

Anything else is a ``TypeError``: a caller must convert on purpose.

``tests/test_sprint885_excel_typed_cells.py`` fails the build if an Excel
generator writes a cell any other way.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE, Cell
from openpyxl.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet

_FORMULA_TRIGGERS = ("=", "+", "-", "@", "\t", "\r", "\n", "|")
_DATE_FORMAT = "yyyy-mm-dd"


def _set(cell: Cell, value: Any) -> Cell:
    if value is None or isinstance(value, bool):
        cell.value = value
    elif isinstance(value, str):
        # Characters XML cannot carry would make openpyxl raise; show them as U+FFFD.
        text = ILLEGAL_CHARACTERS_RE.sub("�", value)
        cell.value = text
        cell.data_type = "s"  # never "f" (formula) or "e" (error), whatever the text says
        if text.startswith(_FORMULA_TRIGGERS):
            cell.quotePrefix = True
    elif isinstance(value, (int, Decimal)):
        if isinstance(value, Decimal) and not value.is_finite():
            raise ValueError(f"not a finite number: {value!r}")
        cell.value = value
    elif isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"not a finite number: {value!r}")
        cell.value = value
    elif isinstance(value, (date, datetime)):
        cell.value = value
        if cell.number_format == "General":
            cell.number_format = _DATE_FORMAT
    else:
        raise TypeError(f"Excel cell value must be str, number, date, bool or None, not {type(value).__name__}")
    return cell


def put(ws: Worksheet, row: int, column: int, value: Any) -> Cell:
    """Write ``value`` to (row, column) by its type and return the cell."""
    return _set(ws.cell(row=row, column=column), value)


def put_ref(ws: Worksheet, ref: str, value: Any) -> Cell:
    """Write ``value`` to a cell named like ``"A1"`` and return the cell."""
    return _set(ws[ref], value)


def append_row(ws: Worksheet, values: Iterable[Any]) -> int:
    """Write ``values`` to the next empty row (like ``ws.append``); return the row number."""
    # The same row ``ws.append`` would choose (openpyxl tracks it as _current_row).
    row: int = int(ws._current_row) + 1
    for col, value in enumerate(values, start=1):
        put(ws, row, col, value)
    return row


def as_date(value: Any) -> date | None:
    """A workpaper date: a ``date``, an ISO ``YYYY-MM-DD`` string, or None. Anything else is a ValueError."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value.strip()) if len(value.strip()) == 10 else _bad_date(value)
    return _bad_date(value)


def _bad_date(value: Any) -> date:
    raise ValueError(f"workpaper date must be YYYY-MM-DD, got {value!r}")


def assert_no_formulas(wb: Workbook) -> None:
    """Second layer: refuse to save a workbook holding any formula cell."""
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for cell in row:
                if cell.data_type == "f":
                    raise ValueError(f"formula cell {ws.title}!{cell.coordinate} in an export workbook")
