"""Three-Way Match anomaly generators.

Each generator injects a specific matching anomaly into clean PO, invoice,
and receipt data, returning AnomalyRecords describing the expected detection
outcome.
"""

from copy import deepcopy

from tests.anomaly_framework.base import AnomalyRecord


class TWMGeneratorBase:
    """Base class for three-way match anomaly generators."""

    name: str
    target_test_key: str

    def inject(
        self,
        po_rows: list[dict],
        invoice_rows: list[dict],
        receipt_rows: list[dict],
        seed: int = 42,
    ) -> tuple[list[dict], list[dict], list[dict], list[AnomalyRecord]]:
        raise NotImplementedError


class QuantityVarianceGenerator(TWMGeneratorBase):
    """Inject an invoice with quantity different from PO.

    Modifies an invoice to show more units than the PO authorized,
    simulating an over-shipment or billing discrepancy.
    """

    name = "quantity_variance"
    target_test_key = "quantity_variances"

    def inject(self, po_rows, invoice_rows, receipt_rows, seed=42):
        po_rows = deepcopy(po_rows)
        invoice_rows = deepcopy(invoice_rows)
        receipt_rows = deepcopy(receipt_rows)

        # Modify invoice for PO-3001: change quantity from 150 to 175
        for inv in invoice_rows:
            if inv["PO Number"] == "PO-3001":
                inv["Quantity"] = 175
                inv["Amount"] = 175 * inv["Unit Price"]  # 175 * 87.50 = 15312.50
                break

        record = AnomalyRecord(
            anomaly_type="quantity_variance",
            report_targets=["TWM-01"],
            injected_at="PO-3001: invoice qty=175 vs PO qty=150",
            expected_field="quantity_variances",
            expected_condition="items_count > 0",
            metadata={
                "po_number": "PO-3001",
                "po_quantity": 150,
                "invoice_quantity": 175,
                "variance": 25,
            },
        )
        return po_rows, invoice_rows, receipt_rows, [record]


class PriceVarianceGenerator(TWMGeneratorBase):
    """Inject an invoice with unit price different from PO.

    Modifies an invoice to have a higher unit price than authorized,
    simulating a price escalation or billing error.
    """

    name = "price_variance"
    target_test_key = "price_variances"

    def inject(self, po_rows, invoice_rows, receipt_rows, seed=42):
        po_rows = deepcopy(po_rows)
        invoice_rows = deepcopy(invoice_rows)
        receipt_rows = deepcopy(receipt_rows)

        # Modify invoice for PO-3002: change unit price from 425.00 to 475.00
        for inv in invoice_rows:
            if inv["PO Number"] == "PO-3002":
                inv["Unit Price"] = 475.00
                inv["Amount"] = inv["Quantity"] * 475.00  # 12 * 475 = 5700.00
                break

        record = AnomalyRecord(
            anomaly_type="price_variance",
            report_targets=["TWM-02"],
            injected_at="PO-3002: invoice price=$475.00 vs PO price=$425.00",
            expected_field="price_variances",
            expected_condition="items_count > 0",
            metadata={
                "po_number": "PO-3002",
                "po_unit_price": 425.00,
                "invoice_unit_price": 475.00,
                "variance": 50.00,
            },
        )
        return po_rows, invoice_rows, receipt_rows, [record]


class UnmatchedInvoiceGenerator(TWMGeneratorBase):
    """Inject an invoice with no matching purchase order.

    Adds an invoice that references a PO number not in the PO dataset,
    simulating an unauthorized purchase or data entry error.
    """

    name = "unmatched_invoice"
    target_test_key = "unmatched_invoices"

    def inject(self, po_rows, invoice_rows, receipt_rows, seed=42):
        po_rows = deepcopy(po_rows)
        invoice_rows = deepcopy(invoice_rows)
        receipt_rows = deepcopy(receipt_rows)

        invoice_rows.append(
            {
                "Invoice Number": "INV-7599",
                "Vendor Name": "Phantom Supply Corp",
                "PO Number": "PO-9999",
                "Description": "Specialty materials - rush order",
                "Quantity": 20,
                "Unit Price": 156.75,
                "Amount": 3135.00,
                "Invoice Date": "2025-06-12",
            }
        )

        record = AnomalyRecord(
            anomaly_type="unmatched_invoice",
            report_targets=["TWM-03"],
            injected_at="Invoice INV-7599 references non-existent PO-9999",
            expected_field="unmatched_invoices",
            expected_condition="items_count > 0",
            metadata={
                "invoice_number": "INV-7599",
                "po_reference": "PO-9999",
                "amount": 3135.00,
                "vendor": "Phantom Supply Corp",
            },
        )
        return po_rows, invoice_rows, receipt_rows, [record]


class MissingReceiptGenerator(TWMGeneratorBase):
    """Inject a PO + invoice combination with no receipt.

    Removes the receipt for an existing PO/invoice pair, simulating
    goods invoiced but never received (potential fictitious purchase).
    """

    name = "missing_receipt"
    target_test_key = "missing_receipts"

    def inject(self, po_rows, invoice_rows, receipt_rows, seed=42):
        po_rows = deepcopy(po_rows)
        invoice_rows = deepcopy(invoice_rows)
        receipt_rows = deepcopy(receipt_rows)

        # Remove receipt for PO-3004 (Ergonomic desk chairs)
        receipt_rows = [r for r in receipt_rows if r["PO Number"] != "PO-3004"]

        record = AnomalyRecord(
            anomaly_type="missing_receipt",
            report_targets=["TWM-04"],
            injected_at="PO-3004 has invoice INV-7504 but no receipt",
            expected_field="missing_receipts",
            expected_condition="items_count > 0",
            metadata={
                "po_number": "PO-3004",
                "invoice_number": "INV-7504",
                "amount": 7225.00,
                "vendor": "Meridian Office Solutions",
            },
        )
        return po_rows, invoice_rows, receipt_rows, [record]


TWM_REGISTRY: list[TWMGeneratorBase] = [
    QuantityVarianceGenerator(),
    PriceVarianceGenerator(),
    UnmatchedInvoiceGenerator(),
    MissingReceiptGenerator(),
]
