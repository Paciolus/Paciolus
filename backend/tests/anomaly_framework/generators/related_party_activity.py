"""Related Party Activity Anomaly Generator.

Injects two accounts with offsetting balances and names containing known
related-party keywords. The engine's detect_related_party_accounts() method
should flag these based on RELATED_PARTY_KEYWORDS in classification_rules.py.
"""

import pandas as pd

from tests.anomaly_framework.base import AnomalyGenerator, AnomalyRecord


class RelatedPartyActivityGenerator(AnomalyGenerator):
    """Injects intercompany/related-party accounts with offsetting balances.

    Adds 'Intercompany Receivable - Affiliate' (debit) and
    'Due To Affiliate' (credit) with matching balances.
    Both names contain keywords from RELATED_PARTY_KEYWORDS.
    """

    name = "related_party_activity"
    report_targets = ["RPT-01", "RPT-21"]

    def inject(self, df: pd.DataFrame, seed: int = 42) -> tuple[pd.DataFrame, list[AnomalyRecord]]:
        df = df.copy()

        amount = 250_000.00

        new_rows = pd.DataFrame(
            [
                {
                    "Account": "1850",
                    "Account Name": "Intercompany Receivable - Affiliate",
                    "Account Type": "Asset",
                    "Debit": amount,
                    "Credit": 0.00,
                },
                {
                    "Account": "2850",
                    "Account Name": "Due To Affiliate",
                    "Account Type": "Liability",
                    "Debit": 0.00,
                    "Credit": amount,
                },
            ]
        )

        df = pd.concat([df, new_rows], ignore_index=True)

        records = [
            AnomalyRecord(
                anomaly_type="related_party_activity",
                report_targets=self.report_targets,
                injected_at="Added 'Intercompany Receivable - Affiliate' and 'Due To Affiliate'",
                expected_field="abnormal_balances",
                expected_condition="any_match anomaly_type=related_party",
                metadata={
                    "accounts": [
                        "Intercompany Receivable - Affiliate",
                        "Due To Affiliate",
                    ],
                    "amount": amount,
                },
            ),
        ]

        return df, records
