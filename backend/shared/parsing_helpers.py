"""
Shared data-parsing helpers for Paciolus testing engines.

Sprint 136: Extracted from 9 engine files where these functions were
duplicated verbatim.  The canonical implementation is the superset of
all variants (standard + ar_aging isinstance fast-path +
three_way_match/bank_rec parenthetical-negative handling).
"""

import decimal
import functools
import math
import re
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Optional, TypeVar

# Set sufficient precision for monetary arithmetic
decimal.getcontext().prec = 28


def safe_decimal(value: object, default: Decimal = Decimal("0")) -> Decimal:
    """Parse a monetary value from user-uploaded data as Decimal.

    Never accepts float as intermediate; always parses from string or int.
    Returns ``default`` for None, empty string, or unparseable input.

    Handles:
    - ``None`` → default
    - ``int`` / ``Decimal`` pass-through
    - ``float`` → stringified first to avoid binary imprecision
    - Currency strings: ``$1,234.56``, ``(1,234.56)`` (parenthetical negatives)
    - Trailing-negative: ``1234-``
    """
    if value is None:
        return default
    if isinstance(value, Decimal):
        return value
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return default
        return Decimal(str(value))
    if isinstance(value, int):
        return Decimal(value)
    try:
        cleaned = str(value).strip()
        if not cleaned or cleaned.lower() in ("nan", "none", "inf", "-inf"):
            return default
        # Detect accounting-style parenthetical negatives: (1,234.56).
        # Sprint 824: test after dropping currency signs and spaces — checking
        # the raw string missed "$(2,000.00)", which parsed as +2,000.
        bare = re.sub(r"[$\s]", "", cleaned)
        is_negative = bare.startswith("(") and bare.endswith(")")
        cleaned = re.sub(r"[,$\s()%]", "", cleaned)
        if cleaned.startswith("-") or cleaned.endswith("-"):
            cleaned = "-" + cleaned.strip("-")
            is_negative = True
        elif is_negative and not cleaned.startswith("-"):
            cleaned = "-" + cleaned
        result = Decimal(cleaned)
    except (InvalidOperation, ValueError, TypeError):
        return default
    # Sprint 824: "Infinity", "-Infinity", "sNaN" etc. parse as non-finite
    # Decimals — the string check above only knew "inf". A non-finite amount is
    # never a monetary value; treat it like any other unparseable cell.
    return result if result.is_finite() else default


def safe_float(value: object) -> float:
    """Convert *value* to float, returning ``0.0`` for non-numeric.

    .. deprecated::
        DEPRECATED for monetary values. Use :func:`safe_decimal` instead.
        This function is retained only for genuinely non-financial numeric
        parsing (e.g., quantities, hours, statistical z-scores).

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
        f = float(str(value))
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
        # Detect accounting-style parenthetical negatives: (1,234.56) — after
        # dropping currency signs, so "$(2,000.00)" stays negative (Sprint 824).
        bare = re.sub(r"[$\s]", "", s)
        is_negative = bare.startswith("(") and bare.endswith(")")
        cleaned = re.sub(r"[,$\s()%]", "", s)
        if cleaned.startswith("-") or cleaned.endswith("-"):
            cleaned = "-" + cleaned.strip("-")
            is_negative = True
        elif is_negative and not cleaned.startswith("-"):
            cleaned = "-" + cleaned
        try:
            f = float(cleaned)
        except (ValueError, TypeError):
            return 0.0
        return f if math.isfinite(f) else 0.0

    return 0.0


def safe_str(value: object) -> Optional[str]:
    """Convert *value* to stripped string, returning ``None`` for empty/NaN."""
    if value is None:
        return None
    s = str(value).strip()
    if s == "" or s.lower() == "nan" or s.lower() == "none":
        return None
    return s


def safe_int(value: object) -> Optional[int]:
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


# ---------------------------------------------------------------------------
# Sprint 815: run-scoped parse memo
# ---------------------------------------------------------------------------
# The JE engine parsed each entry's dates ~11 times (once per date-based test),
# and each parse tries up to nine strptime formats: on a 100k-row GL that was
# ~1.2M parses / 8.4M strptime calls — 283 of 302 seconds. A memo keyed by the
# raw string removes the repetition without changing any result.
#
# It is deliberately NOT a process-wide ``lru_cache``: that would retain values
# from uploaded files across requests, which Zero-Storage forbids. The memo
# exists only inside ``parse_memo()`` — entered around one engine run — and is
# dropped when that run exits. Outside it, every call parses as before.

_PARSE_MEMO: ContextVar[Optional[dict[tuple[str, str], Any]]] = ContextVar("paciolus_parse_memo", default=None)

_T = TypeVar("_T")


@contextmanager
def parse_memo() -> Iterator[None]:
    """Memoise string parsing for the duration of one engine run.

    Re-entrant: a nested ``parse_memo()`` reuses the outer run's memo.
    """
    if _PARSE_MEMO.get() is not None:
        yield
        return
    token = _PARSE_MEMO.set({})
    try:
        yield
    finally:
        _PARSE_MEMO.reset(token)


def with_parse_memo(fn: Callable[..., _T]) -> Callable[..., _T]:
    """Decorator form of :func:`parse_memo` for engine entry points."""

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> _T:
        with parse_memo():
            return fn(*args, **kwargs)

    return wrapper


def memoized_parse(kind: str, value: object, parse: Callable[[Any], _T]) -> _T:
    """Return ``parse(value)``, memoised by ``(kind, value)`` inside a run.

    Only ``str`` values are memoised — they are what uploads produce, and they
    are hashable with value semantics. Anything else is parsed directly.
    """
    memo = _PARSE_MEMO.get()
    if memo is None or not isinstance(value, str):
        return parse(value)
    key = (kind, value)
    try:
        return memo[key]  # type: ignore[no-any-return]
    except KeyError:
        result = memo[key] = parse(value)
        return result


def parse_date(date_str: object) -> Optional[date]:
    """Try to parse a date string into a :class:`date` object.

    Supports ISO, US, EU, and datetime formats. Memoised inside ``parse_memo()``.
    """
    if not date_str:
        return None
    # Sprint 829: an .xlsx cell can arrive as a datetime / pandas Timestamp
    # rather than text; every one of those parsed to None (payroll pay dates
    # from an Excel register were all missing). NaT is a datetime too.
    if isinstance(date_str, datetime):
        try:
            result = date_str.date()
        except ValueError:
            return None
        return result if result == result else None  # NaT.date() is NaT, which != itself
    if isinstance(date_str, date):
        return date_str
    return memoized_parse("date", date_str, _parse_date_uncached)


def _parse_date_uncached(date_str: str) -> Optional[date]:
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
        # Sprint 829: forms seen in exported ledgers that were silently skipped.
        # All are unambiguous and only tried after the numeric forms above.
        "%Y-%m-%d %H:%M:%S.%f",
        "%d-%b-%Y",
        "%d %b %Y",
        "%b %d, %Y",
        "%B %d, %Y",
        "%Y%m%d",
    ):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except (ValueError, AttributeError):
            continue
    return None
