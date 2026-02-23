"""
Sprint 292: Revenue Concentration Sub-typing + Language Fixes (L1, L3, L4)

Tests:
- F3: Concentration anomaly_type is now category-specific (e.g., "revenue_concentration")
- F3: risk_summary includes both aggregate and sub-type counts
- L1: Accrual narrative uses pure numeric language (no "appears")
- L4: All memo generators have explicit ISA citation in disclaimer
"""

import io

import pandas as pd
import pytest

from accrual_completeness_engine import compute_accrual_completeness

# ═══════════════════════════════════════════════════════════════
# F3: Concentration Sub-typing Tests
# ═══════════════════════════════════════════════════════════════

class TestConcentrationSubTyping:
    """Verify concentration anomaly_type uses category-specific labels."""

    @pytest.fixture
    def revenue_concentration_csv(self):
        """Revenue data with one dominant account (>50%)."""
        data = """Account Name,Debit,Credit
Big Customer Revenue,,80000
Small Customer Revenue,,10000
Other Revenue,,10000
Cash,100000,
"""
        return data.encode("utf-8")

    @pytest.fixture
    def asset_concentration_csv(self):
        """Asset data with one dominant account (>50%)."""
        data = """Account Name,Debit,Credit
Main Bank Account,80000,
Petty Cash,5000,
Receivables,15000,
Revenue,,100000
"""
        return data.encode("utf-8")

    def test_revenue_concentration_anomaly_type(self, revenue_concentration_csv):
        """Revenue concentration should have anomaly_type 'revenue_concentration'."""
        from audit_engine import StreamingAuditor

        auditor = StreamingAuditor(materiality_threshold=0)
        df = pd.read_csv(io.BytesIO(revenue_concentration_csv))
        auditor.process_chunk(df, len(df))

        risks = auditor.detect_concentration_risk()
        revenue_risks = [r for r in risks if r["category"] == "revenue"]

        assert len(revenue_risks) > 0
        for r in revenue_risks:
            assert r["anomaly_type"] == "revenue_concentration"

    def test_asset_concentration_anomaly_type(self, asset_concentration_csv):
        """Asset concentration should have anomaly_type 'asset_concentration'."""
        from audit_engine import StreamingAuditor

        auditor = StreamingAuditor(materiality_threshold=0)
        df = pd.read_csv(io.BytesIO(asset_concentration_csv))
        auditor.process_chunk(df, len(df))

        risks = auditor.detect_concentration_risk()
        asset_risks = [r for r in risks if r["category"] == "asset"]

        assert len(asset_risks) > 0
        for r in asset_risks:
            assert r["anomaly_type"] == "asset_concentration"

    def test_no_generic_concentration_risk_type(self, revenue_concentration_csv):
        """No entry should use the old generic 'concentration_risk' anomaly_type."""
        from audit_engine import StreamingAuditor

        auditor = StreamingAuditor(materiality_threshold=0)
        df = pd.read_csv(io.BytesIO(revenue_concentration_csv))
        auditor.process_chunk(df, len(df))

        risks = auditor.detect_concentration_risk()
        generic = [r for r in risks if r["anomaly_type"] == "concentration_risk"]
        assert len(generic) == 0

    def test_risk_summary_aggregate_concentration(self, revenue_concentration_csv):
        """risk_summary should still contain aggregate concentration_risk count."""
        from audit_engine import audit_trial_balance_streaming

        result = audit_trial_balance_streaming(
            file_bytes=revenue_concentration_csv,
            filename="test.csv",
            materiality_threshold=0,
        )
        risk_summary = result["risk_summary"]
        assert "concentration_risk" in risk_summary["anomaly_types"]
        # Aggregate should count all sub-type concentrations
        assert risk_summary["anomaly_types"]["concentration_risk"] > 0

    def test_risk_summary_sub_type_counts(self, revenue_concentration_csv):
        """risk_summary should include revenue_concentration sub-type count."""
        from audit_engine import audit_trial_balance_streaming

        result = audit_trial_balance_streaming(
            file_bytes=revenue_concentration_csv,
            filename="test.csv",
            materiality_threshold=0,
        )
        anomaly_types = result["risk_summary"]["anomaly_types"]
        assert "revenue_concentration" in anomaly_types
        assert "asset_concentration" in anomaly_types
        assert "liability_concentration" in anomaly_types
        assert "expense_concentration" in anomaly_types

    def test_concentration_anomaly_type_ends_with_concentration(self, revenue_concentration_csv):
        """All concentration entries should have anomaly_type ending in '_concentration'."""
        from audit_engine import StreamingAuditor

        auditor = StreamingAuditor(materiality_threshold=0)
        df = pd.read_csv(io.BytesIO(revenue_concentration_csv))
        auditor.process_chunk(df, len(df))

        risks = auditor.detect_concentration_risk()
        for r in risks:
            assert r["anomaly_type"].endswith("_concentration"), (
                f"Expected anomaly_type ending in '_concentration', got '{r['anomaly_type']}'"
            )


# ═══════════════════════════════════════════════════════════════
# L1: Accrual Narrative Language Guardrail Tests
# ═══════════════════════════════════════════════════════════════

class TestAccrualNarrativeLanguage:
    """Verify accrual narrative uses only factual numeric language."""

    def test_no_appears_in_narrative(self):
        """Narrative must NOT contain 'appears' — evaluative language forbidden."""
        balances = {"Accrued Expenses": {"debit": 0.0, "credit": 1000.0}}
        classified = {"Accrued Expenses": "liability"}
        result = compute_accrual_completeness(
            balances, classified,
            prior_operating_expenses=120000.0,
            threshold_pct=50.0,
        )
        assert "appears" not in result.narrative.lower()

    def test_below_threshold_uses_numeric_comparison(self):
        """Below-threshold narrative should state ratio vs threshold numerically."""
        balances = {"Accrued Wages": {"debit": 0.0, "credit": 1000.0}}
        classified = {"Accrued Wages": "liability"}
        result = compute_accrual_completeness(
            balances, classified,
            prior_operating_expenses=120000.0,  # run-rate = $10,000/mo
            threshold_pct=50.0,
        )
        # 1000/10000 = 10% which is below 50%
        assert result.below_threshold is True
        assert "50%" in result.narrative
        assert "10.0%" in result.narrative
        assert "threshold" in result.narrative.lower()

    def test_above_threshold_uses_numeric_comparison(self):
        """Above-threshold narrative should also state ratio vs threshold."""
        balances = {"Accrued Wages": {"debit": 0.0, "credit": 8000.0}}
        classified = {"Accrued Wages": "liability"}
        result = compute_accrual_completeness(
            balances, classified,
            prior_operating_expenses=120000.0,  # run-rate = $10,000/mo
            threshold_pct=50.0,
        )
        # 8000/10000 = 80% which is above 50%
        assert result.below_threshold is False
        assert "80.0%" in result.narrative
        assert "50%" in result.narrative

    def test_no_warrants_in_narrative(self):
        """Narrative must NOT contain 'warrants' — practitioner judgment language forbidden."""
        balances = {"Accrued Expenses": {"debit": 0.0, "credit": 500.0}}
        classified = {"Accrued Expenses": "liability"}
        result = compute_accrual_completeness(
            balances, classified,
            prior_operating_expenses=120000.0,
            threshold_pct=50.0,
        )
        assert "warrants" not in result.narrative.lower()


# ═══════════════════════════════════════════════════════════════
# L4: ISA Citation Disclaimer Tests
# ═══════════════════════════════════════════════════════════════

class TestISACitationDisclaimers:
    """Verify all memo generators have explicit ISA citations in disclaimers."""

    def test_ap_memo_has_isa_reference(self):
        """AP testing memo config should have explicit ISA reference."""
        from ap_testing_memo_generator import _AP_CONFIG
        assert _AP_CONFIG.isa_reference != "applicable professional standards"
        assert "ISA" in _AP_CONFIG.isa_reference

    def test_je_memo_has_isa_reference(self):
        """JE testing memo config should have explicit ISA reference."""
        from je_testing_memo_generator import _JE_CONFIG
        assert _JE_CONFIG.isa_reference != "applicable professional standards"
        assert "ISA" in _JE_CONFIG.isa_reference or "PCAOB" in _JE_CONFIG.isa_reference

    def test_payroll_memo_has_isa_reference(self):
        """Payroll testing memo config should have explicit ISA reference."""
        from payroll_testing_memo_generator import _PAYROLL_CONFIG
        assert _PAYROLL_CONFIG.isa_reference != "applicable professional standards"
        assert "ISA" in _PAYROLL_CONFIG.isa_reference

    def test_all_template_configs_have_specific_isa(self):
        """No template-based memo config should use the generic default."""
        from ap_testing_memo_generator import _AP_CONFIG
        from ar_aging_memo_generator import _AR_CONFIG
        from fixed_asset_testing_memo_generator import _FA_CONFIG
        from inventory_testing_memo_generator import _INV_CONFIG
        from je_testing_memo_generator import _JE_CONFIG
        from payroll_testing_memo_generator import _PAYROLL_CONFIG
        from revenue_testing_memo_generator import _REVENUE_CONFIG

        configs = [
            ("AP", _AP_CONFIG),
            ("JE", _JE_CONFIG),
            ("Payroll", _PAYROLL_CONFIG),
            ("AR Aging", _AR_CONFIG),
            ("Fixed Asset", _FA_CONFIG),
            ("Inventory", _INV_CONFIG),
            ("Revenue", _REVENUE_CONFIG),
        ]
        for name, config in configs:
            assert config.isa_reference != "applicable professional standards", (
                f"{name} memo config is missing explicit ISA reference"
            )
