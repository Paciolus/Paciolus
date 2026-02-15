"""Test suite for ratio_engine.py — multi-period trend and rolling window analysis.

Covers: TrendAnalyzer, RollingWindowAnalyzer.
"""

import pytest
from datetime import date
from ratio_engine import (
    CategoryTotals,
    TrendDirection,
    TrendAnalyzer,
    PeriodSnapshot,
    create_period_snapshot,
    RollingWindowAnalyzer,
    MomentumType,
)


# =============================================================================
# Sprint 33: TrendAnalyzer Tests
# =============================================================================

class TestTrendAnalyzer:
    """Test cases for multi-period trend analysis."""

    @pytest.fixture
    def quarterly_snapshots(self):
        """Four quarters of financial data showing growth."""
        return [
            PeriodSnapshot(
                period_date=date(2025, 3, 31),
                period_type="quarterly",
                category_totals=CategoryTotals(
                    total_assets=900000.0,
                    total_revenue=200000.0,
                    total_expenses=180000.0,
                    total_equity=400000.0,
                ),
                ratios={"current_ratio": 1.5, "gross_margin": 25.0}
            ),
            PeriodSnapshot(
                period_date=date(2025, 6, 30),
                period_type="quarterly",
                category_totals=CategoryTotals(
                    total_assets=950000.0,
                    total_revenue=220000.0,
                    total_expenses=190000.0,
                    total_equity=450000.0,
                ),
                ratios={"current_ratio": 1.6, "gross_margin": 27.0}
            ),
            PeriodSnapshot(
                period_date=date(2025, 9, 30),
                period_type="quarterly",
                category_totals=CategoryTotals(
                    total_assets=1000000.0,
                    total_revenue=250000.0,
                    total_expenses=200000.0,
                    total_equity=500000.0,
                ),
                ratios={"current_ratio": 1.8, "gross_margin": 30.0}
            ),
            PeriodSnapshot(
                period_date=date(2025, 12, 31),
                period_type="quarterly",
                category_totals=CategoryTotals(
                    total_assets=1100000.0,
                    total_revenue=280000.0,
                    total_expenses=210000.0,
                    total_equity=550000.0,
                ),
                ratios={"current_ratio": 2.0, "gross_margin": 32.0}
            ),
        ]

    @pytest.fixture
    def declining_snapshots(self):
        """Three periods showing decline."""
        return [
            PeriodSnapshot(
                period_date=date(2025, 1, 31),
                period_type="monthly",
                category_totals=CategoryTotals(
                    total_assets=1000000.0,
                    total_revenue=300000.0,
                    total_liabilities=400000.0,
                ),
                ratios={"current_ratio": 2.0, "net_profit_margin": 15.0}
            ),
            PeriodSnapshot(
                period_date=date(2025, 2, 28),
                period_type="monthly",
                category_totals=CategoryTotals(
                    total_assets=950000.0,
                    total_revenue=250000.0,
                    total_liabilities=450000.0,
                ),
                ratios={"current_ratio": 1.5, "net_profit_margin": 10.0}
            ),
            PeriodSnapshot(
                period_date=date(2025, 3, 31),
                period_type="monthly",
                category_totals=CategoryTotals(
                    total_assets=900000.0,
                    total_revenue=200000.0,
                    total_liabilities=500000.0,
                ),
                ratios={"current_ratio": 1.0, "net_profit_margin": 5.0}
            ),
        ]

    def test_trend_analyzer_init_sorts_snapshots(self, quarterly_snapshots):
        """Test that TrendAnalyzer sorts snapshots by date."""
        # Shuffle the order
        shuffled = [quarterly_snapshots[2], quarterly_snapshots[0], quarterly_snapshots[3], quarterly_snapshots[1]]
        analyzer = TrendAnalyzer(shuffled)

        # Should be sorted oldest first
        assert analyzer.snapshots[0].period_date == date(2025, 3, 31)
        assert analyzer.snapshots[-1].period_date == date(2025, 12, 31)

    def test_analyze_category_trends_growth(self, quarterly_snapshots):
        """Test category trend analysis for growing company."""
        analyzer = TrendAnalyzer(quarterly_snapshots)
        trends = analyzer.analyze_category_totals()

        # Total assets should show positive trend
        assert "total_assets" in trends
        assert trends["total_assets"].overall_direction == TrendDirection.POSITIVE
        assert trends["total_assets"].total_change > 0
        assert trends["total_assets"].periods_analyzed == 4

        # Revenue should show positive trend
        assert "total_revenue" in trends
        assert trends["total_revenue"].overall_direction == TrendDirection.POSITIVE

    def test_analyze_category_trends_decline(self, declining_snapshots):
        """Test category trend analysis for declining company."""
        analyzer = TrendAnalyzer(declining_snapshots)
        trends = analyzer.analyze_category_totals()

        # Total assets declining is negative
        assert "total_assets" in trends
        assert trends["total_assets"].overall_direction == TrendDirection.NEGATIVE

        # Revenue declining is negative
        assert "total_revenue" in trends
        assert trends["total_revenue"].overall_direction == TrendDirection.NEGATIVE

        # Liabilities increasing is negative (higher_is_better=False)
        assert "total_liabilities" in trends
        assert trends["total_liabilities"].overall_direction == TrendDirection.NEGATIVE

    def test_analyze_ratio_trends(self, quarterly_snapshots):
        """Test ratio trend analysis."""
        analyzer = TrendAnalyzer(quarterly_snapshots)
        trends = analyzer.analyze_ratio_trends()

        # Current ratio improving
        assert "current_ratio" in trends
        assert trends["current_ratio"].overall_direction == TrendDirection.POSITIVE
        assert trends["current_ratio"].total_change == pytest.approx(0.5, rel=0.01)  # 2.0 - 1.5

        # Gross margin improving
        assert "gross_margin" in trends
        assert trends["gross_margin"].overall_direction == TrendDirection.POSITIVE

    def test_get_full_analysis(self, quarterly_snapshots):
        """Test complete trend analysis output."""
        analyzer = TrendAnalyzer(quarterly_snapshots)
        analysis = analyzer.get_full_analysis()

        # Should have all expected keys
        assert "periods_analyzed" in analysis
        assert "date_range" in analysis
        assert "category_trends" in analysis
        assert "ratio_trends" in analysis

        # Verify date range
        assert analysis["date_range"]["start"] == "2025-03-31"
        assert analysis["date_range"]["end"] == "2025-12-31"

        # Verify periods
        assert analysis["periods_analyzed"] == 4

    def test_trend_analyzer_insufficient_data(self):
        """Test analyzer with insufficient data."""
        single_snapshot = [
            PeriodSnapshot(
                period_date=date(2025, 1, 31),
                period_type="monthly",
                category_totals=CategoryTotals(total_assets=100000.0),
                ratios={}
            )
        ]
        analyzer = TrendAnalyzer(single_snapshot)
        trends = analyzer.analyze_category_totals()

        # Should return empty dict with insufficient data
        assert trends == {}

    def test_trend_analyzer_empty_data(self):
        """Test analyzer with no data."""
        analyzer = TrendAnalyzer([])
        analysis = analyzer.get_full_analysis()

        assert analysis["periods_analyzed"] == 0
        assert analysis["category_trends"] == {}
        assert analysis["ratio_trends"] == {}

    def test_trend_point_calculations(self, quarterly_snapshots):
        """Test period-over-period calculations."""
        analyzer = TrendAnalyzer(quarterly_snapshots)
        trends = analyzer.analyze_category_totals()

        # Check data points
        total_assets_trend = trends["total_assets"]
        points = total_assets_trend.data_points

        # First point has no previous
        assert points[0].change_from_previous is None

        # Second point should show change from first
        assert points[1].change_from_previous == pytest.approx(50000.0, rel=0.01)  # 950k - 900k

    def test_trend_summary_statistics(self, quarterly_snapshots):
        """Test trend summary statistics."""
        analyzer = TrendAnalyzer(quarterly_snapshots)
        trends = analyzer.analyze_category_totals()

        assets_trend = trends["total_assets"]

        # Check min/max/average
        assert assets_trend.min_value == 900000.0
        assert assets_trend.max_value == 1100000.0
        assert assets_trend.average_value == pytest.approx(987500.0, rel=0.01)  # (900k + 950k + 1000k + 1100k) / 4

    def test_create_period_snapshot_calculates_ratios(self):
        """Test that create_period_snapshot calculates ratios if not provided."""
        totals = CategoryTotals(
            current_assets=200000.0,
            current_liabilities=100000.0,
            inventory=50000.0,
            total_assets=500000.0,
            total_liabilities=200000.0,
            total_equity=300000.0,
            total_revenue=400000.0,
            cost_of_goods_sold=200000.0,
            total_expenses=300000.0,
        )

        snapshot = create_period_snapshot(
            period_date=date(2025, 3, 31),
            period_type="quarterly",
            category_totals=totals
        )

        # Should have auto-calculated ratios
        assert snapshot.ratios.get("current_ratio") == 2.0  # 200k / 100k
        assert snapshot.ratios.get("quick_ratio") == 1.5  # (200k - 50k) / 100k

    def test_trend_summary_to_dict(self, quarterly_snapshots):
        """Test TrendSummary serialization."""
        analyzer = TrendAnalyzer(quarterly_snapshots)
        trends = analyzer.analyze_category_totals()
        trend_dict = trends["total_assets"].to_dict()

        assert isinstance(trend_dict, dict)
        assert "metric_name" in trend_dict
        assert "data_points" in trend_dict
        assert "overall_direction" in trend_dict
        assert isinstance(trend_dict["data_points"], list)

    def test_period_snapshot_to_dict(self, quarterly_snapshots):
        """Test PeriodSnapshot serialization."""
        snapshot = quarterly_snapshots[0]
        snapshot_dict = snapshot.to_dict()

        assert isinstance(snapshot_dict, dict)
        assert snapshot_dict["period_date"] == "2025-03-31"
        assert snapshot_dict["period_type"] == "quarterly"
        assert "category_totals" in snapshot_dict
        assert "ratios" in snapshot_dict

    def test_neutral_trend_detection(self):
        """Test detection of neutral/flat trends - equal positive and negative changes."""
        # Create snapshots with equal positive and negative changes (net zero)
        snapshots = [
            PeriodSnapshot(
                period_date=date(2025, 1, 31),
                period_type="monthly",
                category_totals=CategoryTotals(total_assets=100000.0),
                ratios={"current_ratio": 2.0}
            ),
            PeriodSnapshot(
                period_date=date(2025, 2, 28),
                period_type="monthly",
                category_totals=CategoryTotals(total_assets=110000.0),  # +10k
                ratios={"current_ratio": 2.1}
            ),
            PeriodSnapshot(
                period_date=date(2025, 3, 31),
                period_type="monthly",
                category_totals=CategoryTotals(total_assets=100000.0),  # -10k back to original
                ratios={"current_ratio": 2.0}
            ),
        ]
        analyzer = TrendAnalyzer(snapshots)
        trends = analyzer.analyze_category_totals()

        # Equal positive and negative changes should result in neutral
        assert trends["total_assets"].overall_direction == TrendDirection.NEUTRAL

    def test_mixed_trend_majority_wins(self):
        """Test that majority of changes determines direction."""
        # 2 positive, 1 negative = overall positive
        snapshots = [
            PeriodSnapshot(
                period_date=date(2025, 1, 31),
                period_type="monthly",
                category_totals=CategoryTotals(total_assets=100000.0),
                ratios={}
            ),
            PeriodSnapshot(
                period_date=date(2025, 2, 28),
                period_type="monthly",
                category_totals=CategoryTotals(total_assets=120000.0),  # +20k
                ratios={}
            ),
            PeriodSnapshot(
                period_date=date(2025, 3, 31),
                period_type="monthly",
                category_totals=CategoryTotals(total_assets=110000.0),  # -10k
                ratios={}
            ),
            PeriodSnapshot(
                period_date=date(2025, 4, 30),
                period_type="monthly",
                category_totals=CategoryTotals(total_assets=130000.0),  # +20k
                ratios={}
            ),
        ]
        analyzer = TrendAnalyzer(snapshots)
        trends = analyzer.analyze_category_totals()

        # 2 positive vs 1 negative = positive overall
        assert trends["total_assets"].overall_direction == TrendDirection.POSITIVE


# =============================================================================
# Sprint 37: Rolling Window Analyzer Tests
# =============================================================================

class TestRollingWindowAnalyzer:
    """Tests for RollingWindowAnalyzer class."""

    @pytest.fixture
    def monthly_snapshots(self):
        """Create 12 months of test snapshots with growth pattern."""
        snapshots = []
        base_assets = 100000.0
        base_revenue = 50000.0

        for i in range(12):
            month = i + 1
            year = 2025 if month <= 12 else 2026

            # Growth pattern with some variation
            assets = base_assets * (1 + i * 0.05)  # 5% monthly growth
            revenue = base_revenue * (1 + i * 0.03)  # 3% monthly growth

            snapshots.append(PeriodSnapshot(
                period_date=date(year, month, 28),
                period_type="monthly",
                category_totals=CategoryTotals(
                    total_assets=assets,
                    total_revenue=revenue,
                    total_liabilities=assets * 0.4,
                    total_equity=assets * 0.6,
                ),
                ratios={
                    "current_ratio": 1.5 + i * 0.05,
                    "gross_margin": 30 + i * 0.5,
                }
            ))

        return snapshots

    @pytest.fixture
    def declining_snapshots(self):
        """Create snapshots with declining pattern."""
        snapshots = []
        base_assets = 200000.0

        for i in range(6):
            assets = base_assets * (1 - i * 0.08)  # 8% monthly decline

            snapshots.append(PeriodSnapshot(
                period_date=date(2025, i + 1, 28),
                period_type="monthly",
                category_totals=CategoryTotals(
                    total_assets=assets,
                    total_revenue=50000,
                ),
                ratios={}
            ))

        return snapshots

    def test_rolling_window_init(self, monthly_snapshots):
        """Test RollingWindowAnalyzer initialization."""
        analyzer = RollingWindowAnalyzer(monthly_snapshots)
        assert len(analyzer.snapshots) == 12

    def test_supported_windows(self, monthly_snapshots):
        """Test that 3, 6, 12 month windows are supported."""
        analyzer = RollingWindowAnalyzer(monthly_snapshots)
        assert 3 in analyzer.SUPPORTED_WINDOWS
        assert 6 in analyzer.SUPPORTED_WINDOWS
        assert 12 in analyzer.SUPPORTED_WINDOWS

    def test_rolling_average_calculation(self, monthly_snapshots):
        """Test rolling average calculation for different windows."""
        analyzer = RollingWindowAnalyzer(monthly_snapshots)
        results = analyzer.analyze_category_totals()

        assert "total_assets" in results
        result = results["total_assets"]

        # Should have rolling averages for all windows
        assert 3 in result.rolling_averages
        assert 6 in result.rolling_averages
        assert 12 in result.rolling_averages

        # 12-month average should be lower than 3-month (growth pattern)
        avg_3m = result.rolling_averages[3].value
        avg_12m = result.rolling_averages[12].value
        assert avg_3m > avg_12m  # Recent values higher in growth pattern

    def test_momentum_accelerating(self, monthly_snapshots):
        """Test momentum detection for accelerating growth."""
        analyzer = RollingWindowAnalyzer(monthly_snapshots)
        results = analyzer.analyze_category_totals()

        momentum = results["total_assets"].momentum
        # With consistent 5% growth, should detect as steady or accelerating
        assert momentum.momentum_type in [MomentumType.ACCELERATING, MomentumType.STEADY]
        assert momentum.rate_of_change > 0  # Positive change

    def test_momentum_decelerating(self, declining_snapshots):
        """Test momentum detection for declining trend."""
        analyzer = RollingWindowAnalyzer(declining_snapshots)
        results = analyzer.analyze_category_totals()

        momentum = results["total_assets"].momentum
        # Declining pattern should show negative rate of change
        assert momentum.rate_of_change < 0

    def test_trend_direction_positive(self, monthly_snapshots):
        """Test trend direction for growth pattern."""
        analyzer = RollingWindowAnalyzer(monthly_snapshots)
        results = analyzer.analyze_category_totals()

        assert results["total_assets"].trend_direction == TrendDirection.POSITIVE
        assert results["total_revenue"].trend_direction == TrendDirection.POSITIVE

    def test_trend_direction_negative(self, declining_snapshots):
        """Test trend direction for declining pattern."""
        analyzer = RollingWindowAnalyzer(declining_snapshots)
        results = analyzer.analyze_category_totals()

        assert results["total_assets"].trend_direction == TrendDirection.NEGATIVE

    def test_insufficient_data(self):
        """Test handling of insufficient data."""
        # Only 1 snapshot - not enough for analysis
        snapshots = [PeriodSnapshot(
            period_date=date(2025, 1, 31),
            period_type="monthly",
            category_totals=CategoryTotals(total_assets=100000),
            ratios={}
        )]

        analyzer = RollingWindowAnalyzer(snapshots)
        results = analyzer.analyze_category_totals()

        # Should return empty dict with insufficient data
        assert len(results) == 0

    def test_rolling_average_data_points(self, monthly_snapshots):
        """Test that rolling average includes correct number of data points."""
        analyzer = RollingWindowAnalyzer(monthly_snapshots)
        results = analyzer.analyze_category_totals()

        # 3-month window should have ~3 data points
        avg_3m = results["total_assets"].rolling_averages[3]
        assert avg_3m.data_points >= 2
        assert avg_3m.data_points <= 4

    def test_analyze_ratios(self, monthly_snapshots):
        """Test rolling window analysis for ratios."""
        analyzer = RollingWindowAnalyzer(monthly_snapshots)
        results = analyzer.analyze_ratios()

        assert "current_ratio" in results
        assert "gross_margin" in results

    def test_current_value(self, monthly_snapshots):
        """Test that current value is the most recent."""
        analyzer = RollingWindowAnalyzer(monthly_snapshots)
        results = analyzer.analyze_category_totals()

        # Current value should be from the last snapshot
        last_assets = monthly_snapshots[-1].category_totals.total_assets
        assert results["total_assets"].current_value == pytest.approx(last_assets, rel=0.01)

    def test_to_dict_serialization(self, monthly_snapshots):
        """Test complete serialization."""
        analyzer = RollingWindowAnalyzer(monthly_snapshots)
        result = analyzer.to_dict()

        assert "periods_analyzed" in result
        assert result["periods_analyzed"] == 12
        assert "supported_windows" in result
        assert "date_range" in result
        assert "category_rolling" in result
        assert "ratio_rolling" in result

    def test_rolling_average_to_dict(self, monthly_snapshots):
        """Test RollingAverage serialization."""
        analyzer = RollingWindowAnalyzer(monthly_snapshots)
        results = analyzer.analyze_category_totals()

        avg = results["total_assets"].rolling_averages[3]
        avg_dict = avg.to_dict()

        assert "window_months" in avg_dict
        assert avg_dict["window_months"] == 3
        assert "value" in avg_dict
        assert "data_points" in avg_dict
        assert "start_date" in avg_dict
        assert "end_date" in avg_dict

    def test_momentum_indicator_to_dict(self, monthly_snapshots):
        """Test MomentumIndicator serialization."""
        analyzer = RollingWindowAnalyzer(monthly_snapshots)
        results = analyzer.analyze_category_totals()

        momentum = results["total_assets"].momentum
        momentum_dict = momentum.to_dict()

        assert "momentum_type" in momentum_dict
        assert "rate_of_change" in momentum_dict
        assert "acceleration" in momentum_dict
        assert "confidence" in momentum_dict

    def test_momentum_confidence(self, monthly_snapshots):
        """Test momentum confidence calculation."""
        analyzer = RollingWindowAnalyzer(monthly_snapshots)
        results = analyzer.analyze_category_totals()

        confidence = results["total_assets"].momentum.confidence
        assert 0.0 <= confidence <= 1.0

    def test_get_full_analysis(self, monthly_snapshots):
        """Test complete analysis output."""
        analyzer = RollingWindowAnalyzer(monthly_snapshots)
        analysis = analyzer.get_full_analysis()

        assert analysis["periods_analyzed"] == 12
        assert analysis["supported_windows"] == [3, 6, 12]
        assert analysis["date_range"]["start"] is not None
        assert analysis["date_range"]["end"] is not None

    def test_empty_snapshots(self):
        """Test handling of empty snapshots list."""
        analyzer = RollingWindowAnalyzer([])
        results = analyzer.analyze_category_totals()

        assert len(results) == 0
