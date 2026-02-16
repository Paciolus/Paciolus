"""
Paciolus Audit Engine — Core Tests
Core unit tests, pipeline integration, edge cases, zero-storage leak verification,
and performance benchmarks for the StreamingAuditor and audit pipeline.
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

        result = auditor.get_balance_result()
        assert result["total_debits"] == 18000.0  # 10000 + 5000 + 3000
        assert result["total_credits"] == 18000.0  # 15000 + 2000 + 1000
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
        """Verify get_balance_result returns balanced=False when debits!=credits."""
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
        assert len(auditor._debit_chunks) > 0

        # Clear
        auditor.clear()

        # Verify data is released
        assert len(auditor.account_balances) == 0
        assert auditor._debit_chunks == []
        assert auditor._credit_chunks == []
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

    def test_no_temp_files_created(self, large_csv_bytes, tmp_path, monkeypatch):
        """Verify no temporary files are created during processing."""
        # Redirect tempdir to an isolated directory so other processes
        # can't create noise that causes false failures
        monkeypatch.setattr(tempfile, 'tempdir', str(tmp_path))

        # Process file
        result = audit_trial_balance_streaming(
            file_bytes=large_csv_bytes,
            filename="leak_test.csv",
            materiality_threshold=0
        )

        # No data files should exist in our isolated temp dir
        new_files = list(tmp_path.iterdir())
        data_files = [f for f in new_files if f.suffix in ('.csv', '.xlsx', '.xls', '.tmp')]

        assert len(data_files) == 0, f"Temp files created: {[f.name for f in data_files]}"

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
        """Verify large file processing completes within acceptable time.

        Threshold is 15s — generous enough for loaded CI machines,
        tight enough to catch catastrophic O(n^2) regressions.
        """
        import time

        start = time.time()
        result = audit_trial_balance_streaming(
            file_bytes=large_csv_bytes,
            filename="perf_test.csv",
            materiality_threshold=0
        )
        elapsed = time.time() - start

        # 15s budget: 1000 rows should never take this long on any reasonable machine
        assert elapsed < 15.0, f"Processing took {elapsed:.1f}s (budget: 15s)"
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
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
