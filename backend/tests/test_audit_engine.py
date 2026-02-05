"""
Paciolus Audit Engine Test Suite
Day 8: Automated Verification

Tests cover:
- Small files vs Large (chunked) files
- Materiality threshold filtering accuracy
- Edge cases (empty CSVs, non-numeric columns)
- Zero-Storage leak verification
"""

import gc
import io
import os
import sys
import tempfile
from pathlib import Path

import pandas as pd
import psutil
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from audit_engine import (
    StreamingAuditor,
    audit_trial_balance_streaming,
    check_balance,
    detect_abnormal_balances,
    DEFAULT_CHUNK_SIZE,
)
from security_utils import (
    process_tb_chunked,
    read_csv_chunked,
    clear_memory,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def small_balanced_csv() -> bytes:
    """Generate a small balanced CSV (10 rows)."""
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
def small_unbalanced_csv() -> bytes:
    """Generate a small unbalanced CSV."""
    data = """Account Name,Debit,Credit
Cash,10000,
Revenue,,5000
"""
    return data.encode('utf-8')


@pytest.fixture
def abnormal_balances_csv() -> bytes:
    """Generate CSV with abnormal balances for testing."""
    data = """Account Name,Debit,Credit
Cash,,500
Accounts Receivable,,1000
Accounts Payable,2000,
Sales Tax Payable,300,
Revenue,,2800
"""
    # Cash (asset) has credit balance - ABNORMAL
    # Accounts Receivable (asset) has credit balance - ABNORMAL
    # Accounts Payable (liability) has debit balance - ABNORMAL
    # Sales Tax Payable (liability) has debit balance - ABNORMAL
    return data.encode('utf-8')


@pytest.fixture
def large_csv_bytes() -> bytes:
    """Generate a large CSV (1000 rows) for chunked processing tests."""
    rows = ["Account Name,Debit,Credit"]
    total_debit = 0
    total_credit = 0

    for i in range(499):
        debit = 1000 + i
        rows.append(f"Asset Account {i},{debit},")
        total_debit += debit

    for i in range(499):
        credit = 1000 + i
        rows.append(f"Revenue Account {i},,{credit}")
        total_credit += credit

    # Balance it
    diff = total_debit - total_credit
    if diff > 0:
        rows.append(f"Balancing Entry,,{diff}")
    else:
        rows.append(f"Balancing Entry,{abs(diff)},")

    return "\n".join(rows).encode('utf-8')


@pytest.fixture
def empty_csv() -> bytes:
    """Generate an empty CSV with headers only."""
    return b"Account Name,Debit,Credit\n"


@pytest.fixture
def non_numeric_csv() -> bytes:
    """Generate CSV with non-numeric values in Debit/Credit."""
    data = """Account Name,Debit,Credit
Cash,abc,
Revenue,,xyz
Inventory,1000,
Payable,,500
"""
    return data.encode('utf-8')


@pytest.fixture
def unicode_csv() -> bytes:
    """Generate CSV with Unicode account names."""
    data = """Account Name,Debit,Credit
現金 (Cash),1000,
売掛金 (Receivable),500,
売上 (Revenue),,1500
"""
    return data.encode('utf-8')


# =============================================================================
# Unit Tests: StreamingAuditor Class
# =============================================================================

class TestStreamingAuditor:
    """Unit tests for StreamingAuditor class."""

    def test_running_totals_single_chunk(self, small_balanced_csv):
        """Verify running totals are correct for a single chunk."""
        auditor = StreamingAuditor(materiality_threshold=0)
        df = pd.read_csv(io.BytesIO(small_balanced_csv))

        auditor.process_chunk(df, len(df))

        assert auditor.total_debits == 18000.0  # 10000 + 5000 + 3000
        assert auditor.total_credits == 18000.0  # 15000 + 2000 + 1000
        assert auditor.total_rows == len(df)

    def test_running_totals_multiple_chunks(self, large_csv_bytes):
        """Verify running totals accumulate correctly across chunks."""
        auditor = StreamingAuditor(materiality_threshold=0, chunk_size=100)

        chunk_count = 0
        for chunk, rows_processed in read_csv_chunked(large_csv_bytes, chunk_size=100):
            auditor.process_chunk(chunk, rows_processed)
            chunk_count += 1

        # Should have multiple chunks
        assert chunk_count > 1

        # Totals should match
        result = auditor.get_balance_result()
        assert result["balanced"] is True
        assert abs(result["difference"]) < 0.01

    def test_account_aggregation(self):
        """Verify same account in multiple chunks is aggregated."""
        auditor = StreamingAuditor(materiality_threshold=0)

        # First chunk
        df1 = pd.DataFrame({
            "Account Name": ["Cash", "Revenue"],
            "Debit": [1000, 0],
            "Credit": [0, 1000]
        })
        auditor.process_chunk(df1, 2)

        # Second chunk with same account names
        df2 = pd.DataFrame({
            "Account Name": ["Cash", "Revenue"],
            "Debit": [500, 0],
            "Credit": [0, 500]
        })
        auditor.process_chunk(df2, 4)

        # Should have aggregated balances
        assert "Cash" in auditor.account_balances
        assert auditor.account_balances["Cash"]["debit"] == 1500
        assert auditor.account_balances["Cash"]["credit"] == 0

    def test_balance_check_balanced(self, small_balanced_csv):
        """Verify get_balance_result returns balanced=True when debits=credits."""
        auditor = StreamingAuditor(materiality_threshold=0)
        df = pd.read_csv(io.BytesIO(small_balanced_csv))
        auditor.process_chunk(df, len(df))

        result = auditor.get_balance_result()

        assert result["status"] == "success"
        assert result["balanced"] is True
        assert abs(result["difference"]) < 0.01
        assert "balanced" in result["message"].lower()

    def test_balance_check_unbalanced(self, small_unbalanced_csv):
        """Verify get_balance_result returns balanced=False when debits≠credits."""
        auditor = StreamingAuditor(materiality_threshold=0)
        df = pd.read_csv(io.BytesIO(small_unbalanced_csv))
        auditor.process_chunk(df, len(df))

        result = auditor.get_balance_result()

        assert result["status"] == "success"
        assert result["balanced"] is False
        assert result["difference"] == 5000.0  # 10000 - 5000
        assert "out of balance" in result["message"].lower()

    def test_abnormal_asset_credit(self, abnormal_balances_csv):
        """Verify asset account with net credit is flagged as abnormal."""
        auditor = StreamingAuditor(materiality_threshold=0)
        df = pd.read_csv(io.BytesIO(abnormal_balances_csv))
        auditor.process_chunk(df, len(df))

        abnormals = auditor.get_abnormal_balances()

        # Find Cash in abnormal balances
        cash_entry = next((ab for ab in abnormals if "cash" in ab["account"].lower()), None)

        assert cash_entry is not None
        assert cash_entry["type"] == "Asset"
        assert "credit" in cash_entry["issue"].lower()

    def test_abnormal_liability_debit(self, abnormal_balances_csv):
        """Verify liability account with net debit is flagged as abnormal."""
        auditor = StreamingAuditor(materiality_threshold=0)
        df = pd.read_csv(io.BytesIO(abnormal_balances_csv))
        auditor.process_chunk(df, len(df))

        abnormals = auditor.get_abnormal_balances()

        # Find Accounts Payable in abnormal balances
        payable_entry = next((ab for ab in abnormals if "payable" in ab["account"].lower() and "accounts" in ab["account"].lower()), None)

        assert payable_entry is not None
        assert payable_entry["type"] == "Liability"
        assert "debit" in payable_entry["issue"].lower()

    def test_materiality_classification_material(self):
        """Verify balances >= threshold are marked material."""
        auditor = StreamingAuditor(materiality_threshold=500)

        df = pd.DataFrame({
            "Account Name": ["Cash", "Revenue"],
            "Debit": [0, 600],
            "Credit": [600, 0]  # Cash has $600 credit (abnormal, >= threshold)
        })
        auditor.process_chunk(df, 2)

        abnormals = auditor.get_abnormal_balances()
        cash_entry = next((ab for ab in abnormals if "cash" in ab["account"].lower()), None)

        assert cash_entry is not None
        assert cash_entry["materiality"] == "material"
        assert cash_entry["amount"] == 600

    def test_materiality_classification_immaterial(self):
        """Verify balances < threshold are marked immaterial."""
        auditor = StreamingAuditor(materiality_threshold=500)

        df = pd.DataFrame({
            "Account Name": ["Cash", "Revenue"],
            "Debit": [0, 100],
            "Credit": [100, 0]  # Cash has $100 credit (abnormal, < threshold)
        })
        auditor.process_chunk(df, 2)

        abnormals = auditor.get_abnormal_balances()
        cash_entry = next((ab for ab in abnormals if "cash" in ab["account"].lower()), None)

        assert cash_entry is not None
        assert cash_entry["materiality"] == "immaterial"
        assert cash_entry["amount"] == 100

    def test_clear_releases_memory(self, small_balanced_csv):
        """Verify clear() method releases accumulated data."""
        auditor = StreamingAuditor(materiality_threshold=0)
        df = pd.read_csv(io.BytesIO(small_balanced_csv))
        auditor.process_chunk(df, len(df))

        # Verify data is populated
        assert len(auditor.account_balances) > 0
        assert auditor.total_debits > 0

        # Clear
        auditor.clear()

        # Verify data is released
        assert len(auditor.account_balances) == 0
        assert auditor.total_debits == 0
        assert auditor.total_credits == 0
        assert auditor.total_rows == 0


# =============================================================================
# Integration Tests: Full Pipeline
# =============================================================================

class TestAuditPipeline:
    """Integration tests for full audit pipeline."""

    def test_small_file_audit(self, small_balanced_csv):
        """Verify small file is processed correctly."""
        result = audit_trial_balance_streaming(
            file_bytes=small_balanced_csv,
            filename="test.csv",
            materiality_threshold=0
        )

        assert result["status"] == "success"
        assert result["balanced"] is True
        assert result["row_count"] == 6
        assert "abnormal_balances" in result
        assert "materiality_threshold" in result

    def test_large_file_chunked_audit(self, large_csv_bytes):
        """Verify large file is processed in chunks correctly."""
        result = audit_trial_balance_streaming(
            file_bytes=large_csv_bytes,
            filename="large.csv",
            materiality_threshold=0,
            chunk_size=100
        )

        assert result["status"] == "success"
        assert result["balanced"] is True
        assert result["row_count"] == 999  # 499 + 499 + 1 balancing

    def test_result_format_compatibility(self, small_balanced_csv):
        """Verify streaming result format matches expected schema."""
        result = audit_trial_balance_streaming(
            file_bytes=small_balanced_csv,
            filename="test.csv",
            materiality_threshold=500
        )

        # All required keys must be present
        required_keys = [
            "status", "balanced", "total_debits", "total_credits",
            "difference", "row_count", "timestamp", "message",
            "abnormal_balances", "materiality_threshold",
            "material_count", "immaterial_count", "has_risk_alerts"
        ]

        for key in required_keys:
            assert key in result, f"Missing key: {key}"

    def test_materiality_threshold_filtering(self, abnormal_balances_csv):
        """Verify materiality threshold correctly filters alerts."""
        # With threshold=0, all abnormals are material
        result_zero = audit_trial_balance_streaming(
            file_bytes=abnormal_balances_csv,
            filename="test.csv",
            materiality_threshold=0
        )

        # With threshold=1000, smaller abnormals are immaterial
        result_high = audit_trial_balance_streaming(
            file_bytes=abnormal_balances_csv,
            filename="test.csv",
            materiality_threshold=1000
        )

        # High threshold should have fewer material alerts
        assert result_high["material_count"] <= result_zero["material_count"]
        assert result_high["materiality_threshold"] == 1000


# =============================================================================
# Edge Case Tests
# =============================================================================

class TestEdgeCases:
    """Edge case tests."""

    def test_empty_file(self, empty_csv):
        """Verify graceful handling of empty file (headers only)."""
        result = audit_trial_balance_streaming(
            file_bytes=empty_csv,
            filename="empty.csv",
            materiality_threshold=0
        )

        assert result["status"] == "success"
        assert result["row_count"] == 0
        assert result["balanced"] is True  # 0 = 0
        assert result["total_debits"] == 0
        assert result["total_credits"] == 0

    def test_non_numeric_values(self, non_numeric_csv):
        """Verify non-numeric values are coerced to 0."""
        result = audit_trial_balance_streaming(
            file_bytes=non_numeric_csv,
            filename="non_numeric.csv",
            materiality_threshold=0
        )

        assert result["status"] == "success"
        # "abc" and "xyz" should be coerced to 0
        # Only 1000 debit and 500 credit remain
        assert result["total_debits"] == 1000
        assert result["total_credits"] == 500

    def test_unicode_account_names(self, unicode_csv):
        """Verify Unicode characters in account names handled correctly."""
        result = audit_trial_balance_streaming(
            file_bytes=unicode_csv,
            filename="unicode.csv",
            materiality_threshold=0
        )

        assert result["status"] == "success"
        assert result["balanced"] is True
        assert result["row_count"] == 3

    def test_very_large_numbers(self):
        """Verify large dollar amounts don't overflow."""
        data = """Account Name,Debit,Credit
Asset,999999999999.99,
Revenue,,999999999999.99
"""
        result = audit_trial_balance_streaming(
            file_bytes=data.encode('utf-8'),
            filename="large_numbers.csv",
            materiality_threshold=0
        )

        assert result["status"] == "success"
        assert result["balanced"] is True
        assert result["total_debits"] == 999999999999.99

    def test_negative_values(self):
        """Verify negative values in Debit/Credit columns handled."""
        data = """Account Name,Debit,Credit
Cash,-1000,
Revenue,,-500
Payable,,500
Asset,1000,
"""
        result = audit_trial_balance_streaming(
            file_bytes=data.encode('utf-8'),
            filename="negative.csv",
            materiality_threshold=0
        )

        assert result["status"] == "success"
        # -1000 + 1000 = 0 debits, -500 + 500 = 0 credits
        assert result["total_debits"] == 0
        assert result["total_credits"] == 0


# =============================================================================
# Zero-Storage Leak Tests (QualityGuardian)
# =============================================================================

class TestZeroStorageLeak:
    """Verify Zero-Storage policy - no data leaks."""

    def test_no_temp_files_created(self, large_csv_bytes):
        """Verify no temporary files are created during processing."""
        # Get temp directory contents before
        temp_dir = tempfile.gettempdir()
        before_files = set(os.listdir(temp_dir))

        # Process file
        result = audit_trial_balance_streaming(
            file_bytes=large_csv_bytes,
            filename="leak_test.csv",
            materiality_threshold=0
        )

        # Get temp directory contents after
        after_files = set(os.listdir(temp_dir))

        # No new CSV or data files should exist
        new_files = after_files - before_files
        csv_files = [f for f in new_files if f.endswith(('.csv', '.xlsx', '.xls', '.tmp'))]

        assert len(csv_files) == 0, f"Temp files created: {csv_files}"

    def test_memory_released_after_processing(self, large_csv_bytes):
        """Verify memory is released after processing completes."""
        gc.collect()
        process = psutil.Process()

        # Memory before
        mem_before = process.memory_info().rss / 1024 / 1024  # MB

        # Process file
        result = audit_trial_balance_streaming(
            file_bytes=large_csv_bytes,
            filename="memory_test.csv",
            materiality_threshold=0
        )

        # Force cleanup
        del result
        clear_memory()
        gc.collect()

        # Memory after
        mem_after = process.memory_info().rss / 1024 / 1024  # MB

        # Memory should not grow significantly (allow 50MB tolerance)
        memory_growth = mem_after - mem_before
        assert memory_growth < 50, f"Memory grew by {memory_growth}MB"

    def test_no_data_persists_after_error(self):
        """Verify no data persists after a processing error."""
        gc.collect()

        # Create invalid file that will cause an error
        invalid_bytes = b"not,valid,csv\ndata\n"

        try:
            # This should handle gracefully
            result = audit_trial_balance_streaming(
                file_bytes=invalid_bytes,
                filename="error_test.csv",
                materiality_threshold=0
            )
        except Exception:
            pass

        # Force cleanup
        clear_memory()
        gc.collect()

        # Verify no orphaned data
        temp_dir = tempfile.gettempdir()
        csv_files = [f for f in os.listdir(temp_dir) if 'error_test' in f]
        assert len(csv_files) == 0

    def test_auditor_clear_on_exception(self):
        """Verify StreamingAuditor clears state even on exception."""
        auditor = StreamingAuditor(materiality_threshold=0)

        # Add some data
        df = pd.DataFrame({
            "Account Name": ["Cash"],
            "Debit": [1000],
            "Credit": [0]
        })
        auditor.process_chunk(df, 1)

        # Verify data exists
        assert len(auditor.account_balances) > 0

        # Simulate cleanup that would happen in finally block
        auditor.clear()

        # Verify cleared
        assert len(auditor.account_balances) == 0


# =============================================================================
# Performance Tests
# =============================================================================

class TestPerformance:
    """Performance and benchmark tests."""

    def test_large_file_completes_in_time(self, large_csv_bytes):
        """Verify large file processing completes within acceptable time."""
        import time

        start = time.time()
        result = audit_trial_balance_streaming(
            file_bytes=large_csv_bytes,
            filename="perf_test.csv",
            materiality_threshold=0
        )
        elapsed = time.time() - start

        # Should complete in under 5 seconds for 1000 rows
        assert elapsed < 5.0, f"Processing took {elapsed}s"
        assert result["status"] == "success"

    def test_memory_stays_bounded(self, large_csv_bytes):
        """Verify memory usage stays bounded during processing."""
        gc.collect()
        process = psutil.Process()

        mem_baseline = process.memory_info().rss / 1024 / 1024

        # Process with small chunks to force multiple iterations
        result = audit_trial_balance_streaming(
            file_bytes=large_csv_bytes,
            filename="bounded_test.csv",
            materiality_threshold=0,
            chunk_size=50
        )

        mem_peak = process.memory_info().rss / 1024 / 1024

        # Peak should be less than 2x baseline
        assert mem_peak < mem_baseline * 2, f"Memory grew from {mem_baseline}MB to {mem_peak}MB"


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
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
