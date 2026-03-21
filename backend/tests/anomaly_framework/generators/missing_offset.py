"""Missing Offset Anomaly Generator.

Injects an unmatched debit entry without a corresponding credit, causing
the trial balance to become unbalanced. The engine detects this via the
'balanced' field becoming False in the audit result.
"""

import pandas as pd

from tests.anomaly_framework.base import AnomalyGenerator, AnomalyRecord


class MissingOffsetGenerator(AnomalyGenerator):
    """Adds a debit entry with no corresponding credit offset.

    Inserts a new expense account with a debit balance but no matching credit,
    which directly causes total debits > total credits and the engine reports
    balanced=False.
    """

    name = "missing_offset"
    report_targets = ["RPT-01", "RPT-21"]

    def inject(self, df: pd.DataFrame, seed: int = 42) -> tuple[pd.DataFrame, list[AnomalyRecord]]:
        df = df.copy()

        orphan_amount = 25_678.50

        new_row = pd.DataFrame(
            [
                {
                    "Account": "6800",
                    "Account Name": "Miscellaneous Expense - Unreconciled",
                    "Account Type": "Expense",
                    "Debit": orphan_amount,
                    "Credit": 0.00,
                }
            ]
        )

        # Deliberately do NOT adjust any other account — this creates imbalance
        df = pd.concat([df, new_row], ignore_index=True)

        record = AnomalyRecord(
            anomaly_type="missing_offset",
            report_targets=self.report_targets,
            injected_at=f"Added orphan debit of ${orphan_amount:,.2f} with no offset",
            expected_field="balanced",
            expected_condition="value == False",
            metadata={
                "orphan_account": "Miscellaneous Expense - Unreconciled",
                "orphan_amount": orphan_amount,
            },
        )

        return df, [record]
