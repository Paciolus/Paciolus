"""
Paciolus API — Statistical Sampling Routes (Sprint 268)

Two-phase workflow:
  POST /audit/sampling/design — Upload population, configure params, get selected sample
  POST /audit/sampling/evaluate — Upload completed sample, get projected misstatement + Pass/Fail
"""
import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from auth import require_verified_user
from database import get_db
from models import User
from sampling_engine import SamplingConfig, design_sample, evaluate_sample
from shared.error_messages import sanitize_error
from shared.helpers import (
    maybe_record_tool_run,
    memory_cleanup,
    parse_json_mapping,
    validate_file_size,
)
from shared.rate_limits import RATE_LIMIT_AUDIT, limiter
from shared.testing_response_schemas import SamplingDesignResponse, SamplingEvaluationResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["sampling"])


def _run_design(
    file_bytes: bytes,
    filename: str,
    method: str,
    confidence_level: float,
    tolerable_misstatement: float,
    expected_misstatement: float,
    stratification_threshold: Optional[float],
    sample_size_override: Optional[int],
    column_mapping: Optional[dict[str, str]],
) -> dict:
    """CPU-bound: parse population, calculate, and select sample."""
    config = SamplingConfig(
        method=method,
        confidence_level=confidence_level,
        tolerable_misstatement=tolerable_misstatement,
        expected_misstatement=expected_misstatement,
        stratification_threshold=stratification_threshold,
        sample_size_override=sample_size_override,
    )

    result = design_sample(
        file_bytes=file_bytes,
        filename=filename,
        config=config,
        column_mapping=column_mapping,
    )

    # Convert to dict for JSON serialization
    selected_items = []
    for sel in result.selected_items:
        selected_items.append({
            "row_index": sel.item.row_index,
            "item_id": sel.item.item_id,
            "description": sel.item.description[:200],
            "recorded_amount": round(sel.item.recorded_amount, 2),
            "stratum": sel.item.stratum,
            "selection_method": sel.selection_method,
            "interval_position": (
                round(sel.interval_position, 2)
                if sel.interval_position is not None else None
            ),
        })

    return {
        "method": result.method,
        "confidence_level": result.confidence_level,
        "confidence_factor": round(result.confidence_factor, 4),
        "tolerable_misstatement": round(result.tolerable_misstatement, 2),
        "expected_misstatement": round(result.expected_misstatement, 2),
        "population_size": result.population_size,
        "population_value": result.population_value,
        "sampling_interval": result.sampling_interval,
        "calculated_sample_size": result.calculated_sample_size,
        "actual_sample_size": result.actual_sample_size,
        "high_value_count": result.high_value_count,
        "high_value_total": result.high_value_total,
        "remainder_count": result.remainder_count,
        "remainder_sample_size": result.remainder_sample_size,
        "selected_items": selected_items,
        "random_start": result.random_start,
        "strata_summary": result.strata_summary,
    }


def _run_evaluation(
    file_bytes: bytes,
    filename: str,
    method: str,
    confidence_level: float,
    tolerable_misstatement: float,
    expected_misstatement: float,
    population_value: float,
    sample_size: int,
    sampling_interval: Optional[float],
    column_mapping: Optional[dict[str, str]],
) -> dict:
    """CPU-bound: parse completed sample and evaluate."""
    config = SamplingConfig(
        method=method,
        confidence_level=confidence_level,
        tolerable_misstatement=tolerable_misstatement,
        expected_misstatement=expected_misstatement,
    )

    result = evaluate_sample(
        file_bytes=file_bytes,
        filename=filename,
        config=config,
        population_value=population_value,
        sample_size=sample_size,
        sampling_interval=sampling_interval,
        column_mapping=column_mapping,
    )

    errors_list = []
    for err in result.errors:
        errors_list.append({
            "row_index": err.row_index,
            "item_id": err.item_id,
            "recorded_amount": round(err.recorded_amount, 2),
            "audited_amount": round(err.audited_amount, 2),
            "misstatement": round(err.misstatement, 2),
            "tainting": round(err.tainting, 4),
        })

    return {
        "method": result.method,
        "confidence_level": result.confidence_level,
        "tolerable_misstatement": round(result.tolerable_misstatement, 2),
        "expected_misstatement": round(result.expected_misstatement, 2),
        "population_value": round(result.population_value, 2),
        "sample_size": result.sample_size,
        "sample_value": round(result.sample_value, 2),
        "errors_found": result.errors_found,
        "total_misstatement": round(result.total_misstatement, 2),
        "projected_misstatement": round(result.projected_misstatement, 2),
        "basic_precision": round(result.basic_precision, 2),
        "incremental_allowance": round(result.incremental_allowance, 2),
        "upper_error_limit": round(result.upper_error_limit, 2),
        "conclusion": result.conclusion,
        "conclusion_detail": result.conclusion_detail,
        "errors": errors_list,
        "taintings_ranked": [round(t, 4) for t in result.taintings_ranked],
    }


@router.post("/audit/sampling/design", response_model=SamplingDesignResponse)
@limiter.limit(RATE_LIMIT_AUDIT)
async def sampling_design(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    method: str = Form(default="mus"),
    confidence_level: float = Form(default=0.95),
    tolerable_misstatement: float = Form(default=0.0),
    expected_misstatement: float = Form(default=0.0),
    stratification_threshold: Optional[float] = Form(default=None),
    sample_size_override: Optional[int] = Form(default=None),
    column_mapping: Optional[str] = Form(default=None),
    engagement_id: Optional[int] = Form(default=None),
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
):
    """Design and select a statistical sample from an uploaded population.

    ISA 530 / PCAOB AS 2315: Statistical sampling for substantive tests.

    Phase 1 of 2: Upload population data + configure parameters.
    Returns selected sample items for the auditor to test.
    """
    from shared.testing_route import enforce_tool_access
    enforce_tool_access(current_user, "statistical_sampling")

    if method not in ("mus", "random"):
        raise HTTPException(status_code=422, detail="Method must be 'mus' or 'random'")
    if confidence_level < 0.50 or confidence_level > 0.99:
        raise HTTPException(
            status_code=422, detail="Confidence level must be between 0.50 and 0.99"
        )

    file_bytes = await validate_file_size(file)
    mapping = parse_json_mapping(column_mapping, "sampling_design_mapping")

    try:
        with memory_cleanup():
            result = await asyncio.to_thread(
                _run_design,
                file_bytes, file.filename or "population.csv",
                method, confidence_level,
                tolerable_misstatement, expected_misstatement,
                stratification_threshold, sample_size_override,
                mapping,
            )

        background_tasks.add_task(
            maybe_record_tool_run,
            db, engagement_id, current_user.id,
            "statistical_sampling", True, None,
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except HTTPException:
        raise
    except (TypeError, KeyError, OSError) as e:
        logger.exception("Sampling design failed")
        raise HTTPException(
            status_code=500,
            detail=sanitize_error(e, "analysis", "sampling_design_error"),
        )


@router.post("/audit/sampling/evaluate", response_model=SamplingEvaluationResponse)
@limiter.limit(RATE_LIMIT_AUDIT)
async def sampling_evaluate(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    method: str = Form(default="mus"),
    confidence_level: float = Form(default=0.95),
    tolerable_misstatement: float = Form(default=0.0),
    expected_misstatement: float = Form(default=0.0),
    population_value: float = Form(default=0.0),
    sample_size: int = Form(default=0),
    sampling_interval: Optional[float] = Form(default=None),
    column_mapping: Optional[str] = Form(default=None),
    engagement_id: Optional[int] = Form(default=None),
    current_user: User = Depends(require_verified_user),
    db: Session = Depends(get_db),
):
    """Evaluate a completed sample and determine Pass/Fail.

    ISA 530 / PCAOB AS 2315: Sample evaluation using Stringer bound (MUS)
    or ratio estimation (random).

    Phase 2 of 2: Upload completed sample with audited amounts.
    Returns projected misstatement, upper error limit, and conclusion.
    """
    if method not in ("mus", "random"):
        raise HTTPException(status_code=422, detail="Method must be 'mus' or 'random'")
    if population_value <= 0:
        raise HTTPException(
            status_code=422, detail="Population value must be positive"
        )
    if sample_size <= 0:
        raise HTTPException(
            status_code=422, detail="Sample size must be positive"
        )

    file_bytes = await validate_file_size(file)
    mapping = parse_json_mapping(column_mapping, "sampling_evaluate_mapping")

    try:
        with memory_cleanup():
            result = await asyncio.to_thread(
                _run_evaluation,
                file_bytes, file.filename or "sample.csv",
                method, confidence_level,
                tolerable_misstatement, expected_misstatement,
                population_value, sample_size,
                sampling_interval, mapping,
            )

        background_tasks.add_task(
            maybe_record_tool_run,
            db, engagement_id, current_user.id,
            "statistical_sampling", True, None,
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except HTTPException:
        raise
    except (TypeError, KeyError, OSError) as e:
        logger.exception("Sampling evaluation failed")
        raise HTTPException(
            status_code=500,
            detail=sanitize_error(e, "analysis", "sampling_evaluate_error"),
        )
