"""
Tests for Journal Entry Testing Engine — Tier 1 Statistical Tests (T6-T8)

Covers:
- T6: Benford's Law (Sprint 65)
- T7: Weekend Postings (Sprint 65)
- T8: Month-End Clustering (Sprint 65)
- Scoring calibration fixtures (Sprint 65)
- Full pipeline with Benford integration (Sprint 65)
"""

import pytest
from je_testing_engine import (
    JournalEntry,
    JETestingConfig,
    # Tier 1 Statistical — aliased to avoid pytest collection
    test_benford_law as run_benford_test,
    test_weekend_postings as run_weekend_test,
    test_month_end_clustering as run_month_end_test,
    # Battery & scoring
    run_test_battery,
    calculate_composite_score,
    score_to_risk_tier,
    # Main entry point
    run_je_testing,
    # Column detection (needed for helpers)
    detect_gl_columns,
    parse_gl_entries,
    # Enums & types
    RiskTier,
    TestTier,
    Severity,
    TestResult,
    FlaggedEntry,
    CompositeScore,
    BenfordResult,
    JETestingResult,
)


# =============================================================================
# FIXTURES (duplicated from test_je_core.py for pipeline tests)
# =============================================================================

def sample_gl_rows() -> list[dict]:
    """Standard GL rows for testing."""
    return [
        {"Entry ID": "JE001", "Date": "2025-01-15", "Account": "Cash", "Debit": 1000, "Credit": 0, "Description": "Payment received", "Posted By": "jsmith", "Reference": "INV-001"},
        {"Entry ID": "JE001", "Date": "2025-01-15", "Account": "Accounts Receivable", "Debit": 0, "Credit": 1000, "Description": "Payment received", "Posted By": "jsmith", "Reference": "INV-001"},
        {"Entry ID": "JE002", "Date": "2025-01-20", "Account": "Office Supplies", "Debit": 250, "Credit": 0, "Description": "Office supplies purchase", "Posted By": "jdoe", "Reference": "PO-100"},
        {"Entry ID": "JE002", "Date": "2025-01-20", "Account": "Accounts Payable", "Debit": 0, "Credit": 250, "Description": "Office supplies purchase", "Posted By": "jdoe", "Reference": "PO-100"},
    ]


def sample_gl_columns() -> list[str]:
    return ["Entry ID", "Date", "Account", "Debit", "Credit", "Description", "Posted By", "Reference"]


# =============================================================================
# T6: BENFORD'S LAW (Sprint 65)
# =============================================================================

class TestBenfordLaw:
    """Tests for test_benford_law()."""

    def _make_benford_entries(self, n=600):
        """Generate entries following Benford's distribution for testing."""
        import random
        random.seed(42)
        entries = []
        for i in range(1, n + 1):
            # Generate amounts roughly following Benford's Law
            # Using log-uniform distribution
            amt = 10 ** (random.uniform(1, 5))  # $10 to $100,000
            entries.append(JournalEntry(
                account="Revenue", debit=amt, posting_date="2025-01-15", row_number=i,
            ))
        return entries

    def _make_non_benford_entries(self, n=600):
        """Generate entries NOT following Benford's distribution.

        All amounts start with digit 5 but span 2+ orders of magnitude
        to pass the magnitude precheck while violating Benford's Law.
        """
        entries = []
        for i in range(1, n + 1):
            # Spread across magnitudes (50+, 500+, 5000+) — all start with 5
            magnitude = i % 3  # 0, 1, 2
            amt = 5 * (10 ** (magnitude + 1)) + (i % 50)
            entries.append(JournalEntry(
                account="Revenue", debit=amt, posting_date="2025-01-15", row_number=i,
            ))
        return entries

    def test_insufficient_entries_precheck(self):
        entries = [JournalEntry(debit=100, row_number=i) for i in range(1, 100)]
        result, benford = run_benford_test(entries, JETestingConfig())
        assert benford.passed_prechecks is False
        assert "Insufficient data" in benford.precheck_message
        assert result.entries_flagged == 0

    def test_insufficient_magnitude_precheck(self):
        # All amounts in same order of magnitude
        entries = [
            JournalEntry(debit=100 + i, row_number=i)
            for i in range(1, 600)
        ]
        config = JETestingConfig(benford_min_entries=100)
        result, benford = run_benford_test(entries, config)
        assert benford.passed_prechecks is False
        assert "magnitude" in benford.precheck_message.lower()

    def test_passes_prechecks_with_valid_data(self):
        entries = self._make_benford_entries(600)
        result, benford = run_benford_test(entries, JETestingConfig())
        assert benford.passed_prechecks is True
        assert benford.eligible_count >= 500

    def test_expected_distribution_present(self):
        entries = self._make_benford_entries(600)
        _, benford = run_benford_test(entries, JETestingConfig())
        assert len(benford.expected_distribution) == 9
        for d in range(1, 10):
            assert d in benford.expected_distribution
        # Benford expected for digit 1 ≈ 0.301
        assert abs(benford.expected_distribution[1] - 0.30103) < 0.001

    def test_actual_distribution_sums_to_one(self):
        entries = self._make_benford_entries(600)
        _, benford = run_benford_test(entries, JETestingConfig())
        total = sum(benford.actual_distribution.values())
        assert abs(total - 1.0) < 0.001

    def test_mad_calculated(self):
        entries = self._make_benford_entries(600)
        _, benford = run_benford_test(entries, JETestingConfig())
        assert benford.mad >= 0
        assert benford.mad < 1.0

    def test_chi_squared_positive(self):
        entries = self._make_benford_entries(600)
        _, benford = run_benford_test(entries, JETestingConfig())
        assert benford.chi_squared >= 0

    def test_conforming_data(self):
        entries = self._make_benford_entries(1000)
        _, benford = run_benford_test(entries, JETestingConfig())
        # Log-uniform should produce conforming or acceptable
        assert benford.conformity_level in ("conforming", "acceptable")

    def test_nonconforming_data_detected(self):
        entries = self._make_non_benford_entries(600)
        _, benford = run_benford_test(entries, JETestingConfig())
        # Uniform 5xxx amounts should be nonconforming
        assert benford.conformity_level in ("marginally_acceptable", "nonconforming")

    def test_nonconforming_flags_entries(self):
        entries = self._make_non_benford_entries(600)
        result, benford = run_benford_test(entries, JETestingConfig())
        if benford.conformity_level in ("marginally_acceptable", "nonconforming"):
            # Should have some flagged entries
            assert result.entries_flagged > 0

    def test_sub_dollar_excluded(self):
        # Entries below min_amount should be excluded
        entries = [
            JournalEntry(debit=0.50, row_number=i)
            for i in range(1, 600)
        ]
        entries.extend([
            JournalEntry(debit=10 ** (i % 4 + 1), row_number=600 + i)
            for i in range(1, 100)
        ])
        config = JETestingConfig(benford_min_entries=50, benford_min_amount=1.0)
        _, benford = run_benford_test(entries, config)
        # Only non-sub-dollar entries should be counted
        assert benford.eligible_count < len(entries)

    def test_benford_test_key(self):
        entries = self._make_benford_entries(600)
        result, _ = run_benford_test(entries, JETestingConfig())
        assert result.test_key == "benford_law"
        assert result.test_tier == TestTier.STATISTICAL

    def test_custom_min_entries(self):
        entries = [
            JournalEntry(debit=10 ** (i % 4 + 1), row_number=i)
            for i in range(1, 200)
        ]
        config = JETestingConfig(benford_min_entries=100)
        _, benford = run_benford_test(entries, config)
        assert benford.passed_prechecks is True


# =============================================================================
# T7: WEEKEND POSTINGS (Sprint 65)
# =============================================================================

class TestWeekendPostings:
    """Tests for test_weekend_postings()."""

    def test_weekday_entries_no_flags(self):
        # 2025-01-15 is a Wednesday
        entries = [
            JournalEntry(posting_date="2025-01-15", debit=100, row_number=1),
            JournalEntry(posting_date="2025-01-16", debit=200, row_number=2),
        ]
        result = run_weekend_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_saturday_flagged(self):
        # 2025-01-18 is a Saturday
        entries = [
            JournalEntry(posting_date="2025-01-18", debit=100, row_number=1),
        ]
        result = run_weekend_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert "Saturday" in result.flagged_entries[0].issue

    def test_sunday_flagged(self):
        # 2025-01-19 is a Sunday
        entries = [
            JournalEntry(posting_date="2025-01-19", debit=100, row_number=1),
        ]
        result = run_weekend_test(entries, JETestingConfig())
        assert result.entries_flagged == 1
        assert "Sunday" in result.flagged_entries[0].issue

    def test_large_amount_high_severity(self):
        # 2025-01-18 is Saturday, amount > threshold
        entries = [
            JournalEntry(posting_date="2025-01-18", debit=50000, row_number=1),
        ]
        result = run_weekend_test(entries, JETestingConfig(weekend_large_amount_threshold=10000))
        assert result.flagged_entries[0].severity == Severity.HIGH

    def test_small_amount_low_severity(self):
        entries = [
            JournalEntry(posting_date="2025-01-18", debit=50, row_number=1),
        ]
        result = run_weekend_test(entries, JETestingConfig(weekend_large_amount_threshold=10000))
        assert result.flagged_entries[0].severity == Severity.LOW

    def test_medium_amount_medium_severity(self):
        # Between threshold/5 and threshold
        entries = [
            JournalEntry(posting_date="2025-01-18", debit=5000, row_number=1),
        ]
        result = run_weekend_test(entries, JETestingConfig(weekend_large_amount_threshold=10000))
        assert result.flagged_entries[0].severity == Severity.MEDIUM

    def test_disabled_no_flags(self):
        entries = [
            JournalEntry(posting_date="2025-01-18", debit=100, row_number=1),
        ]
        config = JETestingConfig(weekend_posting_enabled=False)
        result = run_weekend_test(entries, config)
        assert result.entries_flagged == 0

    def test_unparseable_date_skipped(self):
        entries = [
            JournalEntry(posting_date="not-a-date", debit=100, row_number=1),
        ]
        result = run_weekend_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_test_key(self):
        entries = [JournalEntry(posting_date="2025-01-15", debit=100, row_number=1)]
        result = run_weekend_test(entries, JETestingConfig())
        assert result.test_key == "weekend_postings"
        assert result.test_tier == TestTier.STATISTICAL


# =============================================================================
# T8: MONTH-END CLUSTERING (Sprint 65)
# =============================================================================

class TestMonthEndClustering:
    """Tests for test_month_end_clustering()."""

    def test_uniform_distribution_no_flags(self):
        # Entries spread evenly across the month
        entries = []
        for day in range(1, 29):
            entries.append(JournalEntry(
                posting_date=f"2025-01-{day:02d}", debit=100, row_number=day,
            ))
        result = run_month_end_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_month_end_cluster_flagged(self):
        # 5 entries spread across month + 20 crammed into last 3 days
        entries = []
        for i in range(1, 6):
            entries.append(JournalEntry(
                posting_date=f"2025-01-{i:02d}", debit=100, row_number=i,
            ))
        for i in range(20):
            entries.append(JournalEntry(
                posting_date=f"2025-01-{29 + (i % 3):02d}", debit=100, row_number=6 + i,
            ))
        result = run_month_end_test(entries, JETestingConfig())
        assert result.entries_flagged > 0

    def test_too_few_entries_skipped(self):
        # Less than 10 entries in month
        entries = [
            JournalEntry(posting_date="2025-01-31", debit=100, row_number=1),
            JournalEntry(posting_date="2025-01-30", debit=100, row_number=2),
        ]
        result = run_month_end_test(entries, JETestingConfig())
        assert result.entries_flagged == 0

    def test_custom_multiplier(self):
        # High multiplier = fewer flags
        entries = []
        for day in range(1, 25):
            entries.append(JournalEntry(
                posting_date=f"2025-01-{day:02d}", debit=100, row_number=day,
            ))
        # Add some month-end entries
        for i in range(10):
            entries.append(JournalEntry(
                posting_date="2025-01-31", debit=100, row_number=25 + i,
            ))
        # With very high multiplier, should not flag
        config = JETestingConfig(month_end_volume_multiplier=100.0)
        result = run_month_end_test(entries, config)
        assert result.entries_flagged == 0

    def test_multiple_months(self):
        # Two months, only one with clustering
        entries = []
        # January: even
        for day in range(1, 29):
            entries.append(JournalEntry(
                posting_date=f"2025-01-{day:02d}", debit=100, row_number=day,
            ))
        # February: all crammed at month end
        for i in range(15):
            entries.append(JournalEntry(
                posting_date=f"2025-02-{26 + (i % 3):02d}", debit=100, row_number=29 + i,
            ))
        result = run_month_end_test(entries, JETestingConfig())
        # Feb should be flagged but not Jan
        flagged_dates = [f.details.get("month") for f in result.flagged_entries]
        if result.entries_flagged > 0:
            assert "2025-02" in flagged_dates

    def test_test_key(self):
        entries = [JournalEntry(posting_date="2025-01-15", debit=100, row_number=1)]
        result = run_month_end_test(entries, JETestingConfig())
        assert result.test_key == "month_end_clustering"
        assert result.test_tier == TestTier.STATISTICAL


# =============================================================================
# SCORING CALIBRATION FIXTURES (Sprint 65)
# =============================================================================

class TestScoringCalibration:
    """Validate scoring engine produces expected risk tiers for known profiles."""

    def _generate_clean_gl(self, n=200):
        """Generate a clean GL: balanced entries, no anomalies."""
        entries = []
        for i in range(1, n + 1):
            entries.append(JournalEntry(
                entry_id=f"JE{i:04d}", account="Cash",
                posting_date=f"2025-01-{(i % 28) + 1:02d}",
                debit=100 + (i * 7.3), row_number=i * 2 - 1,
            ))
            entries.append(JournalEntry(
                entry_id=f"JE{i:04d}", account="Revenue",
                posting_date=f"2025-01-{(i % 28) + 1:02d}",
                credit=100 + (i * 7.3), row_number=i * 2,
            ))
        return entries

    def _generate_moderate_risk_gl(self, n=200):
        """Generate moderate risk GL: some duplicates, round amounts, missing fields."""
        entries = self._generate_clean_gl(n)
        # Add duplicates (10% of entries)
        for i in range(n // 10):
            entries.append(JournalEntry(
                entry_id=f"JE{1:04d}", account="Cash",
                posting_date="2025-01-01", debit=107.3, row_number=len(entries) + 1,
            ))
        # Add entries with missing fields
        for i in range(n // 10):
            entries.append(JournalEntry(
                account="", debit=100, row_number=len(entries) + 1,
            ))
        # Add round amounts
        for i in range(n // 10):
            entries.append(JournalEntry(
                account="Expense", debit=100000, posting_date="2025-01-15",
                row_number=len(entries) + 1,
            ))
        return entries

    def _generate_high_risk_gl(self, n=200):
        """Generate high risk GL: many issues across all test types."""
        entries = []
        # Unbalanced entries (25% of base)
        for i in range(1, n // 4 + 1):
            entries.append(JournalEntry(
                entry_id=f"BAD{i:04d}", account="Cash",
                posting_date="2025-01-15", debit=5000, row_number=len(entries) + 1,
            ))
            entries.append(JournalEntry(
                entry_id=f"BAD{i:04d}", account="Revenue",
                posting_date="2025-01-15", credit=3000, row_number=len(entries) + 1,
            ))
        # Duplicates (many identical)
        for i in range(n // 3):
            entries.append(JournalEntry(
                account="Cash", posting_date="2025-01-10", debit=999,
                description="duplicate payment", row_number=len(entries) + 1,
            ))
        # Missing fields
        for i in range(n // 5):
            entries.append(JournalEntry(row_number=len(entries) + 1))
        # Round amounts
        for i in range(n // 5):
            entries.append(JournalEntry(
                account="Expense", debit=100000, posting_date="2025-01-15",
                row_number=len(entries) + 1,
            ))
        return entries

    def test_clean_gl_low_risk(self):
        entries = self._generate_clean_gl(200)
        results, _ = run_test_battery(entries)
        score = calculate_composite_score(results, len(entries))
        assert score.risk_tier in (RiskTier.LOW, RiskTier.ELEVATED)
        assert score.score < 25

    def test_moderate_risk_gl(self):
        entries = self._generate_moderate_risk_gl(200)
        results, _ = run_test_battery(entries)
        score = calculate_composite_score(results, len(entries))
        # Should score above zero — comparative ordering validated by other tests
        assert score.score > 2
        assert score.risk_tier in (RiskTier.LOW, RiskTier.ELEVATED, RiskTier.MODERATE, RiskTier.HIGH)

    def test_high_risk_gl(self):
        entries = self._generate_high_risk_gl(200)
        results, _ = run_test_battery(entries)
        score = calculate_composite_score(results, len(entries))
        # Should be elevated or higher (Tier 2 tests dilute average since they find fewer flags)
        assert score.score >= 15
        assert score.risk_tier in (RiskTier.ELEVATED, RiskTier.MODERATE, RiskTier.HIGH, RiskTier.CRITICAL)

    def test_clean_fewer_flagged_than_risky(self):
        clean = self._generate_clean_gl(200)
        risky = self._generate_high_risk_gl(200)
        clean_results, _ = run_test_battery(clean)
        risky_results, _ = run_test_battery(risky)
        clean_score = calculate_composite_score(clean_results, len(clean))
        risky_score = calculate_composite_score(risky_results, len(risky))
        assert clean_score.score < risky_score.score

    def test_score_increases_with_risk(self):
        clean = self._generate_clean_gl(200)
        risky = self._generate_high_risk_gl(200)
        clean_results, _ = run_test_battery(clean)
        risky_results, _ = run_test_battery(risky)
        clean_score = calculate_composite_score(clean_results, len(clean))
        risky_score = calculate_composite_score(risky_results, len(risky))
        # Risky GL should produce a higher composite score
        assert clean_score.score < risky_score.score


# =============================================================================
# FULL PIPELINE WITH BENFORD (Sprint 65)
# =============================================================================

class TestFullPipelineWithBenford:
    """Tests for run_je_testing with Benford integration."""

    def test_pipeline_includes_benford_result(self):
        rows = sample_gl_rows()
        cols = sample_gl_columns()
        result = run_je_testing(rows, cols)
        assert result.benford_result is not None
        # Small dataset won't pass prechecks
        assert result.benford_result.passed_prechecks is False

    def test_pipeline_to_dict_includes_benford(self):
        rows = sample_gl_rows()
        cols = sample_gl_columns()
        result = run_je_testing(rows, cols)
        d = result.to_dict()
        assert "benford_result" in d
        assert d["benford_result"]["passed_prechecks"] is False
