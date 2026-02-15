"""
Tests for AP Testing Engine — Tier 2 Statistical Tests (Sprint 74)

Covers: T6 Fuzzy Duplicate Payments, T7 Invoice Number Reuse,
T8 Unusual Payment Amounts, T9 Weekend Payments,
T10 High-Frequency Vendors.

40 tests across 5 test classes.
"""

from ap_testing_engine import (
    APPayment,
    APTestingConfig,
    Severity,
    TestTier,
    detect_ap_columns,
    parse_ap_payments,
    test_fuzzy_duplicate_payments as run_fuzzy_duplicates_test,
    test_invoice_number_reuse as run_invoice_reuse_test,
    test_unusual_payment_amounts as run_unusual_amounts_test,
    test_weekend_payments as run_weekend_payments_test,
    test_high_frequency_vendors as run_high_frequency_test,
)


# =============================================================================
# FIXTURE HELPERS
# =============================================================================

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
        "Invoice Number", "Invoice Date", "Payment Date",
        "Vendor Name", "Vendor ID", "Amount",
        "Check Number", "Description", "GL Account", "Payment Method",
    ]


# =============================================================================
# TIER 2 TESTS — Sprint 74
# =============================================================================

class TestFuzzyDuplicatePayments:
    """8 tests for AP-T6: Fuzzy Duplicate Payments."""

    def test_no_fuzzy_duplicates(self):
        rows = sample_ap_rows()
        payments = make_payments(rows, sample_ap_columns())
        config = APTestingConfig()
        result = run_fuzzy_duplicates_test(payments, config)
        assert result.entries_flagged == 0
        assert result.test_key == "fuzzy_duplicate_payments"

    def test_same_vendor_same_amount_different_date(self):
        rows = [
            {"Vendor Name": "Acme Corp", "Amount": 5000, "Payment Date": "2025-01-10"},
            {"Vendor Name": "Acme Corp", "Amount": 5000, "Payment Date": "2025-01-20"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_fuzzy_duplicates_test(payments, config)
        assert result.entries_flagged == 2

    def test_outside_window_not_flagged(self):
        rows = [
            {"Vendor Name": "Acme Corp", "Amount": 5000, "Payment Date": "2025-01-01"},
            {"Vendor Name": "Acme Corp", "Amount": 5000, "Payment Date": "2025-03-15"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig(duplicate_days_window=30)
        result = run_fuzzy_duplicates_test(payments, config)
        assert result.entries_flagged == 0

    def test_different_amounts_not_flagged(self):
        rows = [
            {"Vendor Name": "Acme Corp", "Amount": 5000, "Payment Date": "2025-01-10"},
            {"Vendor Name": "Acme Corp", "Amount": 6000, "Payment Date": "2025-01-20"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_fuzzy_duplicates_test(payments, config)
        assert result.entries_flagged == 0

    def test_different_vendors_not_flagged(self):
        rows = [
            {"Vendor Name": "Acme Corp", "Amount": 5000, "Payment Date": "2025-01-10"},
            {"Vendor Name": "Beta LLC", "Amount": 5000, "Payment Date": "2025-01-20"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_fuzzy_duplicates_test(payments, config)
        assert result.entries_flagged == 0

    def test_high_severity_above_10k(self):
        rows = [
            {"Vendor Name": "Acme Corp", "Amount": 15000, "Payment Date": "2025-01-10"},
            {"Vendor Name": "Acme Corp", "Amount": 15000, "Payment Date": "2025-01-20"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_fuzzy_duplicates_test(payments, config)
        assert result.entries_flagged == 2
        for f in result.flagged_entries:
            assert f.severity == Severity.HIGH

    def test_medium_severity_below_10k(self):
        rows = [
            {"Vendor Name": "Acme Corp", "Amount": 5000, "Payment Date": "2025-01-10"},
            {"Vendor Name": "Acme Corp", "Amount": 5000, "Payment Date": "2025-01-20"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_fuzzy_duplicates_test(payments, config)
        for f in result.flagged_entries:
            assert f.severity == Severity.MEDIUM

    def test_test_tier_statistical(self):
        payments = make_payments(sample_ap_rows(), sample_ap_columns())
        config = APTestingConfig()
        result = run_fuzzy_duplicates_test(payments, config)
        assert result.test_tier == TestTier.STATISTICAL


class TestInvoiceNumberReuse:
    """8 tests for AP-T7: Invoice Number Reuse."""

    def test_no_reuse(self):
        rows = sample_ap_rows()
        payments = make_payments(rows, sample_ap_columns())
        config = APTestingConfig()
        result = run_invoice_reuse_test(payments, config)
        assert result.entries_flagged == 0
        assert result.test_key == "invoice_number_reuse"

    def test_same_invoice_different_vendors(self):
        rows = [
            {"Vendor Name": "Acme Corp", "Invoice Number": "INV-001", "Amount": 5000, "Payment Date": "2025-01-10"},
            {"Vendor Name": "Beta LLC", "Invoice Number": "INV-001", "Amount": 3000, "Payment Date": "2025-01-15"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Invoice Number", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_invoice_reuse_test(payments, config)
        assert result.entries_flagged == 2

    def test_same_invoice_same_vendor_not_flagged(self):
        rows = [
            {"Vendor Name": "Acme Corp", "Invoice Number": "INV-001", "Amount": 5000, "Payment Date": "2025-01-10"},
            {"Vendor Name": "Acme Corp", "Invoice Number": "INV-001", "Amount": 3000, "Payment Date": "2025-01-15"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Invoice Number", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_invoice_reuse_test(payments, config)
        assert result.entries_flagged == 0

    def test_always_high_severity(self):
        rows = [
            {"Vendor Name": "Acme Corp", "Invoice Number": "INV-001", "Amount": 100, "Payment Date": "2025-01-10"},
            {"Vendor Name": "Beta LLC", "Invoice Number": "INV-001", "Amount": 100, "Payment Date": "2025-01-15"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Invoice Number", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_invoice_reuse_test(payments, config)
        for f in result.flagged_entries:
            assert f.severity == Severity.HIGH

    def test_disabled(self):
        rows = [
            {"Vendor Name": "Acme Corp", "Invoice Number": "INV-001", "Amount": 5000, "Payment Date": "2025-01-10"},
            {"Vendor Name": "Beta LLC", "Invoice Number": "INV-001", "Amount": 3000, "Payment Date": "2025-01-15"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Invoice Number", "Amount", "Payment Date"])
        config = APTestingConfig(invoice_reuse_check=False)
        result = run_invoice_reuse_test(payments, config)
        assert result.entries_flagged == 0
        assert "disabled" in result.description.lower()

    def test_blank_invoices_ignored(self):
        rows = [
            {"Vendor Name": "Acme Corp", "Invoice Number": "", "Amount": 5000, "Payment Date": "2025-01-10"},
            {"Vendor Name": "Beta LLC", "Invoice Number": "", "Amount": 3000, "Payment Date": "2025-01-15"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Invoice Number", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_invoice_reuse_test(payments, config)
        assert result.entries_flagged == 0

    def test_case_insensitive(self):
        rows = [
            {"Vendor Name": "Acme Corp", "Invoice Number": "INV-001", "Amount": 5000, "Payment Date": "2025-01-10"},
            {"Vendor Name": "Beta LLC", "Invoice Number": "inv-001", "Amount": 3000, "Payment Date": "2025-01-15"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Invoice Number", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_invoice_reuse_test(payments, config)
        assert result.entries_flagged == 2

    def test_details_structure(self):
        rows = [
            {"Vendor Name": "Acme Corp", "Invoice Number": "INV-001", "Amount": 5000, "Payment Date": "2025-01-10"},
            {"Vendor Name": "Beta LLC", "Invoice Number": "INV-001", "Amount": 3000, "Payment Date": "2025-01-15"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Invoice Number", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_invoice_reuse_test(payments, config)
        d = result.flagged_entries[0].details
        assert "invoice_number" in d
        assert "vendor_count" in d
        assert "vendors" in d
        assert d["vendor_count"] == 2


class TestUnusualPaymentAmounts:
    """8 tests for AP-T8: Unusual Payment Amounts."""

    def _vendor_payments(self, amounts, vendor="Acme Corp"):
        rows = [
            {"Vendor Name": vendor, "Amount": a, "Payment Date": "2025-01-01"}
            for a in amounts
        ]
        return make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])

    def test_no_outliers(self):
        payments = self._vendor_payments([100, 105, 98, 102, 110])
        config = APTestingConfig()
        result = run_unusual_amounts_test(payments, config)
        assert result.entries_flagged == 0
        assert result.test_key == "unusual_payment_amounts"

    def test_outlier_detected(self):
        payments = self._vendor_payments([100, 100, 100, 100, 100, 100, 100, 10000])
        config = APTestingConfig(unusual_amount_stddev=2.0)
        result = run_unusual_amounts_test(payments, config)
        assert result.entries_flagged >= 1

    def test_min_payments_threshold(self):
        """Vendors with fewer than min_payments are skipped."""
        payments = self._vendor_payments([100, 100, 10000])
        config = APTestingConfig(unusual_amount_min_payments=5)
        result = run_unusual_amounts_test(payments, config)
        assert result.entries_flagged == 0

    def test_severity_tiers(self):
        # z>5 → HIGH, z>4 → MEDIUM, z>3 → LOW
        # Use very tight cluster with single extreme outlier
        base = [100] * 50
        base.append(1000000)  # massive outlier for guaranteed high z-score
        payments = self._vendor_payments(base)
        config = APTestingConfig(unusual_amount_stddev=3.0)
        result = run_unusual_amounts_test(payments, config)
        assert result.entries_flagged >= 1
        # The extreme outlier should be HIGH
        high_flags = [f for f in result.flagged_entries if f.severity == Severity.HIGH]
        assert len(high_flags) >= 1

    def test_all_same_amounts_no_flags(self):
        payments = self._vendor_payments([500, 500, 500, 500, 500])
        config = APTestingConfig()
        result = run_unusual_amounts_test(payments, config)
        assert result.entries_flagged == 0

    def test_per_vendor_analysis(self):
        """Each vendor analyzed independently."""
        rows = [
            {"Vendor Name": "Acme", "Amount": 100, "Payment Date": "2025-01-01"},
            {"Vendor Name": "Acme", "Amount": 100, "Payment Date": "2025-01-02"},
            {"Vendor Name": "Acme", "Amount": 100, "Payment Date": "2025-01-03"},
            {"Vendor Name": "Acme", "Amount": 100, "Payment Date": "2025-01-04"},
            {"Vendor Name": "Acme", "Amount": 100, "Payment Date": "2025-01-05"},
            {"Vendor Name": "Beta", "Amount": 50000, "Payment Date": "2025-01-01"},
            {"Vendor Name": "Beta", "Amount": 50000, "Payment Date": "2025-01-02"},
            {"Vendor Name": "Beta", "Amount": 50000, "Payment Date": "2025-01-03"},
            {"Vendor Name": "Beta", "Amount": 50000, "Payment Date": "2025-01-04"},
            {"Vendor Name": "Beta", "Amount": 50000, "Payment Date": "2025-01-05"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        # No outliers within each vendor
        result = run_unusual_amounts_test(payments, config)
        assert result.entries_flagged == 0

    def test_details_structure(self):
        base = [100] * 20
        base.append(100000)
        payments = self._vendor_payments(base)
        config = APTestingConfig(unusual_amount_stddev=3.0)
        result = run_unusual_amounts_test(payments, config)
        if result.entries_flagged > 0:
            d = result.flagged_entries[0].details
            assert "z_score" in d
            assert "vendor_mean" in d
            assert "vendor_stdev" in d
            assert "vendor_payment_count" in d

    def test_test_tier_statistical(self):
        payments = self._vendor_payments([100, 100, 100, 100, 100])
        config = APTestingConfig()
        result = run_unusual_amounts_test(payments, config)
        assert result.test_tier == TestTier.STATISTICAL


class TestWeekendPayments:
    """8 tests for AP-T9: Weekend Payments."""

    def test_no_weekend_payments(self):
        # 2025-01-06 is Monday, 2025-01-07 is Tuesday
        rows = [
            {"Vendor Name": "Acme", "Amount": 5000, "Payment Date": "2025-01-06"},
            {"Vendor Name": "Beta", "Amount": 3000, "Payment Date": "2025-01-07"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_weekend_payments_test(payments, config)
        assert result.entries_flagged == 0
        assert result.test_key == "weekend_payments"

    def test_saturday_flagged(self):
        # 2025-01-04 is Saturday
        rows = [{"Vendor Name": "Acme", "Amount": 5000, "Payment Date": "2025-01-04"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_weekend_payments_test(payments, config)
        assert result.entries_flagged == 1
        assert "Saturday" in result.flagged_entries[0].issue

    def test_sunday_flagged(self):
        # 2025-01-05 is Sunday
        rows = [{"Vendor Name": "Acme", "Amount": 5000, "Payment Date": "2025-01-05"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_weekend_payments_test(payments, config)
        assert result.entries_flagged == 1
        assert "Sunday" in result.flagged_entries[0].issue

    def test_high_severity_large_amount(self):
        # 2025-01-04 is Saturday
        rows = [{"Vendor Name": "Acme", "Amount": 15000, "Payment Date": "2025-01-04"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_weekend_payments_test(payments, config)
        assert result.flagged_entries[0].severity == Severity.HIGH

    def test_medium_severity_small_amount(self):
        # 2025-01-04 is Saturday
        rows = [{"Vendor Name": "Acme", "Amount": 500, "Payment Date": "2025-01-04"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_weekend_payments_test(payments, config)
        assert result.flagged_entries[0].severity == Severity.MEDIUM

    def test_disabled(self):
        # 2025-01-04 is Saturday
        rows = [{"Vendor Name": "Acme", "Amount": 15000, "Payment Date": "2025-01-04"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig(weekend_payment_enabled=False)
        result = run_weekend_payments_test(payments, config)
        assert result.entries_flagged == 0
        assert "disabled" in result.description.lower()

    def test_missing_date_skipped(self):
        rows = [{"Vendor Name": "Acme", "Amount": 5000, "Payment Date": ""}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_weekend_payments_test(payments, config)
        assert result.entries_flagged == 0

    def test_details_structure(self):
        # 2025-01-04 is Saturday
        rows = [{"Vendor Name": "Acme", "Amount": 5000, "Payment Date": "2025-01-04"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_weekend_payments_test(payments, config)
        d = result.flagged_entries[0].details
        assert "day_of_week" in d
        assert "payment_date" in d
        assert "amount" in d


class TestHighFrequencyVendors:
    """8 tests for AP-T10: High-Frequency Vendors."""

    def test_no_high_frequency(self):
        rows = sample_ap_rows()
        payments = make_payments(rows, sample_ap_columns())
        config = APTestingConfig()
        result = run_high_frequency_test(payments, config)
        assert result.entries_flagged == 0
        assert result.test_key == "high_frequency_vendors"

    def test_five_payments_same_day_flagged(self):
        rows = [
            {"Vendor Name": "Acme Corp", "Amount": 1000 * (i + 1), "Payment Date": "2025-01-10"}
            for i in range(5)
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_high_frequency_test(payments, config)
        assert result.entries_flagged == 5

    def test_below_threshold_not_flagged(self):
        rows = [
            {"Vendor Name": "Acme Corp", "Amount": 1000 * (i + 1), "Payment Date": "2025-01-10"}
            for i in range(4)
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_high_frequency_test(payments, config)
        assert result.entries_flagged == 0

    def test_different_days_not_flagged(self):
        rows = [
            {"Vendor Name": "Acme Corp", "Amount": 1000, "Payment Date": f"2025-01-{10+i:02d}"}
            for i in range(5)
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_high_frequency_test(payments, config)
        assert result.entries_flagged == 0

    def test_high_severity_ten_plus(self):
        rows = [
            {"Vendor Name": "Acme Corp", "Amount": 100 * (i + 1), "Payment Date": "2025-01-10"}
            for i in range(10)
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_high_frequency_test(payments, config)
        for f in result.flagged_entries:
            assert f.severity == Severity.HIGH

    def test_medium_severity_five_to_nine(self):
        rows = [
            {"Vendor Name": "Acme Corp", "Amount": 1000 * (i + 1), "Payment Date": "2025-01-10"}
            for i in range(6)
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_high_frequency_test(payments, config)
        for f in result.flagged_entries:
            assert f.severity == Severity.MEDIUM

    def test_disabled(self):
        rows = [
            {"Vendor Name": "Acme Corp", "Amount": 1000, "Payment Date": "2025-01-10"}
            for _ in range(10)
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig(high_frequency_vendor_enabled=False)
        result = run_high_frequency_test(payments, config)
        assert result.entries_flagged == 0
        assert "disabled" in result.description.lower()

    def test_details_structure(self):
        rows = [
            {"Vendor Name": "Acme Corp", "Amount": 1000 * (i + 1), "Payment Date": "2025-01-10"}
            for i in range(5)
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_high_frequency_test(payments, config)
        d = result.flagged_entries[0].details
        assert "vendor" in d
        assert "date" in d
        assert "daily_count" in d
        assert d["daily_count"] == 5
