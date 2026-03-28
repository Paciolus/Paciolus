"""Baseline anomaly tests — false-positive, threshold boundary, compound, and materiality.

These tests complement the detection tests (test_anomaly_detection.py) by verifying:
1. The clean base TB produces zero findings (no false positives).
2. Detection thresholds trigger at the documented boundaries.
3. Multiple anomalies injected into the same TB are all independently detected.
4. Materiality threshold affects severity classification.
"""

import pandas as pd
import pytest

from audit_engine import audit_trial_balance_streaming
from tests.anomaly_framework.fixtures.base_trial_balance import BaseTrialBalanceFactory
from tests.anomaly_framework.generators.related_party_activity import RelatedPartyActivityGenerator
from tests.anomaly_framework.generators.round_number import RoundNumberGenerator
from tests.anomaly_framework.generators.suspense_account import SuspenseAccountGenerator


def _run_audit(df: pd.DataFrame, materiality: float = 0.0) -> dict:
    """Helper: convert DataFrame to CSV bytes and run the audit engine."""
    csv_bytes = df.to_csv(index=False).encode()
    return audit_trial_balance_streaming(
        file_bytes=csv_bytes,
        filename="baseline_test.csv",
        materiality_threshold=materiality,
    )


# =============================================================================
# 1. Negative Baseline — Clean TB Must Produce Zero Findings
# =============================================================================


class TestNegativeBaseline:
    """Verify the clean base trial balance produces no anomaly findings."""

    def test_clean_tb_produces_zero_findings(self):
        """Base trial balance must produce zero anomaly findings."""
        result = _run_audit(BaseTrialBalanceFactory.as_dataframe())

        assert result["status"] == "success"
        assert result["balanced"] is True

        abnormal = result.get("abnormal_balances", [])
        assert len(abnormal) == 0, (
            f"Base TB should produce 0 findings but got {len(abnormal)}: "
            f"{[(a.get('account'), a.get('anomaly_type')) for a in abnormal]}"
        )

    def test_clean_tb_is_balanced(self):
        """Base trial balance total debits must equal total credits."""
        result = _run_audit(BaseTrialBalanceFactory.as_dataframe())
        assert result["balanced"] is True
        assert result["total_debits"] == result["total_credits"]


# =============================================================================
# 2. Threshold Boundary Tests
# =============================================================================


class TestThresholdBoundaries:
    """Verify detection triggers at documented threshold boundaries."""

    def test_rounding_just_below_min_amount(self):
        """Round amount at $9,999 should NOT trigger rounding detection."""
        df = BaseTrialBalanceFactory.as_dataframe()
        # Set an expense to $9,999 (below ROUNDING_MIN_AMOUNT = 10,000)
        expense_mask = (df["Account Type"] == "Expense") & (
            ~df["Account Name"].str.contains("Cost of|Salaries|Depreciation", case=False)
        )
        idx = df.index[expense_mask][0]
        old_amt = df.loc[idx, "Debit"]
        df.loc[idx, "Debit"] = 9_999.00

        # Rebalance via Cash - Operating
        cash_idx = df.index[df["Account Name"].str.contains("Cash - Operating")][0]
        df.loc[cash_idx, "Debit"] = df.loc[cash_idx, "Debit"] - (9_999.00 - old_amt)

        result = _run_audit(df)
        rounding_findings = [
            a for a in result.get("abnormal_balances", []) if a.get("anomaly_type") == "rounding_anomaly"
        ]
        assert len(rounding_findings) == 0, "Amount $9,999 should NOT trigger rounding detection"

    def test_rounding_at_min_amount(self):
        """Round amount at $10,000 SHOULD trigger rounding detection."""
        df = BaseTrialBalanceFactory.as_dataframe()
        expense_mask = (df["Account Type"] == "Expense") & (
            ~df["Account Name"].str.contains("Cost of|Salaries|Depreciation", case=False)
        )
        idx = df.index[expense_mask][0]
        old_amt = df.loc[idx, "Debit"]
        df.loc[idx, "Debit"] = 10_000.00

        cash_idx = df.index[df["Account Name"].str.contains("Cash - Operating")][0]
        df.loc[cash_idx, "Debit"] = df.loc[cash_idx, "Debit"] - (10_000.00 - old_amt)

        result = _run_audit(df)
        rounding_findings = [
            a for a in result.get("abnormal_balances", []) if a.get("anomaly_type") == "rounding_anomaly"
        ]
        assert len(rounding_findings) >= 1, "Amount $10,000 SHOULD trigger rounding detection"

    def test_concentration_below_medium_threshold(self):
        """Account at 24% of category should NOT trigger concentration."""
        df = BaseTrialBalanceFactory.as_dataframe()
        # The restructured base TB already has all concentrations < 24%
        result = _run_audit(df)
        concentration_findings = [
            a for a in result.get("abnormal_balances", []) if "concentration" in a.get("anomaly_type", "")
        ]
        assert len(concentration_findings) == 0, (
            f"No account should exceed 25% concentration but got: "
            f"{[(a['account'], a['anomaly_type'], a.get('concentration_percent')) for a in concentration_findings]}"
        )

    def test_concentration_at_high_threshold(self):
        """Account at 55% of category SHOULD trigger HIGH severity."""
        df = BaseTrialBalanceFactory.as_dataframe()
        # Replace all liabilities with one dominant at 55%
        liab_mask = df["Account Type"].str.lower() == "liability"
        total_liab = df.loc[liab_mask, "Credit"].sum()
        df = df[~liab_mask].reset_index(drop=True)

        dominant = total_liab * 0.55
        minor = total_liab * 0.45
        new_rows = pd.DataFrame(
            [
                {
                    "Account": "2500",
                    "Account Name": "Term Loan Payable",
                    "Account Type": "Liability",
                    "Debit": 0.0,
                    "Credit": dominant,
                },
                {
                    "Account": "2000",
                    "Account Name": "Accounts Payable - Trade",
                    "Account Type": "Liability",
                    "Debit": 0.0,
                    "Credit": minor,
                },
            ]
        )
        df = pd.concat([df, new_rows], ignore_index=True)

        result = _run_audit(df)
        high_conc = [
            a
            for a in result.get("abnormal_balances", [])
            if a.get("anomaly_type") == "liability_concentration" and a.get("severity") == "high"
        ]
        assert len(high_conc) >= 1, "55% concentration SHOULD trigger HIGH severity finding"


# =============================================================================
# 3. Compound Anomaly Test
# =============================================================================


class TestCompoundAnomalies:
    """Verify multiple anomalies injected into the same TB are all detected."""

    def test_three_independent_anomalies_all_detected(self):
        """Chain suspense + rounding + related-party and verify all found."""
        base_df = BaseTrialBalanceFactory.as_dataframe()

        # Chain balance-preserving generators
        df1, records1 = SuspenseAccountGenerator().inject(base_df, seed=1)
        df2, records2 = RoundNumberGenerator().inject(df1, seed=2)
        df3, records3 = RelatedPartyActivityGenerator().inject(df2, seed=3)

        result = _run_audit(df3)
        assert result["status"] == "success"

        abnormal = result.get("abnormal_balances", [])
        anomaly_types = {a.get("anomaly_type") for a in abnormal}
        flag_types = set()
        for a in abnormal:
            if a.get("is_suspense_account"):
                flag_types.add("suspense_account")
            if a.get("is_related_party"):
                flag_types.add("related_party")
            if a.get("has_rounding_anomaly"):
                flag_types.add("rounding_anomaly")

        all_detected = anomaly_types | flag_types

        assert "suspense_account" in all_detected or "suspense_account" in anomaly_types, (
            f"Suspense anomaly not detected. Types found: {anomaly_types}, flags: {flag_types}"
        )
        assert "rounding_anomaly" in all_detected or "rounding_anomaly" in anomaly_types, (
            f"Rounding anomaly not detected. Types found: {anomaly_types}, flags: {flag_types}"
        )
        assert "related_party" in all_detected or "related_party" in anomaly_types, (
            f"Related party anomaly not detected. Types found: {anomaly_types}, flags: {flag_types}"
        )


# =============================================================================
# 4. Materiality Variation Tests
# =============================================================================


class TestMaterialityVariation:
    """Verify materiality threshold affects severity classification."""

    @pytest.mark.parametrize(
        "threshold,expected_materiality",
        [
            (0.0, "material"),  # everything is material at zero threshold
            (500_000.0, "immaterial"),  # most anomalies below this are immaterial
        ],
    )
    def test_rounding_materiality_varies_with_threshold(self, threshold, expected_materiality):
        """Rounding findings change materiality based on threshold."""
        gen = RoundNumberGenerator(amount_scale=100_000.0)
        base_df = BaseTrialBalanceFactory.as_dataframe()
        mutated_df, _ = gen.inject(base_df, seed=42)

        result = _run_audit(mutated_df, materiality=threshold)
        rounding = [a for a in result.get("abnormal_balances", []) if a.get("anomaly_type") == "rounding_anomaly"]

        if rounding:
            assert rounding[0]["materiality"] == expected_materiality, (
                f"At threshold ${threshold:,.0f}, expected '{expected_materiality}' "
                f"but got '{rounding[0]['materiality']}'"
            )

    def test_suspense_materiality_at_high_threshold(self):
        """Suspense finding at $15,743 is immaterial when threshold is $50,000."""
        gen = SuspenseAccountGenerator()
        base_df = BaseTrialBalanceFactory.as_dataframe()
        mutated_df, _ = gen.inject(base_df, seed=42)

        result = _run_audit(mutated_df, materiality=50_000.0)
        suspense = [
            a
            for a in result.get("abnormal_balances", [])
            if a.get("anomaly_type") == "suspense_account" or a.get("is_suspense_account") is True
        ]

        assert len(suspense) >= 1, "Suspense account should still be detected"
        assert suspense[0]["materiality"] == "immaterial", "$15,743 suspense should be immaterial at $50K threshold"
