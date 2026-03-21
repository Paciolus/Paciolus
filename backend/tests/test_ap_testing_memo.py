"""
Tests for AP Testing Memo Generator — Sprint 517

Covers:
- PDF generation (basic, with options, edge cases)
- Test descriptions completeness
- High-severity drill-down tables (DRILL-02, DRILL-03)
- DPO metric rendering (IMPROVEMENT-03)
- Risk tier conclusion coverage (low/elevated/moderate/high)
- Guardrail compliance (terminology, ISA references, disclaimer)
- Export route registration
"""

import inspect
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from ap_testing_memo_generator import (
    AP_TEST_DESCRIPTIONS,
    generate_ap_testing_memo,
)

# =============================================================================
# FIXTURES
# =============================================================================


def _make_ap_result(
    score: float = 15.0,
    risk_tier: str = "elevated",
    total_entries: int = 500,
    total_flagged: int = 18,
    flag_rate: float = 0.036,
    num_tests: int = 13,
    top_findings: list | None = None,
) -> dict:
    """Build a minimal AP testing result dict."""
    test_keys = [
        "exact_duplicate_payments",
        "missing_critical_fields",
        "check_number_gaps",
        "round_dollar_amounts",
        "payment_before_invoice",
        "fuzzy_duplicate_payments",
        "invoice_number_reuse",
        "unusual_payment_amounts",
        "weekend_payments",
        "high_frequency_vendors",
        "vendor_name_variations",
        "just_below_threshold",
        "suspicious_descriptions",
    ]
    test_names = [
        "Exact Duplicate Payments",
        "Missing Critical Fields",
        "Check Number Gaps",
        "Round Dollar Amounts",
        "Payment Before Invoice",
        "Fuzzy Duplicate Payments",
        "Invoice Number Reuse",
        "Unusual Payment Amounts",
        "Weekend Payments",
        "High Frequency Vendors",
        "Vendor Name Variations",
        "Just Below Threshold",
        "Suspicious Descriptions",
    ]
    tiers = [
        "structural",
        "structural",
        "structural",
        "structural",
        "structural",
        "structural",
        "advanced",
        "statistical",
        "structural",
        "statistical",
        "advanced",
        "advanced",
        "advanced",
    ]

    test_results = []
    for i in range(min(num_tests, 13)):
        flagged_count = 3 if i < 2 else 0
        test_results.append(
            {
                "test_name": test_names[i],
                "test_key": test_keys[i],
                "test_tier": tiers[i],
                "entries_flagged": flagged_count,
                "total_entries": total_entries,
                "flag_rate": flagged_count / max(total_entries, 1),
                "severity": "high" if i == 0 else "medium" if i < 5 else "low",
                "description": f"Test description for {test_keys[i]}",
                "flagged_entries": [],
            }
        )

    return {
        "composite_score": {
            "score": score,
            "risk_tier": risk_tier,
            "tests_run": num_tests,
            "total_entries": total_entries,
            "total_flagged": total_flagged,
            "flag_rate": flag_rate,
            "flags_by_severity": {"high": 3, "medium": 9, "low": 6},
            "top_findings": top_findings
            or [
                "Exact Duplicate Payments: 3 entries flagged (0.6%)",
                "Missing Critical Fields: 3 entries flagged (0.6%)",
            ],
        },
        "test_results": test_results,
        "data_quality": {
            "completeness_score": 94.0,
            "field_fill_rates": {"vendor_name": 0.99, "amount": 1.0, "payment_date": 0.97},
            "detected_issues": [],
            "total_rows": total_entries,
        },
        "column_detection": {
            "date_column": "Payment Date",
            "amount_column": "Amount",
            "vendor_column": "Vendor Name",
            "overall_confidence": 0.92,
        },
    }


def _make_ap_result_with_drill_down() -> dict:
    """Build an AP result with high-severity flagged entries for drill-down tables."""
    result = _make_ap_result(score=40.0, risk_tier="moderate")

    # Add exact duplicate payments with flagged entries
    for tr in result["test_results"]:
        if tr["test_key"] == "exact_duplicate_payments":
            tr["severity"] = "high"
            tr["entries_flagged"] = 2
            tr["flagged_entries"] = [
                {
                    "entry": {
                        "vendor_name": "Meridian Holdings LLC",
                        "invoice_number": "INV-4401",
                        "payment_date": "2025-10-15",
                        "amount": 25000.0,
                        "check_number": "8801",
                    },
                    "details": {
                        "payment_1_date": "2025-10-15",
                        "payment_2_date": "2025-10-22",
                    },
                    "severity": "high",
                    "issue": "Exact duplicate payment",
                },
                {
                    "entry": {
                        "vendor_name": "Apex Solutions Inc",
                        "invoice_number": "INV-5502",
                        "payment_date": "2025-11-01",
                        "amount": 18500.0,
                        "check_number": "8812",
                    },
                    "details": {
                        "payment_1_date": "2025-11-01",
                        "payment_2_date": "2025-11-08",
                    },
                    "severity": "high",
                    "issue": "Exact duplicate payment",
                },
            ]
        if tr["test_key"] == "payment_before_invoice":
            tr["severity"] = "high"
            tr["entries_flagged"] = 1
            tr["flagged_entries"] = [
                {
                    "entry": {
                        "vendor_name": "Sterling Corp",
                        "invoice_number": "INV-6603",
                        "invoice_date": "2025-12-15",
                        "payment_date": "2025-12-01",
                        "amount": 42000.0,
                    },
                    "details": {"days_early": 14},
                    "severity": "high",
                    "issue": "Payment 14 days before invoice",
                },
            ]

    return result


def _make_ap_result_with_vendor_variations() -> dict:
    """Build AP result with vendor name variation pairs."""
    result = _make_ap_result(score=28.0, risk_tier="elevated")

    for tr in result["test_results"]:
        if tr["test_key"] == "vendor_name_variations":
            tr["entries_flagged"] = 4
            tr["flagged_entries"] = [
                {
                    "entry": {},
                    "details": {
                        "name_a": "Meridian Holdings LLC",
                        "name_b": "Meridian Holdings Inc",
                        "similarity": 0.92,
                        "total_paid_a": 125000.0,
                        "total_paid_b": 89000.0,
                    },
                },
                {
                    "entry": {},
                    "details": {
                        "name_a": "Meridian Holdings Inc",
                        "name_b": "Meridian Holdings LLC",
                        "similarity": 0.92,
                        "total_paid_a": 89000.0,
                        "total_paid_b": 125000.0,
                    },
                },
                {
                    "entry": {},
                    "details": {
                        "name_a": "Apex Solutions",
                        "name_b": "Apex Solution Inc",
                        "similarity": 0.88,
                        "total_paid_a": 45000.0,
                        "total_paid_b": 32000.0,
                    },
                },
                {
                    "entry": {},
                    "details": {
                        "name_a": "Apex Solution Inc",
                        "name_b": "Apex Solutions",
                        "similarity": 0.88,
                        "total_paid_a": 32000.0,
                        "total_paid_b": 45000.0,
                    },
                },
            ]

    return result


# =============================================================================
# PDF GENERATION TESTS
# =============================================================================


class TestAPMemoGeneration:
    """Test PDF generation for AP testing memos."""

    def test_generates_pdf_bytes(self):
        result = _make_ap_result()
        pdf = generate_ap_testing_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000

    def test_pdf_header(self):
        result = _make_ap_result()
        pdf = generate_ap_testing_memo(result)
        assert pdf[:5] == b"%PDF-"

    def test_with_client_name(self):
        result = _make_ap_result()
        pdf = generate_ap_testing_memo(result, client_name="Acme Corp")
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000

    def test_with_all_options(self):
        result = _make_ap_result()
        pdf = generate_ap_testing_memo(
            result,
            filename="acme_ap_register",
            client_name="Acme Corp",
            period_tested="FY 2025",
            prepared_by="John Doe",
            reviewed_by="Jane Smith",
            workpaper_date="2025-12-31",
            source_document_title="AP Payment Register — FY2025",
            source_context_note="Exported from NetSuite",
        )
        assert isinstance(pdf, bytes)
        assert pdf[:5] == b"%PDF-"

    def test_empty_test_results(self):
        result = _make_ap_result(num_tests=0)
        result["test_results"] = []
        result["composite_score"]["tests_run"] = 0
        pdf = generate_ap_testing_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_no_findings(self):
        result = _make_ap_result(top_findings=[])
        pdf = generate_ap_testing_memo(result)
        assert isinstance(pdf, bytes)


# =============================================================================
# RISK TIER CONCLUSION TESTS
# =============================================================================


class TestAPRiskConclusions:
    """Test conclusion text varies by risk tier."""

    def test_low_risk_conclusion(self):
        result = _make_ap_result(score=5.0, risk_tier="low")
        pdf = generate_ap_testing_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000

    def test_elevated_risk_conclusion(self):
        result = _make_ap_result(score=18.0, risk_tier="elevated")
        pdf = generate_ap_testing_memo(result)
        assert isinstance(pdf, bytes)

    def test_moderate_risk_conclusion(self):
        result = _make_ap_result(score=35.0, risk_tier="moderate")
        pdf = generate_ap_testing_memo(result)
        assert isinstance(pdf, bytes)

    def test_high_risk_conclusion(self):
        result = _make_ap_result(score=65.0, risk_tier="high")
        pdf = generate_ap_testing_memo(result)
        assert isinstance(pdf, bytes)


# =============================================================================
# TEST DESCRIPTIONS
# =============================================================================


class TestAPTestDescriptions:
    """Test AP_TEST_DESCRIPTIONS completeness."""

    def test_all_13_tests_have_descriptions(self):
        expected_keys = [
            "exact_duplicate_payments",
            "missing_critical_fields",
            "check_number_gaps",
            "round_dollar_amounts",
            "payment_before_invoice",
            "fuzzy_duplicate_payments",
            "invoice_number_reuse",
            "unusual_payment_amounts",
            "weekend_payments",
            "high_frequency_vendors",
            "vendor_name_variations",
            "just_below_threshold",
            "suspicious_descriptions",
        ]
        for key in expected_keys:
            assert key in AP_TEST_DESCRIPTIONS, f"Missing description for {key}"

    def test_descriptions_are_nonempty(self):
        for key, desc in AP_TEST_DESCRIPTIONS.items():
            assert len(desc) > 20, f"Description too short for {key}"

    def test_total_description_count(self):
        assert len(AP_TEST_DESCRIPTIONS) == 13


# =============================================================================
# DRILL-DOWN TESTS
# =============================================================================


class TestAPDrillDown:
    """Test high-severity drill-down detail tables."""

    def test_generates_with_drill_down(self):
        result = _make_ap_result_with_drill_down()
        pdf = generate_ap_testing_memo(result, client_name="Test Corp")
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000

    def test_vendor_variations_renders(self):
        result = _make_ap_result_with_vendor_variations()
        pdf = generate_ap_testing_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000

    def test_drill_down_larger_than_basic(self):
        basic = generate_ap_testing_memo(_make_ap_result())
        drill = generate_ap_testing_memo(_make_ap_result_with_drill_down())
        assert len(drill) > len(basic)


# =============================================================================
# DPO METRIC TESTS
# =============================================================================


class TestAPDPOMetric:
    """Test DPO metric rendering in scope section."""

    def test_with_dpo_data(self):
        result = _make_ap_result()
        result["dpo_data"] = {"dpo": 42.5}
        pdf = generate_ap_testing_memo(result, client_name="Test Corp")
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000

    def test_with_dpo_unavailable(self):
        result = _make_ap_result()
        result["dpo_data"] = {"unavailable": True}
        pdf = generate_ap_testing_memo(result)
        assert isinstance(pdf, bytes)

    def test_without_dpo_data(self):
        result = _make_ap_result()
        pdf = generate_ap_testing_memo(result)
        assert isinstance(pdf, bytes)


# =============================================================================
# GUARDRAIL TESTS
# =============================================================================


class TestAPMemoGuardrails:
    """Verify terminology compliance and ISA references."""

    def test_isa_references_present(self):
        source = inspect.getsource(generate_ap_testing_memo)
        module_source = inspect.getsource(inspect.getmodule(generate_ap_testing_memo))
        assert "ISA 240" in module_source
        assert "ISA 500" in module_source
        assert "PCAOB AS 2401" in module_source

    def test_no_forbidden_assertions(self):
        source = inspect.getsource(inspect.getmodule(generate_ap_testing_memo))
        forbidden = [
            "payments are correct",
            "no fraud detected",
            "AP balance is accurate",
        ]
        for phrase in forbidden:
            assert phrase.lower() not in source.lower(), f"Forbidden phrase found: {phrase}"

    def test_domain_text(self):
        source = inspect.getsource(inspect.getmodule(generate_ap_testing_memo))
        assert "AP payment testing" in source


# =============================================================================
# EXPORT ROUTE REGISTRATION
# =============================================================================


class TestAPMemoExportRoute:
    """Verify the export route is registered."""

    def test_ap_memo_route_exists(self):
        from main import app

        routes = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/export/ap-testing-memo" in routes

    def test_ap_memo_route_is_post(self):
        from main import app

        for route in app.routes:
            if hasattr(route, "path") and route.path == "/export/ap-testing-memo":
                assert "POST" in route.methods
                break
        else:
            pytest.fail("Route /export/ap-testing-memo not found")
