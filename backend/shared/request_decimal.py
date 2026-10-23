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
