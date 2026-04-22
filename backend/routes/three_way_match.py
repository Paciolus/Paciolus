"""
Paciolus API — Three-Way Match Routes
"""

import asyncio
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from auth import require_verified_user
from database import get_db
from models import User
from security_utils import log_secure_operation
from shared.error_messages import sanitize_error
from shared.helpers import (
    maybe_record_tool_run,
    memory_cleanup,
    parse_json_mapping,
    parse_uploaded_file,
    validate_file_size,
)
from shared.rate_limits import RATE_LIMIT_AUDIT, limiter
from shared.testing_response_schemas import ThreeWayMatchResponse
from three_way_match_engine import (
    ThreeWayMatchConfig,
    assess_three_way_data_quality,
    detect_invoice_columns,
    detect_po_columns,
    detect_receipt_columns,
    parse_invoices,
    parse_purchase_orders,
    parse_receipts,
    run_three_way_match,
)

router = APIRouter(tags=["three_way_match"])


# ---------------------------------------------------------------------------
# Config override bounds (RPT-11 remediation, 2026-04-20)
# ---------------------------------------------------------------------------
# Accept validated tolerance overrides from request.  Bounds are defensive:
# they reject nonsensical or weaponised inputs (e.g. negative tolerances,
# >100% variance thresholds, or date windows measured in years) that would
# otherwise silently produce degenerate match results.
_TWM_CONFIG_BOUNDS: dict[str, tuple[float, float]] = {
    "amount_tolerance": (0.0, 10_000.0),  # up to $10K absolute
    "quantity_tolerance": (0.0, 10_000.0),  # up to 10K units
    "date_window_days": (0.0, 365.0),  # up to 1 year
    "fuzzy_vendor_threshold": (0.0, 1.0),
    "price_variance_threshold": (0.0, 1.0),  # 0–100%
    "fuzzy_composite_threshold": (0.0, 1.0),
}


def _build_twm_config(
    *,
    amount_tolerance: Optional[float],
    quantity_tolerance: Optional[float],
    date_window_days: Optional[int],
    fuzzy_vendor_threshold: Optional[float],
    price_variance_threshold: Optional[float],
    enable_fuzzy_matching: Optional[bool],
    fuzzy_composite_threshold: Optional[float],
) -> ThreeWayMatchConfig:
    """Build a validated ThreeWayMatchConfig from optional override params.

    Any ``None`` override falls back to the dataclass default so existing
    clients (which supply no overrides) are bit-for-bit unchanged.
    Out-of-bounds numeric overrides raise HTTP 400.
    """
    overrides: dict[str, Any] = {
        "amount_tolerance": amount_tolerance,
        "quantity_tolerance": quantity_tolerance,
        "date_window_days": date_window_days,
        "fuzzy_vendor_threshold": fuzzy_vendor_threshold,
        "price_variance_threshold": price_variance_threshold,
        "enable_fuzzy_matching": enable_fuzzy_matching,
        "fuzzy_composite_threshold": fuzzy_composite_threshold,
    }
    supplied: dict[str, Any] = {}
    for key, value in overrides.items():
        if value is None:
            continue
        if key == "enable_fuzzy_matching":
            supplied[key] = bool(value)
            continue
        lo, hi = _TWM_CONFIG_BOUNDS[key]
        if not (lo <= float(value) <= hi):
            raise HTTPException(
                status_code=400,
                detail=(f"Three-way match config override out of range: {key}={value} must be within [{lo}, {hi}]."),
            )
        supplied[key] = int(value) if key == "date_window_days" else float(value)
    return ThreeWayMatchConfig(**supplied)


@router.post("/audit/three-way-match", response_model=ThreeWayMatchResponse)
@limiter.limit(RATE_LIMIT_AUDIT)
async def audit_three_way_match(
    request: Request,
    background_tasks: BackgroundTasks,
    po_file: UploadFile = File(...),
    invoice_file: UploadFile = File(...),
    receipt_file: UploadFile = File(...),
    po_column_mapping: Optional[str] = Form(default=None),
    invoice_column_mapping: Optional[str] = Form(default=None),
    receipt_column_mapping: Optional[str] = Form(default=None),
    engagement_id: Optional[int] = Form(default=None),
    # RPT-11 remediation: optional config overrides.  All default to None so
    # existing clients (which pass none) continue to use ThreeWayMatchConfig
    # defaults.  Each override is bounds-checked in _build_twm_config.
    amount_tolerance: Optional[float] = Form(default=None),
    quantity_tolerance: Optional[float] = Form(default=None),
    date_window_days: Optional[int] = Form(default=None),
    fuzzy_vendor_threshold: Optional[float] = Form(default=None),
    price_variance_threshold: Optional[float] = Form(default=None),
    enable_fuzzy_matching: Optional[bool] = Form(default=None),
    fuzzy_composite_threshold: Optional[float] = Form(default=None),
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Run three-way match validation across PO, Invoice, and Receipt files."""
    from shared.entitlement_checks import check_upload_limit
    from shared.testing_route import enforce_tool_access

    enforce_tool_access(current_user, "three_way_match", db)
    # Sprint 678: count three-way-match uploads toward the monthly quota.
    check_upload_limit(current_user, db)

    # parse_json_mapping has a log_secure_operation side effect; returns ignored
    # until column-override wiring is implemented for three-way-match.
    _ = parse_json_mapping(po_column_mapping, "twm_po")
    _ = parse_json_mapping(invoice_column_mapping, "twm_invoice")
    _ = parse_json_mapping(receipt_column_mapping, "twm_receipt")

    # Build the config before file I/O so bounds-check errors short-circuit
    # without having to read / parse the uploads.
    config = _build_twm_config(
        amount_tolerance=amount_tolerance,
        quantity_tolerance=quantity_tolerance,
        date_window_days=date_window_days,
        fuzzy_vendor_threshold=fuzzy_vendor_threshold,
        price_variance_threshold=price_variance_threshold,
        enable_fuzzy_matching=enable_fuzzy_matching,
        fuzzy_composite_threshold=fuzzy_composite_threshold,
    )

    log_secure_operation(
        "three_way_match_upload",
        f"Processing 3-way match: po={po_file.filename}, inv={invoice_file.filename}, rec={receipt_file.filename}",
    )

    with memory_cleanup():
        try:
            # Read file bytes (async I/O)
            po_bytes = await validate_file_size(po_file)
            inv_bytes = await validate_file_size(invoice_file)
            rec_bytes = await validate_file_size(receipt_file)
            po_filename = po_file.filename or ""
            inv_filename = invoice_file.filename or ""
            rec_filename = receipt_file.filename or ""

            def _analyze() -> Any:
                po_columns, po_rows = parse_uploaded_file(po_bytes, po_filename)
                inv_columns, inv_rows = parse_uploaded_file(inv_bytes, inv_filename)
                rec_columns, rec_rows = parse_uploaded_file(rec_bytes, rec_filename)

                po_detection = detect_po_columns(po_columns)
                inv_detection = detect_invoice_columns(inv_columns)
                rec_detection = detect_receipt_columns(rec_columns)

                pos = parse_purchase_orders(po_rows, po_detection)
                invoices = parse_invoices(inv_rows, inv_detection)
                receipts = parse_receipts(rec_rows, rec_detection)

                data_quality = assess_three_way_data_quality(pos, invoices, receipts)

                result = run_three_way_match(pos, invoices, receipts, config)

                result.data_quality = data_quality
                result.column_detection = {
                    "po": po_detection.to_dict(),
                    "invoice": inv_detection.to_dict(),
                    "receipt": rec_detection.to_dict(),
                }

                return result

            result = await asyncio.to_thread(_analyze)

            background_tasks.add_task(
                maybe_record_tool_run, db, engagement_id, current_user.id, "three_way_match", True
            )

            return result.to_dict()  # type: ignore[no-any-return]

        except HTTPException:
            # Preserve 400 bounds-check errors raised upstream of the thread.
            raise
        except (ValueError, KeyError, TypeError) as e:
            logger.exception("Three-way match analysis failed")
            maybe_record_tool_run(db, engagement_id, current_user.id, "three_way_match", False)
            raise HTTPException(status_code=400, detail=sanitize_error(e, "analysis", "three_way_match_error"))
