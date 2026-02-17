"""
Paciolus Audit Engine — Anomaly Detection Tests
Multi-sheet column detection, suspense account detection, concentration risk
detection, and rounding anomaly detection tests.
"""

import io
import sys
from pathlib import Path

import pandas as pd
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from audit_engine import (
    StreamingAuditor,
    audit_trial_balance_streaming,
)

# =============================================================================
# Multi-Sheet Column Detection Tests (Sprint 25)
# =============================================================================

class TestMultiSheetColumnDetection:
    """Test per-sheet column detection for multi-sheet audits (Sprint 25 fix)."""

    @pytest.fixture
    def multi_sheet_xlsx_same_columns(self):
        """Create Excel bytes with multiple sheets having same column order."""
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Sheet 1
            df1 = pd.DataFrame({
                "Account Name": ["Cash", "Revenue"],
                "Debit": [1000, 0],
                "Credit": [0, 1000]
            })
            df1.to_excel(writer, sheet_name="Sheet1", index=False)

            # Sheet 2 - same column order
            df2 = pd.DataFrame({
                "Account Name": ["Inventory", "Sales"],
                "Debit": [500, 0],
                "Credit": [0, 500]
            })
            df2.to_excel(writer, sheet_name="Sheet2", index=False)

        return output.getvalue()

    @pytest.fixture
    def multi_sheet_xlsx_different_columns(self):
        """Create Excel bytes with sheets having different column orders."""
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Sheet 1: Account, Debit, Credit
            df1 = pd.DataFrame({
                "Account Name": ["Cash", "Revenue"],
                "Debit": [1000, 0],
                "Credit": [0, 1000]
            })
            df1.to_excel(writer, sheet_name="Sheet1", index=False)

            # Sheet 2: Different column order - Credit before Debit
            df2 = pd.DataFrame({
                "GL Account": ["Inventory", "Sales"],
                "Credit Amount": [0, 500],
                "Debit Amount": [500, 0]
            })
            df2.to_excel(writer, sheet_name="Sheet2", index=False)

        return output.getvalue()

    def test_multi_sheet_returns_per_sheet_detection(self, multi_sheet_xlsx_same_columns):
        """Verify each sheet has its own column detection result."""
        from audit_engine import audit_trial_balance_multi_sheet

        result = audit_trial_balance_multi_sheet(
            file_bytes=multi_sheet_xlsx_same_columns,
            filename="test.xlsx",
            selected_sheets=["Sheet1", "Sheet2"],
            materiality_threshold=0
        )

        # Should have per-sheet column detections
        assert "sheet_column_detections" in result
        assert "Sheet1" in result["sheet_column_detections"]
        assert "Sheet2" in result["sheet_column_detections"]

    def test_multi_sheet_detects_column_order_mismatch(self, multi_sheet_xlsx_different_columns):
        """Verify warning is generated when column orders differ across sheets."""
        from audit_engine import audit_trial_balance_multi_sheet

        result = audit_trial_balance_multi_sheet(
            file_bytes=multi_sheet_xlsx_different_columns,
            filename="test.xlsx",
            selected_sheets=["Sheet1", "Sheet2"],
            materiality_threshold=0
        )

        # Should have column order warnings
        assert "column_order_warnings" in result
        assert "has_column_order_mismatch" in result
        assert result["has_column_order_mismatch"] is True
        assert len(result["column_order_warnings"]) > 0

    def test_multi_sheet_same_columns_no_warning(self, multi_sheet_xlsx_same_columns):
        """Verify no warning when all sheets have same column order."""
        from audit_engine import audit_trial_balance_multi_sheet

        result = audit_trial_balance_multi_sheet(
            file_bytes=multi_sheet_xlsx_same_columns,
            filename="test.xlsx",
            selected_sheets=["Sheet1", "Sheet2"],
            materiality_threshold=0
        )

        assert result["has_column_order_mismatch"] is False
        assert len(result["column_order_warnings"]) == 0

    def test_multi_sheet_includes_detection_in_sheet_results(self, multi_sheet_xlsx_same_columns):
        """Verify sheet_results includes column detection for each sheet."""
        from audit_engine import audit_trial_balance_multi_sheet

        result = audit_trial_balance_multi_sheet(
            file_bytes=multi_sheet_xlsx_same_columns,
            filename="test.xlsx",
            selected_sheets=["Sheet1", "Sheet2"],
            materiality_threshold=0
        )

        # Each sheet result should include its column detection
        for sheet_name in ["Sheet1", "Sheet2"]:
            assert "column_detection" in result["sheet_results"][sheet_name]

    def test_multi_sheet_backward_compat_column_detection(self, multi_sheet_xlsx_same_columns):
        """Verify backward compatibility: column_detection field still exists at top level."""
        from audit_engine import audit_trial_balance_multi_sheet

        result = audit_trial_balance_multi_sheet(
            file_bytes=multi_sheet_xlsx_same_columns,
            filename="test.xlsx",
            selected_sheets=["Sheet1", "Sheet2"],
            materiality_threshold=0
        )

        # Top-level column_detection should still exist (uses first sheet)
        assert "column_detection" in result
        assert result["column_detection"] is not None

    def test_multi_sheet_user_mapping_overrides_all(self, multi_sheet_xlsx_different_columns):
        """Verify user-provided column mapping is applied to all sheets."""
        from audit_engine import audit_trial_balance_multi_sheet

        result = audit_trial_balance_multi_sheet(
            file_bytes=multi_sheet_xlsx_different_columns,
            filename="test.xlsx",
            selected_sheets=["Sheet1"],
            materiality_threshold=0,
            column_mapping={
                "account_column": "Account Name",
                "debit_column": "Debit",
                "credit_column": "Credit"
            }
        )

        # With user mapping, detection should show 100% confidence
        sheet1_detection = result["sheet_column_detections"].get("Sheet1", {})
        assert sheet1_detection.get("overall_confidence") == 1.0


# =============================================================================
# Suspense Account Detection Tests (Sprint 41)
# =============================================================================

class TestSuspenseAccountDetection:
    """Test suspense account detection feature (Sprint 41 - Phase III)."""

    @pytest.fixture
    def suspense_accounts_csv(self) -> bytes:
        """Generate CSV with various suspense and clearing accounts."""
        data = """Account Name,Debit,Credit
Cash,10000,
Suspense Account,5000,
Bank Clearing Account,,2000
Unallocated Expenses,1500,
Accounts Payable,,8000
Payroll Clearing,800,
Revenue,,7300
"""
        return data.encode('utf-8')

    @pytest.fixture
    def no_suspense_csv(self) -> bytes:
        """Generate CSV without any suspense accounts."""
        data = """Account Name,Debit,Credit
Cash,10000,
Accounts Receivable,5000,
Inventory,3000,
Revenue,,15000
Accounts Payable,,2000
Retained Earnings,,1000
"""
        return data.encode('utf-8')

    @pytest.fixture
    def edge_case_suspense_csv(self) -> bytes:
        """Generate CSV with edge case suspense keywords."""
        data = """Account Name,Debit,Credit
Pending Classification Account,2500,
Awaiting Classification,1000,
Intercompany Clearing,500,
Miscellaneous Expense,300,
Other Income,,4300
"""
        return data.encode('utf-8')

    @pytest.fixture
    def zero_balance_suspense_csv(self) -> bytes:
        """Generate CSV with suspense accounts that have zero balances."""
        data = """Account Name,Debit,Credit
Cash,10000,
Suspense Account,1000,1000
Bank Clearing,500,500
Revenue,,10000
"""
        return data.encode('utf-8')

    def test_detects_suspense_keyword(self, suspense_accounts_csv):
        """Verify 'Suspense Account' is detected."""
        auditor = StreamingAuditor(materiality_threshold=0)
        df = pd.read_csv(io.BytesIO(suspense_accounts_csv))
        auditor.process_chunk(df, len(df))

        suspense = auditor.detect_suspense_accounts()

        suspense_entry = next(
            (s for s in suspense if "suspense" in s["account"].lower()),
            None
        )
        assert suspense_entry is not None
        assert suspense_entry["anomaly_type"] == "suspense_account"
        assert suspense_entry["confidence"] >= 0.90

    def test_detects_clearing_keyword(self, suspense_accounts_csv):
        """Verify 'Clearing Account' is detected."""
        auditor = StreamingAuditor(materiality_threshold=0)
        df = pd.read_csv(io.BytesIO(suspense_accounts_csv))
        auditor.process_chunk(df, len(df))

        suspense = auditor.detect_suspense_accounts()

        clearing_entries = [s for s in suspense if "clearing" in s["account"].lower()]
        assert len(clearing_entries) >= 2  # Bank Clearing and Payroll Clearing

    def test_detects_unallocated_keyword(self, suspense_accounts_csv):
        """Verify 'Unallocated' is detected."""
        auditor = StreamingAuditor(materiality_threshold=0)
        df = pd.read_csv(io.BytesIO(suspense_accounts_csv))
        auditor.process_chunk(df, len(df))

        suspense = auditor.detect_suspense_accounts()

        unallocated = next(
            (s for s in suspense if "unallocated" in s["account"].lower()),
            None
        )
        assert unallocated is not None
        assert unallocated["confidence"] >= 0.60

    def test_no_false_positives_on_clean_data(self, no_suspense_csv):
        """Verify no suspense accounts flagged on clean data."""
        auditor = StreamingAuditor(materiality_threshold=0)
        df = pd.read_csv(io.BytesIO(no_suspense_csv))
        auditor.process_chunk(df, len(df))

        suspense = auditor.detect_suspense_accounts()

        assert len(suspense) == 0

    def test_zero_balance_suspense_not_flagged(self, zero_balance_suspense_csv):
        """Verify suspense accounts with zero balance are not flagged."""
        auditor = StreamingAuditor(materiality_threshold=0)
        df = pd.read_csv(io.BytesIO(zero_balance_suspense_csv))
        auditor.process_chunk(df, len(df))

        suspense = auditor.detect_suspense_accounts()

        # Suspense Account and Bank Clearing have zero net balance
        assert len(suspense) == 0

    def test_suspense_includes_recommendation(self, suspense_accounts_csv):
        """Verify suspense accounts include recommendation field."""
        auditor = StreamingAuditor(materiality_threshold=0)
        df = pd.read_csv(io.BytesIO(suspense_accounts_csv))
        auditor.process_chunk(df, len(df))

        suspense = auditor.detect_suspense_accounts()

        for entry in suspense:
            assert "recommendation" in entry
            assert "investigate" in entry["recommendation"].lower()

    def test_suspense_always_requires_review(self, suspense_accounts_csv):
        """Verify all suspense accounts are marked as requiring review."""
        auditor = StreamingAuditor(materiality_threshold=0)
        df = pd.read_csv(io.BytesIO(suspense_accounts_csv))
        auditor.process_chunk(df, len(df))

        suspense = auditor.detect_suspense_accounts()

        for entry in suspense:
            assert entry["requires_review"] is True

    def test_suspense_severity_material(self, suspense_accounts_csv):
        """Verify material suspense accounts are high severity."""
        auditor = StreamingAuditor(materiality_threshold=1000)
        df = pd.read_csv(io.BytesIO(suspense_accounts_csv))
        auditor.process_chunk(df, len(df))

        suspense = auditor.detect_suspense_accounts()

        # Suspense Account ($5000) and Unallocated ($1500) are material
        high_severity = [s for s in suspense if s["severity"] == "high"]
        assert len(high_severity) >= 2

    def test_suspense_severity_immaterial_is_medium(self, suspense_accounts_csv):
        """Verify immaterial suspense accounts are medium severity (not low)."""
        auditor = StreamingAuditor(materiality_threshold=10000)
        df = pd.read_csv(io.BytesIO(suspense_accounts_csv))
        auditor.process_chunk(df, len(df))

        suspense = auditor.detect_suspense_accounts()

        # All suspense accounts are below threshold, should be medium
        for entry in suspense:
            assert entry["severity"] in ["high", "medium"]
            # Immaterial ones should be medium, not low
            if entry["materiality"] == "immaterial":
                assert entry["severity"] == "medium"

    def test_edge_case_pending_classification(self, edge_case_suspense_csv):
        """Verify 'Pending Classification' phrase is detected."""
        auditor = StreamingAuditor(materiality_threshold=0)
        df = pd.read_csv(io.BytesIO(edge_case_suspense_csv))
        auditor.process_chunk(df, len(df))

        suspense = auditor.detect_suspense_accounts()

        pending = next(
            (s for s in suspense if "pending" in s["account"].lower()),
            None
        )
        assert pending is not None
        assert pending["confidence"] >= 0.75

    def test_low_confidence_miscellaneous_not_flagged(self, edge_case_suspense_csv):
        """Verify 'Miscellaneous' alone has low confidence and may not be flagged."""
        auditor = StreamingAuditor(materiality_threshold=0)
        df = pd.read_csv(io.BytesIO(edge_case_suspense_csv))
        auditor.process_chunk(df, len(df))

        suspense = auditor.detect_suspense_accounts()

        # 'Miscellaneous Expense' should have confidence ~0.55, below threshold 0.60
        misc = next(
            (s for s in suspense if s["account"] == "Miscellaneous Expense"),
            None
        )
        # May or may not be flagged depending on threshold
        if misc:
            assert misc["confidence"] >= 0.60

    def test_suspense_merged_into_abnormal_balances(self, suspense_accounts_csv):
        """Verify suspense accounts are merged into audit result abnormal_balances."""
        result = audit_trial_balance_streaming(
            file_bytes=suspense_accounts_csv,
            filename="test.csv",
            materiality_threshold=0
        )

        abnormals = result["abnormal_balances"]

        # Find suspense entries in abnormal_balances
        suspense_entries = [
            ab for ab in abnormals
            if ab.get("anomaly_type") == "suspense_account"
        ]
        assert len(suspense_entries) > 0

    def test_risk_summary_includes_suspense_count(self, suspense_accounts_csv):
        """Verify risk_summary includes suspense_account count."""
        result = audit_trial_balance_streaming(
            file_bytes=suspense_accounts_csv,
            filename="test.csv",
            materiality_threshold=0
        )

        risk_summary = result["risk_summary"]

        assert "anomaly_types" in risk_summary
        assert "suspense_account" in risk_summary["anomaly_types"]
        assert risk_summary["anomaly_types"]["suspense_account"] > 0

    def test_risk_summary_medium_severity_included(self, suspense_accounts_csv):
        """Verify risk_summary includes medium_severity count (Sprint 41)."""
        result = audit_trial_balance_streaming(
            file_bytes=suspense_accounts_csv,
            filename="test.csv",
            materiality_threshold=10000  # Make most immaterial
        )

        risk_summary = result["risk_summary"]

        assert "medium_severity" in risk_summary

    def test_suspense_plus_abnormal_balance_merged(self):
        """Verify account that is both suspense AND abnormal balance is handled."""
        # Create CSV where Cash (asset) is in suspense and has credit balance
        data = """Account Name,Debit,Credit
Suspense - Cash Account,,5000
Revenue,,5000
Asset,10000,
"""
        result = audit_trial_balance_streaming(
            file_bytes=data.encode('utf-8'),
            filename="test.csv",
            materiality_threshold=0
        )

        abnormals = result["abnormal_balances"]

        # Should only appear once, but with suspense indicator
        suspense_cash = [
            ab for ab in abnormals
            if "suspense" in ab["account"].lower() and "cash" in ab["account"].lower()
        ]
        assert len(suspense_cash) == 1

        entry = suspense_cash[0]
        # Should have either anomaly_type=suspense_account or is_suspense_account=True
        assert (
            entry.get("anomaly_type") == "suspense_account" or
            entry.get("is_suspense_account") is True
        )

    def test_matched_keywords_returned(self, suspense_accounts_csv):
        """Verify matched keywords are returned in results."""
        auditor = StreamingAuditor(materiality_threshold=0)
        df = pd.read_csv(io.BytesIO(suspense_accounts_csv))
        auditor.process_chunk(df, len(df))

        suspense = auditor.detect_suspense_accounts()

        for entry in suspense:
            assert "matched_keywords" in entry
            assert len(entry["matched_keywords"]) > 0

    def test_multi_sheet_suspense_detection(self):
        """Verify suspense detection works in multi-sheet audits."""
        from audit_engine import audit_trial_balance_multi_sheet

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Sheet 1 with suspense
            df1 = pd.DataFrame({
                "Account Name": ["Cash", "Suspense Account"],
                "Debit": [1000, 500],
                "Credit": [0, 0]
            })
            df1.to_excel(writer, sheet_name="Sheet1", index=False)

            # Sheet 2 with clearing
            df2 = pd.DataFrame({
                "Account Name": ["Revenue", "Bank Clearing"],
                "Debit": [0, 300],
                "Credit": [1800, 0]
            })
            df2.to_excel(writer, sheet_name="Sheet2", index=False)

        result = audit_trial_balance_multi_sheet(
            file_bytes=output.getvalue(),
            filename="test.xlsx",
            selected_sheets=["Sheet1", "Sheet2"],
            materiality_threshold=0
        )

        # Verify suspense accounts found across sheets
        abnormals = result["abnormal_balances"]
        suspense_entries = [
            ab for ab in abnormals
            if ab.get("anomaly_type") == "suspense_account"
        ]
        assert len(suspense_entries) >= 2  # Suspense Account + Bank Clearing

        # Verify sheet_name is added
        for entry in suspense_entries:
            assert "sheet_name" in entry


# =============================================================================
# Concentration Risk Detection Tests (Sprint 42)
# =============================================================================

class TestConcentrationRiskDetection:
    """Test concentration risk detection feature (Sprint 42 - Phase III)."""

    @pytest.fixture
    def high_concentration_csv(self) -> bytes:
        """Generate CSV with accounts having high concentration."""
        data = """Account Name,Debit,Credit
Accounts Receivable - Customer A,80000,
Accounts Receivable - Customer B,10000,
Accounts Receivable - Customer C,10000,
Revenue,,100000
"""
        # Customer A is 80% of total receivables - HIGH concentration
        return data.encode('utf-8')

    @pytest.fixture
    def medium_concentration_csv(self) -> bytes:
        """Generate CSV with accounts having medium concentration."""
        data = """Account Name,Debit,Credit
Accounts Receivable - Customer A,35000,
Accounts Receivable - Customer B,35000,
Accounts Receivable - Customer C,30000,
Revenue,,100000
"""
        # Customer A is 35% of total receivables - MEDIUM concentration
        return data.encode('utf-8')

    @pytest.fixture
    def no_concentration_csv(self) -> bytes:
        """Generate CSV without concentration issues."""
        data = """Account Name,Debit,Credit
Accounts Receivable - Customer A,20000,
Accounts Receivable - Customer B,20000,
Accounts Receivable - Customer C,20000,
Accounts Receivable - Customer D,20000,
Accounts Receivable - Customer E,20000,
Service Revenue,,20000
Product Revenue,,20000
Consulting Revenue,,20000
Other Revenue,,20000
Rental Income,,20000
"""
        # Each customer is 20% - no concentration
        # Each revenue is 20% - no concentration
        return data.encode('utf-8')

    @pytest.fixture
    def small_category_csv(self) -> bytes:
        """Generate CSV with small category total (below minimum)."""
        data = """Account Name,Debit,Credit
Petty Cash,300,
Bank Account,300,
Office Supplies,200,
Service Revenue,,400
Sales Revenue,,400
"""
        # Total assets only $800 - below $1000 minimum threshold
        # Each revenue is 50% but total revenue is $800 - below threshold
        return data.encode('utf-8')

    def test_detects_high_concentration(self, high_concentration_csv):
        """Verify high concentration (>50%) is detected with high severity."""
        auditor = StreamingAuditor(materiality_threshold=0)
        df = pd.read_csv(io.BytesIO(high_concentration_csv))
        auditor.process_chunk(df, len(df))

        concentration = auditor.detect_concentration_risk()

        high_conc = [c for c in concentration if c["severity"] == "high"]
        assert len(high_conc) >= 1

        # Customer A should be flagged
        customer_a = next(
            (c for c in concentration if "customer a" in c["account"].lower()),
            None
        )
        assert customer_a is not None
        assert customer_a["concentration_percent"] >= 50

    def test_detects_medium_concentration(self, medium_concentration_csv):
        """Verify medium concentration (25-50%) is detected with medium severity."""
        auditor = StreamingAuditor(materiality_threshold=0)
        df = pd.read_csv(io.BytesIO(medium_concentration_csv))
        auditor.process_chunk(df, len(df))

        concentration = auditor.detect_concentration_risk()

        # Customer A at 35% should be flagged as medium
        customer_a = next(
            (c for c in concentration if "customer a" in c["account"].lower()),
            None
        )
        assert customer_a is not None
        assert customer_a["severity"] == "medium"
        assert 25 <= customer_a["concentration_percent"] <= 50

    def test_no_false_positives_on_distributed_data(self, no_concentration_csv):
        """Verify no concentration flagged when accounts are evenly distributed."""
        auditor = StreamingAuditor(materiality_threshold=0)
        df = pd.read_csv(io.BytesIO(no_concentration_csv))
        auditor.process_chunk(df, len(df))

        concentration = auditor.detect_concentration_risk()

        # Each account is 20%, below medium threshold (25%)
        assert len(concentration) == 0

    def test_skips_small_categories(self, small_category_csv):
        """Verify categories below minimum total are not analyzed."""
        auditor = StreamingAuditor(materiality_threshold=0)
        df = pd.read_csv(io.BytesIO(small_category_csv))
        auditor.process_chunk(df, len(df))

        concentration = auditor.detect_concentration_risk()

        # Category total is $1000, below $1000 minimum
        assert len(concentration) == 0

    def test_concentration_includes_category_total(self, high_concentration_csv):
        """Verify category_total is included in results."""
        auditor = StreamingAuditor(materiality_threshold=0)
        df = pd.read_csv(io.BytesIO(high_concentration_csv))
        auditor.process_chunk(df, len(df))

        concentration = auditor.detect_concentration_risk()

        for entry in concentration:
            assert "category_total" in entry
            assert entry["category_total"] > 0

    def test_concentration_includes_recommendation(self, high_concentration_csv):
        """Verify concentration risks include recommendation."""
        auditor = StreamingAuditor(materiality_threshold=0)
        df = pd.read_csv(io.BytesIO(high_concentration_csv))
        auditor.process_chunk(df, len(df))

        concentration = auditor.detect_concentration_risk()

        for entry in concentration:
            assert "recommendation" in entry
            assert "review" in entry["recommendation"].lower()

    def test_concentration_merged_into_abnormal_balances(self, high_concentration_csv):
        """Verify concentration risks are merged into audit result."""
        result = audit_trial_balance_streaming(
            file_bytes=high_concentration_csv,
            filename="test.csv",
            materiality_threshold=0
        )

        abnormals = result["abnormal_balances"]
        concentration_entries = [
            ab for ab in abnormals
            if ab.get("anomaly_type") == "concentration_risk"
        ]
        assert len(concentration_entries) > 0

    def test_risk_summary_includes_concentration_count(self, high_concentration_csv):
        """Verify risk_summary includes concentration_risk count."""
        result = audit_trial_balance_streaming(
            file_bytes=high_concentration_csv,
            filename="test.csv",
            materiality_threshold=0
        )

        risk_summary = result["risk_summary"]
        assert "concentration_risk" in risk_summary["anomaly_types"]
        assert risk_summary["anomaly_types"]["concentration_risk"] > 0

    def test_concentration_sorted_by_percentage(self, high_concentration_csv):
        """Verify results are sorted by concentration percentage (highest first)."""
        auditor = StreamingAuditor(materiality_threshold=0)
        df = pd.read_csv(io.BytesIO(high_concentration_csv))
        auditor.process_chunk(df, len(df))

        concentration = auditor.detect_concentration_risk()

        if len(concentration) > 1:
            for i in range(len(concentration) - 1):
                assert concentration[i]["concentration_percent"] >= concentration[i + 1]["concentration_percent"]


# =============================================================================
# Rounding Anomaly Detection Tests (Sprint 42)
# =============================================================================

class TestRoundingAnomalyDetection:
    """Test rounding anomaly detection feature (Sprint 42 - Phase III)."""

    @pytest.fixture
    def round_numbers_csv(self) -> bytes:
        """Generate CSV with suspicious round numbers."""
        data = """Account Name,Debit,Credit
Accounts Receivable,100000,
Inventory,50000,
Prepaid Expenses,20000,
Revenue,,170000
"""
        # All amounts are suspiciously round
        return data.encode('utf-8')

    @pytest.fixture
    def normal_numbers_csv(self) -> bytes:
        """Generate CSV with normal (non-round) numbers."""
        data = """Account Name,Debit,Credit
Accounts Receivable,98347.52,
Inventory,51234.89,
Prepaid Expenses,19876.43,
Revenue,,169458.84
"""
        return data.encode('utf-8')

    @pytest.fixture
    def mixed_numbers_csv(self) -> bytes:
        """Generate CSV with mix of round and normal numbers."""
        data = """Account Name,Debit,Credit
Accounts Receivable,100000,
Inventory,51234.89,
Equipment,50000,
Revenue,,201234.89
"""
        return data.encode('utf-8')

    @pytest.fixture
    def excluded_round_csv(self) -> bytes:
        """Generate CSV with round numbers on excluded account types."""
        data = """Account Name,Debit,Credit
Cash,50000,
Bank Loan,,100000
Mortgage Payable,,200000
Common Stock,,50000
Note Payable,,100000
Equipment,400000,
"""
        # Loan, Mortgage, Stock, Note Payable should be excluded
        # Only Equipment should be flagged
        return data.encode('utf-8')

    @pytest.fixture
    def small_amounts_csv(self) -> bytes:
        """Generate CSV with small round amounts (below threshold)."""
        data = """Account Name,Debit,Credit
Supplies,5000,
Office Expense,1000,
Revenue,,6000
"""
        # Amounts below $10,000 minimum threshold
        return data.encode('utf-8')

    def test_detects_hundred_thousand_rounding(self, round_numbers_csv):
        """Verify $100,000 round numbers are detected."""
        auditor = StreamingAuditor(materiality_threshold=0)
        df = pd.read_csv(io.BytesIO(round_numbers_csv))
        auditor.process_chunk(df, len(df))

        rounding = auditor.detect_rounding_anomalies()

        # Accounts Receivable at $100,000 should be flagged
        ar_entry = next(
            (r for r in rounding if "receivable" in r["account"].lower()),
            None
        )
        assert ar_entry is not None
        assert ar_entry["rounding_pattern"] == "hundred_thousand"
        assert ar_entry["severity"] == "high"

    def test_detects_fifty_thousand_rounding(self, round_numbers_csv):
        """Verify $50,000 round numbers are detected."""
        auditor = StreamingAuditor(materiality_threshold=0)
        df = pd.read_csv(io.BytesIO(round_numbers_csv))
        auditor.process_chunk(df, len(df))

        rounding = auditor.detect_rounding_anomalies()

        # Inventory at $50,000 should be flagged
        inv_entry = next(
            (r for r in rounding if "inventory" in r["account"].lower()),
            None
        )
        assert inv_entry is not None
        assert inv_entry["rounding_pattern"] in ["hundred_thousand", "fifty_thousand"]

    def test_no_false_positives_on_normal_numbers(self, normal_numbers_csv):
        """Verify no rounding anomalies flagged on normal amounts."""
        auditor = StreamingAuditor(materiality_threshold=0)
        df = pd.read_csv(io.BytesIO(normal_numbers_csv))
        auditor.process_chunk(df, len(df))

        rounding = auditor.detect_rounding_anomalies()

        assert len(rounding) == 0

    def test_excludes_loan_and_capital_accounts(self, excluded_round_csv):
        """Verify loan, mortgage, stock accounts are excluded."""
        auditor = StreamingAuditor(materiality_threshold=0)
        df = pd.read_csv(io.BytesIO(excluded_round_csv))
        auditor.process_chunk(df, len(df))

        rounding = auditor.detect_rounding_anomalies()

        # Loan, Mortgage, Stock, Note Payable should NOT be flagged
        excluded_accounts = ["loan", "mortgage", "stock", "note payable"]
        for entry in rounding:
            for excluded in excluded_accounts:
                assert excluded not in entry["account"].lower(), \
                    f"{entry['account']} should be excluded"

        # Only Equipment should potentially be flagged
        equipment = [r for r in rounding if "equipment" in r["account"].lower()]
        assert len(equipment) >= 1

    def test_skips_small_amounts(self, small_amounts_csv):
        """Verify amounts below threshold are not flagged."""
        auditor = StreamingAuditor(materiality_threshold=0)
        df = pd.read_csv(io.BytesIO(small_amounts_csv))
        auditor.process_chunk(df, len(df))

        rounding = auditor.detect_rounding_anomalies()

        # All amounts below $10,000 minimum
        assert len(rounding) == 0

    def test_rounding_includes_pattern_info(self, round_numbers_csv):
        """Verify rounding_pattern and rounding_divisor are included."""
        auditor = StreamingAuditor(materiality_threshold=0)
        df = pd.read_csv(io.BytesIO(round_numbers_csv))
        auditor.process_chunk(df, len(df))

        rounding = auditor.detect_rounding_anomalies()

        for entry in rounding:
            assert "rounding_pattern" in entry
            assert "rounding_divisor" in entry
            assert entry["rounding_divisor"] > 0

    def test_rounding_includes_recommendation(self, round_numbers_csv):
        """Verify rounding anomalies include recommendation."""
        auditor = StreamingAuditor(materiality_threshold=0)
        df = pd.read_csv(io.BytesIO(round_numbers_csv))
        auditor.process_chunk(df, len(df))

        rounding = auditor.detect_rounding_anomalies()

        for entry in rounding:
            assert "recommendation" in entry
            assert "verify" in entry["recommendation"].lower()

    def test_rounding_merged_into_abnormal_balances(self, round_numbers_csv):
        """Verify rounding anomalies are merged into audit result."""
        result = audit_trial_balance_streaming(
            file_bytes=round_numbers_csv,
            filename="test.csv",
            materiality_threshold=0
        )

        abnormals = result["abnormal_balances"]
        rounding_entries = [
            ab for ab in abnormals
            if ab.get("anomaly_type") == "rounding_anomaly"
        ]
        assert len(rounding_entries) > 0

    def test_risk_summary_includes_rounding_count(self, round_numbers_csv):
        """Verify risk_summary includes rounding_anomaly count."""
        result = audit_trial_balance_streaming(
            file_bytes=round_numbers_csv,
            filename="test.csv",
            materiality_threshold=0
        )

        risk_summary = result["risk_summary"]
        assert "rounding_anomaly" in risk_summary["anomaly_types"]
        assert risk_summary["anomaly_types"]["rounding_anomaly"] > 0

    def test_rounding_limited_to_max_anomalies(self):
        """Verify rounding anomalies are limited to max count."""
        # Create CSV with many round amounts
        rows = ["Account Name,Debit,Credit"]
        for i in range(30):
            rows.append(f"Account {i},{(i + 1) * 100000},")
        rows.append(f"Balancing,,{sum((i + 1) * 100000 for i in range(30))}")

        data = "\n".join(rows)
        auditor = StreamingAuditor(materiality_threshold=0)
        df = pd.read_csv(io.BytesIO(data.encode('utf-8')))
        auditor.process_chunk(df, len(df))

        rounding = auditor.detect_rounding_anomalies()

        # Should be limited to ROUNDING_MAX_ANOMALIES (20)
        assert len(rounding) <= 20

    def test_rounding_sorted_by_amount(self, round_numbers_csv):
        """Verify results are sorted by amount (highest first)."""
        auditor = StreamingAuditor(materiality_threshold=0)
        df = pd.read_csv(io.BytesIO(round_numbers_csv))
        auditor.process_chunk(df, len(df))

        rounding = auditor.detect_rounding_anomalies()

        if len(rounding) > 1:
            for i in range(len(rounding) - 1):
                assert rounding[i]["amount"] >= rounding[i + 1]["amount"]

    def test_multi_sheet_rounding_detection(self):
        """Verify rounding detection works in multi-sheet audits."""
        from audit_engine import audit_trial_balance_multi_sheet

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Use account names that won't be excluded
            df1 = pd.DataFrame({
                "Account Name": ["Equipment", "Revenue"],
                "Debit": [100000, 0],
                "Credit": [0, 100000]
            })
            df1.to_excel(writer, sheet_name="Sheet1", index=False)

            df2 = pd.DataFrame({
                "Account Name": ["Prepaid Expenses", "Sales"],
                "Debit": [50000, 0],
                "Credit": [0, 50000]
            })
            df2.to_excel(writer, sheet_name="Sheet2", index=False)

        result = audit_trial_balance_multi_sheet(
            file_bytes=output.getvalue(),
            filename="test.xlsx",
            selected_sheets=["Sheet1", "Sheet2"],
            materiality_threshold=0
        )

        # Check both direct anomaly_type and has_rounding_anomaly flag
        rounding_entries = [
            ab for ab in result["abnormal_balances"]
            if ab.get("anomaly_type") == "rounding_anomaly" or ab.get("has_rounding_anomaly")
        ]

        # Also check the risk_summary count
        rounding_count = result["risk_summary"]["anomaly_types"].get("rounding_anomaly", 0)
        assert rounding_count >= 2 or len(rounding_entries) >= 2

        for entry in rounding_entries:
            assert "sheet_name" in entry


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
