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
from collections.abc import Callable, Iterable, Iterator, Sequence
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Literal, Optional, TypeVar

from shared.monetary import ensure_supported_amount

# Set sufficient precision for monetary arithmetic
decimal.getcontext().prec = 28


# ---------------------------------------------------------------------------
# Sprint 883 (review ST-01): the one amount-parsing policy
# ---------------------------------------------------------------------------
# Every path that reads an amount from an uploaded cell — the testing engines
# (``safe_decimal``), preflight, the intake totals-row detector and the trial
# balance's pandas ingestion — calls ``parse_amount``. Before this, four
# parsers disagreed: "$(2,000.00)" was -2000 in one and 0 in two others, and
# preflight summed its readings into the balance check.
#
# The policy:
# - Blank (None, float NaN, empty/whitespace text) is zero, never an error.
# - Text is: an optional sign, an optional currency symbol ($ € £) in either
#   order, optional parentheses, the number, and an optional trailing minus.
#   Parentheses, a leading "-" and a trailing "-" each mean negative; more than
#   one sign character is invalid. Spaces are allowed between those parts,
#   never inside the number.
# - The number is ASCII digits, either ungrouped or grouped in thousands with
#   commas, an optional decimal point and fraction, and an optional exponent.
#   No other grouping or decimal separator is read ("1.234,56", "1 234.56" are
#   invalid): locale support is deliberately not wider than this.
# - A lone dash ("-", "$ -") is the accounting-format zero.
# - Non-finite values ("Infinity", "NaN", float inf, Decimal NaN) are invalid.
# - Invalid input is zero by default (``on_invalid="zero"``) or raises
#   ``InvalidAmountError`` (``on_invalid="error"``) for callers that must
#   reject it.

AmountOnInvalid = Literal["zero", "error"]

_AMOUNT_RE = re.compile(
    r"""
    ^
    (?P<sign1>[-+])?\s*
    (?P<cur1>[$€£])?\s*
    (?P<sign2>[-+])?\s*
    (?P<open>\()?\s*
    (?P<cur2>[$€£])?\s*
    (?P<sign3>[-+])?\s*
    (?P<number>
        (?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?:\.[0-9]*)?
        |\.[0-9]+
    )
    (?P<exponent>[eE][-+]?[0-9]+)?
    \s*(?P<close>\))?
    \s*(?P<trail>-)?
    $
    """,
    re.VERBOSE | re.ASCII,
)
_ACCOUNTING_ZERO_RE = re.compile(r"^[$€£]?\s*-\s*$")


class InvalidAmountError(ValueError):
    """An amount cell that is not blank and is not a number under the policy."""


_BLANK = object()


def _read_amount(value: object) -> Decimal | object | None:
    """Return the Decimal, ``_BLANK`` for a blank cell, or ``None`` if invalid."""
    if value is None:
        return _BLANK
    if isinstance(value, Decimal):
        return value if value.is_finite() else None
    if isinstance(value, float):  # includes numpy.float64
        if math.isnan(value):
            return _BLANK  # pandas' missing cell
        return Decimal(str(value)) if math.isfinite(value) else None
    if isinstance(value, int):
        return Decimal(value)
    text = str(value).strip()
    if not text:
        return _BLANK
    match = _AMOUNT_RE.match(text)
    if match is None:
        return Decimal(0) if _ACCOUNTING_ZERO_RE.match(text) else None
    if match["cur1"] and match["cur2"]:
        return None
    if bool(match["open"]) != bool(match["close"]):
        return None
    signs = [s for s in (match["sign1"], match["sign2"], match["sign3"]) if s]
    if len(signs) + bool(match["trail"]) > 1:
        return None
    if signs == ["+"] and match["open"]:
        return None  # "+(5)" contradicts itself
    negative = bool(match["open"]) or bool(match["trail"]) or signs == ["-"]
    try:
        result = Decimal(match["number"].replace(",", "") + (match["exponent"] or ""))
    except InvalidOperation:
        return None
    if not result.is_finite():
        return None
    return -result if negative else result


def _read_supported_amount(value: object) -> Decimal | object | None:
    """``_read_amount``, refusing anything above MAX_SUPPORTED_AMOUNT.

    Sprint 884 (TQ-12): an amount too large to carry is an error the user
    sees (AmountTooLargeError, a 400), never a cell silently read as zero.
    """
    result = _read_amount(value)
    if isinstance(result, Decimal):
        ensure_supported_amount(result)
    return result


def parse_amount(value: object, *, on_invalid: AmountOnInvalid = "zero") -> Decimal:
    """Read a monetary cell from uploaded data under the one amount policy.

    Blank cells are ``Decimal("0")``. Invalid cells are ``Decimal("0")`` when
    ``on_invalid="zero"`` (the default) and raise :class:`InvalidAmountError`
    when ``on_invalid="error"``. See the policy comment above.
    """
    result = _read_supported_amount(value)
    if result is _BLANK:
        return Decimal(0)
    if result is None:
        if on_invalid == "error":
            raise InvalidAmountError(f"Not a valid amount: {str(value)[:40]!r}")
        return Decimal(0)
    assert isinstance(result, Decimal)
    return result


def safe_decimal(value: object, default: Decimal = Decimal("0")) -> Decimal:
    """Parse a monetary value from user-uploaded data as Decimal.

    Reads ``value`` under the amount policy (:func:`parse_amount`); returns
    ``default`` when the cell is blank or invalid. Floats are stringified
    first to avoid binary imprecision.
    """
    result = _read_supported_amount(value)
    if result is _BLANK or result is None:
        return default
    assert isinstance(result, Decimal)
    return result


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


def parse_date(date_str: object, formats: Optional[Sequence[str]] = None, day_first: bool = False) -> Optional[date]:
    """Try to parse a date string into a :class:`date` object.

    Supports ISO, US, EU, and datetime formats (``DEFAULT_DATE_FORMATS``, tried
    in order). Memoised inside ``parse_memo()``.

    ``formats`` (Sprint 819 item 4) restricts the string forms tried, in the
    given order, for a caller whose accepted set is narrower than the default
    and must stay that way — e.g. a user-typed reference date whose error
    message names the forms it accepts. ``date``/``datetime`` values are
    returned as dates either way.

    Ambiguous numeric dates (``01/12/2020``) read month-first unless
    ``day_first`` is set — callers that know a column is DD/MM (see
    :func:`infer_day_first`) opt in; the default is unchanged (Sprint 855 A4).
    With ``formats`` as well, the day-first forms among ``formats`` are tried
    first; nothing outside ``formats`` is ever tried.
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
    if formats is None:
        if day_first:
            return memoized_parse("date_day_first", date_str, _parse_date_day_first_uncached)
        return memoized_parse("date", date_str, _parse_date_uncached)
    fmts = tuple(formats)
    if day_first:
        fmts = tuple(f for f in _DAY_FIRST_FORMATS if f in fmts) + tuple(f for f in fmts if f not in _DAY_FIRST_FORMATS)
        return memoized_parse("date_day_first:" + "|".join(fmts), date_str, lambda s: _parse_date_uncached(s, fmts))
    return memoized_parse("date:" + "|".join(fmts), date_str, lambda s: _parse_date_uncached(s, fmts))


# Sprint 855 (A4): the numeric forms whose day/month order is ambiguous, in the
# order a day-first column needs them tried. Anything that does not match falls
# through to the default list, where the remaining forms are unambiguous.
_DAY_FIRST_FORMATS = (
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%y",
)
_AMBIGUOUS_NUMERIC_DATE = re.compile(r"^\s*(\d{1,2})[/-](\d{1,2})[/-](\d{2}|\d{4})(?:[ T].*)?$")


def infer_day_first(values: Iterable[object]) -> bool:
    """Whether a column of dates is written day-first (DD/MM/YYYY).

    True only when at least one value can only be day-first (first part > 12)
    and none can only be month-first (second part > 12). A column with no
    unambiguous value, or with contradictory values, keeps the month-first
    default — a guess is not evidence.
    """
    day_first_seen = month_first_seen = False
    for value in values:
        if not isinstance(value, str):
            continue
        match = _AMBIGUOUS_NUMERIC_DATE.match(value)
        if not match:
            continue
        first, second = int(match.group(1)), int(match.group(2))
        if first > 12 and second <= 12:
            day_first_seen = True
        elif second > 12 and first <= 12:
            month_first_seen = True
        if day_first_seen and month_first_seen:
            return False
    return day_first_seen


def _parse_date_day_first_uncached(date_str: str) -> Optional[date]:
    for fmt in _DAY_FIRST_FORMATS:
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except (ValueError, AttributeError):
            continue
    return _parse_date_uncached(date_str)


DEFAULT_DATE_FORMATS: tuple[str, ...] = (
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
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%SZ",
    "%m/%d/%Y %I:%M %p",
    "%m/%d/%Y %I:%M:%S %p",
    "%m/%d/%y",  # 2-digit year, US order (the order the 4-digit forms prefer)
    "%d.%m.%Y",  # dotted dates are day-first everywhere they are used
    "%d-%b-%Y",
    "%d %b %Y",
    "%b %d, %Y",
    "%B %d, %Y",
    "%Y%m%d",
)


def _parse_date_uncached(date_str: str, formats: Sequence[str] = DEFAULT_DATE_FORMATS) -> Optional[date]:
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except (ValueError, AttributeError):
            continue
    return None
