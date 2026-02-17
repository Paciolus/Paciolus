"""
Paciolus API — Fixed Asset Testing Routes (Sprint 114)
"""
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Request, UploadFile
from sqlalchemy.orm import Session

from auth import require_verified_user
from database import get_db
from fixed_asset_testing_engine import FixedAssetTestingConfig, run_fixed_asset_testing
from models import User
from shared.rate_limits import RATE_LIMIT_AUDIT, limiter
from shared.testing_response_schemas import FATestingResponse
from shared.testing_route import run_single_file_testing

router = APIRouter(tags=["fixed_asset_testing"])


@router.post("/audit/fixed-assets", response_model=FATestingResponse)
@limiter.limit(RATE_LIMIT_AUDIT)
async def audit_fixed_assets(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    column_mapping: Optional[str] = Form(default=None),
    engagement_id: Optional[int] = Form(default=None),
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
):
    """Run automated fixed asset register testing.

    IAS 16/ASC 360: Property, Plant and Equipment assertions.
    ISA 540: Auditing accounting estimates (depreciation, useful life, residual value).
    """
    return await run_single_file_testing(
        file=file, column_mapping=column_mapping,
        engagement_id=engagement_id, current_user=current_user, db=db,
        background_tasks=background_tasks,
        tool_name="fixed_asset_testing", mapping_key="fixed_asset_testing",
        log_label="fixed asset", error_key="fixed_asset_testing_error",
        run_engine=lambda rows, cols, mapping, fn: run_fixed_asset_testing(
            rows=rows, column_names=cols,
            config=FixedAssetTestingConfig(), column_mapping=mapping,
        ),
    )
