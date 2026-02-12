"""
Sprint 157: Tests for Shared Memo Template.

Validates:
- TestingMemoConfig dataclass construction
- generate_testing_memo() PDF generation with standard config
- Custom scope builder callback
- Custom extra sections callback (Benford-style)
- Custom finding formatter callback (Payroll-style)
- Section numbering with/without optional sections
- _roman() helper
- All 4 risk tier branches
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.memo_template import (
    TestingMemoConfig, generate_testing_memo, _roman,
)


# =============================================================================
# FIXTURES
# =============================================================================

def _make_config(**overrides) -> TestingMemoConfig:
    """Create a minimal TestingMemoConfig for testing."""
    defaults = dict(
        title="Test Memo",
        ref_prefix="TST",
        entry_label="Total Entries Tested",
        flagged_label="Total Entries Flagged",
        log_prefix="test_memo",
        domain="test domain",
        test_descriptions={
            "test_a": "Description A",
            "test_b": "Description B",
        },
        methodology_intro="Automated tests were applied per ISA 999:",
        risk_assessments={
            "low": "LOW risk assessment text.",
            "elevated": "ELEVATED risk assessment text.",
            "moderate": "MODERATE risk assessment text.",
            "high": "HIGH risk assessment text.",
        },
        isa_reference="ISA 999",
    )
    defaults.update(overrides)
    return TestingMemoConfig(**defaults)


def _make_result(
    score: float = 5.0,
    risk_tier: str = "low",
    total_flagged: int = 2,
    top_findings: list | None = None,
) -> dict:
    """Build a minimal testing result dict."""
    return {
        "composite_score": {
            "score": score,
            "risk_tier": risk_tier,
            "total_entries": 100,
            "total_flagged": total_flagged,
            "flag_rate": total_flagged / 100,
            "tests_run": 2,
            "flags_by_severity": {"high": 1, "medium": 0, "low": 1},
            "top_findings": top_findings or [],
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
            {
                "test_key": "test_b",
                "test_name": "Test B",
                "test_tier": "statistical",
                "entries_flagged": 1,
                "flag_rate": 0.01,
                "severity": "low",
            },
        ],
        "data_quality": {
            "completeness_score": 95.0,
        },
    }


# =============================================================================
# ROMAN NUMERAL HELPER
# =============================================================================

class TestRomanHelper:
    """Tests for the _roman() helper."""

    def test_roman_1_through_10(self):
        expected = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V",
                    6: "VI", 7: "VII", 8: "VIII", 9: "IX", 10: "X"}
        for n, roman in expected.items():
            assert _roman(n) == roman

    def test_roman_beyond_10_falls_back(self):
        assert _roman(11) == "11"
        assert _roman(99) == "99"


# =============================================================================
# CONFIG CONSTRUCTION
# =============================================================================

class TestTestingMemoConfig:
    """Tests for TestingMemoConfig dataclass."""

    def test_config_basic_construction(self):
        config = _make_config()
        assert config.title == "Test Memo"
        assert config.ref_prefix == "TST"
        assert config.isa_reference == "ISA 999"

    def test_config_default_isa_reference(self):
        config = TestingMemoConfig(
            title="T", ref_prefix="T", entry_label="E",
            flagged_label="F", log_prefix="t", domain="d",
            test_descriptions={}, methodology_intro="M",
            risk_assessments={"low": "", "elevated": "", "moderate": "", "high": ""},
        )
        assert config.isa_reference == "applicable professional standards"

    def test_config_risk_assessments_keys(self):
        config = _make_config()
        assert set(config.risk_assessments.keys()) == {"low", "elevated", "moderate", "high"}


# =============================================================================
# PDF GENERATION — STANDARD
# =============================================================================

class TestGenerateTestingMemo:
    """Tests for generate_testing_memo() output."""

    def test_returns_bytes(self):
        config = _make_config()
        result = _make_result()
        pdf = generate_testing_memo(result, config)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_pdf_starts_with_pdf_header(self):
        config = _make_config()
        result = _make_result()
        pdf = generate_testing_memo(result, config)
        assert pdf[:5] == b"%PDF-"

    def test_with_client_name(self):
        config = _make_config()
        result = _make_result()
        pdf = generate_testing_memo(result, config, client_name="Acme Corp")
        assert isinstance(pdf, bytes)

    def test_with_period_tested(self):
        config = _make_config()
        result = _make_result()
        pdf = generate_testing_memo(result, config, period_tested="FY 2025")
        assert isinstance(pdf, bytes)

    def test_with_workpaper_signoff(self):
        config = _make_config()
        result = _make_result()
        pdf = generate_testing_memo(
            result, config,
            prepared_by="Auditor A",
            reviewed_by="Reviewer B",
            workpaper_date="2025-01-01",
        )
        assert isinstance(pdf, bytes)

    def test_with_top_findings(self):
        config = _make_config()
        result = _make_result(top_findings=["Finding 1", "Finding 2", "Finding 3"])
        pdf = generate_testing_memo(result, config)
        assert isinstance(pdf, bytes)


# =============================================================================
# RISK TIER BRANCHES
# =============================================================================

class TestRiskTierBranches:
    """Ensure all 4 risk tier conclusion branches are reachable."""

    def test_low_risk_branch(self):
        config = _make_config()
        result = _make_result(score=5.0)
        pdf = generate_testing_memo(result, config)
        assert isinstance(pdf, bytes)

    def test_elevated_risk_branch(self):
        config = _make_config()
        result = _make_result(score=15.0, risk_tier="elevated")
        pdf = generate_testing_memo(result, config)
        assert isinstance(pdf, bytes)

    def test_moderate_risk_branch(self):
        config = _make_config()
        result = _make_result(score=35.0, risk_tier="moderate")
        pdf = generate_testing_memo(result, config)
        assert isinstance(pdf, bytes)

    def test_high_risk_branch(self):
        config = _make_config()
        result = _make_result(score=60.0, risk_tier="high")
        pdf = generate_testing_memo(result, config)
        assert isinstance(pdf, bytes)


# =============================================================================
# CUSTOM SCOPE BUILDER
# =============================================================================

class TestCustomScopeBuilder:
    """Tests for the build_scope callback."""

    def test_custom_scope_called(self):
        scope_called = []

        def custom_scope(story, styles, doc_width, composite, data_quality, period_tested):
            scope_called.append(True)

        config = _make_config()
        result = _make_result()
        pdf = generate_testing_memo(result, config, build_scope=custom_scope)
        assert isinstance(pdf, bytes)
        assert len(scope_called) == 1

    def test_custom_scope_receives_period(self):
        received_period = []

        def custom_scope(story, styles, doc_width, composite, data_quality, period_tested):
            received_period.append(period_tested)

        config = _make_config()
        result = _make_result()
        generate_testing_memo(
            result, config,
            period_tested="Q4 2025",
            build_scope=custom_scope,
        )
        assert received_period == ["Q4 2025"]


# =============================================================================
# CUSTOM EXTRA SECTIONS
# =============================================================================

class TestCustomExtraSections:
    """Tests for the build_extra_sections callback."""

    def test_extra_sections_called_and_increments_counter(self):
        calls = []

        def extra_sections(story, styles, doc_width, result, section_counter):
            calls.append(section_counter)
            return section_counter + 1  # simulates adding one section

        config = _make_config()
        result = _make_result(top_findings=["Finding"])
        pdf = generate_testing_memo(result, config, build_extra_sections=extra_sections)
        assert isinstance(pdf, bytes)
        # With findings: IV=KEY FINDINGS (counter goes to 5), extra gets 5
        assert calls == [5]

    def test_extra_sections_without_findings(self):
        calls = []

        def extra_sections(story, styles, doc_width, result, section_counter):
            calls.append(section_counter)
            return section_counter + 1

        config = _make_config()
        result = _make_result(top_findings=[])
        pdf = generate_testing_memo(result, config, build_extra_sections=extra_sections)
        assert isinstance(pdf, bytes)
        # No findings: extra gets 4 (right after results)
        assert calls == [4]


# =============================================================================
# CUSTOM FINDING FORMATTER
# =============================================================================

class TestCustomFindingFormatter:
    """Tests for the format_finding callback."""

    def test_dict_finding_formatter(self):
        def fmt(finding):
            if isinstance(finding, dict):
                return f"{finding['name']} - {finding['issue']}"
            return str(finding)

        config = _make_config()
        result = _make_result(top_findings=[
            {"name": "John", "issue": "Duplicate"},
            "Simple string finding",
        ])
        pdf = generate_testing_memo(result, config, format_finding=fmt)
        assert isinstance(pdf, bytes)

    def test_default_formatter_handles_strings(self):
        config = _make_config()
        result = _make_result(top_findings=["Finding A", "Finding B"])
        pdf = generate_testing_memo(result, config)
        assert isinstance(pdf, bytes)


# =============================================================================
# INTEGRATION — REAL CONFIGS
# =============================================================================

class TestRealConfigIntegration:
    """Verify actual tool configs generate valid PDFs via the template."""

    def test_ap_testing_memo(self):
        from ap_testing_memo_generator import generate_ap_testing_memo
        result = _make_result(top_findings=["Duplicate payment detected"])
        pdf = generate_ap_testing_memo(result)
        assert pdf[:5] == b"%PDF-"

    def test_payroll_testing_memo(self):
        from payroll_testing_memo_generator import generate_payroll_testing_memo
        result = _make_result(top_findings=[
            {"employee": "John Doe", "issue": "Ghost employee indicator"},
        ])
        pdf = generate_payroll_testing_memo(result)
        assert pdf[:5] == b"%PDF-"

    def test_revenue_testing_memo(self):
        from revenue_testing_memo_generator import generate_revenue_testing_memo
        result = _make_result()
        pdf = generate_revenue_testing_memo(result)
        assert pdf[:5] == b"%PDF-"

    def test_fixed_asset_testing_memo(self):
        from fixed_asset_testing_memo_generator import generate_fixed_asset_testing_memo
        result = _make_result()
        pdf = generate_fixed_asset_testing_memo(result)
        assert pdf[:5] == b"%PDF-"

    def test_inventory_testing_memo(self):
        from inventory_testing_memo_generator import generate_inventory_testing_memo
        result = _make_result()
        pdf = generate_inventory_testing_memo(result)
        assert pdf[:5] == b"%PDF-"

    def test_je_testing_memo_without_benford(self):
        from je_testing_memo_generator import generate_je_testing_memo
        result = _make_result()
        pdf = generate_je_testing_memo(result)
        assert pdf[:5] == b"%PDF-"

    def test_je_testing_memo_with_benford(self):
        from je_testing_memo_generator import generate_je_testing_memo
        result = _make_result(top_findings=["Unusual amount"])
        result["benford_result"] = {
            "passed_prechecks": True,
            "eligible_count": 500,
            "mad": 0.00123,
            "conformity_level": "close_conformity",
            "expected_distribution": {str(d): 0.1 for d in range(1, 10)},
            "actual_distribution": {str(d): 0.1 for d in range(1, 10)},
            "deviation_by_digit": {str(d): 0.0 for d in range(1, 10)},
        }
        pdf = generate_je_testing_memo(result)
        assert pdf[:5] == b"%PDF-"

    def test_ar_aging_memo(self):
        from ar_aging_memo_generator import generate_ar_aging_memo
        result = _make_result()
        result["data_quality"]["total_tb_accounts"] = 50
        result["data_quality"]["total_subledger_entries"] = 200
        result["composite_score"]["has_subledger"] = True
        result["composite_score"]["tests_skipped"] = 2
        pdf = generate_ar_aging_memo(result)
        assert pdf[:5] == b"%PDF-"
