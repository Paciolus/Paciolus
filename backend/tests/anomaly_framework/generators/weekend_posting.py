"""Weekend Posting Anomaly Generator.

Simulates the residual effect of weekend corrections in a trial balance.
In practice, weekend postings often manifest as intercompany clearing entries
or manual adjustments that bypass normal controls. Since trial balances lack
date fields, this generator injects a pair of intercompany accounts with a
deliberate imbalance, simulating a weekend reconciliation error.

The engine detects intercompany imbalances via detect_intercompany_imbalances()
when it finds intercompany-related account names with offsetting but mismatched
balances.
"""

import pandas as pd

from tests.anomaly_framework.base import AnomalyGenerator, AnomalyRecord


class WeekendPostingGenerator(AnomalyGenerator):
    """Injects mismatched intercompany entries simulating weekend reconciliation errors.

    Adds an 'Intercompany Receivable' asset and 'Intercompany Payable' liability
    with a deliberate balance mismatch to trigger intercompany_imbalance detection.
    """

    name = "weekend_posting"
    report_targets = ["RPT-01", "RPT-03", "RPT-21"]

    def inject(self, df: pd.DataFrame, seed: int = 42) -> tuple[pd.DataFrame, list[AnomalyRecord]]:
        df = df.copy()

        # Inject intercompany pair with deliberate mismatch
        ic_receivable_amount = 75_432.00
        ic_payable_amount = 72_918.00  # Mismatch of $2,514

        new_rows = pd.DataFrame(
            [
                {
                    "Account": "1600",
                    "Account Name": "Intercompany Receivable - Subsidiary",
                    "Account Type": "Asset",
                    "Debit": ic_receivable_amount,
                    "Credit": 0.00,
                },
                {
                    "Account": "2600",
                    "Account Name": "Intercompany Payable - Subsidiary",
                    "Account Type": "Liability",
                    "Debit": 0.00,
                    "Credit": ic_payable_amount,
                },
            ]
        )

        # Adjust Cash to keep TB balanced despite the intercompany mismatch
        mismatch = ic_receivable_amount - ic_payable_amount
        cash_mask = df["Account Name"].str.contains("Cash - Operating", case=False)
        cash_idx = df.index[cash_mask][0]
        df.loc[cash_idx, "Debit"] = df.loc[cash_idx, "Debit"] - mismatch

        df = pd.concat([df, new_rows], ignore_index=True)

        record = AnomalyRecord(
            anomaly_type="weekend_posting",
            report_targets=self.report_targets,
            injected_at="Intercompany pair with $2,514 mismatch",
            expected_field="abnormal_balances",
            expected_condition="any_match anomaly_type=intercompany_imbalance",
            metadata={
                "ic_receivable": ic_receivable_amount,
                "ic_payable": ic_payable_amount,
                "mismatch": round(mismatch, 2),
            },
        )

        return df, [record]
