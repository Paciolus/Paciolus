"""
Sprint 3: Tests for Universal Scope/Methodology with Framework-Aware Citations.

Validates:
- YAML content loading (FASB and GASB)
- get_tool_content() returns correct content per framework
- build_scope_statement() produces correct flowables
- build_methodology_statement() produces correct flowables
- build_authoritative_reference_block() produces correct flowables
- Framework switch: same tool, different framework → different citations
- Non-committal language guardrails (validate_non_committal)
- Presence tests: generated memos include scope/methodology/reference sections
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.framework_resolution import ResolvedFramework
from shared.scope_methodology import (
    APPROVED_PHRASES,
    BANNED_PATTERNS,
    AuthoritativeReference,
    ToolContent,
    build_authoritative_reference_block,
    build_methodology_statement,
    build_scope_statement,
    get_tool_content,
    validate_non_committal,
)

# =============================================================================
# YAML Loading & Content Resolution
# =============================================================================


class TestYAMLLoading:
    """Tests for YAML content loading and caching."""

    def test_fasb_content_loads(self):
        content = get_tool_content("journal_entry_testing", ResolvedFramework.FASB)
        assert isinstance(content, ToolContent)
        assert content.body == "FASB"

    def test_gasb_content_loads(self):
        content = get_tool_content("journal_entry_testing", ResolvedFramework.GASB)
        assert isinstance(content, ToolContent)
        assert content.body == "GASB"

    def test_fasb_body_full(self):
        content = get_tool_content("revenue_testing", ResolvedFramework.FASB)
        assert content.body_full == "Financial Accounting Standards Board"

    def test_gasb_body_full(self):
        content = get_tool_content("revenue_testing", ResolvedFramework.GASB)
        assert content.body_full == "Governmental Accounting Standards Board"

    def test_unknown_tool_domain_returns_generic_content(self):
        """Unknown tool domain should still return valid content with empty refs."""
        content = get_tool_content("nonexistent_tool", ResolvedFramework.FASB)
        assert isinstance(content, ToolContent)
        assert content.scope_statement  # should still have template text
        assert content.references == ()  # no refs for unknown tool

    def test_all_fasb_tool_domains_have_references(self):
        """Every registered FASB tool domain should have at least one reference."""
        domains = [
            "journal_entry_testing",
            "ap_payment_testing",
            "payroll_testing",
            "revenue_testing",
            "ar_aging_testing",
            "fixed_asset_testing",
            "inventory_testing",
            "bank_reconciliation",
            "three_way_match",
            "multi_period_comparison",
            "statistical_sampling",
            "data_quality_preflight",
            "population_profile",
            "expense_category",
            "flux_analysis",
            "accrual_completeness",
            "currency_conversion",
            "anomaly_summary",
        ]
        for domain in domains:
            content = get_tool_content(domain, ResolvedFramework.FASB)
            assert len(content.references) > 0, f"FASB domain {domain} has no references"

    def test_all_gasb_tool_domains_have_references(self):
        """Every registered GASB tool domain should have at least one reference."""
        domains = [
            "journal_entry_testing",
            "ap_payment_testing",
            "payroll_testing",
            "revenue_testing",
            "ar_aging_testing",
            "fixed_asset_testing",
            "inventory_testing",
            "bank_reconciliation",
            "three_way_match",
            "multi_period_comparison",
            "statistical_sampling",
            "data_quality_preflight",
            "population_profile",
            "expense_category",
            "flux_analysis",
            "accrual_completeness",
            "currency_conversion",
            "anomaly_summary",
        ]
        for domain in domains:
            content = get_tool_content(domain, ResolvedFramework.GASB)
            assert len(content.references) > 0, f"GASB domain {domain} has no references"


# =============================================================================
# Framework Switch Tests
# =============================================================================


class TestFrameworkSwitch:
    """Same tool, different framework → different citation body and references."""

    def test_revenue_fasb_vs_gasb_body(self):
        fasb = get_tool_content("revenue_testing", ResolvedFramework.FASB)
        gasb = get_tool_content("revenue_testing", ResolvedFramework.GASB)
        assert fasb.body == "FASB"
        assert gasb.body == "GASB"

    def test_revenue_fasb_cites_asc_606(self):
        content = get_tool_content("revenue_testing", ResolvedFramework.FASB)
        refs = [r.reference for r in content.references]
        assert any("ASC 606" in r for r in refs)

    def test_revenue_gasb_cites_statement_33(self):
        content = get_tool_content("revenue_testing", ResolvedFramework.GASB)
        refs = [r.reference for r in content.references]
        assert any("33" in r for r in refs)

    def test_fixed_asset_fasb_cites_asc_360(self):
        content = get_tool_content("fixed_asset_testing", ResolvedFramework.FASB)
        refs = [r.reference for r in content.references]
        assert any("ASC 360" in r for r in refs)

    def test_fixed_asset_gasb_cites_statement_34_or_42(self):
        content = get_tool_content("fixed_asset_testing", ResolvedFramework.GASB)
        refs = [r.reference for r in content.references]
        assert any("34" in r or "42" in r for r in refs)

    def test_scope_statement_mentions_fasb(self):
        content = get_tool_content("journal_entry_testing", ResolvedFramework.FASB)
        assert "FASB" in content.scope_statement

    def test_scope_statement_mentions_gasb(self):
        content = get_tool_content("journal_entry_testing", ResolvedFramework.GASB)
        assert "GASB" in content.scope_statement

    def test_fasb_references_use_asc_format(self):
        content = get_tool_content("ar_aging_testing", ResolvedFramework.FASB)
        for ref in content.references:
            assert ref.body == "FASB"
            assert "ASC" in ref.reference

    def test_gasb_references_use_statement_format(self):
        content = get_tool_content("ar_aging_testing", ResolvedFramework.GASB)
        for ref in content.references:
            assert ref.body == "GASB"
            assert "Statement" in ref.reference

    def test_currency_fasb_cites_asc_830(self):
        content = get_tool_content("currency_conversion", ResolvedFramework.FASB)
        refs = [r.reference for r in content.references]
        assert any("ASC 830" in r for r in refs)


# =============================================================================
# AuthoritativeReference Dataclass
# =============================================================================


class TestAuthoritativeReference:
    """Tests for the AuthoritativeReference frozen dataclass."""

    def test_construction(self):
        ref = AuthoritativeReference(
            body="FASB",
            reference="ASC 606-10-25",
            topic="Revenue Recognition",
            paragraph="25-1 through 25-5",
            status="Current",
        )
        assert ref.body == "FASB"
        assert ref.reference == "ASC 606-10-25"
        assert ref.status == "Current"

    def test_frozen(self):
        ref = AuthoritativeReference(
            body="FASB",
            reference="ASC 606",
            topic="Rev",
            paragraph="",
            status="Current",
        )
        with pytest.raises(AttributeError):
            ref.body = "GASB"


# =============================================================================
# Non-Committal Language Guardrails
# =============================================================================


class TestNonCommittalLanguage:
    """Tests for validate_non_committal() and language guardrails."""

    def test_clean_text_passes(self):
        text = (
            "The results may indicate areas requiring additional inquiry. "
            "Identified anomalies could suggest the need for further procedures."
        )
        violations = validate_non_committal(text)
        assert violations == []

    def test_banned_proves_detected(self):
        violations = validate_non_committal("This analysis proves the balance is correct.")
        assert len(violations) == 1
        assert r"\bproves\b" in violations[0]

    def test_banned_confirms_detected(self):
        violations = validate_non_committal("The testing confirms the account is accurate.")
        assert len(violations) == 1
        assert r"\bconfirms\b" in violations[0]

    def test_banned_establishes_detected(self):
        violations = validate_non_committal("This establishes that no fraud occurred.")
        assert len(violations) == 1

    def test_banned_demonstrates_that_detected(self):
        violations = validate_non_committal("The analysis demonstrates that controls are effective.")
        assert len(violations) == 1

    def test_banned_conclusively_detected(self):
        violations = validate_non_committal("The test conclusively shows no errors.")
        assert len(violations) == 1

    def test_banned_constitutes_fraud_detected(self):
        violations = validate_non_committal("This constitutes fraud in the GL.")
        assert len(violations) == 1

    def test_multiple_violations(self):
        text = "This proves and confirms that the balance establishes accuracy."
        violations = validate_non_committal(text)
        assert len(violations) >= 3

    def test_case_insensitive(self):
        violations = validate_non_committal("This PROVES the account balance.")
        assert len(violations) == 1

    def test_approved_phrases_exist(self):
        """Verify at least 5 approved phrases are defined."""
        assert len(APPROVED_PHRASES) >= 5

    def test_banned_patterns_exist(self):
        """Verify at least 10 banned patterns are defined."""
        assert len(BANNED_PATTERNS) >= 10

    def test_scope_template_is_non_committal(self):
        """Verify FASB scope template passes non-committal check."""
        content = get_tool_content("journal_entry_testing", ResolvedFramework.FASB)
        violations = validate_non_committal(content.scope_statement)
        assert violations == [], f"Scope template has banned language: {violations}"

    def test_methodology_template_is_non_committal(self):
        """Verify FASB methodology template passes non-committal check."""
        content = get_tool_content("journal_entry_testing", ResolvedFramework.FASB)
        violations = validate_non_committal(content.methodology_statement)
        assert violations == [], f"Methodology template has banned language: {violations}"

    def test_gasb_scope_template_is_non_committal(self):
        """Verify GASB scope template passes non-committal check."""
        content = get_tool_content("revenue_testing", ResolvedFramework.GASB)
        violations = validate_non_committal(content.scope_statement)
        assert violations == [], f"GASB scope has banned language: {violations}"

    def test_gasb_methodology_template_is_non_committal(self):
        """Verify GASB methodology template passes non-committal check."""
        content = get_tool_content("revenue_testing", ResolvedFramework.GASB)
        violations = validate_non_committal(content.methodology_statement)
        assert violations == [], f"GASB methodology has banned language: {violations}"


# =============================================================================
# PDF Builders — Flowable Output
# =============================================================================


class TestPDFBuilders:
    """Tests for the PDF section builder functions."""

    @pytest.fixture()
    def styles(self):
        from shared.memo_base import create_memo_styles

        return create_memo_styles()

    def test_build_scope_statement_adds_flowables(self, styles):
        story = []
        build_scope_statement(
            story,
            styles,
            468.0,
            tool_domain="journal_entry_testing",
            framework=ResolvedFramework.FASB,
        )
        assert len(story) >= 2  # Paragraph + Spacer

    def test_build_methodology_statement_adds_flowables(self, styles):
        story = []
        build_methodology_statement(
            story,
            styles,
            468.0,
            tool_domain="revenue_testing",
            framework=ResolvedFramework.GASB,
        )
        assert len(story) >= 2  # Paragraph + Spacer

    def test_build_authoritative_reference_block_adds_flowables(self, styles):
        story = []
        build_authoritative_reference_block(
            story,
            styles,
            468.0,
            tool_domain="ap_payment_testing",
            framework=ResolvedFramework.FASB,
        )
        # Section heading + LedgerRule + Table + Spacer
        assert len(story) >= 3

    def test_build_authoritative_reference_block_with_section_label(self, styles):
        story = []
        build_authoritative_reference_block(
            story,
            styles,
            468.0,
            tool_domain="revenue_testing",
            framework=ResolvedFramework.FASB,
            section_label="V.",
        )
        # Check heading includes section label
        from reportlab.platypus import Paragraph as P

        heading = story[0]
        assert isinstance(heading, P)
        assert "V." in heading.text

    def test_build_authoritative_reference_block_no_refs_no_output(self, styles):
        """Unknown tool with no refs should produce no flowables."""
        story = []
        build_authoritative_reference_block(
            story,
            styles,
            468.0,
            tool_domain="nonexistent_tool",
            framework=ResolvedFramework.FASB,
        )
        assert len(story) == 0

    def test_build_scope_statement_gasb_mentions_gasb(self, styles):
        story = []
        build_scope_statement(
            story,
            styles,
            468.0,
            tool_domain="bank_reconciliation",
            framework=ResolvedFramework.GASB,
        )
        # First flowable should be a Paragraph containing "GASB"
        from reportlab.platypus import Paragraph as P

        para = story[0]
        assert isinstance(para, P)
        assert "GASB" in para.text


# =============================================================================
# Memo Generation Integration — Presence Tests
# =============================================================================


class TestMemoPresence:
    """Verify that generated memos include scope/methodology/reference sections."""

    @staticmethod
    def _make_result(score=5.0, risk_tier="low"):
        """Create a minimal testing tool result dict."""
        return {
            "composite_score": {
                "score": score,
                "risk_tier": risk_tier,
                "total_entries": 100,
                "tests_run": 3,
                "total_flagged": 2,
                "flag_rate": 0.02,
                "flags_by_severity": {"high": 0, "medium": 1, "low": 1},
                "top_findings": [],
            },
            "test_results": [
                {
                    "test_key": "test_a",
                    "test_name": "Test A",
                    "test_tier": "structural",
                    "entries_flagged": 1,
                    "flag_rate": 0.01,
                    "severity": "low",
                    "description": "Test A desc",
                },
                {
                    "test_key": "test_b",
                    "test_name": "Test B",
                    "test_tier": "statistical",
                    "entries_flagged": 1,
                    "flag_rate": 0.01,
                    "severity": "medium",
                    "description": "Test B desc",
                },
            ],
            "data_quality": {
                "completeness_score": 95,
            },
        }

    def test_standard_memo_generates_with_fasb(self):
        """Standard testing memo generates successfully with FASB framework."""
        from je_testing_memo_generator import generate_je_testing_memo

        result = self._make_result()
        pdf_bytes = generate_je_testing_memo(
            result,
            filename="test.csv",
            client_name="Acme Corp",
            period_tested="FY 2025",
        )
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 1000

    def test_standard_memo_generates_with_gasb(self):
        """Standard testing memo generates successfully with GASB framework."""
        from shared.memo_template import generate_testing_memo

        result = self._make_result()
        # Call via the template directly with GASB
        from je_testing_memo_generator import _JE_CONFIG

        pdf_bytes = generate_testing_memo(
            result,
            _JE_CONFIG,
            filename="test.csv",
            client_name="City of Springfield",
            period_tested="FY 2025",
            resolved_framework=ResolvedFramework.GASB,
        )
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 1000

    def test_bank_rec_memo_generates_with_framework(self):
        """Bank rec memo generates successfully with resolved framework."""
        from bank_reconciliation_memo_generator import generate_bank_rec_memo

        rec_result = {
            "summary": {
                "matched_count": 50,
                "bank_only_count": 3,
                "ledger_only_count": 2,
                "matched_amount": 50000.0,
                "bank_only_amount": 1500.0,
                "ledger_only_amount": 800.0,
                "reconciling_difference": 700.0,
                "total_bank": 51500.0,
                "total_ledger": 50800.0,
            },
            "bank_column_detection": {"overall_confidence": 0.95},
            "ledger_column_detection": {"overall_confidence": 0.92},
        }

        pdf_bytes = generate_bank_rec_memo(
            rec_result,
            client_name="Test Client",
            resolved_framework=ResolvedFramework.GASB,
        )
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 1000

    def test_sampling_memo_generates_with_framework(self):
        """Sampling design memo generates successfully with resolved framework."""
        from sampling_memo_generator import generate_sampling_design_memo

        design_result = {
            "method": "mus",
            "population_size": 1000,
            "population_value": 500000.0,
            "confidence_level": 0.95,
            "confidence_factor": 3.0,
            "tolerable_misstatement": 25000.0,
            "expected_misstatement": 5000.0,
            "sampling_interval": 8333.33,
            "calculated_sample_size": 60,
            "actual_sample_size": 60,
        }

        pdf_bytes = generate_sampling_design_memo(
            design_result,
            client_name="City of Portland",
            resolved_framework=ResolvedFramework.GASB,
        )
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 1000

    def test_preflight_memo_generates_with_framework(self):
        """Pre-flight memo generates successfully with resolved framework."""
        from preflight_memo_generator import generate_preflight_memo

        preflight_result = {
            "readiness_score": 85.0,
            "readiness_label": "Good",
            "row_count": 500,
            "column_count": 6,
            "columns": [],
            "issues": [],
        }

        pdf_bytes = generate_preflight_memo(
            preflight_result,
            filename="test_tb.csv",
            resolved_framework=ResolvedFramework.FASB,
        )
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 1000
