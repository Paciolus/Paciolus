"""
Sprint 2: Tests for Shared Report Chrome (Cover Page + Page Footer).

Validates:
- ReportMetadata construction and frozen immutability
- find_logo() graceful fallback
- build_cover_page() produces flowables with and without logo
- build_cover_page() story ends with PageBreak
- draw_page_footer() canvas callback runs without error
- draw_page_header() canvas callback runs without error
- Regression: targeted generators still produce valid PDF bytes
- Cover metadata presence in generated PDFs
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.report_chrome import (
    ReportMetadata,
    build_cover_page,
    draw_page_footer,
    draw_page_header,
    find_logo,
)

# =============================================================================
# ReportMetadata
# =============================================================================


class TestReportMetadata:
    """Tests for ReportMetadata dataclass."""

    def test_construction_with_title_only(self):
        m = ReportMetadata(title="Test Report")
        assert m.title == "Test Report"
        assert m.subtitle == ""
        assert m.client_name == ""
        assert m.engagement_period == ""
        assert m.source_document == ""
        assert m.reference == ""

    def test_construction_with_all_fields(self):
        m = ReportMetadata(
            title="AP Testing Memo",
            subtitle="Phase 2 Review",
            client_name="Acme Corp",
            engagement_period="FY 2025",
            source_document="ap_data.csv",
            reference="APT-2025-0224-001",
        )
        assert m.title == "AP Testing Memo"
        assert m.client_name == "Acme Corp"
        assert m.reference == "APT-2025-0224-001"

    def test_frozen_immutability(self):
        m = ReportMetadata(title="Frozen")
        with pytest.raises(AttributeError):
            m.title = "Changed"


# =============================================================================
# find_logo
# =============================================================================


class TestFindLogo:
    """Tests for find_logo() utility."""

    def test_returns_string_or_none(self):
        result = find_logo()
        assert result is None or isinstance(result, str)

    def test_no_crash_when_logo_missing(self):
        """find_logo() should never raise, even if all paths miss."""
        # This test passes as long as find_logo() doesn't throw
        find_logo()


# =============================================================================
# build_cover_page
# =============================================================================


class TestBuildCoverPage:
    """Tests for build_cover_page() flowable generation."""

    def _get_styles(self):
        from shared.memo_base import create_memo_styles

        return create_memo_styles()

    def test_cover_page_without_logo(self):
        """Produces flowables with text lockup when logo_path=None."""
        styles = self._get_styles()
        story = []
        metadata = ReportMetadata(title="Test Report")
        build_cover_page(story, styles, metadata, 6.5 * 72, logo_path=None)
        assert len(story) > 0

    def test_cover_page_with_all_metadata(self):
        """All metadata fields populate the story."""
        styles = self._get_styles()
        story = []
        metadata = ReportMetadata(
            title="Full Report",
            subtitle="Subtitle Text",
            client_name="Client ABC",
            engagement_period="Q4 2025",
            source_document="data.csv",
            reference="REF-001",
        )
        build_cover_page(story, styles, metadata, 6.5 * 72, logo_path=None)
        assert len(story) > 3  # lockup + title + subtitle + rule + table + pagebreak

    def test_cover_page_ends_with_pagebreak(self):
        """Story must end with PageBreak so content starts on page 2."""
        from reportlab.platypus import PageBreak

        styles = self._get_styles()
        story = []
        metadata = ReportMetadata(title="Test Report")
        build_cover_page(story, styles, metadata, 6.5 * 72)
        assert isinstance(story[-1], PageBreak)

    def test_cover_page_with_classical_styles(self):
        """Works with create_classical_styles() (diagnostic PDF styles)."""
        from pdf_generator import create_classical_styles

        styles = create_classical_styles()
        story = []
        metadata = ReportMetadata(title="Diagnostic Report", subtitle="Sub")
        build_cover_page(story, styles, metadata, 6.5 * 72)
        assert len(story) > 0

    def test_cover_page_with_invalid_logo_path(self):
        """Gracefully falls back when logo path doesn't exist."""
        styles = self._get_styles()
        story = []
        metadata = ReportMetadata(title="Test Report")
        build_cover_page(story, styles, metadata, 6.5 * 72, logo_path="/nonexistent/logo.png")
        assert len(story) > 0


# =============================================================================
# draw_page_footer
# =============================================================================


class TestDrawPageFooter:
    """Tests for draw_page_footer() canvas callback."""

    def test_footer_does_not_crash(self):
        """Canvas callback runs without error on mock canvas."""
        canvas = MagicMock()
        canvas.stringWidth = MagicMock(return_value=200)
        doc = MagicMock()
        doc.page = 1
        draw_page_footer(canvas, doc)
        # Should have called drawCentredString at least twice (page num + disclaimer)
        assert canvas.drawCentredString.call_count >= 2

    def test_footer_page_number_format(self):
        """Footer renders page number in classical style."""
        canvas = MagicMock()
        doc = MagicMock()
        doc.page = 5
        draw_page_footer(canvas, doc)
        # Check that page 5 was rendered
        calls = [str(c) for c in canvas.drawCentredString.call_args_list]
        page_call = [c for c in calls if "5" in c]
        assert len(page_call) > 0


# =============================================================================
# draw_page_header
# =============================================================================


class TestDrawPageHeader:
    """Tests for draw_page_header() canvas callback."""

    def test_header_does_not_crash(self):
        """Canvas callback runs without error on mock canvas."""
        canvas = MagicMock()
        doc = MagicMock()
        draw_page_header(canvas, doc, title="Test", reference="REF-001")
        assert canvas.drawString.called or canvas.drawRightString.called

    def test_header_without_title(self):
        """Runs cleanly even with empty title/reference."""
        canvas = MagicMock()
        doc = MagicMock()
        draw_page_header(canvas, doc)


# =============================================================================
# Regression: Targeted generators still produce valid PDF bytes
# =============================================================================


class TestRegressionPdfGenerator:
    """Diagnostic PDF still generates after cover page integration."""

    def test_diagnostic_pdf(self):
        from pdf_generator import generate_audit_report

        result = {
            "balanced": True,
            "total_debits": 100000.0,
            "total_credits": 100000.0,
            "difference": 0.0,
            "row_count": 50,
            "materiality_threshold": 5000.0,
            "abnormal_balances": [],
            "risk_summary": {},
            "material_count": 0,
            "immaterial_count": 0,
        }
        pdf = generate_audit_report(result, "test_file")
        assert pdf[:5] == b"%PDF-"
        assert len(pdf) > 1000

    def test_diagnostic_pdf_with_anomalies(self):
        from pdf_generator import generate_audit_report

        result = {
            "balanced": False,
            "total_debits": 100000.0,
            "total_credits": 99000.0,
            "difference": 1000.0,
            "row_count": 50,
            "materiality_threshold": 500.0,
            "abnormal_balances": [
                {
                    "account": "Suspense",
                    "type": "Liability",
                    "issue": "Suspense account with balance",
                    "amount": 1000.0,
                    "materiality": "material",
                }
            ],
            "risk_summary": {"total_anomalies": 1, "high_severity": 1, "low_severity": 0},
            "material_count": 1,
            "immaterial_count": 0,
        }
        pdf = generate_audit_report(result, "test_anomalies", prepared_by="Auditor A")
        assert pdf[:5] == b"%PDF-"


class TestRegressionMemoTemplate:
    """Template-based memos still generate via AP as proxy."""

    def _make_result(self):
        return {
            "composite_score": {
                "score": 12.0,
                "risk_tier": "elevated",
                "total_entries": 200,
                "total_flagged": 8,
                "flag_rate": 0.04,
                "tests_run": 2,
                "flags_by_severity": {"high": 2, "medium": 4, "low": 2},
                "top_findings": [],
            },
            "test_results": [
                {
                    "test_key": "dup",
                    "test_name": "Dup Check",
                    "test_tier": "structural",
                    "entries_flagged": 3,
                    "flag_rate": 0.015,
                    "severity": "high",
                },
            ],
            "data_quality": {"completeness_score": 90.0},
        }

    def test_ap_memo(self):
        from ap_testing_memo_generator import generate_ap_testing_memo

        pdf = generate_ap_testing_memo(self._make_result(), client_name="TestCo")
        assert pdf[:5] == b"%PDF-"

    def test_je_memo(self):
        from je_testing_memo_generator import generate_je_testing_memo

        pdf = generate_je_testing_memo(self._make_result())
        assert pdf[:5] == b"%PDF-"


class TestRegressionPreflight:
    """Pre-flight memo still generates after cover page integration."""

    def test_preflight_memo(self):
        from preflight_memo_generator import generate_preflight_memo

        pf_result = {
            "readiness_score": 85,
            "readiness_label": "Good",
            "row_count": 100,
            "column_count": 6,
            "columns": [],
            "issues": [],
        }
        pdf = generate_preflight_memo(pf_result, client_name="TestCo")
        assert pdf[:5] == b"%PDF-"


class TestRegressionTWM:
    """Three-way match memo still generates after cover page integration."""

    def test_twm_memo(self):
        from three_way_match_memo_generator import generate_three_way_match_memo

        twm_result = {
            "summary": {
                "total_pos": 10,
                "total_invoices": 10,
                "total_receipts": 10,
                "full_match_count": 8,
                "partial_match_count": 1,
                "full_match_rate": 0.8,
                "partial_match_rate": 0.1,
                "material_variances_count": 1,
                "net_variance": 100.0,
                "risk_assessment": "low",
                "total_po_amount": 50000,
                "total_invoice_amount": 49900,
                "total_receipt_amount": 50000,
            },
            "variances": [],
            "config": {},
            "data_quality": {"overall_quality_score": 90},
            "unmatched_pos": [],
            "unmatched_invoices": [],
            "unmatched_receipts": [],
            "partial_matches": [],
        }
        pdf = generate_three_way_match_memo(twm_result, client_name="TestCo")
        assert pdf[:5] == b"%PDF-"


class TestRegressionMultiPeriod:
    """Multi-period memo still generates after cover page integration."""

    def test_multi_period_memo(self):
        from multi_period_memo_generator import generate_multi_period_memo

        mp_result = {
            "prior_label": "FY24",
            "current_label": "FY25",
            "total_accounts": 50,
            "movements_by_type": {"increase": 20, "decrease": 15},
            "movements_by_significance": {"material": 2, "significant": 5, "minor": 43},
            "significant_movements": [],
            "lead_sheet_summaries": [],
            "dormant_account_count": 0,
        }
        pdf = generate_multi_period_memo(
            mp_result,
            client_name="TestCo",
            period_tested="FY24 vs FY25",
            prepared_by="Auditor A",
        )
        assert pdf[:5] == b"%PDF-"


# =============================================================================
# Cover metadata presence (text extraction)
# =============================================================================


class TestCoverMetadataPresence:
    """Verify cover page is included by checking PDF structure.

    PDF text streams are compressed, so we verify indirectly:
    - Multi-page PDFs (cover adds a page)
    - PDF size is larger than a minimal document would be
    - The PDF is structurally valid (starts with %PDF-, ends with %%EOF)
    """

    def test_diagnostic_pdf_has_multiple_pages(self):
        """Cover page adds at least one extra page to the diagnostic PDF."""
        from pdf_generator import generate_audit_report

        result = {
            "balanced": True,
            "total_debits": 100000.0,
            "total_credits": 100000.0,
            "difference": 0.0,
            "row_count": 50,
            "materiality_threshold": 5000.0,
            "abnormal_balances": [],
            "risk_summary": {},
            "material_count": 0,
            "immaterial_count": 0,
        }
        pdf = generate_audit_report(result, "test_file")
        # Cover page = page 1, content starts on page 2+
        # Multiple /Page objects indicate multi-page
        assert pdf.count(b"/Type /Page") >= 2

    def test_memo_pdf_has_multiple_pages(self):
        """Cover page adds at least one extra page to template-based memos."""
        from ap_testing_memo_generator import generate_ap_testing_memo

        result = {
            "composite_score": {
                "score": 5.0,
                "risk_tier": "low",
                "total_entries": 100,
                "total_flagged": 1,
                "flag_rate": 0.01,
                "tests_run": 1,
                "flags_by_severity": {"high": 0, "medium": 1, "low": 0},
                "top_findings": [],
            },
            "test_results": [
                {
                    "test_key": "t1",
                    "test_name": "Test 1",
                    "test_tier": "structural",
                    "entries_flagged": 1,
                    "flag_rate": 0.01,
                    "severity": "medium",
                },
            ],
            "data_quality": {"completeness_score": 95.0},
        }
        pdf = generate_ap_testing_memo(result, client_name="Acme Corp")
        assert pdf.count(b"/Type /Page") >= 2

    def test_pdf_valid_structure(self):
        """Generated PDFs have valid PDF header and trailer."""
        from multi_period_memo_generator import generate_multi_period_memo

        result = {
            "prior_label": "FY24",
            "current_label": "FY25",
            "total_accounts": 10,
            "movements_by_type": {},
            "movements_by_significance": {},
            "significant_movements": [],
            "lead_sheet_summaries": [],
            "dormant_account_count": 0,
        }
        pdf = generate_multi_period_memo(result)
        assert pdf[:5] == b"%PDF-"
        assert pdf.rstrip().endswith(b"%%EOF")
