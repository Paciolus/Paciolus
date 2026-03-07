"""
Tests for population_profile_engine.py
Sprint 287: Phase XXXIX — TB Population Profile Report
Sprint 511: Enrichment — Benford, stratification, exceptions, procedures, data quality
"""

import pytest

from population_profile_engine import (
    GINI_HIGH_LABEL,
    ExceptionFlags,
    _compute_account_type_stratification,
    _compute_data_quality,
    _compute_exception_flags,
    _compute_gini,
    _generate_suggested_procedures,
    _interpret_gini,
    compute_population_profile,
    run_population_profile,
)


class TestComputeGini:
    """Tests for the Gini coefficient computation."""

    def test_empty_list(self):
        assert _compute_gini([]) == 0.0

    def test_single_value(self):
        assert _compute_gini([100.0]) == 0.0

    def test_equal_values_low_gini(self):
        """All equal values should yield Gini ~ 0."""
        values = sorted([100.0] * 10)
        gini = _compute_gini(values)
        assert gini == pytest.approx(0.0, abs=0.01)

    def test_concentrated_values_high_gini(self):
        """One large value + many zeros → high Gini."""
        values = sorted([0.0] * 9 + [1_000_000.0])
        gini = _compute_gini(values)
        assert gini > 0.8

    def test_moderate_distribution(self):
        """Moderately spread values should yield moderate Gini."""
        values = sorted([10.0, 20.0, 50.0, 100.0, 500.0])
        gini = _compute_gini(values)
        assert 0.2 < gini < 0.7

    def test_all_zeros(self):
        """All zeros → 0.0 (division guard)."""
        assert _compute_gini([0.0, 0.0, 0.0]) == 0.0


class TestInterpretGini:
    """Tests for Gini interpretation labels (Sprint 511 thresholds)."""

    def test_low(self):
        assert _interpret_gini(0.1) == "Low"
        assert _interpret_gini(0.39) == "Low"

    def test_moderate(self):
        assert _interpret_gini(0.40) == "Moderate"
        assert _interpret_gini(0.64) == "Moderate"

    def test_high(self):
        assert _interpret_gini(0.65) == GINI_HIGH_LABEL
        assert _interpret_gini(0.95) == GINI_HIGH_LABEL

    def test_boundary_low_moderate(self):
        """0.40 is the boundary — should be Moderate."""
        assert _interpret_gini(0.40) == "Moderate"

    def test_boundary_moderate_high(self):
        """0.65 is the boundary — should be High."""
        assert _interpret_gini(0.65) == GINI_HIGH_LABEL


class TestComputePopulationProfile:
    """Tests for the core compute_population_profile function."""

    def test_empty_input(self):
        result = compute_population_profile({})
        assert result.account_count == 0
        assert result.total_abs_balance == 0.0
        assert result.gini_interpretation == "Low"
        assert result.buckets == []
        assert result.top_accounts == []

    def test_single_account(self):
        balances = {"Cash": {"debit": 5000.0, "credit": 0.0}}
        result = compute_population_profile(balances)
        assert result.account_count == 1
        assert result.total_abs_balance == pytest.approx(5000.0)
        assert result.mean_abs_balance == pytest.approx(5000.0)
        assert result.median_abs_balance == pytest.approx(5000.0)
        assert result.std_dev_abs_balance == 0.0
        assert result.min_abs_balance == pytest.approx(5000.0)
        assert result.max_abs_balance == pytest.approx(5000.0)
        assert result.gini_coefficient == 0.0

    def test_basic_stats(self):
        balances = {
            "Cash": {"debit": 1000.0, "credit": 0.0},
            "AR": {"debit": 3000.0, "credit": 0.0},
            "Inventory": {"debit": 5000.0, "credit": 0.0},
        }
        result = compute_population_profile(balances)
        assert result.account_count == 3
        assert result.total_abs_balance == pytest.approx(9000.0)
        assert result.mean_abs_balance == pytest.approx(3000.0)
        assert result.median_abs_balance == pytest.approx(3000.0)
        assert result.min_abs_balance == pytest.approx(1000.0)
        assert result.max_abs_balance == pytest.approx(5000.0)

    def test_credit_balances_use_absolute(self):
        """Net credit balances should use absolute value."""
        balances = {
            "AP": {"debit": 0.0, "credit": 2000.0},
            "Revenue": {"debit": 0.0, "credit": 8000.0},
        }
        result = compute_population_profile(balances)
        assert result.total_abs_balance == pytest.approx(10000.0)
        assert result.mean_abs_balance == pytest.approx(5000.0)

    def test_bucket_allocation(self):
        """Accounts should land in the correct magnitude buckets."""
        balances = {
            "Petty Cash": {"debit": 0.005, "credit": 0.0},  # Zero bucket
            "Postage": {"debit": 500.0, "credit": 0.0},  # <$1K
            "Supplies": {"debit": 5000.0, "credit": 0.0},  # $1K–$10K
            "Vehicle": {"debit": 50000.0, "credit": 0.0},  # $10K–$100K
            "Building": {"debit": 500000.0, "credit": 0.0},  # $100K–$1M
            "Land": {"debit": 2000000.0, "credit": 0.0},  # >$1M
        }
        result = compute_population_profile(balances)

        bucket_map = {b.label: b.count for b in result.buckets}
        assert bucket_map["Zero (<$0.01)"] == 1
        assert bucket_map["<$1K"] == 1
        assert bucket_map["$1K–$10K"] == 1
        assert bucket_map["$10K–$100K"] == 1
        assert bucket_map["$100K–$1M"] == 1
        assert bucket_map[">$1M"] == 1

    def test_bucket_sums_equal_total(self):
        """Sum of all bucket sums should equal total_abs_balance."""
        balances = {f"Acct{i}": {"debit": float(i * 100 + 50), "credit": 0.0} for i in range(50)}
        result = compute_population_profile(balances)
        bucket_total = sum(b.sum_abs for b in result.buckets)
        assert bucket_total == pytest.approx(result.total_abs_balance, rel=1e-6)

    def test_top_accounts_ordering(self):
        """Top accounts should be ordered by absolute balance descending."""
        balances = {f"Account {i}": {"debit": float(i * 100), "credit": 0.0} for i in range(1, 15)}
        result = compute_population_profile(balances, top_n=5)
        assert len(result.top_accounts) == 5
        assert result.top_accounts[0].rank == 1
        assert result.top_accounts[0].abs_balance == pytest.approx(1400.0)
        assert result.top_accounts[4].rank == 5

    def test_classified_accounts_passthrough(self):
        """Category from classified_accounts should appear in top_accounts."""
        balances = {"Cash": {"debit": 1000.0, "credit": 0.0}}
        classified = {"Cash": "current_asset"}
        result = compute_population_profile(balances, classified)
        assert result.top_accounts[0].category == "current_asset"

    def test_unclassified_defaults_unknown(self):
        balances = {"Mystery": {"debit": 1000.0, "credit": 0.0}}
        result = compute_population_profile(balances, classified_accounts=None)
        assert result.top_accounts[0].category == "Unknown"

    def test_account_number_passthrough(self):
        """Account numbers should appear in top_accounts when provided."""
        balances = {"Cash": {"debit": 1000.0, "credit": 0.0}}
        result = compute_population_profile(
            balances,
            account_numbers={"Cash": "1010"},
        )
        assert result.top_accounts[0].account_number == "1010"

    def test_to_dict_structure(self):
        """to_dict() should produce the expected keys."""
        balances = {
            "A": {"debit": 100.0, "credit": 0.0},
            "B": {"debit": 200.0, "credit": 0.0},
        }
        result = compute_population_profile(balances)
        d = result.to_dict()
        expected_keys = {
            "account_count",
            "total_abs_balance",
            "mean_abs_balance",
            "median_abs_balance",
            "std_dev_abs_balance",
            "min_abs_balance",
            "max_abs_balance",
            "p25",
            "p75",
            "gini_coefficient",
            "gini_interpretation",
            "buckets",
            "top_accounts",
            "benford_analysis",
            "exception_flags",
            "suggested_procedures",
            "data_quality",
        }
        assert expected_keys.issubset(set(d.keys()))
        assert isinstance(d["buckets"], list)
        assert isinstance(d["top_accounts"], list)

    def test_equal_balances_gini_near_zero(self):
        """All equal non-zero balances → Gini ≈ 0."""
        balances = {f"Acct{i}": {"debit": 1000.0, "credit": 0.0} for i in range(20)}
        result = compute_population_profile(balances)
        assert result.gini_coefficient < 0.05
        assert result.gini_interpretation == "Low"

    def test_concentrated_balances_high_gini(self):
        """One dominant account → high Gini."""
        balances = {
            "Small1": {"debit": 1.0, "credit": 0.0},
            "Small2": {"debit": 1.0, "credit": 0.0},
            "Small3": {"debit": 1.0, "credit": 0.0},
            "Big": {"debit": 1_000_000.0, "credit": 0.0},
        }
        result = compute_population_profile(balances)
        assert result.gini_coefficient > 0.65
        assert result.gini_interpretation == GINI_HIGH_LABEL

    def test_bucket_percentages_sum_to_100(self):
        """Bucket percent_count values should sum to ~100."""
        balances = {f"Acct{i}": {"debit": float(i * 100 + 50), "credit": 0.0} for i in range(50)}
        result = compute_population_profile(balances)
        total_pct = sum(b.percent_count for b in result.buckets)
        assert total_pct == pytest.approx(100.0, abs=0.5)

    def test_benford_analysis_included(self):
        """Profile should include benford_analysis when enough accounts."""
        balances = {f"Acct{i}": {"debit": float(i * 137 + 50), "credit": 0.0} for i in range(1, 30)}
        result = compute_population_profile(balances)
        assert result.benford_analysis is not None
        assert "passed_prechecks" in result.benford_analysis
        assert "chi_squared" in result.benford_analysis

    def test_exception_flags_included(self):
        """Profile should include exception_flags."""
        balances = {
            "Cash": {"debit": 1000.0, "credit": 0.0},
            "Revenue": {"debit": 0.0, "credit": 5000.0},
        }
        result = compute_population_profile(balances)
        assert result.exception_flags is not None

    def test_data_quality_included(self):
        """Profile should include data_quality score."""
        balances = {
            "A": {"debit": 100.0, "credit": 0.0},
            "B": {"debit": 200.0, "credit": 0.0},
        }
        result = compute_population_profile(balances)
        assert result.data_quality is not None
        assert 0.0 <= result.data_quality.overall_score <= 100.0

    def test_suggested_procedures_included(self):
        """Profile should include suggested_procedures."""
        balances = {
            "Big": {"debit": 1_000_000.0, "credit": 0.0},
            "Small": {"debit": 1.0, "credit": 0.0},
        }
        result = compute_population_profile(balances)
        assert len(result.suggested_procedures) > 0


class TestAccountTypeStratification:
    """Tests for account type stratification."""

    def test_stratification_basic(self):
        entries = [
            ("Cash", 1000.0, 1000.0, "Asset", "1010"),
            ("Revenue", -5000.0, 5000.0, "Revenue", "4000"),
            ("AP", -2000.0, 2000.0, "Liability", "2010"),
        ]
        result = _compute_account_type_stratification(entries, 8000.0)
        types = {s.account_type for s in result}
        assert "Asset" in types
        assert "Revenue" in types
        assert "Liability" in types

    def test_stratification_percentages(self):
        entries = [
            ("Cash", 1000.0, 1000.0, "Asset", ""),
            ("Revenue", -9000.0, 9000.0, "Revenue", ""),
        ]
        result = _compute_account_type_stratification(entries, 10000.0)
        revenue = next(s for s in result if s.account_type == "Revenue")
        assert revenue.pct_of_population == pytest.approx(90.0, abs=0.1)

    def test_stratification_unknown_category(self):
        entries = [
            ("Mystery", 1000.0, 1000.0, "Unknown", ""),
        ]
        result = _compute_account_type_stratification(entries, 1000.0)
        assert len(result) == 1
        assert result[0].account_type == "Unknown"


class TestExceptionFlags:
    """Tests for exception flag computation."""

    def test_normal_balance_violation(self):
        """Asset with credit balance should be flagged."""
        entries = [
            ("Cash", -500.0, 500.0, "Asset", "1010"),
        ]
        flags = _compute_exception_flags(entries, 500.0)
        assert len(flags.normal_balance_violations) == 1
        assert flags.normal_balance_violations[0].expected == "Debit"
        assert flags.normal_balance_violations[0].actual == "Credit"

    def test_no_violation_for_correct_balance(self):
        """Asset with debit balance should not be flagged."""
        entries = [
            ("Cash", 500.0, 500.0, "Asset", "1010"),
        ]
        flags = _compute_exception_flags(entries, 500.0)
        assert len(flags.normal_balance_violations) == 0

    def test_revenue_debit_flagged(self):
        """Revenue account with debit balance (net positive) should be flagged."""
        entries = [
            ("Returns", 100.0, 100.0, "Revenue", "4500"),
        ]
        flags = _compute_exception_flags(entries, 100.0)
        assert len(flags.normal_balance_violations) == 1

    def test_zero_balance_detected(self):
        """Accounts with $0.00 balance should be flagged."""
        entries = [
            ("Inactive", 0.0, 0.0, "Asset", "1200"),
        ]
        flags = _compute_exception_flags(entries, 0.0)
        assert len(flags.zero_balance_accounts) == 1
        assert flags.zero_balance_accounts[0].is_zero is True

    def test_near_zero_detected(self):
        """Accounts with balance ≤ $100 should be flagged as near-zero."""
        entries = [
            ("Petty", 50.0, 50.0, "Asset", "1050"),
        ]
        flags = _compute_exception_flags(entries, 50.0)
        assert len(flags.near_zero_accounts) == 1
        assert flags.near_zero_accounts[0].is_zero is False

    def test_dominant_account_flagged(self):
        """Account exceeding 10% of total should be flagged."""
        entries = [
            ("Big", 9000.0, 9000.0, "Revenue", "4000"),
            ("Small", 1000.0, 1000.0, "Asset", "1010"),
        ]
        flags = _compute_exception_flags(entries, 10000.0)
        assert len(flags.dominant_accounts) == 1
        assert flags.dominant_accounts[0].pct_of_total == pytest.approx(90.0, abs=0.1)

    def test_no_dominant_below_threshold(self):
        """No flags when no account exceeds 10%."""
        entries = [(f"Acct{i}", 100.0, 100.0, "Asset", f"{i}") for i in range(20)]
        flags = _compute_exception_flags(entries, 2000.0)
        assert len(flags.dominant_accounts) == 0

    def test_exception_flags_to_dict(self):
        flags = ExceptionFlags()
        d = flags.to_dict()
        assert "normal_balance_violations" in d
        assert "zero_balance_accounts" in d
        assert "near_zero_accounts" in d
        assert "dominant_accounts" in d


class TestSuggestedProcedures:
    """Tests for dynamic procedure generation."""

    def test_procedures_for_violations(self):
        from population_profile_engine import NormalBalanceViolation, TopAccount

        flags = ExceptionFlags(
            normal_balance_violations=[NormalBalanceViolation("1210", "Acc Dep", "Asset", "Debit", "Credit", -100.0)]
        )
        top = [TopAccount(1, "Big", "Revenue", -5000.0, 5000.0, 50.0)]
        procs = _generate_suggested_procedures(0.75, "High", top, flags, None)
        areas = [p.area for p in procs]
        assert "Normal Balance Violations" in areas
        assert "Concentration Risk" in areas

    def test_procedures_for_zeros(self):
        from population_profile_engine import TopAccount, ZeroBalanceAccount

        flags = ExceptionFlags(zero_balance_accounts=[ZeroBalanceAccount("1100", "Inactive", "Asset", 0.0, True)])
        top = [TopAccount(1, "Big", "Revenue", -5000.0, 5000.0, 50.0)]
        procs = _generate_suggested_procedures(0.5, "Moderate", top, flags, None)
        areas = [p.area for p in procs]
        assert "Zero-Balance Accounts" in areas

    def test_procedures_sorted_by_priority(self):
        from population_profile_engine import (
            NormalBalanceViolation,
            TopAccount,
            ZeroBalanceAccount,
        )

        flags = ExceptionFlags(
            normal_balance_violations=[NormalBalanceViolation("1210", "Acc Dep", "Asset", "Debit", "Credit", -100.0)],
            zero_balance_accounts=[ZeroBalanceAccount("1100", "Inactive", "Asset", 0.0, True)],
        )
        top = [TopAccount(1, "Big", "Revenue", -5000.0, 5000.0, 50.0)]
        procs = _generate_suggested_procedures(0.75, "High", top, flags, None)
        priorities = [p.priority for p in procs]
        # High should come before Low
        high_idx = next(i for i, p in enumerate(priorities) if p == "High")
        low_idx = next(i for i, p in enumerate(priorities) if p == "Low")
        assert high_idx < low_idx

    def test_benford_nonconforming_procedure(self):
        from population_profile_engine import TopAccount

        flags = ExceptionFlags()
        top = [TopAccount(1, "Big", "Revenue", -5000.0, 5000.0, 50.0)]
        benford = {
            "passed_prechecks": True,
            "conformity_level": "nonconforming",
            "most_deviated_digits": [1, 5],
            "chi_squared": 25.5,
        }
        procs = _generate_suggested_procedures(0.5, "Moderate", top, flags, benford)
        areas = [p.area for p in procs]
        assert "Benford's Law Deviation" in areas


class TestDataQuality:
    """Tests for data quality score computation."""

    def test_perfect_quality(self):
        entries = [
            ("Cash", 1000.0, 1000.0, "Asset", "1010"),
        ]
        flags = ExceptionFlags()
        dq = _compute_data_quality(entries, flags)
        assert dq.overall_score == pytest.approx(100.0, abs=0.1)
        assert dq.completeness_score == pytest.approx(100.0, abs=0.1)

    def test_quality_penalized_by_violations(self):
        from population_profile_engine import NormalBalanceViolation

        entries = [
            ("Cash", -1000.0, 1000.0, "Asset", "1010"),
        ]
        flags = ExceptionFlags(
            normal_balance_violations=[NormalBalanceViolation("1010", "Cash", "Asset", "Debit", "Credit", -1000.0)]
        )
        dq = _compute_data_quality(entries, flags)
        assert dq.violation_score < 100.0
        assert dq.overall_score < 100.0

    def test_quality_penalized_by_zeros(self):
        from population_profile_engine import ZeroBalanceAccount

        entries = [
            ("Cash", 1000.0, 1000.0, "Asset", "1010"),
            ("Empty", 0.0, 0.0, "Asset", "1020"),
        ]
        flags = ExceptionFlags(zero_balance_accounts=[ZeroBalanceAccount("1020", "Empty", "Asset", 0.0, True)])
        dq = _compute_data_quality(entries, flags)
        assert dq.zero_balance_score < 100.0

    def test_empty_entries(self):
        dq = _compute_data_quality([], ExceptionFlags())
        assert dq.overall_score == 0.0


class TestRunPopulationProfile:
    """Tests for the standalone entry point."""

    def test_missing_columns(self):
        """Should return empty report if columns can't be detected."""
        result = run_population_profile(
            ["foo", "bar", "baz"],
            [{"foo": "A", "bar": "B", "baz": "C"}],
            "test.csv",
        )
        assert result.account_count == 0

    def test_basic_parsed_data(self):
        """Should compute profile from raw parsed data."""
        cols = ["Account", "Debit", "Credit"]
        rows = [
            {"Account": "Cash", "Debit": "5000", "Credit": "0"},
            {"Account": "AR", "Debit": "3000", "Credit": "0"},
            {"Account": "AP", "Debit": "0", "Credit": "2000"},
        ]
        result = run_population_profile(cols, rows, "test.csv")
        assert result.account_count == 3
        assert result.total_abs_balance == pytest.approx(10000.0)

    def test_duplicate_accounts_aggregate(self):
        """Multiple rows for same account should aggregate."""
        cols = ["Account", "Debit", "Credit"]
        rows = [
            {"Account": "Cash", "Debit": "1000", "Credit": "0"},
            {"Account": "Cash", "Debit": "2000", "Credit": "0"},
            {"Account": "AP", "Debit": "0", "Credit": "500"},
        ]
        result = run_population_profile(cols, rows, "test.csv")
        assert result.account_count == 2  # Cash + AP
        # Cash: 3000 debit, AP: 500 credit
        assert result.total_abs_balance == pytest.approx(3500.0)


class TestRouteRegistration:
    """Test that population profile routes are registered in the app."""

    def test_population_profile_route(self):
        from main import app

        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/audit/population-profile" in paths

    def test_population_profile_memo_route(self):
        from main import app

        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/export/population-profile-memo" in paths

    def test_population_profile_csv_route(self):
        from main import app

        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/export/csv/population-profile" in paths
