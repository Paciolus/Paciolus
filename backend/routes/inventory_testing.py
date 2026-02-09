"""
Paciolus API — Inventory Testing Routes (Sprint 117)
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Request
from sqlalchemy.orm import Session

from security_utils import log_secure_operation, clear_memory
from database import get_db
from models import User
from auth import require_verified_user
from inventory_testing_engine import run_inventory_testing, InventoryTestingConfig
from shared.helpers import validate_file_size, parse_uploaded_file, parse_json_mapping, maybe_record_tool_run
from shared.rate_limits import limiter, RATE_LIMIT_AUDIT

router = APIRouter(tags=["inventory_testing"])


@router.post("/audit/inventory-testing")
@limiter.limit(RATE_LIMIT_AUDIT)
async def audit_inventory(
    request: Request,
    file: UploadFile = File(...),
    column_mapping: Optional[str] = Form(default=None),
    engagement_id: Optional[int] = Form(default=None),
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
):
    """Run automated inventory register testing.

    IAS 2/ASC 330: Inventory assertions.
    ISA 501: Audit Evidence — Inventory.
    ISA 540: Auditing accounting estimates (NRV indicators).
    """
    column_mapping_dict = parse_json_mapping(column_mapping, "inventory_testing")

    log_secure_operation(
        "inventory_testing_upload",
        f"Processing inventory file: {file.filename}"
    )

    try:
        file_bytes = await validate_file_size(file)
        column_names, rows = parse_uploaded_file(file_bytes, file.filename or "")
        del file_bytes

        config = InventoryTestingConfig()

        result = run_inventory_testing(
            rows=rows,
            column_names=column_names,
            config=config,
            column_mapping=column_mapping_dict,
        )

        del rows
        clear_memory()

        score = result.composite_score.score if hasattr(result, 'composite_score') and result.composite_score else None
        maybe_record_tool_run(db, engagement_id, current_user.id, "inventory_testing", True, score)

        return result.to_dict()

    except Exception as e:
        log_secure_operation("inventory_testing_error", str(e))
        maybe_record_tool_run(db, engagement_id, current_user.id, "inventory_testing", False)
        clear_memory()
        raise HTTPException(
            status_code=400,
            detail=f"Failed to process inventory file: {str(e)}"
        )
