"""
Paciolus API — Benchmark Comparison Routes
"""

from datetime import UTC, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi import Path as PathParam
from pydantic import BaseModel

from auth import require_verified_user
from benchmark_engine import (
    calculate_overall_score,
    compare_ratios_to_benchmarks,
    get_available_industries,
    get_benchmark_set,
    get_benchmark_sources,
    get_percentile_band,
)
from models import Industry, User
from security_utils import log_secure_operation
from shared.rate_limits import RATE_LIMIT_DEFAULT, limiter

router = APIRouter(tags=["benchmarks"])


class BenchmarkDataResponse(BaseModel):
    ratio_name: str
    p10: float
    p25: float
    p50: float
    p75: float
    p90: float
    mean: float
    std_dev: float
    sample_size: int
    source: str
    notes: Optional[str] = None


class BenchmarkSetResponse(BaseModel):
    industry: str
    fiscal_year: int
    benchmarks: dict[str, BenchmarkDataResponse]
    source_attribution: str
    data_quality_score: float
    available_ratios: list[str]


class BenchmarkComparisonResult(BaseModel):
    ratio_name: str
    client_value: float
    percentile: int
    percentile_label: str
    vs_median: float
    vs_mean: float
    position: str
    interpretation: str
    health_indicator: str
    benchmark_median: float
    benchmark_mean: float
    framework_note: Optional[str] = None


class BenchmarkComparisonRequest(BaseModel):
    ratios: dict[str, float]
    industry: str


class BenchmarkComparisonResponse(BaseModel):
    industry: str
    fiscal_year: int
    comparisons: list[BenchmarkComparisonResult]
    overall_score: float
    overall_health: str
    source_attribution: str
    generated_at: str
    disclaimer: str


class BenchmarkSourceInfo(BaseModel):
    name: str
    description: str
    url: Optional[str] = None
    data_type: str
    update_frequency: Optional[str] = None
    note: Optional[str] = None


class BenchmarkSourcesResponse(BaseModel):
    primary_sources: list[BenchmarkSourceInfo]
    coverage: dict
    disclaimer: str
    last_updated: str
    available_industries: list[str]


@router.get("/benchmarks/industries", response_model=list[str])
async def get_benchmark_industries():
    """Get list of industries with available benchmark data."""
    industries = get_available_industries()
    return [ind.value for ind in industries]


@router.get("/benchmarks/sources", response_model=BenchmarkSourcesResponse)
async def get_benchmarks_sources():
    """Get benchmark data source attribution information."""
    sources = get_benchmark_sources()

    primary_sources = [BenchmarkSourceInfo(**src) for src in sources["primary_sources"]]

    available_industries = [ind.value for ind in get_available_industries()]

    return BenchmarkSourcesResponse(
        primary_sources=primary_sources,
        coverage=sources["coverage"],
        disclaimer=sources["disclaimer"],
        last_updated=sources["last_updated"],
        available_industries=available_industries,
    )


@router.get("/benchmarks/{industry}", response_model=BenchmarkSetResponse)
async def get_industry_benchmarks(
    industry: str = PathParam(..., description="Industry type (e.g., 'retail', 'manufacturing')"),
    fiscal_year: int = Query(2025, description="Fiscal year for benchmarks"),
):
    """Get benchmark data for a specific industry."""
    try:
        industry_enum = Industry(industry.lower())
    except ValueError:
        available = [ind.value for ind in get_available_industries()]
        raise HTTPException(
            status_code=404, detail=f"Industry '{industry}' not found. Available industries: {available}"
        )

    benchmark_set = get_benchmark_set(industry_enum, fiscal_year)

    if benchmark_set is None:
        available = [ind.value for ind in get_available_industries()]
        raise HTTPException(
            status_code=404, detail=f"No benchmarks available for '{industry}'. Available industries: {available}"
        )

    benchmarks_dict = {}
    for ratio_name, benchmark in benchmark_set.benchmarks.items():
        benchmarks_dict[ratio_name] = BenchmarkDataResponse(
            ratio_name=benchmark.ratio_name,
            p10=benchmark.p10,
            p25=benchmark.p25,
            p50=benchmark.p50,
            p75=benchmark.p75,
            p90=benchmark.p90,
            mean=benchmark.mean,
            std_dev=benchmark.std_dev,
            sample_size=benchmark.sample_size,
            source=benchmark.source,
            notes=benchmark.notes,
        )

    return BenchmarkSetResponse(
        industry=benchmark_set.industry.value,
        fiscal_year=benchmark_set.fiscal_year,
        benchmarks=benchmarks_dict,
        source_attribution=benchmark_set.source_attribution,
        data_quality_score=benchmark_set.data_quality_score,
        available_ratios=benchmark_set.available_ratios(),
    )


@router.post("/benchmarks/compare", response_model=BenchmarkComparisonResponse)
@limiter.limit(RATE_LIMIT_DEFAULT)
async def compare_to_benchmarks(
    request: Request, payload: BenchmarkComparisonRequest, current_user: User = Depends(require_verified_user)
):
    """Compare client ratios to industry benchmarks."""
    log_secure_operation(
        "benchmark_compare", f"User {current_user.id} comparing {len(payload.ratios)} ratios to {payload.industry}"
    )

    try:
        industry_enum = Industry(payload.industry.lower())
    except ValueError:
        available = [ind.value for ind in get_available_industries()]
        raise HTTPException(
            status_code=400, detail=f"Industry '{payload.industry}' not found. Available industries: {available}"
        )

    benchmark_set = get_benchmark_set(industry_enum)

    if benchmark_set is None:
        available = [ind.value for ind in get_available_industries()]
        raise HTTPException(
            status_code=400,
            detail=f"No benchmarks available for '{payload.industry}'. Available industries: {available}",
        )

    comparisons = compare_ratios_to_benchmarks(payload.ratios, benchmark_set)

    if not comparisons:
        raise HTTPException(
            status_code=400,
            detail=f"None of the provided ratios have benchmarks available for {payload.industry}. "
            f"Available ratios: {benchmark_set.available_ratios()}",
        )

    overall_score = calculate_overall_score(comparisons)
    overall_health = get_percentile_band(overall_score)

    comparison_results = []
    for comp in comparisons:
        comparison_results.append(
            BenchmarkComparisonResult(
                ratio_name=comp.ratio_name,
                client_value=comp.client_value,
                percentile=comp.percentile,
                percentile_label=comp.percentile_label,
                vs_median=comp.vs_median,
                vs_mean=comp.vs_mean,
                position=comp.position,
                interpretation=comp.interpretation,
                health_indicator=comp.health_indicator,
                benchmark_median=comp.benchmark.p50,
                benchmark_mean=comp.benchmark.mean,
            )
        )

    return BenchmarkComparisonResponse(
        industry=benchmark_set.industry.value,
        fiscal_year=benchmark_set.fiscal_year,
        comparisons=comparison_results,
        overall_score=overall_score,
        overall_health=overall_health,
        source_attribution=benchmark_set.source_attribution,
        generated_at=datetime.now(UTC).isoformat(),
        disclaimer=(
            "Benchmark comparisons are based on aggregate industry data and may not reflect "
            "your specific market segment, company size, or regional conditions. "
            "Professional judgment should always be applied when interpreting results."
        ),
    )
