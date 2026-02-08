"""
Paciolus API — Three-Way Match Routes
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Request
from sqlalchemy.orm import Session

from security_utils import log_secure_operation, clear_memory
from database import get_db
from models import User
from auth import require_verified_user
from three_way_match_engine import (
    detect_po_columns, detect_invoice_columns, detect_receipt_columns,
    parse_purchase_orders, parse_invoices, parse_receipts,
    assess_three_way_data_quality, run_three_way_match,
    ThreeWayMatchConfig,
)
from shared.helpers import validate_file_size, parse_uploaded_file, parse_json_mapping, maybe_record_tool_run
from shared.rate_limits import limiter, RATE_LIMIT_AUDIT

router = APIRouter(tags=["three_way_match"])


@router.post("/audit/three-way-match")
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
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
):
    """Run three-way match validation across PO, Invoice, and Receipt files."""
    po_mapping = parse_json_mapping(po_column_mapping, "twm_po")
    inv_mapping = parse_json_mapping(invoice_column_mapping, "twm_invoice")
    rec_mapping = parse_json_mapping(receipt_column_mapping, "twm_receipt")

    log_secure_operation(
        "three_way_match_upload",
        f"Processing 3-way match: po={po_file.filename}, inv={invoice_file.filename}, rec={receipt_file.filename}"
    )

    try:
        # Parse all 3 files
        po_bytes = await validate_file_size(po_file)
        po_columns, po_rows = parse_uploaded_file(po_bytes, po_file.filename or "")
        del po_bytes

        inv_bytes = await validate_file_size(invoice_file)
        inv_columns, inv_rows = parse_uploaded_file(inv_bytes, invoice_file.filename or "")
        del inv_bytes

        rec_bytes = await validate_file_size(receipt_file)
        rec_columns, rec_rows = parse_uploaded_file(rec_bytes, receipt_file.filename or "")
        del rec_bytes

        # Detect columns
        po_detection = detect_po_columns(po_columns)
        inv_detection = detect_invoice_columns(inv_columns)
        rec_detection = detect_receipt_columns(rec_columns)

        # Parse into typed objects
        pos = parse_purchase_orders(po_rows, po_detection)
        invoices = parse_invoices(inv_rows, inv_detection)
        receipts = parse_receipts(rec_rows, rec_detection)

        del po_rows, inv_rows, rec_rows

        # Assess data quality
        data_quality = assess_three_way_data_quality(pos, invoices, receipts)

        # Run matching
        config = ThreeWayMatchConfig()
        result = run_three_way_match(pos, invoices, receipts, config)

        # Attach data quality and column detection
        result.data_quality = data_quality
        result.column_detection = {
            "po": po_detection.to_dict(),
            "invoice": inv_detection.to_dict(),
            "receipt": rec_detection.to_dict(),
        }

        del pos, invoices, receipts
        clear_memory()

        maybe_record_tool_run(db, engagement_id, current_user.id, "three_way_match", True)

        return result.to_dict()

    except Exception as e:
        log_secure_operation("three_way_match_error", str(e))
        maybe_record_tool_run(db, engagement_id, current_user.id, "three_way_match", False)
        clear_memory()
        raise HTTPException(
            status_code=400,
            detail=f"Failed to process three-way match: {str(e)}"
        )
