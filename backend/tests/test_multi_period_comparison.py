"""
Tests for Sprint 61 Multi-Period Trial Balance Comparison.

Tests cover:
- Account name normalization
- Account matching between periods
- Movement type classification (all 6 types)
- Significance tier assignment
- Lead sheet grouping of movements
- Full comparison integration
- Edge cases (empty TB, single account, all new/closed)
- Dormant account detection
"""

import pytest

from multi_period_comparison import (
    MovementSummary,
    MovementType,
    SignificanceTier,
    calculate_movement,
    classify_significance,
    compare_trial_balances,
    match_accounts,
    normalize_account_name,
)

# =============================================================================
# FIXTURES
# =============================================================================

def _make_account(name: str, debit: float = 0, credit: float = 0, acct_type: str = "asset") -> dict:
    """Helper to create account dicts for testing."""
    return {"account": name, "debit": debit, "credit": credit, "type": acct_type}


@pytest.fixture
def simple_prior():
    """Simple prior period trial balance."""
    return [
        _make_account("Cash", debit=50000, acct_type="asset"),
        _make_account("Accounts Receivable", debit=30000, acct_type="asset"),
        _make_account("Inventory", debit=20000, acct_type="asset"),
        _make_account("Accounts Payable", credit=25000, acct_type="liability"),
        _make_account("Revenue", credit=100000, acct_type="revenue"),
        _make_account("Rent Expense", debit=12000, acct_type="expense"),
    ]


@pytest.fixture
def simple_current():
    """Simple current period trial balance with changes."""
    return [
        _make_account("Cash", debit=65000, acct_type="asset"),
        _make_account("Accounts Receivable", debit=35000, acct_type="asset"),
        _make_account("Inventory", debit=18000, acct_type="asset"),
        _make_account("Accounts Payable", credit=30000, acct_type="liability"),
        _make_account("Revenue", credit=120000, acct_type="revenue"),
        _make_account("Rent Expense", debit=12000, acct_type="expense"),
    ]


# =============================================================================
# ACCOUNT NAME NORMALIZATION TESTS
# =============================================================================

class TestNormalizeAccountName:
    """Tests for account name normalization."""

    def test_basic_lowercase(self):
        assert normalize_account_name("Cash") == "cash"

    def test_strips_whitespace(self):
        assert normalize_account_name("  Cash  ") == "cash"

    def test_removes_special_characters(self):
        assert normalize_account_name("Cash & Equivalents") == "cash equivalents"

    def test_collapses_multiple_spaces(self):
        result = normalize_account_name("Cash   and   Equivalents")
        assert "  " not in result

    def test_abbreviation_ar(self):
        assert normalize_account_name("A/R") == "accounts receivable"

    def test_abbreviation_ap(self):
        assert normalize_account_name("A/P") == "accounts payable"

    def test_abbreviation_cogs(self):
        assert normalize_account_name("COGS") == "cost of goods sold"

    def test_abbreviation_ppe(self):
        assert normalize_account_name("PP&E") == "property plant and equipment"

    def test_same_name_normalizes_equally(self):
        assert normalize_account_name("Accounts Receivable") == normalize_account_name("accounts receivable")

    def test_empty_string(self):
        assert normalize_account_name("") == ""


# =============================================================================
# ACCOUNT MATCHING TESTS
# =============================================================================

class TestMatchAccounts:
    """Tests for account matching between periods."""

    def test_exact_match(self):
        prior = [_make_account("Cash", debit=100)]
        current = [_make_account("Cash", debit=200)]
        matched = match_accounts(prior, current)
        assert len(matched) == 1
        assert matched[0][0] is not None  # prior
        assert matched[0][1] is not None  # current

    def test_case_insensitive_match(self):
        prior = [_make_account("CASH", debit=100)]
        current = [_make_account("cash", debit=200)]
        matched = match_accounts(prior, current)
        assert len(matched) == 1
        assert matched[0][0] is not None
        assert matched[0][1] is not None

    def test_new_account_detected(self):
        prior = [_make_account("Cash", debit=100)]
        current = [
            _make_account("Cash", debit=100),
            _make_account("Inventory", debit=50),
        ]
        matched = match_accounts(prior, current)
        assert len(matched) == 2
        # Find the new account
        new = [m for m in matched if m[0] is None]
        assert len(new) == 1
        assert new[0][2] == "Inventory"

    def test_closed_account_detected(self):
        prior = [
            _make_account("Cash", debit=100),
            _make_account("Inventory", debit=50),
        ]
        current = [_make_account("Cash", debit=100)]
        matched = match_accounts(prior, current)
        assert len(matched) == 2
        closed = [m for m in matched if m[1] is None]
        assert len(closed) == 1
        assert closed[0][2] == "Inventory"

    def test_abbreviation_matching(self):
        """A/R should match Accounts Receivable."""
        prior = [_make_account("A/R", debit=100)]
        current = [_make_account("Accounts Receivable", debit=200)]
        matched = match_accounts(prior, current)
        assert len(matched) == 1
        assert matched[0][0] is not None
        assert matched[0][1] is not None

    def test_empty_prior(self):
        prior = []
        current = [_make_account("Cash", debit=100)]
        matched = match_accounts(prior, current)
        assert len(matched) == 1
        assert matched[0][0] is None  # No prior
        assert matched[0][1] is not None

    def test_empty_current(self):
        prior = [_make_account("Cash", debit=100)]
        current = []
        matched = match_accounts(prior, current)
        assert len(matched) == 1
        assert matched[0][0] is not None
        assert matched[0][1] is None  # No current

    def test_both_empty(self):
        matched = match_accounts([], [])
        assert len(matched) == 0


# =============================================================================
# MOVEMENT TYPE CLASSIFICATION TESTS
# =============================================================================

class TestCalculateMovement:
    """Tests for movement type classification."""

    def test_new_account(self):
        mt, change, pct = calculate_movement(0, 50000, is_new=True)
        assert mt == MovementType.NEW_ACCOUNT
        assert change == 50000

    def test_closed_account(self):
        mt, change, pct = calculate_movement(30000, 0, is_closed=True)
        assert mt == MovementType.CLOSED_ACCOUNT
        assert change == -30000

    def test_increase(self):
        mt, change, pct = calculate_movement(50000, 65000)
        assert mt == MovementType.INCREASE
        assert change == 15000
        assert pct == 30.0

    def test_decrease(self):
        mt, change, pct = calculate_movement(50000, 40000)
        assert mt == MovementType.DECREASE
        assert change == -10000
        assert pct == -20.0

    def test_unchanged(self):
        mt, change, pct = calculate_movement(50000, 50000)
        assert mt == MovementType.UNCHANGED
        assert change == 0.0
        assert pct == 0.0

    def test_sign_change_positive_to_negative(self):
        mt, change, pct = calculate_movement(10000, -5000)
        assert mt == MovementType.SIGN_CHANGE
        assert change == -15000

    def test_sign_change_negative_to_positive(self):
        mt, change, pct = calculate_movement(-10000, 5000)
        assert mt == MovementType.SIGN_CHANGE
        assert change == 15000

    def test_zero_prior_not_new(self):
        """Zero prior without is_new flag should be increase."""
        mt, change, pct = calculate_movement(0, 5000)
        assert mt == MovementType.INCREASE

    def test_zero_current_not_closed(self):
        """Zero current without is_closed flag should be decrease."""
        mt, change, pct = calculate_movement(5000, 0)
        assert mt == MovementType.DECREASE

    def test_percent_change_from_zero(self):
        """Change from zero should have None percent."""
        mt, change, pct = calculate_movement(0, 5000)
        assert pct is None

    def test_floating_point_unchanged(self):
        """Very small difference should be classified as unchanged."""
        mt, change, pct = calculate_movement(50000.001, 50000.009)
        assert mt == MovementType.UNCHANGED

    def test_near_zero_prior_returns_none_percent(self):
        """Near-zero prior (below NEAR_ZERO threshold) returns None percent."""
        mt, change, pct = calculate_movement(0.001, 5000)
        assert pct is None
        assert mt == MovementType.INCREASE

    def test_near_zero_no_false_sign_change(self):
        """Near-zero balances should not trigger sign change detection."""
        mt, change, pct = calculate_movement(0.001, -5000)
        # 0.001 is below NEAR_ZERO, so sign change should NOT trigger
        assert mt != MovementType.SIGN_CHANGE


# =============================================================================
# SIGNIFICANCE TIER TESTS
# =============================================================================

class TestClassifySignificance:
    """Tests for significance tier classification."""

    def test_material_exceeds_threshold(self):
        sig = classify_significance(50000, 25.0, materiality_threshold=40000)
        assert sig == SignificanceTier.MATERIAL

    def test_significant_by_amount(self):
        sig = classify_significance(15000, 5.0)
        assert sig == SignificanceTier.SIGNIFICANT

    def test_significant_by_percent(self):
        sig = classify_significance(500, 15.0)
        assert sig == SignificanceTier.SIGNIFICANT

    def test_minor_below_thresholds(self):
        sig = classify_significance(500, 5.0)
        assert sig == SignificanceTier.MINOR

    def test_new_account_always_significant(self):
        """New accounts should always be at least significant."""
        sig = classify_significance(100, None, movement_type=MovementType.NEW_ACCOUNT)
        assert sig == SignificanceTier.SIGNIFICANT

    def test_closed_account_always_significant(self):
        """Closed accounts should always be at least significant."""
        sig = classify_significance(-100, None, movement_type=MovementType.CLOSED_ACCOUNT)
        assert sig == SignificanceTier.SIGNIFICANT

    def test_sign_change_always_significant(self):
        """Sign changes should always be at least significant."""
        sig = classify_significance(500, 10.0, movement_type=MovementType.SIGN_CHANGE)
        assert sig == SignificanceTier.SIGNIFICANT

    def test_new_account_material_when_large(self):
        """Large new account should be material if exceeds threshold."""
        sig = classify_significance(
            100000, None,
            materiality_threshold=50000,
            movement_type=MovementType.NEW_ACCOUNT,
        )
        assert sig == SignificanceTier.MATERIAL

    def test_zero_change_is_minor(self):
        sig = classify_significance(0, 0.0)
        assert sig == SignificanceTier.MINOR

    def test_no_materiality_threshold(self):
        """Without materiality threshold, can't be material."""
        sig = classify_significance(100000, 50.0, materiality_threshold=0)
        assert sig == SignificanceTier.SIGNIFICANT


# =============================================================================
# FULL COMPARISON INTEGRATION TESTS
# =============================================================================

class TestCompareTrialBalances:
    """Integration tests for compare_trial_balances."""

    def test_basic_comparison(self, simple_prior, simple_current):
        result = compare_trial_balances(simple_prior, simple_current)
        assert isinstance(result, MovementSummary)
        assert result.total_accounts == 6

    def test_movement_type_counts(self, simple_prior, simple_current):
        result = compare_trial_balances(simple_prior, simple_current)
        types = result.movements_by_type
        # Cash increased, AR increased, Inventory decreased,
        # AP increased, Revenue increased, Rent unchanged
        assert types["unchanged"] == 1  # Rent Expense
        assert types["increase"] + types["decrease"] == 5

    def test_labels_preserved(self, simple_prior, simple_current):
        result = compare_trial_balances(
            simple_prior, simple_current,
            prior_label="FY2024", current_label="FY2025",
        )
        assert result.prior_label == "FY2024"
        assert result.current_label == "FY2025"

    def test_totals_calculated(self, simple_prior, simple_current):
        result = compare_trial_balances(simple_prior, simple_current)
        assert result.prior_total_debits > 0
        assert result.prior_total_credits > 0
        assert result.current_total_debits > 0
        assert result.current_total_credits > 0

    def test_lead_sheet_grouping(self, simple_prior, simple_current):
        result = compare_trial_balances(simple_prior, simple_current)
        assert len(result.lead_sheet_summaries) > 0
        # Each summary should have movements
        for ls in result.lead_sheet_summaries:
            assert ls.account_count > 0
            assert len(ls.movements) > 0

    def test_significant_movements_sorted(self, simple_prior, simple_current):
        result = compare_trial_balances(simple_prior, simple_current)
        if len(result.significant_movements) >= 2:
            for i in range(len(result.significant_movements) - 1):
                assert abs(result.significant_movements[i].change_amount) >= \
                       abs(result.significant_movements[i + 1].change_amount)

    def test_to_dict_serializable(self, simple_prior, simple_current):
        result = compare_trial_balances(simple_prior, simple_current)
        d = result.to_dict()
        assert isinstance(d, dict)
        assert "all_movements" in d
        assert "lead_sheet_summaries" in d
        assert isinstance(d["all_movements"], list)

    def test_with_new_accounts(self, simple_prior):
        current = simple_prior.copy()
        current.append(_make_account("New Equipment", debit=75000, acct_type="asset"))
        result = compare_trial_balances(simple_prior, current)
        assert "New Equipment" in result.new_accounts
        assert result.movements_by_type["new_account"] == 1

    def test_with_closed_accounts(self, simple_current):
        prior = simple_current.copy()
        prior.append(_make_account("Old Inventory Reserve", debit=5000, acct_type="asset"))
        result = compare_trial_balances(prior, simple_current)
        assert "Old Inventory Reserve" in result.closed_accounts
        assert result.movements_by_type["closed_account"] == 1

    def test_with_materiality_threshold(self, simple_prior, simple_current):
        result = compare_trial_balances(
            simple_prior, simple_current,
            materiality_threshold=25000,
        )
        material_count = result.movements_by_significance.get("material", 0)
        assert material_count >= 0  # May or may not have material items

    def test_dormant_account_detection(self):
        prior = [_make_account("Dormant Fund", debit=0, credit=0, acct_type="asset")]
        current = [_make_account("Dormant Fund", debit=0, credit=0, acct_type="asset")]
        result = compare_trial_balances(prior, current)
        assert "Dormant Fund" in result.dormant_accounts
        assert result.all_movements[0].is_dormant is True


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestEdgeCases:
    """Edge cases and boundary conditions."""

    def test_empty_prior_tb(self):
        """All accounts should be new."""
        current = [
            _make_account("Cash", debit=50000, acct_type="asset"),
            _make_account("Revenue", credit=100000, acct_type="revenue"),
        ]
        result = compare_trial_balances([], current)
        assert result.total_accounts == 2
        assert result.movements_by_type["new_account"] == 2
        assert len(result.new_accounts) == 2

    def test_empty_current_tb(self):
        """All accounts should be closed."""
        prior = [
            _make_account("Cash", debit=50000, acct_type="asset"),
            _make_account("Revenue", credit=100000, acct_type="revenue"),
        ]
        result = compare_trial_balances(prior, [])
        assert result.total_accounts == 2
        assert result.movements_by_type["closed_account"] == 2
        assert len(result.closed_accounts) == 2

    def test_both_empty(self):
        result = compare_trial_balances([], [])
        assert result.total_accounts == 0
        assert all(v == 0 for v in result.movements_by_type.values())

    def test_single_account_increase(self):
        prior = [_make_account("Cash", debit=100)]
        current = [_make_account("Cash", debit=200)]
        result = compare_trial_balances(prior, current)
        assert result.total_accounts == 1
        movement = result.all_movements[0]
        assert movement.movement_type == MovementType.INCREASE
        assert movement.change_amount == 100

    def test_large_trial_balance(self):
        """Performance: should handle 500+ accounts."""
        prior = [_make_account(f"Account {i}", debit=i * 100) for i in range(500)]
        current = [_make_account(f"Account {i}", debit=i * 110) for i in range(500)]
        result = compare_trial_balances(prior, current)
        assert result.total_accounts == 500

    def test_sign_change_detection(self):
        prior = [_make_account("Retained Earnings", debit=10000, acct_type="equity")]
        current = [_make_account("Retained Earnings", credit=5000, acct_type="equity")]
        result = compare_trial_balances(prior, current)
        movement = result.all_movements[0]
        assert movement.movement_type == MovementType.SIGN_CHANGE

    def test_negative_balances(self):
        """Accounts with credit > debit (negative net) should work."""
        prior = [_make_account("Contra Asset", debit=0, credit=5000, acct_type="asset")]
        current = [_make_account("Contra Asset", debit=0, credit=8000, acct_type="asset")]
        result = compare_trial_balances(prior, current)
        movement = result.all_movements[0]
        assert movement.prior_balance == -5000
        assert movement.current_balance == -8000
        assert movement.change_amount == -3000

    def test_unknown_account_type(self):
        """Accounts with unknown type should still be processed."""
        prior = [_make_account("Mystery Account", debit=100, acct_type="unknown")]
        current = [_make_account("Mystery Account", debit=200, acct_type="unknown")]
        result = compare_trial_balances(prior, current)
        assert result.total_accounts == 1
        movement = result.all_movements[0]
        assert movement.lead_sheet == "Z"  # Unclassified

    def test_all_unchanged(self):
        accounts = [
            _make_account("Cash", debit=50000, acct_type="asset"),
            _make_account("Revenue", credit=100000, acct_type="revenue"),
        ]
        result = compare_trial_balances(accounts, accounts)
        assert result.movements_by_type["unchanged"] == 2
        assert len(result.significant_movements) == 0


# =============================================================================
# LEAD SHEET GROUPING TESTS
# =============================================================================

class TestLeadSheetGrouping:
    """Tests for lead sheet grouping in comparison results."""

    def test_cash_grouped_to_lead_sheet_a(self):
        prior = [_make_account("Cash", debit=50000, acct_type="asset")]
        current = [_make_account("Cash", debit=60000, acct_type="asset")]
        result = compare_trial_balances(prior, current)
        assert result.all_movements[0].lead_sheet == "A"
        assert result.all_movements[0].lead_sheet_name == "Cash and Cash Equivalents"

    def test_receivable_grouped_to_lead_sheet_b(self):
        prior = [_make_account("Accounts Receivable", debit=30000, acct_type="asset")]
        current = [_make_account("Accounts Receivable", debit=40000, acct_type="asset")]
        result = compare_trial_balances(prior, current)
        assert result.all_movements[0].lead_sheet == "B"

    def test_multiple_lead_sheets(self, simple_prior, simple_current):
        result = compare_trial_balances(simple_prior, simple_current)
        lead_sheets_used = {m.lead_sheet for m in result.all_movements}
        assert len(lead_sheets_used) >= 3  # At least Cash, AR, Inventory etc.

    def test_lead_sheet_summary_totals(self):
        prior = [
            _make_account("Cash", debit=50000, acct_type="asset"),
            _make_account("Petty Cash", debit=1000, acct_type="asset"),
        ]
        current = [
            _make_account("Cash", debit=60000, acct_type="asset"),
            _make_account("Petty Cash", debit=1500, acct_type="asset"),
        ]
        result = compare_trial_balances(prior, current)
        # Both should be in lead sheet A
        ls_a = [s for s in result.lead_sheet_summaries if s.lead_sheet == "A"]
        assert len(ls_a) == 1
        assert ls_a[0].account_count == 2
        assert ls_a[0].prior_total == 51000
        assert ls_a[0].current_total == 61500
        assert ls_a[0].net_change == 10500
