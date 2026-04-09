"""Liability Concentration Anomaly Generator.

Injects a trial balance where a single liability account represents >80% of
total liabilities. The engine's detect_concentration_risk() should flag this
as liability_concentration with HIGH severity (>= 50% threshold).
"""

import pandas as pd

from tests.anomaly_framework.base import AnomalyGenerator, AnomalyRecord


class LiabilityConcentrationGenerator(AnomalyGenerator):
    """Injects a dominant liability account representing >80% of total liabilities.

    Replaces all existing liability balances with a heavily skewed distribution:
    one account at $425,000 and a second at $75,000, giving 85% concentration.
    Rebalances via an equity account to maintain TB balance.
    """

    name = "liability_concentration"
    report_targets = ["RPT-01", "RPT-21"]

    def inject(self, df: pd.DataFrame, seed: int = 42) -> tuple[pd.DataFrame, list[AnomalyRecord]]:
        df = df.copy()

        # Remove existing liability accounts to control concentration
        liab_mask = df["Account Type"].str.lower() == "liability"
        removed_credit = df.loc[liab_mask, "Credit"].sum()
        df = df[~liab_mask].reset_index(drop=True)

        # Inject heavily skewed liabilities
        dominant_amount = 425_000.00
        minor_amount = 75_000.00
        total_new = dominant_amount + minor_amount

        new_rows = pd.DataFrame(
            [
                {
                    "Account": "2500",
                    "Account Name": "Term Loan Payable",
                    "Account Type": "Liability",
                    "Debit": 0.00,
                    "Credit": dominant_amount,
                },
                {
                    "Account": "2000",
                    "Account Name": "Accounts Payable - Trade",
                    "Account Type": "Liability",
                    "Debit": 0.00,
                    "Credit": minor_amount,
                },
            ]
        )

        # Rebalance via equity if liability total changed
        delta = total_new - removed_credit
        if abs(delta) > 0.01:
            equity_mask = df["Account Type"].str.lower() == "equity"
            if equity_mask.any():
                idx = df.index[equity_mask][0]
                df.loc[idx, "Credit"] = df.loc[idx, "Credit"] - delta

        df = pd.concat([df, new_rows], ignore_index=True)

        record = AnomalyRecord(
            anomaly_type="liability_concentration",
            report_targets=self.report_targets,
            injected_at="Injected 85% liability concentration in 'Term Loan Payable'",
            expected_field="abnormal_balances",
            expected_condition="any_match anomaly_type=liability_concentration",
            metadata={
                "dominant_account": "Term Loan Payable",
                "concentration_pct": 85.0,
                "amount": dominant_amount,
            },
        )

        return df, [record]
