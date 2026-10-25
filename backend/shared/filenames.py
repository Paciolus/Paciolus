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


# A plain number — "-1,234.56", "+12", "-0.5%" — is not a formula and must stay
# numeric in the spreadsheet, so a negative amount is never turned into text.
_PLAIN_NUMBER = re.compile(r"^[+-]?(?:\d{1,3}(?:,\d{3})+|\d+)?(?:\.\d+)?%?$")


def _escape_cell(value: object) -> object:
    if isinstance(value, str) and value and not (_PLAIN_NUMBER.match(value) and any(c.isdigit() for c in value)):
        return sanitize_csv_value(value)
    return value


class SafeCsvWriter:
    """A ``csv.writer`` that formula-escapes every text cell (Sprint 840, S4).

    The claims review found six exports writing customer-supplied names —
    account, user, vendor, entity, lease and adjustment labels — straight into
    CSV with no escaping, while others escaped field by field. Escaping at the
    writer means a new column cannot forget it. Non-string cells (numbers,
    Decimals, None) pass through to ``csv`` unchanged, as do strings that are
    plain numbers. ``tests/test_csv_formula_guard.py`` fails the build if
    export code constructs a raw ``csv.writer``.
    """

    def __init__(self, stream: Any, **kwargs: Any) -> None:
        self._writer = csv.writer(stream, **kwargs)  # the one sanctioned raw writer

    def writerow(self, row: Iterable[object]) -> Any:
        return self._writer.writerow([_escape_cell(v) for v in row])

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
