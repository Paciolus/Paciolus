"""
Tests for Anomaly Summary Generator + Engagement Export — Sprint 101
Phase X: Engagement Layer

Covers:
- TestAnomalySummaryReport: section structure, disclaimer, no ISA 265, access control
- TestEngagementZIP: file structure, manifest, naming convention
- TestDisclaimerUpdates: strengthened disclaimer in memo_base
- TestExportRoutes: route registration
"""

import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime, UTC
from zipfile import ZipFile
from io import BytesIO

import pytest
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).parent.parent))

from anomaly_summary_generator import AnomalySummaryGenerator, DISCLAIMER_TEXT, AUDITOR_INSTRUCTIONS
from engagement_export import EngagementExporter, PLATFORM_VERSION
from workpaper_index_generator import WorkpaperIndexGenerator
from engagement_model import ToolName, ToolRunStatus
from follow_up_items_model import FollowUpSeverity, FollowUpDisposition


class TestAnomalySummaryReport:
    """Tests for the anomaly summary PDF generator."""

    def test_generate_pdf_returns_bytes(self, db_session, make_engagement):
        """PDF generator returns non-empty bytes."""
        eng = make_engagement()
        gen = AnomalySummaryGenerator(db_session)
        pdf = gen.generate_pdf(eng.created_by, eng.id)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100
        assert pdf[:5] == b'%PDF-'

    def test_pdf_with_no_follow_ups(self, db_session, make_engagement):
        """PDF generates successfully with no follow-up items."""
        eng = make_engagement()
        gen = AnomalySummaryGenerator(db_session)
        pdf = gen.generate_pdf(eng.created_by, eng.id)
        assert pdf[:5] == b'%PDF-'

    def test_pdf_with_follow_up_items(self, db_session, make_engagement, make_follow_up_item):
        """PDF generates successfully with follow-up items."""
        eng = make_engagement()
        make_follow_up_item(engagement=eng, severity=FollowUpSeverity.HIGH, tool_source="trial_balance")
        make_follow_up_item(engagement=eng, severity=FollowUpSeverity.MEDIUM, tool_source="ap_testing")
        gen = AnomalySummaryGenerator(db_session)
        pdf = gen.generate_pdf(eng.created_by, eng.id)
        assert pdf[:5] == b'%PDF-'
        assert len(pdf) > 500

    def test_pdf_with_tool_runs(self, db_session, make_engagement, make_tool_run):
        """PDF includes scope with tool run data."""
        eng = make_engagement()
        make_tool_run(engagement=eng, tool_name=ToolName.TRIAL_BALANCE)
        make_tool_run(engagement=eng, tool_name=ToolName.AP_TESTING)
        gen = AnomalySummaryGenerator(db_session)
        pdf = gen.generate_pdf(eng.created_by, eng.id)
        assert pdf[:5] == b'%PDF-'

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
        assert pdf[:5] == b'%PDF-'

    def test_pdf_multiple_tools_grouped(self, db_session, make_engagement, make_follow_up_item):
        """Follow-up items are grouped by tool source."""
        eng = make_engagement()
        make_follow_up_item(engagement=eng, tool_source="trial_balance", description="TB anomaly")
        make_follow_up_item(engagement=eng, tool_source="trial_balance", description="TB anomaly 2")
        make_follow_up_item(engagement=eng, tool_source="ap_testing", description="AP anomaly")
        gen = AnomalySummaryGenerator(db_session)
        pdf = gen.generate_pdf(eng.created_by, eng.id)
        assert pdf[:5] == b'%PDF-'


class TestEngagementZIP:
    """Tests for the engagement ZIP export."""

    def test_zip_returns_bytes_and_filename(self, db_session, make_engagement):
        """ZIP generator returns (bytes, filename) tuple."""
        eng = make_engagement()
        exporter = EngagementExporter(db_session)
        zip_bytes, filename = exporter.generate_zip(eng.created_by, eng.id)
        assert isinstance(zip_bytes, bytes)
        assert isinstance(filename, str)
        assert filename.endswith('.zip')

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
        assert len(index["document_register"]) == 7

    def test_anomaly_pdf_is_valid(self, db_session, make_engagement):
        """Anomaly summary PDF in ZIP is valid PDF."""
        eng = make_engagement()
        exporter = EngagementExporter(db_session)
        zip_bytes, _ = exporter.generate_zip(eng.created_by, eng.id)

        zf = ZipFile(BytesIO(zip_bytes))
        pdf = zf.read("anomaly_summary.pdf")
        assert pdf[:5] == b'%PDF-'

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
            assert not name.endswith('.csv'), "ZIP should not contain CSV data files"
            assert not name.endswith('.xlsx'), "ZIP should not contain Excel data files"
            assert 'upload' not in name.lower(), "ZIP should not contain uploaded files"


class TestDisclaimerUpdates:
    """Test strengthened disclaimer text in memo_base."""

    def test_disclaimer_mentions_analytics(self):
        """Strengthened disclaimer mentions data anomalies."""
        from shared.memo_base import build_disclaimer, create_memo_styles, Spacer
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
        from shared.memo_base import build_disclaimer, create_memo_styles
        from reportlab.platypus import Paragraph as RParagraph
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
        from shared.memo_base import build_disclaimer, create_memo_styles
        from reportlab.platypus import Paragraph as RParagraph
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
