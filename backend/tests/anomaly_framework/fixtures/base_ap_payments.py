"""Base AP payment factory for AP testing anomaly framework.

Produces a valid, clean set of 20 AP payment records that trigger zero flags
in the AP testing engine. Uses Meridian Capital Group vendor naming conventions.

Key design decisions:
- No duplicate invoices (exact or fuzzy — unique vendor+invoice+amount+date combos)
- No round amounts >= $10,000
- No weekend payments (all dates are weekdays in June-July 2025)
- No missing critical fields (all required columns populated)
- No gaps in check numbers (sequential 10001-10020)
- Reasonable variety of vendors, dates, and amounts
- All Invoice Dates before Payment Dates
- No suspicious keywords in descriptions
- Amounts NOT just below common thresholds ($5K, $10K, $25K, $50K)
- No vendor name variations that would trigger fuzzy matching
- Payment methods: Check, ACH, Wire
"""

# fmt: off
_PAYMENTS: list[dict] = [
    # Payment 1: Office supplies
    {
        "Invoice Number": "INV-4201",
        "Invoice Date": "2025-06-02",
        "Payment Date": "2025-06-16",
        "Vendor Name": "Meridian Office Solutions",
        "Vendor ID": "V-1001",
        "Amount": 2347.85,
        "Check Number": "10001",
        "Description": "Q2 office supplies - printer paper and toner",
        "GL Account": "6500",
        "Payment Method": "Check",
    },
    # Payment 2: IT consulting
    {
        "Invoice Number": "INV-4202",
        "Invoice Date": "2025-06-03",
        "Payment Date": "2025-06-17",
        "Vendor Name": "Apex Technology Partners",
        "Vendor ID": "V-1002",
        "Amount": 8743.50,
        "Check Number": "10002",
        "Description": "Network infrastructure maintenance - June",
        "GL Account": "6600",
        "Payment Method": "ACH",
    },
    # Payment 3: Building lease
    {
        "Invoice Number": "INV-4203",
        "Invoice Date": "2025-06-04",
        "Payment Date": "2025-06-18",
        "Vendor Name": "Harborview Properties LLC",
        "Vendor ID": "V-1003",
        "Amount": 6891.25,
        "Check Number": "10003",
        "Description": "Monthly facility lease - Suite 400",
        "GL Account": "6100",
        "Payment Method": "ACH",
    },
    # Payment 4: Legal services
    {
        "Invoice Number": "INV-4204",
        "Invoice Date": "2025-06-05",
        "Payment Date": "2025-06-19",
        "Vendor Name": "Whitfield & Associates LLP",
        "Vendor ID": "V-1004",
        "Amount": 3156.70,
        "Check Number": "10004",
        "Description": "Contract review services - vendor agreement",
        "GL Account": "6600",
        "Payment Method": "Check",
    },
    # Payment 5: Insurance premium
    {
        "Invoice Number": "INV-4205",
        "Invoice Date": "2025-06-06",
        "Payment Date": "2025-06-20",
        "Vendor Name": "National Indemnity Group",
        "Vendor ID": "V-1005",
        "Amount": 1897.43,
        "Check Number": "10005",
        "Description": "Monthly GL&P insurance premium",
        "GL Account": "6400",
        "Payment Method": "ACH",
    },
    # Payment 6: Janitorial services
    {
        "Invoice Number": "INV-4206",
        "Invoice Date": "2025-06-09",
        "Payment Date": "2025-06-23",
        "Vendor Name": "CleanPro Facility Services",
        "Vendor ID": "V-1006",
        "Amount": 1425.60,
        "Check Number": "10006",
        "Description": "Monthly janitorial and cleaning contract",
        "GL Account": "6450",
        "Payment Method": "Check",
    },
    # Payment 7: Marketing agency
    {
        "Invoice Number": "INV-4207",
        "Invoice Date": "2025-06-10",
        "Payment Date": "2025-06-24",
        "Vendor Name": "Brightline Creative Agency",
        "Vendor ID": "V-1007",
        "Amount": 4263.90,
        "Check Number": "10007",
        "Description": "Digital marketing campaign - LinkedIn Q2",
        "GL Account": "6700",
        "Payment Method": "Wire",
    },
    # Payment 8: Telecom
    {
        "Invoice Number": "INV-4208",
        "Invoice Date": "2025-06-11",
        "Payment Date": "2025-06-25",
        "Vendor Name": "Summit Telecom Inc",
        "Vendor ID": "V-1008",
        "Amount": 783.45,
        "Check Number": "10008",
        "Description": "Monthly phone and internet service",
        "GL Account": "6200",
        "Payment Method": "ACH",
    },
    # Payment 9: Raw materials
    {
        "Invoice Number": "INV-4209",
        "Invoice Date": "2025-06-12",
        "Payment Date": "2025-06-26",
        "Vendor Name": "Cascade Industrial Supply",
        "Vendor ID": "V-1009",
        "Amount": 7634.15,
        "Check Number": "10009",
        "Description": "PO-3301 raw materials - aluminum stock",
        "GL Account": "1300",
        "Payment Method": "Check",
    },
    # Payment 10: Accounting software
    {
        "Invoice Number": "INV-4210",
        "Invoice Date": "2025-06-13",
        "Payment Date": "2025-06-27",
        "Vendor Name": "Ledgerworks Software Corp",
        "Vendor ID": "V-1010",
        "Amount": 3599.75,
        "Check Number": "10010",
        "Description": "Annual SaaS platform license renewal",
        "GL Account": "6250",
        "Payment Method": "ACH",
    },
    # Payment 11: Staffing agency
    {
        "Invoice Number": "INV-4211",
        "Invoice Date": "2025-06-16",
        "Payment Date": "2025-06-30",
        "Vendor Name": "Pinnacle Staffing Solutions",
        "Vendor ID": "V-1011",
        "Amount": 6217.80,
        "Check Number": "10011",
        "Description": "Temporary staffing - warehouse operations",
        "GL Account": "6000",
        "Payment Method": "Check",
    },
    # Payment 12: Equipment maintenance
    {
        "Invoice Number": "INV-4212",
        "Invoice Date": "2025-06-17",
        "Payment Date": "2025-07-01",
        "Vendor Name": "Atlas Equipment Services",
        "Vendor ID": "V-1012",
        "Amount": 2871.30,
        "Check Number": "10012",
        "Description": "Quarterly HVAC preventive maintenance",
        "GL Account": "6450",
        "Payment Method": "ACH",
    },
    # Payment 13: Courier services
    {
        "Invoice Number": "INV-4213",
        "Invoice Date": "2025-06-18",
        "Payment Date": "2025-07-02",
        "Vendor Name": "Velocity Logistics Corp",
        "Vendor ID": "V-1013",
        "Amount": 1623.45,
        "Check Number": "10013",
        "Description": "Monthly courier and shipping statement",
        "GL Account": "6050",
        "Payment Method": "Check",
    },
    # Payment 14: Training provider
    {
        "Invoice Number": "INV-4214",
        "Invoice Date": "2025-06-19",
        "Payment Date": "2025-07-03",
        "Vendor Name": "Cornerstone Learning Institute",
        "Vendor ID": "V-1014",
        "Amount": 1875.20,
        "Check Number": "10014",
        "Description": "Staff CPE certification course - July cohort",
        "GL Account": "6150",
        "Payment Method": "Wire",
    },
    # Payment 15: Security services
    {
        "Invoice Number": "INV-4215",
        "Invoice Date": "2025-06-20",
        "Payment Date": "2025-07-07",
        "Vendor Name": "Ironclad Security Group",
        "Vendor ID": "V-1015",
        "Amount": 3412.65,
        "Check Number": "10015",
        "Description": "Monthly building security patrol contract",
        "GL Account": "6450",
        "Payment Method": "ACH",
    },
    # Payment 16: Printing services
    {
        "Invoice Number": "INV-4216",
        "Invoice Date": "2025-06-23",
        "Payment Date": "2025-07-08",
        "Vendor Name": "Prestige Print & Copy",
        "Vendor ID": "V-1016",
        "Amount": 567.90,
        "Check Number": "10016",
        "Description": "Business cards and letterhead reprint",
        "GL Account": "6500",
        "Payment Method": "Check",
    },
    # Payment 17: Utility payment
    {
        "Invoice Number": "INV-4217",
        "Invoice Date": "2025-06-24",
        "Payment Date": "2025-07-09",
        "Vendor Name": "Metro Power & Light",
        "Vendor ID": "V-1017",
        "Amount": 1287.35,
        "Check Number": "10017",
        "Description": "Monthly electric and gas utility bill",
        "GL Account": "6200",
        "Payment Method": "ACH",
    },
    # Payment 18: Professional audit
    {
        "Invoice Number": "INV-4218",
        "Invoice Date": "2025-06-25",
        "Payment Date": "2025-07-10",
        "Vendor Name": "Sterling Audit Partners",
        "Vendor ID": "V-1018",
        "Amount": 8456.75,
        "Check Number": "10018",
        "Description": "Interim financial review engagement - Q2",
        "GL Account": "6600",
        "Payment Method": "Wire",
    },
    # Payment 19: Fleet fuel
    {
        "Invoice Number": "INV-4219",
        "Invoice Date": "2025-06-26",
        "Payment Date": "2025-07-11",
        "Vendor Name": "Continental Fuel Services",
        "Vendor ID": "V-1019",
        "Amount": 2134.55,
        "Check Number": "10019",
        "Description": "Monthly fleet fuel card statement",
        "GL Account": "6350",
        "Payment Method": "ACH",
    },
    # Payment 20: Landscaping
    {
        "Invoice Number": "INV-4220",
        "Invoice Date": "2025-06-27",
        "Payment Date": "2025-07-14",
        "Vendor Name": "Greenscape Property Care",
        "Vendor ID": "V-1020",
        "Amount": 945.80,
        "Check Number": "10020",
        "Description": "Monthly grounds maintenance and lawn care",
        "GL Account": "6450",
        "Payment Method": "Check",
    },
]
# fmt: on


def _verify_no_duplicates(payments: list[dict]) -> None:
    """Raise if any exact duplicate keys exist (vendor + invoice + amount + date)."""
    seen: set[tuple] = set()
    for p in payments:
        key = (
            p["Vendor Name"],
            p["Invoice Number"],
            p["Amount"],
            p["Payment Date"],
        )
        assert key not in seen, (
            f"Duplicate payment key found: vendor={p['Vendor Name']}, "
            f"invoice={p['Invoice Number']}, amount={p['Amount']}"
        )
        seen.add(key)


# Validate at import time
_verify_no_duplicates(_PAYMENTS)


class BaseAPPaymentFactory:
    """Factory for a clean, flag-free set of AP payment records."""

    @classmethod
    def as_rows(cls) -> list[dict]:
        """Return the base payments as a list of dicts (for run_ap_testing)."""
        return [dict(p) for p in _PAYMENTS]

    @classmethod
    def column_names(cls) -> list[str]:
        """Return column names matching the payment dicts."""
        return list(_PAYMENTS[0].keys())
