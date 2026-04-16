"""
Tests for the Pre-Flight Data Quality Engine — Sprint 283, Sprint 510

Original 7 tests + Sprint 510 additions:
- Balance check (3 tests)
- Score breakdown (2 tests)
- Affected items (2 tests)
- Tests affected (1 test)
- to_dict serialization (1 test)
"""

from preflight_engine import (
    PreFlightReport,
    ScoreComponent,
    run_preflight,
)


class TestPreflightCleanFile:
    """Test 1: Well-formed CSV → readiness >= 90, 'Ready'."""

    def test_clean_file_high_readiness(self):
        column_names = ["Account Name", "Debit", "Credit"]
        # Sprint 631: TB must include every GAAP category or the
        # completeness check reduces readiness. Expense of 500 kept
        # but named "Cost of Goods Sold" so the Revenue/COGS gap
        # secondary check also stays silent.
        rows = [
            {"Account Name": "Cash", "Debit": 2000.0, "Credit": 0.0},
            {"Account Name": "Accounts Payable", "Debit": 0.0, "Credit": 400.0},
            {"Account Name": "Revenue", "Debit": 0.0, "Credit": 1500.0},
            {"Account Name": "Cost of Goods Sold", "Debit": 500.0, "Credit": 0.0},
            {"Account Name": "Retained Earnings", "Debit": 0.0, "Credit": 600.0},
        ]

        report = run_preflight(column_names, rows, "clean.csv")

        assert isinstance(report, PreFlightReport)
        assert report.readiness_score >= 90
        assert report.readiness_label == "Ready"
        assert report.row_count == 5
        assert report.column_count == 3
        assert report.filename == "clean.csv"

        # Column detection should find all three
        found_cols = {c.role: c for c in report.columns}
        assert found_cols["account"].status == "found"
        assert found_cols["debit"].status == "found"
        assert found_cols["credit"].status == "found"


class TestPreflightMissingColumns:
    """Test 2: Bad column names → HIGH column_detection issue."""

    def test_unrecognized_columns(self):
        column_names = ["Foo", "Bar", "Baz"]
        rows = [{"Foo": "A", "Bar": 1, "Baz": 2}]

        report = run_preflight(column_names, rows, "bad_cols.csv")

        # Should have column detection issue
        col_issues = [i for i in report.issues if i.category == "column_detection"]
        assert len(col_issues) >= 1
        assert col_issues[0].severity == "high"

        # Readiness should be significantly reduced (column_detection HIGH = -20)
        assert report.readiness_score <= 80


class TestPreflightNullValues:
    """Test 3: 10% null accounts → null_values issue."""

    def test_null_in_critical_column(self):
        column_names = ["Account Name", "Debit", "Credit"]
        rows = [
            {"Account Name": "Cash", "Debit": 1000, "Credit": 0},
            {"Account Name": None, "Debit": 500, "Credit": 0},
            {"Account Name": "", "Debit": 200, "Credit": 0},
            {"Account Name": "Revenue", "Debit": 0, "Credit": 1000},
            {"Account Name": "Equity", "Debit": 0, "Credit": 500},
            {"Account Name": "Assets", "Debit": 300, "Credit": 0},
            {"Account Name": "Supplies", "Debit": 100, "Credit": 0},
            {"Account Name": "Rent", "Debit": 400, "Credit": 0},
            {"Account Name": "Utilities", "Debit": 150, "Credit": 0},
            {"Account Name": "Insurance", "Debit": 50, "Credit": 0},
        ]

        report = run_preflight(column_names, rows, "nulls.csv")

        null_issues = [i for i in report.issues if i.category == "null_values"]
        assert len(null_issues) >= 1

        # Should detect nulls in Account Name column
        account_issue = [i for i in null_issues if "Account Name" in i.message]
        assert len(account_issue) >= 1


class TestPreflightDuplicateAccounts:
    """Test 4: Repeated codes → duplicates issue."""

    def test_duplicate_account_codes(self):
        column_names = ["Account Name", "Debit", "Credit"]
        rows = [
            {"Account Name": "Cash", "Debit": 1000, "Credit": 0},
            {"Account Name": "Cash", "Debit": 500, "Credit": 0},
            {"Account Name": "Revenue", "Debit": 0, "Credit": 2000},
            {"Account Name": "Expenses", "Debit": 800, "Credit": 0},
            {"Account Name": "Expenses", "Debit": 200, "Credit": 0},
        ]

        report = run_preflight(column_names, rows, "dupes.csv")

        dup_issues = [i for i in report.issues if i.category == "duplicates"]
        assert len(dup_issues) >= 1

        # Should list duplicates
        assert len(report.duplicates) >= 2
        cash_dup = [d for d in report.duplicates if d.account_code == "cash"]
        assert len(cash_dup) == 1
        assert cash_dup[0].count == 2


class TestPreflightEncodingAnomalies:
    """Test 5: Non-ASCII chars → encoding issue."""

    def test_non_ascii_characters(self):
        column_names = ["Account Name", "Debit", "Credit"]
        rows = [
            {"Account Name": "Café Expenses", "Debit": 500, "Credit": 0},
            {"Account Name": "Über Revenue", "Debit": 0, "Credit": 1000},
            {"Account Name": "Cash", "Debit": 200, "Credit": 0},
            {"Account Name": "Normal Account", "Debit": 100, "Credit": 0},
        ]

        report = run_preflight(column_names, rows, "encoding.csv")

        enc_issues = [i for i in report.issues if i.category == "encoding"]
        assert len(enc_issues) == 1
        assert len(report.encoding_anomalies) == 2


class TestPreflightMixedSigns:
    """Test 6: Both +/- in debit → mixed_signs issue."""

    def test_mixed_positive_negative_debits(self):
        column_names = ["Account Name", "Debit", "Credit"]
        rows = [
            {"Account Name": "Cash", "Debit": 1000, "Credit": 0},
            {"Account Name": "Cash", "Debit": -200, "Credit": 0},
            {"Account Name": "Revenue", "Debit": 0, "Credit": 500},
        ]

        report = run_preflight(column_names, rows, "mixed.csv")

        sign_issues = [i for i in report.issues if i.category == "mixed_signs"]
        assert len(sign_issues) == 1
        assert len(report.mixed_sign_accounts) == 1
        assert report.mixed_sign_accounts[0].account == "Cash"
        assert report.mixed_sign_accounts[0].positive_count == 1
        assert report.mixed_sign_accounts[0].negative_count == 1


class TestPreflightZeroBalances:
    """Test 7: 30% zero rows → zero_balance issue."""

    def test_zero_balance_rows(self):
        column_names = ["Account Name", "Debit", "Credit"]
        rows = [
            {"Account Name": "Cash", "Debit": 1000, "Credit": 0},
            {"Account Name": "Revenue", "Debit": 0, "Credit": 0},  # zero
            {"Account Name": "Expenses", "Debit": 500, "Credit": 0},
            {"Account Name": "Closed", "Debit": 0, "Credit": 0},  # zero
            {"Account Name": "Inactive", "Debit": 0, "Credit": 0},  # zero
            {"Account Name": "Equity", "Debit": 0, "Credit": 500},
            {"Account Name": "Supplies", "Debit": 100, "Credit": 0},
        ]

        report = run_preflight(column_names, rows, "zeros.csv")

        zero_issues = [i for i in report.issues if i.category == "zero_balance"]
        assert len(zero_issues) == 1
        assert report.zero_balance_count == 3
        # 3/7 ≈ 43% → should be medium severity (>20% but <50%)
        assert zero_issues[0].severity == "medium"


class TestPreflightToDict:
    """Test serialization to dict."""

    def test_to_dict_structure(self):
        column_names = ["Account Name", "Debit", "Credit"]
        rows = [{"Account Name": "Cash", "Debit": 1000, "Credit": 0}]

        report = run_preflight(column_names, rows, "test.csv")
        d = report.to_dict()

        assert "filename" in d
        assert "readiness_score" in d
        assert "readiness_label" in d
        assert "columns" in d
        assert "issues" in d
        assert "null_counts" in d
        assert isinstance(d["columns"], list)
        assert isinstance(d["issues"], list)

        # Sprint 510: new fields
        assert "balance_check" in d
        assert "score_breakdown" in d


class TestPreflightRouteRegistration:
    """Verify the /audit/preflight endpoint is registered."""

    def test_route_exists(self):
        from main import app

        route_paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/audit/preflight" in route_paths

    def test_export_memo_route_exists(self):
        from main import app

        route_paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/export/preflight-memo" in route_paths

    def test_export_csv_route_exists(self):
        from main import app

        route_paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/export/csv/preflight-issues" in route_paths


# ═══════════════════════════════════════════════════════════════
# Sprint 510: New tests
# ═══════════════════════════════════════════════════════════════


class TestPreflightBalanceCheck:
    """Sprint 510: TB balance verification."""

    def test_balanced_tb(self):
        """Balanced TB → balance_check.balanced = True, no tb_balance issue."""
        column_names = ["Account Name", "Debit", "Credit"]
        rows = [
            {"Account Name": "Cash", "Debit": 5000, "Credit": 0},
            {"Account Name": "Revenue", "Debit": 0, "Credit": 3000},
            {"Account Name": "Expenses", "Debit": 1000, "Credit": 0},
            {"Account Name": "Equity", "Debit": 0, "Credit": 3000},
        ]

        report = run_preflight(column_names, rows, "balanced.csv")

        assert report.balance_check is not None
        assert report.balance_check.balanced is True
        assert report.balance_check.total_debits == 6000.0
        assert report.balance_check.total_credits == 6000.0
        assert report.balance_check.difference == 0.0

        tb_issues = [i for i in report.issues if i.category == "tb_balance"]
        assert len(tb_issues) == 0

    def test_unbalanced_tb(self):
        """Unbalanced TB → balance_check.balanced = False, HIGH tb_balance issue."""
        column_names = ["Account Name", "Debit", "Credit"]
        rows = [
            {"Account Name": "Cash", "Debit": 5000, "Credit": 0},
            {"Account Name": "Revenue", "Debit": 0, "Credit": 3000},
            {"Account Name": "Expenses", "Debit": 1000, "Credit": 0},
            # Missing equity — debits > credits
        ]

        report = run_preflight(column_names, rows, "unbalanced.csv")

        assert report.balance_check is not None
        assert report.balance_check.balanced is False
        assert report.balance_check.total_debits == 6000.0
        assert report.balance_check.total_credits == 3000.0
        assert report.balance_check.difference == 3000.0

        tb_issues = [i for i in report.issues if i.category == "tb_balance"]
        assert len(tb_issues) == 1
        assert tb_issues[0].severity == "high"

    def test_balanced_within_tolerance(self):
        """Difference within tolerance → balanced."""
        column_names = ["Account Name", "Debit", "Credit"]
        rows = [
            {"Account Name": "Cash", "Debit": 1000.005, "Credit": 0},
            {"Account Name": "Equity", "Debit": 0, "Credit": 1000.0},
        ]

        report = run_preflight(column_names, rows, "rounding.csv")

        assert report.balance_check is not None
        assert report.balance_check.balanced is True


class TestPreflightScoreBreakdown:
    """Sprint 510: Score breakdown components."""

    def test_clean_file_all_components_100(self):
        """Clean file → all component scores should be 100."""
        column_names = ["Account Name", "Debit", "Credit"]
        # Sprint 631: include every GAAP category so the completeness
        # component also scores 100.
        rows = [
            {"Account Name": "Cash", "Debit": 1000, "Credit": 0},
            {"Account Name": "Accounts Payable", "Debit": 0, "Credit": 200},
            {"Account Name": "Retained Earnings", "Debit": 0, "Credit": 100},
            {"Account Name": "Revenue", "Debit": 0, "Credit": 1000},
            {"Account Name": "Cost of Goods Sold", "Debit": 300, "Credit": 0},
        ]

        report = run_preflight(column_names, rows, "clean.csv")

        assert len(report.score_breakdown) > 0
        for sc in report.score_breakdown:
            assert isinstance(sc, ScoreComponent)
            assert sc.score == 100.0

        # Total should be 100
        total = sum(sc.contribution for sc in report.score_breakdown)
        assert abs(total - 100.0) < 0.1

    def test_issue_reduces_component_score(self):
        """Issues should reduce the relevant component score."""
        column_names = ["Account Name", "Debit", "Credit"]
        rows = [
            {"Account Name": "Cash", "Debit": 1000, "Credit": 0},
            {"Account Name": "Cash", "Debit": -200, "Credit": 0},
            {"Account Name": "Revenue", "Debit": 0, "Credit": 800},
        ]

        report = run_preflight(column_names, rows, "issues.csv")

        # mixed_signs should have reduced score
        mixed_sc = [sc for sc in report.score_breakdown if sc.component == "mixed_signs"]
        assert len(mixed_sc) == 1
        assert mixed_sc[0].score < 100.0

        # tb_balance should still be 100 (balanced)
        tb_sc = [sc for sc in report.score_breakdown if sc.component == "tb_balance"]
        assert len(tb_sc) == 1
        assert tb_sc[0].score == 100.0


class TestPreflightAffectedItems:
    """Sprint 510: Affected item identifiers."""

    def test_encoding_affected_items(self):
        """Encoding issues should list affected account names."""
        column_names = ["Account Name", "Debit", "Credit"]
        rows = [
            {"Account Name": "Café Expenses", "Debit": 500, "Credit": 0},
            {"Account Name": "Cash", "Debit": 200, "Credit": 0},
            {"Account Name": "Revenue", "Debit": 0, "Credit": 700},
        ]

        report = run_preflight(column_names, rows, "encoding.csv")

        enc_issues = [i for i in report.issues if i.category == "encoding"]
        assert len(enc_issues) == 1
        assert "Café Expenses" in enc_issues[0].affected_items

    def test_mixed_signs_affected_items(self):
        """Mixed sign issues should list affected account names."""
        column_names = ["Account Name", "Debit", "Credit"]
        rows = [
            {"Account Name": "Cash", "Debit": 1000, "Credit": 0},
            {"Account Name": "Cash", "Debit": -200, "Credit": 0},
            {"Account Name": "Revenue", "Debit": 0, "Credit": 800},
        ]

        report = run_preflight(column_names, rows, "mixed.csv")

        sign_issues = [i for i in report.issues if i.category == "mixed_signs"]
        assert len(sign_issues) == 1
        assert "Cash" in sign_issues[0].affected_items


class TestPreflightTestsAffected:
    """Sprint 510: Tests affected count."""

    def test_issues_have_tests_affected(self):
        """All issues should have a tests_affected count > 0."""
        column_names = ["Account Name", "Debit", "Credit"]
        rows = [
            {"Account Name": "Cash", "Debit": 1000, "Credit": 0},
            {"Account Name": "Cash", "Debit": -200, "Credit": 0},
            {"Account Name": "Revenue", "Debit": 0, "Credit": 800},
        ]

        report = run_preflight(column_names, rows, "test.csv")

        for issue in report.issues:
            assert issue.tests_affected > 0, f"Issue {issue.category} has 0 tests_affected"


class TestPreflightToDictSprint510:
    """Sprint 510: Enhanced to_dict serialization."""

    def test_to_dict_has_new_issue_fields(self):
        """Issues in to_dict should have affected_items and tests_affected."""
        column_names = ["Account Name", "Debit", "Credit"]
        rows = [
            {"Account Name": "Café", "Debit": 500, "Credit": 0},
            {"Account Name": "Cash", "Debit": 200, "Credit": 0},
            {"Account Name": "Revenue", "Debit": 0, "Credit": 700},
        ]

        report = run_preflight(column_names, rows, "test.csv")
        d = report.to_dict()

        for issue in d["issues"]:
            assert "affected_items" in issue
            assert "affected_items_truncated" in issue
            assert "affected_items_total" in issue
            assert "tests_affected" in issue
            assert isinstance(issue["affected_items"], list)
            assert isinstance(issue["tests_affected"], int)

    def test_to_dict_balance_check(self):
        """to_dict should include balance_check."""
        column_names = ["Account Name", "Debit", "Credit"]
        rows = [
            {"Account Name": "Cash", "Debit": 1000, "Credit": 0},
            {"Account Name": "Equity", "Debit": 0, "Credit": 1000},
        ]

        report = run_preflight(column_names, rows, "test.csv")
        d = report.to_dict()

        assert "balance_check" in d
        bc = d["balance_check"]
        assert bc["balanced"] is True
        assert bc["total_debits"] == 1000.0
        assert bc["total_credits"] == 1000.0

    def test_to_dict_score_breakdown(self):
        """to_dict should include score_breakdown."""
        column_names = ["Account Name", "Debit", "Credit"]
        rows = [
            {"Account Name": "Cash", "Debit": 1000, "Credit": 0},
            {"Account Name": "Equity", "Debit": 0, "Credit": 1000},
        ]

        report = run_preflight(column_names, rows, "test.csv")
        d = report.to_dict()

        assert "score_breakdown" in d
        assert len(d["score_breakdown"]) > 0
        for sc in d["score_breakdown"]:
            assert "component" in sc
            assert "weight" in sc
            assert "score" in sc
            assert "contribution" in sc


# ═══════════════════════════════════════════════════════════════
# Sprint 631 — GAAP category completeness check
# ═══════════════════════════════════════════════════════════════


class TestCategoryCompleteness:
    """Sprint 631: Balance-sheet-assertion completeness checker."""

    def _full_tb(self) -> tuple[list[str], list[dict]]:
        columns = ["Account Name", "Debit", "Credit"]
        rows = [
            {"Account Name": "Cash", "Debit": 1000.0, "Credit": 0.0},
            {"Account Name": "Accounts Payable", "Debit": 0.0, "Credit": 300.0},
            {"Account Name": "Retained Earnings", "Debit": 0.0, "Credit": 200.0},
            {"Account Name": "Revenue", "Debit": 0.0, "Credit": 800.0},
            {"Account Name": "Cost of Goods Sold", "Debit": 300.0, "Credit": 0.0},
        ]
        return columns, rows

    def test_complete_tb_has_no_completeness_issue(self):
        columns, rows = self._full_tb()
        report = run_preflight(columns, rows, "complete.csv")

        completeness_issues = [i for i in report.issues if i.category == "category_completeness"]
        assert completeness_issues == []

        cc = report.category_completeness
        assert cc is not None
        assert cc.asset_count >= 1
        assert cc.liability_count >= 1
        assert cc.equity_count >= 1
        assert cc.revenue_count >= 1
        assert cc.expense_count >= 1
        assert cc.missing_categories == []
        assert cc.cogs_gap is False

    def test_missing_equity_raises_high_severity(self):
        columns = ["Account Name", "Debit", "Credit"]
        rows = [
            {"Account Name": "Cash", "Debit": 1000.0, "Credit": 0.0},
            {"Account Name": "Accounts Payable", "Debit": 0.0, "Credit": 300.0},
            {"Account Name": "Revenue", "Debit": 0.0, "Credit": 700.0},
            {"Account Name": "Cost of Goods Sold", "Debit": 400.0, "Credit": 0.0},
        ]

        report = run_preflight(columns, rows, "no_equity.csv")
        issues = [i for i in report.issues if i.category == "category_completeness"]
        assert len(issues) == 1
        assert issues[0].severity == "high"
        assert "Equity" in issues[0].message

        cc = report.category_completeness
        assert cc is not None
        assert cc.equity_count == 0
        assert "Equity" in cc.missing_categories

    def test_revenue_with_zero_cogs_flags_classification_gap(self):
        columns = ["Account Name", "Debit", "Credit"]
        rows = [
            {"Account Name": "Cash", "Debit": 1000.0, "Credit": 0.0},
            {"Account Name": "Accounts Payable", "Debit": 0.0, "Credit": 300.0},
            {"Account Name": "Retained Earnings", "Debit": 0.0, "Credit": 500.0},
            {"Account Name": "Sales Revenue", "Debit": 0.0, "Credit": 800.0},
            # Expense exists but is not COGS-like — Revenue>0 + no COGS + expense material
            {"Account Name": "Rent Expense", "Debit": 600.0, "Credit": 0.0},
        ]

        report = run_preflight(columns, rows, "no_cogs.csv")
        gap_issues = [
            i for i in report.issues if i.category == "category_completeness" and "Cost of Goods Sold" in i.message
        ]
        assert len(gap_issues) == 1
        assert gap_issues[0].severity == "medium"
        assert report.category_completeness is not None
        assert report.category_completeness.cogs_gap is True

    def test_service_business_no_revenue_no_cogs_does_not_flag(self):
        """If neither revenue nor cogs exists, the COGS gap must not fire."""
        columns = ["Account Name", "Debit", "Credit"]
        rows = [
            {"Account Name": "Cash", "Debit": 1000.0, "Credit": 0.0},
            {"Account Name": "Accounts Payable", "Debit": 0.0, "Credit": 300.0},
            {"Account Name": "Retained Earnings", "Debit": 0.0, "Credit": 500.0},
            {"Account Name": "Consulting Revenue", "Debit": 0.0, "Credit": 800.0},
            {"Account Name": "Cost of Sales", "Debit": 600.0, "Credit": 0.0},
        ]
        report = run_preflight(columns, rows, "service.csv")
        cc = report.category_completeness
        assert cc is not None
        assert cc.cogs_gap is False

    def test_to_dict_includes_category_completeness(self):
        columns, rows = self._full_tb()
        d = run_preflight(columns, rows, "t.csv").to_dict()

        assert "category_completeness" in d
        cc = d["category_completeness"]
        for key in (
            "asset_count",
            "liability_count",
            "equity_count",
            "revenue_count",
            "expense_count",
            "unknown_count",
            "missing_categories",
            "revenue_total",
            "cogs_total",
            "cogs_gap",
        ):
            assert key in cc
