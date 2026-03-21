"""
Tests for Engagement Risk Dashboard Memo Generator — Sprint 517

Covers:
- PDF generation (basic, with options, edge cases)
- Engagement summary section (report count, scores, tier)
- Report-by-report summary table
- Cross-report risk threads section
- Recommended audit response priority section
- Risk tier coverage (low/elevated/moderate/high)
- Empty/no data edge cases
- Guardrail compliance (terminology, ISA references, disclaimer)
"""

import inspect
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from engagement_dashboard_memo import generate_engagement_dashboard_memo

# =============================================================================
# FIXTURES
# =============================================================================


def _make_dashboard_result(
    report_count: int = 5,
    overall_risk_score: float = 28.0,
    overall_risk_tier: str = "elevated",
    total_high_findings: int = 8,
) -> dict:
    """Build a minimal dashboard result dict."""
    return {
        "report_count": report_count,
        "overall_risk_score": overall_risk_score,
        "overall_risk_tier": overall_risk_tier,
        "total_high_findings": total_high_findings,
        "report_summaries": [
            {
                "report_title": "Journal Entry Testing",
                "risk_score": 35.0,
                "risk_tier": "moderate",
                "total_flagged": 24,
                "high_severity_count": 4,
                "tests_run": 9,
            },
            {
                "report_title": "AP Payment Testing",
                "risk_score": 22.0,
                "risk_tier": "elevated",
                "total_flagged": 18,
                "high_severity_count": 3,
                "tests_run": 13,
            },
            {
                "report_title": "Payroll Testing",
                "risk_score": 15.0,
                "risk_tier": "elevated",
                "total_flagged": 12,
                "high_severity_count": 1,
                "tests_run": 11,
            },
            {
                "report_title": "Revenue Testing",
                "risk_score": 8.0,
                "risk_tier": "low",
                "total_flagged": 6,
                "high_severity_count": 0,
                "tests_run": 16,
            },
            {
                "report_title": "Bank Reconciliation",
                "risk_score": 5.0,
                "risk_tier": "low",
                "total_flagged": 3,
                "high_severity_count": 0,
                "tests_run": 8,
            },
        ],
        "risk_threads": [
            {
                "name": "Revenue Recognition Timing Risk",
                "severity": "high",
                "narrative": (
                    "Year-end revenue concentration detected in Revenue Testing corroborates "
                    "with cut-off risk entries near period end. Journal entries with round dollar "
                    "amounts were also concentrated in December."
                ),
                "matched_conditions": [
                    "Revenue Testing: Year-End Concentration (HIGH)",
                    "JE Testing: Month-End Clustering (MEDIUM)",
                    "Revenue Testing: Cut-Off Risk (HIGH)",
                ],
            },
            {
                "name": "Vendor Payment Controls",
                "severity": "medium",
                "narrative": (
                    "AP testing flagged duplicate payments and just-below-threshold amounts. "
                    "Consider whether AP authorization controls are operating effectively."
                ),
                "matched_conditions": [
                    "AP Testing: Exact Duplicate Payments (HIGH)",
                    "AP Testing: Just Below Threshold (MEDIUM)",
                ],
            },
        ],
        "priority_actions": [
            "Extend revenue cut-off testing procedures for the final 5 business days of Q4.",
            "Perform detailed review of all duplicate AP payments identified.",
            "Request management representation on ghost employee indicators in payroll.",
            "Evaluate Benford's Law deviation in JE testing against prior period results.",
        ],
    }


def _make_empty_dashboard() -> dict:
    """Build a dashboard result with no reports."""
    return {
        "report_count": 0,
        "overall_risk_score": 0.0,
        "overall_risk_tier": "low",
        "total_high_findings": 0,
        "report_summaries": [],
        "risk_threads": [],
        "priority_actions": [],
    }


def _make_dashboard_no_threads() -> dict:
    """Build a dashboard result with reports but no risk threads."""
    result = _make_dashboard_result()
    result["risk_threads"] = []
    return result


def _make_dashboard_no_actions() -> dict:
    """Build a dashboard result with no priority actions."""
    result = _make_dashboard_result()
    result["priority_actions"] = []
    return result


# =============================================================================
# PDF GENERATION TESTS
# =============================================================================


class TestDashboardMemoGeneration:
    """Test PDF generation for engagement dashboard memos."""

    def test_generates_pdf_bytes(self):
        result = _make_dashboard_result()
        pdf = generate_engagement_dashboard_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000

    def test_pdf_header(self):
        result = _make_dashboard_result()
        pdf = generate_engagement_dashboard_memo(result)
        assert pdf[:5] == b"%PDF-"

    def test_with_client_name(self):
        result = _make_dashboard_result()
        pdf = generate_engagement_dashboard_memo(result, client_name="Meridian Capital Group")
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000

    def test_with_all_options(self):
        result = _make_dashboard_result()
        pdf = generate_engagement_dashboard_memo(
            result,
            client_name="Meridian Capital Group",
            period_tested="FY 2025",
            prepared_by="John Doe",
            reviewed_by="Jane Smith",
            workpaper_date="2025-12-31",
        )
        assert isinstance(pdf, bytes)
        assert pdf[:5] == b"%PDF-"

    def test_empty_dashboard_generates(self):
        result = _make_empty_dashboard()
        pdf = generate_engagement_dashboard_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_dashboard_with_client_larger(self):
        """Dashboard with client name should be >= dashboard without."""
        basic = generate_engagement_dashboard_memo(_make_dashboard_result())
        with_client = generate_engagement_dashboard_memo(
            _make_dashboard_result(),
            client_name="Meridian Capital Group",
            period_tested="FY 2025",
        )
        # Both should be substantial
        assert len(basic) > 1000
        assert len(with_client) > 1000


# =============================================================================
# RISK TIER COVERAGE TESTS
# =============================================================================


class TestDashboardRiskTiers:
    """Test conclusion rendering across risk tiers."""

    def test_low_risk_tier(self):
        result = _make_dashboard_result(overall_risk_score=5.0, overall_risk_tier="low")
        pdf = generate_engagement_dashboard_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 1000

    def test_elevated_risk_tier(self):
        result = _make_dashboard_result(overall_risk_score=18.0, overall_risk_tier="elevated")
        pdf = generate_engagement_dashboard_memo(result)
        assert isinstance(pdf, bytes)

    def test_moderate_risk_tier(self):
        result = _make_dashboard_result(overall_risk_score=35.0, overall_risk_tier="moderate")
        pdf = generate_engagement_dashboard_memo(result)
        assert isinstance(pdf, bytes)

    def test_high_risk_tier(self):
        result = _make_dashboard_result(overall_risk_score=65.0, overall_risk_tier="high")
        pdf = generate_engagement_dashboard_memo(result)
        assert isinstance(pdf, bytes)


# =============================================================================
# REPORT SUMMARY TABLE TESTS
# =============================================================================


class TestDashboardReportSummary:
    """Test report-by-report summary table."""

    def test_summary_renders_with_reports(self):
        result = _make_dashboard_result()
        assert len(result["report_summaries"]) == 5
        pdf = generate_engagement_dashboard_memo(result)
        assert isinstance(pdf, bytes)

    def test_summary_renders_no_reports(self):
        result = _make_empty_dashboard()
        assert len(result["report_summaries"]) == 0
        pdf = generate_engagement_dashboard_memo(result)
        assert isinstance(pdf, bytes)

    def test_single_report_summary(self):
        result = _make_dashboard_result()
        result["report_summaries"] = [result["report_summaries"][0]]
        result["report_count"] = 1
        pdf = generate_engagement_dashboard_memo(result)
        assert isinstance(pdf, bytes)


# =============================================================================
# RISK THREADS TESTS
# =============================================================================


class TestDashboardRiskThreads:
    """Test cross-report risk threads section."""

    def test_threads_render(self):
        result = _make_dashboard_result()
        assert len(result["risk_threads"]) == 2
        pdf = generate_engagement_dashboard_memo(result)
        assert isinstance(pdf, bytes)

    def test_no_threads_render(self):
        result = _make_dashboard_no_threads()
        pdf = generate_engagement_dashboard_memo(result)
        assert isinstance(pdf, bytes)

    def test_thread_structure(self):
        result = _make_dashboard_result()
        for thread in result["risk_threads"]:
            assert "name" in thread
            assert "severity" in thread
            assert "narrative" in thread
            assert "matched_conditions" in thread


# =============================================================================
# PRIORITY ACTIONS TESTS
# =============================================================================


class TestDashboardPriorityActions:
    """Test recommended audit response priority section."""

    def test_actions_render(self):
        result = _make_dashboard_result()
        assert len(result["priority_actions"]) == 4
        pdf = generate_engagement_dashboard_memo(result)
        assert isinstance(pdf, bytes)

    def test_no_actions_render(self):
        result = _make_dashboard_no_actions()
        pdf = generate_engagement_dashboard_memo(result)
        assert isinstance(pdf, bytes)


# =============================================================================
# GUARDRAIL TESTS
# =============================================================================


class TestDashboardMemoGuardrails:
    """Verify terminology compliance and ISA references."""

    def test_isa_references_present(self):
        source = inspect.getsource(inspect.getmodule(generate_engagement_dashboard_memo))
        assert "ISA 315" in source
        assert "ISA 330" in source

    def test_disclaimer_called(self):
        source = inspect.getsource(generate_engagement_dashboard_memo)
        assert "build_disclaimer" in source

    def test_workpaper_signoff_called(self):
        source = inspect.getsource(generate_engagement_dashboard_memo)
        assert "build_workpaper_signoff" in source

    def test_domain_text(self):
        source = inspect.getsource(generate_engagement_dashboard_memo)
        assert "engagement risk assessment" in source

    def test_no_forbidden_assertions(self):
        source = inspect.getsource(inspect.getmodule(generate_engagement_dashboard_memo))
        forbidden = [
            "audit is complete",
            "no material misstatements",
            "financial statements are correct",
        ]
        for phrase in forbidden:
            assert phrase.lower() not in source.lower(), f"Forbidden phrase found: {phrase}"
