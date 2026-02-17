"""
Paciolus Audit Engine — Float Precision Tests (Sprint 263)
Edge-case tests verifying that math.fsum, Decimal concentration division,
and Decimal rounding modulo produce correct results for:
- Very large monetary values (trillions)
- Very small values (fractions of a cent)
- Values known to cause float rounding errors (0.1 + 0.2)
- Streaming cross-chunk accumulation precision
- Rounding detection near divisor boundaries
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from audit_engine import StreamingAuditor, check_balance

# =============================================================================
# Fix 1: check_balance() — math.fsum precision
# =============================================================================


class TestCheckBalancePrecision:
    """Verify math.fsum produces correct sums for edge-case datasets."""

    def test_many_small_values_that_cause_float_drift(self):
        """0.1 added 10 times should equal 1.0, not 0.9999...999 or 1.0000...001."""
        # 1000 rows of 0.1 debit — naive float sum drifts
        rows = [{"Account Name": f"Acct{i}", "Debit": 0.1, "Credit": 0.0}
                for i in range(1000)]
        # One balancing credit
        rows.append({"Account Name": "Revenue", "Debit": 0.0, "Credit": 100.0})
        df = pd.DataFrame(rows)

        result = check_balance(df)
        assert result["status"] == "success"
        assert result["balanced"] is True
        assert result["total_debits"] == 100.0

    def test_trillion_scale_values(self):
        """Values in the trillions should sum precisely to 2 decimal places."""
        df = pd.DataFrame({
            "Account Name": ["Total Assets", "Total Liabilities"],
            "Debit": [1234567890123.45, 0.0],
            "Credit": [0.0, 1234567890123.45],
        })
        result = check_balance(df)
        assert result["status"] == "success"
        assert result["balanced"] is True
        assert result["total_debits"] == 1234567890123.45
        assert result["total_credits"] == 1234567890123.45
        assert result["difference"] == 0.0

    def test_mixed_large_and_tiny_values(self):
        """Summing 1e12 + many 0.01 values should not lose the small values."""
        rows = [{"Account Name": "BigAsset", "Debit": 1_000_000_000_000.00, "Credit": 0.0}]
        # 100 rows of $0.01 debit each = $1.00
        for i in range(100):
            rows.append({"Account Name": f"SmallAcct{i}", "Debit": 0.01, "Credit": 0.0})
        # Balancing credit
        rows.append({"Account Name": "Revenue", "Debit": 0.0, "Credit": 1_000_000_000_001.00})
        df = pd.DataFrame(rows)

        result = check_balance(df)
        assert result["status"] == "success"
        assert result["balanced"] is True
        assert result["total_debits"] == 1_000_000_000_001.0

    def test_classic_float_error_values(self):
        """0.1 + 0.2 should equal 0.3, not 0.30000000000000004."""
        df = pd.DataFrame({
            "Account Name": ["A", "B", "C"],
            "Debit": [0.1, 0.2, 0.0],
            "Credit": [0.0, 0.0, 0.3],
        })
        result = check_balance(df)
        assert result["status"] == "success"
        assert result["balanced"] is True


# =============================================================================
# Fix 2: StreamingAuditor — cross-chunk accumulation
# =============================================================================


class TestStreamingAccumulationPrecision:
    """Verify chunk-list + math.fsum avoids cross-chunk drift."""

    def test_many_chunks_of_small_values(self):
        """Process 50 chunks of 20 rows each with 0.1 values — total should be exact."""
        auditor = StreamingAuditor(materiality_threshold=1.0)
        chunk_size = 20

        for chunk_idx in range(50):
            df = pd.DataFrame({
                "Account Name": [f"Acct{chunk_idx}_{i}" for i in range(chunk_size)],
                "Debit": [0.1] * chunk_size,
                "Credit": [0.0] * chunk_size,
            })
            if not auditor.columns_discovered:
                auditor._discover_columns(df)
            auditor.process_chunk(df, (chunk_idx + 1) * chunk_size)

        result = auditor.get_balance_result()
        # 50 chunks * 20 rows * 0.1 = 100.0
        assert result["total_debits"] == 100.0
        assert result["total_credits"] == 0.0

    def test_alternating_large_small_chunks(self):
        """Alternating 1e9 and 0.01 chunks should accumulate precisely."""
        auditor = StreamingAuditor(materiality_threshold=1.0)

        # Chunk 1: one large value
        df1 = pd.DataFrame({
            "Account Name": ["BigAsset"],
            "Debit": [1_000_000_000.0],
            "Credit": [0.0],
        })
        auditor._discover_columns(df1)
        auditor.process_chunk(df1, 1)

        # Chunk 2: 100 tiny values
        df2 = pd.DataFrame({
            "Account Name": [f"Tiny{i}" for i in range(100)],
            "Debit": [0.01] * 100,
            "Credit": [0.0] * 100,
        })
        auditor.process_chunk(df2, 101)

        result = auditor.get_balance_result()
        assert result["total_debits"] == 1_000_000_001.0

    def test_clear_resets_chunk_lists(self):
        """After clear(), chunk lists should be empty and results should be zero."""
        auditor = StreamingAuditor(materiality_threshold=1.0)
        df = pd.DataFrame({
            "Account Name": ["Cash"],
            "Debit": [1000.0],
            "Credit": [0.0],
        })
        auditor._discover_columns(df)
        auditor.process_chunk(df, 1)

        auditor.clear()
        assert auditor._debit_chunks == []
        assert auditor._credit_chunks == []

    def test_balanced_across_chunks(self):
        """Debits in chunk 1, credits in chunk 2 — should detect balanced."""
        auditor = StreamingAuditor(materiality_threshold=1.0)

        df1 = pd.DataFrame({
            "Account Name": ["Cash", "Inventory"],
            "Debit": [50000.0, 30000.0],
            "Credit": [0.0, 0.0],
        })
        auditor._discover_columns(df1)
        auditor.process_chunk(df1, 2)

        df2 = pd.DataFrame({
            "Account Name": ["Revenue", "Payable"],
            "Debit": [0.0, 0.0],
            "Credit": [50000.0, 30000.0],
        })
        auditor.process_chunk(df2, 4)

        result = auditor.get_balance_result()
        assert result["balanced"] is True
        assert result["total_debits"] == 80000.0
        assert result["total_credits"] == 80000.0


# =============================================================================
# Fix 3: Concentration percentage — Decimal division
# =============================================================================


class TestConcentrationPrecision:
    """Verify Decimal division produces accurate concentration percentages."""

    def _build_auditor_with_accounts(self, accounts: dict[str, dict[str, float]]) -> StreamingAuditor:
        """Helper to set up a StreamingAuditor with pre-populated account balances."""
        auditor = StreamingAuditor(materiality_threshold=1.0)
        auditor.account_balances = accounts
        return auditor

    def test_exact_50_percent_concentration(self):
        """An account that is exactly 50% of its category should be flagged high."""
        auditor = self._build_auditor_with_accounts({
            "Accounts Receivable": {"debit": 500_000.0, "credit": 0.0},
            "Other Receivable": {"debit": 500_000.0, "credit": 0.0},
        })
        risks = auditor.detect_concentration_risk()
        # Both at exactly 50% — should trigger high severity
        assert len(risks) == 2
        for risk in risks:
            assert risk["severity"] == "high"
            assert risk["concentration_percent"] == 50.0

    def test_concentration_with_repeating_decimal(self):
        """1/3 concentration (33.33...%) should be computed precisely."""
        auditor = self._build_auditor_with_accounts({
            "Accounts Receivable": {"debit": 100_000.0, "credit": 0.0},
            "Trade Receivable": {"debit": 100_000.0, "credit": 0.0},
            "Other Receivable": {"debit": 100_000.0, "credit": 0.0},
        })
        risks = auditor.detect_concentration_risk()
        # 33.3% is above CONCENTRATION_THRESHOLD_MEDIUM (25%) but below HIGH (50%)
        for risk in risks:
            assert risk["severity"] == "medium"
            assert abs(risk["concentration_percent"] - 33.3) < 0.1

    def test_concentration_trillion_scale(self):
        """Concentration detection should work at trillion-dollar scale."""
        auditor = self._build_auditor_with_accounts({
            "Government Receivable": {"debit": 800_000_000_000.0, "credit": 0.0},
            "Corporate Receivable": {"debit": 200_000_000_000.0, "credit": 0.0},
        })
        risks = auditor.detect_concentration_risk()
        high_risk = [r for r in risks if r["severity"] == "high"]
        assert len(high_risk) == 1
        assert high_risk[0]["account"] == "Government Receivable"
        assert high_risk[0]["concentration_percent"] == 80.0

    def test_concentration_very_small_denominator(self):
        """Category total near the minimum threshold should not cause division artifacts."""
        # CONCENTRATION_MIN_CATEGORY_TOTAL = 1000.0
        auditor = self._build_auditor_with_accounts({
            "Petty Cash Receivable": {"debit": 800.0, "credit": 0.0},
            "Other Receivable": {"debit": 201.0, "credit": 0.0},
        })
        risks = auditor.detect_concentration_risk()
        # Total is 1001 (just above 1000 threshold), 800/1001 = 79.9% → high
        high_risks = [r for r in risks if r["severity"] == "high"]
        assert len(high_risks) == 1
        assert abs(high_risks[0]["concentration_percent"] - 79.9) < 0.2


# =============================================================================
# Fix 4: Rounding detection — Decimal modulo
# =============================================================================


class TestRoundingDetectionPrecision:
    """Verify Decimal modulo correctly identifies round amounts."""

    def _build_auditor_with_accounts(self, accounts: dict[str, dict[str, float]]) -> StreamingAuditor:
        auditor = StreamingAuditor(materiality_threshold=1.0)
        auditor.account_balances = accounts
        return auditor

    def test_exact_hundred_thousand(self):
        """$100,000 exactly should be detected as hundred_thousand rounding."""
        auditor = self._build_auditor_with_accounts({
            "Consulting Revenue": {"debit": 100_000.0, "credit": 0.0},
        })
        anomalies = auditor.detect_rounding_anomalies()
        assert len(anomalies) == 1
        assert anomalies[0]["amount"] == 100_000.0

    def test_near_boundary_not_round(self):
        """$100,000.01 should NOT be detected as a round amount."""
        auditor = self._build_auditor_with_accounts({
            "Consulting Revenue": {"debit": 100_000.01, "credit": 0.0},
        })
        anomalies = auditor.detect_rounding_anomalies()
        assert len(anomalies) == 0

    def test_float_modulo_edge_case(self):
        """$300,000 — float modulo of 300000.0 % 100000.0 should yield 0, not a drift value."""
        auditor = self._build_auditor_with_accounts({
            "Misc Revenue": {"debit": 300_000.0, "credit": 0.0},
        })
        anomalies = auditor.detect_rounding_anomalies()
        assert len(anomalies) == 1
        assert anomalies[0]["amount"] == 300_000.0

    def test_large_round_amount(self):
        """$1,000,000,000 (1 billion) should be detected as round."""
        auditor = self._build_auditor_with_accounts({
            "Investment Revenue": {"debit": 1_000_000_000.0, "credit": 0.0},
        })
        anomalies = auditor.detect_rounding_anomalies()
        assert len(anomalies) == 1

    def test_excluded_accounts_not_flagged(self):
        """Loan accounts are excluded from rounding detection."""
        auditor = self._build_auditor_with_accounts({
            "Term Loan": {"debit": 100_000.0, "credit": 0.0},
        })
        anomalies = auditor.detect_rounding_anomalies()
        assert len(anomalies) == 0

    def test_below_minimum_not_flagged(self):
        """Amounts below ROUNDING_MIN_AMOUNT (10,000) should not be flagged."""
        auditor = self._build_auditor_with_accounts({
            "Office Supplies": {"debit": 5_000.0, "credit": 0.0},
        })
        anomalies = auditor.detect_rounding_anomalies()
        assert len(anomalies) == 0

    def test_fifty_thousand_boundary(self):
        """$50,000 should be detected as fifty_thousand pattern."""
        auditor = self._build_auditor_with_accounts({
            "Advertising Expense": {"debit": 50_000.0, "credit": 0.0},
        })
        anomalies = auditor.detect_rounding_anomalies()
        assert len(anomalies) == 1

    def test_ten_thousand_boundary(self):
        """$10,000 should be detected as ten_thousand pattern."""
        auditor = self._build_auditor_with_accounts({
            "Travel Expense": {"debit": 10_000.0, "credit": 0.0},
        })
        anomalies = auditor.detect_rounding_anomalies()
        assert len(anomalies) == 1

    def test_credit_balance_round_amount(self):
        """Round amounts on the credit side should also be detected."""
        auditor = self._build_auditor_with_accounts({
            "Consulting Revenue": {"debit": 0.0, "credit": 200_000.0},
        })
        anomalies = auditor.detect_rounding_anomalies()
        assert len(anomalies) == 1
        assert anomalies[0]["amount"] == 200_000.0
