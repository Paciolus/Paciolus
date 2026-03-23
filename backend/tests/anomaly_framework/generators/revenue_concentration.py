"""Revenue Concentration Anomaly Generator.

Injects a trial balance where >80% of total revenue comes from a single
revenue account. The engine's detect_revenue_concentration() should flag
this as a concentration risk.
"""

import pandas as pd

from tests.anomaly_framework.base import AnomalyGenerator, AnomalyRecord


class RevenueConcentrationGenerator(AnomalyGenerator):
    """Injects a dominant revenue account representing >80% of total revenue.

    Replaces existing revenue balances with a heavily skewed distribution:
    one account at $900,000 and a second at $100,000, giving 90% concentration.
    """

    name = "revenue_concentration"
    report_targets = ["RPT-01", "RPT-21"]

    def inject(self, df: pd.DataFrame, seed: int = 42) -> tuple[pd.DataFrame, list[AnomalyRecord]]:
        df = df.copy()

        # Remove existing revenue accounts to control concentration
        revenue_mask = df["Account Type"].str.lower() == "revenue"
        removed_credit = df.loc[revenue_mask, "Credit"].sum()
        df = df[~revenue_mask].reset_index(drop=True)

        # Inject heavily skewed revenue
        dominant_amount = 900_000.00
        minor_amount = 100_000.00
        total_new = dominant_amount + minor_amount

        new_rows = pd.DataFrame(
            [
                {
                    "Account": "4000",
                    "Account Name": "Sales Revenue - Primary",
                    "Account Type": "Revenue",
                    "Debit": 0.00,
                    "Credit": dominant_amount,
                },
                {
                    "Account": "4100",
                    "Account Name": "Service Revenue - Secondary",
                    "Account Type": "Revenue",
                    "Debit": 0.00,
                    "Credit": minor_amount,
                },
            ]
        )

        # Adjust an expense account to rebalance TB if needed
        delta = total_new - removed_credit
        if abs(delta) > 0.01:
            expense_mask = df["Account Type"].str.lower() == "expense"
            if expense_mask.any():
                idx = df.index[expense_mask][0]
                df.loc[idx, "Debit"] = df.loc[idx, "Debit"] + delta

        df = pd.concat([df, new_rows], ignore_index=True)

        record = AnomalyRecord(
            anomaly_type="revenue_concentration",
            report_targets=self.report_targets,
            injected_at="Injected 90% revenue concentration in 'Sales Revenue - Primary'",
            expected_field="abnormal_balances",
            expected_condition="any_match anomaly_type=revenue_concentration",
            metadata={
                "dominant_account": "Sales Revenue - Primary",
                "concentration_pct": 90.0,
                "amount": dominant_amount,
            },
        )

        return df, [record]
