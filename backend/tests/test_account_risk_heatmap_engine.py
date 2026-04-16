"""Tests for account_risk_heatmap_engine (Sprint 627)."""

from __future__ import annotations

from decimal import Decimal

from account_risk_heatmap_engine import (
    SOURCE_AUDIT_ANOMALY,
    SOURCE_CLASSIFICATION,
    SOURCE_CUTOFF,
    RiskSignal,
    build_signals_from_accrual_findings,
    build_signals_from_audit_anomalies,
    build_signals_from_classification_issues,
    build_signals_from_composite_risk,
    build_signals_from_cutoff_flags,
    compute_account_heatmap,
    heatmap_to_csv,
)

# =============================================================================
# Aggregation
# =============================================================================


class TestAggregation:
    def test_signals_aggregate_per_account(self):
        signals = [
            RiskSignal(
                account_number="1010",
                account_name="Cash",
                source=SOURCE_AUDIT_ANOMALY,
                severity="high",
                issue="Round-number anomaly",
                materiality=Decimal("50000"),
            ),
            RiskSignal(
                account_number="1010",
                account_name="Cash",
                source=SOURCE_CUTOFF,
                severity="medium",
                issue="Cutoff window risk",
                materiality=Decimal("10000"),
            ),
            RiskSignal(
                account_number="2010",
                account_name="AP",
                source=SOURCE_CLASSIFICATION,
                severity="low",
                issue="Inconsistent naming",
                materiality=Decimal("0"),
            ),
        ]
        result = compute_account_heatmap(signals)
        assert result.total_accounts_with_signals == 2
        assert result.total_signals == 3
        # Cash should rank above AP — two signals, higher severity, higher materiality
        cash_row = next(r for r in result.rows if r.account_number == "1010")
        ap_row = next(r for r in result.rows if r.account_number == "2010")
        assert cash_row.signal_count == 2
        assert cash_row.weighted_score > ap_row.weighted_score
        assert SOURCE_AUDIT_ANOMALY in cash_row.sources
        assert SOURCE_CUTOFF in cash_row.sources
        assert cash_row.severities == {"high": 1, "medium": 1}

    def test_priority_tier_top_10_pct_high(self):
        signals: list[RiskSignal] = []
        # 20 accounts with descending scores
        for i in range(20):
            signals.append(
                RiskSignal(
                    account_number=f"{1000 + i}",
                    account_name=f"Account {i}",
                    source=SOURCE_AUDIT_ANOMALY,
                    severity="high" if i < 5 else "low",
                    issue="x",
                    materiality=Decimal(str(10 ** (5 - (i // 5)))),
                )
            )
        result = compute_account_heatmap(signals)
        # 20 accounts → top 10% = 2, next 20% = 6 (10–30 percentile)
        assert result.high_priority_count == 2
        assert result.moderate_priority_count == 4
        assert result.low_priority_count == 14
        # First two ranks must be the highest-score (highest severity + materiality)
        assert result.rows[0].priority_tier == "high"
        assert result.rows[1].priority_tier == "high"

    def test_empty_signals_produces_empty_result(self):
        result = compute_account_heatmap([])
        assert result.total_accounts_with_signals == 0
        assert result.total_signals == 0
        assert result.high_priority_count == 0
        assert result.rows == []
        assert result.sources_active == []

    def test_active_sources_collected(self):
        signals = [
            RiskSignal("1", "A", SOURCE_AUDIT_ANOMALY, "high", "x"),
            RiskSignal("2", "B", SOURCE_CUTOFF, "low", "y"),
            RiskSignal("3", "C", SOURCE_CUTOFF, "low", "z"),
        ]
        result = compute_account_heatmap(signals)
        assert result.sources_active == sorted([SOURCE_AUDIT_ANOMALY, SOURCE_CUTOFF])


# =============================================================================
# Severity weighting
# =============================================================================


class TestSeverityWeighting:
    def test_high_outweighs_low_at_same_materiality(self):
        high_sig = RiskSignal("1", "A", SOURCE_AUDIT_ANOMALY, "high", "x", materiality=Decimal("1000"))
        low_sig = RiskSignal("2", "B", SOURCE_AUDIT_ANOMALY, "low", "y", materiality=Decimal("1000"))
        assert high_sig.weighted_score() > low_sig.weighted_score()

    def test_materiality_amplifies_score(self):
        small = RiskSignal("1", "A", SOURCE_AUDIT_ANOMALY, "medium", "x", materiality=Decimal("100"))
        big = RiskSignal("1", "A", SOURCE_AUDIT_ANOMALY, "medium", "x", materiality=Decimal("1000000"))
        assert big.weighted_score() > small.weighted_score()


# =============================================================================
# Adapters
# =============================================================================


class TestAuditAnomalyAdapter:
    def test_unified_anomaly_dict_translates(self):
        anomalies = [
            {
                "account": "Cash",
                "account_number": "1010",
                "type": "round_number",
                "issue": "Round-number $50,000 deposit",
                "amount": 50000,
                "materiality": 50000,
                "confidence": 0.85,
                "anomaly_type": "round_number",
                "severity": "medium",
            }
        ]
        signals = build_signals_from_audit_anomalies(anomalies)
        assert len(signals) == 1
        s = signals[0]
        assert s.account_number == "1010"
        assert s.account_name == "Cash"
        assert s.severity == "medium"
        assert s.materiality == Decimal("50000")
        assert s.confidence == 0.85
        assert s.source == SOURCE_AUDIT_ANOMALY


class TestClassificationAdapter:
    def test_classification_dict_translates(self):
        issues = [
            {
                "account_number": "5010",
                "account_name": "Travel",
                "issue_type": "unclassified",
                "description": "No lead sheet mapping",
                "severity": "medium",
                "confidence": 0.8,
            }
        ]
        signals = build_signals_from_classification_issues(issues)
        assert len(signals) == 1
        assert signals[0].source == SOURCE_CLASSIFICATION
        assert signals[0].severity == "medium"
        assert signals[0].issue == "No lead sheet mapping"


class TestCutoffAdapter:
    def test_cutoff_flag_translates(self):
        class FakeFlag:
            account_number = "4010"
            account_name = "Revenue"
            issue = "Period-end spike"
            severity = "high"
            amount = Decimal("75000")
            confidence = 0.9

        signals = build_signals_from_cutoff_flags([FakeFlag()])
        assert len(signals) == 1
        s = signals[0]
        assert s.source == SOURCE_CUTOFF
        assert s.severity == "high"
        assert s.materiality == Decimal("75000")


class TestAccrualAdapter:
    def test_accrual_finding_translates(self):
        findings = [
            {
                "account_number": "2110",
                "account_name": "Accrued Liabilities",
                "title": "Reasonableness deviation",
                "severity": "high",
                "amount": 25000,
            }
        ]
        signals = build_signals_from_accrual_findings(findings)
        assert len(signals) == 1
        assert signals[0].source == "accrual_completeness"
        assert signals[0].materiality == Decimal("25000")


class TestCompositeRiskAdapter:
    def test_composite_profile_only_emits_moderate_or_higher(self):
        profile = {
            "account_assessments": [
                {"account_name": "Cash", "assertion": "existence", "combined_risk": "low"},
                {"account_name": "Revenue", "assertion": "occurrence", "combined_risk": "high"},
                {"account_name": "AP", "assertion": "completeness", "combined_risk": "moderate"},
            ]
        }
        signals = build_signals_from_composite_risk(profile)
        # Low-risk accounts excluded
        assert len(signals) == 2
        assert {s.account_name for s in signals} == {"Revenue", "AP"}

    def test_none_profile_returns_empty(self):
        assert build_signals_from_composite_risk(None) == []


# =============================================================================
# CSV export
# =============================================================================


class TestCsvExport:
    def test_csv_contains_header_and_rows(self):
        signals = [
            RiskSignal("1010", "Cash", SOURCE_AUDIT_ANOMALY, "high", "x", materiality=Decimal("1000")),
            RiskSignal("2010", "AP", SOURCE_CLASSIFICATION, "low", "y"),
        ]
        result = compute_account_heatmap(signals)
        csv_text = heatmap_to_csv(result)
        lines = csv_text.strip().split("\n")
        assert len(lines) == 3  # header + 2 data rows
        assert "Rank" in lines[0]
        assert "Priority" in lines[0]
        # First data row is the highest-score account (Cash)
        assert "Cash" in lines[1]
