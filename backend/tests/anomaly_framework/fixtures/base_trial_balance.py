"""Base trial balance factory for anomaly testing.

Produces a valid, balanced trial balance with 26 accounts covering all five
account types. Uses Meridian Capital Group naming conventions. Designed to
trigger zero anomalies in the audit engine so that any detected anomaly can
be attributed to the injected mutation.

Key design decisions:
- No amounts divisible by 10,000 (avoids rounding detection) except where
  covered by Tier 1 suppress (Common Stock at 50,000).
- No single revenue account exceeds 30% of total revenue.
- No single asset exceeds 50% of asset category.
- No single expense exceeds 40% of total expenses.
- No suspense/clearing keywords in account names.
- All accounts carry their normal-side balance.
"""

import io

import pandas as pd

# fmt: off
_ACCOUNTS: list[dict] = [
    # ── Assets (Debit normal) ──────────────────────────────────────────
    {"Account": "1000", "Account Name": "Cash - Operating",               "Account Type": "Asset",     "Debit": 167023.00, "Credit": 0.00},
    {"Account": "1050", "Account Name": "Cash - Payroll",                 "Account Type": "Asset",     "Debit":  23415.00, "Credit": 0.00},
    {"Account": "1100", "Account Name": "Accounts Receivable - Trade",    "Account Type": "Asset",     "Debit":  84623.00, "Credit": 0.00},
    {"Account": "1200", "Account Name": "Prepaid Insurance",              "Account Type": "Asset",     "Debit":  11875.25, "Credit": 0.00},
    {"Account": "1300", "Account Name": "Inventory - Raw Materials",      "Account Type": "Asset",     "Debit":  44891.00, "Credit": 0.00},
    {"Account": "1500", "Account Name": "Property & Equipment",           "Account Type": "Asset",     "Debit": 187500.00, "Credit": 0.00},
    {"Account": "1510", "Account Name": "Accumulated Depreciation",       "Account Type": "Asset",     "Debit":      0.00, "Credit": 62312.50},
    # ── Liabilities (Credit normal) ────────────────────────────────────
    {"Account": "2000", "Account Name": "Accounts Payable - Trade",       "Account Type": "Liability", "Debit": 0.00, "Credit":  41678.00},
    {"Account": "2100", "Account Name": "Accrued Salaries",               "Account Type": "Liability", "Debit": 0.00, "Credit":  27945.25},
    {"Account": "2200", "Account Name": "Current Portion - Term Loan",    "Account Type": "Liability", "Debit": 0.00, "Credit":  24500.00},
    {"Account": "2500", "Account Name": "Term Loan Payable",              "Account Type": "Liability", "Debit": 0.00, "Credit": 118750.00},
    # ── Equity (Credit normal) ─────────────────────────────────────────
    {"Account": "3000", "Account Name": "Common Stock",                   "Account Type": "Equity",    "Debit": 0.00, "Credit":  50000.00},
    {"Account": "3100", "Account Name": "Retained Earnings",              "Account Type": "Equity",    "Debit": 0.00, "Credit": 145387.50},
    # ── Revenue (Credit normal) ────────────────────────────────────────
    {"Account": "4000", "Account Name": "Service Revenue",                "Account Type": "Revenue",   "Debit": 0.00, "Credit": 112456.00},
    {"Account": "4100", "Account Name": "Consulting Revenue",             "Account Type": "Revenue",   "Debit": 0.00, "Credit": 108782.00},
    {"Account": "4200", "Account Name": "License Fee Revenue",            "Account Type": "Revenue",   "Debit": 0.00, "Credit":  97654.00},
    {"Account": "4300", "Account Name": "Product Revenue",                "Account Type": "Revenue",   "Debit": 0.00, "Credit":  84321.00},
    # ── Expenses (Debit normal) ────────────────────────────────────────
    {"Account": "5000", "Account Name": "Cost of Services",               "Account Type": "Expense",   "Debit": 132456.00, "Credit": 0.00},
    {"Account": "6000", "Account Name": "Salaries & Wages",               "Account Type": "Expense",   "Debit":  98750.00, "Credit": 0.00},
    {"Account": "6100", "Account Name": "Rent Expense",                   "Account Type": "Expense",   "Debit":  36123.00, "Credit": 0.00},
    {"Account": "6200", "Account Name": "Utilities Expense",              "Account Type": "Expense",   "Debit":   8467.00, "Credit": 0.00},
    {"Account": "6300", "Account Name": "Depreciation Expense",           "Account Type": "Expense",   "Debit":  24812.50, "Credit": 0.00},
    {"Account": "6400", "Account Name": "Insurance Expense",              "Account Type": "Expense",   "Debit":  15234.00, "Credit": 0.00},
    {"Account": "6500", "Account Name": "Office Supplies",                "Account Type": "Expense",   "Debit":   8976.00, "Credit": 0.00},
    {"Account": "6600", "Account Name": "Professional Fees",              "Account Type": "Expense",   "Debit":  11245.00, "Credit": 0.00},
    {"Account": "6700", "Account Name": "Marketing & Advertising",        "Account Type": "Expense",   "Debit":  18395.50, "Credit": 0.00},
]
# fmt: on


def _verify_balance(accounts: list[dict]) -> None:
    """Raise if total debits != total credits."""
    total_debits = sum(a["Debit"] for a in accounts)
    total_credits = sum(a["Credit"] for a in accounts)
    assert abs(total_debits - total_credits) < 0.01, (
        f"Base TB is unbalanced: debits={total_debits}, credits={total_credits}"
    )


# Validate at import time
_verify_balance(_ACCOUNTS)


class BaseTrialBalanceFactory:
    """Factory for a clean, anomaly-free trial balance."""

    @classmethod
    def as_dataframe(cls) -> pd.DataFrame:
        """Return the base trial balance as a pandas DataFrame."""
        return pd.DataFrame(_ACCOUNTS)

    @classmethod
    def as_csv_bytes(cls) -> bytes:
        """Return the base trial balance as CSV bytes suitable for audit_trial_balance_streaming."""
        df = cls.as_dataframe()
        buf = io.BytesIO()
        df.to_csv(buf, index=False)
        return buf.getvalue()
