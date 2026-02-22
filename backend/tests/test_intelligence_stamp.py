"""
Tests for build_intelligence_stamp — Sprint 409: Phase LVII
"""

import pytest
from reportlab.platypus import Paragraph, Spacer

from shared.memo_base import build_intelligence_stamp, create_memo_styles


class TestBuildIntelligenceStamp:
    """Tests for the intelligence watermark stamp."""

    def setup_method(self):
        self.styles = create_memo_styles()
        self.story: list = []

    def test_appends_elements_to_story(self):
        build_intelligence_stamp(self.story, self.styles)
        # Should add: Spacer + Paragraph + Spacer
        assert len(self.story) == 3
        assert isinstance(self.story[0], Spacer)
        assert isinstance(self.story[1], Paragraph)
        assert isinstance(self.story[2], Spacer)

    def test_includes_paciolus_intelligence(self):
        build_intelligence_stamp(self.story, self.styles)
        para = self.story[1]
        text = para.text
        assert "Paciolus Intelligence" in text

    def test_includes_generated_timestamp(self):
        build_intelligence_stamp(self.story, self.styles)
        para = self.story[1]
        text = para.text
        assert "Generated" in text
        assert "UTC" in text

    def test_includes_client_name_when_provided(self):
        build_intelligence_stamp(
            self.story, self.styles,
            client_name="Acme Corp",
        )
        para = self.story[1]
        text = para.text
        assert "Acme Corp" in text

    def test_includes_period_when_provided(self):
        build_intelligence_stamp(
            self.story, self.styles,
            period_tested="FY 2025",
        )
        para = self.story[1]
        text = para.text
        assert "Period: FY 2025" in text

    def test_omits_client_name_when_none(self):
        build_intelligence_stamp(self.story, self.styles, client_name=None)
        para = self.story[1]
        text = para.text
        # Should only have "Paciolus Intelligence" and "Generated..."
        parts = text.split("&bull;")
        # 2 parts: intelligence label + timestamp
        assert len(parts) == 2

    def test_omits_period_when_none(self):
        build_intelligence_stamp(
            self.story, self.styles,
            client_name="Test Co",
            period_tested=None,
        )
        para = self.story[1]
        text = para.text
        assert "Period:" not in text

    def test_all_fields_present(self):
        build_intelligence_stamp(
            self.story, self.styles,
            client_name="Global Industries",
            period_tested="Q3 2025",
        )
        para = self.story[1]
        text = para.text
        assert "Paciolus Intelligence" in text
        assert "Generated" in text
        assert "Global Industries" in text
        assert "Period: Q3 2025" in text
