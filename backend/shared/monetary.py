"""
Shared Monetary Precision Utilities — Sprint 340

Deterministic 2dp ROUND_HALF_UP at all system boundaries.
Replaces float-based BALANCE_TOLERANCE and Python's banker's rounding.

Used by:
- audit_engine.py (balance checks, result quantization)
- ratio_engine.py (CategoryTotals.to_dict)
- routes/diagnostics.py (DB write quantization)
- routes/engagements.py (materiality_amount quantization)
- engagement_manager.py (materiality cascade)
- shared/round_amounts.py (Decimal modulo)
"""

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

# 2 decimal-place precision for all monetary values
MONETARY_PRECISION = Decimal("0.01")

# Canonical zero for monetary comparisons
MONETARY_ZERO = Decimal("0.00")

# Balance tolerance — replaces the float literal 0.01 in audit_engine.py.
# Use this for "are two amounts equal within rounding error" checks.
BALANCE_TOLERANCE = MONETARY_PRECISION

# Sprint 766: half-a-cent denominator guard for percent-variance calculations.
# Use this for "is the prior balance large enough that dividing by it yields
# a meaningful percent" checks.  Distinct from BALANCE_TOLERANCE: this is
# the lower bound for division, not an equality tolerance.  Several engines
# previously redefined this locally (three_way_match_engine.MONETARY_EPSILON,
# scattered ``NEAR_ZERO = 0.005`` floats in multi_period_comparison /
# prior_period_comparison) — consolidate to the canonical Decimal here.
MONETARY_NEAR_ZERO = Decimal("0.005")


def quantize_monetary(value: float | Decimal | str | int | None) -> Decimal:
    """Quantize a value to 2 decimal places using ROUND_HALF_UP.

    Converts any numeric input to a Decimal with exactly 2dp.
    Uses ROUND_HALF_UP (commercial rounding) instead of Python's
    default ROUND_HALF_EVEN (banker's rounding).

    Args:
        value: Numeric value to quantize. None is treated as 0.

    Returns:
        Decimal quantized to 2dp with ROUND_HALF_UP.

    Examples:
        >>> quantize_monetary(0.1 + 0.2)
        Decimal('0.30')
        >>> quantize_monetary(2.225)
        Decimal('2.23')  # HALF_UP, not banker's 2.22
        >>> quantize_monetary(None)
        Decimal('0.00')
    """
    if value is None:
        return MONETARY_ZERO

    try:
        if isinstance(value, Decimal):
            dec = value
        elif isinstance(value, float):
            # str() conversion avoids binary float representation issues
            dec = Decimal(str(value))
        else:
            dec = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return MONETARY_ZERO

    return dec.quantize(MONETARY_PRECISION, rounding=ROUND_HALF_UP)


def monetary_equal(a: float | Decimal | str | int | None, b: float | Decimal | str | int | None) -> bool:
    """Compare two monetary values for equality after quantization.

    Both values are quantized to 2dp ROUND_HALF_UP before comparison,
    making this safe for float inputs.

    Args:
        a: First monetary value.
        b: Second monetary value.

    Returns:
        True if both values are equal after 2dp quantization.
    """
    return quantize_monetary(a) == quantize_monetary(b)


def decimals_to_floats(value: object) -> object:
    """Return ``value`` with every Decimal (at any depth) as a float.

    Sprint 829: flagged-entry ``details`` mixed Decimals and floats, and a
    response model serializes a Decimal inside ``dict[str, Any]`` as a JSON
    string — so the same field (JE ``details.amount``) reached the client as a
    number from one test and a string from another. Details are display data;
    they go out as numbers.
    """
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {k: decimals_to_floats(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [decimals_to_floats(v) for v in value]
    return value


# ─────────────────────────────────────────────────────────────────────────────
# Sprint 884 (TQ-12 / OUT-19): the largest amount the product supports.
#
# CEO decision 2026-11-18: 999,999,999,999,999.99. Every amount up to it is
# carried exactly as a Decimal from upload to API response, PDF and workbook.
# An uploaded amount above it is refused with AmountTooLargeError (a 400),
# never read as zero; serializing one refuses the same way.
#
# Two limits sit below this one and are handled where they bite:
# - a float (and so a JavaScript number) holds every cent exactly only up to
#   about 2**53 cents (~90 trillion). The API writes exact digits regardless
#   (shared/exact_json.py); a browser may still show a value above that ~70-90
#   trillion range one cent off.
# - Excel keeps 15 significant digits. Workbooks write the exact value into the
#   file and, where it has more than 15 digits, an exact text copy beside it
#   (EXCEL_EXACT_DIGITS / excel_holds_exactly).
# ─────────────────────────────────────────────────────────────────────────────

MAX_SUPPORTED_AMOUNT = Decimal("999999999999999.99")

EXCEL_EXACT_DIGITS = 15


class AmountTooLargeError(ValueError):
    """An amount larger than MAX_SUPPORTED_AMOUNT (in absolute value)."""

    def __init__(self, value: object = None) -> None:
        self.value = value
        super().__init__(
            f"An amount exceeds the largest supported amount, {MAX_SUPPORTED_AMOUNT:,}. "
            "Split the balance or report it in thousands."
        )


def ensure_supported_amount(value: Decimal) -> Decimal:
    """Return ``value``, or raise AmountTooLargeError if it is above the limit."""
    if value.is_finite() and abs(value) > MAX_SUPPORTED_AMOUNT:
        raise AmountTooLargeError(value)
    return value


def excel_holds_exactly(value: Decimal) -> bool:
    """True if Excel's 15 significant digits hold ``value`` exactly."""
    if not value.is_finite():
        return False
    digits = value.normalize().as_tuple().digits
    return len(digits) <= EXCEL_EXACT_DIGITS
