"""Round Number Anomaly Generator.

Injects a suspiciously round amount into an expense account. Round amounts
(divisible by 10,000 or higher) in non-suppressed account types trigger the
engine's rounding anomaly detection (classification_rules.ROUNDING_PATTERNS).

The generator modifies an expense account to have a round balance and adjusts
the Cash account to keep the trial balance balanced.
"""

import pandas as pd

from tests.anomaly_framework.base import AnomalyGenerator, AnomalyRecord


class RoundNumberGenerator(AnomalyGenerator):
    """Injects a round-number amount into an expense account.

    The injected amount is rounded to the nearest 10,000 (minimum 10,000)
    to ensure it exceeds the ROUNDING_MIN_AMOUNT threshold and is divisible
    by at least one ROUNDING_PATTERNS divisor.
    """

    name = "round_number"
    report_targets = ["RPT-01", "RPT-21"]

    def __init__(self, amount_scale: float = 100_000.0):
        self.amount_scale = amount_scale

    def inject(self, df: pd.DataFrame, seed: int = 42) -> tuple[pd.DataFrame, list[AnomalyRecord]]:
        df = df.copy()
        rng = __import__("random").Random(seed)

        # Compute the round amount — at least 10,000 and divisible by 10,000
        round_amount = max(10_000.0, round(self.amount_scale / 10_000) * 10_000.0)

        # Pick an expense account to mutate (avoid Cost of Services / Salaries
        # which might hit COGS subtype logic — use a clear operating expense)
        expense_mask = (df["Account Type"] == "Expense") & (
            ~df["Account Name"].str.contains("Cost of|Salaries", case=False)
        )
        expense_indices = df.index[expense_mask].tolist()
        if not expense_indices:
            expense_indices = df.index[df["Account Type"] == "Expense"].tolist()

        target_idx = rng.choice(expense_indices)
        target_name = df.loc[target_idx, "Account Name"]
        old_amount = df.loc[target_idx, "Debit"]

        # Set the round amount
        df.loc[target_idx, "Debit"] = round_amount

        # Rebalance via Cash - Operating
        cash_mask = df["Account Name"].str.contains("Cash - Operating", case=False)
        cash_idx = df.index[cash_mask][0]
        adjustment = round_amount - old_amount
        df.loc[cash_idx, "Debit"] = df.loc[cash_idx, "Debit"] - adjustment

        record = AnomalyRecord(
            anomaly_type="round_number",
            report_targets=self.report_targets,
            injected_at=f"Account '{target_name}' set to ${round_amount:,.0f}",
            expected_field="abnormal_balances",
            expected_condition="any_match anomaly_type=rounding_anomaly",
            metadata={
                "target_account": target_name,
                "round_amount": round_amount,
                "original_amount": old_amount,
            },
        )

        return df, [record]
