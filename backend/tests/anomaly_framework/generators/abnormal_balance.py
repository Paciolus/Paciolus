"""Abnormal Balance Anomaly Generator.

Injects a natural balance violation by giving a Revenue account a debit
(wrong-side) balance. Revenue accounts normally carry credit balances;
a net debit balance triggers the engine's get_abnormal_balances() detection
for natural_balance_violation anomaly type.
"""

import pandas as pd

from tests.anomaly_framework.base import AnomalyGenerator, AnomalyRecord


class AbnormalBalanceGenerator(AnomalyGenerator):
    """Flips a Revenue account to carry an abnormal debit balance.

    Selects a revenue account and moves its balance to the debit side,
    which violates the normal credit balance for revenue accounts. The
    engine flags this as a natural_balance_violation.
    """

    name = "abnormal_balance"
    report_targets = ["RPT-01", "RPT-21"]

    def inject(self, df: pd.DataFrame, seed: int = 42) -> tuple[pd.DataFrame, list[AnomalyRecord]]:
        df = df.copy()
        rng = __import__("random").Random(seed)

        # Find revenue accounts
        revenue_mask = df["Account Type"] == "Revenue"
        revenue_indices = df.index[revenue_mask].tolist()
        target_idx = rng.choice(revenue_indices)

        target_name = df.loc[target_idx, "Account Name"]
        original_credit = df.loc[target_idx, "Credit"]

        # Flip: move credit to debit (revenue now has wrong-side balance)
        abnormal_debit = original_credit
        df.loc[target_idx, "Debit"] = abnormal_debit
        df.loc[target_idx, "Credit"] = 0.00

        # Rebalance: increase Cash credit by the full swing (2x original credit)
        # because we removed a credit and added a debit of the same amount
        cash_mask = df["Account Name"].str.contains("Cash - Operating", case=False)
        cash_idx = df.index[cash_mask][0]
        swing = 2 * original_credit  # debit went up by original, credit went down by original
        df.loc[cash_idx, "Debit"] = df.loc[cash_idx, "Debit"] + swing

        record = AnomalyRecord(
            anomaly_type="abnormal_balance",
            report_targets=self.report_targets,
            injected_at=f"Flipped '{target_name}' to debit ${abnormal_debit:,.2f}",
            expected_field="abnormal_balances",
            expected_condition="any_match anomaly_type=natural_balance_violation",
            metadata={
                "target_account": target_name,
                "abnormal_debit": abnormal_debit,
                "original_credit": original_credit,
            },
        )

        return df, [record]
