"""Suspense Account Anomaly Generator.

Injects a suspense or clearing account with an outstanding balance into the
trial balance. The engine's detect_suspense_accounts() method uses weighted
keyword matching against SUSPENSE_KEYWORDS to identify these accounts with
a confidence threshold of 0.60.
"""

import pandas as pd

from tests.anomaly_framework.base import AnomalyGenerator, AnomalyRecord


class SuspenseAccountGenerator(AnomalyGenerator):
    """Injects a suspense/clearing account with an outstanding balance.

    Adds an account named 'Clearing Account - Unallocated' which triggers
    multiple suspense keywords ('clearing account' weight=0.95, 'unallocated'
    weight=0.90) for a combined confidence well above the 0.60 threshold.
    """

    name = "suspense_account"
    report_targets = ["RPT-01", "RPT-21"]

    def inject(self, df: pd.DataFrame, seed: int = 42) -> tuple[pd.DataFrame, list[AnomalyRecord]]:
        df = df.copy()

        suspense_amount = 15_743.00

        new_row = pd.DataFrame(
            [
                {
                    "Account": "1900",
                    "Account Name": "Clearing Account - Unallocated",
                    "Account Type": "Asset",
                    "Debit": suspense_amount,
                    "Credit": 0.00,
                }
            ]
        )

        # Reduce Cash to keep TB balanced
        cash_mask = df["Account Name"].str.contains("Cash - Operating", case=False)
        cash_idx = df.index[cash_mask][0]
        df.loc[cash_idx, "Debit"] = df.loc[cash_idx, "Debit"] - suspense_amount

        df = pd.concat([df, new_row], ignore_index=True)

        record = AnomalyRecord(
            anomaly_type="suspense_account",
            report_targets=self.report_targets,
            injected_at="Added 'Clearing Account - Unallocated' with $15,743 balance",
            expected_field="abnormal_balances",
            expected_condition="any_match anomaly_type=suspense_account",
            metadata={
                "account_name": "Clearing Account - Unallocated",
                "amount": suspense_amount,
            },
        )

        return df, [record]
