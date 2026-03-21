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
from shared.helpers import maybe_record_tool_run, memory_cleanup, validate_file_size
from shared.materiality_resolver import resolve_materiality
from shared.rate_limits import RATE_LIMIT_AUDIT, limiter

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

            return {"flux": flux_dict, "recon": recon_result.to_dict()}

        except (ValueError, KeyError, TypeError) as e:
            logger.exception("Flux analysis failed")
            maybe_record_tool_run(db, engagement_id, current_user.id, "flux_analysis", False)
            raise HTTPException(status_code=500, detail=sanitize_error(e, "analysis", "flux_error"))
