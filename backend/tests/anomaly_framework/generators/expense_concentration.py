"""Expense Concentration Anomaly Generator.

Injects a trial balance where >80% of total expenses come from a single
expense account. The engine's detect_expense_concentration() should flag
this as a concentration risk.
"""

import pandas as pd

from tests.anomaly_framework.base import AnomalyGenerator, AnomalyRecord


class ExpenseConcentrationGenerator(AnomalyGenerator):
    """Injects a dominant expense account representing >80% of total expenses.

    Replaces existing expense balances with a heavily skewed distribution:
    one account at $800,000 and a second at $100,000, giving ~89% concentration.
    """

    name = "expense_concentration"
    report_targets = ["RPT-01", "RPT-21"]

    def inject(self, df: pd.DataFrame, seed: int = 42) -> tuple[pd.DataFrame, list[AnomalyRecord]]:
        df = df.copy()

        # Remove existing expense accounts to control concentration
        expense_mask = df["Account Type"].str.lower() == "expense"
        removed_debit = df.loc[expense_mask, "Debit"].sum()
        df = df[~expense_mask].reset_index(drop=True)

        # Inject heavily skewed expenses
        dominant_amount = 800_000.00
        minor_amount = 100_000.00
        total_new = dominant_amount + minor_amount

        new_rows = pd.DataFrame(
            [
                {
                    "Account": "6000",
                    "Account Name": "Salaries and Wages",
                    "Account Type": "Expense",
                    "Debit": dominant_amount,
                    "Credit": 0.00,
                },
                {
                    "Account": "6500",
                    "Account Name": "Office Supplies Expense",
                    "Account Type": "Expense",
                    "Debit": minor_amount,
                    "Credit": 0.00,
                },
            ]
        )

        # Adjust a revenue account to rebalance TB if needed
        delta = total_new - removed_debit
        if abs(delta) > 0.01:
            revenue_mask = df["Account Type"].str.lower() == "revenue"
            if revenue_mask.any():
                idx = df.index[revenue_mask][0]
                df.loc[idx, "Credit"] = df.loc[idx, "Credit"] + delta

        df = pd.concat([df, new_rows], ignore_index=True)

        record = AnomalyRecord(
            anomaly_type="expense_concentration",
            report_targets=self.report_targets,
            injected_at="Injected ~89% expense concentration in 'Salaries and Wages'",
            expected_field="abnormal_balances",
            expected_condition="any_match anomaly_type=expense_concentration",
            metadata={
                "dominant_account": "Salaries and Wages",
                "concentration_pct": round(dominant_amount / total_new * 100, 1),
                "amount": dominant_amount,
            },
        )

        return df, [record]
