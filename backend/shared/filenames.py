"""
File naming & CSV-cell sanitization utilities.

Centralizes the small helpers used across export pipelines and activity
logging so callers do not depend on the large upload-pipeline module.
"""

import csv
import hashlib
import re
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

# Characters that trigger formula execution in spreadsheet software (CWE-1236).
# Includes `|` per OWASP recommendation (LibreOffice Calc macro trigger).
_FORMULA_TRIGGERS = frozenset(("=", "+", "-", "@", "\t", "\r", "\n", "|"))


def escape_like_wildcards(term: str) -> str:
    """Escape SQL LIKE wildcards (``%``, ``_``, ``\\``) for literal matching.

    Paired with ``.ilike(pattern, escape="\\")`` so user input cannot trigger
    a full-table scan. A user searching for a literal ``%`` gets exactly that.
    """
    if not term:
        return ""
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def sanitize_csv_value(value: object) -> str:
    """Escape formula injection in CSV/Excel cell values (CWE-1236).

    Spreadsheet software interprets cells starting with =, +, -, @, tab, or CR
    as formulas. Prefixing with a single quote neutralizes this.
    """
    if value is None:
        return ""
    s = str(value)
    if s and s[0] in _FORMULA_TRIGGERS:
        return "'" + s
    return s


# A plain number — "-1,234.56", "+12", "-0.5%". Used only to validate text a
# caller says it formatted from a number (``number_cell``), and for the one
# untyped re-write of a client-supplied CSV (``untyped=True``).
_PLAIN_NUMBER = re.compile(r"^[+-]?(?:\d{1,3}(?:,\d{3})+|\d+)?(?:\.\d+)?%?$")


def _is_plain_number(text: str) -> bool:
    return bool(_PLAIN_NUMBER.match(text)) and any(c.isdigit() for c in text)


class NumberCell(str):
    """Text the caller formatted from a number, e.g. ``"-1,234.56"`` or ``"12.5%"``.

    Sprint 885 (review OUT-33): the safe CSV writer decides by what a column
    is, not by what its content looks like. A plain ``str`` is text and is
    always escaped, so an identifier such as ``"+00123"`` can no longer slip
    through as a number. A numeric column passes ints, floats or Decimals, or a
    ``NumberCell`` when it needs a fixed format. Build one with ``number_cell``.
    """

    __slots__ = ()


def number_cell(value: Any, spec: str = "", suffix: str = "") -> str:
    """``format(value, spec) + suffix`` marked as a number for the CSV writer.

    The text is exactly what ``f"{value:{spec}}{suffix}"`` gave before. If it is
    not a plain number (``"nan"``, ``"inf"``) it is returned as ordinary text,
    so the writer escapes it rather than trusting it.
    """
    text = format(value, spec) + suffix
    return NumberCell(text) if _is_plain_number(text) else text


def _escape_cell(value: object) -> object:
    if isinstance(value, NumberCell):
        return str(value)
    if isinstance(value, str) and value:
        return sanitize_csv_value(value)
    return value


def _escape_untyped_cell(value: object) -> object:
    if isinstance(value, str) and value and not _is_plain_number(value):
        return sanitize_csv_value(value)
    return value


class SafeCsvWriter:
    """A ``csv.writer`` that formula-escapes every text cell (Sprint 840, S4).

    The claims review found six exports writing customer-supplied names —
    account, user, vendor, entity, lease and adjustment labels — straight into
    CSV with no escaping, while others escaped field by field. Escaping at the
    writer means a new column cannot forget it. ``tests/test_csv_formula_guard.py``
    fails the build if export code constructs a raw ``csv.writer``.

    Sprint 885 (OUT-33): every ``str`` is text and is escaped, even when it
    looks like a number. Numbers, Decimals, ``NumberCell`` and None pass
    through unchanged. ``untyped=True`` is only for re-writing a CSV whose
    cells have lost their types (a client-supplied share): there a plain
    number is the best evidence available and is left bare.
    """

    def __init__(self, stream: Any, *, untyped: bool = False, **kwargs: Any) -> None:
        self._writer = csv.writer(stream, **kwargs)  # the one sanctioned raw writer
        self._escape = _escape_untyped_cell if untyped else _escape_cell

    def writerow(self, row: Iterable[object]) -> Any:
        return self._writer.writerow([self._escape(v) for v in row])

    def writerows(self, rows: Iterable[Iterable[object]]) -> None:
        for row in rows:
            self.writerow(row)

    @property
    def dialect(self) -> Any:
        return self._writer.dialect


def safe_csv_writer(stream: Any, **kwargs: Any) -> SafeCsvWriter:
    """Return a formula-escaping CSV writer — use this for every export."""
    return SafeCsvWriter(stream, **kwargs)


def hash_filename(filename: str) -> str:
    """SHA-256 hash of filename for privacy-preserving storage."""
    return hashlib.sha256(filename.encode("utf-8")).hexdigest()


def get_filename_display(filename: str, max_length: int = 12) -> str:
    """Truncated filename preview for display."""
    if len(filename) <= max_length:
        return filename
    return filename[: max_length - 3] + "..."


def safe_download_filename(raw_name: str, suffix: str, ext: str) -> str:
    """Generate sanitized timestamped download filename."""
    safe = "".join(c for c in raw_name if c.isalnum() or c in "._-")
    if not safe:
        safe = "Export"
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    return f"{safe}_{suffix}_{timestamp}.{ext}"
