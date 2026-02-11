"""
Shared data-parsing helpers for Paciolus testing engines.

Sprint 136: Extracted from 9 engine files where these functions were
duplicated verbatim.  The canonical implementation is the superset of
all variants (standard + ar_aging isinstance fast-path +
three_way_match/bank_rec parenthetical-negative handling).
"""

import math
import re
from datetime import date, datetime
from typing import Optional


def safe_float(value) -> float:
    """Convert *value* to float, returning ``0.0`` for non-numeric.

    Handles:
    - ``None`` → 0.0
    - ``int`` / ``float`` (with NaN/Inf guard)
    - Currency strings: ``$1,234.56``, ``(1,234.56)`` (parenthetical negatives)
    - Trailing-negative: ``1234-``
    - Percent: ``45.2%``
    """
    if value is None:
        return 0.0

    # Fast path for numeric types (from ar_aging variant)
    if isinstance(value, (int, float)):
        f = float(value)
        if math.isnan(f) or math.isinf(f):
            return 0.0
        return f

    # Try direct conversion first
    try:
        f = float(value)
        if math.isnan(f) or math.isinf(f):
            return 0.0
        return f
    except (ValueError, TypeError):
        pass

    # String cleaning (handles currency, parentheses, trailing negatives)
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return 0.0
        # Detect accounting-style parenthetical negatives: (1,234.56)
        is_negative = s.startswith("(") and s.endswith(")")
        cleaned = re.sub(r"[,$\s()%]", "", s)
        if cleaned.startswith("-") or cleaned.endswith("-"):
            cleaned = "-" + cleaned.strip("-")
            is_negative = True
        elif is_negative and not cleaned.startswith("-"):
            cleaned = "-" + cleaned
        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return 0.0

    return 0.0


def safe_str(value) -> Optional[str]:
    """Convert *value* to stripped string, returning ``None`` for empty/NaN."""
    if value is None:
        return None
    s = str(value).strip()
    if s == "" or s.lower() == "nan" or s.lower() == "none":
        return None
    return s


def safe_int(value) -> Optional[int]:
    """Convert *value* to int, returning ``None`` on failure.

    Useful for aging-day counts, row IDs, and similar integer fields.
    """
    if value is None:
        return None
    if isinstance(value, int):
        return value
    try:
        return int(float(str(value).strip()))
    except (ValueError, TypeError):
        return None


def parse_date(date_str: Optional[str]) -> Optional[date]:
    """Try to parse a date string into a :class:`date` object.

    Supports ISO, US, EU, and datetime formats.
    """
    if not date_str:
        return None
    for fmt in (
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%m-%d-%Y",
        "%d-%m-%Y",
        "%Y-%m-%d %H:%M:%S",
        "%m/%d/%Y %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
    ):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except (ValueError, AttributeError):
            continue
    return None
