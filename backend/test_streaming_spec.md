# Test-Streaming Script Specification

**Author:** BackendCritic
**Date:** 2026-02-01
**Status:** Draft for Day 8 Implementation

---

## Purpose

Verify the `StreamingAuditor` class performance and correctness under various conditions:
1. Memory efficiency (no leaks)
2. Accuracy of running totals
3. Per-account aggregation correctness
4. Materiality classification
5. Processing speed benchmarks

---

## Test Script: `test_streaming.py`

### Required Dependencies
```
pytest>=7.0.0
pytest-benchmark>=4.0.0
psutil>=5.9.0  # For memory monitoring
```

### Test Categories

#### 1. Unit Tests — StreamingAuditor Class

```python
class TestStreamingAuditor:
    """Unit tests for StreamingAuditor class."""

    def test_running_totals_single_chunk(self):
        """Verify running totals are correct for a single chunk."""
        # Create auditor
        # Process one chunk with known values
        # Assert total_debits and total_credits match expected
        pass

    def test_running_totals_multiple_chunks(self):
        """Verify running totals accumulate correctly across chunks."""
        # Create auditor
        # Process 3 chunks with known values
        # Assert final totals are sum of all chunks
        pass

    def test_account_aggregation(self):
        """Verify same account in multiple chunks is aggregated."""
        # Create auditor
        # Process 2 chunks with same account name
        # Assert account_balances dict has single entry with combined values
        pass

    def test_balance_check_balanced(self):
        """Verify get_balance_result returns balanced=True when debits=credits."""
        # Process data where debits = credits
        # Assert result["balanced"] is True
        # Assert result["difference"] is 0 or near-zero
        pass

    def test_balance_check_unbalanced(self):
        """Verify get_balance_result returns balanced=False when debits≠credits."""
        # Process data where debits ≠ credits
        # Assert result["balanced"] is False
        # Assert result["difference"] is correct
        pass

    def test_abnormal_asset_credit(self):
        """Verify asset account with net credit is flagged as abnormal."""
        # Process data with "Cash" account having credit > debit
        # Assert abnormal_balances contains the account
        # Assert type is "Asset" and issue mentions "Credit balance"
        pass

    def test_abnormal_liability_debit(self):
        """Verify liability account with net debit is flagged as abnormal."""
        # Process data with "Accounts Payable" having debit > credit
        # Assert abnormal_balances contains the account
        # Assert type is "Liability" and issue mentions "Debit balance"
        pass

    def test_materiality_classification_material(self):
        """Verify balances >= threshold are marked material."""
        # Create auditor with threshold=500
        # Process data with abnormal balance of $600
        # Assert materiality is "material"
        pass

    def test_materiality_classification_immaterial(self):
        """Verify balances < threshold are marked immaterial."""
        # Create auditor with threshold=500
        # Process data with abnormal balance of $100
        # Assert materiality is "immaterial"
        pass

    def test_clear_releases_memory(self):
        """Verify clear() method releases accumulated data."""
        # Create auditor and process data
        # Assert account_balances is populated
        # Call clear()
        # Assert account_balances is empty
        # Assert totals are reset to 0
        pass
```

#### 2. Integration Tests — Full Pipeline

```python
class TestStreamingPipeline:
    """Integration tests for full audit pipeline."""

    def test_csv_streaming(self, tmp_path):
        """Verify CSV file is processed correctly via streaming."""
        # Create temp CSV with 1000 rows
        # Call audit_trial_balance_streaming()
        # Assert result format matches expected schema
        # Assert row_count is correct
        pass

    def test_excel_streaming(self, tmp_path):
        """Verify Excel file is processed correctly via streaming."""
        # Create temp XLSX with 1000 rows
        # Call audit_trial_balance_streaming()
        # Assert result format matches expected schema
        pass

    def test_large_file_memory_stable(self):
        """Verify memory usage stays bounded during large file processing."""
        # Use generate_large_tb.py to create 50K row file
        # Monitor memory before, during, after processing
        # Assert peak memory < 2x initial memory
        # Assert final memory ≈ initial memory (no leak)
        pass

    def test_result_format_compatibility(self):
        """Verify streaming result format matches Day 5 non-streaming format."""
        # Process same file with streaming
        # Assert all expected keys present:
        #   status, balanced, total_debits, total_credits, difference,
        #   row_count, timestamp, message, abnormal_balances,
        #   materiality_threshold, material_count, immaterial_count, has_risk_alerts
        pass
```

#### 3. Performance Benchmarks

```python
class TestStreamingPerformance:
    """Performance benchmarks for streaming auditor."""

    def test_benchmark_1k_rows(self, benchmark):
        """Benchmark: 1,000 rows processing time."""
        # Generate 1K row file
        # benchmark(audit_trial_balance_streaming, file_bytes, filename)
        pass

    def test_benchmark_10k_rows(self, benchmark):
        """Benchmark: 10,000 rows processing time."""
        pass

    def test_benchmark_50k_rows(self, benchmark):
        """Benchmark: 50,000 rows processing time."""
        pass

    def test_chunk_size_comparison(self, benchmark):
        """Compare performance with different chunk sizes."""
        # Test with chunk_size = 1000, 5000, 10000, 20000
        # Report optimal chunk size for 50K rows
        pass
```

#### 4. Edge Cases

```python
class TestStreamingEdgeCases:
    """Edge case tests."""

    def test_empty_file(self):
        """Verify graceful handling of empty file."""
        pass

    def test_missing_columns(self):
        """Verify error when Debit/Credit columns missing."""
        pass

    def test_non_numeric_values(self):
        """Verify non-numeric values are coerced to 0."""
        pass

    def test_unicode_account_names(self):
        """Verify Unicode characters in account names handled correctly."""
        pass

    def test_very_large_numbers(self):
        """Verify large dollar amounts don't overflow."""
        # Test with values > 1 billion
        pass

    def test_negative_values(self):
        """Verify negative values in Debit/Credit columns handled."""
        pass
```

---

## Acceptance Criteria

| Criterion | Target |
|-----------|--------|
| All unit tests pass | 100% |
| All integration tests pass | 100% |
| Memory leak test passes | Peak < 2x baseline |
| 50K row benchmark | < 5 seconds |
| Result format compatibility | 100% |

---

## Implementation Notes

### Memory Monitoring Pattern
```python
import psutil
import gc

def get_memory_mb():
    gc.collect()
    return psutil.Process().memory_info().rss / 1024 / 1024

# Usage
before = get_memory_mb()
# ... process ...
after = get_memory_mb()
assert after < before * 2, f"Memory grew from {before}MB to {after}MB"
```

### Test Data Generation
Use `generate_large_tb.py` or create fixtures:
```python
@pytest.fixture
def sample_csv_bytes():
    """Generate sample CSV as bytes."""
    data = "Account Name,Debit,Credit\n"
    data += "Cash,1000,\n"
    data += "Revenue,,1000\n"
    return data.encode('utf-8')
```

---

## Complexity Score

**BackendCritic Assessment:** 4/10

- Standard pytest patterns
- No external services required
- Memory monitoring is straightforward with psutil
- Benchmark tooling provided by pytest-benchmark

**Risk:** None identified. Proceed with implementation on Day 8.
