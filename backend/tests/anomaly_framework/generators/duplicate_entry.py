"""Duplicate Entry Anomaly Generator.

Injects duplicate rows into the trial balance to simulate double-posted
transactions. Duplicate entries cause the trial balance to become unbalanced
(total debits != total credits) because the duplicated amounts are counted
twice. The engine detects this via the 'balanced' field becoming False.
"""

import pandas as pd

from tests.anomaly_framework.base import AnomalyGenerator, AnomalyRecord


class DuplicateEntryGenerator(AnomalyGenerator):
    """Injects duplicate rows by copying an existing account entry.

    Duplicating a row with a non-zero debit or credit will unbalance the TB,
    which the engine reports via balanced=False and potential balance_sheet_imbalance
    anomalies.
    """

    name = "duplicate_entry"
    report_targets = ["RPT-01", "RPT-03", "RPT-21"]

    def __init__(self, num_duplicates: int = 3):
        self.num_duplicates = num_duplicates

    def inject(self, df: pd.DataFrame, seed: int = 42) -> tuple[pd.DataFrame, list[AnomalyRecord]]:
        df = df.copy()
        rng = __import__("random").Random(seed)

        # Pick a row with a non-zero balance to duplicate
        non_zero_mask = (df["Debit"] > 0) | (df["Credit"] > 0)
        candidates = df.index[non_zero_mask].tolist()
        target_idx = rng.choice(candidates)
        target_row = df.iloc[target_idx]
        target_name = target_row["Account Name"]

        # Append duplicates
        duplicates = pd.DataFrame([target_row.to_dict()] * self.num_duplicates)
        df = pd.concat([df, duplicates], ignore_index=True)

        record = AnomalyRecord(
            anomaly_type="duplicate_entry",
            report_targets=self.report_targets,
            injected_at=f"Duplicated '{target_name}' x{self.num_duplicates}",
            expected_field="balanced",
            expected_condition="value == False",
            metadata={
                "target_account": target_name,
                "num_duplicates": self.num_duplicates,
                "target_debit": float(target_row["Debit"]),
                "target_credit": float(target_row["Credit"]),
            },
        )

        return df, [record]
