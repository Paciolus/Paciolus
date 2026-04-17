"""
Depreciation Routes (Sprint 626).

Form-input only — zero-storage compliant. Generates book + MACRS depreciation
schedules with optional book-vs-tax timing reconciliation, and a CSV export.
"""

from __future__ import annotations

import csv
import io
import logging
from decimal import Decimal, InvalidOperation
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from auth import User, require_verified_user
from depreciation_engine import (
    AssetConfig,
    BookMethod,
    DepreciationInputError,
    MacrsConvention,
    MacrsSystem,
    generate_depreciation_schedule,
)
from shared.error_messages import sanitize_error
from shared.rate_limits import RATE_LIMIT_AUDIT, limiter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["depreciation"])


# =============================================================================
# Request / response schemas
# =============================================================================


class DepreciationRequest(BaseModel):
    asset_name: str = Field(..., min_length=1, max_length=200)
    cost: str = Field(..., min_length=1, max_length=20)
    salvage_value: str = Field(default="0", max_length=20)
    useful_life_years: int = Field(..., ge=1, le=50)
    placed_in_service_year: Optional[int] = Field(default=None, ge=1900, le=2100)
    placed_in_service_quarter: Literal[1, 2, 3, 4] = 1
    placed_in_service_month: int = Field(default=1, ge=1, le=12)
    book_method: Literal[
        "straight_line",
        "declining_balance",
        "sum_of_years_digits",
        "units_of_production",
    ] = "straight_line"
    db_factor: str = Field(default="2", max_length=10)
    units_total: Optional[str] = Field(default=None, max_length=20)
    units_per_year: list[str] = Field(default_factory=list, max_length=50)
    macrs_system: Optional[Literal["gds_200db", "gds_150db", "gds_sl"]] = None
    macrs_property_class: Optional[int] = None
    macrs_convention: Literal["half_year", "mid_quarter", "mid_month"] = "half_year"
    tax_rate: str = Field(default="0.21", max_length=10)


class DepreciationResponse(BaseModel):
    inputs: dict
    book_schedule: list[dict]
    tax_schedule: list[dict]
    book_tax_comparison: list[dict]
    total_book_depreciation: str
    total_tax_depreciation: str
    cumulative_deferred_tax: str


# =============================================================================
# Helpers
# =============================================================================


def _to_decimal(field_name: str, raw: str) -> Decimal:
    try:
        return Decimal(raw)
    except (InvalidOperation, ValueError, TypeError):
        raise HTTPException(status_code=400, detail=f"Invalid numeric value for {field_name}: {raw!r}")


def _build_config(payload: DepreciationRequest) -> AssetConfig:
    units_per_year = [_to_decimal("units_per_year", u) for u in payload.units_per_year]
    return AssetConfig(
        asset_name=payload.asset_name,
        cost=_to_decimal("cost", payload.cost),
        salvage_value=_to_decimal("salvage_value", payload.salvage_value),
        useful_life_years=payload.useful_life_years,
        placed_in_service_year=payload.placed_in_service_year,
        placed_in_service_quarter=payload.placed_in_service_quarter,
        placed_in_service_month=payload.placed_in_service_month,
        book_method=BookMethod(payload.book_method),
        db_factor=_to_decimal("db_factor", payload.db_factor),
        units_total=_to_decimal("units_total", payload.units_total) if payload.units_total else None,
        units_per_year=units_per_year,
        macrs_system=MacrsSystem(payload.macrs_system) if payload.macrs_system else None,
        macrs_property_class=payload.macrs_property_class,
        macrs_convention=MacrsConvention(payload.macrs_convention),
        tax_rate=_to_decimal("tax_rate", payload.tax_rate),
    )


# =============================================================================
# Endpoints
# =============================================================================


@router.post("/audit/depreciation", response_model=DepreciationResponse)
@limiter.limit(RATE_LIMIT_AUDIT)
def calculate_depreciation(
    request: Request,
    payload: DepreciationRequest,
    current_user: User = Depends(require_verified_user),
) -> DepreciationResponse:
    """Calculate book + MACRS depreciation schedules from form inputs.

    Zero-storage: nothing persisted. Salvage value is honored under book methods
    and ignored under MACRS (per IRC §168).
    """
    try:
        config = _build_config(payload)
        result = generate_depreciation_schedule(config)
    except DepreciationInputError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (ValueError,) as e:
        logger.exception("Depreciation computation failed")
        raise HTTPException(status_code=400, detail=sanitize_error(e, "audit", "depreciation_error"))

    return DepreciationResponse(**result.to_dict())  # type: ignore[arg-type]


@router.post("/audit/depreciation/export.csv")
@limiter.limit(RATE_LIMIT_AUDIT)
def export_depreciation_csv(
    request: Request,
    payload: DepreciationRequest,
    current_user: User = Depends(require_verified_user),
) -> StreamingResponse:
    """CSV export of the depreciation schedules + book/tax comparison."""
    try:
        config = _build_config(payload)
        result = generate_depreciation_schedule(config)
    except DepreciationInputError as e:
        raise HTTPException(status_code=400, detail=str(e))

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([f"Asset: {config.asset_name}"])
    writer.writerow([])
    writer.writerow(["BOOK SCHEDULE"])
    writer.writerow(
        [
            "Year",
            "Calendar Year",
            "Beginning Book Value",
            "Depreciation",
            "Accumulated Depreciation",
            "Ending Book Value",
        ]
    )
    for entry in result.book_schedule:
        writer.writerow(
            [
                entry.year_index,
                entry.calendar_year if entry.calendar_year else "",
                f"{entry.beginning_book_value}",
                f"{entry.depreciation}",
                f"{entry.accumulated_depreciation}",
                f"{entry.ending_book_value}",
            ]
        )
    writer.writerow(["", "Total", "", f"{result.total_book_depreciation}", "", ""])

    if result.tax_schedule:
        writer.writerow([])
        writer.writerow(["TAX (MACRS) SCHEDULE"])
        writer.writerow(
            [
                "Year",
                "Calendar Year",
                "Beginning Basis",
                "Depreciation",
                "Accumulated Depreciation",
                "Ending Basis",
            ]
        )
        for entry in result.tax_schedule:
            writer.writerow(
                [
                    entry.year_index,
                    entry.calendar_year if entry.calendar_year else "",
                    f"{entry.beginning_book_value}",
                    f"{entry.depreciation}",
                    f"{entry.accumulated_depreciation}",
                    f"{entry.ending_book_value}",
                ]
            )
        writer.writerow(["", "Total", "", f"{result.total_tax_depreciation}", "", ""])

        writer.writerow([])
        writer.writerow(["BOOK vs TAX TIMING"])
        writer.writerow(
            [
                "Year",
                "Book Depreciation",
                "Tax Depreciation",
                "Timing Difference",
                "Deferred Tax Change",
                "Cumulative Deferred Tax",
            ]
        )
        for row in result.book_tax_comparison:
            writer.writerow(
                [
                    row.year_index,
                    f"{row.book_depreciation}",
                    f"{row.tax_depreciation}",
                    f"{row.timing_difference}",
                    f"{row.deferred_tax_change}",
                    f"{row.cumulative_deferred_tax}",
                ]
            )

    buffer.seek(0)
    safe_name = "".join(c if c.isalnum() else "_" for c in config.asset_name)[:60]
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=depreciation_{safe_name}.csv"},
    )
