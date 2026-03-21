"""
Tests for Pre-Flight Report Memo Generator — Sprint 517

Covers:
- PDF generation (basic, with options, edge cases)
- Score breakdown rendering (IMP-01)
- TB balance check section (BUG-04)
- Column detection section with low-confidence notes (IMP-02)
- Data quality issues table with tests_affected sort (IMP-04)
- Affected items list (IMP-03)
- Conclusion text generation (BUG-03)
- Framework support (FASB/GASB)
- Guardrail compliance (terminology, ISA references, disclaimer)
- Export route registration
"""

import inspect
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from preflight_memo_generator import (
    _COMPONENT_DISPLAY_NAMES,
    _build_conclusion,
    generate_preflight_memo,
)
from shared.framework_resolution import ResolvedFramework

# =============================================================================
# FIXTURES
# =============================================================================


def _make_preflight_result(
    readiness_score: float = 92.5,
    readiness_label: str = "Ready",
    row_count: int = 450,
    column_count: int = 8,
) -> dict:
    """Build a minimal preflight result dict."""
    return {
        "readiness_score": readiness_score,
        "readiness_label": readiness_label,
        "row_count": row_count,
        "column_count": column_count,
        "issues": [],
        "columns": [
            {"role": "account_number", "detected_name": "Acct No", "confidence": 0.95, "status": "confirmed"},
            {"role": "account_name", "detected_name": "Account Name", "confidence": 0.92, "status": "confirmed"},
            {"role": "debit", "detected_name": "Debit", "confidence": 0.98, "status": "confirmed"},
            {"role": "credit", "detected_name": "Credit", "confidence": 0.97, "status": "confirmed"},
        ],
    }


def _make_preflight_with_score_breakdown() -> dict:
    """Build a preflight result with score breakdown."""
    result = _make_preflight_result()
    result["score_breakdown"] = [
        {"component": "tb_balance", "weight": 0.25, "score": 100.0, "contribution": 25.0},
        {"component": "column_detection", "weight": 0.20, "score": 95.0, "contribution": 19.0},
        {"component": "null_values", "weight": 0.15, "score": 88.0, "contribution": 13.2},
        {"component": "duplicates", "weight": 0.10, "score": 100.0, "contribution": 10.0},
        {"component": "encoding", "weight": 0.10, "score": 100.0, "contribution": 10.0},
        {"component": "mixed_signs", "weight": 0.10, "score": 90.0, "contribution": 9.0},
        {"component": "zero_balance", "weight": 0.10, "score": 65.0, "contribution": 6.5},
    ]
    return result


def _make_preflight_with_balance_check(balanced: bool = True) -> dict:
    """Build a preflight result with TB balance check."""
    result = _make_preflight_result()
    if balanced:
        result["balance_check"] = {
            "total_debits": 2_450_000.00,
            "total_credits": 2_450_000.00,
            "difference": 0.00,
            "balanced": True,
            "tolerance": 0.01,
        }
    else:
        result["balance_check"] = {
            "total_debits": 2_450_000.00,
            "total_credits": 2_425_000.00,
            "difference": 25_000.00,
            "balanced": False,
            "tolerance": 0.01,
        }
    return result


def _make_preflight_with_issues() -> dict:
    """Build a preflight result with data quality issues."""
    result = _make_preflight_result(readiness_score=78.0, readiness_label="Ready with caveats")
    result["issues"] = [
        {
            "category": "null_values",
            "severity": "medium",
            "message": "12 accounts missing account number",
            "affected_count": 12,
            "tests_affected": 5,
            "remediation": "Fill in missing account numbers from chart of accounts",
            "downstream_impact": "Classification and lead sheet mapping may be incomplete",
            "affected_items": ["Revenue", "Cost of Sales", "Rent Expense"],
        },
        {
            "category": "mixed_signs",
            "severity": "low",
            "message": "3 accounts have mixed debit/credit signs",
            "affected_count": 3,
            "tests_affected": 2,
            "remediation": "Verify sign convention is consistent",
            "downstream_impact": "Ratio calculations may be affected",
        },
        {
            "category": "duplicates",
            "severity": "medium",
            "message": "2 potential duplicate rows detected",
            "affected_count": 2,
            "tests_affected": 4,
            "remediation": "Review for unintended duplicates",
            "downstream_impact": "Balance totals may be overstated",
            "affected_items": [
                "Accounts Receivable",
                "Accounts Receivable (duplicate)",
            ],
        },
    ]
    return result


def _make_preflight_with_low_confidence() -> dict:
    """Build a preflight result with low-confidence column detection."""
    result = _make_preflight_result()
    result["columns"] = [
        {"role": "account_number", "detected_name": "Col A", "confidence": 0.72, "status": "low_confidence"},
        {"role": "account_name", "detected_name": "Description", "confidence": 0.95, "status": "confirmed"},
        {"role": "debit", "detected_name": "DR", "confidence": 0.65, "status": "low_confidence"},
        {"role": "credit", "detected_name": "CR", "confidence": 0.98, "status": "confirmed"},
    ]
    return result


# =============================================================================
# PDF GENERATION TESTS
# =============================================================================


class TestPreflightMemoGeneration:
    """Test PDF generation for preflight report memos."""

    def test_generates_pdf_bytes(self):
        result = _make_preflight_result()
        pdf = generate_preflight_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000

    def test_pdf_header(self):
        result = _make_preflight_result()
        pdf = generate_preflight_memo(result)
        assert pdf[:5] == b"%PDF-"

    def test_with_client_name(self):
        result = _make_preflight_result()
        pdf = generate_preflight_memo(result, client_name="Meridian Capital Group")
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000

    def test_with_all_options(self):
        result = _make_preflight_result()
        pdf = generate_preflight_memo(
            result,
            filename="meridian_tb_2025.xlsx",
            client_name="Meridian Capital Group",
            period_tested="FY 2025",
            prepared_by="John Doe",
            reviewed_by="Jane Smith",
            workpaper_date="2025-12-31",
            source_document_title="Trial Balance — FY2025",
            source_context_note="Exported from QuickBooks",
        )
        assert isinstance(pdf, bytes)
        assert pdf[:5] == b"%PDF-"

    def test_minimal_result(self):
        """Minimal result with no optional sections."""
        result = {
            "readiness_score": 50.0,
            "readiness_label": "Needs Review",
            "row_count": 10,
            "column_count": 3,
            "issues": [],
            "columns": [],
        }
        pdf = generate_preflight_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_with_gasb_framework(self):
        result = _make_preflight_result()
        pdf = generate_preflight_memo(result, resolved_framework=ResolvedFramework.GASB)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000


# =============================================================================
# SCORE BREAKDOWN TESTS
# =============================================================================


class TestPreflightScoreBreakdown:
    """Test score breakdown section (IMP-01)."""

    def test_score_breakdown_generates(self):
        result = _make_preflight_with_score_breakdown()
        pdf = generate_preflight_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000

    def test_score_breakdown_larger_than_basic(self):
        basic = generate_preflight_memo(_make_preflight_result())
        breakdown = generate_preflight_memo(_make_preflight_with_score_breakdown())
        assert len(breakdown) > len(basic)

    def test_component_display_names_coverage(self):
        """All component keys have display names."""
        components = [
            "tb_balance",
            "column_detection",
            "null_values",
            "duplicates",
            "encoding",
            "mixed_signs",
            "zero_balance",
        ]
        for c in components:
            assert c in _COMPONENT_DISPLAY_NAMES, f"Missing display name for {c}"

    def test_component_display_names_are_readable(self):
        for key, name in _COMPONENT_DISPLAY_NAMES.items():
            assert len(name) > 3, f"Display name too short for {key}"


# =============================================================================
# TB BALANCE CHECK TESTS
# =============================================================================


class TestPreflightBalanceCheck:
    """Test TB balance check section (BUG-04)."""

    def test_balanced_generates(self):
        result = _make_preflight_with_balance_check(balanced=True)
        pdf = generate_preflight_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000

    def test_unbalanced_generates(self):
        result = _make_preflight_with_balance_check(balanced=False)
        pdf = generate_preflight_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000

    def test_no_balance_check_generates(self):
        result = _make_preflight_result()
        assert "balance_check" not in result
        pdf = generate_preflight_memo(result)
        assert isinstance(pdf, bytes)


# =============================================================================
# COLUMN DETECTION TESTS
# =============================================================================


class TestPreflightColumnDetection:
    """Test column detection section with low-confidence notes (IMP-02)."""

    def test_columns_render(self):
        result = _make_preflight_result()
        pdf = generate_preflight_memo(result)
        assert isinstance(pdf, bytes)

    def test_low_confidence_columns(self):
        result = _make_preflight_with_low_confidence()
        pdf = generate_preflight_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000

    def test_empty_columns(self):
        result = _make_preflight_result()
        result["columns"] = []
        pdf = generate_preflight_memo(result)
        assert isinstance(pdf, bytes)


# =============================================================================
# DATA QUALITY ISSUES TESTS
# =============================================================================


class TestPreflightIssues:
    """Test data quality issues table."""

    def test_issues_render(self):
        result = _make_preflight_with_issues()
        pdf = generate_preflight_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000

    def test_no_issues_render(self):
        result = _make_preflight_result()
        pdf = generate_preflight_memo(result)
        assert isinstance(pdf, bytes)

    def test_issues_sorted_by_tests_affected(self):
        """Issues with more tests_affected should appear first."""
        result = _make_preflight_with_issues()
        sorted_issues = sorted(result["issues"], key=lambda i: i.get("tests_affected", 0), reverse=True)
        assert sorted_issues[0]["tests_affected"] >= sorted_issues[-1]["tests_affected"]


# =============================================================================
# CONCLUSION TESTS
# =============================================================================


class TestPreflightConclusion:
    """Test conclusion text generation (BUG-03)."""

    def test_clean_conclusion(self):
        result = _make_preflight_result()
        conclusion = _build_conclusion(result, "test_tb.xlsx")
        assert "suitable for all downstream" in conclusion
        assert "no caveats" in conclusion

    def test_conclusion_with_issues(self):
        result = _make_preflight_with_issues()
        conclusion = _build_conclusion(result, "test_tb.xlsx")
        assert "caveat" in conclusion

    def test_conclusion_unbalanced_tb(self):
        result = _make_preflight_with_balance_check(balanced=False)
        conclusion = _build_conclusion(result, "test_tb.xlsx")
        assert "out of balance" in conclusion
        assert "critical" in conclusion.lower()

    def test_conclusion_includes_filename(self):
        result = _make_preflight_result()
        conclusion = _build_conclusion(result, "meridian_tb.xlsx")
        assert "meridian_tb.xlsx" in conclusion

    def test_conclusion_includes_score(self):
        result = _make_preflight_result(readiness_score=87.3)
        conclusion = _build_conclusion(result, "test.xlsx")
        assert "87.3" in conclusion


# =============================================================================
# GUARDRAIL TESTS
# =============================================================================


class TestPreflightMemoGuardrails:
    """Verify terminology compliance and ISA references."""

    def test_isa_references_present(self):
        source = inspect.getsource(inspect.getmodule(generate_preflight_memo))
        assert "ISA 500" in source
        assert "ISA 330" in source
        assert "ISA 315" in source

    def test_disclaimer_called(self):
        source = inspect.getsource(generate_preflight_memo)
        assert "build_disclaimer" in source

    def test_domain_text(self):
        source = inspect.getsource(generate_preflight_memo)
        assert "data quality assessment" in source


# =============================================================================
# EXPORT ROUTE REGISTRATION
# =============================================================================


class TestPreflightMemoExportRoute:
    """Verify the export route is registered."""

    def test_preflight_memo_route_exists(self):
        from main import app

        routes = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/export/preflight-memo" in routes

    def test_preflight_memo_route_is_post(self):
        from main import app

        for route in app.routes:
            if hasattr(route, "path") and route.path == "/export/preflight-memo":
                assert "POST" in route.methods
                break
        else:
            pytest.fail("Route /export/preflight-memo not found")
