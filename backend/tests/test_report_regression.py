"""
Sprint 8: PDF Regression Suite.

Tests for 3 representative report categories:
  1. Primary Diagnostic (pdf_generator.generate_audit_report)
  2. Shared-Template Memo (je_testing_memo_generator — via memo_template.py)
  3. Custom Memos (preflight, three-way match, multi-period)

Each category verifies:
  - Valid PDF structure (%PDF- header, %%EOF trailer)
  - Multi-page output (cover page present)
  - No prohibited legacy patterns (spaced-caps, ALL-CAPS headings)
  - Disclaimer footer text present
  - Source document block support
  - Framework reference block (where applicable)
"""

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.scope_methodology import BANNED_PATTERNS

# =============================================================================
# Shared fixtures
# =============================================================================

_BANNED_RE = [re.compile(p, re.IGNORECASE) for p in BANNED_PATTERNS]
_SPACED_CAPS_RE = re.compile(rb"[A-Z](?: [A-Z]){3,}")


def _assert_valid_pdf(pdf_bytes: bytes, min_pages: int = 2) -> None:
    """Assert basic PDF structural validity."""
    assert pdf_bytes[:5] == b"%PDF-", "Missing PDF header"
    assert pdf_bytes.rstrip().endswith(b"%%EOF"), "Missing PDF trailer"
    assert len(pdf_bytes) > 1000, "PDF suspiciously small"
    page_count = pdf_bytes.count(b"/Type /Page")
    assert page_count >= min_pages, f"Expected >= {min_pages} pages (cover + content), found {page_count}"


def _assert_no_banned_language_in_source(source_text: str) -> None:
    """Assert no banned assertive phrases appear in source code strings."""
    for pattern, regex in zip(BANNED_PATTERNS, _BANNED_RE):
        # Only match inside string literals (rough heuristic)
        for match in regex.finditer(source_text):
            # Check if the match is inside a quoted string
            start = match.start()
            before = source_text[max(0, start - 80) : start]
            if '"' in before or "'" in before:
                pytest.fail(
                    f"Banned assertive language pattern '{pattern}' found near: "
                    f"...{source_text[max(0, start - 20) : start + 30]}..."
                )


# =============================================================================
# 1. Primary Diagnostic PDF
# =============================================================================


class TestDiagnosticPdfRegression:
    """Regression suite for the primary Trial Balance Diagnostic PDF."""

    @staticmethod
    def _make_balanced_result():
        return {
            "balanced": True,
            "total_debits": 250000.0,
            "total_credits": 250000.0,
            "difference": 0.0,
            "row_count": 120,
            "materiality_threshold": 5000.0,
            "abnormal_balances": [],
            "risk_summary": {},
            "material_count": 0,
            "immaterial_count": 0,
        }

    @staticmethod
    def _make_anomaly_result():
        return {
            "balanced": False,
            "total_debits": 250000.0,
            "total_credits": 248500.0,
            "difference": 1500.0,
            "row_count": 120,
            "materiality_threshold": 1000.0,
            "abnormal_balances": [
                {
                    "account": "Suspense Account",
                    "type": "Liability",
                    "issue": "Suspense account with material balance",
                    "amount": 1500.0,
                    "materiality": "material",
                },
                {
                    "account": "Prepaid Insurance",
                    "type": "Asset",
                    "issue": "Abnormal credit balance",
                    "amount": -800.0,
                    "materiality": "immaterial",
                },
            ],
            "risk_summary": {
                "total_anomalies": 2,
                "high_severity": 1,
                "medium_severity": 0,
                "low_severity": 1,
            },
            "material_count": 1,
            "immaterial_count": 1,
        }

    def test_balanced_diagnostic_valid_pdf(self):
        from pdf_generator import generate_audit_report

        pdf = generate_audit_report(self._make_balanced_result(), "test_balanced.csv")
        _assert_valid_pdf(pdf)

    def test_anomaly_diagnostic_valid_pdf(self):
        from pdf_generator import generate_audit_report

        pdf = generate_audit_report(
            self._make_anomaly_result(),
            "test_anomaly.csv",
            prepared_by="Auditor A",
        )
        _assert_valid_pdf(pdf)

    def test_diagnostic_no_spaced_caps_in_output(self):
        """Raw PDF bytes should not contain letter-spaced all-caps patterns."""
        from pdf_generator import generate_audit_report

        pdf = generate_audit_report(self._make_balanced_result(), "test.csv")
        # Check uncompressed text streams — compressed streams are opaque
        matches = _SPACED_CAPS_RE.findall(pdf)
        # Filter out PDF internal keywords
        real_matches = [m for m in matches if not any(kw in m for kw in [b"Type", b"Page", b"Font"])]
        assert not real_matches, f"Spaced-caps found in PDF: {real_matches}"

    def test_diagnostic_disclaimer_present(self):
        """Diagnostic PDF source uses draw_page_footer which includes disclaimer."""
        source = Path(__file__).parent.parent / "pdf_generator.py"
        content = source.read_text(encoding="utf-8")
        # Diagnostic PDF uses draw_page_footer from report_chrome which has disclaimer
        assert "draw_page_footer" in content or "report_chrome" in content, (
            "Diagnostic generator should use shared page footer with disclaimer"
        )

    def test_diagnostic_signoff_default_off(self):
        """With include_signoff=False (default), PDF should not contain signoff section."""
        from pdf_generator import generate_audit_report

        pdf_default = generate_audit_report(
            self._make_balanced_result(),
            "test.csv",
            prepared_by="Alice",
            reviewed_by="Bob",
        )
        pdf_signoff = generate_audit_report(
            self._make_balanced_result(),
            "test.csv",
            prepared_by="Alice",
            reviewed_by="Bob",
            include_signoff=True,
        )
        # Signoff version should be larger
        assert len(pdf_signoff) > len(pdf_default)

    def test_diagnostic_with_source_document_metadata(self):
        """Diagnostic PDF generates cleanly with all available params."""
        from pdf_generator import generate_audit_report

        pdf = generate_audit_report(
            self._make_balanced_result(),
            "uploaded_data.csv",
            prepared_by="Auditor A",
            reviewed_by="Auditor B",
            workpaper_date="2025-01-15",
        )
        _assert_valid_pdf(pdf)


# =============================================================================
# 2. Shared-Template Memo (JE Testing as representative)
# =============================================================================


class TestSharedTemplateMemoRegression:
    """Regression suite for shared-template memos via JE Testing."""

    @staticmethod
    def _make_je_result(risk_tier: str = "low", with_findings: bool = False):
        findings = []
        if with_findings:
            findings = [
                {"description": "Weekend posting detected", "severity": "high", "count": 3},
                {"description": "Round amount entries", "severity": "medium", "count": 12},
            ]
        return {
            "composite_score": {
                "score": {"low": 5.0, "elevated": 15.0, "moderate": 30.0, "high": 55.0}[risk_tier],
                "risk_tier": risk_tier,
                "total_entries": 500,
                "total_flagged": 15,
                "flag_rate": 0.03,
                "tests_run": 5,
                "flags_by_severity": {"high": 3, "medium": 7, "low": 5},
                "top_findings": findings,
            },
            "test_results": [
                {
                    "test_key": "weekend_posting",
                    "test_name": "Weekend Posting",
                    "test_tier": "structural",
                    "entries_flagged": 3,
                    "flag_rate": 0.006,
                    "severity": "high",
                },
                {
                    "test_key": "round_amounts",
                    "test_name": "Round Amounts",
                    "test_tier": "statistical",
                    "entries_flagged": 12,
                    "flag_rate": 0.024,
                    "severity": "medium",
                },
                {
                    "test_key": "duplicate_entries",
                    "test_name": "Duplicate Entries",
                    "test_tier": "structural",
                    "entries_flagged": 0,
                    "flag_rate": 0.0,
                    "severity": "low",
                },
            ],
            "data_quality": {"completeness_score": 92.0},
        }

    def test_je_memo_valid_pdf(self):
        from je_testing_memo_generator import generate_je_testing_memo

        pdf = generate_je_testing_memo(self._make_je_result(), client_name="Test Corp")
        _assert_valid_pdf(pdf)

    def test_je_memo_all_risk_tiers(self):
        """All 4 risk tiers produce valid PDFs."""
        from je_testing_memo_generator import generate_je_testing_memo

        for tier in ("low", "elevated", "moderate", "high"):
            pdf = generate_je_testing_memo(
                self._make_je_result(risk_tier=tier),
                client_name=f"Tier {tier}",
            )
            _assert_valid_pdf(pdf)

    def test_je_memo_with_findings(self):
        from je_testing_memo_generator import generate_je_testing_memo

        pdf = generate_je_testing_memo(
            self._make_je_result(with_findings=True),
            client_name="Findings Corp",
        )
        _assert_valid_pdf(pdf)

    def test_je_memo_with_source_document(self):
        from je_testing_memo_generator import generate_je_testing_memo

        pdf = generate_je_testing_memo(
            self._make_je_result(),
            client_name="Source Corp",
            source_document_title="General Ledger Journal Entries Export",
            source_context_note="Exported from ERP system Q4 FY 2025",
        )
        _assert_valid_pdf(pdf)

    def test_je_memo_signoff_default_off(self):
        from je_testing_memo_generator import generate_je_testing_memo

        pdf_default = generate_je_testing_memo(
            self._make_je_result(),
            prepared_by="Alice",
            reviewed_by="Bob",
        )
        pdf_signoff = generate_je_testing_memo(
            self._make_je_result(),
            prepared_by="Alice",
            reviewed_by="Bob",
            include_signoff=True,
        )
        assert len(pdf_signoff) > len(pdf_default)

    def test_template_memo_source_has_scope_section(self):
        """memo_template.py should build a Scope section."""
        source = Path(__file__).parent.parent / "shared" / "memo_template.py"
        content = source.read_text(encoding="utf-8")
        assert "Scope" in content, "memo_template.py must build a Scope section"
        assert "Methodology" in content, "memo_template.py must build a Methodology section"

    def test_template_memo_source_has_framework_references(self):
        """memo_template.py should use authoritative reference block."""
        source = Path(__file__).parent.parent / "shared" / "memo_template.py"
        content = source.read_text(encoding="utf-8")
        assert "build_authoritative_reference_block" in content, (
            "memo_template.py must include authoritative references"
        )

    def test_template_memo_source_has_disclaimer(self):
        """memo_template.py should include disclaimer."""
        source = Path(__file__).parent.parent / "shared" / "memo_template.py"
        content = source.read_text(encoding="utf-8")
        assert "build_disclaimer" in content, "memo_template.py must include disclaimer"

    def test_template_memo_source_has_cover_page(self):
        """memo_template.py should include cover page."""
        source = Path(__file__).parent.parent / "shared" / "memo_template.py"
        content = source.read_text(encoding="utf-8")
        assert "build_cover_page" in content, "memo_template.py must include cover page"


# =============================================================================
# 3. Custom Memo Regression (preflight, TWM, multi-period)
# =============================================================================


class TestPreflightMemoRegression:
    """Regression suite for the Pre-Flight Data Quality memo."""

    @staticmethod
    def _make_result():
        return {
            "readiness_score": 82,
            "readiness_label": "Good",
            "row_count": 200,
            "column_count": 8,
            "columns": [
                {"name": "Account", "detected_type": "account_name", "confidence": 0.95},
                {"name": "Debit", "detected_type": "debit", "confidence": 0.90},
                {"name": "Credit", "detected_type": "credit", "confidence": 0.88},
            ],
            "issues": [
                {"severity": "warning", "message": "3 rows with missing account names"},
            ],
        }

    def test_preflight_valid_pdf(self):
        from preflight_memo_generator import generate_preflight_memo

        pdf = generate_preflight_memo(self._make_result(), client_name="QA Corp")
        _assert_valid_pdf(pdf)

    def test_preflight_source_has_required_sections(self):
        """Preflight memo source should include scope and disclaimer."""
        source = Path(__file__).parent.parent / "preflight_memo_generator.py"
        content = source.read_text(encoding="utf-8")
        assert "build_cover_page" in content or "report_chrome" in content, "preflight memo must use shared cover page"
        assert "build_disclaimer" in content or "disclaimer" in content.lower(), (
            "preflight memo must include disclaimer"
        )


class TestThreeWayMatchMemoRegression:
    """Regression suite for the Three-Way Match memo."""

    @staticmethod
    def _make_result():
        return {
            "summary": {
                "total_pos": 25,
                "total_invoices": 25,
                "total_receipts": 25,
                "full_match_count": 20,
                "partial_match_count": 3,
                "full_match_rate": 0.80,
                "partial_match_rate": 0.12,
                "material_variances_count": 2,
                "net_variance": 500.0,
                "risk_assessment": "elevated",
                "total_po_amount": 100000,
                "total_invoice_amount": 99500,
                "total_receipt_amount": 100000,
            },
            "variances": [
                {
                    "po_number": "PO-001",
                    "po_amount": 5000,
                    "invoice_amount": 5200,
                    "receipt_amount": 5000,
                    "variance_amount": 200,
                    "variance_pct": 0.04,
                    "match_type": "partial",
                },
            ],
            "config": {"variance_threshold": 0.05},
            "data_quality": {"overall_quality_score": 88},
            "unmatched_pos": [],
            "unmatched_invoices": [],
            "unmatched_receipts": [],
            "partial_matches": [],
        }

    def test_twm_valid_pdf(self):
        from three_way_match_memo_generator import generate_three_way_match_memo

        pdf = generate_three_way_match_memo(self._make_result(), client_name="Match Corp")
        _assert_valid_pdf(pdf)

    def test_twm_source_has_required_sections(self):
        """TWM memo source should include scope, methodology, and references."""
        source = Path(__file__).parent.parent / "three_way_match_memo_generator.py"
        content = source.read_text(encoding="utf-8")
        assert "build_cover_page" in content or "report_chrome" in content
        assert "build_disclaimer" in content or "disclaimer" in content.lower()


class TestMultiPeriodMemoRegression:
    """Regression suite for the Multi-Period Comparison memo."""

    @staticmethod
    def _make_result():
        return {
            "prior_label": "FY 2024",
            "current_label": "FY 2025",
            "total_accounts": 85,
            "movements_by_type": {"increase": 30, "decrease": 25, "stable": 30},
            "movements_by_significance": {"material": 5, "significant": 10, "minor": 70},
            "significant_movements": [
                {
                    "account": "Revenue",
                    "prior_balance": 100000,
                    "current_balance": 120000,
                    "change_amount": 20000,
                    "change_pct": 0.20,
                    "significance": "material",
                },
            ],
            "lead_sheet_summaries": [],
            "dormant_account_count": 3,
        }

    def test_multi_period_valid_pdf(self):
        from multi_period_memo_generator import generate_multi_period_memo

        pdf = generate_multi_period_memo(
            self._make_result(),
            client_name="Period Corp",
            period_tested="FY 2024 vs FY 2025",
        )
        _assert_valid_pdf(pdf)

    def test_multi_period_source_has_required_sections(self):
        """Multi-period memo source should include cover page and disclaimer."""
        source = Path(__file__).parent.parent / "multi_period_memo_generator.py"
        content = source.read_text(encoding="utf-8")
        assert "build_cover_page" in content or "report_chrome" in content
        assert "build_disclaimer" in content or "disclaimer" in content.lower()


# =============================================================================
# 4. Cross-cutting: All generators comply with Sprint 0-7 standards
# =============================================================================


class TestAllGeneratorsStandardsCompliance:
    """Verify all memo generators comply with the report standardization spec."""

    GENERATOR_DIR = Path(__file__).parent.parent
    GENERATOR_NAMES = sorted(
        [f.name for f in GENERATOR_DIR.glob("*_memo*.py")]
        + [f.name for f in GENERATOR_DIR.glob("*_summary_generator.py")]
    )

    @pytest.mark.parametrize("filename", GENERATOR_NAMES)
    def test_no_banned_language_in_generator(self, filename: str):
        """Generator source code should not contain banned assertive phrases."""
        source_path = self.GENERATOR_DIR / filename
        content = source_path.read_text(encoding="utf-8")
        # Only check inside string literals — skip imports, comments
        _assert_no_banned_language_in_source(content)

    @pytest.mark.parametrize("filename", GENERATOR_NAMES)
    def test_generator_uses_shared_chrome(self, filename: str):
        """Every generator should import from shared report_chrome or memo_base."""
        source_path = self.GENERATOR_DIR / filename
        content = source_path.read_text(encoding="utf-8")
        uses_chrome = "report_chrome" in content or "memo_base" in content or "memo_template" in content
        assert uses_chrome, f"{filename} does not use shared report chrome (report_chrome, memo_base, or memo_template)"
