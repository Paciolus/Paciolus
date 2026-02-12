"""
Paciolus API — Fixed Asset Testing Routes (Sprint 114)
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Request
from sqlalchemy.orm import Session

from database import get_db
from models import User
from auth import require_verified_user
from fixed_asset_testing_engine import run_fixed_asset_testing, FixedAssetTestingConfig
from shared.rate_limits import limiter, RATE_LIMIT_AUDIT
from shared.testing_route import run_single_file_testing

router = APIRouter(tags=["fixed_asset_testing"])


@router.post("/audit/fixed-assets")
@limiter.limit(RATE_LIMIT_AUDIT)
async def audit_fixed_assets(
    request: Request,
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
        tool_name="fixed_asset_testing", mapping_key="fixed_asset_testing",
        log_label="fixed asset", error_key="fixed_asset_testing_error",
        run_engine=lambda rows, cols, mapping, fn: run_fixed_asset_testing(
            rows=rows, column_names=cols,
            config=FixedAssetTestingConfig(), column_mapping=mapping,
        ),
    )
