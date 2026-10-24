"""
Paciolus API — Three-Way Match Routes
"""

import asyncio
import dataclasses
import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from auth import require_verified_user
from database import get_db
from models import User
from security_utils import log_secure_operation
from shared.error_messages import sanitize_error
from shared.rate_limits import RATE_LIMIT_AUDIT, limiter
from shared.saved_testing_config import (
    TWM_CONFIG_BOUNDS,
    TWM_SPEC,
    load_saved_testing_config,
    supersede_with_run_overrides,
)
from shared.testing_response_schemas import ThreeWayMatchResponse
from shared.tool_run_recorder import maybe_record_tool_run
from shared.upload_pipeline import (
    memory_cleanup,
    parse_uploaded_file,
    validate_file_size,
)
from three_way_match_engine import (
    ColumnMappingError,
    InvoiceColumnDetectionResult,
    POColumnDetectionResult,
    ReceiptColumnDetectionResult,
    ThreeWayMatchConfig,
    apply_column_mapping,
    assess_three_way_data_quality,
    detect_invoice_columns,
    detect_po_columns,
    detect_receipt_columns,
    parse_invoices,
    parse_purchase_orders,
    parse_receipts,
    run_three_way_match,
    validate_column_mapping_keys,
)

router = APIRouter(tags=["three_way_match"])


# ---------------------------------------------------------------------------
# Config override bounds (RPT-11 remediation, 2026-04-20)
# ---------------------------------------------------------------------------
# Accept validated tolerance overrides from request.  Bounds are defensive:
# they reject nonsensical or weaponised inputs (e.g. negative tolerances,
# >100% variance thresholds, or date windows measured in years) that would
# otherwise silently produce degenerate match results.  Sprint 836: the same
# bounds govern saved practice settings, so they live with that helper.
_TWM_CONFIG_BOUNDS: dict[str, tuple[float, float]] = TWM_CONFIG_BOUNDS


def _build_twm_config(
    *,
    amount_tolerance: Optional[float],
    quantity_tolerance: Optional[float],
    date_window_days: Optional[int],
    fuzzy_vendor_threshold: Optional[float],
    price_variance_threshold: Optional[float],
    enable_fuzzy_matching: Optional[bool],
    fuzzy_composite_threshold: Optional[float],
    base: Optional[ThreeWayMatchConfig] = None,
) -> ThreeWayMatchConfig:
    """Build a validated ThreeWayMatchConfig from optional override params.

    Any ``None`` override falls back to ``base`` (Sprint 836: the user's saved
    settings) or, without one, the dataclass default, so existing clients
    (which supply no overrides) are bit-for-bit unchanged.
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
    return dataclasses.replace(base if base is not None else ThreeWayMatchConfig(), **supplied)


def _parse_column_mapping(raw: Optional[str], detection_cls: type, label: str) -> Optional[dict[str, str]]:
    """Parse and check one manual column mapping (Sprint 839).

    Before Sprint 839 the three mappings were parsed and then ignored. They are
    now applied to column detection; anything malformed is refused with a 400
    rather than accepted and dropped.
    """
    if raw is None or not raw.strip():
        return None
    try:
        mapping = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail=f"{label} column mapping is not valid JSON.")
    if not isinstance(mapping, dict):
        raise HTTPException(
            status_code=400,
            detail=f"{label} column mapping must be an object of field name to column name.",
        )
    if not mapping:
        return None
    try:
        validate_column_mapping_keys(mapping, detection_cls, label)
    except ColumnMappingError as e:
        raise HTTPException(status_code=400, detail=str(e))
    log_secure_operation(f"twm_{label.lower()}_mapping", f"Received mapping: {sorted(mapping.keys())}")
    return {str(k): str(v) for k, v in mapping.items()}


@router.post("/audit/three-way-match", response_model=ThreeWayMatchResponse)
@limiter.limit(RATE_LIMIT_AUDIT)
async def audit_three_way_match(
    request: Request,
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

    # Sprint 839: manual column mappings are applied to detection (they were
    # parsed and then ignored before). Field names are checked here, before
    # any file I/O; mapped column names are checked against each file.
    po_mapping = _parse_column_mapping(po_column_mapping, POColumnDetectionResult, "PO")
    inv_mapping = _parse_column_mapping(invoice_column_mapping, InvoiceColumnDetectionResult, "Invoice")
    rec_mapping = _parse_column_mapping(receipt_column_mapping, ReceiptColumnDetectionResult, "Receipt")

    # Sprint 836: start from the user's saved settings; a value supplied for
    # this run replaces the saved one (and the result says so).
    saved = load_saved_testing_config(current_user, TWM_SPEC)
    run_overrides = {
        "amount_tolerance": amount_tolerance,
        "quantity_tolerance": quantity_tolerance,
        "date_window_days": date_window_days,
        "fuzzy_vendor_threshold": fuzzy_vendor_threshold,
        "price_variance_threshold": price_variance_threshold,
        "enable_fuzzy_matching": enable_fuzzy_matching,
        "fuzzy_composite_threshold": fuzzy_composite_threshold,
    }
    supplied_run_overrides = {k for k, v in run_overrides.items() if v is not None}
    supersede_with_run_overrides(saved, supplied_run_overrides)

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
        base=saved.config,
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

                try:
                    po_detection = apply_column_mapping(detect_po_columns(po_columns), po_mapping, "PO")
                    inv_detection = apply_column_mapping(detect_invoice_columns(inv_columns), inv_mapping, "Invoice")
                    rec_detection = apply_column_mapping(detect_receipt_columns(rec_columns), rec_mapping, "Receipt")
                except ColumnMappingError as e:
                    # The message names only the user's own column headers.
                    raise HTTPException(status_code=400, detail=str(e))

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

            maybe_record_tool_run(db, engagement_id, current_user.id, "three_way_match", True, consumes_upload=True)

            response: dict[str, Any] = result.to_dict()
            response.update(saved.result_fields())
            # Sprint 839: disclose every value supplied for this run, as
            # applied (the saved value it replaced is in settings_ignored).
            # settings_applied stays the saved settings that took effect, so
            # each value's source is explicit (refines the PR #229 fix).
            response["settings_run_overrides"] = {
                name: getattr(config, name) for name in sorted(supplied_run_overrides)
            }
            return response

        except HTTPException:
            # Preserve 400 bounds-check errors raised upstream of the thread.
            raise
        except (ValueError, KeyError, TypeError) as e:
            logger.exception("Three-way match analysis failed")
            maybe_record_tool_run(db, engagement_id, current_user.id, "three_way_match", False)
            raise HTTPException(status_code=400, detail=sanitize_error(e, "analysis", "three_way_match_error"))
