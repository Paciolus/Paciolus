"""
Paciolus API — Journal Entry Testing Routes
"""
import asyncio
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File, Form, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from security_utils import log_secure_operation
from database import get_db
from models import User
from auth import require_verified_user
from shared.error_messages import sanitize_error
from je_testing_engine import run_je_testing, run_stratified_sampling, preview_sampling_strata, parse_gl_entries, detect_gl_columns
from shared.helpers import validate_file_size, parse_uploaded_file, parse_json_list, parse_json_mapping, memory_cleanup
from shared.rate_limits import limiter, RATE_LIMIT_AUDIT
from shared.testing_route import run_single_file_testing
from shared.testing_response_schemas import JETestingResponse, SamplingResultResponse

router = APIRouter(tags=["je_testing"])


class SamplingPreviewResponse(BaseModel):
    strata: List[dict]
    total_population: int
    stratify_by: List[str]


@router.post("/audit/journal-entries", response_model=JETestingResponse)
@limiter.limit(RATE_LIMIT_AUDIT)
async def audit_journal_entries(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    column_mapping: Optional[str] = Form(default=None),
    engagement_id: Optional[int] = Form(default=None),
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
):
    """Run automated journal entry testing on a General Ledger extract."""
    return await run_single_file_testing(
        file=file, column_mapping=column_mapping,
        engagement_id=engagement_id, current_user=current_user, db=db,
        background_tasks=background_tasks,
        tool_name="journal_entry_testing", mapping_key="je_testing",
        log_label="GL", error_key="je_testing_error",
        run_engine=lambda rows, cols, mapping, fn: run_je_testing(
            rows=rows, column_names=cols, config=None, column_mapping=mapping,
        ),
    )


@router.post("/audit/journal-entries/sample", response_model=SamplingResultResponse)
@limiter.limit(RATE_LIMIT_AUDIT)
async def sample_journal_entries(
    request: Request,
    file: UploadFile = File(...),
    stratify_by: str = Form(default='["account","amount_range"]'),
    sample_rate: float = Form(default=0.10, ge=0.01, le=1.0),
    fixed_per_stratum: Optional[int] = Form(default=None),
    column_mapping: Optional[str] = Form(default=None),
    current_user: User = Depends(require_verified_user),
):
    """Run stratified random sampling on a General Ledger extract."""
    stratify_list = parse_json_list(stratify_by, "je_stratify")
    if stratify_list is None:
        raise HTTPException(status_code=400, detail="Invalid JSON in stratify_by")
    valid_criteria = {"account", "amount_range", "period", "user"}
    for c in stratify_list:
        if c not in valid_criteria:
            raise HTTPException(status_code=400, detail=f"Invalid criterion: {c}. Valid: {valid_criteria}")

    column_mapping_dict = parse_json_mapping(column_mapping, "je_sampling")

    log_secure_operation(
        "je_sampling_upload",
        f"Sampling GL file: {file.filename}, stratify_by={stratify_list}, rate={sample_rate}"
    )

    with memory_cleanup():
        try:
            file_bytes = await validate_file_size(file)
            filename = file.filename or ""

            def _sample():
                column_names, rows = parse_uploaded_file(file_bytes, filename)

                col_detection = detect_gl_columns(column_names)
                if column_mapping_dict:
                    for key, val in column_mapping_dict.items():
                        setattr(col_detection, key, val)

                entries = parse_gl_entries(rows, col_detection)

                return run_stratified_sampling(
                    entries=entries,
                    stratify_by=stratify_list,
                    sample_rate=sample_rate,
                    fixed_per_stratum=fixed_per_stratum,
                )

            sampling_result = await asyncio.to_thread(_sample)

            return sampling_result.to_dict()

        except (ValueError, KeyError, TypeError) as e:
            logger.exception("JE sampling failed")
            raise HTTPException(
                status_code=400,
                detail=sanitize_error(e, "analysis", "je_sampling_error")
            )


@router.post("/audit/journal-entries/sample/preview", response_model=SamplingPreviewResponse)
@limiter.limit(RATE_LIMIT_AUDIT)
async def preview_sampling(
    request: Request,
    file: UploadFile = File(...),
    stratify_by: str = Form(default='["account","amount_range"]'),
    column_mapping: Optional[str] = Form(default=None),
    current_user: User = Depends(require_verified_user),
):
    """Preview stratum counts without running sampling."""
    stratify_list = parse_json_list(stratify_by, "je_preview_stratify")
    if stratify_list is None:
        raise HTTPException(status_code=400, detail="Invalid stratify_by parameter")

    column_mapping_dict = parse_json_mapping(column_mapping, "je_preview")

    with memory_cleanup():
        try:
            file_bytes = await validate_file_size(file)
            filename = file.filename or ""

            def _preview():
                column_names, rows = parse_uploaded_file(file_bytes, filename)

                col_detection = detect_gl_columns(column_names)
                if column_mapping_dict:
                    for key, val in column_mapping_dict.items():
                        setattr(col_detection, key, val)

                entries = parse_gl_entries(rows, col_detection)

                preview = preview_sampling_strata(entries, stratify_list)

                return {
                    "strata": preview,
                    "total_population": sum(s["population_size"] for s in preview),
                    "stratify_by": stratify_list,
                }

            result = await asyncio.to_thread(_preview)

            return result

        except (ValueError, KeyError, TypeError) as e:
            logger.exception("JE preview failed")
            raise HTTPException(
                status_code=400,
                detail=sanitize_error(e, "analysis", "je_preview_error")
            )
