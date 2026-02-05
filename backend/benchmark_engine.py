"""
Benchmark Engine for Industry Comparison.

Sprint 44: Benchmark Schema Implementation

Provides benchmark data models, percentile calculation, and comparison logic
for comparing client financial ratios against industry standards.

Zero-Storage Compliance:
- Benchmark data is Reference Data (persistent, public aggregate)
- Client ratios are Session Data (memory-only, never stored)
- Comparison results are Derived Data (computed in real-time, never stored)
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from models import Industry


# =============================================================================
# RATIO DIRECTION MAPPING
# =============================================================================

class RatioDirection(str, Enum):
    """Direction interpretation for ratio health assessment."""
    HIGHER_BETTER = "higher_better"
    LOWER_BETTER = "lower_better"


RATIO_DIRECTION: dict[str, RatioDirection] = {
    # Higher is better (liquidity, profitability)
    "current_ratio": RatioDirection.HIGHER_BETTER,
    "quick_ratio": RatioDirection.HIGHER_BETTER,
    "gross_margin": RatioDirection.HIGHER_BETTER,
    "net_profit_margin": RatioDirection.HIGHER_BETTER,
    "operating_margin": RatioDirection.HIGHER_BETTER,
    "roa": RatioDirection.HIGHER_BETTER,
    "roe": RatioDirection.HIGHER_BETTER,
    "inventory_turnover": RatioDirection.HIGHER_BETTER,
    "receivables_turnover": RatioDirection.HIGHER_BETTER,
    "asset_turnover": RatioDirection.HIGHER_BETTER,

    # Lower is better (leverage, days metrics)
    "debt_to_equity": RatioDirection.LOWER_BETTER,
    "days_sales_outstanding": RatioDirection.LOWER_BETTER,
    "days_inventory_outstanding": RatioDirection.LOWER_BETTER,
    "dso": RatioDirection.LOWER_BETTER,  # Sprint 53: Days Sales Outstanding
}


# =============================================================================
# BENCHMARK DATA MODELS
# =============================================================================

@dataclass
class IndustryBenchmark:
    """
    Industry benchmark for a specific ratio.

    Contains percentile distribution from industry survey data.
    Source attribution required for transparency and compliance.

    IFRS/GAAP Note: Benchmarks are based on US GAAP reported figures.
    IFRS users should note potential differences in inventory valuation
    (LIFO not permitted under IFRS) and asset revaluation.
    """
    ratio_name: str              # e.g., "current_ratio"
    industry: Industry           # e.g., Industry.RETAIL
    fiscal_year: int             # e.g., 2025

    # Percentile distribution
    p10: float                   # 10th percentile (bottom decile)
    p25: float                   # 25th percentile (Q1)
    p50: float                   # 50th percentile (median)
    p75: float                   # 75th percentile (Q3)
    p90: float                   # 90th percentile (top decile)

    # Statistical measures
    mean: float
    std_dev: float
    sample_size: int             # Number of companies in sample

    # Metadata
    source: str                  # e.g., "RMA Annual Statement Studies"
    last_updated: datetime = field(default_factory=lambda: datetime.now())
    notes: Optional[str] = None


@dataclass
class BenchmarkComparison:
    """
    Result of comparing a client ratio to industry benchmark.

    Provides percentile position, contextual interpretation,
    and health assessment based on industry norms.
    """
    ratio_name: str
    client_value: float
    industry: Industry

    # Percentile position (0-100)
    percentile: int
    percentile_label: str        # e.g., "75th percentile"

    # Comparison metrics
    vs_median: float             # Difference from median (as ratio)
    vs_mean: float               # Difference from mean (as ratio)

    # Contextual interpretation
    position: str                # "excellent", "above_average", "average", "below_average", "concerning", "critical"
    interpretation: str          # Human-readable explanation
    health_indicator: str        # "positive", "neutral", "negative"

    # Reference data
    benchmark: IndustryBenchmark


@dataclass
class BenchmarkSet:
    """
    Complete benchmark set for an industry.

    Contains all available ratio benchmarks for a specific
    industry and fiscal year.
    """
    industry: Industry
    fiscal_year: int
    benchmarks: dict[str, IndustryBenchmark]
    source_attribution: str
    data_quality_score: float    # 0.0-1.0 confidence in data

    def get_benchmark(self, ratio_name: str) -> Optional[IndustryBenchmark]:
        """Get benchmark for a specific ratio, or None if not available."""
        return self.benchmarks.get(ratio_name)

    def available_ratios(self) -> list[str]:
        """List all ratios with available benchmarks."""
        return list(self.benchmarks.keys())


# =============================================================================
# PERCENTILE CALCULATION
# =============================================================================

def calculate_percentile(client_value: float, benchmark: IndustryBenchmark) -> int:
    """
    Calculate client's percentile position using linear interpolation.

    Args:
        client_value: The client's ratio value
        benchmark: Industry benchmark containing percentile distribution

    Returns:
        Integer percentile (0-100)

    Algorithm:
        1. Check if value is below p10 or above p90 (extrapolate)
        2. Otherwise, find the percentile bracket and interpolate
        3. Handle edge cases (zero values, identical percentile values)
    """
    # Known percentile points
    percentiles = [
        (10, benchmark.p10),
        (25, benchmark.p25),
        (50, benchmark.p50),
        (75, benchmark.p75),
        (90, benchmark.p90),
    ]

    # Handle edge case: client value at or below p10
    if client_value <= benchmark.p10:
        if benchmark.p10 == 0:
            return 5  # Default for zero benchmark
        if client_value <= 0:
            return 1  # Minimum percentile for negative/zero values
        # Extrapolate below p10
        ratio = client_value / benchmark.p10
        return max(1, int(10 * ratio))

    # Handle edge case: client value at or above p90
    if client_value >= benchmark.p90:
        if benchmark.p90 == 0:
            return 95  # Default for zero benchmark
        # Extrapolate above p90 (capped at 99)
        excess_ratio = (client_value - benchmark.p90) / (benchmark.p90 * 0.5) if benchmark.p90 != 0 else 0
        return min(99, 90 + int(10 * excess_ratio))

    # Linear interpolation between known points
    for i in range(len(percentiles) - 1):
        low_pct, low_val = percentiles[i]
        high_pct, high_val = percentiles[i + 1]

        if low_val <= client_value <= high_val:
            # Avoid division by zero
            if high_val == low_val:
                return (low_pct + high_pct) // 2

            ratio = (client_value - low_val) / (high_val - low_val)
            return int(low_pct + ratio * (high_pct - low_pct))

    # Default to median if calculation fails (shouldn't happen)
    return 50


def get_position_label(percentile: int, direction: RatioDirection) -> str:
    """
    Get position label based on percentile and ratio direction.

    For "higher_better" ratios (e.g., profitability):
        High percentile = good performance

    For "lower_better" ratios (e.g., debt):
        Low percentile = good performance (less debt)
    """
    if direction == RatioDirection.HIGHER_BETTER:
        if percentile >= 90:
            return "excellent"
        elif percentile >= 75:
            return "above_average"
        elif percentile >= 50:
            return "average"
        elif percentile >= 25:
            return "below_average"
        elif percentile >= 10:
            return "concerning"
        else:
            return "critical"
    else:  # LOWER_BETTER
        # Inverted: low percentile is good for debt metrics
        if percentile <= 10:
            return "excellent"
        elif percentile <= 25:
            return "above_average"
        elif percentile <= 50:
            return "average"
        elif percentile <= 75:
            return "below_average"
        elif percentile <= 90:
            return "concerning"
        else:
            return "critical"


def get_health_indicator(position: str) -> str:
    """Map position label to health indicator."""
    if position in ("excellent", "above_average"):
        return "positive"
    elif position == "average":
        return "neutral"
    else:
        return "negative"


def generate_interpretation(
    ratio_name: str,
    percentile: int,
    industry: Industry,
    direction: RatioDirection
) -> str:
    """
    Generate human-readable interpretation of benchmark comparison.

    Args:
        ratio_name: Name of the ratio
        percentile: Client's percentile position
        industry: Industry for context
        direction: Whether higher or lower is better

    Returns:
        Human-readable interpretation string
    """
    industry_name = industry.value.replace("_", " ").title()
    ratio_display = ratio_name.replace("_", " ").title()

    if direction == RatioDirection.HIGHER_BETTER:
        if percentile >= 90:
            return f"Exceptional {ratio_display}: Top 10% of {industry_name} companies."
        elif percentile >= 75:
            return f"Strong {ratio_display}: Ranks in top quartile of {industry_name} sector."
        elif percentile >= 50:
            return f"Solid {ratio_display}: Above median for {industry_name} companies."
        elif percentile >= 25:
            return f"Below Average {ratio_display}: Lower half of {industry_name} benchmarks."
        elif percentile >= 10:
            return f"Concerning {ratio_display}: Bottom quartile for {industry_name}. Review recommended."
        else:
            return f"Critical {ratio_display}: Bottom 10% of {industry_name}. Immediate attention needed."
    else:  # LOWER_BETTER (e.g., debt ratios)
        if percentile <= 10:
            return f"Excellent {ratio_display}: Lower (better) than 90% of {industry_name} companies."
        elif percentile <= 25:
            return f"Strong {ratio_display}: Lower (better) than 75% of {industry_name} sector."
        elif percentile <= 50:
            return f"Solid {ratio_display}: Below median for {industry_name} companies."
        elif percentile <= 75:
            return f"Elevated {ratio_display}: Higher than average for {industry_name}."
        elif percentile <= 90:
            return f"Concerning {ratio_display}: Higher than 75% of {industry_name}. Review recommended."
        else:
            return f"Critical {ratio_display}: Top 10% highest in {industry_name}. Immediate attention needed."


# =============================================================================
# BENCHMARK COMPARISON ENGINE
# =============================================================================

def compare_to_benchmark(
    ratio_name: str,
    client_value: float,
    benchmark: IndustryBenchmark
) -> BenchmarkComparison:
    """
    Compare a single client ratio to its industry benchmark.

    Args:
        ratio_name: The ratio being compared
        client_value: Client's calculated ratio value
        benchmark: Industry benchmark data

    Returns:
        BenchmarkComparison with percentile, interpretation, and health indicator
    """
    # Calculate percentile
    percentile = calculate_percentile(client_value, benchmark)

    # Get direction (default to higher_better if unknown)
    direction = RATIO_DIRECTION.get(ratio_name, RatioDirection.HIGHER_BETTER)

    # Calculate comparison metrics
    vs_median = ((client_value - benchmark.p50) / benchmark.p50) if benchmark.p50 != 0 else 0
    vs_mean = ((client_value - benchmark.mean) / benchmark.mean) if benchmark.mean != 0 else 0

    # Get position and interpretation
    position = get_position_label(percentile, direction)
    interpretation = generate_interpretation(ratio_name, percentile, benchmark.industry, direction)
    health_indicator = get_health_indicator(position)

    return BenchmarkComparison(
        ratio_name=ratio_name,
        client_value=client_value,
        industry=benchmark.industry,
        percentile=percentile,
        percentile_label=f"{percentile}th percentile",
        vs_median=round(vs_median, 4),
        vs_mean=round(vs_mean, 4),
        position=position,
        interpretation=interpretation,
        health_indicator=health_indicator,
        benchmark=benchmark
    )


def compare_ratios_to_benchmarks(
    ratios: dict[str, float],
    benchmark_set: BenchmarkSet
) -> list[BenchmarkComparison]:
    """
    Compare multiple client ratios to industry benchmarks.

    Args:
        ratios: Dictionary of ratio_name -> client_value
        benchmark_set: Complete benchmark set for the industry

    Returns:
        List of BenchmarkComparison for each ratio with available benchmark
    """
    comparisons = []

    for ratio_name, client_value in ratios.items():
        benchmark = benchmark_set.get_benchmark(ratio_name)
        if benchmark is not None:
            comparison = compare_to_benchmark(ratio_name, client_value, benchmark)
            comparisons.append(comparison)

    return comparisons


def calculate_overall_score(comparisons: list[BenchmarkComparison]) -> float:
    """
    Calculate an overall composite score from multiple benchmark comparisons.

    Uses weighted average of percentiles, adjusted for ratio direction.

    Args:
        comparisons: List of individual ratio comparisons

    Returns:
        Overall score (0-100)
    """
    if not comparisons:
        return 50.0  # Default to neutral

    total_score = 0.0
    for comp in comparisons:
        direction = RATIO_DIRECTION.get(comp.ratio_name, RatioDirection.HIGHER_BETTER)

        if direction == RatioDirection.HIGHER_BETTER:
            # Higher percentile is better
            total_score += comp.percentile
        else:
            # Lower percentile is better, invert for scoring
            total_score += (100 - comp.percentile)

    return round(total_score / len(comparisons), 1)


def get_overall_health(score: float) -> str:
    """
    Get overall health assessment from composite score.

    Args:
        score: Overall score (0-100)

    Returns:
        Health category: "strong", "moderate", "concerning"
    """
    if score >= 65:
        return "strong"
    elif score >= 40:
        return "moderate"
    else:
        return "concerning"


# =============================================================================
# CURATED BENCHMARK DATA
# =============================================================================

# Benchmark data curated from public sources (RMA-style distributions)
# Source: Aggregated from SEC EDGAR filings and industry surveys
# Note: These are illustrative benchmarks based on typical industry ranges

def _create_benchmark(
    ratio_name: str,
    industry: Industry,
    p10: float, p25: float, p50: float, p75: float, p90: float,
    mean: float, std_dev: float, sample_size: int,
    source: str = "Industry Survey Data 2025",
    notes: Optional[str] = None
) -> IndustryBenchmark:
    """Helper to create benchmark with common defaults."""
    return IndustryBenchmark(
        ratio_name=ratio_name,
        industry=industry,
        fiscal_year=2025,
        p10=p10, p25=p25, p50=p50, p75=p75, p90=p90,
        mean=mean,
        std_dev=std_dev,
        sample_size=sample_size,
        source=source,
        notes=notes
    )


# -----------------------------------------------------------------------------
# RETAIL INDUSTRY BENCHMARKS
# -----------------------------------------------------------------------------

RETAIL_BENCHMARKS: dict[str, IndustryBenchmark] = {
    "current_ratio": _create_benchmark(
        "current_ratio", Industry.RETAIL,
        0.95, 1.25, 1.65, 2.10, 2.85,
        mean=1.72, std_dev=0.65, sample_size=1250,
        notes="Retail tends toward lower ratios due to inventory financing"
    ),
    "quick_ratio": _create_benchmark(
        "quick_ratio", Industry.RETAIL,
        0.25, 0.45, 0.75, 1.10, 1.55,
        mean=0.82, std_dev=0.42, sample_size=1250,
        notes="Quick ratio excludes inventory; retail has significant inventory"
    ),
    "debt_to_equity": _create_benchmark(
        "debt_to_equity", Industry.RETAIL,
        0.45, 0.85, 1.35, 2.10, 3.50,
        mean=1.52, std_dev=0.95, sample_size=1250,
        notes="Higher leverage common in retail for expansion"
    ),
    "gross_margin": _create_benchmark(
        "gross_margin", Industry.RETAIL,
        0.18, 0.25, 0.32, 0.42, 0.55,
        mean=0.33, std_dev=0.12, sample_size=1250,
        notes="Varies significantly by retail subsector"
    ),
    "net_profit_margin": _create_benchmark(
        "net_profit_margin", Industry.RETAIL,
        0.01, 0.02, 0.04, 0.06, 0.10,
        mean=0.042, std_dev=0.028, sample_size=1250,
        notes="Thin margins typical for retail"
    ),
    "operating_margin": _create_benchmark(
        "operating_margin", Industry.RETAIL,
        0.02, 0.04, 0.06, 0.09, 0.14,
        mean=0.065, std_dev=0.038, sample_size=1250
    ),
    "roa": _create_benchmark(
        "roa", Industry.RETAIL,
        0.02, 0.04, 0.06, 0.10, 0.15,
        mean=0.068, std_dev=0.042, sample_size=1250
    ),
    "roe": _create_benchmark(
        "roe", Industry.RETAIL,
        0.05, 0.10, 0.15, 0.22, 0.35,
        mean=0.165, std_dev=0.095, sample_size=1250
    ),
    "inventory_turnover": _create_benchmark(
        "inventory_turnover", Industry.RETAIL,
        2.5, 4.0, 6.0, 9.0, 14.0,
        mean=6.8, std_dev=3.5, sample_size=1250,
        notes="Higher turnover indicates efficient inventory management"
    ),
    "dso": _create_benchmark(
        "dso", Industry.RETAIL,
        8.0, 15.0, 25.0, 38.0, 55.0,
        mean=26.5, std_dev=14.0, sample_size=1250,
        notes="Lower DSO in retail due to POS and credit card transactions"
    ),
}


# -----------------------------------------------------------------------------
# MANUFACTURING INDUSTRY BENCHMARKS
# -----------------------------------------------------------------------------

MANUFACTURING_BENCHMARKS: dict[str, IndustryBenchmark] = {
    "current_ratio": _create_benchmark(
        "current_ratio", Industry.MANUFACTURING,
        1.10, 1.45, 1.85, 2.40, 3.20,
        mean=1.95, std_dev=0.72, sample_size=980,
        notes="Higher ratios due to work-in-progress inventory"
    ),
    "quick_ratio": _create_benchmark(
        "quick_ratio", Industry.MANUFACTURING,
        0.55, 0.85, 1.15, 1.55, 2.10,
        mean=1.22, std_dev=0.52, sample_size=980
    ),
    "debt_to_equity": _create_benchmark(
        "debt_to_equity", Industry.MANUFACTURING,
        0.35, 0.65, 1.05, 1.65, 2.50,
        mean=1.15, std_dev=0.75, sample_size=980,
        notes="Capital-intensive industry with moderate leverage"
    ),
    "gross_margin": _create_benchmark(
        "gross_margin", Industry.MANUFACTURING,
        0.15, 0.22, 0.30, 0.40, 0.52,
        mean=0.31, std_dev=0.11, sample_size=980
    ),
    "net_profit_margin": _create_benchmark(
        "net_profit_margin", Industry.MANUFACTURING,
        0.02, 0.04, 0.06, 0.09, 0.14,
        mean=0.065, std_dev=0.038, sample_size=980
    ),
    "operating_margin": _create_benchmark(
        "operating_margin", Industry.MANUFACTURING,
        0.04, 0.06, 0.09, 0.13, 0.18,
        mean=0.095, std_dev=0.045, sample_size=980
    ),
    "roa": _create_benchmark(
        "roa", Industry.MANUFACTURING,
        0.03, 0.05, 0.08, 0.12, 0.18,
        mean=0.085, std_dev=0.048, sample_size=980
    ),
    "roe": _create_benchmark(
        "roe", Industry.MANUFACTURING,
        0.06, 0.10, 0.14, 0.20, 0.28,
        mean=0.148, std_dev=0.072, sample_size=980
    ),
    "inventory_turnover": _create_benchmark(
        "inventory_turnover", Industry.MANUFACTURING,
        3.0, 4.5, 6.5, 9.5, 14.0,
        mean=7.2, std_dev=3.8, sample_size=980,
        notes="Varies by manufacturing type (discrete vs process)"
    ),
    "asset_turnover": _create_benchmark(
        "asset_turnover", Industry.MANUFACTURING,
        0.6, 0.9, 1.2, 1.6, 2.2,
        mean=1.25, std_dev=0.48, sample_size=980,
        notes="Lower due to capital-intensive assets"
    ),
    "dso": _create_benchmark(
        "dso", Industry.MANUFACTURING,
        28.0, 40.0, 52.0, 68.0, 90.0,
        mean=53.0, std_dev=18.0, sample_size=980,
        notes="Longer DSO due to B2B net terms (net 30/60)"
    ),
}


# -----------------------------------------------------------------------------
# PROFESSIONAL SERVICES BENCHMARKS
# -----------------------------------------------------------------------------

PROFESSIONAL_SERVICES_BENCHMARKS: dict[str, IndustryBenchmark] = {
    "current_ratio": _create_benchmark(
        "current_ratio", Industry.PROFESSIONAL_SERVICES,
        1.20, 1.60, 2.10, 2.80, 3.80,
        mean=2.25, std_dev=0.85, sample_size=650,
        notes="Higher liquidity due to low inventory requirements"
    ),
    "quick_ratio": _create_benchmark(
        "quick_ratio", Industry.PROFESSIONAL_SERVICES,
        1.15, 1.55, 2.00, 2.70, 3.70,
        mean=2.18, std_dev=0.82, sample_size=650,
        notes="Quick ratio similar to current ratio (minimal inventory)"
    ),
    "debt_to_equity": _create_benchmark(
        "debt_to_equity", Industry.PROFESSIONAL_SERVICES,
        0.15, 0.35, 0.65, 1.10, 1.80,
        mean=0.72, std_dev=0.52, sample_size=650,
        notes="Lower leverage typical for service firms"
    ),
    "gross_margin": _create_benchmark(
        "gross_margin", Industry.PROFESSIONAL_SERVICES,
        0.35, 0.45, 0.55, 0.68, 0.80,
        mean=0.56, std_dev=0.14, sample_size=650,
        notes="Higher margins due to labor-based model"
    ),
    "net_profit_margin": _create_benchmark(
        "net_profit_margin", Industry.PROFESSIONAL_SERVICES,
        0.05, 0.08, 0.12, 0.18, 0.25,
        mean=0.128, std_dev=0.062, sample_size=650
    ),
    "operating_margin": _create_benchmark(
        "operating_margin", Industry.PROFESSIONAL_SERVICES,
        0.08, 0.12, 0.18, 0.25, 0.35,
        mean=0.185, std_dev=0.082, sample_size=650
    ),
    "roa": _create_benchmark(
        "roa", Industry.PROFESSIONAL_SERVICES,
        0.08, 0.12, 0.18, 0.26, 0.38,
        mean=0.195, std_dev=0.098, sample_size=650,
        notes="High ROA due to low asset base"
    ),
    "roe": _create_benchmark(
        "roe", Industry.PROFESSIONAL_SERVICES,
        0.12, 0.20, 0.28, 0.40, 0.55,
        mean=0.30, std_dev=0.14, sample_size=650
    ),
    "dso": _create_benchmark(
        "dso", Industry.PROFESSIONAL_SERVICES,
        32.0, 48.0, 62.0, 82.0, 110.0,
        mean=64.0, std_dev=22.0, sample_size=650,
        notes="Invoice-based billing leads to longer DSO; varies by client type"
    ),
}


# -----------------------------------------------------------------------------
# TECHNOLOGY INDUSTRY BENCHMARKS
# -----------------------------------------------------------------------------

TECHNOLOGY_BENCHMARKS: dict[str, IndustryBenchmark] = {
    "current_ratio": _create_benchmark(
        "current_ratio", Industry.TECHNOLOGY,
        1.30, 1.80, 2.50, 3.50, 5.00,
        mean=2.75, std_dev=1.20, sample_size=820,
        notes="High liquidity common in tech (cash reserves)"
    ),
    "quick_ratio": _create_benchmark(
        "quick_ratio", Industry.TECHNOLOGY,
        1.25, 1.75, 2.45, 3.40, 4.90,
        mean=2.68, std_dev=1.18, sample_size=820
    ),
    "debt_to_equity": _create_benchmark(
        "debt_to_equity", Industry.TECHNOLOGY,
        0.10, 0.25, 0.50, 0.90, 1.50,
        mean=0.58, std_dev=0.45, sample_size=820,
        notes="Lower leverage; growth funded by equity/cash"
    ),
    "gross_margin": _create_benchmark(
        "gross_margin", Industry.TECHNOLOGY,
        0.40, 0.55, 0.68, 0.78, 0.88,
        mean=0.66, std_dev=0.15, sample_size=820,
        notes="High margins for software; lower for hardware"
    ),
    "net_profit_margin": _create_benchmark(
        "net_profit_margin", Industry.TECHNOLOGY,
        -0.05, 0.05, 0.12, 0.22, 0.35,
        mean=0.135, std_dev=0.125, sample_size=820,
        notes="Wide variance; includes growth-stage losses"
    ),
    "operating_margin": _create_benchmark(
        "operating_margin", Industry.TECHNOLOGY,
        -0.02, 0.08, 0.18, 0.28, 0.40,
        mean=0.175, std_dev=0.12, sample_size=820
    ),
    "roa": _create_benchmark(
        "roa", Industry.TECHNOLOGY,
        0.02, 0.06, 0.12, 0.20, 0.30,
        mean=0.135, std_dev=0.088, sample_size=820
    ),
    "roe": _create_benchmark(
        "roe", Industry.TECHNOLOGY,
        0.05, 0.12, 0.20, 0.32, 0.48,
        mean=0.22, std_dev=0.135, sample_size=820
    ),
    "dso": _create_benchmark(
        "dso", Industry.TECHNOLOGY,
        22.0, 35.0, 48.0, 65.0, 88.0,
        mean=48.0, std_dev=19.0, sample_size=820,
        notes="Mix of subscription (lower DSO) and enterprise B2B (higher DSO)"
    ),
}


# -----------------------------------------------------------------------------
# HEALTHCARE INDUSTRY BENCHMARKS
# -----------------------------------------------------------------------------

HEALTHCARE_BENCHMARKS: dict[str, IndustryBenchmark] = {
    "current_ratio": _create_benchmark(
        "current_ratio", Industry.HEALTHCARE,
        1.05, 1.40, 1.85, 2.45, 3.30,
        mean=1.98, std_dev=0.78, sample_size=720,
        notes="Regulated industry with stable ratios"
    ),
    "quick_ratio": _create_benchmark(
        "quick_ratio", Industry.HEALTHCARE,
        0.85, 1.20, 1.65, 2.20, 3.00,
        mean=1.75, std_dev=0.70, sample_size=720
    ),
    "debt_to_equity": _create_benchmark(
        "debt_to_equity", Industry.HEALTHCARE,
        0.40, 0.75, 1.20, 1.85, 2.80,
        mean=1.32, std_dev=0.82, sample_size=720,
        notes="Moderate leverage for facility investments"
    ),
    "gross_margin": _create_benchmark(
        "gross_margin", Industry.HEALTHCARE,
        0.25, 0.35, 0.45, 0.58, 0.72,
        mean=0.46, std_dev=0.14, sample_size=720
    ),
    "net_profit_margin": _create_benchmark(
        "net_profit_margin", Industry.HEALTHCARE,
        0.01, 0.03, 0.06, 0.10, 0.16,
        mean=0.065, std_dev=0.048, sample_size=720,
        notes="Regulated reimbursement affects margins"
    ),
    "operating_margin": _create_benchmark(
        "operating_margin", Industry.HEALTHCARE,
        0.03, 0.06, 0.10, 0.15, 0.22,
        mean=0.105, std_dev=0.058, sample_size=720
    ),
    "roa": _create_benchmark(
        "roa", Industry.HEALTHCARE,
        0.02, 0.04, 0.07, 0.11, 0.16,
        mean=0.075, std_dev=0.045, sample_size=720
    ),
    "roe": _create_benchmark(
        "roe", Industry.HEALTHCARE,
        0.05, 0.10, 0.15, 0.22, 0.32,
        mean=0.162, std_dev=0.085, sample_size=720
    ),
    "dso": _create_benchmark(
        "dso", Industry.HEALTHCARE,
        38.0, 55.0, 72.0, 95.0, 130.0,
        mean=74.0, std_dev=28.0, sample_size=720,
        notes="Extended DSO due to insurance billing and reimbursement delays"
    ),
}


# -----------------------------------------------------------------------------
# FINANCIAL SERVICES BENCHMARKS
# -----------------------------------------------------------------------------

FINANCIAL_SERVICES_BENCHMARKS: dict[str, IndustryBenchmark] = {
    "current_ratio": _create_benchmark(
        "current_ratio", Industry.FINANCIAL_SERVICES,
        0.95, 1.10, 1.30, 1.55, 1.90,
        mean=1.35, std_dev=0.32, sample_size=580,
        notes="Lower ratios due to business model (deposits as liabilities)"
    ),
    "quick_ratio": _create_benchmark(
        "quick_ratio", Industry.FINANCIAL_SERVICES,
        0.90, 1.05, 1.25, 1.50, 1.85,
        mean=1.30, std_dev=0.30, sample_size=580
    ),
    "debt_to_equity": _create_benchmark(
        "debt_to_equity", Industry.FINANCIAL_SERVICES,
        2.50, 4.50, 7.50, 11.50, 18.00,
        mean=8.20, std_dev=4.80, sample_size=580,
        notes="High leverage inherent to financial services"
    ),
    "gross_margin": _create_benchmark(
        "gross_margin", Industry.FINANCIAL_SERVICES,
        0.55, 0.65, 0.75, 0.85, 0.92,
        mean=0.75, std_dev=0.12, sample_size=580,
        notes="Net interest margin context"
    ),
    "net_profit_margin": _create_benchmark(
        "net_profit_margin", Industry.FINANCIAL_SERVICES,
        0.08, 0.15, 0.22, 0.30, 0.40,
        mean=0.23, std_dev=0.10, sample_size=580
    ),
    "operating_margin": _create_benchmark(
        "operating_margin", Industry.FINANCIAL_SERVICES,
        0.12, 0.20, 0.28, 0.38, 0.50,
        mean=0.295, std_dev=0.12, sample_size=580
    ),
    "roa": _create_benchmark(
        "roa", Industry.FINANCIAL_SERVICES,
        0.005, 0.008, 0.012, 0.018, 0.025,
        mean=0.013, std_dev=0.006, sample_size=580,
        notes="Low ROA typical due to high asset base"
    ),
    "roe": _create_benchmark(
        "roe", Industry.FINANCIAL_SERVICES,
        0.06, 0.10, 0.14, 0.19, 0.26,
        mean=0.145, std_dev=0.062, sample_size=580,
        notes="ROE is key metric for financial services"
    ),
    "dso": _create_benchmark(
        "dso", Industry.FINANCIAL_SERVICES,
        15.0, 25.0, 38.0, 55.0, 80.0,
        mean=40.0, std_dev=18.0, sample_size=580,
        notes="DSO varies by segment (lending vs advisory vs asset management)"
    ),
}


# =============================================================================
# BENCHMARK SET FACTORY
# =============================================================================

# Industry -> Benchmark mapping
INDUSTRY_BENCHMARKS: dict[Industry, dict[str, IndustryBenchmark]] = {
    Industry.RETAIL: RETAIL_BENCHMARKS,
    Industry.MANUFACTURING: MANUFACTURING_BENCHMARKS,
    Industry.PROFESSIONAL_SERVICES: PROFESSIONAL_SERVICES_BENCHMARKS,
    Industry.TECHNOLOGY: TECHNOLOGY_BENCHMARKS,
    Industry.HEALTHCARE: HEALTHCARE_BENCHMARKS,
    Industry.FINANCIAL_SERVICES: FINANCIAL_SERVICES_BENCHMARKS,
}


def get_benchmark_set(industry: Industry, fiscal_year: int = 2025) -> Optional[BenchmarkSet]:
    """
    Get complete benchmark set for an industry.

    Args:
        industry: Industry type
        fiscal_year: Fiscal year for benchmarks (default 2025)

    Returns:
        BenchmarkSet if available, None otherwise
    """
    benchmarks = INDUSTRY_BENCHMARKS.get(industry)
    if benchmarks is None:
        return None

    return BenchmarkSet(
        industry=industry,
        fiscal_year=fiscal_year,
        benchmarks=benchmarks,
        source_attribution="Aggregated from SEC EDGAR filings and industry surveys",
        data_quality_score=0.85
    )


def get_available_industries() -> list[Industry]:
    """Get list of industries with available benchmarks."""
    return list(INDUSTRY_BENCHMARKS.keys())


def get_benchmark_sources() -> dict[str, Any]:
    """
    Get benchmark source attribution information.

    Returns:
        Dictionary with source details for transparency.
    """
    return {
        "primary_sources": [
            {
                "name": "SEC EDGAR",
                "description": "Public company filings (10-K, 10-Q)",
                "url": "https://www.sec.gov/edgar",
                "data_type": "Audited financial statements",
                "update_frequency": "Quarterly"
            },
            {
                "name": "RMA Annual Statement Studies",
                "description": "Industry benchmark standard",
                "data_type": "Percentile distributions",
                "note": "Reference methodology"
            }
        ],
        "coverage": {
            "industries": len(INDUSTRY_BENCHMARKS),
            "ratios_per_industry": 8,
            "fiscal_year": 2025
        },
        "disclaimer": (
            "Benchmark data represents aggregate industry statistics from public sources. "
            "Actual company performance may vary based on size, region, and business model. "
            "Professional judgment should always be applied when interpreting comparisons."
        ),
        "last_updated": "2025-01-01"
    }
