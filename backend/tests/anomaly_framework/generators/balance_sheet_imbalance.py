"""Balance Sheet Imbalance Anomaly Generator.

Injects a material difference between total debits and total credits by
adding an unbalanced entry. The TB risk summary should report balanced=False.
"""

import pandas as pd

from tests.anomaly_framework.base import AnomalyGenerator, AnomalyRecord


class BalanceSheetImbalanceGenerator(AnomalyGenerator):
    """Injects a material TB imbalance ($10,000 excess debit).

    Adds a $10,000 debit to a new asset account without a corresponding
    credit, causing total_debits != total_credits.
    """

    name = "balance_sheet_imbalance"
    report_targets = ["RPT-01"]

    def inject(self, df: pd.DataFrame, seed: int = 42) -> tuple[pd.DataFrame, list[AnomalyRecord]]:
        df = df.copy()

        imbalance_amount = 10_000.00

        new_row = pd.DataFrame(
            [
                {
                    "Account": "1999",
                    "Account Name": "Miscellaneous Asset - Unreconciled",
                    "Account Type": "Asset",
                    "Debit": imbalance_amount,
                    "Credit": 0.00,
                }
            ]
        )

        df = pd.concat([df, new_row], ignore_index=True)

        record = AnomalyRecord(
            anomaly_type="balance_sheet_imbalance",
            report_targets=self.report_targets,
            injected_at=f"Added ${imbalance_amount:,.2f} unbalanced debit to 'Miscellaneous Asset - Unreconciled'",
            expected_field="balanced",
            expected_condition="value == False",
            metadata={
                "imbalance_amount": imbalance_amount,
                "direction": "excess_debit",
            },
        )

        return df, [record]
