"""Equity Signal Anomaly Generator.

Injects a retained earnings deficit plus a dividends declared account to
trigger the engine's equity signal detection (audit/rules/equity.py).
The pattern indicates potential governance/solvency concern: declaring
dividends while operating at a deficit.
"""

import pandas as pd

from tests.anomaly_framework.base import AnomalyGenerator, AnomalyRecord


class EquitySignalGenerator(AnomalyGenerator):
    """Injects retained earnings deficit + dividends declared.

    Flips the Retained Earnings account to a debit (deficit) balance and
    adds a Dividends Declared equity account. An Additional Paid-in Capital
    credit absorbs the rebalancing swing to maintain TB balance.
    """

    name = "equity_signal"
    report_targets = ["RPT-01", "RPT-21"]

    def __init__(self, deficit_amount: float = 35_000.0, dividend_amount: float = 12_431.0):
        self.deficit_amount = deficit_amount
        self.dividend_amount = dividend_amount

    def inject(self, df: pd.DataFrame, seed: int = 42) -> tuple[pd.DataFrame, list[AnomalyRecord]]:
        df = df.copy()

        # Find Retained Earnings and flip to deficit (debit balance)
        re_mask = df["Account Name"].str.contains("Retained Earnings", case=False)
        re_idx = df.index[re_mask][0]
        original_re_credit = df.loc[re_idx, "Credit"]

        df.loc[re_idx, "Debit"] = self.deficit_amount
        df.loc[re_idx, "Credit"] = 0.00

        # Add Dividends Declared (equity, debit = contra-equity)
        dividends_row = pd.DataFrame(
            [
                {
                    "Account": "3200",
                    "Account Name": "Dividends Declared",
                    "Account Type": "Equity",
                    "Debit": self.dividend_amount,
                    "Credit": 0.00,
                }
            ]
        )

        # Rebalance: original RE was credit, now it's debit; plus dividends debit.
        # Need to add credits to compensate.
        apic_amount = original_re_credit + self.deficit_amount + self.dividend_amount
        apic_row = pd.DataFrame(
            [
                {
                    "Account": "3050",
                    "Account Name": "Additional Paid-in Capital",
                    "Account Type": "Equity",
                    "Debit": 0.00,
                    "Credit": apic_amount,
                }
            ]
        )

        df = pd.concat([df, dividends_row, apic_row], ignore_index=True)

        record = AnomalyRecord(
            anomaly_type="equity_signal",
            report_targets=self.report_targets,
            injected_at=(
                f"Retained Earnings flipped to deficit (${self.deficit_amount:,.0f}), "
                f"Dividends Declared added (${self.dividend_amount:,.0f})"
            ),
            expected_field="abnormal_balances",
            expected_condition="any_match is_equity_signal=True",
            metadata={
                "deficit_amount": self.deficit_amount,
                "dividend_amount": self.dividend_amount,
                "apic_amount": apic_amount,
            },
        )

        return df, [record]
