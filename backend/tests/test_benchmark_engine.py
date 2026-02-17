"""
Tests for Benchmark Engine.

Sprint 44: Benchmark Schema Implementation

Tests cover:
- Data model integrity
- Percentile calculation accuracy
- Position label generation
- Interpretation generation
- Benchmark comparison engine
- Industry benchmark data
"""

# Import from parent directory
import sys

import pytest

sys.path.insert(0, '..')

from benchmark_engine import (
    FINANCIAL_SERVICES_BENCHMARKS,
    HEALTHCARE_BENCHMARKS,
    MANUFACTURING_BENCHMARKS,
    PROFESSIONAL_SERVICES_BENCHMARKS,
    RATIO_DIRECTION,
    # Benchmark data
    RETAIL_BENCHMARKS,
    TECHNOLOGY_BENCHMARKS,
    BenchmarkComparison,
    # Data models
    IndustryBenchmark,
    # Enums and constants
    RatioDirection,
    calculate_overall_score,
    calculate_percentile,
    compare_ratios_to_benchmarks,
    # Comparison functions
    compare_to_benchmark,
    generate_interpretation,
    get_available_industries,
    # Data access functions
    get_benchmark_set,
    get_benchmark_sources,
    get_health_indicator,
    get_overall_health,
    get_position_label,
)
from models import Industry

# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def sample_benchmark():
    """Create a sample benchmark for testing."""
    return IndustryBenchmark(
        ratio_name="current_ratio",
        industry=Industry.RETAIL,
        fiscal_year=2025,
        p10=0.95,
        p25=1.25,
        p50=1.65,
        p75=2.10,
        p90=2.85,
        mean=1.72,
        std_dev=0.65,
        sample_size=1250,
        source="Test Data",
        notes="Test benchmark"
    )


@pytest.fixture
def sample_benchmark_set():
    """Create a sample benchmark set for testing."""
    return get_benchmark_set(Industry.RETAIL, 2025)


# =============================================================================
# TEST: DATA MODELS
# =============================================================================

class TestIndustryBenchmark:
    """Tests for IndustryBenchmark dataclass."""

    def test_create_benchmark(self, sample_benchmark):
        """Test benchmark creation with all fields."""
        assert sample_benchmark.ratio_name == "current_ratio"
        assert sample_benchmark.industry == Industry.RETAIL
        assert sample_benchmark.fiscal_year == 2025
        assert sample_benchmark.p50 == 1.65
        assert sample_benchmark.mean == 1.72
        assert sample_benchmark.sample_size == 1250

    def test_benchmark_percentile_ordering(self, sample_benchmark):
        """Test that percentiles are in ascending order."""
        assert sample_benchmark.p10 < sample_benchmark.p25
        assert sample_benchmark.p25 < sample_benchmark.p50
        assert sample_benchmark.p50 < sample_benchmark.p75
        assert sample_benchmark.p75 < sample_benchmark.p90

    def test_benchmark_optional_notes(self):
        """Test benchmark can be created without notes."""
        benchmark = IndustryBenchmark(
            ratio_name="test",
            industry=Industry.RETAIL,
            fiscal_year=2025,
            p10=1.0, p25=1.5, p50=2.0, p75=2.5, p90=3.0,
            mean=2.0, std_dev=0.5, sample_size=100,
            source="Test"
        )
        assert benchmark.notes is None


class TestBenchmarkComparison:
    """Tests for BenchmarkComparison dataclass."""

    def test_create_comparison(self, sample_benchmark):
        """Test comparison creation."""
        comparison = BenchmarkComparison(
            ratio_name="current_ratio",
            client_value=1.80,
            industry=Industry.RETAIL,
            percentile=58,
            percentile_label="58th percentile",
            vs_median=0.0909,
            vs_mean=0.0465,
            position="average",
            interpretation="Solid performance",
            health_indicator="neutral",
            benchmark=sample_benchmark
        )
        assert comparison.percentile == 58
        assert comparison.position == "average"
        assert comparison.health_indicator == "neutral"


class TestBenchmarkSet:
    """Tests for BenchmarkSet dataclass."""

    def test_get_benchmark_exists(self, sample_benchmark_set):
        """Test getting a benchmark that exists."""
        benchmark = sample_benchmark_set.get_benchmark("current_ratio")
        assert benchmark is not None
        assert benchmark.ratio_name == "current_ratio"

    def test_get_benchmark_not_exists(self, sample_benchmark_set):
        """Test getting a benchmark that doesn't exist."""
        benchmark = sample_benchmark_set.get_benchmark("nonexistent_ratio")
        assert benchmark is None

    def test_available_ratios(self, sample_benchmark_set):
        """Test listing available ratios."""
        ratios = sample_benchmark_set.available_ratios()
        assert "current_ratio" in ratios
        assert "gross_margin" in ratios
        assert len(ratios) >= 8  # At least 8 ratios


# =============================================================================
# TEST: RATIO DIRECTION
# =============================================================================

class TestRatioDirection:
    """Tests for ratio direction mapping."""

    def test_higher_better_ratios(self):
        """Test that profitability ratios are higher_better."""
        assert RATIO_DIRECTION["current_ratio"] == RatioDirection.HIGHER_BETTER
        assert RATIO_DIRECTION["gross_margin"] == RatioDirection.HIGHER_BETTER
        assert RATIO_DIRECTION["roa"] == RatioDirection.HIGHER_BETTER
        assert RATIO_DIRECTION["roe"] == RatioDirection.HIGHER_BETTER

    def test_lower_better_ratios(self):
        """Test that leverage ratios are lower_better."""
        assert RATIO_DIRECTION["debt_to_equity"] == RatioDirection.LOWER_BETTER
        assert RATIO_DIRECTION["days_sales_outstanding"] == RatioDirection.LOWER_BETTER

    def test_all_ratios_mapped(self):
        """Test that common ratios have direction mapping."""
        expected_ratios = [
            "current_ratio", "quick_ratio", "debt_to_equity",
            "gross_margin", "net_profit_margin", "operating_margin",
            "roa", "roe"
        ]
        for ratio in expected_ratios:
            assert ratio in RATIO_DIRECTION


# =============================================================================
# TEST: PERCENTILE CALCULATION
# =============================================================================

class TestCalculatePercentile:
    """Tests for percentile calculation function."""

    def test_value_at_median(self, sample_benchmark):
        """Test value exactly at median (p50)."""
        percentile = calculate_percentile(1.65, sample_benchmark)
        assert percentile == 50

    def test_value_at_p25(self, sample_benchmark):
        """Test value exactly at p25."""
        percentile = calculate_percentile(1.25, sample_benchmark)
        assert percentile == 25

    def test_value_at_p75(self, sample_benchmark):
        """Test value exactly at p75."""
        percentile = calculate_percentile(2.10, sample_benchmark)
        assert percentile == 75

    def test_value_between_percentiles(self, sample_benchmark):
        """Test interpolation between percentile points."""
        # Value between p50 (1.65) and p75 (2.10)
        percentile = calculate_percentile(1.875, sample_benchmark)
        # Should be between 50 and 75
        assert 50 < percentile < 75

    def test_value_below_p10(self, sample_benchmark):
        """Test value below minimum percentile."""
        percentile = calculate_percentile(0.50, sample_benchmark)
        assert percentile < 10
        assert percentile >= 1

    def test_value_above_p90(self, sample_benchmark):
        """Test value above maximum percentile."""
        percentile = calculate_percentile(4.00, sample_benchmark)
        assert percentile > 90
        assert percentile <= 99

    def test_zero_value(self, sample_benchmark):
        """Test zero client value."""
        percentile = calculate_percentile(0.0, sample_benchmark)
        assert percentile == 1  # Minimum percentile

    def test_negative_value(self, sample_benchmark):
        """Test negative client value."""
        percentile = calculate_percentile(-0.5, sample_benchmark)
        assert percentile == 1  # Minimum percentile

    def test_percentile_is_integer(self, sample_benchmark):
        """Test that percentile is always an integer."""
        percentile = calculate_percentile(1.50, sample_benchmark)
        assert isinstance(percentile, int)


# =============================================================================
# TEST: POSITION LABELS
# =============================================================================

class TestGetPositionLabel:
    """Tests for position label generation."""

    def test_higher_better_excellent(self):
        """Test excellent position for higher_better ratio."""
        position = get_position_label(92, RatioDirection.HIGHER_BETTER)
        assert position == "excellent"

    def test_higher_better_above_average(self):
        """Test above_average position."""
        position = get_position_label(78, RatioDirection.HIGHER_BETTER)
        assert position == "above_average"

    def test_higher_better_average(self):
        """Test average position."""
        position = get_position_label(55, RatioDirection.HIGHER_BETTER)
        assert position == "average"

    def test_higher_better_below_average(self):
        """Test below_average position."""
        position = get_position_label(35, RatioDirection.HIGHER_BETTER)
        assert position == "below_average"

    def test_higher_better_concerning(self):
        """Test concerning position."""
        position = get_position_label(18, RatioDirection.HIGHER_BETTER)
        assert position == "concerning"

    def test_higher_better_critical(self):
        """Test critical position."""
        position = get_position_label(5, RatioDirection.HIGHER_BETTER)
        assert position == "critical"

    def test_lower_better_inverted(self):
        """Test that lower_better inverts interpretation."""
        # For debt ratio, low percentile (low debt) is excellent
        position = get_position_label(8, RatioDirection.LOWER_BETTER)
        assert position == "excellent"

        # High percentile (high debt) is critical
        position = get_position_label(95, RatioDirection.LOWER_BETTER)
        assert position == "critical"


class TestGetHealthIndicator:
    """Tests for health indicator mapping."""

    def test_positive_health(self):
        """Test positive health for good positions."""
        assert get_health_indicator("excellent") == "positive"
        assert get_health_indicator("above_average") == "positive"

    def test_neutral_health(self):
        """Test neutral health for average position."""
        assert get_health_indicator("average") == "neutral"

    def test_negative_health(self):
        """Test negative health for poor positions."""
        assert get_health_indicator("below_average") == "negative"
        assert get_health_indicator("concerning") == "negative"
        assert get_health_indicator("critical") == "negative"


# =============================================================================
# TEST: INTERPRETATION GENERATION
# =============================================================================

class TestGenerateInterpretation:
    """Tests for interpretation generation."""

    def test_interpretation_includes_industry(self):
        """Test that interpretation mentions the industry."""
        interpretation = generate_interpretation(
            "current_ratio", 75, Industry.RETAIL, RatioDirection.HIGHER_BETTER
        )
        assert "Retail" in interpretation

    def test_interpretation_includes_ratio_name(self):
        """Test that interpretation mentions the ratio."""
        interpretation = generate_interpretation(
            "gross_margin", 60, Industry.MANUFACTURING, RatioDirection.HIGHER_BETTER
        )
        assert "Gross Margin" in interpretation

    def test_higher_better_top_tier(self):
        """Test interpretation for top performer."""
        interpretation = generate_interpretation(
            "current_ratio", 92, Industry.RETAIL, RatioDirection.HIGHER_BETTER
        )
        assert "Exceptional" in interpretation or "Top 10%" in interpretation

    def test_lower_better_excellent(self):
        """Test interpretation for low debt (excellent)."""
        interpretation = generate_interpretation(
            "debt_to_equity", 8, Industry.RETAIL, RatioDirection.LOWER_BETTER
        )
        assert "Excellent" in interpretation or "better" in interpretation.lower()


# =============================================================================
# TEST: BENCHMARK COMPARISON ENGINE
# =============================================================================

class TestCompareTooBenchmark:
    """Tests for single ratio comparison."""

    def test_compare_returns_comparison(self, sample_benchmark):
        """Test that compare returns BenchmarkComparison."""
        comparison = compare_to_benchmark("current_ratio", 1.80, sample_benchmark)
        assert isinstance(comparison, BenchmarkComparison)

    def test_comparison_has_all_fields(self, sample_benchmark):
        """Test that comparison has all required fields."""
        comparison = compare_to_benchmark("current_ratio", 1.80, sample_benchmark)
        assert comparison.ratio_name == "current_ratio"
        assert comparison.client_value == 1.80
        assert comparison.industry == Industry.RETAIL
        assert comparison.percentile >= 0
        assert comparison.percentile <= 100
        assert comparison.percentile_label is not None
        assert comparison.position is not None
        assert comparison.interpretation is not None
        assert comparison.health_indicator is not None
        assert comparison.benchmark is sample_benchmark

    def test_vs_median_calculation(self, sample_benchmark):
        """Test vs_median calculation."""
        # Value above median
        comparison = compare_to_benchmark("current_ratio", 2.00, sample_benchmark)
        assert comparison.vs_median > 0  # Above median

        # Value below median
        comparison = compare_to_benchmark("current_ratio", 1.50, sample_benchmark)
        assert comparison.vs_median < 0  # Below median


class TestCompareRatiosToBenchmarks:
    """Tests for multiple ratio comparison."""

    def test_compare_multiple_ratios(self, sample_benchmark_set):
        """Test comparing multiple ratios at once."""
        ratios = {
            "current_ratio": 1.80,
            "gross_margin": 0.35,
            "debt_to_equity": 1.20
        }
        comparisons = compare_ratios_to_benchmarks(ratios, sample_benchmark_set)
        assert len(comparisons) == 3

    def test_skips_unavailable_benchmarks(self, sample_benchmark_set):
        """Test that unavailable benchmarks are skipped."""
        ratios = {
            "current_ratio": 1.80,
            "nonexistent_ratio": 0.50
        }
        comparisons = compare_ratios_to_benchmarks(ratios, sample_benchmark_set)
        assert len(comparisons) == 1
        assert comparisons[0].ratio_name == "current_ratio"


class TestOverallScore:
    """Tests for overall score calculation."""

    def test_perfect_score(self, sample_benchmark_set):
        """Test score for top-tier performance."""
        # All ratios at top percentiles
        ratios = {
            "current_ratio": 3.50,  # Above p90
            "gross_margin": 0.60,   # Above p90
        }
        comparisons = compare_ratios_to_benchmarks(ratios, sample_benchmark_set)
        score = calculate_overall_score(comparisons)
        assert score > 80

    def test_average_score(self, sample_benchmark_set):
        """Test score for median performance."""
        # All ratios at median
        ratios = {
            "current_ratio": 1.65,  # At p50
            "gross_margin": 0.32,   # At p50
        }
        comparisons = compare_ratios_to_benchmarks(ratios, sample_benchmark_set)
        score = calculate_overall_score(comparisons)
        assert 40 <= score <= 60

    def test_empty_comparisons(self):
        """Test score with no comparisons."""
        score = calculate_overall_score([])
        assert score == 50.0  # Default neutral


class TestOverallHealth:
    """Tests for overall health assessment."""

    def test_strong_health(self):
        """Test strong health for high score."""
        assert get_overall_health(75) == "strong"

    def test_moderate_health(self):
        """Test moderate health for mid score."""
        assert get_overall_health(50) == "moderate"

    def test_concerning_health(self):
        """Test concerning health for low score."""
        assert get_overall_health(30) == "concerning"


# =============================================================================
# TEST: INDUSTRY BENCHMARK DATA
# =============================================================================

class TestRetailBenchmarks:
    """Tests for Retail industry benchmark data."""

    def test_all_core_ratios_present(self):
        """Test that all core ratios have benchmarks."""
        core_ratios = ["current_ratio", "quick_ratio", "debt_to_equity", "gross_margin"]
        for ratio in core_ratios:
            assert ratio in RETAIL_BENCHMARKS

    def test_percentile_ordering(self):
        """Test percentiles are properly ordered."""
        for ratio_name, benchmark in RETAIL_BENCHMARKS.items():
            assert benchmark.p10 <= benchmark.p25 <= benchmark.p50 <= benchmark.p75 <= benchmark.p90, \
                f"Percentile ordering violated for {ratio_name}"

    def test_sample_sizes_reasonable(self):
        """Test that sample sizes are reasonable."""
        for ratio_name, benchmark in RETAIL_BENCHMARKS.items():
            assert benchmark.sample_size >= 100, f"Sample size too small for {ratio_name}"


class TestManufacturingBenchmarks:
    """Tests for Manufacturing industry benchmark data."""

    def test_has_inventory_turnover(self):
        """Test that manufacturing has inventory turnover benchmark."""
        assert "inventory_turnover" in MANUFACTURING_BENCHMARKS

    def test_has_asset_turnover(self):
        """Test that manufacturing has asset turnover benchmark."""
        assert "asset_turnover" in MANUFACTURING_BENCHMARKS


class TestProfessionalServicesBenchmarks:
    """Tests for Professional Services benchmark data."""

    def test_higher_margins(self):
        """Test that professional services has higher margins than retail."""
        ps_gross = PROFESSIONAL_SERVICES_BENCHMARKS["gross_margin"]
        retail_gross = RETAIL_BENCHMARKS["gross_margin"]
        assert ps_gross.p50 > retail_gross.p50, "Professional services should have higher margins"


class TestTechnologyBenchmarks:
    """Tests for Technology industry benchmark data."""

    def test_high_liquidity(self):
        """Test that technology has high current ratio benchmarks."""
        tech_current = TECHNOLOGY_BENCHMARKS["current_ratio"]
        retail_current = RETAIL_BENCHMARKS["current_ratio"]
        assert tech_current.p50 > retail_current.p50, "Tech should have higher liquidity"


class TestHealthcareBenchmarks:
    """Tests for Healthcare industry benchmark data."""

    def test_all_ratios_present(self):
        """Test all standard ratios are present."""
        assert len(HEALTHCARE_BENCHMARKS) >= 8


class TestFinancialServicesBenchmarks:
    """Tests for Financial Services benchmark data."""

    def test_high_leverage(self):
        """Test financial services has high debt-to-equity."""
        fs_dte = FINANCIAL_SERVICES_BENCHMARKS["debt_to_equity"]
        retail_dte = RETAIL_BENCHMARKS["debt_to_equity"]
        assert fs_dte.p50 > retail_dte.p50, "Financial services should have higher leverage"

    def test_low_roa(self):
        """Test financial services has lower ROA due to high assets."""
        fs_roa = FINANCIAL_SERVICES_BENCHMARKS["roa"]
        retail_roa = RETAIL_BENCHMARKS["roa"]
        assert fs_roa.p50 < retail_roa.p50, "Financial services should have lower ROA"


# =============================================================================
# TEST: BENCHMARK SET FACTORY
# =============================================================================

class TestGetBenchmarkSet:
    """Tests for benchmark set retrieval."""

    def test_get_retail_benchmarks(self):
        """Test getting retail benchmark set."""
        benchmark_set = get_benchmark_set(Industry.RETAIL)
        assert benchmark_set is not None
        assert benchmark_set.industry == Industry.RETAIL

    def test_get_manufacturing_benchmarks(self):
        """Test getting manufacturing benchmark set."""
        benchmark_set = get_benchmark_set(Industry.MANUFACTURING)
        assert benchmark_set is not None

    def test_unavailable_industry(self):
        """Test getting benchmarks for unsupported industry."""
        benchmark_set = get_benchmark_set(Industry.EDUCATION)
        assert benchmark_set is None

    def test_benchmark_set_has_quality_score(self):
        """Test that benchmark set has data quality score."""
        benchmark_set = get_benchmark_set(Industry.RETAIL)
        assert benchmark_set.data_quality_score > 0
        assert benchmark_set.data_quality_score <= 1.0


class TestGetAvailableIndustries:
    """Tests for available industries listing."""

    def test_returns_list(self):
        """Test that available industries returns a list."""
        industries = get_available_industries()
        assert isinstance(industries, list)

    def test_priority_industries_available(self):
        """Test that all 6 priority industries are available."""
        industries = get_available_industries()
        priority = [
            Industry.RETAIL,
            Industry.MANUFACTURING,
            Industry.PROFESSIONAL_SERVICES,
            Industry.TECHNOLOGY,
            Industry.HEALTHCARE,
            Industry.FINANCIAL_SERVICES
        ]
        for industry in priority:
            assert industry in industries


class TestGetBenchmarkSources:
    """Tests for benchmark source information."""

    def test_returns_dict(self):
        """Test that sources returns a dictionary."""
        sources = get_benchmark_sources()
        assert isinstance(sources, dict)

    def test_has_primary_sources(self):
        """Test that primary sources are listed."""
        sources = get_benchmark_sources()
        assert "primary_sources" in sources
        assert len(sources["primary_sources"]) > 0

    def test_has_disclaimer(self):
        """Test that disclaimer is included."""
        sources = get_benchmark_sources()
        assert "disclaimer" in sources

    def test_has_coverage_info(self):
        """Test that coverage information is included."""
        sources = get_benchmark_sources()
        assert "coverage" in sources
        assert "industries" in sources["coverage"]


# =============================================================================
# TEST: EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_zero_benchmark_values(self):
        """Test handling of zero values in benchmark."""
        benchmark = IndustryBenchmark(
            ratio_name="test",
            industry=Industry.RETAIL,
            fiscal_year=2025,
            p10=0.0, p25=0.0, p50=0.0, p75=0.0, p90=0.0,
            mean=0.0, std_dev=0.0, sample_size=100,
            source="Test"
        )
        # Should not raise exception
        percentile = calculate_percentile(0.5, benchmark)
        assert percentile >= 0
        assert percentile <= 100

    def test_identical_percentile_values(self):
        """Test handling when percentile values are identical."""
        benchmark = IndustryBenchmark(
            ratio_name="test",
            industry=Industry.RETAIL,
            fiscal_year=2025,
            p10=1.0, p25=1.0, p50=1.0, p75=1.0, p90=1.0,
            mean=1.0, std_dev=0.0, sample_size=100,
            source="Test"
        )
        percentile = calculate_percentile(1.0, benchmark)
        assert percentile >= 0
        assert percentile <= 100

    def test_very_large_client_value(self, sample_benchmark):
        """Test handling of extremely large client values."""
        percentile = calculate_percentile(1000.0, sample_benchmark)
        assert percentile == 99  # Capped at 99

    def test_very_small_positive_value(self, sample_benchmark):
        """Test handling of very small positive values."""
        percentile = calculate_percentile(0.001, sample_benchmark)
        assert percentile >= 1
        assert percentile <= 10
