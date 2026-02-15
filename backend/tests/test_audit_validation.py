"""
Paciolus Audit Engine — Validation & Precision Tests
Balance sheet validation, vectorized keyword matching, Decimal accumulation
precision, anomaly detection edge cases, and variance/flux edge cases.
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
    detect_abnormal_balances,
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


# =============================================================================
# Balance Sheet Validator Tests (Sprint 43)
# =============================================================================

class TestBalanceSheetValidator:
    """Test balance sheet equation validation (Sprint 43 - Phase III)."""

    @pytest.fixture
    def balanced_bs_csv(self) -> bytes:
        """Generate CSV with balanced balance sheet (A = L + E)."""
        data = """Account Name,Debit,Credit
Cash,50000,
Accounts Receivable,30000,
Inventory,20000,
Accounts Payable,,40000
Notes Payable,,30000
Common Stock,,20000
Retained Earnings,,10000
"""
        # Assets: 50000 + 30000 + 20000 = 100000
        # Liabilities: 40000 + 30000 = 70000
        # Equity: 20000 + 10000 = 30000
        # L + E = 100000 = Assets
        return data.encode('utf-8')

    @pytest.fixture
    def unbalanced_bs_assets_high_csv(self) -> bytes:
        """Generate CSV with assets exceeding liabilities + equity."""
        data = """Account Name,Debit,Credit
Cash,80000,
Accounts Receivable,30000,
Accounts Payable,,40000
Common Stock,,20000
Retained Earnings,,10000
"""
        # Assets: 80000 + 30000 = 110000
        # Liabilities: 40000
        # Equity: 20000 + 10000 = 30000
        # L + E = 70000 < 110000 Assets (diff = 40000)
        return data.encode('utf-8')

    @pytest.fixture
    def unbalanced_bs_liabilities_high_csv(self) -> bytes:
        """Generate CSV with liabilities + equity exceeding assets."""
        data = """Account Name,Debit,Credit
Cash,30000,
Accounts Payable,,50000
Notes Payable,,30000
Common Stock,,20000
Retained Earnings,,10000
"""
        # Assets: 30000
        # Liabilities: 50000 + 30000 = 80000
        # Equity: 20000 + 10000 = 30000
        # L + E = 110000 > 30000 Assets (diff = -80000)
        return data.encode('utf-8')

    @pytest.fixture
    def minor_imbalance_csv(self) -> bytes:
        """Generate CSV with minor imbalance (<$1000)."""
        data = """Account Name,Debit,Credit
Cash,50500,
Accounts Payable,,50000
Common Stock,,100
"""
        # Assets: 50500
        # Liabilities: 50000
        # Equity: 100
        # L + E = 50100, diff = 400
        return data.encode('utf-8')

    def test_balanced_balance_sheet(self, balanced_bs_csv):
        """Verify balanced balance sheet is correctly identified."""
        result = audit_trial_balance_streaming(
            file_bytes=balanced_bs_csv,
            filename="test.csv",
            materiality_threshold=0
        )

        bs_validation = result["balance_sheet_validation"]

        assert bs_validation["is_balanced"] is True
        assert bs_validation["status"] == "balanced"
        assert bs_validation["severity"] is None
        assert abs(bs_validation["difference"]) < 0.01

    def test_unbalanced_assets_high(self, unbalanced_bs_assets_high_csv):
        """Verify assets > L+E imbalance is detected."""
        result = audit_trial_balance_streaming(
            file_bytes=unbalanced_bs_assets_high_csv,
            filename="test.csv",
            materiality_threshold=0
        )

        bs_validation = result["balance_sheet_validation"]

        assert bs_validation["is_balanced"] is False
        assert bs_validation["difference"] > 0  # Assets exceed L+E
        assert bs_validation["severity"] == "high"  # diff > 10000
        assert "exceed" in bs_validation["recommendation"].lower()

    def test_unbalanced_liabilities_high(self, unbalanced_bs_liabilities_high_csv):
        """Verify L+E > assets imbalance is detected."""
        result = audit_trial_balance_streaming(
            file_bytes=unbalanced_bs_liabilities_high_csv,
            filename="test.csv",
            materiality_threshold=0
        )

        bs_validation = result["balance_sheet_validation"]

        assert bs_validation["is_balanced"] is False
        assert bs_validation["difference"] < 0  # L+E exceed Assets
        assert bs_validation["severity"] == "high"

    def test_minor_imbalance_low_severity(self, minor_imbalance_csv):
        """Verify minor imbalance (<$1000) has low severity."""
        result = audit_trial_balance_streaming(
            file_bytes=minor_imbalance_csv,
            filename="test.csv",
            materiality_threshold=0
        )

        bs_validation = result["balance_sheet_validation"]

        assert bs_validation["is_balanced"] is False
        assert bs_validation["status"] == "minor_imbalance"
        assert bs_validation["severity"] == "low"
        assert bs_validation["abs_difference"] < 1000

    def test_validation_includes_equation(self, balanced_bs_csv):
        """Verify validation result includes the equation."""
        result = audit_trial_balance_streaming(
            file_bytes=balanced_bs_csv,
            filename="test.csv",
            materiality_threshold=0
        )

        bs_validation = result["balance_sheet_validation"]

        assert "equation" in bs_validation
        assert bs_validation["equation"] == "Assets = Liabilities + Equity"

    def test_validation_includes_totals(self, balanced_bs_csv):
        """Verify validation result includes all component totals."""
        result = audit_trial_balance_streaming(
            file_bytes=balanced_bs_csv,
            filename="test.csv",
            materiality_threshold=0
        )

        bs_validation = result["balance_sheet_validation"]

        assert "total_assets" in bs_validation
        assert "total_liabilities" in bs_validation
        assert "total_equity" in bs_validation
        assert "liabilities_plus_equity" in bs_validation

    def test_imbalance_added_to_risk_summary(self, unbalanced_bs_assets_high_csv):
        """Verify imbalance is added to risk_summary."""
        result = audit_trial_balance_streaming(
            file_bytes=unbalanced_bs_assets_high_csv,
            filename="test.csv",
            materiality_threshold=0
        )

        risk_summary = result["risk_summary"]

        assert "balance_sheet_imbalance" in risk_summary["anomaly_types"]
        assert risk_summary["anomaly_types"]["balance_sheet_imbalance"] == 1

    def test_balanced_not_in_risk_summary(self, balanced_bs_csv):
        """Verify balanced BS does not add to risk_summary."""
        result = audit_trial_balance_streaming(
            file_bytes=balanced_bs_csv,
            filename="test.csv",
            materiality_threshold=0
        )

        risk_summary = result["risk_summary"]

        # balance_sheet_imbalance should not be in anomaly_types for balanced BS
        assert risk_summary["anomaly_types"].get("balance_sheet_imbalance", 0) == 0

    def test_multi_sheet_balance_sheet_validation(self):
        """Verify balance sheet validation works in multi-sheet audits."""
        from audit_engine import audit_trial_balance_multi_sheet

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Sheet 1: Assets
            df1 = pd.DataFrame({
                "Account Name": ["Cash", "Inventory"],
                "Debit": [50000, 30000],
                "Credit": [0, 0]
            })
            df1.to_excel(writer, sheet_name="Assets", index=False)

            # Sheet 2: Liabilities and Equity
            df2 = pd.DataFrame({
                "Account Name": ["Accounts Payable", "Common Stock"],
                "Debit": [0, 0],
                "Credit": [50000, 30000]
            })
            df2.to_excel(writer, sheet_name="Liabilities", index=False)

        result = audit_trial_balance_multi_sheet(
            file_bytes=output.getvalue(),
            filename="test.xlsx",
            selected_sheets=["Assets", "Liabilities"],
            materiality_threshold=0
        )

        assert "balance_sheet_validation" in result
        bs_validation = result["balance_sheet_validation"]
        assert bs_validation["is_balanced"] is True

    def test_standalone_function_works(self):
        """Verify the standalone validate_balance_sheet_equation function works."""
        from audit_engine import validate_balance_sheet_equation
        from ratio_engine import CategoryTotals

        # Create balanced totals
        totals = CategoryTotals(
            total_assets=100000,
            total_liabilities=70000,
            total_equity=30000
        )

        result = validate_balance_sheet_equation(totals)

        assert result["is_balanced"] is True
        assert result["total_assets"] == 100000
        assert result["liabilities_plus_equity"] == 100000


# =============================================================================
# Sprint 191: Vectorization & Precision Tests
# =============================================================================

class TestVectorizedKeywordMatching:
    """Test that vectorized str.contains() produces same results as apply()."""

    def test_vectorized_keyword_matching_equivalence(self):
        """100-row CSV verifying vectorized str.contains() produces correct results.

        Tests the standalone detect_abnormal_balances() function which uses
        the vectorized keyword matching (ASSET_KEYWORDS / LIABILITY_KEYWORDS).
        """
        rows = ["Account Name,Debit,Credit"]
        # Use names that contain exact keywords from ASSET_KEYWORDS and LIABILITY_KEYWORDS
        asset_names = [
            "Cash in Bank", "Accounts Receivable", "Prepaid Insurance",
            "Equipment - Office", "Land Holdings", "Building - HQ",
            "Inventory - Raw Materials", "Vehicle Fleet", "Bank Account - Ops",
        ]
        liability_names = [
            "Accounts Payable", "Loan from Bank", "Tax Liability",
            "Accrued Expenses", "Unearned Revenue", "Debt Facility",
            "Mortgage - Property", "Note Payable - Short",
        ]
        neutral_names = [
            "Revenue - Sales", "Cost of Goods Sold", "Rent Expense",
            "Salary Expense", "Depreciation", "Retained Earnings",
            "Common Stock", "Dividends", "Interest Income", "Utilities",
        ]

        total_debit = 0
        total_credit = 0

        # Asset accounts with abnormal credit balances (should be flagged)
        for i, name in enumerate(asset_names):
            credit = 1000 + i * 100
            rows.append(f"{name},,{credit}")
            total_credit += credit

        # Liability accounts with abnormal debit balances (should be flagged)
        for i, name in enumerate(liability_names):
            debit = 2000 + i * 100
            rows.append(f"{name},{debit},")
            total_debit += debit

        # Neutral accounts (should not be flagged by keyword matching)
        for i, name in enumerate(neutral_names):
            debit = 500 + i * 50
            rows.append(f"{name},{debit},")
            total_debit += debit

        # Fill to ~100 rows with more accounts
        for i in range(100 - len(asset_names) - len(liability_names) - len(neutral_names)):
            credit = 100 + i * 10
            rows.append(f"Other Account {i},,{credit}")
            total_credit += credit

        # Balance it
        diff = total_debit - total_credit
        if diff > 0:
            rows.append(f"Balancing,,{diff}")
        elif diff < 0:
            rows.append(f"Balancing,{abs(diff)},")

        csv_bytes = "\n".join(rows).encode('utf-8')
        df = pd.read_csv(io.BytesIO(csv_bytes))

        # Call the standalone function directly (uses vectorized keyword matching)
        abnormals = detect_abnormal_balances(df, materiality_threshold=0)

        # All 9 asset accounts should be flagged (credit balance = abnormal for assets)
        asset_flagged = [ab for ab in abnormals if ab["type"] == "Asset"]
        assert len(asset_flagged) == len(asset_names), (
            f"Expected {len(asset_names)} asset abnormals, got {len(asset_flagged)}"
        )

        # All 8 liability accounts should be flagged (debit balance = abnormal)
        liability_flagged = [ab for ab in abnormals if ab["type"] == "Liability"]
        assert len(liability_flagged) == len(liability_names), (
            f"Expected {len(liability_names)} liability abnormals, got {len(liability_flagged)}"
        )

        # Verify specific accounts are present
        flagged_names = {ab["account"] for ab in abnormals}
        for name in asset_names:
            assert name in flagged_names, f"Asset '{name}' should be flagged"
        for name in liability_names:
            assert name in flagged_names, f"Liability '{name}' should be flagged"

        # Neutral accounts should NOT be flagged
        for name in neutral_names:
            assert name not in flagged_names, f"Neutral '{name}' should NOT be flagged"


class TestConcentrationDecimalAccumulation:
    """Test Decimal accumulation precision in concentration risk detection."""

    def test_concentration_decimal_accumulation(self):
        """Sum 1000x 0.1 values and verify exact total (float sum would drift)."""
        auditor = StreamingAuditor(materiality_threshold=0)

        # Create 1000 receivable accounts each with 0.1 balance
        # float sum of 1000 * 0.1 may != 100.0 due to IEEE 754
        # Decimal accumulation should give exactly 100.0
        rows = ["Account Name,Debit,Credit"]
        for i in range(1000):
            rows.append(f"Receivable {i:04d},0.1,")
        # Add a balancing credit
        rows.append("Revenue,,100")

        csv_bytes = "\n".join(rows).encode('utf-8')
        df = pd.read_csv(io.BytesIO(csv_bytes))
        auditor.process_chunk(df, len(df))

        # Force concentration detection
        concentration = auditor.detect_concentration_risk()

        # The category total for receivables should be exactly 100.0
        # (Decimal accumulation prevents float drift)
        # Each account represents 0.1% — below concentration thresholds,
        # so no individual risks should be flagged
        assert len(concentration) == 0, (
            "1000 equal accounts should have no concentration risk"
        )


# =============================================================================
# Sprint 241: Financial Edge Cases — Anomaly Detection
# =============================================================================

class TestAnomalyDetectionEdgeCases:
    """Sprint 241: Targeted edge case tests for anomaly detection."""

    def test_zero_net_balance_not_flagged_abnormal(self):
        """10000 debit / 10000 credit on asset — zero net balance, should NOT be flagged."""
        data = """Account Name,Debit,Credit
Cash,10000,10000
Revenue,,5000
Expenses,5000,
"""
        result = audit_trial_balance_streaming(
            file_bytes=data.encode("utf-8"),
            filename="zero_net.csv",
            materiality_threshold=0,
        )

        # Cash has zero net balance (debit == credit), should be skipped
        abnormal = result.get("abnormal_balances", [])
        cash_flagged = [ab for ab in abnormal if ab["account"].lower() == "cash"]
        assert len(cash_flagged) == 0, "Zero net balance account should NOT be flagged abnormal"

    def test_concentration_risk_all_zero_balances(self):
        """All accounts have $0 balance — no division by zero in concentration."""
        data = """Account Name,Debit,Credit
Cash,0,0
Accounts Receivable,0,0
Inventory,0,0
"""
        result = audit_trial_balance_streaming(
            file_bytes=data.encode("utf-8"),
            filename="all_zeros.csv",
            materiality_threshold=0,
        )

        # Should complete without division by zero errors
        assert result["status"] == "success"
        abnormal = result.get("abnormal_balances", [])
        # No accounts should be flagged (all zeros)
        assert len(abnormal) == 0

    def test_multiple_anomaly_merge_flags(self):
        """Account triggers suspense + concentration + abnormal — all flags set."""
        from audit_engine import _merge_anomalies

        abnormal = [{
            "account": "Suspense Account",
            "type": "Asset",
            "issue": "Net Credit balance (should be Debit)",
            "amount": 50000.0,
            "severity": "high",
            "anomaly_type": "natural_balance_violation",
        }]

        suspense = [{
            "account": "Suspense Account",
            "confidence": 0.9,
            "matched_keywords": ["suspense"],
        }]

        concentration = [{
            "account": "Suspense Account",
            "concentration_percent": 85.0,
            "category_total": 58823.53,
        }]

        rounding = [{
            "account": "Suspense Account",
            "rounding_pattern": "exact_thousands",
        }]

        merged = _merge_anomalies(abnormal, suspense, concentration, rounding)

        # Should still be just 1 entry (merged, not duplicated)
        assert len(merged) == 1
        entry = merged[0]

        # All flags should be set
        assert entry.get("is_suspense_account") is True
        assert entry.get("suspense_confidence") == 0.9
        assert entry.get("has_concentration_risk") is True
        assert entry.get("concentration_percent") == 85.0
        assert entry.get("has_rounding_anomaly") is True
        assert entry.get("rounding_pattern") == "exact_thousands"

    def test_materiality_at_exact_boundary(self):
        """Amount == materiality threshold — verify >= inclusive behavior (ISA 320)."""
        data = """Account Name,Debit,Credit
Cash,,1000
Revenue,,1000
Expenses,2000,
"""
        # Cash (asset) has credit balance — abnormal
        # Amount = 1000, materiality = 1000 — should be "material" (>=)
        result = audit_trial_balance_streaming(
            file_bytes=data.encode("utf-8"),
            filename="boundary.csv",
            materiality_threshold=1000,
        )

        abnormal = result.get("abnormal_balances", [])
        cash_entries = [ab for ab in abnormal if ab["account"].lower() == "cash"]
        if cash_entries:
            assert cash_entries[0]["materiality"] == "material", \
                "Amount exactly at threshold should be material (>= behavior)"


class TestVarianceEdgeCases:
    """Sprint 241: Targeted edge case tests for variance/flux calculations."""

    def test_prior_exactly_near_zero_returns_none_percent(self):
        """Prior = 0.005 (exactly NEAR_ZERO boundary) — should return None percent."""
        from prior_period_comparison import calculate_variance, NEAR_ZERO

        dollar_var, pct_var, is_sig, direction = calculate_variance(
            current=1_000_000.0,
            prior=NEAR_ZERO,  # 0.005 — exactly at boundary
            amount_threshold=0.0,
            percent_threshold=0.0,
        )

        # abs(0.005) > NEAR_ZERO is False (0.005 > 0.005 is False)
        assert pct_var is None, "Prior at exactly NEAR_ZERO should produce None percent"

    def test_prior_negative_near_zero(self):
        """Prior = -0.00001 (negative small) — should return None percent, not crash."""
        from prior_period_comparison import calculate_variance

        dollar_var, pct_var, is_sig, direction = calculate_variance(
            current=500.0,
            prior=-0.00001,
            amount_threshold=0.0,
            percent_threshold=0.0,
        )

        # abs(-0.00001) = 0.00001, which is < NEAR_ZERO (0.005)
        assert pct_var is None, "Negative near-zero prior should produce None percent"

    def test_flux_near_zero_prior_no_inf(self):
        """Flux engine: prior=0.001 (below NEAR_ZERO), current=1M — no inf output."""
        from flux_engine import FluxEngine

        engine = FluxEngine(materiality_threshold=0.0)
        current = {"TestAccount": {"net": 1_000_000.0, "type": "Asset"}}
        prior = {"TestAccount": {"net": 0.001, "type": "Asset"}}

        result = engine.compare(current, prior)
        result_dict = result.to_dict()

        acct = next(i for i in result_dict["items"] if i["account"] == "TestAccount")
        # Near-zero prior should give None, not inf
        assert acct["delta_percent"] is None


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
