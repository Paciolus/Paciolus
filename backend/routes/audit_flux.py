"""
Paciolus API — Audit Flux Routes (Period-over-Period Analysis)
"""

import asyncio
import logging
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from auth import require_verified_user
from database import get_db
from models import User
from security_utils import log_secure_operation
from services.audit.flux_service import run_flux_analysis
from shared.account_extractors import extract_flux_accounts
from shared.diagnostic_response_schemas import FluxAnalysisResponse
from shared.error_messages import sanitize_error
from shared.expectation_evaluation import (
    evaluate_expectations_against_measurements,
    extract_flux_measurements,
)
from shared.materiality_resolver import resolve_materiality
from shared.rate_limits import RATE_LIMIT_AUDIT, limiter
from shared.tool_run_recorder import maybe_record_tool_run
from shared.upload_pipeline import (
    memory_cleanup,
    validate_file_size,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["audit"])


@router.post("/audit/flux", response_model=FluxAnalysisResponse)
@limiter.limit(RATE_LIMIT_AUDIT)
async def flux_analysis(
    request: Request,
    background_tasks: BackgroundTasks,
    current_file: UploadFile = File(...),
    prior_file: UploadFile = File(...),
    materiality: float = Form(0.0),
    engagement_id: Optional[int] = Form(default=None),
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Perform a Flux (Period-over-Period) Analysis."""
    # Sprint 310: Resolve materiality from engagement cascade if not explicitly set
    materiality, _flux_mat_source = resolve_materiality(
        materiality,
        engagement_id,
        current_user.id,
        db,
    )
    log_secure_operation("flux_start", f"Starting Flux Analysis for user {current_user.id}")

    with memory_cleanup():
        try:
            content_curr = await validate_file_size(current_file)
            content_prior = await validate_file_size(prior_file)
            curr_filename = current_file.filename or ""
            prior_filename = prior_file.filename or ""

            flux_result, recon_result = await asyncio.to_thread(
                run_flux_analysis,
                content_curr,
                curr_filename,
                content_prior,
                prior_filename,
                materiality,
            )

            log_secure_operation("flux_complete", f"Flux analysis complete: {len(flux_result.items)} items")

            flux_dict = flux_result.to_dict()
            flagged = extract_flux_accounts({"items": flux_dict.get("items", [])})
            background_tasks.add_task(
                maybe_record_tool_run,
                db,
                engagement_id,
                current_user.id,
                "flux_analysis",
                True,
                None,
                flagged,
            )

            # Sprint 728c: evaluate ISA 520 expectations targeting these
            # flux outputs. No-op when engagement_id is None.
            expectations_evaluated: list[dict[str, Any]] = []
            if engagement_id is not None:
                measurements = extract_flux_measurements(flux_dict)
                expectations_evaluated = evaluate_expectations_against_measurements(
                    db=db,
                    user_id=current_user.id,
                    engagement_id=engagement_id,
                    measurements=measurements,
                )

            return {
                "flux": flux_dict,
                "recon": recon_result.to_dict(),
                "expectations_evaluated": expectations_evaluated,
            }

        except (ValueError, KeyError, TypeError) as e:
            logger.exception("Flux analysis failed")
            maybe_record_tool_run(db, engagement_id, current_user.id, "flux_analysis", False)
            raise HTTPException(status_code=500, detail=sanitize_error(e, "analysis", "flux_error"))
