"""Base three-way match factory for anomaly testing.

Produces a valid, fully matched set of purchase orders, invoices, and receipts
using Meridian Capital Group naming conventions. All 8 POs have matching
invoices and receipts, yielding 100% three-way match with zero variances.

Key design decisions:
- All quantities match exactly across PO, invoice, and receipt
- All unit prices match exactly between PO and invoice
- All PO numbers are referenced consistently across documents
- Dates follow logical order: PO date < invoice date < receipt date
- Vendor names match exactly across all three document types
- Amounts are computed as quantity * unit_price for consistency
"""

# fmt: off
_PO_ROWS: list[dict] = [
    {"PO Number": "PO-3001", "Vendor Name": "Apex Industrial Supply",    "Description": "Structural steel beams - Grade A",      "Quantity": 150,  "Unit Price": 87.50,  "Amount": 13125.00, "PO Date": "2025-05-12"},
    {"PO Number": "PO-3002", "Vendor Name": "DataStream Technologies",   "Description": "Network switches - 48-port managed",    "Quantity": 12,   "Unit Price": 425.00, "Amount": 5100.00,  "PO Date": "2025-05-14"},
    {"PO Number": "PO-3003", "Vendor Name": "Greenfield Logistics",      "Description": "Pallet shipping - domestic standard",    "Quantity": 40,   "Unit Price": 62.75,  "Amount": 2510.00,  "PO Date": "2025-05-15"},
    {"PO Number": "PO-3004", "Vendor Name": "Meridian Office Solutions",  "Description": "Ergonomic desk chairs - model XR-9",    "Quantity": 25,   "Unit Price": 289.00, "Amount": 7225.00,  "PO Date": "2025-05-19"},
    {"PO Number": "PO-3005", "Vendor Name": "Pacific Coast Chemicals",   "Description": "Industrial solvent - 55 gal drums",     "Quantity": 8,    "Unit Price": 312.50, "Amount": 2500.00,  "PO Date": "2025-05-20"},
    {"PO Number": "PO-3006", "Vendor Name": "Summit Electric Co",        "Description": "LED panel lighting fixtures",            "Quantity": 100,  "Unit Price": 34.75,  "Amount": 3475.00,  "PO Date": "2025-05-22"},
    {"PO Number": "PO-3007", "Vendor Name": "Hartwell Paper Products",   "Description": "Copy paper - 20lb letter 10-ream case", "Quantity": 60,   "Unit Price": 42.95,  "Amount": 2577.00,  "PO Date": "2025-05-26"},
    {"PO Number": "PO-3008", "Vendor Name": "TechVault Systems",         "Description": "Server rack mount UPS 3000VA",          "Quantity": 4,    "Unit Price": 1875.00,"Amount": 7500.00,  "PO Date": "2025-05-28"},
]

_INVOICE_ROWS: list[dict] = [
    {"Invoice Number": "INV-7501", "Vendor Name": "Apex Industrial Supply",    "PO Number": "PO-3001", "Description": "Structural steel beams - Grade A",      "Quantity": 150,  "Unit Price": 87.50,  "Amount": 13125.00, "Invoice Date": "2025-06-02"},
    {"Invoice Number": "INV-7502", "Vendor Name": "DataStream Technologies",   "PO Number": "PO-3002", "Description": "Network switches - 48-port managed",    "Quantity": 12,   "Unit Price": 425.00, "Amount": 5100.00,  "Invoice Date": "2025-06-03"},
    {"Invoice Number": "INV-7503", "Vendor Name": "Greenfield Logistics",      "PO Number": "PO-3003", "Description": "Pallet shipping - domestic standard",    "Quantity": 40,   "Unit Price": 62.75,  "Amount": 2510.00,  "Invoice Date": "2025-06-04"},
    {"Invoice Number": "INV-7504", "Vendor Name": "Meridian Office Solutions",  "PO Number": "PO-3004", "Description": "Ergonomic desk chairs - model XR-9",    "Quantity": 25,   "Unit Price": 289.00, "Amount": 7225.00,  "Invoice Date": "2025-06-05"},
    {"Invoice Number": "INV-7505", "Vendor Name": "Pacific Coast Chemicals",   "PO Number": "PO-3005", "Description": "Industrial solvent - 55 gal drums",     "Quantity": 8,    "Unit Price": 312.50, "Amount": 2500.00,  "Invoice Date": "2025-06-06"},
    {"Invoice Number": "INV-7506", "Vendor Name": "Summit Electric Co",        "PO Number": "PO-3006", "Description": "LED panel lighting fixtures",            "Quantity": 100,  "Unit Price": 34.75,  "Amount": 3475.00,  "Invoice Date": "2025-06-09"},
    {"Invoice Number": "INV-7507", "Vendor Name": "Hartwell Paper Products",   "PO Number": "PO-3007", "Description": "Copy paper - 20lb letter 10-ream case", "Quantity": 60,   "Unit Price": 42.95,  "Amount": 2577.00,  "Invoice Date": "2025-06-10"},
    {"Invoice Number": "INV-7508", "Vendor Name": "TechVault Systems",         "PO Number": "PO-3008", "Description": "Server rack mount UPS 3000VA",          "Quantity": 4,    "Unit Price": 1875.00,"Amount": 7500.00,  "Invoice Date": "2025-06-11"},
]

_RECEIPT_ROWS: list[dict] = [
    {"Receipt Number": "RCV-4001", "PO Number": "PO-3001", "Description": "Structural steel beams - Grade A",      "Quantity": 150,  "Receipt Date": "2025-06-05"},
    {"Receipt Number": "RCV-4002", "PO Number": "PO-3002", "Description": "Network switches - 48-port managed",    "Quantity": 12,   "Receipt Date": "2025-06-06"},
    {"Receipt Number": "RCV-4003", "PO Number": "PO-3003", "Description": "Pallet shipping - domestic standard",    "Quantity": 40,   "Receipt Date": "2025-06-09"},
    {"Receipt Number": "RCV-4004", "PO Number": "PO-3004", "Description": "Ergonomic desk chairs - model XR-9",    "Quantity": 25,   "Receipt Date": "2025-06-10"},
    {"Receipt Number": "RCV-4005", "PO Number": "PO-3005", "Description": "Industrial solvent - 55 gal drums",     "Quantity": 8,    "Receipt Date": "2025-06-11"},
    {"Receipt Number": "RCV-4006", "PO Number": "PO-3006", "Description": "LED panel lighting fixtures",            "Quantity": 100,  "Receipt Date": "2025-06-12"},
    {"Receipt Number": "RCV-4007", "PO Number": "PO-3007", "Description": "Copy paper - 20lb letter 10-ream case", "Quantity": 60,   "Receipt Date": "2025-06-13"},
    {"Receipt Number": "RCV-4008", "PO Number": "PO-3008", "Description": "Server rack mount UPS 3000VA",          "Quantity": 4,    "Receipt Date": "2025-06-16"},
]
# fmt: on


def _verify_match(po_rows: list[dict], inv_rows: list[dict], rec_rows: list[dict]) -> None:
    """Raise if any PO lacks a matching invoice or receipt."""
    po_numbers = {r["PO Number"] for r in po_rows}
    inv_po_refs = {r["PO Number"] for r in inv_rows}
    rec_po_refs = {r["PO Number"] for r in rec_rows}

    missing_inv = po_numbers - inv_po_refs
    missing_rec = po_numbers - rec_po_refs
    assert not missing_inv, f"POs without invoices: {missing_inv}"
    assert not missing_rec, f"POs without receipts: {missing_rec}"

    # Verify quantity consistency
    for po in po_rows:
        po_num = po["PO Number"]
        inv = next(r for r in inv_rows if r["PO Number"] == po_num)
        rec = next(r for r in rec_rows if r["PO Number"] == po_num)
        assert po["Quantity"] == inv["Quantity"] == rec["Quantity"], (
            f"{po_num}: quantity mismatch PO={po['Quantity']} INV={inv['Quantity']} REC={rec['Quantity']}"
        )


# Validate at import time
_verify_match(_PO_ROWS, _INVOICE_ROWS, _RECEIPT_ROWS)


class BaseThreeWayMatchFactory:
    """Factory for clean, fully matched PO/invoice/receipt data."""

    @classmethod
    def as_po_rows(cls) -> list[dict]:
        """Return purchase order rows as list of dicts."""
        return [dict(r) for r in _PO_ROWS]

    @classmethod
    def po_column_names(cls) -> list[str]:
        """Return column names for purchase order data."""
        return list(_PO_ROWS[0].keys())

    @classmethod
    def as_invoice_rows(cls) -> list[dict]:
        """Return invoice rows as list of dicts."""
        return [dict(r) for r in _INVOICE_ROWS]

    @classmethod
    def invoice_column_names(cls) -> list[str]:
        """Return column names for invoice data."""
        return list(_INVOICE_ROWS[0].keys())

    @classmethod
    def as_receipt_rows(cls) -> list[dict]:
        """Return receipt rows as list of dicts."""
        return [dict(r) for r in _RECEIPT_ROWS]

    @classmethod
    def receipt_column_names(cls) -> list[str]:
        """Return column names for receipt data."""
        return list(_RECEIPT_ROWS[0].keys())
