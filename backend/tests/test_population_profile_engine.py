"""
Tests for population_profile_engine.py
Sprint 287: Phase XXXIX — TB Population Profile Report
"""


import pytest

from population_profile_engine import (
    _compute_gini,
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
        assert 0.3 < gini < 0.7

    def test_all_zeros(self):
        """All zeros → 0.0 (division guard)."""
        assert _compute_gini([0.0, 0.0, 0.0]) == 0.0


class TestInterpretGini:
    """Tests for Gini interpretation labels."""

    def test_low(self):
        assert _interpret_gini(0.1) == "Low"
        assert _interpret_gini(0.29) == "Low"

    def test_moderate(self):
        assert _interpret_gini(0.3) == "Moderate"
        assert _interpret_gini(0.49) == "Moderate"

    def test_high(self):
        assert _interpret_gini(0.5) == "High"
        assert _interpret_gini(0.69) == "High"

    def test_very_high(self):
        assert _interpret_gini(0.7) == "Very High"
        assert _interpret_gini(0.95) == "Very High"


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
            "Petty Cash": {"debit": 0.005, "credit": 0.0},   # Zero bucket
            "Postage": {"debit": 500.0, "credit": 0.0},       # <$1K
            "Supplies": {"debit": 5000.0, "credit": 0.0},     # $1K–$10K
            "Vehicle": {"debit": 50000.0, "credit": 0.0},     # $10K–$100K
            "Building": {"debit": 500000.0, "credit": 0.0},   # $100K–$1M
            "Land": {"debit": 2000000.0, "credit": 0.0},      # >$1M
        }
        result = compute_population_profile(balances)

        bucket_map = {b.label: b.count for b in result.buckets}
        assert bucket_map["Zero (<$0.01)"] == 1
        assert bucket_map["<$1K"] == 1
        assert bucket_map["$1K–$10K"] == 1
        assert bucket_map["$10K–$100K"] == 1
        assert bucket_map["$100K–$1M"] == 1
        assert bucket_map[">$1M"] == 1

    def test_top_accounts_ordering(self):
        """Top accounts should be ordered by absolute balance descending."""
        balances = {
            f"Account {i}": {"debit": float(i * 100), "credit": 0.0}
            for i in range(1, 15)
        }
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

    def test_to_dict_structure(self):
        """to_dict() should produce the expected keys."""
        balances = {
            "A": {"debit": 100.0, "credit": 0.0},
            "B": {"debit": 200.0, "credit": 0.0},
        }
        result = compute_population_profile(balances)
        d = result.to_dict()
        expected_keys = {
            "account_count", "total_abs_balance", "mean_abs_balance",
            "median_abs_balance", "std_dev_abs_balance", "min_abs_balance",
            "max_abs_balance", "p25", "p75", "gini_coefficient",
            "gini_interpretation", "buckets", "top_accounts",
        }
        assert set(d.keys()) == expected_keys
        assert isinstance(d["buckets"], list)
        assert isinstance(d["top_accounts"], list)

    def test_equal_balances_gini_near_zero(self):
        """All equal non-zero balances → Gini ≈ 0."""
        balances = {
            f"Acct{i}": {"debit": 1000.0, "credit": 0.0}
            for i in range(20)
        }
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
        assert result.gini_coefficient > 0.7
        assert result.gini_interpretation == "Very High"

    def test_bucket_percentages_sum_to_100(self):
        """Bucket percent_count values should sum to ~100."""
        balances = {
            f"Acct{i}": {"debit": float(i * 100 + 50), "credit": 0.0}
            for i in range(50)
        }
        result = compute_population_profile(balances)
        total_pct = sum(b.percent_count for b in result.buckets)
        assert total_pct == pytest.approx(100.0, abs=0.5)


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
        paths = [r.path for r in app.routes if hasattr(r, 'path')]
        assert "/audit/population-profile" in paths

    def test_population_profile_memo_route(self):
        from main import app
        paths = [r.path for r in app.routes if hasattr(r, 'path')]
        assert "/export/population-profile-memo" in paths

    def test_population_profile_csv_route(self):
        from main import app
        paths = [r.path for r in app.routes if hasattr(r, 'path')]
        assert "/export/csv/population-profile" in paths
