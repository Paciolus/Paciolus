"""
Tests for the Pre-Flight Data Quality Engine — Sprint 283

7 tests covering all 6 quality checks + route registration.
"""


from preflight_engine import PreFlightReport, run_preflight


class TestPreflightCleanFile:
    """Test 1: Well-formed CSV → readiness >= 90, 'Ready'."""

    def test_clean_file_high_readiness(self):
        column_names = ["Account Name", "Debit", "Credit"]
        rows = [
            {"Account Name": "Cash", "Debit": 1000.0, "Credit": 0.0},
            {"Account Name": "Revenue", "Debit": 0.0, "Credit": 2000.0},
            {"Account Name": "Expenses", "Debit": 500.0, "Credit": 0.0},
            {"Account Name": "Equity", "Debit": 0.0, "Credit": 1500.0},
        ]

        report = run_preflight(column_names, rows, "clean.csv")

        assert isinstance(report, PreFlightReport)
        assert report.readiness_score >= 90
        assert report.readiness_label == "Ready"
        assert report.row_count == 4
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

        # Readiness should be significantly reduced
        assert report.readiness_score < 80


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
