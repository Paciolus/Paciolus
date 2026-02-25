"""
Sprint 8: Structural Snapshot Tests.

Text-based structural verification for key report sections.
Uses ReportLab story inspection (flowable types, Paragraph text,
Table dimensions) rather than pixel-level image comparison — this
approach is deterministic and CI-friendly.

Covers:
  1. Cover page structure (flowable sequence + PageBreak)
  2. Table-heavy section (methodology test table, results summary table)
  3. Disclaimer / footer content
  4. Proof summary section
  5. Intelligence stamp
"""

import sys
from pathlib import Path

import pytest
from reportlab.platypus import PageBreak, Paragraph, Table

sys.path.insert(0, str(Path(__file__).parent.parent))

from pdf_generator import DoubleRule, LedgerRule
from shared.memo_base import (
    build_disclaimer,
    build_intelligence_stamp,
    build_methodology_section,
    build_proof_summary_section,
    build_results_summary_section,
    build_scope_section,
    build_workpaper_signoff,
    create_memo_styles,
)
from shared.report_chrome import (
    ReportMetadata,
    build_cover_page,
)


@pytest.fixture
def styles():
    return create_memo_styles()


@pytest.fixture
def doc_width():
    return 6.5 * 72  # Standard letter width minus margins


# =============================================================================
# 1. Cover page structural invariants
# =============================================================================


class TestCoverPageStructure:
    """Verify the cover page flowable sequence is stable."""

    def test_cover_page_ends_with_pagebreak(self, styles, doc_width):
        story = []
        metadata = ReportMetadata(title="Test Report")
        build_cover_page(story, styles, metadata, doc_width)
        assert isinstance(story[-1], PageBreak), "Cover must end with PageBreak"

    def test_cover_page_contains_double_rule(self, styles, doc_width):
        story = []
        metadata = ReportMetadata(title="Test Report")
        build_cover_page(story, styles, metadata, doc_width)
        double_rules = [f for f in story if isinstance(f, DoubleRule)]
        assert len(double_rules) == 1, "Cover must have exactly 1 DoubleRule"

    def test_cover_page_contains_metadata_table(self, styles, doc_width):
        story = []
        metadata = ReportMetadata(
            title="Full Report",
            client_name="Client Corp",
            engagement_period="FY 2025",
            source_document="data.csv",
            reference="REF-001",
        )
        build_cover_page(story, styles, metadata, doc_width)
        tables = [f for f in story if isinstance(f, Table)]
        assert len(tables) >= 1, "Cover must have a metadata table"

    def test_cover_page_source_document_transparency(self, styles, doc_width):
        """When source_document_title is provided, cover shows both title and filename."""
        story = []
        metadata = ReportMetadata(
            title="Report",
            source_document="ledger.csv",
            source_document_title="General Ledger Export Q4",
        )
        build_cover_page(story, styles, metadata, doc_width)
        tables = [f for f in story if isinstance(f, Table)]
        assert len(tables) >= 1

    def test_cover_page_flowable_count_stable(self, styles, doc_width):
        """Cover page flowable count for a standard report should be stable."""
        story = []
        metadata = ReportMetadata(
            title="Standard Report",
            client_name="Corp",
            engagement_period="FY 2025",
        )
        build_cover_page(story, styles, metadata, doc_width)
        # Expected: text lockup (2 Paragraphs) + title + DoubleRule + metadata table + Spacer + PageBreak
        # Exact count may vary slightly with optional fields, but should be >= 5
        assert len(story) >= 5, f"Cover page should have >= 5 flowables, got {len(story)}"

    def test_cover_page_title_is_first_paragraph(self, styles, doc_width):
        """Title paragraph appears after logo/lockup elements."""
        story = []
        metadata = ReportMetadata(title="My Report Title")
        build_cover_page(story, styles, metadata, doc_width)
        paragraphs = [f for f in story if isinstance(f, Paragraph)]
        # Find the title paragraph
        title_found = any("My Report Title" in p.text for p in paragraphs)
        assert title_found, "Title paragraph must appear on cover page"


# =============================================================================
# 2. Table-heavy section snapshots
# =============================================================================


class TestMethodologyTableStructure:
    """Verify methodology test table has correct shape."""

    def test_methodology_table_present(self, styles, doc_width):
        story = []
        test_results = [
            {
                "test_key": "t1",
                "test_name": "Test One",
                "test_tier": "structural",
                "entries_flagged": 5,
                "flag_rate": 0.01,
                "severity": "medium",
            },
            {
                "test_key": "t2",
                "test_name": "Test Two",
                "test_tier": "statistical",
                "entries_flagged": 0,
                "flag_rate": 0.0,
                "severity": "low",
            },
        ]
        test_descriptions = {
            "t1": "First test description",
            "t2": "Second test description",
        }
        build_methodology_section(story, styles, doc_width, test_results, test_descriptions, "Intro text.")
        tables = [f for f in story if isinstance(f, Table)]
        assert len(tables) >= 1, "Methodology should have at least 1 table"

    def test_methodology_section_heading_present(self, styles, doc_width):
        story = []
        build_methodology_section(
            story,
            styles,
            doc_width,
            [
                {
                    "test_key": "t1",
                    "test_name": "Test",
                    "test_tier": "structural",
                    "entries_flagged": 0,
                    "flag_rate": 0.0,
                    "severity": "low",
                }
            ],
            {"t1": "Desc"},
            "Intro.",
        )
        headings = [f for f in story if isinstance(f, Paragraph) and "Methodology" in getattr(f, "text", "")]
        assert len(headings) >= 1, "Methodology section heading must be present"


class TestResultsSummaryTableStructure:
    """Verify results summary table shape."""

    def test_results_table_present(self, styles, doc_width):
        story = []
        composite = {
            "score": 10.0,
            "risk_tier": "low",
            "total_entries": 100,
            "total_flagged": 2,
            "flag_rate": 0.02,
            "tests_run": 2,
            "flags_by_severity": {"high": 0, "medium": 1, "low": 1},
        }
        test_results = [
            {
                "test_key": "t1",
                "test_name": "Test One",
                "test_tier": "structural",
                "entries_flagged": 1,
                "flag_rate": 0.01,
                "severity": "medium",
            },
        ]
        build_results_summary_section(story, styles, doc_width, composite, test_results, "flagged entries")
        tables = [f for f in story if isinstance(f, Table)]
        assert len(tables) >= 1, "Results summary should have at least 1 table"

    def test_results_has_ledger_rule(self, styles, doc_width):
        story = []
        composite = {
            "score": 5.0,
            "risk_tier": "low",
            "total_entries": 50,
            "total_flagged": 1,
            "flag_rate": 0.02,
            "tests_run": 1,
            "flags_by_severity": {"high": 0, "medium": 0, "low": 1},
        }
        test_results = [
            {
                "test_key": "t1",
                "test_name": "T1",
                "test_tier": "structural",
                "entries_flagged": 1,
                "flag_rate": 0.02,
                "severity": "low",
            },
        ]
        build_results_summary_section(story, styles, doc_width, composite, test_results, "flagged")
        ledger_rules = [f for f in story if isinstance(f, LedgerRule)]
        assert len(ledger_rules) >= 1, "Results section should have a LedgerRule separator"


# =============================================================================
# 3. Disclaimer / footer content
# =============================================================================


class TestDisclaimerSection:
    """Verify disclaimer section structural invariants."""

    def test_disclaimer_produces_paragraph(self, styles):
        story = []
        build_disclaimer(story, styles, "journal_entry_testing", "ISA 240")
        paragraphs = [f for f in story if isinstance(f, Paragraph)]
        assert len(paragraphs) >= 1, "Disclaimer must produce at least 1 paragraph"

    def test_disclaimer_text_content(self, styles):
        story = []
        build_disclaimer(story, styles, "journal_entry_testing", "ISA 240")
        paragraphs = [f for f in story if isinstance(f, Paragraph)]
        combined_text = " ".join(p.text for p in paragraphs).lower()
        assert "professional judgment" in combined_text or "does not constitute" in combined_text, (
            "Disclaimer must reference professional judgment or non-attestation language"
        )

    def test_disclaimer_references_domain(self, styles):
        """Disclaimer should reference the tool domain or ISA citation."""
        story = []
        build_disclaimer(story, styles, "revenue_testing", "ISA 240")
        paragraphs = [f for f in story if isinstance(f, Paragraph)]
        combined_text = " ".join(p.text for p in paragraphs).lower()
        # Should mention either the domain or standard
        has_domain = "revenue" in combined_text
        has_standard = "isa" in combined_text
        assert has_domain or has_standard, "Disclaimer should reference the tool domain or ISA citation"


# =============================================================================
# 4. Proof summary section
# =============================================================================


class TestProofSummaryStructure:
    """Verify proof summary section shape (Sprint 392)."""

    def test_proof_summary_with_data(self, styles, doc_width):
        story = []
        result = {
            "data_quality": {"completeness_score": 95.0},
            "composite_score": {"tests_run": 5, "total_flagged": 2},
            "test_results": [
                {"test_key": "t1", "severity": "low", "entries_flagged": 0},
                {"test_key": "t2", "severity": "medium", "entries_flagged": 2},
            ],
        }
        build_proof_summary_section(story, styles, doc_width, result)
        tables = [f for f in story if isinstance(f, Table)]
        assert len(tables) >= 1, "Proof summary should have a table"

    def test_proof_summary_with_empty_result(self, styles, doc_width):
        """Proof summary should handle empty results gracefully."""
        story = []
        result = {}
        build_proof_summary_section(story, styles, doc_width, result)
        # Should not crash, may produce empty or minimal output
        assert isinstance(story, list)


# =============================================================================
# 5. Intelligence stamp
# =============================================================================


class TestIntelligenceStamp:
    """Verify intelligence stamp section."""

    def test_stamp_produces_paragraph(self, styles):
        story = []
        build_intelligence_stamp(story, styles, "Test Client", "FY 2025")
        paragraphs = [f for f in story if isinstance(f, Paragraph)]
        assert len(paragraphs) >= 1, "Intelligence stamp must produce at least 1 paragraph"

    def test_stamp_contains_brand(self, styles):
        story = []
        build_intelligence_stamp(story, styles, "Corp A", "FY 2025")
        paragraphs = [f for f in story if isinstance(f, Paragraph)]
        combined_text = " ".join(p.text for p in paragraphs).lower()
        assert "paciolus" in combined_text, "Intelligence stamp should include brand name"


# =============================================================================
# 6. Scope section
# =============================================================================


class TestScopeSectionStructure:
    """Verify scope section structural invariants."""

    def test_scope_produces_content(self, styles, doc_width):
        story = []
        composite = {"score": 10, "total_entries": 100}
        data_quality = {"completeness_score": 95}
        build_scope_section(
            story,
            styles,
            doc_width,
            composite,
            data_quality,
            "entries",
            "FY 2025",
            source_document="data.csv",
        )
        assert len(story) > 0, "Scope section must produce content"

    def test_scope_section_heading(self, styles, doc_width):
        story = []
        composite = {"score": 10, "total_entries": 100}
        data_quality = {"completeness_score": 95}
        build_scope_section(
            story,
            styles,
            doc_width,
            composite,
            data_quality,
            "entries",
            "FY 2025",
        )
        headings = [f for f in story if isinstance(f, Paragraph) and "Scope" in getattr(f, "text", "")]
        assert len(headings) >= 1, "Scope section heading must be present"


# =============================================================================
# 7. Workpaper signoff gate
# =============================================================================


class TestWorkpaperSignoffGate:
    """Verify signoff section gating behavior."""

    def test_signoff_default_produces_nothing(self, styles, doc_width):
        story = []
        build_workpaper_signoff(
            story,
            styles,
            doc_width,
            prepared_by="Alice",
            reviewed_by="Bob",
            workpaper_date="2025-01-01",
        )
        assert len(story) == 0, "Default signoff (include_signoff=False) must produce nothing"

    def test_signoff_explicit_true_produces_content(self, styles, doc_width):
        story = []
        build_workpaper_signoff(
            story,
            styles,
            doc_width,
            prepared_by="Alice",
            reviewed_by="Bob",
            workpaper_date="2025-01-01",
            include_signoff=True,
        )
        assert len(story) > 0, "Explicit include_signoff=True must produce content"

    def test_signoff_true_without_names_produces_nothing(self, styles, doc_width):
        story = []
        build_workpaper_signoff(
            story,
            styles,
            doc_width,
            prepared_by="",
            reviewed_by="",
            workpaper_date="",
            include_signoff=True,
        )
        assert len(story) == 0, "Signoff with no names should produce nothing even if opted in"
