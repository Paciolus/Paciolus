"""
Paciolus API — Journal Entry Testing Routes
"""

import asyncio
import json
import logging
from datetime import date
from typing import Any, Optional

logger = logging.getLogger(__name__)

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import require_verified_user
from database import get_db
from je_testing_engine import (
    JETestingConfig,
    detect_gl_columns,
    parse_gl_entries,
    preview_sampling_strata,
    run_je_testing,
    run_stratified_sampling,
)
from models import User
from security_utils import log_secure_operation
from shared.account_extractors import extract_je_accounts
from shared.error_messages import sanitize_error
from shared.helpers import (
    parse_json_list,
    parse_json_mapping,
)
from shared.holiday_calendar import us_federal_holiday_names
from shared.rate_limits import RATE_LIMIT_AUDIT, limiter
from shared.testing_response_schemas import JETestingResponse, SamplingResultResponse
from shared.testing_route import run_single_file_testing
from shared.upload_pipeline import (
    memory_cleanup,
    parse_uploaded_file,
    validate_file_size,
)

router = APIRouter(tags=["je_testing"])


class SamplingPreviewResponse(BaseModel):
    strata: list[dict]
    total_population: int
    stratify_by: list[str]


_MAX_CLOSURE_DATES = 60


def _parse_holiday_calendar(raw: Optional[str]) -> Optional[JETestingConfig]:
    """Build a JE config from the auditor's holiday calendar for this client.

    Sprint 831 (CEO decision 3). ``raw`` is JSON:
    ``{"exclude": ["Columbus Day"], "closed_dates": ["2025-12-24"]}``.
    ``exclude`` names statutory holidays the client works (5 U.S.C. 6103 list);
    ``closed_dates`` adds client-specific closure days. Anything malformed is a
    400 rather than ignored: silently dropping the auditor's calendar would
    change which entries are flagged without telling them.
    """
    if not raw:
        return None
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="holiday_calendar must be valid JSON.")
    if not isinstance(payload, dict) or set(payload) - {"exclude", "closed_dates"}:
        raise HTTPException(status_code=400, detail="holiday_calendar accepts only 'exclude' and 'closed_dates'.")

    exclude = payload.get("exclude") or []
    known = set(us_federal_holiday_names())
    if not isinstance(exclude, list) or any(not isinstance(n, str) or n not in known for n in exclude):
        raise HTTPException(
            status_code=400,
            detail=f"holiday_calendar.exclude must list US federal holiday names: {', '.join(sorted(known))}.",
        )

    closed = payload.get("closed_dates") or []
    if not isinstance(closed, list) or len(closed) > _MAX_CLOSURE_DATES:
        raise HTTPException(
            status_code=400,
            detail=f"holiday_calendar.closed_dates must be a list of at most {_MAX_CLOSURE_DATES} dates.",
        )
    try:
        closed_dates = tuple(sorted({date.fromisoformat(d) for d in closed}))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="holiday_calendar.closed_dates must be ISO dates (YYYY-MM-DD).")

    return JETestingConfig(
        holiday_excluded_names=tuple(dict.fromkeys(exclude)),
        holiday_additional_dates=closed_dates,
    )


@router.post("/audit/journal-entries", response_model=JETestingResponse)
@limiter.limit(RATE_LIMIT_AUDIT)
async def audit_journal_entries(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    column_mapping: Optional[str] = Form(default=None),
    engagement_id: Optional[int] = Form(default=None),
    holiday_calendar: Optional[str] = Form(default=None),
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Run automated journal entry testing on a General Ledger extract."""
    config = _parse_holiday_calendar(holiday_calendar)
    return await run_single_file_testing(
        file=file,
        column_mapping=column_mapping,
        engagement_id=engagement_id,
        current_user=current_user,
        db=db,
        background_tasks=background_tasks,
        tool_name="journal_entry_testing",
        mapping_key="je_testing",
        log_label="GL",
        error_key="je_testing_error",
        run_engine=lambda rows, cols, mapping, fn: run_je_testing(
            rows=rows,
            column_names=cols,
            config=config,
            column_mapping=mapping,
        ),
        extract_accounts=extract_je_accounts,
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
) -> dict[str, Any]:
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
        "je_sampling_upload", f"Sampling GL file: {file.filename}, stratify_by={stratify_list}, rate={sample_rate}"
    )

    with memory_cleanup():
        try:
            file_bytes = await validate_file_size(file)
            filename = file.filename or ""

            def _sample() -> Any:
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

            return sampling_result.to_dict()  # type: ignore[no-any-return]

        except (ValueError, KeyError, TypeError) as e:
            logger.exception("JE sampling failed")
            raise HTTPException(status_code=400, detail=sanitize_error(e, "analysis", "je_sampling_error"))


@router.post("/audit/journal-entries/sample/preview", response_model=SamplingPreviewResponse)
@limiter.limit(RATE_LIMIT_AUDIT)
async def preview_sampling(
    request: Request,
    file: UploadFile = File(...),
    stratify_by: str = Form(default='["account","amount_range"]'),
    column_mapping: Optional[str] = Form(default=None),
    current_user: User = Depends(require_verified_user),
) -> dict[str, Any]:
    """Preview stratum counts without running sampling."""
    stratify_list = parse_json_list(stratify_by, "je_preview_stratify")
    if stratify_list is None:
        raise HTTPException(status_code=400, detail="Invalid stratify_by parameter")

    column_mapping_dict = parse_json_mapping(column_mapping, "je_preview")

    with memory_cleanup():
        try:
            file_bytes = await validate_file_size(file)
            filename = file.filename or ""

            def _preview() -> dict[str, Any]:
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
            raise HTTPException(status_code=400, detail=sanitize_error(e, "analysis", "je_preview_error"))
