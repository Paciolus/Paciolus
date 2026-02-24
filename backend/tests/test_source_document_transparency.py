"""
Sprint 6: Source Document Transparency Tests

Validates:
- ReportMetadata with source_document_title and source_context_note
- Cover page rendering: title+filename vs filename-only fallback
- Scope section source line rendering
- Long-title wrapping (no truncation)
- Non-ASCII filename handling
- WorkpaperMetadata schema accepts new fields
- Backwards compatibility (legacy calls without new fields)
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.memo_base import build_scope_section, create_memo_styles
from shared.report_chrome import ReportMetadata, build_cover_page

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def styles():
    return create_memo_styles()


@pytest.fixture
def dummy_composite():
    return {
        "total_entries": 1000,
        "tests_run": 5,
        "score": 12.5,
        "total_flagged": 3,
        "flag_rate": 0.003,
        "flags_by_severity": {"high": 1, "medium": 1, "low": 1},
    }


@pytest.fixture
def dummy_data_quality():
    return {"completeness_score": 95.0}


def _extract_text(story):
    """Extract all renderable text from story flowables."""
    texts = []
    for item in story:
        if hasattr(item, "text"):
            texts.append(item.text)
        elif hasattr(item, "_cellvalues"):
            for row in item._cellvalues:
                for cell in row:
                    if hasattr(cell, "text"):
                        texts.append(cell.text)
    return " ".join(texts)


# =============================================================================
# ReportMetadata — New Fields
# =============================================================================


class TestReportMetadataSourceFields:
    """Tests for source_document_title and source_context_note on ReportMetadata."""

    def test_defaults_empty(self):
        m = ReportMetadata(title="Test")
        assert m.source_document_title == ""
        assert m.source_context_note == ""

    def test_title_and_context_set(self):
        m = ReportMetadata(
            title="Test",
            source_document="file.csv",
            source_document_title="Q4 General Ledger Export",
            source_context_note="Derived from consolidated ERP extract",
        )
        assert m.source_document == "file.csv"
        assert m.source_document_title == "Q4 General Ledger Export"
        assert m.source_context_note == "Derived from consolidated ERP extract"

    def test_backwards_compat_no_new_fields(self):
        """Legacy construction without new fields still works."""
        m = ReportMetadata(
            title="AP Testing Memo",
            source_document="ap_data.csv",
            reference="APT-001",
        )
        assert m.source_document == "ap_data.csv"
        assert m.source_document_title == ""
        assert m.source_context_note == ""


# =============================================================================
# Cover Page — Source Document Rendering
# =============================================================================


class TestCoverPageSourceRendering:
    """Tests for _append_metadata_table source document logic."""

    def test_title_present_shows_both(self, styles):
        """When title is present, cover page shows 'Source Document' + 'Source File'."""
        story = []
        metadata = ReportMetadata(
            title="Test Report",
            source_document="gl_extract_2025.xlsx",
            source_document_title="Q4 General Ledger Export",
        )
        build_cover_page(story, styles, metadata, 468.0)  # 6.5" usable width

        text = _extract_text(story)
        assert "Source Document" in text
        assert "Q4 General Ledger Export" in text
        assert "Source File" in text
        assert "gl_extract_2025.xlsx" in text

    def test_title_absent_shows_filename_only(self, styles):
        """When title is absent, only 'Source Document' row with filename appears."""
        story = []
        metadata = ReportMetadata(
            title="Test Report",
            source_document="ap_register.csv",
        )
        build_cover_page(story, styles, metadata, 468.0)

        text = _extract_text(story)
        assert "Source Document" in text
        assert "ap_register.csv" in text
        # Should NOT have "Source File" row when title is absent
        assert "Source File" not in text

    def test_context_note_present(self, styles):
        """When context note is provided, it appears as 'Source Context' row."""
        story = []
        metadata = ReportMetadata(
            title="Test Report",
            source_document="data.csv",
            source_document_title="Annual TB Export",
            source_context_note="Extracted from SAP S/4HANA module FI",
        )
        build_cover_page(story, styles, metadata, 468.0)

        text = _extract_text(story)
        assert "Source Context" in text
        assert "Extracted from SAP S/4HANA module FI" in text

    def test_no_source_at_all(self, styles):
        """When no source fields are set, no source rows appear."""
        story = []
        metadata = ReportMetadata(title="Test Report")
        build_cover_page(story, styles, metadata, 468.0)

        text = _extract_text(story)
        assert "Source Document" not in text
        assert "Source File" not in text
        assert "Source Context" not in text

    def test_long_title_not_truncated(self, styles):
        """Long source_document_title must not be truncated — it wraps."""
        long_title = "Annual Consolidated General Ledger Extract from SAP S/4HANA " * 3
        story = []
        metadata = ReportMetadata(
            title="Test Report",
            source_document="file.csv",
            source_document_title=long_title,
        )
        # Should not raise — content wraps inside Paragraph
        build_cover_page(story, styles, metadata, 468.0)

        text = _extract_text(story)
        # Full title appears without ellipsis
        assert long_title in text
        assert "..." not in text.split(long_title)[0]  # no truncation before title

    def test_non_ascii_filename(self, styles):
        """Non-ASCII filenames render without error."""
        story = []
        metadata = ReportMetadata(
            title="Test Report",
            source_document="日本語ファイル_2025.xlsx",
            source_document_title="Japan Office Trial Balance",
        )
        build_cover_page(story, styles, metadata, 468.0)

        text = _extract_text(story)
        assert "日本語ファイル_2025.xlsx" in text
        assert "Japan Office Trial Balance" in text


# =============================================================================
# Scope Section — Source Line
# =============================================================================


class TestScopeSectionSourceLine:
    """Tests for source identifier in build_scope_section()."""

    def test_source_with_title_and_filename(self, styles, dummy_composite, dummy_data_quality):
        """Scope shows 'Source: <title> (<filename>)' when both present."""
        story = []
        build_scope_section(
            story,
            styles,
            468.0,
            dummy_composite,
            dummy_data_quality,
            source_document="data.csv",
            source_document_title="Q4 GL Export",
        )
        text = _extract_text(story)
        assert "Q4 GL Export (data.csv)" in text

    def test_source_filename_only(self, styles, dummy_composite, dummy_data_quality):
        """Scope shows 'Source: <filename>' when title is absent."""
        story = []
        build_scope_section(
            story,
            styles,
            468.0,
            dummy_composite,
            dummy_data_quality,
            source_document="ap_register.csv",
        )
        text = _extract_text(story)
        assert "ap_register.csv" in text

    def test_source_title_only(self, styles, dummy_composite, dummy_data_quality):
        """Scope shows 'Source: <title>' when filename is absent."""
        story = []
        build_scope_section(
            story,
            styles,
            468.0,
            dummy_composite,
            dummy_data_quality,
            source_document_title="Manually Prepared Trial Balance",
        )
        text = _extract_text(story)
        assert "Manually Prepared Trial Balance" in text

    def test_no_source(self, styles, dummy_composite, dummy_data_quality):
        """No source line when neither filename nor title provided."""
        story = []
        build_scope_section(
            story,
            styles,
            468.0,
            dummy_composite,
            dummy_data_quality,
        )
        text = _extract_text(story)
        assert "Source" not in text

    def test_backwards_compat_no_source_params(self, styles, dummy_composite, dummy_data_quality):
        """Legacy calls without source params still work."""
        story = []
        # Old-style call with no source params
        build_scope_section(
            story,
            styles,
            468.0,
            dummy_composite,
            dummy_data_quality,
            entry_label="Total Entries",
            period_tested="FY 2025",
        )
        text = _extract_text(story)
        assert "Total Entries" in text
        assert "FY 2025" in text

    def test_non_ascii_in_scope(self, styles, dummy_composite, dummy_data_quality):
        """Non-ASCII characters in source fields render without error."""
        story = []
        build_scope_section(
            story,
            styles,
            468.0,
            dummy_composite,
            dummy_data_quality,
            source_document="données_2025.xlsx",
            source_document_title="Bilan Comptable Général",
        )
        text = _extract_text(story)
        assert "Bilan Comptable Général" in text
        assert "données_2025.xlsx" in text


# =============================================================================
# WorkpaperMetadata Schema — New Fields
# =============================================================================


class TestWorkpaperMetadataSourceFields:
    """Tests for source fields on WorkpaperMetadata Pydantic model."""

    def test_defaults_none(self):
        from shared.export_schemas import WorkpaperMetadata

        m = WorkpaperMetadata()
        assert m.source_document_title is None
        assert m.source_context_note is None

    def test_accepts_source_fields(self):
        from shared.export_schemas import WorkpaperMetadata

        m = WorkpaperMetadata(
            filename="test.csv",
            source_document_title="Annual TB",
            source_context_note="From SAP",
        )
        assert m.source_document_title == "Annual TB"
        assert m.source_context_note == "From SAP"

    def test_inherited_by_je_export(self):
        from shared.export_schemas import JETestingExportInput

        m = JETestingExportInput(
            composite_score={},
            test_results=[],
            data_quality={},
            source_document_title="GL Export",
        )
        assert m.source_document_title == "GL Export"

    def test_backwards_compat_without_new_fields(self):
        from shared.export_schemas import WorkpaperMetadata

        m = WorkpaperMetadata(filename="old.csv", client_name="Acme")
        assert m.filename == "old.csv"
        assert m.source_document_title is None


# =============================================================================
# End-to-End: Memo Generator with Source Metadata
# =============================================================================


class TestMemoGeneratorSourcePassthrough:
    """Tests that source metadata flows through to generated PDFs without error."""

    _MINIMAL_RESULT = {
        "composite_score": {
            "total_entries": 100,
            "tests_run": 3,
            "score": 5.0,
            "total_flagged": 0,
            "flag_rate": 0.0,
            "flags_by_severity": {"high": 0, "medium": 0, "low": 0},
            "risk_tier": "low",
        },
        "test_results": [],
        "data_quality": {"completeness_score": 100.0},
    }

    def test_je_memo_with_title(self):
        """JE memo generator accepts source_document_title and produces valid PDF."""
        from je_testing_memo_generator import generate_je_testing_memo

        pdf_bytes = generate_je_testing_memo(
            je_result=self._MINIMAL_RESULT,
            filename="gl_export_2025.csv",
            source_document_title="Q4 Consolidated GL Export",
            client_name="Test Corp",
        )
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:5] == b"%PDF-"

    def test_je_memo_without_title(self):
        """JE memo generator works without source_document_title (backwards compat)."""
        from je_testing_memo_generator import generate_je_testing_memo

        pdf_bytes = generate_je_testing_memo(
            je_result=self._MINIMAL_RESULT,
            filename="journal_entries.csv",
        )
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:5] == b"%PDF-"

    def test_je_memo_with_all_source_fields(self):
        """JE memo with title + context note produces valid PDF."""
        from je_testing_memo_generator import generate_je_testing_memo

        pdf_bytes = generate_je_testing_memo(
            je_result=self._MINIMAL_RESULT,
            filename="data.csv",
            source_document_title="Annual GL Export",
            source_context_note="Extracted from SAP S/4HANA",
        )
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:5] == b"%PDF-"

    def test_preflight_memo_with_title(self):
        """Preflight memo accepts source title and produces valid PDF."""
        from preflight_memo_generator import generate_preflight_memo

        result = {
            "readiness_score": 85.0,
            "readiness_label": "Ready",
            "row_count": 500,
            "column_count": 5,
            "columns": [],
            "issues": [],
        }
        pdf_bytes = generate_preflight_memo(
            preflight_result=result,
            filename="raw_data.xlsx",
            source_document_title="Client TB Export v2",
        )
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:5] == b"%PDF-"

    def test_long_title_no_crash(self):
        """Long source title does not crash PDF generation."""
        from je_testing_memo_generator import generate_je_testing_memo

        long_title = "Annual Consolidated General Ledger Full Export " * 5
        pdf_bytes = generate_je_testing_memo(
            je_result=self._MINIMAL_RESULT,
            filename="data.csv",
            source_document_title=long_title,
        )
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:5] == b"%PDF-"

    def test_non_ascii_filename_no_crash(self):
        """Non-ASCII filename does not crash PDF generation."""
        from je_testing_memo_generator import generate_je_testing_memo

        pdf_bytes = generate_je_testing_memo(
            je_result=self._MINIMAL_RESULT,
            filename="日本語ファイル_2025.xlsx",
            source_document_title="Tokyo Office Trial Balance",
        )
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:5] == b"%PDF-"

    def test_bank_rec_memo_with_title(self):
        """Bank rec memo accepts source metadata and produces valid PDF."""
        from bank_reconciliation_memo_generator import generate_bank_rec_memo

        result = {
            "summary": {
                "matched_count": 50,
                "bank_only_count": 5,
                "ledger_only_count": 3,
                "reconciling_difference": 0.0,
            },
            "bank_column_detection": {},
            "ledger_column_detection": {},
        }
        pdf_bytes = generate_bank_rec_memo(
            rec_result=result,
            filename="bank_stmt.csv",
            source_document_title="December Bank Statement",
        )
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:5] == b"%PDF-"
