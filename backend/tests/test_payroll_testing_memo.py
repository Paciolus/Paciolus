"""
Tests for Payroll Testing Memo Generator — Sprint 517

Covers:
- PDF generation (basic, with options, edge cases)
- Test descriptions completeness (PR-T1 through PR-T11)
- High-severity employee detail tables (BUG-02)
- GL reconciliation subsection (IMPROVEMENT-01)
- Headcount roll-forward subsection (IMPROVEMENT-02)
- Benford interpretation note (IMPROVEMENT-03)
- Department summary table (IMPROVEMENT-04)
- Risk tier conclusion coverage (low/elevated/moderate/high)
- Guardrail compliance (terminology, ISA references)
- Export route registration
"""

import inspect
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from payroll_testing_memo_generator import (
    PAYROLL_TEST_DESCRIPTIONS,
    _format_payroll_finding,
    generate_payroll_testing_memo,
)

# =============================================================================
# FIXTURES
# =============================================================================


def _make_payroll_result(
    score: float = 18.0,
    risk_tier: str = "elevated",
    total_entries: int = 800,
    total_flagged: int = 15,
    flag_rate: float = 0.019,
    num_tests: int = 11,
    top_findings: list | None = None,
) -> dict:
    """Build a minimal payroll testing result dict."""
    test_keys = [
        "PR-T1",
        "PR-T2",
        "PR-T3",
        "PR-T4",
        "PR-T5",
        "PR-T6",
        "PR-T7",
        "PR-T8",
        "PR-T9",
        "PR-T10",
        "PR-T11",
    ]
    test_names = [
        "Duplicate Employee IDs",
        "Missing Critical Fields",
        "Round Dollar Pay Amounts",
        "Pay After Termination",
        "Check Number Gaps",
        "Unusual Pay Amounts",
        "Irregular Pay Spacing",
        "Benford's Law Analysis",
        "Ghost Employee Indicators",
        "Duplicate Bank Accounts",
        "Duplicate Tax IDs",
    ]
    tiers = [
        "structural",
        "structural",
        "structural",
        "structural",
        "structural",
        "statistical",
        "statistical",
        "statistical",
        "advanced",
        "advanced",
        "advanced",
    ]

    test_results = []
    for i in range(min(num_tests, 11)):
        flagged_count = 2 if i < 2 else 0
        test_results.append(
            {
                "test_name": test_names[i],
                "test_key": test_keys[i],
                "test_tier": tiers[i],
                "entries_flagged": flagged_count,
                "total_entries": total_entries,
                "flag_rate": flagged_count / max(total_entries, 1),
                "severity": "high" if i == 3 else "medium" if i < 5 else "low",
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
            "flags_by_severity": {"high": 2, "medium": 6, "low": 7},
            "top_findings": top_findings
            or [
                "Duplicate Employee IDs: 2 entries flagged (0.3%)",
                "Missing Critical Fields: 2 entries flagged (0.3%)",
            ],
        },
        "test_results": test_results,
        "data_quality": {
            "completeness_score": 91.0,
            "field_fill_rates": {"employee_name": 0.98, "gross_pay": 1.0, "pay_date": 0.96},
            "detected_issues": [],
            "total_rows": total_entries,
        },
        "column_detection": {
            "date_column": "Pay Date",
            "amount_column": "Gross Pay",
            "employee_column": "Employee Name",
            "overall_confidence": 0.90,
        },
    }


def _make_payroll_result_with_gl_reconciliation() -> dict:
    """Build a payroll result with GL reconciliation data."""
    result = _make_payroll_result()
    result["payroll_register_total"] = 2_450_000.0
    result["gl_salaries_wages"] = 2_450_000.0
    return result


def _make_payroll_result_with_gl_variance() -> dict:
    """Build a payroll result with GL reconciliation variance."""
    result = _make_payroll_result()
    result["payroll_register_total"] = 2_450_000.0
    result["gl_salaries_wages"] = 2_425_000.0
    return result


def _make_payroll_result_with_headcount() -> dict:
    """Build a payroll result with headcount roll-forward."""
    result = _make_payroll_result()
    result["headcount_rollforward"] = {
        "period_start": "2025-01-01",
        "period_end": "2025-12-31",
        "beginning_headcount": 145,
        "new_hires": 32,
        "terminations": 18,
        "computed_ending": 159,
        "final_period_headcount": 157,
        "variance": 2,
    }
    return result


def _make_payroll_result_with_departments() -> dict:
    """Build a payroll result with department summary."""
    result = _make_payroll_result()
    result["department_summary"] = [
        {
            "department": "Engineering",
            "employee_count": 45,
            "total_gross_pay": 1_125_000.0,
            "pct_of_total": 45.9,
        },
        {
            "department": "Sales",
            "employee_count": 30,
            "total_gross_pay": 675_000.0,
            "pct_of_total": 27.6,
        },
        {
            "department": "Operations",
            "employee_count": 25,
            "total_gross_pay": 450_000.0,
            "pct_of_total": 18.4,
        },
        {
            "department": "Administration",
            "employee_count": 10,
            "total_gross_pay": 200_000.0,
            "pct_of_total": 8.2,
        },
    ]
    return result


def _make_payroll_result_with_high_severity() -> dict:
    """Build a payroll result with high-severity flagged entries."""
    result = _make_payroll_result(score=45.0, risk_tier="moderate")

    for tr in result["test_results"]:
        if tr["test_key"] == "PR-T4":
            tr["severity"] = "high"
            tr["entries_flagged"] = 2
            tr["flagged_entries"] = [
                {
                    "entry": {
                        "employee_id": "EMP-1042",
                        "employee_name": "John Anderson",
                        "term_date": "2025-08-15",
                        "pay_date": "2025-09-01",
                        "gross_pay": 4500.0,
                    },
                    "severity": "high",
                    "issue": "Payment after termination",
                },
                {
                    "entry": {
                        "employee_id": "EMP-1089",
                        "employee_name": "Sarah Mitchell",
                        "term_date": "2025-10-01",
                        "pay_date": "2025-10-15",
                        "gross_pay": 5200.0,
                    },
                    "severity": "high",
                    "issue": "Payment after termination",
                },
            ]
        if tr["test_key"] == "PR-T9":
            tr["severity"] = "high"
            tr["entries_flagged"] = 1
            tr["flagged_entries"] = [
                {
                    "entry": {
                        "employee_id": "EMP-2001",
                        "employee_name": "Unknown Employee",
                        "pay_date": "2025-12-31",
                        "gross_pay": 3800.0,
                    },
                    "details": {
                        "indicators": ["No department assignment", "Single entry only"],
                    },
                    "severity": "high",
                    "issue": "Ghost employee indicators",
                },
            ]

    return result


def _make_payroll_result_with_benford_pass() -> dict:
    """Build payroll result with Benford pass for interpretation note."""
    result = _make_payroll_result()
    for tr in result["test_results"]:
        if tr["test_key"] == "PR-T8":
            tr["entries_flagged"] = 0
            tr["flagged_entries"] = []
            tr["description"] = "First-digit analysis (MAD=0.0041, close conformity)"
    return result


# =============================================================================
# PDF GENERATION TESTS
# =============================================================================


class TestPayrollMemoGeneration:
    """Test PDF generation for payroll testing memos."""

    def test_generates_pdf_bytes(self):
        result = _make_payroll_result()
        pdf = generate_payroll_testing_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000

    def test_pdf_header(self):
        result = _make_payroll_result()
        pdf = generate_payroll_testing_memo(result)
        assert pdf[:5] == b"%PDF-"

    def test_with_client_name(self):
        result = _make_payroll_result()
        pdf = generate_payroll_testing_memo(result, client_name="Acme Corp")
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000

    def test_with_all_options(self):
        result = _make_payroll_result()
        pdf = generate_payroll_testing_memo(
            result,
            filename="acme_payroll_register",
            client_name="Acme Corp",
            period_tested="FY 2025",
            prepared_by="John Doe",
            reviewed_by="Jane Smith",
            workpaper_date="2025-12-31",
            source_document_title="Payroll Register — FY2025",
            source_context_note="Exported from ADP",
        )
        assert isinstance(pdf, bytes)
        assert pdf[:5] == b"%PDF-"

    def test_empty_test_results(self):
        result = _make_payroll_result(num_tests=0)
        result["test_results"] = []
        result["composite_score"]["tests_run"] = 0
        pdf = generate_payroll_testing_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_no_findings(self):
        result = _make_payroll_result(top_findings=[])
        pdf = generate_payroll_testing_memo(result)
        assert isinstance(pdf, bytes)


# =============================================================================
# RISK TIER CONCLUSION TESTS
# =============================================================================


class TestPayrollRiskConclusions:
    """Test conclusion text varies by risk tier."""

    def test_low_risk_conclusion(self):
        result = _make_payroll_result(score=4.0, risk_tier="low")
        pdf = generate_payroll_testing_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000

    def test_elevated_risk_conclusion(self):
        result = _make_payroll_result(score=18.0, risk_tier="elevated")
        pdf = generate_payroll_testing_memo(result)
        assert isinstance(pdf, bytes)

    def test_moderate_risk_conclusion(self):
        result = _make_payroll_result(score=35.0, risk_tier="moderate")
        pdf = generate_payroll_testing_memo(result)
        assert isinstance(pdf, bytes)

    def test_high_risk_conclusion(self):
        result = _make_payroll_result(score=60.0, risk_tier="high")
        pdf = generate_payroll_testing_memo(result)
        assert isinstance(pdf, bytes)


# =============================================================================
# TEST DESCRIPTIONS
# =============================================================================


class TestPayrollTestDescriptions:
    """Test PAYROLL_TEST_DESCRIPTIONS completeness."""

    def test_all_11_tests_have_descriptions(self):
        expected_keys = [
            "PR-T1",
            "PR-T2",
            "PR-T3",
            "PR-T4",
            "PR-T5",
            "PR-T6",
            "PR-T7",
            "PR-T8",
            "PR-T9",
            "PR-T10",
            "PR-T11",
        ]
        for key in expected_keys:
            assert key in PAYROLL_TEST_DESCRIPTIONS, f"Missing description for {key}"

    def test_descriptions_are_nonempty(self):
        for key, desc in PAYROLL_TEST_DESCRIPTIONS.items():
            assert len(desc) > 20, f"Description too short for {key}"

    def test_total_description_count(self):
        assert len(PAYROLL_TEST_DESCRIPTIONS) == 11


# =============================================================================
# GL RECONCILIATION TESTS
# =============================================================================


class TestPayrollGLReconciliation:
    """Test GL reconciliation subsection (IMPROVEMENT-01)."""

    def test_reconciled_generates(self):
        result = _make_payroll_result_with_gl_reconciliation()
        pdf = generate_payroll_testing_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000

    def test_variance_generates(self):
        result = _make_payroll_result_with_gl_variance()
        pdf = generate_payroll_testing_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000

    def test_no_gl_data_generates(self):
        result = _make_payroll_result()
        pdf = generate_payroll_testing_memo(result)
        assert isinstance(pdf, bytes)

    def test_register_total_without_gl(self):
        result = _make_payroll_result()
        result["payroll_register_total"] = 2_450_000.0
        # No gl_salaries_wages
        pdf = generate_payroll_testing_memo(result)
        assert isinstance(pdf, bytes)


# =============================================================================
# HEADCOUNT ROLL-FORWARD TESTS
# =============================================================================


class TestPayrollHeadcountRollforward:
    """Test headcount roll-forward subsection (IMPROVEMENT-02)."""

    def test_headcount_generates(self):
        result = _make_payroll_result_with_headcount()
        pdf = generate_payroll_testing_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000

    def test_no_headcount_generates(self):
        result = _make_payroll_result()
        pdf = generate_payroll_testing_memo(result)
        assert isinstance(pdf, bytes)


# =============================================================================
# DEPARTMENT SUMMARY TESTS
# =============================================================================


class TestPayrollDepartmentSummary:
    """Test department summary table (IMPROVEMENT-04)."""

    def test_department_summary_generates(self):
        result = _make_payroll_result_with_departments()
        pdf = generate_payroll_testing_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000

    def test_no_department_data_generates(self):
        result = _make_payroll_result()
        pdf = generate_payroll_testing_memo(result)
        assert isinstance(pdf, bytes)


# =============================================================================
# BENFORD INTERPRETATION TESTS
# =============================================================================


class TestPayrollBenfordInterpretation:
    """Test Benford's Law interpretation note (IMPROVEMENT-03)."""

    def test_benford_pass_generates(self):
        result = _make_payroll_result_with_benford_pass()
        pdf = generate_payroll_testing_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000


# =============================================================================
# HIGH SEVERITY DETAIL TESTS
# =============================================================================


class TestPayrollHighSeverityDetail:
    """Test high-severity employee detail tables (BUG-02)."""

    def test_generates_with_high_severity(self):
        result = _make_payroll_result_with_high_severity()
        pdf = generate_payroll_testing_memo(result, client_name="Test Corp")
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000

    def test_detail_larger_than_basic(self):
        basic = generate_payroll_testing_memo(_make_payroll_result())
        detail = generate_payroll_testing_memo(_make_payroll_result_with_high_severity())
        assert len(detail) > len(basic)

    def test_no_detail_when_no_high_severity(self):
        result = _make_payroll_result()
        pdf = generate_payroll_testing_memo(result)
        assert isinstance(pdf, bytes)


# =============================================================================
# FINDING FORMATTER TESTS
# =============================================================================


class TestPayrollFindingFormatter:
    """Test _format_payroll_finding helper."""

    def test_dict_finding_with_amount(self):
        finding = {"employee": "John Doe", "issue": "Pay after termination", "amount": 4500.0}
        formatted = _format_payroll_finding(finding)
        assert "John Doe" in formatted
        assert "$4,500.00" in formatted

    def test_dict_finding_without_amount(self):
        finding = {"employee": "Jane Smith", "issue": "Ghost employee indicator"}
        formatted = _format_payroll_finding(finding)
        assert "Jane Smith" in formatted
        assert "Ghost employee" in formatted

    def test_string_finding(self):
        finding = "PR-T4: 2 entries flagged"
        formatted = _format_payroll_finding(finding)
        assert formatted == finding

    def test_dict_finding_with_zero_amount(self):
        finding = {"employee": "Test User", "issue": "Missing fields", "amount": 0}
        formatted = _format_payroll_finding(finding)
        assert "Test User" in formatted
        assert "$" not in formatted


# =============================================================================
# GUARDRAIL TESTS
# =============================================================================


class TestPayrollMemoGuardrails:
    """Verify terminology compliance and ISA references."""

    def test_isa_references_present(self):
        source = inspect.getsource(inspect.getmodule(generate_payroll_testing_memo))
        assert "ISA 240" in source
        assert "ISA 500" in source
        assert "PCAOB AS 2401" in source

    def test_no_forbidden_assertions(self):
        source = inspect.getsource(inspect.getmodule(generate_payroll_testing_memo))
        forbidden = [
            "payroll is correct",
            "no fraud detected",
            "employees are legitimate",
        ]
        for phrase in forbidden:
            assert phrase.lower() not in source.lower(), f"Forbidden phrase found: {phrase}"

    def test_domain_text(self):
        source = inspect.getsource(inspect.getmodule(generate_payroll_testing_memo))
        assert "payroll testing" in source


# =============================================================================
# EXPORT ROUTE REGISTRATION
# =============================================================================


class TestPayrollMemoExportRoute:
    """Verify the export route is registered."""

    def test_payroll_memo_route_exists(self):
        from main import app

        routes = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/export/payroll-testing-memo" in routes

    def test_payroll_memo_route_is_post(self):
        from main import app

        for route in app.routes:
            if hasattr(route, "path") and route.path == "/export/payroll-testing-memo":
                assert "POST" in route.methods
                break
        else:
            pytest.fail("Route /export/payroll-testing-memo not found")
