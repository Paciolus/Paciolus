"""
Request-field decimal parsing for the JSON-body tool routes (Sprint 819).

This function existed as nine byte-identical copies, one per route module
(account risk heatmap, book-to-tax, cash flow projector, depreciation,
Form 1099, intercompany elimination, lease accounting, loan amortization,
W-2 reconciliation). A fix to one copy — PR #189's finiteness check — had to
be made nine times; now it is made once.
"""

from decimal import Decimal, InvalidOperation

from fastapi import HTTPException

from shared.parsing_helpers import safe_decimal


def parse_request_decimal(field_name: str, raw: str) -> Decimal:
    """Parse a decimal string, rejecting anything the engines cannot arithmetic on.

    PR #189 review: the finiteness check is the load-bearing half. ``Decimal``
    accepts ``"NaN"``, ``"sNaN"``, ``"Infinity"`` and ``"-Infinity"`` without
    raising, so a syntactically valid non-finite value used to pass straight
    through to the engine and blow up on the first comparison or quantisation —
    an uncaught ``InvalidOperation``, surfacing as a 500 where this function's
    whole purpose is to produce a 400.
    """
    try:
        value = Decimal(raw)
    except (InvalidOperation, ValueError, TypeError):
        raise HTTPException(status_code=400, detail=f"Invalid numeric value for {field_name}: {raw!r}")
    if not value.is_finite():
        raise HTTPException(status_code=400, detail=f"Invalid numeric value for {field_name}: {raw!r}")
    return value


def parse_request_amount(field_name: str, raw: str) -> Decimal:
    """Parse a trial-balance amount cell, accepting accounting formats.

    Sprint 855 (I5): ``(1,000.00)``, ``$(1,000.00)``, ``1,000.00`` and ``1000-``
    are how exported trial balances write amounts, and the upload page forwards
    the parentheses. Normalisation is the shared ``safe_decimal`` the file-based
    engines already use; unlike that helper, an unparseable cell is a 400 here
    rather than a silent zero. A percent sign is refused — ``safe_decimal`` would
    strip it, and ``10%`` is not an amount.
    """
    if "%" in raw:
        raise HTTPException(status_code=400, detail=f"Invalid numeric value for {field_name}: {raw!r}")
    value = safe_decimal(raw, default=Decimal("NaN"))
    if not value.is_finite():
        raise HTTPException(status_code=400, detail=f"Invalid numeric value for {field_name}: {raw!r}")
    return value
