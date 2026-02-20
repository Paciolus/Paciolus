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

# Balance tolerance — replaces the float literal 0.01 in audit_engine.py
BALANCE_TOLERANCE = MONETARY_PRECISION


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


def monetary_equal(a: float | Decimal | str | int | None,
                   b: float | Decimal | str | int | None) -> bool:
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
