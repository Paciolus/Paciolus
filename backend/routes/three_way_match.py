"""
Paciolus API — Three-Way Match Routes
"""
import asyncio
import logging
from typing import Optional

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
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
):
    """Run three-way match validation across PO, Invoice, and Receipt files."""
    from shared.testing_route import enforce_tool_access
    enforce_tool_access(current_user, "three_way_match")

    po_mapping = parse_json_mapping(po_column_mapping, "twm_po")
    inv_mapping = parse_json_mapping(invoice_column_mapping, "twm_invoice")
    rec_mapping = parse_json_mapping(receipt_column_mapping, "twm_receipt")

    log_secure_operation(
        "three_way_match_upload",
        f"Processing 3-way match: po={po_file.filename}, inv={invoice_file.filename}, rec={receipt_file.filename}"
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

            def _analyze():
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

                config = ThreeWayMatchConfig()
                result = run_three_way_match(pos, invoices, receipts, config)

                result.data_quality = data_quality
                result.column_detection = {
                    "po": po_detection.to_dict(),
                    "invoice": inv_detection.to_dict(),
                    "receipt": rec_detection.to_dict(),
                }

                return result

            result = await asyncio.to_thread(_analyze)

            background_tasks.add_task(maybe_record_tool_run, db, engagement_id, current_user.id, "three_way_match", True)

            return result.to_dict()

        except (ValueError, KeyError, TypeError) as e:
            logger.exception("Three-way match analysis failed")
            maybe_record_tool_run(db, engagement_id, current_user.id, "three_way_match", False)
            raise HTTPException(
                status_code=400,
                detail=sanitize_error(e, "analysis", "three_way_match_error")
            )
