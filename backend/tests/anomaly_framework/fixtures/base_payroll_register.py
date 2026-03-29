"""Base payroll register factory for Payroll Testing anomaly framework.

Produces a valid, clean set of 15 payroll records that trigger zero flags
in the Payroll Testing engine. Uses Meridian Capital Group naming conventions.

Key design decisions:
- No duplicate employee IDs, names, tax IDs, or bank accounts
- No round amounts >= $10,000
- All employees have unique addresses
- No gaps in check numbers (sequential 5001–5015)
- No termination dates (all active employees)
- Reasonable gross-to-net ratios (~65–75% net/gross)
- Pay dates on business days (bi-weekly Fridays in June 2025)
- Variety of departments and pay levels
- All employee IDs follow EMP-NNN pattern
- Masked bank accounts (****NNNN) and tax IDs (***-**-NNNN)
"""

import io

import pandas as pd

# fmt: off
_RECORDS: list[dict] = [
    # Pay Period 1: Friday 2025-06-06
    {
        "Employee ID": "EMP-101", "Employee Name": "Margaret Chen",
        "Department": "Accounting", "Pay Date": "2025-06-06",
        "Gross Pay": 4231.75, "Net Pay": 2954.22,
        "Tax ID": "***-**-4821", "Address": "1420 Elm Street, Suite 3A, Hartford, CT 06103",
        "Bank Account": "****7291", "Check Number": "5001",
    },
    {
        "Employee ID": "EMP-102", "Employee Name": "David Kowalski",
        "Department": "Engineering", "Pay Date": "2025-06-06",
        "Gross Pay": 5847.50, "Net Pay": 4093.25,
        "Tax ID": "***-**-6137", "Address": "88 Birch Lane, Glastonbury, CT 06033",
        "Bank Account": "****3058", "Check Number": "5002",
    },
    {
        "Employee ID": "EMP-103", "Employee Name": "Priya Ramanathan",
        "Department": "Operations", "Pay Date": "2025-06-06",
        "Gross Pay": 3756.00, "Net Pay": 2629.20,
        "Tax ID": "***-**-9254", "Address": "305 Oak Ridge Drive, West Hartford, CT 06107",
        "Bank Account": "****6412", "Check Number": "5003",
    },
    {
        "Employee ID": "EMP-104", "Employee Name": "James Whitfield",
        "Department": "Sales", "Pay Date": "2025-06-06",
        "Gross Pay": 6125.33, "Net Pay": 4287.73,
        "Tax ID": "***-**-1748", "Address": "57 Prospect Avenue, Apt 12, New Britain, CT 06051",
        "Bank Account": "****8935", "Check Number": "5004",
    },
    {
        "Employee ID": "EMP-105", "Employee Name": "Rosa Delgado",
        "Department": "Human Resources", "Pay Date": "2025-06-06",
        "Gross Pay": 3412.67, "Net Pay": 2388.87,
        "Tax ID": "***-**-3592", "Address": "742 Maple Court, Wethersfield, CT 06109",
        "Bank Account": "****1647", "Check Number": "5005",
    },
    # Pay Period 2: Friday 2025-06-20
    {
        "Employee ID": "EMP-106", "Employee Name": "Thomas Okafor",
        "Department": "Engineering", "Pay Date": "2025-06-20",
        "Gross Pay": 5523.80, "Net Pay": 3866.66,
        "Tax ID": "***-**-7863", "Address": "19 Willow Bend, Rocky Hill, CT 06067",
        "Bank Account": "****4273", "Check Number": "5006",
    },
    {
        "Employee ID": "EMP-107", "Employee Name": "Linda Vasquez",
        "Department": "Accounting", "Pay Date": "2025-06-20",
        "Gross Pay": 4087.25, "Net Pay": 2861.08,
        "Tax ID": "***-**-2016", "Address": "631 Chestnut Street, Manchester, CT 06040",
        "Bank Account": "****5826", "Check Number": "5007",
    },
    {
        "Employee ID": "EMP-108", "Employee Name": "Sean Fitzgerald",
        "Department": "Operations", "Pay Date": "2025-06-20",
        "Gross Pay": 3298.50, "Net Pay": 2308.95,
        "Tax ID": "***-**-8431", "Address": "214 Cedar Hill Road, Newington, CT 06111",
        "Bank Account": "****9164", "Check Number": "5008",
    },
    {
        "Employee ID": "EMP-109", "Employee Name": "Aisha Patel",
        "Department": "Sales", "Pay Date": "2025-06-20",
        "Gross Pay": 7234.17, "Net Pay": 5063.92,
        "Tax ID": "***-**-5679", "Address": "103 Summit Avenue, Bloomfield, CT 06002",
        "Bank Account": "****2738", "Check Number": "5009",
    },
    {
        "Employee ID": "EMP-110", "Employee Name": "Robert Nakamura",
        "Department": "Legal", "Pay Date": "2025-06-20",
        "Gross Pay": 8156.42, "Net Pay": 5709.49,
        "Tax ID": "***-**-4103", "Address": "486 Pine Terrace, Farmington, CT 06032",
        "Bank Account": "****7589", "Check Number": "5010",
    },
    # Pay Period 1 (continued): additional employees paid 2025-06-06
    {
        "Employee ID": "EMP-111", "Employee Name": "Catherine Brooks",
        "Department": "Marketing", "Pay Date": "2025-06-06",
        "Gross Pay": 4675.83, "Net Pay": 3272.58,
        "Tax ID": "***-**-6842", "Address": "928 Laurel Way, Simsbury, CT 06070",
        "Bank Account": "****3401", "Check Number": "5011",
    },
    {
        "Employee ID": "EMP-112", "Employee Name": "Michael Andersen",
        "Department": "IT", "Pay Date": "2025-06-06",
        "Gross Pay": 5178.92, "Net Pay": 3625.24,
        "Tax ID": "***-**-1265", "Address": "67 Spruce Street, Unit B, Avon, CT 06001",
        "Bank Account": "****8052", "Check Number": "5012",
    },
    # Pay Period 2 (continued): additional employees paid 2025-06-20
    {
        "Employee ID": "EMP-113", "Employee Name": "Jennifer Wu",
        "Department": "Engineering", "Pay Date": "2025-06-20",
        "Gross Pay": 6342.08, "Net Pay": 4439.46,
        "Tax ID": "***-**-3978", "Address": "1501 Valley Drive, South Windsor, CT 06074",
        "Bank Account": "****6193", "Check Number": "5013",
    },
    {
        "Employee ID": "EMP-114", "Employee Name": "Anthony Morales",
        "Department": "Operations", "Pay Date": "2025-06-20",
        "Gross Pay": 3587.33, "Net Pay": 2511.13,
        "Tax ID": "***-**-7521", "Address": "340 Hickory Lane, East Hartford, CT 06108",
        "Bank Account": "****4817", "Check Number": "5014",
    },
    {
        "Employee ID": "EMP-115", "Employee Name": "Karen Sullivan",
        "Department": "Accounting", "Pay Date": "2025-06-20",
        "Gross Pay": 4456.25, "Net Pay": 3119.38,
        "Tax ID": "***-**-2394", "Address": "855 Walnut Circle, Windsor, CT 06095",
        "Bank Account": "****5340", "Check Number": "5015",
    },
]
# fmt: on


def _verify_no_duplicates(records: list[dict]) -> None:
    """Raise if any employee IDs, names, tax IDs, or bank accounts are duplicated."""
    for field in ("Employee ID", "Employee Name", "Tax ID", "Bank Account"):
        values = [r[field] for r in records]
        dupes = [v for v in values if values.count(v) > 1]
        assert not dupes, f"Duplicate {field} values found: {set(dupes)}"


def _verify_no_round_amounts(records: list[dict], threshold: float = 10000.0) -> None:
    """Raise if any gross pay is a round amount >= threshold."""
    for r in records:
        gross = r["Gross Pay"]
        if gross >= threshold and gross % 1000 == 0:
            raise AssertionError(f"Round amount found: {r['Employee Name']} has Gross Pay ${gross:,.2f}")


def _verify_sequential_checks(records: list[dict]) -> None:
    """Raise if check numbers have gaps."""
    checks = sorted(int(r["Check Number"]) for r in records)
    for i in range(1, len(checks)):
        gap = checks[i] - checks[i - 1]
        if gap != 1:
            raise AssertionError(f"Check number gap: {checks[i - 1]} -> {checks[i]} (gap of {gap})")


def _verify_unique_addresses(records: list[dict]) -> None:
    """Raise if any addresses are duplicated."""
    addrs = [r["Address"] for r in records]
    dupes = [a for a in addrs if addrs.count(a) > 1]
    assert not dupes, f"Duplicate addresses found: {set(dupes)}"


# Validate at import time
_verify_no_duplicates(_RECORDS)
_verify_no_round_amounts(_RECORDS)
_verify_sequential_checks(_RECORDS)
_verify_unique_addresses(_RECORDS)


class BasePayrollRegisterFactory:
    """Factory for a clean, flag-free set of payroll register entries."""

    @classmethod
    def as_rows(cls) -> list[dict]:
        """Return the base records as a list of dicts (for run_payroll_testing)."""
        return [dict(r) for r in _RECORDS]

    @classmethod
    def column_names(cls) -> list[str]:
        """Return column names matching the record dicts."""
        return list(_RECORDS[0].keys())

    @classmethod
    def as_dataframe(cls) -> pd.DataFrame:
        """Return the base records as a pandas DataFrame."""
        return pd.DataFrame(_RECORDS)

    @classmethod
    def as_csv_bytes(cls) -> bytes:
        """Return the base records as CSV bytes."""
        df = cls.as_dataframe()
        buf = io.BytesIO()
        df.to_csv(buf, index=False)
        return buf.getvalue()
