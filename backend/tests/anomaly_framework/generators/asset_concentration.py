"""Asset Concentration Anomaly Generator.

Injects a trial balance where a single asset account represents >80% of
total assets. The engine's detect_concentration_risk() should flag this as
asset_concentration with HIGH severity (>= 50% threshold).
"""

import pandas as pd

from tests.anomaly_framework.base import AnomalyGenerator, AnomalyRecord


class AssetConcentrationGenerator(AnomalyGenerator):
    """Injects a dominant asset account representing >80% of total assets.

    Replaces all existing asset balances with a heavily skewed distribution:
    one account at $850,000 and a second at $150,000, giving 85% concentration.
    Rebalances via an equity account to maintain TB balance.
    """

    name = "asset_concentration"
    report_targets = ["RPT-01", "RPT-21"]

    def inject(self, df: pd.DataFrame, seed: int = 42) -> tuple[pd.DataFrame, list[AnomalyRecord]]:
        df = df.copy()

        # Remove existing asset accounts to control concentration
        asset_mask = df["Account Type"].str.lower() == "asset"
        # Net of removed assets: sum(debit) - sum(credit) for asset rows
        removed_net = df.loc[asset_mask, "Debit"].sum() - df.loc[asset_mask, "Credit"].sum()
        df = df[~asset_mask].reset_index(drop=True)

        # Inject heavily skewed assets
        dominant_amount = 850_000.00
        minor_amount = 150_000.00
        new_net = dominant_amount + minor_amount  # both are debit-side

        new_rows = pd.DataFrame(
            [
                {
                    "Account": "1000",
                    "Account Name": "Cash - Operating",
                    "Account Type": "Asset",
                    "Debit": dominant_amount,
                    "Credit": 0.00,
                },
                {
                    "Account": "1100",
                    "Account Name": "Accounts Receivable - Trade",
                    "Account Type": "Asset",
                    "Debit": minor_amount,
                    "Credit": 0.00,
                },
            ]
        )

        # Rebalance via equity if asset total changed
        delta = new_net - removed_net
        if abs(delta) > 0.01:
            equity_mask = df["Account Type"].str.lower() == "equity"
            if equity_mask.any():
                idx = df.index[equity_mask][0]
                df.loc[idx, "Credit"] = df.loc[idx, "Credit"] + delta

        df = pd.concat([df, new_rows], ignore_index=True)

        record = AnomalyRecord(
            anomaly_type="asset_concentration",
            report_targets=self.report_targets,
            injected_at="Injected 85% asset concentration in 'Cash - Operating'",
            expected_field="abnormal_balances",
            expected_condition="any_match anomaly_type=asset_concentration",
            metadata={
                "dominant_account": "Cash - Operating",
                "concentration_pct": 85.0,
                "amount": dominant_amount,
            },
        )

        return df, [record]
