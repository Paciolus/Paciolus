"""
Paciolus API — Inventory Testing Routes (Sprint 117)
"""
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Request, UploadFile
from sqlalchemy.orm import Session

from auth import require_verified_user
from database import get_db
from inventory_testing_engine import InventoryTestingConfig, run_inventory_testing
from models import User
from shared.rate_limits import RATE_LIMIT_AUDIT, limiter
from shared.testing_response_schemas import InvTestingResponse
from shared.testing_route import run_single_file_testing

router = APIRouter(tags=["inventory_testing"])


@router.post("/audit/inventory-testing", response_model=InvTestingResponse)
@limiter.limit(RATE_LIMIT_AUDIT)
async def audit_inventory(
    request: Request,
    background_tasks: BackgroundTasks,
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
    return await run_single_file_testing(
        file=file, column_mapping=column_mapping,
        engagement_id=engagement_id, current_user=current_user, db=db,
        background_tasks=background_tasks,
        tool_name="inventory_testing", mapping_key="inventory_testing",
        log_label="inventory", error_key="inventory_testing_error",
        run_engine=lambda rows, cols, mapping, fn: run_inventory_testing(
            rows=rows, column_names=cols,
            config=InventoryTestingConfig(), column_mapping=mapping,
        ),
    )
