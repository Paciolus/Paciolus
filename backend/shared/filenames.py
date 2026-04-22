"""
File naming & CSV-cell sanitization utilities.

Centralizes the small helpers used across export pipelines and activity
logging so callers do not depend on the large upload-pipeline module.
"""

import hashlib
from datetime import UTC, datetime

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
