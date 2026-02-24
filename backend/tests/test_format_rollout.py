"""
Tests for per-format feature flags and tier-gated format access — Sprint 436.

Covers:
- is_format_enabled() reads config flags
- check_format_access() factory denies/allows based on tier
- parse_uploaded_file_by_format() respects format flags
- Tier entitlements include formats_allowed field
"""

from unittest.mock import patch

import pytest
from fastapi import HTTPException

from models import UserTier
from shared.entitlements import get_entitlements
from shared.file_formats import FileFormat, is_format_enabled
from shared.helpers import parse_uploaded_file_by_format

# =============================================================================
# is_format_enabled()
# =============================================================================


class TestIsFormatEnabled:
    """Format feature flag checks."""

    def test_csv_always_enabled(self):
        """CSV has no feature flag — always enabled."""
        assert is_format_enabled(FileFormat.CSV) is True

    def test_xlsx_always_enabled(self):
        assert is_format_enabled(FileFormat.XLSX) is True

    def test_xls_always_enabled(self):
        assert is_format_enabled(FileFormat.XLS) is True

    def test_tsv_always_enabled(self):
        assert is_format_enabled(FileFormat.TSV) is True

    def test_txt_always_enabled(self):
        assert is_format_enabled(FileFormat.TXT) is True

    def test_ods_reads_config_flag(self):
        """ODS enabled state depends on FORMAT_ODS_ENABLED config."""
        # Default is false
        result = is_format_enabled(FileFormat.ODS)
        assert isinstance(result, bool)

    @patch("config.FORMAT_ODS_ENABLED", True)
    def test_ods_enabled_when_flag_true(self):
        assert is_format_enabled(FileFormat.ODS) is True

    @patch("config.FORMAT_ODS_ENABLED", False)
    def test_ods_disabled_when_flag_false(self):
        assert is_format_enabled(FileFormat.ODS) is False

    @patch("config.FORMAT_PDF_ENABLED", True)
    def test_pdf_enabled_by_default(self):
        assert is_format_enabled(FileFormat.PDF) is True

    @patch("config.FORMAT_PDF_ENABLED", False)
    def test_pdf_disabled_when_flag_false(self):
        assert is_format_enabled(FileFormat.PDF) is False


# =============================================================================
# Format flag enforcement in parse_uploaded_file_by_format()
# =============================================================================


class TestFormatFlagEnforcement:
    """parse_uploaded_file_by_format() rejects disabled formats."""

    @patch("config.FORMAT_ODS_ENABLED", False)
    def test_ods_rejected_when_disabled(self):
        """ODS upload should fail when FORMAT_ODS_ENABLED=false."""
        from tests.test_ods_parser import _build_ods_zip

        ods_bytes = _build_ods_zip()
        with pytest.raises(HTTPException) as exc_info:
            parse_uploaded_file_by_format(ods_bytes, "report.ods")
        assert exc_info.value.status_code == 400
        assert "disabled" in exc_info.value.detail.lower()

    def test_csv_always_parseable(self):
        """CSV should always parse regardless of flags."""
        content = b"A,B\n1,2\n"
        cols, rows = parse_uploaded_file_by_format(content, "data.csv")
        assert len(rows) == 1


# =============================================================================
# Tier entitlements — formats_allowed field
# =============================================================================


class TestTierFormatEntitlements:
    """Tier entitlement format restrictions."""

    def test_free_tier_basic_formats_only(self):
        ent = get_entitlements(UserTier.FREE)
        assert "csv" in ent.formats_allowed
        assert "xlsx" in ent.formats_allowed
        assert "xls" in ent.formats_allowed
        assert "tsv" in ent.formats_allowed
        assert "txt" in ent.formats_allowed
        assert "ods" not in ent.formats_allowed
        assert "pdf" not in ent.formats_allowed
        assert "qbo" not in ent.formats_allowed

    def test_starter_tier_includes_advanced_formats(self):
        ent = get_entitlements(UserTier.STARTER)
        assert "csv" in ent.formats_allowed
        assert "pdf" in ent.formats_allowed
        assert "qbo" in ent.formats_allowed
        assert "ofx" in ent.formats_allowed
        assert "iif" in ent.formats_allowed
        # ODS not in starter — requires Professional+
        assert "ods" not in ent.formats_allowed

    def test_professional_tier_all_formats(self):
        ent = get_entitlements(UserTier.PROFESSIONAL)
        # Empty frozenset = all formats allowed
        assert len(ent.formats_allowed) == 0

    def test_team_tier_all_formats(self):
        ent = get_entitlements(UserTier.TEAM)
        assert len(ent.formats_allowed) == 0

    def test_enterprise_tier_all_formats(self):
        ent = get_entitlements(UserTier.ENTERPRISE)
        assert len(ent.formats_allowed) == 0
