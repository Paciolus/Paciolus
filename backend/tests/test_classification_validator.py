"""
Tests for Classification Validator — Sprint 95

Tests 6 structural chart-of-accounts checks:
  CV-1: Duplicate Account Numbers
  CV-2: Orphan Accounts
  CV-3: Unclassified Accounts
  CV-4: Account Number Gaps
  CV-5: Inconsistent Naming
  CV-6: Sign Anomalies
"""


from classification_validator import (
    ISSUE_TYPE_LABELS,
    ClassificationIssueType,
    ClassificationResult,
    check_duplicate_numbers,
    check_inconsistent_naming,
    check_number_gaps,
    check_orphan_accounts,
    check_sign_anomalies,
    check_unclassified_accounts,
    extract_account_number,
    extract_numeric_prefix,
    run_classification_validation,
)

# =============================================================================
# Test Helpers
# =============================================================================

class TestHelpers:
    def test_extract_account_number_simple(self):
        assert extract_account_number("1000 Cash") == "1000"

    def test_extract_account_number_with_dash(self):
        assert extract_account_number("1000-01 Petty Cash") == "100001"

    def test_extract_account_number_with_dot(self):
        assert extract_account_number("1000.01 Cash") == "100001"

    def test_extract_account_number_no_number(self):
        assert extract_account_number("Cash on Hand") is None

    def test_extract_account_number_just_number(self):
        assert extract_account_number("1000") == "1000"

    def test_extract_numeric_prefix(self):
        assert extract_numeric_prefix("1000 Cash") == 1000

    def test_extract_numeric_prefix_no_number(self):
        assert extract_numeric_prefix("Revenue") is None


# =============================================================================
# CV-1: Duplicate Account Numbers
# =============================================================================

class TestDuplicateNumbers:
    def test_no_duplicates(self):
        accounts = {
            "1000 Cash": {"debit": 1000, "credit": 0},
            "2000 AP": {"debit": 0, "credit": 500},
        }
        issues = check_duplicate_numbers(accounts)
        assert len(issues) == 0

    def test_duplicate_found(self):
        accounts = {
            "1000 Cash": {"debit": 1000, "credit": 0},
            "1000 Petty Cash": {"debit": 200, "credit": 0},
        }
        issues = check_duplicate_numbers(accounts)
        assert len(issues) == 2
        assert all(i.issue_type == ClassificationIssueType.DUPLICATE_NUMBER for i in issues)
        assert all(i.severity == "high" for i in issues)

    def test_same_name_not_flagged(self):
        """Exact same name (e.g., duplicated in source) should not flag."""
        accounts = {
            "1000 Cash": {"debit": 1000, "credit": 0},
            "1000 cash": {"debit": 200, "credit": 0},
        }
        issues = check_duplicate_numbers(accounts)
        # Same name (case-insensitive) — not flagged as different
        assert len(issues) == 0

    def test_no_account_numbers(self):
        accounts = {
            "Cash on Hand": {"debit": 1000, "credit": 0},
            "Accounts Payable": {"debit": 0, "credit": 500},
        }
        issues = check_duplicate_numbers(accounts)
        assert len(issues) == 0

    def test_triple_duplicate(self):
        accounts = {
            "1000 Cash": {"debit": 1000, "credit": 0},
            "1000 Petty Cash": {"debit": 200, "credit": 0},
            "1000 Cash Equivalents": {"debit": 50, "credit": 0},
        }
        issues = check_duplicate_numbers(accounts)
        assert len(issues) == 3

    def test_to_dict(self):
        accounts = {
            "1000 Cash": {"debit": 1000, "credit": 0},
            "1000 Petty Cash": {"debit": 200, "credit": 0},
        }
        issues = check_duplicate_numbers(accounts)
        d = issues[0].to_dict()
        assert d["issue_type"] == "duplicate_number"
        assert d["severity"] == "high"
        assert d["confidence"] == 0.95


# =============================================================================
# CV-2: Orphan Accounts
# =============================================================================

class TestOrphanAccounts:
    def test_no_orphans(self):
        accounts = {
            "1000 Cash": {"debit": 1000, "credit": 0},
            "2000 AP": {"debit": 0, "credit": 500},
        }
        issues = check_orphan_accounts(accounts)
        assert len(issues) == 0

    def test_orphan_found(self):
        accounts = {
            "1000 Cash": {"debit": 1000, "credit": 0},
            "9999 Inactive": {"debit": 0, "credit": 0},
        }
        issues = check_orphan_accounts(accounts)
        assert len(issues) == 1
        assert issues[0].issue_type == ClassificationIssueType.ORPHAN_ACCOUNT
        assert issues[0].severity == "medium"
        assert issues[0].account_name == "9999 Inactive"

    def test_zero_balance_nonzero_activity_not_orphan(self):
        """Debit=100, credit=100 => net zero but has activity — NOT orphan."""
        accounts = {
            "3000 Clearing": {"debit": 100, "credit": 100},
        }
        issues = check_orphan_accounts(accounts)
        assert len(issues) == 0

    def test_near_zero_is_orphan(self):
        accounts = {
            "5000 Old Expense": {"debit": 0.005, "credit": 0.003},
        }
        issues = check_orphan_accounts(accounts)
        assert len(issues) == 1

    def test_multiple_orphans(self):
        accounts = {
            "1000 Active": {"debit": 5000, "credit": 0},
            "8000 Dormant A": {"debit": 0, "credit": 0},
            "8001 Dormant B": {"debit": 0, "credit": 0},
        }
        issues = check_orphan_accounts(accounts)
        assert len(issues) == 2

    def test_only_credit_not_orphan(self):
        accounts = {
            "2000 AP": {"debit": 0, "credit": 500},
        }
        issues = check_orphan_accounts(accounts)
        assert len(issues) == 0


# =============================================================================
# CV-3: Unclassified Accounts
# =============================================================================

class TestUnclassifiedAccounts:
    def test_all_classified(self):
        accounts = {
            "1000 Cash": {"debit": 1000, "credit": 0},
            "2000 AP": {"debit": 0, "credit": 500},
        }
        classifications = {"1000 Cash": "asset", "2000 AP": "liability"}
        issues = check_unclassified_accounts(accounts, classifications)
        assert len(issues) == 0

    def test_unknown_found(self):
        accounts = {
            "9999 Mystery": {"debit": 5000, "credit": 0},
        }
        classifications = {"9999 Mystery": "unknown"}
        issues = check_unclassified_accounts(accounts, classifications)
        assert len(issues) == 1
        assert issues[0].issue_type == ClassificationIssueType.UNCLASSIFIED

    def test_missing_classification(self):
        accounts = {
            "1000 Cash": {"debit": 1000, "credit": 0},
        }
        classifications = {}  # Empty — all unknown
        issues = check_unclassified_accounts(accounts, classifications)
        assert len(issues) == 1

    def test_material_gets_high_severity(self):
        accounts = {
            "9999 Big Unknown": {"debit": 50000, "credit": 0},
        }
        classifications = {"9999 Big Unknown": "unknown"}
        issues = check_unclassified_accounts(accounts, classifications)
        assert issues[0].severity == "high"

    def test_immaterial_gets_medium_severity(self):
        accounts = {
            "9999 Small Unknown": {"debit": 100, "credit": 0},
        }
        classifications = {"9999 Small Unknown": "unknown"}
        issues = check_unclassified_accounts(accounts, classifications)
        assert issues[0].severity == "medium"

    def test_empty_string_category(self):
        accounts = {"Misc": {"debit": 100, "credit": 0}}
        classifications = {"Misc": ""}
        issues = check_unclassified_accounts(accounts, classifications)
        assert len(issues) == 1


# =============================================================================
# CV-4: Account Number Gaps
# =============================================================================

class TestNumberGaps:
    def test_no_gaps(self):
        accounts = {
            "1000 Cash": {"debit": 1000, "credit": 0},
            "1010 Receivables": {"debit": 500, "credit": 0},
            "1020 Inventory": {"debit": 300, "credit": 0},
            "1030 Prepaid": {"debit": 100, "credit": 0},
        }
        classifications = {k: "asset" for k in accounts}
        issues = check_number_gaps(accounts, classifications, gap_threshold=100)
        assert len(issues) == 0

    def test_gap_found(self):
        accounts = {
            "1000 Cash": {"debit": 1000, "credit": 0},
            "1010 Receivables": {"debit": 500, "credit": 0},
            "1200 Fixed Assets": {"debit": 300, "credit": 0},
            "1250 Equipment": {"debit": 100, "credit": 0},
        }
        classifications = {k: "asset" for k in accounts}
        issues = check_number_gaps(accounts, classifications, gap_threshold=100)
        assert len(issues) == 1
        assert issues[0].issue_type == ClassificationIssueType.NUMBER_GAP
        assert issues[0].severity == "low"

    def test_skip_unknown_category(self):
        accounts = {
            "1000 A": {"debit": 1000, "credit": 0},
            "5000 B": {"debit": 500, "credit": 0},
            "9000 C": {"debit": 300, "credit": 0},
        }
        classifications = {k: "unknown" for k in accounts}
        issues = check_number_gaps(accounts, classifications)
        assert len(issues) == 0

    def test_small_group_skipped(self):
        accounts = {
            "1000 Cash": {"debit": 1000, "credit": 0},
            "5000 Revenue": {"debit": 0, "credit": 500},
        }
        classifications = {"1000 Cash": "asset", "5000 Revenue": "revenue"}
        issues = check_number_gaps(accounts, classifications)
        assert len(issues) == 0

    def test_different_categories_separate(self):
        accounts = {
            "1000 Cash": {"debit": 1000, "credit": 0},
            "1010 AR": {"debit": 500, "credit": 0},
            "1020 Inventory": {"debit": 300, "credit": 0},
            "5000 Sales": {"debit": 0, "credit": 1000},
            "5010 Service": {"debit": 0, "credit": 500},
            "5020 Interest": {"debit": 0, "credit": 100},
        }
        classifications = {
            "1000 Cash": "asset", "1010 AR": "asset", "1020 Inventory": "asset",
            "5000 Sales": "revenue", "5010 Service": "revenue", "5020 Interest": "revenue",
        }
        issues = check_number_gaps(accounts, classifications, gap_threshold=100)
        assert len(issues) == 0  # No gaps within categories


# =============================================================================
# CV-5: Inconsistent Naming
# =============================================================================

class TestNamingInconsistency:
    def test_consistent_group(self):
        accounts = {
            "5000 Expense - Rent": {"debit": 1000, "credit": 0},
            "5010 Expense - Utilities": {"debit": 500, "credit": 0},
            "5020 Expense - Supplies": {"debit": 300, "credit": 0},
            "5030 Expense - Travel": {"debit": 200, "credit": 0},
        }
        classifications = {k: "expense" for k in accounts}
        issues = check_inconsistent_naming(accounts, classifications)
        assert len(issues) == 0

    def test_outlier_found(self):
        accounts = {
            "5000 Expense - Rent": {"debit": 1000, "credit": 0},
            "5010 Expense - Utilities": {"debit": 500, "credit": 0},
            "5020 Expense - Supplies": {"debit": 300, "credit": 0},
            "5030 Expense - Travel": {"debit": 200, "credit": 0},
            "5040 Misc Cost": {"debit": 100, "credit": 0},
        }
        classifications = {k: "expense" for k in accounts}
        issues = check_inconsistent_naming(accounts, classifications)
        # "Misc" vs "Expense" prefix — should be flagged
        assert len(issues) >= 1
        assert issues[0].issue_type == ClassificationIssueType.INCONSISTENT_NAMING

    def test_small_group_skipped(self):
        accounts = {
            "1000 Cash": {"debit": 1000, "credit": 0},
            "1010 Receivables": {"debit": 500, "credit": 0},
        }
        classifications = {k: "asset" for k in accounts}
        issues = check_inconsistent_naming(accounts, classifications, min_group_size=4)
        assert len(issues) == 0

    def test_mixed_patterns_no_dominant(self):
        """If no prefix dominates (>40%), no flags."""
        accounts = {
            "5000 A - Rent": {"debit": 1000, "credit": 0},
            "5010 B - Utilities": {"debit": 500, "credit": 0},
            "5020 C - Supplies": {"debit": 300, "credit": 0},
            "5030 D - Travel": {"debit": 200, "credit": 0},
        }
        classifications = {k: "expense" for k in accounts}
        issues = check_inconsistent_naming(accounts, classifications)
        assert len(issues) == 0

    def test_unknown_category_excluded(self):
        accounts = {
            "X1 Foo": {"debit": 1000, "credit": 0},
            "X2 Bar": {"debit": 500, "credit": 0},
            "X3 Baz": {"debit": 300, "credit": 0},
            "X4 Qux": {"debit": 200, "credit": 0},
        }
        classifications = {k: "unknown" for k in accounts}
        issues = check_inconsistent_naming(accounts, classifications)
        assert len(issues) == 0

    def test_similar_prefix_not_flagged(self):
        """Prefixes that are similar enough should not be flagged."""
        accounts = {
            "5000 Expense - Rent": {"debit": 1000, "credit": 0},
            "5010 Expense - Utilities": {"debit": 500, "credit": 0},
            "5020 Expense - Supplies": {"debit": 300, "credit": 0},
            "5030 Expenses - Travel": {"debit": 200, "credit": 0},
        }
        classifications = {k: "expense" for k in accounts}
        issues = check_inconsistent_naming(accounts, classifications)
        # "Expense" vs "Expenses" are similar, should not flag
        assert len(issues) == 0


# =============================================================================
# CV-6: Sign Anomalies
# =============================================================================

class TestSignAnomalies:
    def test_normal_balances(self):
        accounts = {
            "Cash": {"debit": 1000, "credit": 0},
            "AP": {"debit": 0, "credit": 500},
        }
        classifications = {"Cash": "asset", "AP": "liability"}
        issues = check_sign_anomalies(accounts, classifications)
        assert len(issues) == 0

    def test_credit_asset_flagged(self):
        accounts = {
            "1000 Cash": {"debit": 0, "credit": 500},
        }
        classifications = {"1000 Cash": "asset"}
        issues = check_sign_anomalies(accounts, classifications)
        assert len(issues) == 1
        assert issues[0].issue_type == ClassificationIssueType.SIGN_ANOMALY
        assert "credit" in issues[0].description
        assert issues[0].severity == "medium"

    def test_debit_liability_flagged(self):
        accounts = {
            "2000 AP": {"debit": 500, "credit": 0},
        }
        classifications = {"2000 AP": "liability"}
        issues = check_sign_anomalies(accounts, classifications)
        assert len(issues) == 1

    def test_debit_revenue_flagged(self):
        accounts = {
            "4000 Sales": {"debit": 1000, "credit": 0},
        }
        classifications = {"4000 Sales": "revenue"}
        issues = check_sign_anomalies(accounts, classifications)
        assert len(issues) == 1

    def test_credit_expense_flagged(self):
        accounts = {
            "5000 Rent": {"debit": 0, "credit": 1000},
        }
        classifications = {"5000 Rent": "expense"}
        issues = check_sign_anomalies(accounts, classifications)
        assert len(issues) == 1

    def test_unknown_category_ignored(self):
        accounts = {
            "Misc": {"debit": 0, "credit": 500},
        }
        classifications = {"Misc": "unknown"}
        issues = check_sign_anomalies(accounts, classifications)
        assert len(issues) == 0


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    def test_full_pipeline(self):
        accounts = {
            "1000 Cash": {"debit": 5000, "credit": 0},
            "1000 Petty Cash": {"debit": 200, "credit": 0},
            "2000 AP": {"debit": 0, "credit": 3000},
            "5000 Expense - Rent": {"debit": 1000, "credit": 0},
            "9999 Inactive": {"debit": 0, "credit": 0},
        }
        classifications = {
            "1000 Cash": "asset",
            "1000 Petty Cash": "asset",
            "2000 AP": "liability",
            "5000 Expense - Rent": "expense",
            "9999 Inactive": "unknown",
        }
        result = run_classification_validation(accounts, classifications)
        assert isinstance(result, ClassificationResult)
        assert len(result.issues) > 0
        # Should have: duplicate (1000x2), orphan (9999), unclassified (9999)
        types_found = set(i.issue_type for i in result.issues)
        assert ClassificationIssueType.DUPLICATE_NUMBER in types_found
        assert ClassificationIssueType.ORPHAN_ACCOUNT in types_found

    def test_quality_score_perfect(self):
        accounts = {
            "1000 Cash": {"debit": 5000, "credit": 0},
            "2000 AP": {"debit": 0, "credit": 3000},
        }
        classifications = {"1000 Cash": "asset", "2000 AP": "liability"}
        result = run_classification_validation(accounts, classifications)
        assert result.quality_score == 100.0

    def test_quality_score_reduced(self):
        accounts = {
            "1000 Cash": {"debit": 5000, "credit": 0},
            "1000 Petty Cash": {"debit": 200, "credit": 0},
        }
        classifications = {"1000 Cash": "asset", "1000 Petty Cash": "asset"}
        result = run_classification_validation(accounts, classifications)
        assert result.quality_score < 100.0

    def test_to_dict(self):
        accounts = {
            "1000 Cash": {"debit": 5000, "credit": 0},
            "2000 AP": {"debit": 0, "credit": 3000},
        }
        classifications = {"1000 Cash": "asset", "2000 AP": "liability"}
        result = run_classification_validation(accounts, classifications)
        d = result.to_dict()
        assert "issues" in d
        assert "quality_score" in d
        assert "issue_counts" in d
        assert "total_issues" in d
        assert isinstance(d["quality_score"], float)

    def test_issue_counts(self):
        accounts = {
            "1000 Cash": {"debit": 5000, "credit": 0},
            "1000 Petty Cash": {"debit": 200, "credit": 0},
            "9999 Inactive": {"debit": 0, "credit": 0},
        }
        classifications = {
            "1000 Cash": "asset",
            "1000 Petty Cash": "asset",
            "9999 Inactive": "unknown",
        }
        result = run_classification_validation(accounts, classifications)
        assert result.issue_counts.get("duplicate_number", 0) >= 2
        assert result.issue_counts.get("orphan_account", 0) >= 1


# =============================================================================
# Edge Cases
# =============================================================================

class TestEdgeCases:
    def test_empty_accounts(self):
        result = run_classification_validation({}, {})
        assert len(result.issues) == 0
        assert result.quality_score == 100.0

    def test_single_account(self):
        accounts = {"1000 Cash": {"debit": 5000, "credit": 0}}
        classifications = {"1000 Cash": "asset"}
        result = run_classification_validation(accounts, classifications)
        assert result.quality_score == 100.0

    def test_all_unknown(self):
        accounts = {
            "A": {"debit": 1000, "credit": 0},
            "B": {"debit": 500, "credit": 0},
        }
        classifications = {"A": "unknown", "B": "unknown"}
        result = run_classification_validation(accounts, classifications)
        # Should flag both as unclassified
        unclassified = [i for i in result.issues if i.issue_type == ClassificationIssueType.UNCLASSIFIED]
        assert len(unclassified) == 2

    def test_all_zero_balance(self):
        accounts = {
            "A": {"debit": 0, "credit": 0},
            "B": {"debit": 0, "credit": 0},
        }
        classifications = {"A": "asset", "B": "liability"}
        result = run_classification_validation(accounts, classifications)
        orphans = [i for i in result.issues if i.issue_type == ClassificationIssueType.ORPHAN_ACCOUNT]
        assert len(orphans) == 2

    def test_issue_type_labels_complete(self):
        for issue_type in ClassificationIssueType:
            assert issue_type in ISSUE_TYPE_LABELS
