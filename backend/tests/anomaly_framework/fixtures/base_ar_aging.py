"""Base AR Aging factory for anomaly testing.

Produces valid, clean trial balance rows and sub-ledger rows for AR Aging
testing. Uses Meridian Capital Group naming conventions. Designed to trigger
zero anomalies in the AR Aging engine so that any detected anomaly can be
attributed to the injected mutation.

Key design decisions — Trial Balance:
- Balanced TB with AR, Allowance, and Revenue accounts
- Allowance account present (avoids AR-02 missing allowance)
- All balances carry normal-side amounts

Key design decisions — Sub-Ledger:
- No negative amounts (avoids AR-01 sign anomalies, AR-03 negative aging)
- SL total matches TB AR balance (avoids AR-04 unreconciled detail)
- Spread across aging buckets (avoids AR-05 bucket concentration)
- Past-due ratio below 50% (avoids AR-06 past-due concentration)
- No customer > 40% of total (avoids AR-08 customer concentration)
- Multiple customers with realistic invoice data
"""

import io

import pandas as pd

# fmt: off
_TB_ACCOUNTS: list[dict] = [
    # AR account — balance must equal SL total (84,623.00)
    {"Account": "1100", "Account Name": "Accounts Receivable - Trade",    "Account Type": "Asset",     "Debit": 84623.00, "Credit": 0.00},
    # Allowance for doubtful accounts (contra-asset)
    {"Account": "1105", "Account Name": "Allowance for Doubtful Accounts","Account Type": "Asset",     "Debit": 0.00,     "Credit": 4231.15},
    # Revenue accounts
    {"Account": "4000", "Account Name": "Service Revenue",                "Account Type": "Revenue",   "Debit": 0.00,     "Credit": 112456.00},
    {"Account": "4100", "Account Name": "Consulting Revenue",             "Account Type": "Revenue",   "Debit": 0.00,     "Credit": 108782.00},
    # Expense accounts to balance
    {"Account": "6000", "Account Name": "Salaries & Wages",               "Account Type": "Expense",   "Debit": 98750.00, "Credit": 0.00},
    {"Account": "6100", "Account Name": "Rent Expense",                   "Account Type": "Expense",   "Debit": 42096.15, "Credit": 0.00},
]

_SL_RECORDS: list[dict] = [
    # Customer 1: Acme Corp — 4 invoices, ~30% of total
    {"Customer ID": "CUST-001", "Customer Name": "Acme Corporation",       "Invoice Number": "INV-2401", "Invoice Date": "2025-05-15", "Amount": 8750.00,  "Days Past Due": 0,   "Aging Bucket": "Current"},
    {"Customer ID": "CUST-001", "Customer Name": "Acme Corporation",       "Invoice Number": "INV-2318", "Invoice Date": "2025-04-20", "Amount": 6234.50,  "Days Past Due": 25,  "Aging Bucket": "Current"},
    {"Customer ID": "CUST-001", "Customer Name": "Acme Corporation",       "Invoice Number": "INV-2215", "Invoice Date": "2025-03-10", "Amount": 5430.00,  "Days Past Due": 66,  "Aging Bucket": "61-90"},
    {"Customer ID": "CUST-001", "Customer Name": "Acme Corporation",       "Invoice Number": "INV-2112", "Invoice Date": "2025-02-01", "Amount": 4250.50,  "Days Past Due": 45,  "Aging Bucket": "31-60"},
    # Customer 2: Pinnacle Solutions — 3 invoices, ~24% of total
    {"Customer ID": "CUST-002", "Customer Name": "Pinnacle Solutions LLC", "Invoice Number": "INV-2402", "Invoice Date": "2025-05-20", "Amount": 9125.00,  "Days Past Due": 0,   "Aging Bucket": "Current"},
    {"Customer ID": "CUST-002", "Customer Name": "Pinnacle Solutions LLC", "Invoice Number": "INV-2319", "Invoice Date": "2025-04-10", "Amount": 5832.00,  "Days Past Due": 35,  "Aging Bucket": "31-60"},
    {"Customer ID": "CUST-002", "Customer Name": "Pinnacle Solutions LLC", "Invoice Number": "INV-2216", "Invoice Date": "2025-03-25", "Amount": 5418.00,  "Days Past Due": 51,  "Aging Bucket": "31-60"},
    # Customer 3: Redwood Industries — 3 invoices, ~21% of total
    {"Customer ID": "CUST-003", "Customer Name": "Redwood Industries Inc", "Invoice Number": "INV-2403", "Invoice Date": "2025-05-28", "Amount": 7250.00,  "Days Past Due": 0,   "Aging Bucket": "Current"},
    {"Customer ID": "CUST-003", "Customer Name": "Redwood Industries Inc", "Invoice Number": "INV-2320", "Invoice Date": "2025-04-05", "Amount": 4891.00,  "Days Past Due": 40,  "Aging Bucket": "31-60"},
    {"Customer ID": "CUST-003", "Customer Name": "Redwood Industries Inc", "Invoice Number": "INV-2113", "Invoice Date": "2025-01-15", "Amount": 5642.00,  "Days Past Due": 120, "Aging Bucket": "91+"},
    # Customer 4: Clearview Partners — 2 invoices, ~14% of total
    {"Customer ID": "CUST-004", "Customer Name": "Clearview Partners",     "Invoice Number": "INV-2404", "Invoice Date": "2025-05-10", "Amount": 6345.00,  "Days Past Due": 0,   "Aging Bucket": "Current"},
    {"Customer ID": "CUST-004", "Customer Name": "Clearview Partners",     "Invoice Number": "INV-2321", "Invoice Date": "2025-04-15", "Amount": 5655.00,  "Days Past Due": 30,  "Aging Bucket": "Current"},
    # Customer 5: Horizon Tech — 2 invoices, ~11% of total
    {"Customer ID": "CUST-005", "Customer Name": "Horizon Tech Group",     "Invoice Number": "INV-2405", "Invoice Date": "2025-06-01", "Amount": 4950.00,  "Days Past Due": 0,   "Aging Bucket": "Current"},
    {"Customer ID": "CUST-005", "Customer Name": "Horizon Tech Group",     "Invoice Number": "INV-2322", "Invoice Date": "2025-03-15", "Amount": 4850.00,  "Days Past Due": 72,  "Aging Bucket": "61-90"},
]
# fmt: on


def _verify_tb_balanced(accounts: list[dict]) -> None:
    """Raise if total debits != total credits."""
    total_debits = sum(a["Debit"] for a in accounts)
    total_credits = sum(a["Credit"] for a in accounts)
    assert abs(total_debits - total_credits) < 0.01, (
        f"Base AR TB is unbalanced: debits={total_debits}, credits={total_credits}"
    )


def _verify_sl_matches_tb(accounts: list[dict], records: list[dict]) -> None:
    """Raise if sub-ledger total doesn't match TB AR balance."""
    ar_balance = sum(
        a["Debit"] - a["Credit"]
        for a in accounts
        if "Receivable" in a["Account Name"] and "Allowance" not in a["Account Name"]
    )
    sl_total = sum(r["Amount"] for r in records)
    assert abs(ar_balance - sl_total) < 0.01, f"SL total ({sl_total}) != TB AR balance ({ar_balance})"


def _verify_no_concentration(records: list[dict]) -> None:
    """Raise if any customer exceeds 40% of total."""
    sl_total = sum(r["Amount"] for r in records)
    from collections import defaultdict

    by_customer: dict[str, float] = defaultdict(float)
    for r in records:
        by_customer[r["Customer ID"]] += r["Amount"]
    for cid, amt in by_customer.items():
        pct = amt / sl_total
        assert pct <= 0.40, f"Customer {cid} has {pct:.1%} concentration (>40%)"


def _verify_no_negatives(records: list[dict]) -> None:
    """Raise if any SL amount is negative."""
    for r in records:
        assert r["Amount"] >= 0, f"Negative amount in {r['Invoice Number']}: {r['Amount']}"


# Validate at import time
_verify_tb_balanced(_TB_ACCOUNTS)
_verify_sl_matches_tb(_TB_ACCOUNTS, _SL_RECORDS)
_verify_no_concentration(_SL_RECORDS)
_verify_no_negatives(_SL_RECORDS)


class BaseARAgingFactory:
    """Factory for clean, flag-free AR Aging test data (TB + sub-ledger)."""

    @classmethod
    def as_tb_rows(cls) -> list[dict]:
        """Return the base TB accounts as a list of dicts."""
        return [dict(a) for a in _TB_ACCOUNTS]

    @classmethod
    def tb_column_names(cls) -> list[str]:
        """Return column names for the TB rows."""
        return list(_TB_ACCOUNTS[0].keys())

    @classmethod
    def as_sl_rows(cls) -> list[dict]:
        """Return the base sub-ledger records as a list of dicts."""
        return [dict(r) for r in _SL_RECORDS]

    @classmethod
    def sl_column_names(cls) -> list[str]:
        """Return column names for the sub-ledger rows."""
        return list(_SL_RECORDS[0].keys())

    @classmethod
    def as_tb_dataframe(cls) -> pd.DataFrame:
        """Return the base TB as a pandas DataFrame."""
        return pd.DataFrame(_TB_ACCOUNTS)

    @classmethod
    def as_sl_dataframe(cls) -> pd.DataFrame:
        """Return the base sub-ledger as a pandas DataFrame."""
        return pd.DataFrame(_SL_RECORDS)

    @classmethod
    def as_tb_csv_bytes(cls) -> bytes:
        """Return the base TB as CSV bytes."""
        df = cls.as_tb_dataframe()
        buf = io.BytesIO()
        df.to_csv(buf, index=False)
        return buf.getvalue()

    @classmethod
    def as_sl_csv_bytes(cls) -> bytes:
        """Return the base sub-ledger as CSV bytes."""
        df = cls.as_sl_dataframe()
        buf = io.BytesIO()
        df.to_csv(buf, index=False)
        return buf.getvalue()
