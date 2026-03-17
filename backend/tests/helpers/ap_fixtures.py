"""Shared AP test fixture helpers.

Centralizes helpers duplicated across test_ap_core.py, test_ap_tier2.py,
and test_ap_tier3.py.
"""

from __future__ import annotations

from ap_testing_engine import APPayment, detect_ap_columns, parse_ap_payments


def make_payments(rows: list[dict], columns: list[str] | None = None) -> list[APPayment]:
    """Parse rows into APPayment objects using auto-detection."""
    if columns is None:
        columns = list(rows[0].keys()) if rows else []
    detection = detect_ap_columns(columns)
    return parse_ap_payments(rows, detection)


def sample_ap_rows() -> list[dict]:
    """4 clean payments for baseline tests."""
    return [
        {
            "Invoice Number": "INV-001",
            "Invoice Date": "2025-01-05",
            "Payment Date": "2025-01-15",
            "Vendor Name": "Acme Corp",
            "Vendor ID": "V001",
            "Amount": 5000.50,
            "Check Number": "CHK-1001",
            "Description": "Office supplies",
            "GL Account": "6100",
            "Payment Method": "Check",
        },
        {
            "Invoice Number": "INV-002",
            "Invoice Date": "2025-01-10",
            "Payment Date": "2025-01-20",
            "Vendor Name": "Beta LLC",
            "Vendor ID": "V002",
            "Amount": 12500.00,
            "Check Number": "CHK-1002",
            "Description": "Consulting fees",
            "GL Account": "6200",
            "Payment Method": "Check",
        },
        {
            "Invoice Number": "INV-003",
            "Invoice Date": "2025-02-01",
            "Payment Date": "2025-02-10",
            "Vendor Name": "Gamma Inc",
            "Vendor ID": "V003",
            "Amount": 3200.75,
            "Check Number": "CHK-1003",
            "Description": "IT services",
            "GL Account": "6300",
            "Payment Method": "ACH",
        },
        {
            "Invoice Number": "INV-004",
            "Invoice Date": "2025-02-15",
            "Payment Date": "2025-02-25",
            "Vendor Name": "Delta Corp",
            "Vendor ID": "V004",
            "Amount": 8750.00,
            "Check Number": "CHK-1004",
            "Description": "Equipment lease",
            "GL Account": "6400",
            "Payment Method": "Wire",
        },
    ]


def sample_ap_columns() -> list[str]:
    """Standard AP column names."""
    return [
        "Invoice Number",
        "Invoice Date",
        "Payment Date",
        "Vendor Name",
        "Vendor ID",
        "Amount",
        "Check Number",
        "Description",
        "GL Account",
        "Payment Method",
    ]
