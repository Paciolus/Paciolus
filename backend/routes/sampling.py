"""
Paciolus API — Statistical Sampling Routes (Sprint 268)

Two-phase workflow:
  POST /audit/sampling/design — Upload population, configure params, get selected sample
  POST /audit/sampling/evaluate — Upload completed sample, get projected misstatement + Pass/Fail
"""

import asyncio
import logging
import math
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from auth import require_verified_user
from database import get_db
from models import User
from sampling_engine import InsufficientPopulationResult, SamplingConfig, design_sample, evaluate_sample
from shared.error_messages import sanitize_error
from shared.helpers import parse_json_mapping
from shared.rate_limits import RATE_LIMIT_AUDIT, limiter
from shared.testing_response_schemas import SamplingDesignResponse, SamplingEvaluationResponse
from shared.tool_run_recorder import maybe_record_tool_run
from shared.upload_pipeline import (
    memory_cleanup,
    validate_file_size,
)

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

    # Handle insufficient population
    if isinstance(result, InsufficientPopulationResult):
        return {
            "status": result.status,
            "non_zero_count": result.non_zero_count,
            "minimum_required": result.minimum_required,
            "total_row_count": result.total_row_count,
            "message": result.message,
        }

    # Convert to dict for JSON serialization
    selected_items = []
    for sel in result.selected_items:
        selected_items.append(
            {
                "row_index": sel.item.row_index,
                "item_id": sel.item.item_id,
                "description": sel.item.description[:200],
                "recorded_amount": round(sel.item.recorded_amount, 2),
                "stratum": sel.item.stratum,
                "selection_method": sel.selection_method,
                "interval_position": (round(sel.interval_position, 2) if sel.interval_position is not None else None),
            }
        )

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
        errors_list.append(
            {
                "row_index": err.row_index,
                "item_id": err.item_id,
                "recorded_amount": round(err.recorded_amount, 2),
                "audited_amount": round(err.audited_amount, 2),
                "misstatement": round(err.misstatement, 2),
                "tainting": round(err.tainting, 4),
            }
        )

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
        "skipped_missing_audited": result.skipped_missing_audited,
        "evaluated_count": result.evaluated_count,
        "missing_audited_warning": result.missing_audited_warning,
        # Sprint 825 (S6): understatement side, evaluated separately.
        "overstatement_errors_found": result.overstatement_errors_found,
        "understatement_errors_found": result.understatement_errors_found,
        "total_overstatement": round(result.total_overstatement, 2),
        "total_understatement": round(result.total_understatement, 2),
        "understatement_projected_misstatement": round(result.understatement_projected_misstatement, 2),
        "understatement_basic_precision": round(result.understatement_basic_precision, 2),
        "understatement_incremental_allowance": round(result.understatement_incremental_allowance, 2),
        "understatement_upper_error_limit": round(result.understatement_upper_error_limit, 2),
        "understatement_taintings_ranked": [round(t, 4) for t in result.understatement_taintings_ranked],
    }


def _require_finite(**values: Optional[float]) -> None:
    """Reject nan/inf form values (Sprint 824).

    FastAPI accepts "nan" and "inf" for float fields. They either flowed into
    the result and broke JSON serialisation (a 500 after the handler returned)
    or silently became 0 — neither is an answer an auditor should get.
    """
    bad = [name for name, value in values.items() if value is not None and not math.isfinite(value)]
    if bad:
        raise HTTPException(status_code=422, detail=f"Must be a finite number: {', '.join(sorted(bad))}")


@router.post("/audit/sampling/design", response_model=SamplingDesignResponse)
@limiter.limit(RATE_LIMIT_AUDIT)
async def sampling_design(
    request: Request,
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
) -> dict[str, object]:
    """Design and select a statistical sample from an uploaded population.

    ISA 530 / PCAOB AS 2315: Statistical sampling for substantive tests.

    Phase 1 of 2: Upload population data + configure parameters.
    Returns selected sample items for the auditor to test.
    """
    from shared.entitlement_checks import check_upload_limit
    from shared.testing_route import enforce_tool_access

    enforce_tool_access(current_user, "statistical_sampling", db)
    # Sprint 678: count sampling uploads toward the monthly quota.
    check_upload_limit(current_user, db)

    _require_finite(
        confidence_level=confidence_level,
        tolerable_misstatement=tolerable_misstatement,
        expected_misstatement=expected_misstatement,
        stratification_threshold=stratification_threshold,
    )
    if method not in ("mus", "random"):
        raise HTTPException(status_code=422, detail="Method must be 'mus' or 'random'")
    if confidence_level < 0.50 or confidence_level > 0.99:
        raise HTTPException(status_code=422, detail="Confidence level must be between 0.50 and 0.99")

    file_bytes = await validate_file_size(file)
    mapping = parse_json_mapping(column_mapping, "sampling_design_mapping")

    try:
        with memory_cleanup():
            result = await asyncio.to_thread(
                _run_design,
                file_bytes,
                file.filename or "population.csv",
                method,
                confidence_level,
                tolerable_misstatement,
                expected_misstatement,
                stratification_threshold,
                sample_size_override,
                mapping,
            )

        maybe_record_tool_run(
            db,
            engagement_id,
            current_user.id,
            "statistical_sampling",
            True,
            None,
            consumes_upload=True,
        )

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail=sanitize_error(e, "analysis", "sampling_design_validation", allow_passthrough=True),
        )
    except ArithmeticError as e:
        # Sprint 814: a malformed amount in the uploaded sample raises
        # decimal.InvalidOperation, which fell through to an unhandled 500.
        # Not passthrough — the decimal module's message is not user copy.
        logger.warning("Sampling input rejected [%s]", type(e).__name__)  # Sprint 840 (S6): type only
        raise HTTPException(
            status_code=422,
            detail=sanitize_error(e, "analysis", "sampling_design_validation"),
        )
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
) -> dict[str, object]:
    """Evaluate a completed sample and determine Pass/Fail.

    ISA 530 / PCAOB AS 2315: Sample evaluation using Stringer bound (MUS)
    or ratio estimation (random).

    Phase 2 of 2: Upload completed sample with audited amounts.
    Returns projected misstatement, upper error limit, and conclusion.
    """
    _require_finite(
        confidence_level=confidence_level,
        tolerable_misstatement=tolerable_misstatement,
        expected_misstatement=expected_misstatement,
        population_value=population_value,
        sampling_interval=sampling_interval,
    )
    if method not in ("mus", "random"):
        raise HTTPException(status_code=422, detail="Method must be 'mus' or 'random'")
    if population_value <= 0:
        raise HTTPException(status_code=422, detail="Population value must be positive")
    if sample_size <= 0:
        raise HTTPException(status_code=422, detail="Sample size must be positive")

    file_bytes = await validate_file_size(file)
    mapping = parse_json_mapping(column_mapping, "sampling_evaluate_mapping")

    try:
        with memory_cleanup():
            result = await asyncio.to_thread(
                _run_evaluation,
                file_bytes,
                file.filename or "sample.csv",
                method,
                confidence_level,
                tolerable_misstatement,
                expected_misstatement,
                population_value,
                sample_size,
                sampling_interval,
                mapping,
            )

        maybe_record_tool_run(
            db,
            engagement_id,
            current_user.id,
            "statistical_sampling",
            True,
            None,
        )

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail=sanitize_error(e, "analysis", "sampling_evaluate_validation", allow_passthrough=True),
        )
    except ArithmeticError as e:
        # Sprint 814: a malformed amount in the uploaded sample raises
        # decimal.InvalidOperation, which fell through to an unhandled 500.
        # Not passthrough — the decimal module's message is not user copy.
        logger.warning("Sampling input rejected [%s]", type(e).__name__)  # Sprint 840 (S6): type only
        raise HTTPException(
            status_code=422,
            detail=sanitize_error(e, "analysis", "sampling_evaluate_validation"),
        )
    except HTTPException:
        raise
    except (TypeError, KeyError, OSError) as e:
        logger.exception("Sampling evaluation failed")
        raise HTTPException(
            status_code=500,
            detail=sanitize_error(e, "analysis", "sampling_evaluate_error"),
        )
