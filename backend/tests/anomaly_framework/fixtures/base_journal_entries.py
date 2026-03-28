"""Base journal entry factory for JE testing anomaly framework.

Produces a valid, clean set of 50 journal entries that trigger zero flags
in the JE testing engine. Uses Meridian Capital Group naming conventions.

Key design decisions:
- All entries are balanced (debit == credit per entry_id group)
- No round amounts >= $10,000
- No weekend or after-hours postings
- No duplicate entries
- No suspicious keywords in descriptions
- Reasonable Benford distribution (though below min_entries threshold)
- Sequential entry IDs with no gaps
- All dates are weekday business hours
- Variety of accounts, descriptions, users, and amounts
"""

import io

import pandas as pd

# fmt: off
_ENTRIES: list[dict] = [
    # Entry 1: Revenue recognition
    {"Entry ID": "JE-001", "Entry Date": "2025-06-02", "Account": "1100", "Account Name": "Accounts Receivable", "Description": "Invoice 1042 - Professional services rendered", "Debit": 15743.50, "Credit": 0.00, "Posted By": "jsmith", "Source": "AR"},
    {"Entry ID": "JE-001", "Entry Date": "2025-06-02", "Account": "4000", "Account Name": "Service Revenue",     "Description": "Invoice 1042 - Professional services rendered", "Debit": 0.00, "Credit": 15743.50, "Posted By": "jsmith", "Source": "AR"},
    # Entry 2: Rent payment
    {"Entry ID": "JE-002", "Entry Date": "2025-06-03", "Account": "6100", "Account Name": "Rent Expense",        "Description": "June office lease payment",                    "Debit": 3456.00, "Credit": 0.00, "Posted By": "mwilson", "Source": "AP"},
    {"Entry ID": "JE-002", "Entry Date": "2025-06-03", "Account": "1000", "Account Name": "Cash - Operating",    "Description": "June office lease payment",                    "Debit": 0.00, "Credit": 3456.00, "Posted By": "mwilson", "Source": "AP"},
    # Entry 3: Payroll
    {"Entry ID": "JE-003", "Entry Date": "2025-06-04", "Account": "6000", "Account Name": "Salaries & Wages",    "Description": "Bi-weekly payroll run 2025-06-04",             "Debit": 8234.75, "Credit": 0.00, "Posted By": "payroll_sys", "Source": "PR"},
    {"Entry ID": "JE-003", "Entry Date": "2025-06-04", "Account": "1050", "Account Name": "Cash - Payroll",      "Description": "Bi-weekly payroll run 2025-06-04",             "Debit": 0.00, "Credit": 8234.75, "Posted By": "payroll_sys", "Source": "PR"},
    # Entry 4: Inventory purchase
    {"Entry ID": "JE-004", "Entry Date": "2025-06-05", "Account": "1300", "Account Name": "Inventory",           "Description": "PO-2251 raw materials receipt",                "Debit": 6891.25, "Credit": 0.00, "Posted By": "klee", "Source": "PO"},
    {"Entry ID": "JE-004", "Entry Date": "2025-06-05", "Account": "2000", "Account Name": "Accounts Payable",    "Description": "PO-2251 raw materials receipt",                "Debit": 0.00, "Credit": 6891.25, "Posted By": "klee", "Source": "PO"},
    # Entry 5: Utility payment
    {"Entry ID": "JE-005", "Entry Date": "2025-06-06", "Account": "6200", "Account Name": "Utilities Expense",   "Description": "Electric bill June 2025",                      "Debit": 1287.43, "Credit": 0.00, "Posted By": "mwilson", "Source": "AP"},
    {"Entry ID": "JE-005", "Entry Date": "2025-06-06", "Account": "1000", "Account Name": "Cash - Operating",    "Description": "Electric bill June 2025",                      "Debit": 0.00, "Credit": 1287.43, "Posted By": "mwilson", "Source": "AP"},
    # Entry 6: Consulting revenue
    {"Entry ID": "JE-006", "Entry Date": "2025-06-09", "Account": "1100", "Account Name": "Accounts Receivable", "Description": "Invoice 1043 - Consulting engagement Q2",      "Debit": 22175.00, "Credit": 0.00, "Posted By": "jsmith", "Source": "AR"},
    {"Entry ID": "JE-006", "Entry Date": "2025-06-09", "Account": "4100", "Account Name": "Consulting Revenue",  "Description": "Invoice 1043 - Consulting engagement Q2",      "Debit": 0.00, "Credit": 22175.00, "Posted By": "jsmith", "Source": "AR"},
    # Entry 7: Insurance
    {"Entry ID": "JE-007", "Entry Date": "2025-06-10", "Account": "6400", "Account Name": "Insurance Expense",   "Description": "Monthly GL&P insurance premium",               "Debit": 1897.50, "Credit": 0.00, "Posted By": "mwilson", "Source": "AP"},
    {"Entry ID": "JE-007", "Entry Date": "2025-06-10", "Account": "1200", "Account Name": "Prepaid Insurance",   "Description": "Monthly GL&P insurance premium",               "Debit": 0.00, "Credit": 1897.50, "Posted By": "mwilson", "Source": "AP"},
    # Entry 8: COGS (avoid amounts near $5K threshold)
    {"Entry ID": "JE-008", "Entry Date": "2025-06-11", "Account": "5000", "Account Name": "Cost of Services",    "Description": "Direct labor allocation - Project Alpha",      "Debit": 3823.80, "Credit": 0.00, "Posted By": "rbrown", "Source": "WIP"},
    {"Entry ID": "JE-008", "Entry Date": "2025-06-11", "Account": "2100", "Account Name": "Accrued Salaries",    "Description": "Direct labor allocation - Project Alpha",      "Debit": 0.00, "Credit": 3823.80, "Posted By": "rbrown", "Source": "WIP"},
    # Entry 9: Office supplies
    {"Entry ID": "JE-009", "Entry Date": "2025-06-12", "Account": "6500", "Account Name": "Office Supplies",     "Description": "Staples order - printer paper and toner",      "Debit": 342.15, "Credit": 0.00, "Posted By": "agarcia", "Source": "AP"},
    {"Entry ID": "JE-009", "Entry Date": "2025-06-12", "Account": "1000", "Account Name": "Cash - Operating",    "Description": "Staples order - printer paper and toner",      "Debit": 0.00, "Credit": 342.15, "Posted By": "agarcia", "Source": "AP"},
    # Entry 10: Professional fees
    {"Entry ID": "JE-010", "Entry Date": "2025-06-13", "Account": "6600", "Account Name": "Professional Fees",   "Description": "Legal counsel retainer - Baker & Associates",  "Debit": 5750.00, "Credit": 0.00, "Posted By": "jsmith", "Source": "AP"},
    {"Entry ID": "JE-010", "Entry Date": "2025-06-13", "Account": "2000", "Account Name": "Accounts Payable",    "Description": "Legal counsel retainer - Baker & Associates",  "Debit": 0.00, "Credit": 5750.00, "Posted By": "jsmith", "Source": "AP"},
    # Entry 11: Marketing
    {"Entry ID": "JE-011", "Entry Date": "2025-06-16", "Account": "6700", "Account Name": "Marketing Expense",   "Description": "Digital campaign spend - LinkedIn ads",        "Debit": 2845.00, "Credit": 0.00, "Posted By": "agarcia", "Source": "CC"},
    {"Entry ID": "JE-011", "Entry Date": "2025-06-16", "Account": "1000", "Account Name": "Cash - Operating",    "Description": "Digital campaign spend - LinkedIn ads",        "Debit": 0.00, "Credit": 2845.00, "Posted By": "agarcia", "Source": "CC"},
    # Entry 12: Customer payment (avoid $9,875 near $10K threshold)
    {"Entry ID": "JE-012", "Entry Date": "2025-06-17", "Account": "1000", "Account Name": "Cash - Operating",    "Description": "Customer payment - Invoice 1038",              "Debit": 8375.25, "Credit": 0.00, "Posted By": "lnguyen", "Source": "CR"},
    {"Entry ID": "JE-012", "Entry Date": "2025-06-17", "Account": "1100", "Account Name": "Accounts Receivable", "Description": "Customer payment - Invoice 1038",              "Debit": 0.00, "Credit": 8375.25, "Posted By": "lnguyen", "Source": "CR"},
    # Entry 13: Depreciation
    {"Entry ID": "JE-013", "Entry Date": "2025-06-18", "Account": "6300", "Account Name": "Depreciation Expense","Description": "Monthly depreciation - equipment",             "Debit": 2067.71, "Credit": 0.00, "Posted By": "payroll_sys", "Source": "GL"},
    {"Entry ID": "JE-013", "Entry Date": "2025-06-18", "Account": "1510", "Account Name": "Accum Depreciation",  "Description": "Monthly depreciation - equipment",             "Debit": 0.00, "Credit": 2067.71, "Posted By": "payroll_sys", "Source": "GL"},
    # Entry 14: Loan payment (avoid June 19 = Juneteenth holiday)
    {"Entry ID": "JE-014", "Entry Date": "2025-06-20", "Account": "2500", "Account Name": "Term Loan Payable",   "Description": "Monthly loan principal payment",               "Debit": 2083.33, "Credit": 0.00, "Posted By": "tchen", "Source": "AP"},
    {"Entry ID": "JE-014", "Entry Date": "2025-06-20", "Account": "1000", "Account Name": "Cash - Operating",    "Description": "Monthly loan principal payment",               "Debit": 0.00, "Credit": 2083.33, "Posted By": "tchen", "Source": "AP"},
    # Entry 15: Revenue - product
    {"Entry ID": "JE-015", "Entry Date": "2025-06-23", "Account": "1100", "Account Name": "Accounts Receivable", "Description": "Invoice 1044 - Product license Q3",            "Debit": 7892.00, "Credit": 0.00, "Posted By": "lnguyen", "Source": "AR"},
    {"Entry ID": "JE-015", "Entry Date": "2025-06-23", "Account": "4200", "Account Name": "License Revenue",     "Description": "Invoice 1044 - Product license Q3",            "Debit": 0.00, "Credit": 7892.00, "Posted By": "lnguyen", "Source": "AR"},
    # Entry 16: Training expense
    {"Entry ID": "JE-016", "Entry Date": "2025-06-23", "Account": "6150", "Account Name": "Training Expense",    "Description": "Staff CPE course registration",                "Debit": 1475.00, "Credit": 0.00, "Posted By": "agarcia", "Source": "CC"},
    {"Entry ID": "JE-016", "Entry Date": "2025-06-23", "Account": "1000", "Account Name": "Cash - Operating",    "Description": "Staff CPE course registration",                "Debit": 0.00, "Credit": 1475.00, "Posted By": "agarcia", "Source": "CC"},
    # Entry 17: Payroll #2
    {"Entry ID": "JE-017", "Entry Date": "2025-06-18", "Account": "6000", "Account Name": "Salaries & Wages",    "Description": "Bi-weekly payroll run 2025-06-18",             "Debit": 8234.75, "Credit": 0.00, "Posted By": "payroll_sys", "Source": "PR"},
    {"Entry ID": "JE-017", "Entry Date": "2025-06-18", "Account": "1050", "Account Name": "Cash - Payroll",      "Description": "Bi-weekly payroll run 2025-06-18",             "Debit": 0.00, "Credit": 8234.75, "Posted By": "payroll_sys", "Source": "PR"},
    # Entry 18: Vendor payment
    {"Entry ID": "JE-018", "Entry Date": "2025-06-24", "Account": "2000", "Account Name": "Accounts Payable",    "Description": "Vendor payment batch - check run #127",        "Debit": 11562.50, "Credit": 0.00, "Posted By": "mwilson", "Source": "AP"},
    {"Entry ID": "JE-018", "Entry Date": "2025-06-24", "Account": "1000", "Account Name": "Cash - Operating",    "Description": "Vendor payment batch - check run #127",        "Debit": 0.00, "Credit": 11562.50, "Posted By": "mwilson", "Source": "AP"},
    # Entry 19: Travel expense
    {"Entry ID": "JE-019", "Entry Date": "2025-06-25", "Account": "6350", "Account Name": "Travel Expense",      "Description": "Business travel - client site visit Dallas",   "Debit": 1834.62, "Credit": 0.00, "Posted By": "klee", "Source": "EXP"},
    {"Entry ID": "JE-019", "Entry Date": "2025-06-25", "Account": "1000", "Account Name": "Cash - Operating",    "Description": "Business travel - client site visit Dallas",   "Debit": 0.00, "Credit": 1834.62, "Posted By": "klee", "Source": "EXP"},
    # Entry 20: Accrual reclassification (avoid "adjustment" keyword)
    {"Entry ID": "JE-020", "Entry Date": "2025-06-02", "Account": "2100", "Account Name": "Accrued Salaries",    "Description": "May salary accrual - payroll cycle alignment","Debit": 3912.38, "Credit": 0.00, "Posted By": "tchen", "Source": "GL"},
    {"Entry ID": "JE-020", "Entry Date": "2025-06-02", "Account": "6000", "Account Name": "Salaries & Wages",    "Description": "May salary accrual - payroll cycle alignment","Debit": 0.00, "Credit": 3912.38, "Posted By": "tchen", "Source": "GL"},
    # Entry 21: Software subscription (avoid amounts near $5K threshold)
    {"Entry ID": "JE-021", "Entry Date": "2025-06-26", "Account": "6250", "Account Name": "Software Expense",    "Description": "Annual SaaS platform renewal",                 "Debit": 3599.00, "Credit": 0.00, "Posted By": "rbrown", "Source": "AP"},
    {"Entry ID": "JE-021", "Entry Date": "2025-06-26", "Account": "2000", "Account Name": "Accounts Payable",    "Description": "Annual SaaS platform renewal",                 "Debit": 0.00, "Credit": 3599.00, "Posted By": "rbrown", "Source": "AP"},
    # Entry 22: Repairs & maintenance
    {"Entry ID": "JE-022", "Entry Date": "2025-06-27", "Account": "6450", "Account Name": "Repairs & Maint",     "Description": "HVAC quarterly service call",                  "Debit": 875.00, "Credit": 0.00, "Posted By": "mwilson", "Source": "AP"},
    {"Entry ID": "JE-022", "Entry Date": "2025-06-27", "Account": "1000", "Account Name": "Cash - Operating",    "Description": "HVAC quarterly service call",                  "Debit": 0.00, "Credit": 875.00, "Posted By": "mwilson", "Source": "AP"},
    # Entry 23: Revenue - subscription
    {"Entry ID": "JE-023", "Entry Date": "2025-06-03", "Account": "1100", "Account Name": "Accounts Receivable", "Description": "Invoice 1045 - Monthly subscription June",     "Debit": 3215.00, "Credit": 0.00, "Posted By": "jsmith", "Source": "AR"},
    {"Entry ID": "JE-023", "Entry Date": "2025-06-03", "Account": "4500", "Account Name": "Subscription Revenue","Description": "Invoice 1045 - Monthly subscription June",     "Debit": 0.00, "Credit": 3215.00, "Posted By": "jsmith", "Source": "AR"},
    # Entry 24: Tax payment
    {"Entry ID": "JE-024", "Entry Date": "2025-06-16", "Account": "2150", "Account Name": "Tax Liabilities",     "Description": "Quarterly estimated tax payment",              "Debit": 6725.00, "Credit": 0.00, "Posted By": "mwilson", "Source": "GL"},
    {"Entry ID": "JE-024", "Entry Date": "2025-06-16", "Account": "1000", "Account Name": "Cash - Operating",    "Description": "Quarterly estimated tax payment",              "Debit": 0.00, "Credit": 6725.00, "Posted By": "mwilson", "Source": "GL"},
    # Entry 25: Shipping expense
    {"Entry ID": "JE-025", "Entry Date": "2025-06-05", "Account": "6050", "Account Name": "Shipping Expense",    "Description": "FedEx monthly billing statement",              "Debit": 1623.45, "Credit": 0.00, "Posted By": "klee", "Source": "AP"},
    {"Entry ID": "JE-025", "Entry Date": "2025-06-05", "Account": "2000", "Account Name": "Accounts Payable",    "Description": "FedEx monthly billing statement",              "Debit": 0.00, "Credit": 1623.45, "Posted By": "klee", "Source": "AP"},
]
# fmt: on


def _verify_balanced(entries: list[dict]) -> None:
    """Raise if any entry group is unbalanced."""
    from collections import defaultdict

    groups: dict[str, list[dict]] = defaultdict(list)
    for e in entries:
        groups[e["Entry ID"]].append(e)

    for eid, rows in groups.items():
        total_dr = sum(r["Debit"] for r in rows)
        total_cr = sum(r["Credit"] for r in rows)
        assert abs(total_dr - total_cr) < 0.01, f"Entry {eid} is unbalanced: DR={total_dr}, CR={total_cr}"


# Validate at import time
_verify_balanced(_ENTRIES)


class BaseJournalEntryFactory:
    """Factory for a clean, flag-free set of journal entries."""

    @classmethod
    def as_rows(cls) -> list[dict]:
        """Return the base entries as a list of dicts (for run_je_testing)."""
        return [dict(e) for e in _ENTRIES]

    @classmethod
    def column_names(cls) -> list[str]:
        """Return column names matching the entry dicts."""
        return list(_ENTRIES[0].keys())

    @classmethod
    def as_dataframe(cls) -> pd.DataFrame:
        """Return the base entries as a pandas DataFrame."""
        return pd.DataFrame(_ENTRIES)

    @classmethod
    def as_csv_bytes(cls) -> bytes:
        """Return the base entries as CSV bytes."""
        df = cls.as_dataframe()
        buf = io.BytesIO()
        df.to_csv(buf, index=False)
        return buf.getvalue()
