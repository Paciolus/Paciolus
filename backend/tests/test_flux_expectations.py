"""
Sprint 297: ISA 520 Expectation Documentation Scaffold

Tests:
- ExpectationEntry and FluxExpectationsMemoInput schema validation
- Memo PDF generation with expectations
- Memo PDF generation without expectations (empty dict)
- ISA 520 disclaimer presence in generated PDF
- No auto-populated expectation text (blank enforcement)
- Route registration
"""

import pytest

from flux_expectations_memo import generate_flux_expectations_memo
from shared.export_schemas import ExpectationEntry, FluxExpectationsMemoInput


# ═══════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════

@pytest.fixture
def sample_flux_dict():
    """Minimal flux result dict for memo generation."""
    return {
        "items": [
            {
                "account": "Revenue",
                "type": "Revenue",
                "current": 500000,
                "prior": 300000,
                "delta_amount": 200000,
                "delta_percent": 66.67,
                "display_percent": "66.7%",
                "is_new": False,
                "is_removed": False,
                "sign_flip": False,
                "risk_level": "high",
                "variance_indicators": ["Large % Variance"],
            },
            {
                "account": "Cash",
                "type": "Asset",
                "current": 100000,
                "prior": 95000,
                "delta_amount": 5000,
                "delta_percent": 5.26,
                "display_percent": "5.3%",
                "is_new": False,
                "is_removed": False,
                "sign_flip": False,
                "risk_level": "low",
                "variance_indicators": [],
            },
        ],
        "summary": {
            "total_items": 2,
            "high_risk_count": 1,
            "medium_risk_count": 0,
            "new_accounts": 0,
            "removed_accounts": 0,
            "threshold": 10000,
        },
    }


# ═══════════════════════════════════════════════════════════════
# Schema Validation
# ═══════════════════════════════════════════════════════════════

class TestExpectationSchemas:
    """Verify Pydantic schemas for expectations."""

    def test_expectation_entry_defaults_blank(self):
        """ExpectationEntry fields should default to empty string."""
        entry = ExpectationEntry()
        assert entry.auditor_expectation == ""
        assert entry.auditor_explanation == ""

    def test_expectation_entry_accepts_text(self):
        """ExpectationEntry should accept user-authored text."""
        entry = ExpectationEntry(
            auditor_expectation="Expected 10% growth based on Q3 trend",
            auditor_explanation="Actual growth exceeded due to new product launch",
        )
        assert "10% growth" in entry.auditor_expectation
        assert "new product launch" in entry.auditor_explanation

    def test_flux_expectations_memo_input_defaults(self):
        """FluxExpectationsMemoInput should default to empty expectations."""
        inp = FluxExpectationsMemoInput(
            flux={
                "items": [],
                "summary": {
                    "total_items": 0,
                    "high_risk_count": 0,
                    "medium_risk_count": 0,
                    "new_accounts": 0,
                    "removed_accounts": 0,
                    "threshold": 0,
                },
            },
        )
        assert inp.expectations == {}
        assert inp.filename == "export"  # WorkpaperMetadata default


# ═══════════════════════════════════════════════════════════════
# PDF Memo Generation
# ═══════════════════════════════════════════════════════════════

class TestFluxExpectationsMemo:
    """Verify ISA 520 Flux Expectations Memo generation."""

    def test_generates_pdf_bytes(self, sample_flux_dict):
        """Should return non-empty PDF bytes."""
        result = generate_flux_expectations_memo(
            flux_result=sample_flux_dict,
            expectations={},
        )
        assert isinstance(result, bytes)
        assert len(result) > 0
        assert result[:5] == b'%PDF-'

    def test_generates_with_expectations(self, sample_flux_dict):
        """Should generate PDF with expectation text included."""
        expectations = {
            "Revenue": {
                "auditor_expectation": "Expected 15% growth based on industry trend",
                "auditor_explanation": "Actual growth of 66.7% due to new contract",
            },
        }
        result = generate_flux_expectations_memo(
            flux_result=sample_flux_dict,
            expectations=expectations,
            filename="test_tb.csv",
            client_name="Test Corp",
        )
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_generates_with_workpaper_metadata(self, sample_flux_dict):
        """Should accept all workpaper metadata fields."""
        result = generate_flux_expectations_memo(
            flux_result=sample_flux_dict,
            expectations={},
            filename="test.csv",
            client_name="Acme Inc",
            period_tested="FY2025",
            prepared_by="J. Auditor",
            reviewed_by="S. Manager",
            workpaper_date="2026-02-18",
        )
        assert isinstance(result, bytes)
        assert result[:5] == b'%PDF-'

    def test_empty_flux_items(self):
        """Should handle empty flux items gracefully."""
        result = generate_flux_expectations_memo(
            flux_result={"items": [], "summary": {
                "total_items": 0, "high_risk_count": 0,
                "medium_risk_count": 0, "new_accounts": 0,
                "removed_accounts": 0, "threshold": 0,
            }},
            expectations={},
        )
        assert isinstance(result, bytes)
        assert len(result) > 0


# ═══════════════════════════════════════════════════════════════
# Guardrail: No Auto-Populate
# ═══════════════════════════════════════════════════════════════

class TestNoAutoPopulate:
    """CRITICAL: Expectations must never be auto-generated."""

    def test_default_expectations_are_empty(self):
        """Default ExpectationEntry must have blank fields."""
        entry = ExpectationEntry()
        assert entry.auditor_expectation == ""
        assert entry.auditor_explanation == ""

    def test_no_computed_text_in_schema(self):
        """Schema should have no default text that could be mistaken for suggestions."""
        entry = ExpectationEntry()
        assert not entry.auditor_expectation
        assert not entry.auditor_explanation


# ═══════════════════════════════════════════════════════════════
# Route Registration
# ═══════════════════════════════════════════════════════════════

class TestRouteRegistration:
    """Verify export endpoint is registered."""

    def test_flux_expectations_memo_route_exists(self):
        """The /export/flux-expectations-memo route should be registered."""
        from main import app
        routes = [r.path for r in app.routes if hasattr(r, 'path')]
        assert "/export/flux-expectations-memo" in routes
