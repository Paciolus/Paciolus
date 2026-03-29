"""AP Testing anomaly generators -- 13 detectors.

Each generator injects a specific anomaly pattern into clean AP payment
data and returns an AnomalyRecord describing the expected detection.

Generators that require large populations (500+ payments) are marked with
`requires_large_population = True` and are excluded from the small registry.
"""

from copy import deepcopy

from tests.anomaly_framework.base import AnomalyRecord


class APGeneratorBase:
    """Base class for AP anomaly generators."""

    name: str
    target_test_key: str
    requires_large_population: bool = False

    def inject(self, rows: list[dict], seed: int = 42) -> tuple[list[dict], list[AnomalyRecord]]:
        raise NotImplementedError


# =============================================================================
# Tier 1: Structural Tests (AP-T1 through AP-T5)
# =============================================================================


class APExactDuplicateGenerator(APGeneratorBase):
    """AP-T1: Inject an exact duplicate payment (same vendor, invoice, amount, date)."""

    name = "ap_exact_duplicate"
    target_test_key = "exact_duplicate_payments"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        # Duplicate the first payment exactly
        dup = dict(rows[0])
        rows.append(dup)
        record = AnomalyRecord(
            anomaly_type="ap_exact_duplicate",
            report_targets=["AP-T1"],
            injected_at=(f"Exact duplicate of invoice {dup['Invoice Number']} to {dup['Vendor Name']}"),
            expected_field="exact_duplicate_payments",
            expected_condition="entries_flagged > 0",
            metadata={"vendor": dup["Vendor Name"], "amount": dup["Amount"]},
        )
        return rows, [record]


class APMissingFieldsGenerator(APGeneratorBase):
    """AP-T2: Inject a payment with missing critical fields."""

    name = "ap_missing_fields"
    target_test_key = "missing_critical_fields"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        rows.append(
            {
                "Invoice Number": "INV-9901",
                "Invoice Date": "2025-07-01",
                "Payment Date": "",
                "Vendor Name": "",
                "Vendor ID": "",
                "Amount": 0,
                "Check Number": "10099",
                "Description": "Entry with missing required data",
                "GL Account": "6500",
                "Payment Method": "Check",
            }
        )
        record = AnomalyRecord(
            anomaly_type="ap_missing_fields",
            report_targets=["AP-T2"],
            injected_at="Payment with blank vendor_name, payment_date, and zero amount",
            expected_field="missing_critical_fields",
            expected_condition="entries_flagged > 0",
        )
        return rows, [record]


class APCheckNumberGapGenerator(APGeneratorBase):
    """AP-T3: Inject a gap in sequential check numbers."""

    name = "ap_check_number_gap"
    target_test_key = "check_number_gaps"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        # Add a payment with check number 10025, creating a gap from 10020
        rows.append(
            {
                "Invoice Number": "INV-9902",
                "Invoice Date": "2025-07-07",
                "Payment Date": "2025-07-15",
                "Vendor Name": "Meridian Office Solutions",
                "Vendor ID": "V-1001",
                "Amount": 1543.27,
                "Check Number": "10025",
                "Description": "Office furniture delivery and setup",
                "GL Account": "6500",
                "Payment Method": "Check",
            }
        )
        record = AnomalyRecord(
            anomaly_type="ap_check_number_gap",
            report_targets=["AP-T3"],
            injected_at="Check number gap: 10021-10024 missing (10020 -> 10025)",
            expected_field="check_number_gaps",
            expected_condition="entries_flagged > 0",
            metadata={"gap_start": 10021, "gap_end": 10024},
        )
        return rows, [record]


class APRoundDollarGenerator(APGeneratorBase):
    """AP-T4: Inject a round-dollar payment >= $10K."""

    name = "ap_round_dollar"
    target_test_key = "round_dollar_amounts"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        rows.append(
            {
                "Invoice Number": "INV-9903",
                "Invoice Date": "2025-07-02",
                "Payment Date": "2025-07-16",
                "Vendor Name": "Apex Technology Partners",
                "Vendor ID": "V-1002",
                "Amount": 50000.00,
                "Check Number": "10021",
                "Description": "Annual enterprise license renewal",
                "GL Account": "6250",
                "Payment Method": "Wire",
            }
        )
        record = AnomalyRecord(
            anomaly_type="ap_round_dollar",
            report_targets=["AP-T4"],
            injected_at="Payment of $50,000.00 (round amount >= $10K)",
            expected_field="round_dollar_amounts",
            expected_condition="entries_flagged > 0",
            metadata={"amount": 50000.00},
        )
        return rows, [record]


class APPaymentBeforeInvoiceGenerator(APGeneratorBase):
    """AP-T5: Inject a payment where payment_date < invoice_date."""

    name = "ap_payment_before_invoice"
    target_test_key = "payment_before_invoice"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        rows.append(
            {
                "Invoice Number": "INV-9904",
                "Invoice Date": "2025-07-15",
                "Payment Date": "2025-06-30",
                "Vendor Name": "Harborview Properties LLC",
                "Vendor ID": "V-1003",
                "Amount": 4327.60,
                "Check Number": "10021",
                "Description": "Facility deposit prepayment",
                "GL Account": "6100",
                "Payment Method": "ACH",
            }
        )
        record = AnomalyRecord(
            anomaly_type="ap_payment_before_invoice",
            report_targets=["AP-T5"],
            injected_at="Payment on 2025-06-30 before invoice dated 2025-07-15",
            expected_field="payment_before_invoice",
            expected_condition="entries_flagged > 0",
            metadata={"invoice_date": "2025-07-15", "payment_date": "2025-06-30"},
        )
        return rows, [record]


# =============================================================================
# Tier 2: Statistical Tests (AP-T6 through AP-T10)
# =============================================================================


class APFuzzyDuplicateGenerator(APGeneratorBase):
    """AP-T6: Inject a fuzzy duplicate (same vendor, similar amount, within 30 days)."""

    name = "ap_fuzzy_duplicate"
    target_test_key = "fuzzy_duplicate_payments"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        # Base row 0 is Meridian Office Solutions, $2347.85, paid 2025-06-16
        # Add a similar payment within 30 days with near-identical amount
        rows.append(
            {
                "Invoice Number": "INV-9905",
                "Invoice Date": "2025-06-25",
                "Payment Date": "2025-07-09",
                "Vendor Name": "Meridian Office Solutions",
                "Vendor ID": "V-1001",
                "Amount": 2347.85,
                "Check Number": "10021",
                "Description": "Q2 office supplies - supplemental order",
                "GL Account": "6500",
                "Payment Method": "Check",
            }
        )
        record = AnomalyRecord(
            anomaly_type="ap_fuzzy_duplicate",
            report_targets=["AP-T6"],
            injected_at=("Fuzzy duplicate: Meridian Office Solutions, $2,347.85, 23 days after original payment"),
            expected_field="fuzzy_duplicate_payments",
            expected_condition="entries_flagged > 0",
            metadata={"vendor": "Meridian Office Solutions", "amount": 2347.85},
        )
        return rows, [record]


class APInvoiceReuseGenerator(APGeneratorBase):
    """AP-T7: Inject an invoice number reused across different vendors."""

    name = "ap_invoice_reuse"
    target_test_key = "invoice_number_reuse"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        # Reuse INV-4201 (belongs to Meridian Office Solutions) with a different vendor
        rows.append(
            {
                "Invoice Number": "INV-4201",
                "Invoice Date": "2025-07-01",
                "Payment Date": "2025-07-15",
                "Vendor Name": "Cascade Industrial Supply",
                "Vendor ID": "V-1009",
                "Amount": 5432.10,
                "Check Number": "10021",
                "Description": "Industrial supplies order - July",
                "GL Account": "1300",
                "Payment Method": "Check",
            }
        )
        record = AnomalyRecord(
            anomaly_type="ap_invoice_reuse",
            report_targets=["AP-T7"],
            injected_at=("Invoice INV-4201 reused: Meridian Office Solutions and Cascade Industrial Supply"),
            expected_field="invoice_number_reuse",
            expected_condition="entries_flagged > 0",
            metadata={"invoice_number": "INV-4201"},
        )
        return rows, [record]


class APUnusualAmountGenerator(APGeneratorBase):
    """AP-T8: Inject a z-score outlier payment amount. Requires large population."""

    name = "ap_unusual_amount"
    target_test_key = "unusual_payment_amounts"
    requires_large_population = True

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        # Add several normal payments to Meridian Office Solutions to build a baseline
        for i in range(6):
            rows.append(
                {
                    "Invoice Number": f"INV-8{i:03d}",
                    "Invoice Date": f"2025-06-{10 + i:02d}",
                    "Payment Date": f"2025-06-{24 + i:02d}",
                    "Vendor Name": "Meridian Office Solutions",
                    "Vendor ID": "V-1001",
                    "Amount": 2300.00 + i * 15.50,
                    "Check Number": str(10021 + i),
                    "Description": f"Monthly supplies order #{i + 1}",
                    "GL Account": "6500",
                    "Payment Method": "Check",
                }
            )
        # Add a 10x outlier
        rows.append(
            {
                "Invoice Number": "INV-8099",
                "Invoice Date": "2025-07-01",
                "Payment Date": "2025-07-15",
                "Vendor Name": "Meridian Office Solutions",
                "Vendor ID": "V-1001",
                "Amount": 23478.50,
                "Check Number": "10027",
                "Description": "Bulk office furniture procurement",
                "GL Account": "6500",
                "Payment Method": "Wire",
            }
        )
        record = AnomalyRecord(
            anomaly_type="ap_unusual_amount",
            report_targets=["AP-T8"],
            injected_at="Payment of $23,478.50 to Meridian Office Solutions (10x normal)",
            expected_field="unusual_payment_amounts",
            expected_condition="entries_flagged > 0",
            metadata={"amount": 23478.50, "vendor": "Meridian Office Solutions"},
        )
        return rows, [record]


class APWeekendPaymentGenerator(APGeneratorBase):
    """AP-T9: Inject a payment processed on a weekend."""

    name = "ap_weekend_payment"
    target_test_key = "weekend_payments"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        # 2025-06-14 is a Saturday
        rows.append(
            {
                "Invoice Number": "INV-9906",
                "Invoice Date": "2025-06-09",
                "Payment Date": "2025-06-14",
                "Vendor Name": "Whitfield & Associates LLP",
                "Vendor ID": "V-1004",
                "Amount": 7891.35,
                "Check Number": "10021",
                "Description": "Legal consulting engagement - weekend processing",
                "GL Account": "6600",
                "Payment Method": "ACH",
            }
        )
        record = AnomalyRecord(
            anomaly_type="ap_weekend_payment",
            report_targets=["AP-T9"],
            injected_at="Payment on Saturday 2025-06-14",
            expected_field="weekend_payments",
            expected_condition="entries_flagged > 0",
            metadata={"payment_date": "2025-06-14", "day_of_week": "Saturday"},
        )
        return rows, [record]


class APHighFrequencyVendorGenerator(APGeneratorBase):
    """AP-T10: Inject many payments to one vendor on the same day. Requires large population."""

    name = "ap_high_frequency_vendor"
    target_test_key = "high_frequency_vendors"
    requires_large_population = True

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        # Add 6 payments to the same vendor on the same day
        for i in range(6):
            rows.append(
                {
                    "Invoice Number": f"INV-7{i:03d}",
                    "Invoice Date": "2025-07-01",
                    "Payment Date": "2025-07-14",
                    "Vendor Name": "Atlas Equipment Services",
                    "Vendor ID": "V-1012",
                    "Amount": 1234.56 + i * 100.25,
                    "Check Number": str(10021 + i),
                    "Description": f"Equipment service call #{i + 1} - July batch",
                    "GL Account": "6450",
                    "Payment Method": "Check",
                }
            )
        record = AnomalyRecord(
            anomaly_type="ap_high_frequency_vendor",
            report_targets=["AP-T10"],
            injected_at="6 payments to Atlas Equipment Services on 2025-07-14",
            expected_field="high_frequency_vendors",
            expected_condition="entries_flagged > 0",
            metadata={"vendor": "Atlas Equipment Services", "payment_count": 6},
        )
        return rows, [record]


# =============================================================================
# Tier 3: Fraud Indicators (AP-T11 through AP-T13)
# =============================================================================


class APVendorNameVariationGenerator(APGeneratorBase):
    """AP-T11: Inject similar vendor names suggesting ghost vendors."""

    name = "ap_vendor_name_variation"
    target_test_key = "vendor_name_variations"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        # "Apex Technology Partners" exists; add "Apex Technology Parnters" (typo)
        rows.append(
            {
                "Invoice Number": "INV-9907",
                "Invoice Date": "2025-07-02",
                "Payment Date": "2025-07-16",
                "Vendor Name": "Apex Technology Parnters",
                "Vendor ID": "V-1099",
                "Amount": 6543.20,
                "Check Number": "10021",
                "Description": "Server hosting and cloud services",
                "GL Account": "6250",
                "Payment Method": "ACH",
            }
        )
        record = AnomalyRecord(
            anomaly_type="ap_vendor_name_variation",
            report_targets=["AP-T11"],
            injected_at=("Vendor 'Apex Technology Parnters' similar to 'Apex Technology Partners' (deliberate typo)"),
            expected_field="vendor_name_variations",
            expected_condition="entries_flagged > 0",
            metadata={
                "original": "Apex Technology Partners",
                "variation": "Apex Technology Parnters",
            },
        )
        return rows, [record]


class APJustBelowThresholdGenerator(APGeneratorBase):
    """AP-T12: Inject a payment just below an approval threshold."""

    name = "ap_just_below_threshold"
    target_test_key = "just_below_threshold"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        # $9,950 is 0.5% below the $10,000 threshold (within 5% proximity)
        rows.append(
            {
                "Invoice Number": "INV-9908",
                "Invoice Date": "2025-07-03",
                "Payment Date": "2025-07-17",
                "Vendor Name": "National Indemnity Group",
                "Vendor ID": "V-1005",
                "Amount": 9950.00,
                "Check Number": "10021",
                "Description": "Supplemental coverage premium payment",
                "GL Account": "6400",
                "Payment Method": "Check",
            }
        )
        record = AnomalyRecord(
            anomaly_type="ap_just_below_threshold",
            report_targets=["AP-T12"],
            injected_at="Payment of $9,950.00 (just below $10K threshold)",
            expected_field="just_below_threshold",
            expected_condition="entries_flagged > 0",
            metadata={"amount": 9950.00, "threshold": 10000.00},
        )
        return rows, [record]


class APSuspiciousDescriptionGenerator(APGeneratorBase):
    """AP-T13: Inject a payment with suspicious keywords in description."""

    name = "ap_suspicious_description"
    target_test_key = "suspicious_descriptions"

    def inject(self, rows, seed=42):
        rows = deepcopy(rows)
        rows.append(
            {
                "Invoice Number": "INV-9909",
                "Invoice Date": "2025-07-07",
                "Payment Date": "2025-07-18",
                "Vendor Name": "Ironclad Security Group",
                "Vendor ID": "V-1015",
                "Amount": 15432.65,
                "Check Number": "10021",
                "Description": "Petty cash reimbursement - override approved",
                "GL Account": "1000",
                "Payment Method": "Check",
            }
        )
        record = AnomalyRecord(
            anomaly_type="ap_suspicious_description",
            report_targets=["AP-T13"],
            injected_at="Payment with 'petty cash' and 'override' keywords",
            expected_field="suspicious_descriptions",
            expected_condition="entries_flagged > 0",
            metadata={"keywords": ["petty cash", "override"]},
        )
        return rows, [record]


# =============================================================================
# Registries
# =============================================================================

AP_REGISTRY: list[APGeneratorBase] = [
    # Tier 1: Structural
    APExactDuplicateGenerator(),
    APMissingFieldsGenerator(),
    APCheckNumberGapGenerator(),
    APRoundDollarGenerator(),
    APPaymentBeforeInvoiceGenerator(),
    # Tier 2: Statistical
    APFuzzyDuplicateGenerator(),
    APInvoiceReuseGenerator(),
    APUnusualAmountGenerator(),
    APWeekendPaymentGenerator(),
    APHighFrequencyVendorGenerator(),
    # Tier 3: Fraud Indicators
    APVendorNameVariationGenerator(),
    APJustBelowThresholdGenerator(),
    APSuspiciousDescriptionGenerator(),
]

# Small-population-safe generators (work with 20-payment baseline)
AP_REGISTRY_SMALL = [g for g in AP_REGISTRY if not g.requires_large_population]
