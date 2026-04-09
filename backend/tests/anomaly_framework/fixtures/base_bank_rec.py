"""Base bank reconciliation factory for anomaly testing.

Produces a valid, fully reconciled bank statement and general ledger dataset
using Meridian Capital Group naming conventions. All 12 bank transactions
have matching GL entries, yielding 100% reconciliation with zero exceptions.

Key design decisions:
- All amounts match exactly between bank and GL (no rounding differences)
- All dates are weekday business days (June 2025)
- Sequential check numbers and transaction IDs
- Descriptions are similar enough for fuzzy matching but not identical
- No duplicate transactions
- Bank uses single Amount column; GL uses separate Debit/Credit
"""

# fmt: off
_BANK_ROWS: list[dict] = [
    {"Date": "2025-06-02", "Amount": -3456.00,   "Description": "ACH Payment - Office Lease June",        "Check Number": "",       "Transaction ID": "TXN-20250602-001"},
    {"Date": "2025-06-03", "Amount":  15743.50,   "Description": "Wire Deposit - Client Payment Inv 1042", "Check Number": "",       "Transaction ID": "TXN-20250603-001"},
    {"Date": "2025-06-04", "Amount": -8234.75,    "Description": "ACH Payroll Run 2025-06-04",             "Check Number": "",       "Transaction ID": "TXN-20250604-001"},
    {"Date": "2025-06-05", "Amount": -6891.25,    "Description": "Check - PO-2251 Materials Receipt",      "Check Number": "10451",  "Transaction ID": "TXN-20250605-001"},
    {"Date": "2025-06-06", "Amount": -1287.43,    "Description": "ACH Payment - Electric Utility",         "Check Number": "",       "Transaction ID": "TXN-20250606-001"},
    {"Date": "2025-06-09", "Amount":  22175.00,   "Description": "Wire Deposit - Consulting Q2 Inv 1043",  "Check Number": "",       "Transaction ID": "TXN-20250609-001"},
    {"Date": "2025-06-10", "Amount": -1897.50,    "Description": "ACH Payment - Insurance Premium",        "Check Number": "",       "Transaction ID": "TXN-20250610-001"},
    {"Date": "2025-06-11", "Amount": -3823.80,    "Description": "ACH Payment - Direct Labor Allocation",  "Check Number": "",       "Transaction ID": "TXN-20250611-001"},
    {"Date": "2025-06-12", "Amount":  -342.15,    "Description": "Debit Card - Staples Office Supplies",   "Check Number": "",       "Transaction ID": "TXN-20250612-001"},
    {"Date": "2025-06-13", "Amount": -5750.00,    "Description": "Check - Baker & Associates Legal",       "Check Number": "10452",  "Transaction ID": "TXN-20250613-001"},
    {"Date": "2025-06-16", "Amount": -2845.00,    "Description": "ACH Payment - LinkedIn Ads Campaign",    "Check Number": "",       "Transaction ID": "TXN-20250616-001"},
    {"Date": "2025-06-17", "Amount":  8375.25,    "Description": "Wire Deposit - Customer Pmt Inv 1038",   "Check Number": "",       "Transaction ID": "TXN-20250617-001"},
]

_GL_ROWS: list[dict] = [
    {"Entry Date": "2025-06-02", "Account": "1000", "Description": "June office lease payment",                    "Debit": 0.00,     "Credit": 3456.00},
    {"Entry Date": "2025-06-03", "Account": "1000", "Description": "Invoice 1042 - Professional services deposit", "Debit": 15743.50, "Credit": 0.00},
    {"Entry Date": "2025-06-04", "Account": "1000", "Description": "Bi-weekly payroll run 2025-06-04",             "Debit": 0.00,     "Credit": 8234.75},
    {"Entry Date": "2025-06-05", "Account": "1000", "Description": "PO-2251 raw materials payment CHK 10451",      "Debit": 0.00,     "Credit": 6891.25},
    {"Entry Date": "2025-06-06", "Account": "1000", "Description": "Electric bill June 2025",                      "Debit": 0.00,     "Credit": 1287.43},
    {"Entry Date": "2025-06-09", "Account": "1000", "Description": "Invoice 1043 - Consulting engagement Q2",      "Debit": 22175.00, "Credit": 0.00},
    {"Entry Date": "2025-06-10", "Account": "1000", "Description": "Monthly GL&P insurance premium",               "Debit": 0.00,     "Credit": 1897.50},
    {"Entry Date": "2025-06-11", "Account": "1000", "Description": "Direct labor allocation - Project Alpha",      "Debit": 0.00,     "Credit": 3823.80},
    {"Entry Date": "2025-06-12", "Account": "1000", "Description": "Staples order - printer paper and toner",      "Debit": 0.00,     "Credit": 342.15},
    {"Entry Date": "2025-06-13", "Account": "1000", "Description": "Legal counsel retainer - Baker & Associates",  "Debit": 0.00,     "Credit": 5750.00},
    {"Entry Date": "2025-06-16", "Account": "1000", "Description": "Digital campaign spend - LinkedIn ads",        "Debit": 0.00,     "Credit": 2845.00},
    {"Entry Date": "2025-06-17", "Account": "1000", "Description": "Customer payment - Invoice 1038",              "Debit": 8375.25,  "Credit": 0.00},
]
# fmt: on


def _verify_reconciliation(bank_rows: list[dict], gl_rows: list[dict]) -> None:
    """Raise if bank net != GL net."""
    bank_net = sum(r["Amount"] for r in bank_rows)
    gl_net = sum(r["Debit"] - r["Credit"] for r in gl_rows)
    assert abs(bank_net - gl_net) < 0.01, f"Bank/GL mismatch: bank_net={bank_net}, gl_net={gl_net}"


# Validate at import time
_verify_reconciliation(_BANK_ROWS, _GL_ROWS)


class BaseBankRecFactory:
    """Factory for clean, fully reconciled bank statement and GL data."""

    @classmethod
    def as_bank_rows(cls) -> list[dict]:
        """Return bank statement rows as list of dicts."""
        return [dict(r) for r in _BANK_ROWS]

    @classmethod
    def bank_column_names(cls) -> list[str]:
        """Return column names for bank statement data."""
        return list(_BANK_ROWS[0].keys())

    @classmethod
    def as_gl_rows(cls) -> list[dict]:
        """Return general ledger rows as list of dicts."""
        return [dict(r) for r in _GL_ROWS]

    @classmethod
    def gl_column_names(cls) -> list[str]:
        """Return column names for general ledger data."""
        return list(_GL_ROWS[0].keys())
