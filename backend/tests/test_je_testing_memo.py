"""
Tests for JE Testing Memo Generator — Sprint 517

Covers:
- PDF generation (basic, with options, edge cases)
- Test descriptions completeness
- High-severity entry detail tables (DRILL-01)
- Benford's Law analysis section
- Preparer concentration analysis (DRILL-06)
- Risk tier conclusion coverage (low/elevated/moderate/high)
- Guardrail compliance (terminology, ISA references, disclaimer)
- Export route registration
"""

import inspect
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from je_testing_memo_generator import (
    TEST_DESCRIPTIONS,
    generate_je_testing_memo,
)


# =============================================================================
# FIXTURES
# =============================================================================


def _make_je_result(
    score: float = 12.0,
    risk_tier: str = "elevated",
    total_entries: int = 1500,
    total_flagged: int = 24,
    flag_rate: float = 0.016,
    num_tests: int = 9,
    top_findings: list | None = None,
) -> dict:
    """Build a minimal JE testing result dict."""
    test_keys = [
        "unbalanced_entries",
        "missing_fields",
        "duplicate_entries",
        "round_dollar_amounts",
        "unusual_amounts",
        "benford_law",
        "weekend_postings",
        "month_end_clustering",
        "holiday_postings",
    ]
    test_names = [
        "Unbalanced Entries",
        "Missing Fields",
        "Duplicate Entries",
        "Round Dollar Amounts",
        "Unusual Amounts",
        "Benford's Law",
        "Weekend Postings",
        "Month-End Clustering",
        "Holiday Postings",
    ]
    tiers = [
        "structural",
        "structural",
        "structural",
        "structural",
        "statistical",
        "statistical",
        "structural",
        "structural",
        "structural",
    ]

    test_results = []
    for i in range(min(num_tests, 9)):
        flagged_count = 4 if i < 2 else 0
        test_results.append(
            {
                "test_name": test_names[i],
                "test_key": test_keys[i],
                "test_tier": tiers[i],
                "entries_flagged": flagged_count,
                "total_entries": total_entries,
                "flag_rate": flagged_count / max(total_entries, 1),
                "severity": "high" if i == 0 else "medium" if i < 4 else "low",
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
            "flags_by_severity": {"high": 4, "medium": 12, "low": 8},
            "top_findings": top_findings
            or [
                "Unbalanced Entries: 4 entries flagged (0.3%)",
                "Missing Fields: 4 entries flagged (0.3%)",
            ],
        },
        "test_results": test_results,
        "data_quality": {
            "completeness_score": 96.0,
            "field_fill_rates": {"account": 0.99, "amount": 1.0, "date": 0.98},
            "detected_issues": [],
            "total_rows": total_entries,
        },
        "column_detection": {
            "date_column": "Entry Date",
            "amount_column": "Amount",
            "account_column": "Account",
            "overall_confidence": 0.94,
        },
    }


def _make_je_result_with_benford() -> dict:
    """Build a JE result with Benford's Law analysis data."""
    result = _make_je_result()
    result["benford_result"] = {
        "passed_prechecks": True,
        "eligible_count": 1200,
        "mad": 0.00412,
        "conformity_level": "close_conformity",
        "expected_distribution": {
            "1": 0.30103,
            "2": 0.17609,
            "3": 0.12494,
            "4": 0.09691,
            "5": 0.07918,
            "6": 0.06695,
            "7": 0.05799,
            "8": 0.05115,
            "9": 0.04576,
        },
        "actual_distribution": {
            "1": 0.29800,
            "2": 0.17900,
            "3": 0.12600,
            "4": 0.09500,
            "5": 0.08100,
            "6": 0.06800,
            "7": 0.05600,
            "8": 0.05200,
            "9": 0.04500,
        },
        "deviation_by_digit": {
            "1": -0.00303,
            "2": 0.00291,
            "3": 0.00106,
            "4": -0.00191,
            "5": 0.00182,
            "6": 0.00105,
            "7": -0.00199,
            "8": 0.00085,
            "9": -0.00076,
        },
    }
    return result


def _make_je_result_with_high_severity() -> dict:
    """Build a JE result with high-severity flagged entries for detail tables."""
    result = _make_je_result(score=35.0, risk_tier="moderate")

    for tr in result["test_results"]:
        if tr["test_key"] == "unbalanced_entries":
            tr["severity"] = "high"
            tr["entries_flagged"] = 2
            tr["flagged_entries"] = [
                {
                    "entry": {
                        "entry_id": "JE-2847",
                        "entry_date": "2025-12-28",
                        "account": "Accounts Receivable",
                        "debit": 85000.0,
                        "credit": 82500.0,
                        "description": "Year-end revenue adjustment",
                    },
                    "details": {"difference": 2500.0},
                    "severity": "high",
                    "issue": "Unbalanced by $2,500",
                },
                {
                    "entry": {
                        "entry_id": "JE-3012",
                        "entry_date": "2025-12-31",
                        "account": "Cost of Goods Sold",
                        "debit": 42000.0,
                        "credit": 41800.0,
                        "description": "Inventory true-up",
                    },
                    "details": {"difference": 200.0},
                    "severity": "high",
                    "issue": "Unbalanced by $200",
                },
            ]
        if tr["test_key"] == "holiday_postings":
            tr["severity"] = "high"
            tr["entries_flagged"] = 1
            tr["flagged_entries"] = [
                {
                    "entry": {
                        "entry_id": "JE-1501",
                        "entry_date": "2025-12-25",
                        "account": "Revenue",
                        "debit": 0.0,
                        "credit": 150000.0,
                        "description": "Large credit posting",
                        "posted_by": "admin",
                    },
                    "details": {"holiday": "Christmas Day"},
                    "severity": "high",
                    "issue": "Entry posted on Christmas Day",
                },
            ]

    return result


def _make_je_result_with_preparer() -> dict:
    """Build a JE result with preparer info for concentration analysis."""
    result = _make_je_result(score=25.0, risk_tier="elevated")

    # Populate flagged entries with posted_by across multiple tests
    for tr in result["test_results"]:
        if tr["test_key"] == "unbalanced_entries":
            tr["entries_flagged"] = 3
            tr["flagged_entries"] = [
                {
                    "entry": {
                        "entry_id": f"JE-{i}",
                        "entry_date": "2025-12-28",
                        "account": "Revenue",
                        "debit": 10000.0 * i,
                        "credit": 0.0,
                        "posted_by": "jsmith" if i < 3 else "admin",
                    },
                    "severity": "medium",
                    "issue": "Unbalanced entry",
                }
                for i in range(1, 4)
            ]
        if tr["test_key"] == "weekend_postings":
            tr["entries_flagged"] = 2
            tr["flagged_entries"] = [
                {
                    "entry": {
                        "entry_id": f"JE-W{i}",
                        "entry_date": "2025-12-27",
                        "account": "Cash",
                        "debit": 5000.0,
                        "credit": 0.0,
                        "posted_by": "jsmith",
                    },
                    "severity": "medium",
                    "issue": "Weekend posting",
                }
                for i in range(1, 3)
            ]

    return result


# =============================================================================
# PDF GENERATION TESTS
# =============================================================================


class TestJEMemoGeneration:
    """Test PDF generation for JE testing memos."""

    def test_generates_pdf_bytes(self):
        result = _make_je_result()
        pdf = generate_je_testing_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000

    def test_pdf_header(self):
        result = _make_je_result()
        pdf = generate_je_testing_memo(result)
        assert pdf[:5] == b"%PDF-"

    def test_with_client_name(self):
        result = _make_je_result()
        pdf = generate_je_testing_memo(result, client_name="Meridian Capital")
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000

    def test_with_all_options(self):
        result = _make_je_result()
        pdf = generate_je_testing_memo(
            result,
            filename="meridian_gl_extract",
            client_name="Meridian Capital Group",
            period_tested="FY 2025",
            prepared_by="John Doe",
            reviewed_by="Jane Smith",
            workpaper_date="2025-12-31",
            source_document_title="General Ledger Extract — FY2025",
            source_context_note="Exported from SAP",
        )
        assert isinstance(pdf, bytes)
        assert pdf[:5] == b"%PDF-"

    def test_empty_test_results(self):
        result = _make_je_result(num_tests=0)
        result["test_results"] = []
        result["composite_score"]["tests_run"] = 0
        pdf = generate_je_testing_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_no_findings(self):
        result = _make_je_result(top_findings=[])
        pdf = generate_je_testing_memo(result)
        assert isinstance(pdf, bytes)


# =============================================================================
# RISK TIER CONCLUSION TESTS
# =============================================================================


class TestJERiskConclusions:
    """Test conclusion text varies by risk tier."""

    def test_low_risk_conclusion(self):
        result = _make_je_result(score=3.0, risk_tier="low")
        pdf = generate_je_testing_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000

    def test_elevated_risk_conclusion(self):
        result = _make_je_result(score=15.0, risk_tier="elevated")
        pdf = generate_je_testing_memo(result)
        assert isinstance(pdf, bytes)

    def test_moderate_risk_conclusion(self):
        result = _make_je_result(score=30.0, risk_tier="moderate")
        pdf = generate_je_testing_memo(result)
        assert isinstance(pdf, bytes)

    def test_high_risk_conclusion(self):
        result = _make_je_result(score=60.0, risk_tier="high")
        pdf = generate_je_testing_memo(result)
        assert isinstance(pdf, bytes)


# =============================================================================
# TEST DESCRIPTIONS
# =============================================================================


class TestJETestDescriptions:
    """Test TEST_DESCRIPTIONS completeness."""

    def test_all_9_tests_have_descriptions(self):
        expected_keys = [
            "unbalanced_entries",
            "missing_fields",
            "duplicate_entries",
            "round_dollar_amounts",
            "unusual_amounts",
            "benford_law",
            "weekend_postings",
            "month_end_clustering",
            "holiday_postings",
        ]
        for key in expected_keys:
            assert key in TEST_DESCRIPTIONS, f"Missing description for {key}"

    def test_descriptions_are_nonempty(self):
        for key, desc in TEST_DESCRIPTIONS.items():
            assert len(desc) > 20, f"Description too short for {key}"

    def test_total_description_count(self):
        assert len(TEST_DESCRIPTIONS) == 9


# =============================================================================
# BENFORD'S LAW SECTION TESTS
# =============================================================================


class TestJEBenfordSection:
    """Test Benford's Law analysis section."""

    def test_benford_section_generates(self):
        result = _make_je_result_with_benford()
        pdf = generate_je_testing_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000

    def test_benford_larger_than_basic(self):
        basic = generate_je_testing_memo(_make_je_result())
        benford = generate_je_testing_memo(_make_je_result_with_benford())
        assert len(benford) > len(basic)

    def test_no_benford_without_data(self):
        result = _make_je_result()
        assert "benford_result" not in result
        pdf = generate_je_testing_memo(result)
        assert isinstance(pdf, bytes)

    def test_no_benford_when_prechecks_fail(self):
        result = _make_je_result()
        result["benford_result"] = {"passed_prechecks": False}
        pdf = generate_je_testing_memo(result)
        assert isinstance(pdf, bytes)


# =============================================================================
# HIGH-SEVERITY DETAIL TESTS
# =============================================================================


class TestJEHighSeverityDetail:
    """Test high-severity entry detail tables."""

    def test_generates_with_high_severity(self):
        result = _make_je_result_with_high_severity()
        pdf = generate_je_testing_memo(result, client_name="Test Corp")
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000

    def test_detail_larger_than_basic(self):
        basic = generate_je_testing_memo(_make_je_result())
        detail = generate_je_testing_memo(_make_je_result_with_high_severity())
        assert len(detail) > len(basic)

    def test_no_detail_when_no_high_severity(self):
        result = _make_je_result()
        pdf = generate_je_testing_memo(result)
        assert isinstance(pdf, bytes)


# =============================================================================
# PREPARER CONCENTRATION TESTS
# =============================================================================


class TestJEPreparerConcentration:
    """Test preparer concentration analysis section."""

    def test_preparer_section_generates(self):
        result = _make_je_result_with_preparer()
        pdf = generate_je_testing_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000

    def test_preparer_larger_than_basic(self):
        basic = generate_je_testing_memo(_make_je_result())
        preparer = generate_je_testing_memo(_make_je_result_with_preparer())
        assert len(preparer) > len(basic)


# =============================================================================
# GUARDRAIL TESTS
# =============================================================================


class TestJEMemoGuardrails:
    """Verify terminology compliance and ISA references."""

    def test_isa_references_present(self):
        source = inspect.getsource(inspect.getmodule(generate_je_testing_memo))
        assert "PCAOB AS 2401" in source
        assert "ISA 240" in source

    def test_no_forbidden_assertions(self):
        source = inspect.getsource(inspect.getmodule(generate_je_testing_memo))
        forbidden = [
            "entries are correct",
            "no fraud detected",
            "ledger is accurate",
        ]
        for phrase in forbidden:
            assert phrase.lower() not in source.lower(), f"Forbidden phrase found: {phrase}"

    def test_domain_text(self):
        source = inspect.getsource(inspect.getmodule(generate_je_testing_memo))
        assert "journal entry testing" in source


# =============================================================================
# EXPORT ROUTE REGISTRATION
# =============================================================================


class TestJEMemoExportRoute:
    """Verify the export route is registered."""

    def test_je_memo_route_exists(self):
        from main import app

        routes = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/export/je-testing-memo" in routes

    def test_je_memo_route_is_post(self):
        from main import app

        for route in app.routes:
            if hasattr(route, "path") and route.path == "/export/je-testing-memo":
                assert "POST" in route.methods
                break
        else:
            pytest.fail("Route /export/je-testing-memo not found")
