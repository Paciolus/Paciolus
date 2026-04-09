"""Base revenue entry factory for Revenue Testing anomaly framework.

Produces a valid, clean set of 20 revenue entries that trigger zero flags
in the revenue testing engine. Uses Meridian Capital Group naming conventions.

Key design decisions:
- No round amounts >= $10,000 (RT-03 round_revenue_amounts threshold)
- No duplicate entries (same date + amount + account) — RT-11
- No negative amounts (sign anomalies) — RT-04
- Reasonable spread across Q2 2025 months (not all in one period) — RT-02/RT-09
- Multiple revenue accounts (Service, Consulting, License, Subscription) — RT-08
- No suspicious contra-revenue keywords (return, refund, allowance, etc.) — RT-12
- No amounts that are statistical outliers relative to the set — RT-06
- All amounts are positive credits (revenue normal)
- All dates are weekdays in Q2 2025 (April–June)
- No ASC 606 contract columns (clean baseline; generators add them)
- Entry types are "system" or "auto" (not manual) to avoid RT-01
- Amounts below $50,000 large_entry_threshold (RT-01 default)

Column names match revenue_testing_engine.py column detection patterns:
  Date, Amount, Account Name, Account Number, Description, Entry Type, Reference
"""

# fmt: off
_ENTRIES: list[dict] = [
    # April 2025 entries (6 entries — spread across the month)
    {"Date": "2025-04-02", "Amount": 12743.50, "Account Name": "Service Revenue",       "Account Number": "4000", "Description": "Invoice MCG-1101 - IT consulting services",           "Entry Type": "system", "Reference": "INV-1101"},
    {"Date": "2025-04-04", "Amount": 8215.75,  "Account Name": "Consulting Revenue",    "Account Number": "4100", "Description": "Invoice MCG-1102 - Strategy advisory Q2",            "Entry Type": "system", "Reference": "INV-1102"},
    {"Date": "2025-04-09", "Amount": 3456.25,  "Account Name": "Subscription Revenue",  "Account Number": "4500", "Description": "Monthly SaaS platform subscription - April",        "Entry Type": "auto",   "Reference": "SUB-0401"},
    {"Date": "2025-04-15", "Amount": 6891.30,  "Account Name": "License Revenue",       "Account Number": "4200", "Description": "Software license renewal - Meridian Analytics",     "Entry Type": "system", "Reference": "LIC-2251"},
    {"Date": "2025-04-22", "Amount": 15234.80, "Account Name": "Service Revenue",       "Account Number": "4000", "Description": "Invoice MCG-1103 - Managed services April",         "Entry Type": "system", "Reference": "INV-1103"},
    {"Date": "2025-04-28", "Amount": 4567.90,  "Account Name": "Consulting Revenue",    "Account Number": "4100", "Description": "Invoice MCG-1104 - Tax advisory engagement",        "Entry Type": "system", "Reference": "INV-1104"},

    # May 2025 entries (7 entries — heaviest month for realistic variation)
    {"Date": "2025-05-02", "Amount": 9873.45,  "Account Name": "Service Revenue",       "Account Number": "4000", "Description": "Invoice MCG-1105 - Cloud migration phase 2",        "Entry Type": "system", "Reference": "INV-1105"},
    {"Date": "2025-05-07", "Amount": 3456.25,  "Account Name": "Subscription Revenue",  "Account Number": "4500", "Description": "Monthly SaaS platform subscription - May",          "Entry Type": "auto",   "Reference": "SUB-0501"},
    {"Date": "2025-05-12", "Amount": 7234.60,  "Account Name": "License Revenue",       "Account Number": "4200", "Description": "Enterprise license - Meridian Data Suite",          "Entry Type": "system", "Reference": "LIC-2252"},
    {"Date": "2025-05-15", "Amount": 18432.15, "Account Name": "Consulting Revenue",    "Account Number": "4100", "Description": "Invoice MCG-1106 - Regulatory compliance project",  "Entry Type": "system", "Reference": "INV-1106"},
    {"Date": "2025-05-20", "Amount": 5678.40,  "Account Name": "Service Revenue",       "Account Number": "4000", "Description": "Invoice MCG-1107 - Technical support retainer",     "Entry Type": "system", "Reference": "INV-1107"},
    {"Date": "2025-05-23", "Amount": 2345.80,  "Account Name": "Subscription Revenue",  "Account Number": "4500", "Description": "Add-on module subscription - reporting tier",       "Entry Type": "auto",   "Reference": "SUB-0502"},
    {"Date": "2025-05-29", "Amount": 11287.55, "Account Name": "Service Revenue",       "Account Number": "4000", "Description": "Invoice MCG-1108 - Infrastructure audit services",  "Entry Type": "system", "Reference": "INV-1108"},

    # June 2025 entries (7 entries — spread to avoid year-end concentration)
    {"Date": "2025-06-03", "Amount": 3456.25,  "Account Name": "Subscription Revenue",  "Account Number": "4500", "Description": "Monthly SaaS platform subscription - June",         "Entry Type": "auto",   "Reference": "SUB-0601"},
    {"Date": "2025-06-06", "Amount": 14567.35, "Account Name": "Consulting Revenue",    "Account Number": "4100", "Description": "Invoice MCG-1109 - M&A due diligence phase 1",     "Entry Type": "system", "Reference": "INV-1109"},
    {"Date": "2025-06-10", "Amount": 8923.70,  "Account Name": "License Revenue",       "Account Number": "4200", "Description": "Annual license renewal - Meridian Compliance Pro",  "Entry Type": "system", "Reference": "LIC-2253"},
    {"Date": "2025-06-13", "Amount": 6234.50,  "Account Name": "Service Revenue",       "Account Number": "4000", "Description": "Invoice MCG-1110 - Penetration testing services",   "Entry Type": "system", "Reference": "INV-1110"},
    {"Date": "2025-06-17", "Amount": 4789.15,  "Account Name": "Consulting Revenue",    "Account Number": "4100", "Description": "Invoice MCG-1111 - Process improvement workshop",   "Entry Type": "system", "Reference": "INV-1111"},
    {"Date": "2025-06-20", "Amount": 7123.90,  "Account Name": "Service Revenue",       "Account Number": "4000", "Description": "Invoice MCG-1112 - Data analytics deliverable",     "Entry Type": "system", "Reference": "INV-1112"},
    {"Date": "2025-06-24", "Amount": 5891.45,  "Account Name": "License Revenue",       "Account Number": "4200", "Description": "Perpetual license - Meridian Workflow Engine",      "Entry Type": "system", "Reference": "LIC-2254"},
]
# fmt: on


def _verify_clean(entries: list[dict]) -> None:
    """Raise if any entry would trigger a flag in the revenue testing engine.

    Checks:
    - No negative amounts (RT-04)
    - No round amounts >= $10,000 (RT-03)
    - No duplicate (date+amount+account) tuples (RT-11)
    - No contra-revenue keywords in descriptions (RT-12)
    - No manual entry types (RT-01 with amounts above threshold)
    - All dates are weekdays
    """
    from datetime import datetime

    contra_keywords = [
        "return",
        "refund",
        "allowance",
        "discount",
        "rebate",
        "credit memo",
        "credit note",
        "reversal",
        "write-off",
        "write off",
        "contra",
        "adjustment",
    ]

    seen: set[tuple] = set()
    amounts: list[float] = []

    for e in entries:
        amt = e["Amount"]

        # No negatives
        assert amt > 0, f"Negative amount found: {amt} in {e['Description']}"

        # No round amounts >= $10,000
        if amt >= 10_000:
            assert amt % 1000 != 0, f"Round amount >= $10,000 found: ${amt:,.2f} in {e['Description']}"

        # No duplicates
        key = (e["Date"], e["Amount"], e["Account Name"])
        assert key not in seen, f"Duplicate entry found: {key}"
        seen.add(key)

        # No contra-revenue keywords
        desc_lower = e["Description"].lower()
        acct_lower = e["Account Name"].lower()
        combined = desc_lower + " " + acct_lower
        for kw in contra_keywords:
            assert kw not in combined, f"Contra-revenue keyword '{kw}' found in: {e['Description']}"

        # No manual entry types
        entry_type = e.get("Entry Type", "").lower().strip()
        assert entry_type not in ("manual", "man", "m", "manual entry", "manual je", "user"), (
            f"Manual entry type found: {entry_type} in {e['Description']}"
        )

        # Weekday check
        dt = datetime.strptime(e["Date"], "%Y-%m-%d")
        assert dt.weekday() < 5, f"Weekend date found: {e['Date']} in {e['Description']}"

        amounts.append(amt)

    # No extreme outliers (z-score check with relaxed threshold)
    import statistics

    mean = statistics.mean(amounts)
    stdev = statistics.stdev(amounts)
    for amt in amounts:
        if stdev > 0:
            zscore = abs(amt - mean) / stdev
            assert zscore < 3.0, f"Statistical outlier: ${amt:,.2f} (z-score={zscore:.2f})"


# Validate at import time
_verify_clean(_ENTRIES)


class BaseRevenueEntryFactory:
    """Factory for a clean, flag-free set of revenue entries.

    Produces rows compatible with revenue_testing_engine.run_revenue_testing().
    Column names: Date, Amount, Account Name, Account Number, Description,
                  Entry Type, Reference.
    """

    @classmethod
    def as_rows(cls) -> list[dict]:
        """Return the base entries as a list of dicts (for run_revenue_testing)."""
        return [dict(e) for e in _ENTRIES]

    @classmethod
    def column_names(cls) -> list[str]:
        """Return column names matching the entry dicts."""
        return list(_ENTRIES[0].keys())
