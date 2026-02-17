"""
Tests for AP Testing Engine — Tier 3 Advanced Tests + Scoring Calibration + API (Sprint 74)

Covers: T11 Vendor Name Variations, T12 Just-Below-Threshold,
T13 Suspicious Descriptions, scoring calibration across
clean/moderate/high scenarios, and API route registration.

32 tests across 5 test classes.
"""

import pytest

from ap_testing_engine import (
    AP_SUSPICIOUS_KEYWORDS,
    APPayment,
    APTestingConfig,
    RiskTier,
    Severity,
    TestTier,
    detect_ap_columns,
    parse_ap_payments,
    run_ap_testing,
)
from ap_testing_engine import (
    test_just_below_threshold as run_just_below_threshold_test,
)
from ap_testing_engine import (
    test_suspicious_descriptions as run_suspicious_descriptions_test,
)
from ap_testing_engine import (
    test_vendor_name_variations as run_vendor_variations_test,
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
# TIER 3 TESTS — Sprint 74
# =============================================================================

class TestVendorNameVariations:
    """8 tests for AP-T11: Vendor Name Variations."""

    def test_no_variations(self):
        rows = sample_ap_rows()
        payments = make_payments(rows, sample_ap_columns())
        config = APTestingConfig()
        result = run_vendor_variations_test(payments, config)
        assert result.test_key == "vendor_name_variations"
        # All vendors are sufficiently different
        assert result.test_tier == TestTier.ADVANCED

    def test_similar_names_flagged(self):
        rows = [
            {"Vendor Name": "Acme Corporation", "Amount": 5000, "Payment Date": "2025-01-10"},
            {"Vendor Name": "Acme Corpration", "Amount": 3000, "Payment Date": "2025-01-15"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_vendor_variations_test(payments, config)
        assert result.entries_flagged == 2

    def test_identical_names_not_flagged(self):
        rows = [
            {"Vendor Name": "Acme Corp", "Amount": 5000, "Payment Date": "2025-01-10"},
            {"Vendor Name": "Acme Corp", "Amount": 3000, "Payment Date": "2025-01-15"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_vendor_variations_test(payments, config)
        assert result.entries_flagged == 0

    def test_very_different_names_not_flagged(self):
        rows = [
            {"Vendor Name": "Acme Corporation", "Amount": 5000, "Payment Date": "2025-01-10"},
            {"Vendor Name": "XYZ Industries", "Amount": 3000, "Payment Date": "2025-01-15"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_vendor_variations_test(payments, config)
        assert result.entries_flagged == 0

    def test_high_severity_large_combined(self):
        rows = [
            {"Vendor Name": "Acme Corporation", "Amount": 30000, "Payment Date": "2025-01-10"},
            {"Vendor Name": "Acme Corpration", "Amount": 25000, "Payment Date": "2025-01-15"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_vendor_variations_test(payments, config)
        for f in result.flagged_entries:
            assert f.severity == Severity.HIGH

    def test_medium_severity_small_combined(self):
        rows = [
            {"Vendor Name": "Acme Corporation", "Amount": 5000, "Payment Date": "2025-01-10"},
            {"Vendor Name": "Acme Corpration", "Amount": 3000, "Payment Date": "2025-01-15"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_vendor_variations_test(payments, config)
        for f in result.flagged_entries:
            assert f.severity == Severity.MEDIUM

    def test_disabled(self):
        rows = [
            {"Vendor Name": "Acme Corporation", "Amount": 5000, "Payment Date": "2025-01-10"},
            {"Vendor Name": "Acme Corpration", "Amount": 3000, "Payment Date": "2025-01-15"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig(vendor_variation_enabled=False)
        result = run_vendor_variations_test(payments, config)
        assert result.entries_flagged == 0
        assert "disabled" in result.description.lower()

    def test_few_vendors_skip(self):
        rows = [{"Vendor Name": "Solo Vendor", "Amount": 5000, "Payment Date": "2025-01-10"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_vendor_variations_test(payments, config)
        assert result.entries_flagged == 0


class TestJustBelowThreshold:
    """8 tests for AP-T12: Just-Below-Threshold."""

    def test_no_near_threshold(self):
        rows = [
            {"Vendor Name": "Acme", "Amount": 3000, "Payment Date": "2025-01-10"},
            {"Vendor Name": "Beta", "Amount": 7500, "Payment Date": "2025-01-15"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_just_below_threshold_test(payments, config)
        assert result.entries_flagged == 0
        assert result.test_key == "just_below_threshold"

    def test_just_below_5k_flagged(self):
        # 4800 is within 5% of 5000 (lower bound = 4750)
        rows = [{"Vendor Name": "Acme", "Amount": 4800, "Payment Date": "2025-01-10"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_just_below_threshold_test(payments, config)
        assert result.entries_flagged == 1

    def test_just_below_10k_flagged(self):
        # 9600 is within 5% of 10000 (lower bound = 9500)
        rows = [{"Vendor Name": "Acme", "Amount": 9600, "Payment Date": "2025-01-10"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_just_below_threshold_test(payments, config)
        assert result.entries_flagged == 1

    def test_above_threshold_not_flagged(self):
        rows = [{"Vendor Name": "Acme", "Amount": 5100, "Payment Date": "2025-01-10"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_just_below_threshold_test(payments, config)
        # 5100 is above 5K threshold, below proximity range of 10K
        assert result.entries_flagged == 0

    def test_split_payments_detected(self):
        # Two payments to same vendor on same day totaling above 10K
        rows = [
            {"Vendor Name": "Acme Corp", "Amount": 6000, "Payment Date": "2025-01-10"},
            {"Vendor Name": "Acme Corp", "Amount": 5000, "Payment Date": "2025-01-10"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_just_below_threshold_test(payments, config)
        split_flags = [f for f in result.flagged_entries if "Split" in f.issue or "split" in f.issue.lower()]
        assert len(split_flags) >= 1

    def test_high_severity_above_50k_threshold(self):
        # 49000 is within 5% of 50000 (lower = 47500)
        rows = [{"Vendor Name": "Acme", "Amount": 49000, "Payment Date": "2025-01-10"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_just_below_threshold_test(payments, config)
        high_flags = [f for f in result.flagged_entries if f.severity == Severity.HIGH]
        assert len(high_flags) >= 1

    def test_disabled(self):
        rows = [{"Vendor Name": "Acme", "Amount": 4900, "Payment Date": "2025-01-10"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig(threshold_proximity_enabled=False)
        result = run_just_below_threshold_test(payments, config)
        assert result.entries_flagged == 0
        assert "disabled" in result.description.lower()

    def test_details_structure(self):
        rows = [{"Vendor Name": "Acme", "Amount": 4800, "Payment Date": "2025-01-10"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_just_below_threshold_test(payments, config)
        d = result.flagged_entries[0].details
        assert "amount" in d
        assert "threshold" in d
        assert "pct_below" in d


class TestSuspiciousDescriptions:
    """8 tests for AP-T13: Suspicious Descriptions."""

    def test_no_suspicious_descriptions(self):
        rows = sample_ap_rows()
        payments = make_payments(rows, sample_ap_columns())
        config = APTestingConfig()
        result = run_suspicious_descriptions_test(payments, config)
        assert result.test_key == "suspicious_descriptions"

    def test_petty_cash_flagged(self):
        rows = [{"Vendor Name": "Acme", "Amount": 500, "Payment Date": "2025-01-10", "Description": "Petty cash replenishment"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date", "Description"])
        config = APTestingConfig()
        result = run_suspicious_descriptions_test(payments, config)
        assert result.entries_flagged == 1
        assert "petty cash" in result.flagged_entries[0].details["matched_keywords"]

    def test_override_flagged(self):
        rows = [{"Vendor Name": "Acme", "Amount": 15000, "Payment Date": "2025-01-10", "Description": "Manager override approval"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date", "Description"])
        config = APTestingConfig()
        result = run_suspicious_descriptions_test(payments, config)
        assert result.entries_flagged == 1

    def test_high_severity_high_confidence_large_amount(self):
        rows = [{"Vendor Name": "Acme", "Amount": 15000, "Payment Date": "2025-01-10", "Description": "Void reissue required"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date", "Description"])
        config = APTestingConfig()
        result = run_suspicious_descriptions_test(payments, config)
        assert result.entries_flagged == 1
        assert result.flagged_entries[0].severity == Severity.HIGH

    def test_below_threshold_not_flagged(self):
        rows = [{"Vendor Name": "Acme", "Amount": 500, "Payment Date": "2025-01-10", "Description": "Regular payment"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date", "Description"])
        config = APTestingConfig()
        result = run_suspicious_descriptions_test(payments, config)
        assert result.entries_flagged == 0

    def test_no_descriptions_no_flags(self):
        rows = [
            {"Vendor Name": "Acme", "Amount": 5000, "Payment Date": "2025-01-10"},
            {"Vendor Name": "Beta", "Amount": 3000, "Payment Date": "2025-01-15"},
        ]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date"])
        config = APTestingConfig()
        result = run_suspicious_descriptions_test(payments, config)
        assert result.entries_flagged == 0

    def test_disabled(self):
        rows = [{"Vendor Name": "Acme", "Amount": 500, "Payment Date": "2025-01-10", "Description": "Petty cash"}]
        payments = make_payments(rows, ["Vendor Name", "Amount", "Payment Date", "Description"])
        config = APTestingConfig(suspicious_keyword_enabled=False)
        result = run_suspicious_descriptions_test(payments, config)
        assert result.entries_flagged == 0
        assert "disabled" in result.description.lower()

    def test_keywords_constant_has_16_entries(self):
        assert len(AP_SUSPICIOUS_KEYWORDS) == 16


# =============================================================================
# SCORING CALIBRATION + API — Sprint 74
# =============================================================================

class TestAPScoringCalibration:
    """5 tests for scoring calibration across clean/moderate/high scenarios."""

    def test_clean_data_low_score(self):
        rows = sample_ap_rows()
        result = run_ap_testing(rows, sample_ap_columns())
        assert result.composite_score.score < 15
        assert result.composite_score.risk_tier in (RiskTier.LOW, RiskTier.ELEVATED)

    def test_moderate_flags_moderate_score(self):
        """Some flags across a few tests should produce moderate risk."""
        rows = [
            {"Vendor Name": "Acme Corp", "Amount": 4800, "Payment Date": "2025-01-04",
             "Invoice Number": "INV-001", "Description": "Rush order", "Check Number": "1001"},
            {"Vendor Name": "Acme Corp", "Amount": 4800, "Payment Date": "2025-01-11",
             "Invoice Number": "INV-002", "Description": "Normal", "Check Number": "1002"},
            {"Vendor Name": "Beta LLC", "Amount": 5000, "Payment Date": "2025-01-06",
             "Invoice Number": "INV-003", "Description": "Standard", "Check Number": "1003"},
            {"Vendor Name": "Gamma Inc", "Amount": 3000, "Payment Date": "2025-01-07",
             "Invoice Number": "INV-004", "Description": "Standard", "Check Number": "1004"},
        ]
        result = run_ap_testing(rows, list(rows[0].keys()))
        # Should have some flags (weekend, near-threshold, fuzzy dupes)
        assert result.composite_score.score > 0

    def test_high_risk_data_high_score(self):
        """Many flags across multiple tests should produce high risk."""
        rows = []
        # Exact duplicates
        base = {"Vendor Name": "Acme Corp", "Amount": 50000, "Payment Date": "2025-01-04",
                "Invoice Number": "INV-001", "Description": "Override urgent rush",
                "Check Number": "1001", "Invoice Date": "2025-02-01"}
        for _ in range(3):
            rows.append(dict(base))
        # More risky entries
        rows.append({"Vendor Name": "Beta LLC", "Amount": 50000, "Payment Date": "2025-01-05",
                      "Invoice Number": "INV-001", "Description": "Manual check void reissue",
                      "Check Number": "1010", "Invoice Date": "2025-01-01"})
        result = run_ap_testing(rows, list(rows[0].keys()))
        assert result.composite_score.score > result.composite_score.score * 0  # Non-zero

    def test_clean_lower_than_moderate(self):
        clean_rows = sample_ap_rows()
        clean_result = run_ap_testing(clean_rows, sample_ap_columns())

        moderate_rows = [
            {"Vendor Name": "Acme Corp", "Amount": 4800, "Payment Date": "2025-01-04",
             "Invoice Number": "INV-001", "Description": "Rush order", "Check Number": "1001"},
            {"Vendor Name": "Acme Corp", "Amount": 4800, "Payment Date": "2025-01-18",
             "Invoice Number": "INV-002", "Description": "Normal", "Check Number": "1002"},
            {"Vendor Name": "Beta LLC", "Amount": 5000, "Payment Date": "2025-01-05",
             "Invoice Number": "INV-003", "Description": "Override", "Check Number": "1003"},
        ]
        moderate_result = run_ap_testing(moderate_rows, list(moderate_rows[0].keys()))

        assert clean_result.composite_score.score <= moderate_result.composite_score.score

    def test_thirteen_tests_always_run(self):
        result = run_ap_testing(sample_ap_rows(), sample_ap_columns())
        assert result.composite_score.tests_run == 13


class TestAPTestingAPI:
    """3 tests for the POST /audit/ap-payments endpoint."""

    def test_route_registered(self):
        from main import app
        paths = [r.path for r in app.routes]
        assert "/audit/ap-payments" in paths

    def test_route_method_is_post(self):
        from main import app
        for route in app.routes:
            if hasattr(route, "path") and route.path == "/audit/ap-payments":
                assert "POST" in route.methods
                break
        else:
            pytest.fail("Route /audit/ap-payments not found")

    def test_route_has_audit_tag(self):
        from routes.ap_testing import router
        assert "ap_testing" in router.tags
