"""
Sprint 7: Signoff Section Deprecation Tests.

Validates:
- Default memo output does NOT contain "Prepared By" or "Reviewed By"
- Legacy opt-in (include_signoff=True) still renders signoff
- WorkpaperMetadata.include_signoff defaults to False
- FinancialStatementsInput.include_signoff defaults to False
- AuditResultInput.include_signoff defaults to False
- Anomaly summary generator no longer contains signoff table
- build_workpaper_signoff() returns early when include_signoff=False
"""

import inspect
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.export_schemas import (
    FinancialStatementsInput,
    WorkpaperMetadata,
)
from shared.memo_base import build_workpaper_signoff, create_memo_styles
from shared.memo_template import TestingMemoConfig, generate_testing_memo
from shared.schemas import AuditResultInput

# ─── Fixtures ────────────────────────────────────────────────────────────


def _make_config() -> TestingMemoConfig:
    return TestingMemoConfig(
        title="Test Memo",
        ref_prefix="TST",
        entry_label="Total Entries Tested",
        flagged_label="Total Entries Flagged",
        log_prefix="test_memo",
        domain="test domain",
        test_descriptions={"test_a": "Description A"},
        methodology_intro="Automated tests were applied per ISA 999:",
        risk_assessments={
            "low": "LOW risk.",
            "elevated": "ELEVATED risk.",
            "moderate": "MODERATE risk.",
            "high": "HIGH risk.",
        },
        isa_reference="ISA 999",
    )


def _make_result() -> dict:
    return {
        "composite_score": {
            "score": 5.0,
            "risk_tier": "low",
            "total_entries": 100,
            "total_flagged": 2,
            "flag_rate": 0.02,
            "tests_run": 1,
            "flags_by_severity": {"high": 1, "medium": 0, "low": 1},
            "top_findings": [],
        },
        "test_results": [
            {
                "test_key": "test_a",
                "test_name": "Test A",
                "test_tier": "structural",
                "entries_flagged": 1,
                "flag_rate": 0.01,
                "severity": "high",
            },
        ],
        "data_quality": {"completeness_score": 95.0},
    }


# ─── Schema Default Tests ────────────────────────────────────────────────


class TestSchemaDefaults:
    """Verify that include_signoff defaults to False on all relevant schemas."""

    def test_workpaper_metadata_default(self):
        m = WorkpaperMetadata(filename="test.pdf")
        assert m.include_signoff is False

    def test_workpaper_metadata_explicit_true(self):
        m = WorkpaperMetadata(filename="test.pdf", include_signoff=True)
        assert m.include_signoff is True

    def test_financial_statements_input_default(self):
        m = FinancialStatementsInput(lead_sheet_grouping={})
        assert m.include_signoff is False

    def test_audit_result_input_default(self):
        m = AuditResultInput(
            accounts=[],
            materiality_threshold=1000.0,
            material_count=0,
            immaterial_count=0,
            status="balanced",
            balanced=True,
            total_debits=0.0,
            total_credits=0.0,
            difference=0.0,
            row_count=0,
            message="OK",
            abnormal_balances=[],
            has_risk_alerts=False,
        )
        assert m.include_signoff is False


# ─── build_workpaper_signoff Gate Tests ──────────────────────────────────


class TestBuildWorkpaperSignoffGate:
    """Verify that build_workpaper_signoff respects include_signoff flag."""

    def test_default_does_not_render(self):
        """With default include_signoff=False, no elements are appended."""
        story = []
        styles = create_memo_styles()
        build_workpaper_signoff(
            story,
            styles,
            500.0,
            prepared_by="Auditor A",
            reviewed_by="Reviewer B",
            workpaper_date="2025-01-01",
        )
        assert len(story) == 0

    def test_explicit_false_does_not_render(self):
        story = []
        styles = create_memo_styles()
        build_workpaper_signoff(
            story,
            styles,
            500.0,
            prepared_by="Auditor A",
            reviewed_by="Reviewer B",
            include_signoff=False,
        )
        assert len(story) == 0

    def test_explicit_true_renders(self):
        """With include_signoff=True AND names provided, signoff is rendered."""
        story = []
        styles = create_memo_styles()
        build_workpaper_signoff(
            story,
            styles,
            500.0,
            prepared_by="Auditor A",
            reviewed_by="Reviewer B",
            workpaper_date="2025-01-01",
            include_signoff=True,
        )
        assert len(story) > 0

    def test_explicit_true_no_names_does_not_render(self):
        """With include_signoff=True but no names, signoff is still empty."""
        story = []
        styles = create_memo_styles()
        build_workpaper_signoff(
            story,
            styles,
            500.0,
            include_signoff=True,
        )
        assert len(story) == 0


# ─── Standard Testing Memo Default (No Signoff) ─────────────────────────


class TestStandardMemoDefaultNoSignoff:
    """Default memo output should NOT contain signoff elements."""

    def test_default_memo_same_size_as_no_names(self):
        """A default memo with prepared_by should be the same size as one without,
        because signoff is gated off by default."""
        config = _make_config()
        result = _make_result()
        pdf_with_names = generate_testing_memo(
            result,
            config,
            prepared_by="Auditor A",
            reviewed_by="Reviewer B",
            workpaper_date="2025-01-01",
        )
        pdf_without_names = generate_testing_memo(result, config)
        assert isinstance(pdf_with_names, bytes)
        assert isinstance(pdf_without_names, bytes)
        # Both should be roughly equal since signoff is not rendered
        assert abs(len(pdf_with_names) - len(pdf_without_names)) < 200

    def test_no_args_memo_generates_cleanly(self):
        """Memo with zero signoff args still generates successfully."""
        config = _make_config()
        result = _make_result()
        pdf = generate_testing_memo(result, config)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 0


# ─── Legacy Opt-In Tests ────────────────────────────────────────────────


class TestLegacyOptIn:
    """Legacy include_signoff=True path should still render signoff."""

    def test_legacy_opt_in_produces_larger_pdf(self):
        """With include_signoff=True, the PDF should be larger than without."""
        config = _make_config()
        result = _make_result()
        pdf_with = generate_testing_memo(
            result,
            config,
            prepared_by="Auditor A",
            reviewed_by="Reviewer B",
            workpaper_date="2025-01-01",
            include_signoff=True,
        )
        pdf_without = generate_testing_memo(
            result,
            config,
            prepared_by="Auditor A",
            reviewed_by="Reviewer B",
            workpaper_date="2025-01-01",
            include_signoff=False,
        )
        assert isinstance(pdf_with, bytes)
        assert isinstance(pdf_without, bytes)
        # The PDF with signoff should be meaningfully larger
        assert len(pdf_with) > len(pdf_without)


# ─── Anomaly Summary Generator Tests ────────────────────────────────────


class TestAnomalySummaryNoSignoff:
    """Anomaly summary generator should no longer contain signoff table."""

    def test_source_has_no_signoff_table(self):
        """The anomaly summary generator source should not contain signoff data."""
        source_path = Path(__file__).parent.parent / "anomaly_summary_generator.py"
        source = source_path.read_text(encoding="utf-8")
        assert "signoff_data" not in source
        assert "signoff_table" not in source


# ─── Generator Signature Audit ──────────────────────────────────────────


GENERATOR_MODULES = [
    "bank_reconciliation_memo_generator",
    "three_way_match_memo_generator",
    "multi_period_memo_generator",
    "currency_memo_generator",
    "sampling_memo_generator",
    "preflight_memo_generator",
    "population_profile_memo",
    "expense_category_memo",
    "accrual_completeness_memo",
    "flux_expectations_memo",
    "je_testing_memo_generator",
    "ap_testing_memo_generator",
    "payroll_testing_memo_generator",
    "revenue_testing_memo_generator",
    "ar_aging_memo_generator",
    "fixed_asset_testing_memo_generator",
    "inventory_testing_memo_generator",
]


class TestAllGeneratorsHaveIncludeSignoff:
    """Ensure every memo generator accepts include_signoff parameter."""

    # Utility functions re-exported from shared modules (not memo generators)
    _SKIP_FUNCTIONS = {"generate_reference_number"}

    @pytest.mark.parametrize("module_name", GENERATOR_MODULES)
    def test_generator_has_include_signoff_param(self, module_name: str):
        """Every public generate_*_memo() function should accept include_signoff."""
        mod = __import__(module_name)
        # Find the public generate_* function(s) that are memo generators
        gen_funcs = [
            getattr(mod, name)
            for name in dir(mod)
            if (name.startswith("generate_") and callable(getattr(mod, name)) and name not in self._SKIP_FUNCTIONS)
        ]
        assert gen_funcs, f"No generate_* function found in {module_name}"
        for func in gen_funcs:
            sig = inspect.signature(func)
            assert "include_signoff" in sig.parameters, (
                f"{module_name}.{func.__name__}() missing include_signoff parameter"
            )
            # Default should be False
            param = sig.parameters["include_signoff"]
            assert param.default is False, f"{module_name}.{func.__name__}() include_signoff default should be False"
