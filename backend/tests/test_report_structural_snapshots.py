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
    build_assertion_summary,
    build_auditor_conclusion_block,
    build_disclaimer,
    build_intelligence_stamp,
    build_methodology_section,
    build_proof_summary_section,
    build_results_summary_section,
    build_scope_section,
    build_skipped_tests_section,
    build_structured_findings_table,
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


# =============================================================================
# 8. Auditor conclusion block
# =============================================================================


class TestAuditorConclusionBlock:
    """Verify practitioner assessment block structural invariants."""

    def test_auditor_conclusion_block_renders(self, styles, doc_width):
        """Block should produce heading, instruction paragraph, ruled lines, and signature."""
        story = []
        build_auditor_conclusion_block(story, styles, doc_width)
        assert len(story) > 0, "Auditor conclusion block must produce content"
        paragraphs = [f for f in story if isinstance(f, Paragraph)]
        heading_found = any("Practitioner Assessment" in p.text for p in paragraphs)
        assert heading_found, "Block must contain 'Practitioner Assessment' heading"

    def test_auditor_conclusion_block_has_ruled_lines(self, styles, doc_width):
        """Block must include a blank-lines table for practitioner notes."""
        story = []
        build_auditor_conclusion_block(story, styles, doc_width)
        tables = [f for f in story if isinstance(f, Table)]
        assert len(tables) >= 1, "Block must have a ruled-lines table"

    def test_auditor_conclusion_block_has_signature_line(self, styles, doc_width):
        """Block must include a signature/date line."""
        story = []
        build_auditor_conclusion_block(story, styles, doc_width)
        paragraphs = [f for f in story if isinstance(f, Paragraph)]
        sig_found = any("Signature" in p.text for p in paragraphs)
        assert sig_found, "Block must contain 'Signature' line"

    def test_auditor_conclusion_block_always_rendered(self, styles, doc_width):
        """Block is not gated by include_signoff — always rendered."""
        story = []
        build_auditor_conclusion_block(story, styles, doc_width)
        assert len(story) > 0, "Block must always render (no gating)"


# =============================================================================
# 9. Skipped tests section
# =============================================================================


class TestSkippedTestsSection:
    """Verify skipped tests documentation section."""

    def test_skipped_tests_renders_when_skipped(self, styles, doc_width):
        """Section should render when at least one test is skipped."""
        test_results = [
            {"test_key": "t1", "test_name": "Test One", "skipped": True, "skip_reason": "No bank data"},
            {"test_key": "t2", "test_name": "Test Two", "skipped": False, "entries_flagged": 2},
        ]
        story = []
        build_skipped_tests_section(story, styles, doc_width, test_results)
        assert len(story) > 0, "Skipped tests section must render when tests are skipped"
        tables = [f for f in story if isinstance(f, Table)]
        assert len(tables) >= 1, "Must contain a table with skipped test details"

    def test_skipped_tests_hidden_when_none_skipped(self, styles, doc_width):
        """Section should produce nothing when no tests are skipped."""
        test_results = [
            {"test_key": "t1", "test_name": "Test One", "skipped": False, "entries_flagged": 0},
        ]
        story = []
        build_skipped_tests_section(story, styles, doc_width, test_results)
        assert len(story) == 0, "No skipped tests = no output"

    def test_skipped_tests_heading_present(self, styles, doc_width):
        """Section heading 'Tests Not Performed' must be present."""
        test_results = [
            {"test_key": "t1", "test_name": "Ghost Employees", "skipped": True, "skip_reason": "No SSN column"},
        ]
        story = []
        build_skipped_tests_section(story, styles, doc_width, test_results)
        paragraphs = [f for f in story if isinstance(f, Paragraph)]
        heading_found = any("Tests Not Performed" in p.text for p in paragraphs)
        assert heading_found, "Section must have 'Tests Not Performed' heading"


# =============================================================================
# 10. Methodology parameters column
# =============================================================================


class TestMethodologyParametersColumn:
    """Verify methodology table adapts columns for parameters/assertions."""

    def test_methodology_parameters_column(self, styles, doc_width):
        """When test_parameters is provided, table should have 4+ columns."""
        story = []
        test_results = [
            {"test_key": "t1", "test_name": "Test One", "test_tier": "structural",
             "entries_flagged": 0, "flag_rate": 0.0, "severity": "low"},
        ]
        test_descriptions = {"t1": "First test"}
        test_parameters = {"t1": ">= $10,000"}
        build_methodology_section(
            story, styles, doc_width, test_results, test_descriptions, "Intro.",
            test_parameters=test_parameters,
        )
        tables = [f for f in story if isinstance(f, Table)]
        assert len(tables) >= 1
        # Check that the table has 4 columns (Test, Tier, Description, Parameters)
        header_row = tables[0]._cellvalues[0]
        assert len(header_row) >= 4, f"Expected >= 4 columns with parameters, got {len(header_row)}"

    def test_methodology_no_parameters_column(self, styles, doc_width):
        """When test_parameters is empty, table should have 3 columns."""
        story = []
        test_results = [
            {"test_key": "t1", "test_name": "Test One", "test_tier": "structural",
             "entries_flagged": 0, "flag_rate": 0.0, "severity": "low"},
        ]
        test_descriptions = {"t1": "First test"}
        build_methodology_section(
            story, styles, doc_width, test_results, test_descriptions, "Intro.",
        )
        tables = [f for f in story if isinstance(f, Table)]
        assert len(tables) >= 1
        header_row = tables[0]._cellvalues[0]
        assert len(header_row) == 3, f"Expected 3 columns without parameters, got {len(header_row)}"


# =============================================================================
# 11. Assertion summary
# =============================================================================


class TestAssertionSummary:
    """Verify assertion coverage summary rendering."""

    def test_assertion_summary_renders(self, styles, doc_width):
        """Should render assertion coverage lines when assertions are mapped."""
        story = []
        test_results = [
            {"test_key": "t1", "entries_flagged": 2},
            {"test_key": "t2", "entries_flagged": 0},
        ]
        test_assertions = {
            "t1": ["existence"],
            "t2": ["completeness", "accuracy"],
        }
        build_assertion_summary(story, styles, doc_width, test_results, test_assertions)
        assert len(story) > 0, "Assertion summary must render when assertions are mapped"
        paragraphs = [f for f in story if isinstance(f, Paragraph)]
        text = " ".join(p.text for p in paragraphs)
        assert "Assertions Addressed" in text

    def test_assertion_summary_empty_when_no_assertions(self, styles, doc_width):
        """Should produce nothing when test_assertions is empty."""
        story = []
        build_assertion_summary(story, styles, doc_width, [], {})
        assert len(story) == 0


# =============================================================================
# 12. Materiality scope lines
# =============================================================================


class TestMaterialityScopeLines:
    """Verify materiality context in scope section."""

    def test_materiality_scope_lines(self, styles, doc_width):
        """Materiality values should appear in scope when provided."""
        story = []
        composite = {"score": 10, "total_entries": 100}
        data_quality = {"completeness_score": 95}
        build_scope_section(
            story, styles, doc_width, composite, data_quality, "entries", "FY 2025",
            planning_materiality=50000.0,
            performance_materiality=37500.0,
        )
        paragraphs = [f for f in story if isinstance(f, Paragraph)]
        text = " ".join(p.text for p in paragraphs)
        assert "50,000" in text, "Planning materiality must appear in scope"
        assert "37,500" in text, "Performance materiality must appear in scope"

    def test_materiality_hidden_when_absent(self, styles, doc_width):
        """No materiality lines when values are None."""
        story = []
        composite = {"score": 10, "total_entries": 100}
        data_quality = {"completeness_score": 95}
        build_scope_section(
            story, styles, doc_width, composite, data_quality, "entries", "FY 2025",
        )
        paragraphs = [f for f in story if isinstance(f, Paragraph)]
        text = " ".join(p.text for p in paragraphs)
        assert "Planning Materiality" not in text
        assert "Performance Materiality" not in text


# =============================================================================
# 13. Structured findings table
# =============================================================================


class TestStructuredFindingsTable:
    """Verify structured findings table rendering."""

    def test_structured_findings_table(self, styles, doc_width):
        """Structured findings should render table with sort order."""
        story = []
        findings = [
            {"account": "Sales", "amount": 10000, "test": "Round amounts", "severity": "low"},
            {"account": "Cash", "amount": 50000, "test": "Z-score", "severity": "high"},
            {"account": "AR", "amount": 25000, "test": "Duplicates", "severity": "medium"},
        ]
        build_structured_findings_table(story, styles, doc_width, findings, "IV")
        tables = [f for f in story if isinstance(f, Table)]
        assert len(tables) >= 1, "Structured findings must produce a table"
        # Heading should be present
        paragraphs = [f for f in story if isinstance(f, Paragraph)]
        heading_found = any("Key Findings" in p.text for p in paragraphs)
        assert heading_found

    def test_structured_findings_aggregate(self, styles, doc_width):
        """Aggregate flagged amount should appear after table."""
        story = []
        findings = [
            {"account": "Acc1", "amount": 1000, "test": "T1", "severity": "low"},
            {"account": "Acc2", "amount": 2000, "test": "T2", "severity": "medium"},
        ]
        build_structured_findings_table(story, styles, doc_width, findings, "IV")
        paragraphs = [f for f in story if isinstance(f, Paragraph)]
        text = " ".join(p.text for p in paragraphs)
        assert "3,000" in text, "Aggregate flagged amount must appear"

    def test_structured_findings_fallback(self, styles, doc_width):
        """String findings should use text fallback format."""
        story = []
        findings = ["Finding one: unusual pattern", "Finding two: large amount"]
        build_structured_findings_table(story, styles, doc_width, findings, "IV")
        # Should still produce content (text-mode fallback)
        assert len(story) > 0, "Text fallback should produce content"


# =============================================================================
# 14. Proof summary label change
# =============================================================================


class TestProofSummaryLabelChange:
    """Verify proof summary uses 'Tests With No Flags' label."""

    def test_proof_summary_label_change(self, styles, doc_width):
        story = []
        result = {
            "data_quality": {"completeness_score": 95.0},
            "composite_score": {"tests_run": 3, "total_flagged": 1},
            "test_results": [
                {"test_key": "t1", "severity": "low", "entries_flagged": 0, "skipped": False},
                {"test_key": "t2", "severity": "medium", "entries_flagged": 1, "skipped": False},
                {"test_key": "t3", "severity": "low", "entries_flagged": 0, "skipped": False},
            ],
        }
        build_proof_summary_section(story, styles, doc_width, result)
        tables = [f for f in story if isinstance(f, Table)]
        # Find the proof summary table and check for "Tests With No Flags"
        found_correct_label = False
        found_old_label = False
        for tbl in tables:
            for row in tbl._cellvalues:
                for cell in row:
                    cell_text = str(cell)
                    if "Tests With No Flags" in cell_text:
                        found_correct_label = True
                    if "Tests Clear" in cell_text:
                        found_old_label = True
        assert found_correct_label, "Proof summary must use 'Tests With No Flags' label"
        assert not found_old_label, "Old 'Tests Clear' label must not appear"


# =============================================================================
# 15. Language: no banned assertive patterns
# =============================================================================


_RISK_ASSESSMENT_FILES = [
    "je_testing_memo_generator",
    "ap_testing_memo_generator",
    "payroll_testing_memo_generator",
    "revenue_testing_memo_generator",
    "ar_aging_memo_generator",
    "fixed_asset_testing_memo_generator",
    "inventory_testing_memo_generator",
    "bank_reconciliation_memo_generator",
    "three_way_match_memo_generator",
]


class TestLanguageNoBannedPatterns:
    """Verify risk assessment text uses non-assertive language."""

    @pytest.mark.parametrize("module_name", _RISK_ASSESSMENT_FILES)
    def test_language_no_banned_patterns(self, module_name):
        """Risk assessments must not contain assertive/assurance language."""
        import importlib

        mod = importlib.import_module(module_name)
        # Gather all string values from module-level dicts and configs
        all_text = ""
        for attr_name in dir(mod):
            attr = getattr(mod, attr_name)
            if isinstance(attr, dict):
                for v in attr.values():
                    if isinstance(v, str):
                        all_text += v + " "
            elif hasattr(attr, "risk_assessments"):
                for v in attr.risk_assessments.values():
                    if isinstance(v, str):
                        all_text += v + " "

        lower_text = all_text.lower()
        banned = [
            "require detailed investigation",
            "require further investigation",
            "we conclude",
            "we determined",
            "it is our opinion",
            "free from material misstatement",
            "in our professional judgment",
        ]
        for phrase in banned:
            assert phrase not in lower_text, (
                f"Banned phrase '{phrase}' found in {module_name}"
            )
