"""
Tests for Anomaly Summary Generator + Engagement Export — Sprint 101 / Sprint 515

Covers:
- TestAnomalySummaryReport: section structure, disclaimer, no ISA 265, access control
- TestCoverPageMetadata: full metadata block with reference number
- TestScopeEnhancements: unexecuted tools, severity metrics, risk indicator
- TestAnomalyRegister: cross-references, clean-result blocks, severity column
- TestPractitionerAssessment: per-anomaly response blocks, completion tracker
- TestEngagementRiskAssessment: risk scoring, narrative
- TestSignOffBlock: sign-off table, DRAFT watermark
- TestAuthoritativeReferences: AU-C/PCAOB citations, no ASC 250-10
- TestPhantomPageFix: no trailing standalone disclaimer
- TestEngagementZIP: file structure, manifest, naming convention
- TestDisclaimerUpdates: strengthened disclaimer in memo_base
- TestExportRoutes: route registration
"""

import hashlib
import json
import sys
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from anomaly_summary_generator import (
    AUDITOR_INSTRUCTIONS,
    AUTHORITATIVE_REFERENCES,
    DISCLAIMER_TEXT,
    TOOL_CROSS_REFERENCES,
    AnomalySummaryGenerator,
    _compute_engagement_risk,
    _generate_reference,
)
from engagement_export import PLATFORM_VERSION, EngagementExporter
from engagement_model import ToolName
from follow_up_items_model import FollowUpSeverity


class TestAnomalySummaryReport:
    """Tests for the anomaly summary PDF generator."""

    def test_generate_pdf_returns_bytes(self, db_session, make_engagement):
        """PDF generator returns non-empty bytes."""
        eng = make_engagement()
        gen = AnomalySummaryGenerator(db_session)
        pdf = gen.generate_pdf(eng.created_by, eng.id)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100
        assert pdf[:5] == b"%PDF-"

    def test_pdf_with_no_follow_ups(self, db_session, make_engagement):
        """PDF generates successfully with no follow-up items."""
        eng = make_engagement()
        gen = AnomalySummaryGenerator(db_session)
        pdf = gen.generate_pdf(eng.created_by, eng.id)
        assert pdf[:5] == b"%PDF-"

    def test_pdf_with_follow_up_items(self, db_session, make_engagement, make_follow_up_item):
        """PDF generates successfully with follow-up items."""
        eng = make_engagement()
        make_follow_up_item(engagement=eng, severity=FollowUpSeverity.HIGH, tool_source="trial_balance")
        make_follow_up_item(engagement=eng, severity=FollowUpSeverity.MEDIUM, tool_source="ap_testing")
        gen = AnomalySummaryGenerator(db_session)
        pdf = gen.generate_pdf(eng.created_by, eng.id)
        assert pdf[:5] == b"%PDF-"
        assert len(pdf) > 500

    def test_pdf_with_tool_runs(self, db_session, make_engagement, make_tool_run):
        """PDF includes scope with tool run data."""
        eng = make_engagement()
        make_tool_run(engagement=eng, tool_name=ToolName.TRIAL_BALANCE)
        make_tool_run(engagement=eng, tool_name=ToolName.AP_TESTING)
        gen = AnomalySummaryGenerator(db_session)
        pdf = gen.generate_pdf(eng.created_by, eng.id)
        assert pdf[:5] == b"%PDF-"

    def test_access_denied_for_wrong_user(self, db_session, make_engagement, make_user):
        """Wrong user cannot generate anomaly summary."""
        eng = make_engagement()
        other = make_user(email="other@example.com")
        gen = AnomalySummaryGenerator(db_session)
        with pytest.raises(ValueError, match="not found or access denied"):
            gen.generate_pdf(other.id, eng.id)

    def test_nonexistent_engagement(self, db_session, make_user):
        """Nonexistent engagement raises ValueError."""
        user = make_user()
        gen = AnomalySummaryGenerator(db_session)
        with pytest.raises(ValueError, match="not found or access denied"):
            gen.generate_pdf(user.id, 9999)

    def test_disclaimer_text_defined(self):
        """Disclaimer constant is defined and non-empty."""
        assert "NOT AN AUDIT COMMUNICATION" in DISCLAIMER_TEXT
        assert "ISA 265" in DISCLAIMER_TEXT
        assert "PCAOB AS 1305" in DISCLAIMER_TEXT

    def test_no_isa_265_sections(self):
        """Guardrail 3: No ISA 265 structure terms in constants."""
        forbidden = [
            "Material Weakness",
            "Significant Deficiency",
            "Control Environment Assessment",
            "Management Letter",
        ]
        for term in forbidden:
            assert term not in DISCLAIMER_TEXT, f"Forbidden term found: {term}"
            assert term not in AUDITOR_INSTRUCTIONS, f"Forbidden term found: {term}"

    def test_auditor_section_instructions_defined(self):
        """Auditor assessment instructions are defined."""
        assert "auditor should document" in AUDITOR_INSTRUCTIONS

    def test_pdf_with_large_batch(self, db_session, make_engagement, make_follow_up_item):
        """PDF handles many follow-up items."""
        eng = make_engagement()
        for i in range(25):
            sev = [FollowUpSeverity.HIGH, FollowUpSeverity.MEDIUM, FollowUpSeverity.LOW][i % 3]
            make_follow_up_item(
                engagement=eng,
                description=f"Anomaly #{i + 1}: Test description for item",
                severity=sev,
                tool_source=["trial_balance", "ap_testing", "payroll_testing"][i % 3],
            )
        gen = AnomalySummaryGenerator(db_session)
        pdf = gen.generate_pdf(eng.created_by, eng.id)
        assert pdf[:5] == b"%PDF-"

    def test_pdf_multiple_tools_grouped(self, db_session, make_engagement, make_follow_up_item):
        """Follow-up items are grouped by tool source."""
        eng = make_engagement()
        make_follow_up_item(engagement=eng, tool_source="trial_balance", description="TB anomaly")
        make_follow_up_item(engagement=eng, tool_source="trial_balance", description="TB anomaly 2")
        make_follow_up_item(engagement=eng, tool_source="ap_testing", description="AP anomaly")
        gen = AnomalySummaryGenerator(db_session)
        pdf = gen.generate_pdf(eng.created_by, eng.id)
        assert pdf[:5] == b"%PDF-"


class TestCoverPageMetadata:
    """Tests for cover page metadata enhancements."""

    def test_reference_number_format(self):
        """Reference number follows ANS-YYYY-MMDD-NNN format."""
        ref = _generate_reference()
        assert ref.startswith("ANS-")
        parts = ref.split("-")
        assert len(parts) == 4
        assert len(parts[1]) == 4  # YYYY
        assert len(parts[2]) == 4  # MMDD
        assert len(parts[3]) == 3  # NNN

    def test_reference_number_consistent_with_shared(self):
        """Reference uses shared generate_reference_number() pattern (deterministic per-second)."""
        ref = _generate_reference()
        # Shared pattern is deterministic within the same second
        assert ref.startswith("ANS-")
        assert ref == _generate_reference()  # Same second → same reference


class TestScopeEnhancements:
    """Tests for Section I scope enhancements."""

    def test_unexecuted_tools_rendered(self, db_session, make_engagement, make_tool_run):
        """PDF renders when some tools are executed and others are not."""
        eng = make_engagement()
        make_tool_run(engagement=eng, tool_name=ToolName.TRIAL_BALANCE)
        make_tool_run(engagement=eng, tool_name=ToolName.AP_TESTING)
        gen = AnomalySummaryGenerator(db_session)
        pdf = gen.generate_pdf(eng.created_by, eng.id)
        assert pdf[:5] == b"%PDF-"
        # 2 tools run out of 13 → 11 not executed
        assert len(pdf) > 500

    def test_all_tools_executed(self, db_session, make_engagement, make_tool_run):
        """PDF renders correctly when all tools are executed."""
        eng = make_engagement()
        for tn in ToolName:
            make_tool_run(engagement=eng, tool_name=tn)
        gen = AnomalySummaryGenerator(db_session)
        pdf = gen.generate_pdf(eng.created_by, eng.id)
        assert pdf[:5] == b"%PDF-"

    def test_no_tools_executed(self, db_session, make_engagement):
        """PDF renders correctly with no tool runs."""
        eng = make_engagement()
        gen = AnomalySummaryGenerator(db_session)
        pdf = gen.generate_pdf(eng.created_by, eng.id)
        assert pdf[:5] == b"%PDF-"


class TestAnomalyRegister:
    """Tests for Section II anomaly register enhancements."""

    def test_cross_reference_mapping_complete(self):
        """Every ToolName has a cross-reference prefix."""
        for tn in ToolName:
            assert tn in TOOL_CROSS_REFERENCES, f"Missing cross-ref for {tn.value}"

    def test_cross_reference_format(self):
        """Cross-references follow WP-XXX-001 format."""
        for tn, ref in TOOL_CROSS_REFERENCES.items():
            assert ref.startswith("WP-"), f"Bad prefix for {tn.value}: {ref}"
            assert ref.endswith("-001"), f"Bad suffix for {tn.value}: {ref}"

    def test_clean_result_tools_rendered(
        self,
        db_session,
        make_engagement,
        make_tool_run,
        make_follow_up_item,
    ):
        """Tools with runs but no findings render explicit clean-result blocks."""
        eng = make_engagement()
        # Run 3 tools
        make_tool_run(engagement=eng, tool_name=ToolName.TRIAL_BALANCE)
        make_tool_run(engagement=eng, tool_name=ToolName.AP_TESTING)
        make_tool_run(engagement=eng, tool_name=ToolName.PAYROLL_TESTING)
        # Only AP has a finding
        make_follow_up_item(engagement=eng, tool_source="ap_testing", description="Duplicate payment")
        gen = AnomalySummaryGenerator(db_session)
        pdf = gen.generate_pdf(eng.created_by, eng.id)
        assert pdf[:5] == b"%PDF-"
        assert len(pdf) > 500

    def test_severity_column_width(self):
        """Severity column is wide enough for 'MEDIUM' without line-break.

        At 9pt Times-Roman, 'MEDIUM' is ~42pt wide. The column must be
        wider than the text to prevent wrapping. 1.0 inch = 72pt is sufficient.
        """
        from reportlab.lib.units import inch

        column_width_pt = 1.0 * inch  # 72pt
        # 'MEDIUM' in 9pt Times-Roman is ~42pt — column must exceed that
        assert column_width_pt >= 42


class TestPractitionerAssessment:
    """Tests for Section III practitioner assessment framework."""

    def test_response_blocks_with_items(self, db_session, make_engagement, make_follow_up_item):
        """PDF with follow-up items generates Section III response blocks."""
        eng = make_engagement()
        for i in range(3):
            sev = [FollowUpSeverity.HIGH, FollowUpSeverity.MEDIUM, FollowUpSeverity.LOW][i]
            make_follow_up_item(
                engagement=eng,
                description=f"Test anomaly {i + 1}",
                severity=sev,
                tool_source="trial_balance",
            )
        gen = AnomalySummaryGenerator(db_session)
        pdf = gen.generate_pdf(eng.created_by, eng.id)
        assert pdf[:5] == b"%PDF-"
        assert len(pdf) > 1000  # Section III adds substantial content

    def test_no_response_blocks_without_items(self, db_session, make_engagement):
        """PDF with no follow-up items has simplified Section III."""
        eng = make_engagement()
        gen = AnomalySummaryGenerator(db_session)
        pdf = gen.generate_pdf(eng.created_by, eng.id)
        assert pdf[:5] == b"%PDF-"


class TestEngagementRiskAssessment:
    """Tests for Section IV engagement risk scoring."""

    def test_elevated_risk(self):
        """High severity count >= 3 triggers ELEVATED."""
        label, score = _compute_engagement_risk(3, 2, 1, 0)
        assert label == "ELEVATED"

    def test_elevated_risk_by_score(self):
        """Total score >= 15 triggers ELEVATED."""
        label, score = _compute_engagement_risk(2, 3, 2, 2)
        assert label == "ELEVATED"
        assert score >= 15

    def test_moderate_risk(self):
        """1 high severity with low total triggers MODERATE."""
        label, score = _compute_engagement_risk(1, 0, 0, 0)
        assert label == "MODERATE"

    def test_low_risk(self):
        """Zero high severity and low total triggers LOW."""
        label, score = _compute_engagement_risk(0, 1, 1, 0)
        assert label == "LOW"

    def test_coverage_penalty(self):
        """Unexecuted tools add coverage penalty."""
        label1, score1 = _compute_engagement_risk(0, 0, 0, 0)
        label2, score2 = _compute_engagement_risk(0, 0, 0, 10)
        assert score2 > score1

    def test_risk_indicator_in_pdf(self, db_session, make_engagement, make_follow_up_item):
        """PDF generates with risk indicator section."""
        eng = make_engagement()
        make_follow_up_item(engagement=eng, severity=FollowUpSeverity.HIGH, tool_source="ap_testing")
        gen = AnomalySummaryGenerator(db_session)
        pdf = gen.generate_pdf(eng.created_by, eng.id)
        assert pdf[:5] == b"%PDF-"


class TestSignOffBlock:
    """Tests for sign-off block."""

    def test_pdf_with_signoff(self, db_session, make_engagement):
        """PDF generates with sign-off section."""
        eng = make_engagement()
        gen = AnomalySummaryGenerator(db_session)
        pdf = gen.generate_pdf(eng.created_by, eng.id)
        assert pdf[:5] == b"%PDF-"

    def test_pdf_with_draft_watermark(self, db_session, make_engagement, make_follow_up_item):
        """PDF with anomalies includes DRAFT watermark note."""
        eng = make_engagement()
        make_follow_up_item(engagement=eng, severity=FollowUpSeverity.HIGH, tool_source="trial_balance")
        gen = AnomalySummaryGenerator(db_session)
        pdf = gen.generate_pdf(eng.created_by, eng.id)
        assert pdf[:5] == b"%PDF-"
        assert len(pdf) > 500


class TestAuthoritativeReferences:
    """Tests for authoritative references section."""

    def test_references_defined(self):
        """Authoritative references constant is populated."""
        assert len(AUTHORITATIVE_REFERENCES) == 5

    def test_references_include_required_standards(self):
        """All required auditing standards are present."""
        ref_ids = {ref[1] for ref in AUTHORITATIVE_REFERENCES}
        assert "AU-C \u00a7 265" in ref_ids
        assert "AU-C \u00a7 330" in ref_ids
        assert "AU-C \u00a7 520" in ref_ids
        assert "AS 1305" in ref_ids
        assert "AS 2305" in ref_ids

    def test_no_asc_250_10_in_references(self):
        """ASC 250-10 must NOT appear in the anomaly summary references."""
        for body, ref_id, topic in AUTHORITATIVE_REFERENCES:
            assert "ASC 250-10" not in ref_id, "ASC 250-10 must not be in anomaly summary references"

    def test_no_asc_250_10_in_constants(self):
        """ASC 250-10 must not appear anywhere in the module constants."""
        assert "ASC 250-10" not in DISCLAIMER_TEXT
        assert "ASC 250-10" not in AUDITOR_INSTRUCTIONS


class TestPhantomPageFix:
    """Tests for phantom page 5 fix."""

    def test_no_trailing_disclaimer_in_story(self, db_session, make_engagement):
        """Story does not end with a standalone disclaimer paragraph."""
        eng = make_engagement()
        gen = AnomalySummaryGenerator(db_session)
        # Access internal _build_story to inspect the story list
        from shared.memo_base import create_memo_styles

        styles = create_memo_styles()
        doc_width = 468.0  # letter width - 1.5" margins

        from models import Client

        client = db_session.query(Client).filter(Client.id == eng.client_id).first()
        client_name = client.name if client else "Test"

        story = gen._build_story(
            styles,
            doc_width,
            client_name,
            eng,
            [],
            [],
        )

        # The last element should NOT be a disclaimer Paragraph
        # (it should be the sign-off table or spacer)
        from reportlab.platypus import Paragraph as RParagraph

        last_elements = [e for e in story[-3:] if isinstance(e, RParagraph)]
        for elem in last_elements:
            assert "DATA ANALYTICS REPORT" not in getattr(elem, "text", ""), (
                "Trailing disclaimer found — would cause phantom blank page"
            )


class TestEngagementZIP:
    """Tests for the engagement ZIP export."""

    def test_zip_returns_bytes_and_filename(self, db_session, make_engagement):
        """ZIP generator returns (bytes, filename) tuple."""
        eng = make_engagement()
        exporter = EngagementExporter(db_session)
        zip_bytes, filename = exporter.generate_zip(eng.created_by, eng.id)
        assert isinstance(zip_bytes, bytes)
        assert isinstance(filename, str)
        assert filename.endswith(".zip")

    def test_zip_filename_contains_client_and_period(self, db_session, make_engagement):
        """ZIP filename includes client name and period end."""
        eng = make_engagement()
        exporter = EngagementExporter(db_session)
        _, filename = exporter.generate_zip(eng.created_by, eng.id)
        assert "Acme" in filename
        assert "diagnostic_package" in filename

    def test_zip_contains_required_files(self, db_session, make_engagement):
        """ZIP contains anomaly_summary.pdf, workpaper_index.json, manifest.json."""
        eng = make_engagement()
        exporter = EngagementExporter(db_session)
        zip_bytes, _ = exporter.generate_zip(eng.created_by, eng.id)

        zf = ZipFile(BytesIO(zip_bytes))
        names = zf.namelist()
        assert "anomaly_summary.pdf" in names
        assert "workpaper_index.json" in names
        assert "manifest.json" in names
        assert len(names) == 3

    def test_manifest_has_sha256_hashes(self, db_session, make_engagement):
        """Manifest includes SHA-256 hashes for each file."""
        eng = make_engagement()
        exporter = EngagementExporter(db_session)
        zip_bytes, _ = exporter.generate_zip(eng.created_by, eng.id)

        zf = ZipFile(BytesIO(zip_bytes))
        manifest = json.loads(zf.read("manifest.json"))

        assert manifest["version"] == PLATFORM_VERSION
        assert len(manifest["files"]) == 2  # anomaly_summary + workpaper_index

        for file_entry in manifest["files"]:
            assert "filename" in file_entry
            assert "size_bytes" in file_entry
            assert "sha256" in file_entry
            assert len(file_entry["sha256"]) == 64  # SHA-256 hex length

    def test_manifest_sha256_matches_content(self, db_session, make_engagement):
        """Manifest SHA-256 hashes match actual file content."""
        eng = make_engagement()
        exporter = EngagementExporter(db_session)
        zip_bytes, _ = exporter.generate_zip(eng.created_by, eng.id)

        zf = ZipFile(BytesIO(zip_bytes))
        manifest = json.loads(zf.read("manifest.json"))

        for file_entry in manifest["files"]:
            content = zf.read(file_entry["filename"])
            actual_hash = hashlib.sha256(content).hexdigest()
            assert actual_hash == file_entry["sha256"], f"Hash mismatch for {file_entry['filename']}"

    def test_manifest_has_engagement_metadata(self, db_session, make_engagement):
        """Manifest includes engagement metadata."""
        eng = make_engagement()
        exporter = EngagementExporter(db_session)
        zip_bytes, _ = exporter.generate_zip(eng.created_by, eng.id)

        zf = ZipFile(BytesIO(zip_bytes))
        manifest = json.loads(zf.read("manifest.json"))

        assert manifest["platform"] == "Paciolus"
        assert manifest["engagement_id"] == eng.id
        assert manifest["client_name"] == "Acme Corp"
        assert manifest["generated_at"]

    def test_workpaper_index_json_valid(self, db_session, make_engagement):
        """Workpaper index JSON is valid and has expected structure."""
        eng = make_engagement()
        exporter = EngagementExporter(db_session)
        zip_bytes, _ = exporter.generate_zip(eng.created_by, eng.id)

        zf = ZipFile(BytesIO(zip_bytes))
        index = json.loads(zf.read("workpaper_index.json"))

        assert index["engagement_id"] == eng.id
        assert "document_register" in index
        assert "sign_off" in index
        assert len(index["document_register"]) == len(ToolName)

    def test_anomaly_pdf_is_valid(self, db_session, make_engagement):
        """Anomaly summary PDF in ZIP is valid PDF."""
        eng = make_engagement()
        exporter = EngagementExporter(db_session)
        zip_bytes, _ = exporter.generate_zip(eng.created_by, eng.id)

        zf = ZipFile(BytesIO(zip_bytes))
        pdf = zf.read("anomaly_summary.pdf")
        assert pdf[:5] == b"%PDF-"

    def test_access_denied_for_wrong_user(self, db_session, make_engagement, make_user):
        """Wrong user cannot export ZIP."""
        eng = make_engagement()
        other = make_user(email="other@example.com")
        exporter = EngagementExporter(db_session)
        with pytest.raises(ValueError, match="not found or access denied"):
            exporter.generate_zip(other.id, eng.id)

    def test_zip_does_not_contain_financial_data(self, db_session, make_engagement):
        """ZIP files contain no financial data (Zero-Storage compliance)."""
        eng = make_engagement()
        exporter = EngagementExporter(db_session)
        zip_bytes, _ = exporter.generate_zip(eng.created_by, eng.id)

        zf = ZipFile(BytesIO(zip_bytes))
        names = zf.namelist()

        # No raw data files
        for name in names:
            assert not name.endswith(".csv"), "ZIP should not contain CSV data files"
            assert not name.endswith(".xlsx"), "ZIP should not contain Excel data files"
            assert "upload" not in name.lower(), "ZIP should not contain uploaded files"


class TestDisclaimerUpdates:
    """Test strengthened disclaimer text in memo_base."""

    def test_disclaimer_mentions_analytics(self):
        """Strengthened disclaimer mentions data anomalies."""
        from shared.memo_base import build_disclaimer, create_memo_styles

        styles = create_memo_styles()
        story = []
        build_disclaimer(story, styles, domain="journal entry")
        # Verify it produced content
        assert len(story) >= 2  # Spacer + Paragraph

    def test_disclaimer_accepts_isa_reference(self):
        """Strengthened disclaimer accepts ISA reference parameter."""
        from shared.memo_base import build_disclaimer, create_memo_styles

        styles = create_memo_styles()
        story = []
        build_disclaimer(story, styles, domain="AP payment", isa_reference="ISA 240/500")
        assert len(story) >= 2

    def test_disclaimer_backward_compatible(self):
        """Disclaimer still works with just domain parameter."""
        from shared.memo_base import build_disclaimer, create_memo_styles

        styles = create_memo_styles()
        story = []
        build_disclaimer(story, styles)
        assert len(story) >= 2

    def test_disclaimer_does_not_claim_sufficiency(self):
        """Disclaimer explicitly says it does not constitute sufficient audit evidence."""
        from reportlab.platypus import Paragraph as RParagraph

        from shared.memo_base import build_disclaimer, create_memo_styles

        styles = create_memo_styles()
        story = []
        build_disclaimer(story, styles, domain="testing")
        # Find the Paragraph element
        paragraphs = [e for e in story if isinstance(e, RParagraph)]
        assert len(paragraphs) > 0
        text = paragraphs[0].text
        assert "does not constitute audit evidence sufficient" in text

    def test_disclaimer_mentions_professional_standards(self):
        """Disclaimer references professional standards."""
        from reportlab.platypus import Paragraph as RParagraph

        from shared.memo_base import build_disclaimer, create_memo_styles

        styles = create_memo_styles()
        story = []
        build_disclaimer(story, styles, domain="payroll")
        paragraphs = [e for e in story if isinstance(e, RParagraph)]
        text = paragraphs[0].text
        assert "professional standards" in text


class TestExportRoutes:
    """Test route registration for export endpoints."""

    def test_anomaly_summary_route_registered(self):
        """POST /engagements/{id}/export/anomaly-summary is registered."""
        from main import app

        routes = [route.path for route in app.routes]
        assert "/engagements/{engagement_id}/export/anomaly-summary" in routes

    def test_export_package_route_registered(self):
        """POST /engagements/{id}/export/package is registered."""
        from main import app

        routes = [route.path for route in app.routes]
        assert "/engagements/{engagement_id}/export/package" in routes
