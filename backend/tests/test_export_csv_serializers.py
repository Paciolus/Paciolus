"""
Tests for export CSV serializers (backend/export/serializers/csv.py).

Previously 0% covered — Sprint 676 fills the gap. Each serializer gets
a happy-path test plus targeted edge-case coverage (empty inputs,
prior-period vs no-prior, optional narrative, CSV injection sanitization).
"""

import csv as stdlib_csv
from io import StringIO

import pytest

from export.serializers.csv import (
    serialize_accrual_completeness_csv,
    serialize_anomalies_csv,
    serialize_expense_category_csv,
    serialize_population_profile_csv,
    serialize_preflight_issues_csv,
    serialize_trial_balance_csv,
)
from shared.export_schemas import (
    AccrualCompletenessCSVInput,
    ExpenseCategoryCSVInput,
    PopulationProfileCSVInput,
    PreFlightCSVInput,
)
from shared.schemas import AuditResultInput


def _parse(csv_bytes: bytes) -> list[list[str]]:
    """Decode UTF-8-sig CSV bytes and return a list of rows."""
    text = csv_bytes.decode("utf-8-sig")
    return list(stdlib_csv.reader(StringIO(text)))


def _make_audit_result(**overrides) -> AuditResultInput:
    defaults = {
        "status": "ok",
        "balanced": True,
        "total_debits": 1000.0,
        "total_credits": 1000.0,
        "difference": 0.0,
        "row_count": 2,
        "message": "ok",
        "abnormal_balances": [],
        "has_risk_alerts": False,
        "materiality_threshold": 100.0,
        "material_count": 0,
        "immaterial_count": 0,
    }
    defaults.update(overrides)
    return AuditResultInput(**defaults)


# ---------------------------------------------------------------------------
# serialize_trial_balance_csv
# ---------------------------------------------------------------------------


class TestSerializeTrialBalanceCsv:
    def test_header_and_totals_footer(self):
        result = _make_audit_result()
        rows = _parse(serialize_trial_balance_csv(result))
        assert rows[0] == [
            "Reference",
            "Account",
            "Debit",
            "Credit",
            "Net Balance",
            "Category",
            "Classification Confidence",
        ]
        # Empty abnormal_balances → header + blank + totals
        assert rows[-1][0] == "TOTALS"
        assert rows[-1][2] == "1000.00"
        assert rows[-1][3] == "1000.00"

    def test_writes_row_per_unique_account(self):
        result = _make_audit_result(
            abnormal_balances=[
                {"account": "Cash", "debit": 500.0, "credit": 0, "amount": 500.0, "type": "asset"},
                {"account": "Cash", "debit": 100.0, "credit": 0, "amount": 100.0, "type": "asset"},
                {"account": "AR", "debit": 300.0, "credit": 0, "amount": 300.0, "type": "asset"},
            ],
        )
        rows = _parse(serialize_trial_balance_csv(result))
        # Ref assigned sequentially, dedup'd accounts
        account_rows = [r for r in rows if r and r[0].startswith("TB-")]
        assert len(account_rows) == 2
        assert account_rows[0][1] == "Cash"
        assert account_rows[1][1] == "AR"

    def test_uses_classification_summary_category_when_available(self):
        result = _make_audit_result(
            abnormal_balances=[
                {"account": "Rent Expense", "debit": 0, "credit": 200.0, "amount": -200.0, "type": "misc"},
            ],
            classification_summary={
                "Operating Expenses": [{"account": "Rent Expense", "confidence": 0.92}],
            },
        )
        rows = _parse(serialize_trial_balance_csv(result))
        expense_row = [r for r in rows if r and r[0].startswith("TB-")][0]
        assert expense_row[5] == "Operating Expenses"
        assert expense_row[6] == "92%"

    def test_falls_back_to_anomaly_type_when_no_classification(self):
        result = _make_audit_result(
            abnormal_balances=[
                {"account": "Unknown Account", "debit": 50.0, "credit": 0, "amount": 50.0, "type": "fallback_type"},
            ],
        )
        rows = _parse(serialize_trial_balance_csv(result))
        row = [r for r in rows if r and r[0].startswith("TB-")][0]
        assert row[5] == "fallback_type"

    def test_non_dict_anomalies_are_skipped(self):
        result = _make_audit_result(abnormal_balances=["not a dict", 42, None])
        rows = _parse(serialize_trial_balance_csv(result))
        # No account rows emitted, still yields totals
        account_rows = [r for r in rows if r and r[0].startswith("TB-")]
        assert account_rows == []
        assert rows[-1][0] == "TOTALS"

    def test_csv_injection_sanitization_on_account_name(self):
        result = _make_audit_result(
            abnormal_balances=[
                {"account": "=1+1", "debit": 10, "credit": 0, "amount": 10, "type": "x"},
            ],
        )
        rows = _parse(serialize_trial_balance_csv(result))
        account_row = [r for r in rows if r and r[0].startswith("TB-")][0]
        # sanitize_csv_value prefixes a dangerous leading char with a tick
        assert not account_row[1].startswith("=")


# ---------------------------------------------------------------------------
# serialize_anomalies_csv
# ---------------------------------------------------------------------------


class TestSerializeAnomaliesCsv:
    def test_splits_refs_by_materiality(self):
        result = _make_audit_result(
            abnormal_balances=[
                {"account": "A1", "materiality": "material", "amount": 500.0, "severity": "high"},
                {"account": "A2", "materiality": "immaterial", "amount": 10.0, "severity": "low"},
                {"account": "A3", "materiality": "material", "amount": 300.0, "severity": "medium"},
            ],
            material_count=2,
            immaterial_count=1,
        )
        rows = _parse(serialize_anomalies_csv(result))
        refs = [r[0] for r in rows if r and r[0].startswith("TB-")]
        assert refs == ["TB-M001", "TB-I001", "TB-M002"]

    def test_summary_footer_has_counts(self):
        result = _make_audit_result(
            abnormal_balances=[{"account": "X", "materiality": "material", "amount": 1.0}],
            material_count=1,
            immaterial_count=0,
        )
        rows = _parse(serialize_anomalies_csv(result))
        summary_rows = [r for r in rows if r and r[0] in ("Material Count", "Immaterial Count", "Total Anomalies")]
        assert ["Material Count", "1", "", "", "", "", "", "", ""] in summary_rows
        assert ["Total Anomalies", "1", "", "", "", "", "", "", ""] in summary_rows

    def test_risk_breakdown_appended_when_provided(self):
        result = _make_audit_result(
            abnormal_balances=[{"account": "X", "materiality": "material", "amount": 1.0}],
            risk_summary={"fraud_risk": 3, "control_risk": 0, "inherent_risk": 1},
        )
        rows = _parse(serialize_anomalies_csv(result))
        assert any(r and r[0] == "RISK BREAKDOWN" for r in rows)
        # Zero-count entries should be omitted
        risk_rows = [r[0] for r in rows if r and r[0] in ("Fraud Risk", "Control Risk", "Inherent Risk")]
        assert "Fraud Risk" in risk_rows
        assert "Control Risk" not in risk_rows

    def test_no_risk_breakdown_when_risk_summary_absent(self):
        result = _make_audit_result(abnormal_balances=[])
        rows = _parse(serialize_anomalies_csv(result))
        assert not any(r and r[0] == "RISK BREAKDOWN" for r in rows)

    def test_confidence_formatted_as_percent(self):
        result = _make_audit_result(
            abnormal_balances=[
                {"account": "A", "materiality": "immaterial", "amount": 1.0, "confidence": 0.87},
            ],
        )
        rows = _parse(serialize_anomalies_csv(result))
        data_row = [r for r in rows if r and r[0].startswith("TB-")][0]
        assert data_row[-1] == "87%"


# ---------------------------------------------------------------------------
# serialize_preflight_issues_csv
# ---------------------------------------------------------------------------


class TestSerializePreflightIssuesCsv:
    def test_header_only_when_no_issues(self):
        rows = _parse(serialize_preflight_issues_csv(PreFlightCSVInput(issues=[])))
        assert len(rows) == 1
        assert rows[0] == ["Category", "Severity", "Message", "Affected Count", "Remediation"]

    def test_issue_row_formatting(self):
        pf = PreFlightCSVInput(
            issues=[
                {
                    "category": "missing_data",
                    "severity": "warn",
                    "message": "Empty column",
                    "affected_count": 4,
                    "remediation": "Fill the column",
                },
            ]
        )
        rows = _parse(serialize_preflight_issues_csv(pf))
        assert rows[1] == ["Missing Data", "WARN", "Empty column", "4", "Fill the column"]

    def test_non_dict_issues_ignored(self):
        pf = PreFlightCSVInput(issues=["str", None, 3])
        rows = _parse(serialize_preflight_issues_csv(pf))
        assert len(rows) == 1  # only the header


# ---------------------------------------------------------------------------
# serialize_population_profile_csv
# ---------------------------------------------------------------------------


class TestSerializePopulationProfileCsv:
    def test_summary_section_emits_all_stats(self):
        pp = PopulationProfileCSVInput(
            account_count=5,
            total_abs_balance=500.0,
            mean_abs_balance=100.0,
            median_abs_balance=100.0,
            std_dev_abs_balance=10.0,
            min_abs_balance=50.0,
            max_abs_balance=150.0,
            p25=75.0,
            p75=125.0,
            gini_coefficient=0.3333,
            gini_interpretation="Moderate",
        )
        rows = _parse(serialize_population_profile_csv(pp))
        flat = [r[0] for r in rows if r]
        for expected in (
            "TB POPULATION PROFILE",
            "Statistic",
            "Account Count",
            "Gini Coefficient",
            "Gini Interpretation",
            "MAGNITUDE DISTRIBUTION",
            "TOP ACCOUNTS BY ABSOLUTE BALANCE",
        ):
            assert expected in flat

    def test_buckets_and_top_accounts_render(self):
        pp = PopulationProfileCSVInput(
            buckets=[{"label": "Under $100", "count": 3, "percent_count": 30.0, "sum_abs": 150.0}],
            top_accounts=[
                {
                    "rank": 1,
                    "account": "Cash",
                    "category": "Assets",
                    "net_balance": 500.0,
                    "abs_balance": 500.0,
                    "percent_of_total": 50.0,
                },
            ],
        )
        rows = _parse(serialize_population_profile_csv(pp))
        assert any(r and r[0] == "Under $100" and r[3] == "150.00" for r in rows)
        assert any(r and r[0] == "1" and r[1] == "Cash" and r[2] == "Assets" for r in rows)

    def test_non_dict_buckets_and_accounts_skipped(self):
        pp = PopulationProfileCSVInput(
            buckets=["not a dict"],
            top_accounts=[42],
        )
        # Should not raise
        rows = _parse(serialize_population_profile_csv(pp))
        # Just the summary + headers, no data rows
        assert any(r and r[0] == "MAGNITUDE DISTRIBUTION" for r in rows)


# ---------------------------------------------------------------------------
# serialize_expense_category_csv
# ---------------------------------------------------------------------------


class TestSerializeExpenseCategoryCsv:
    def test_layout_without_prior_period(self):
        ec = ExpenseCategoryCSVInput(
            categories=[{"label": "Rent", "amount": 1200.0, "pct_of_revenue": 12.5}],
            total_expenses=1200.0,
            total_revenue=9600.0,
            revenue_available=True,
            prior_available=False,
            materiality_threshold=100.0,
            category_count=1,
        )
        rows = _parse(serialize_expense_category_csv(ec))
        header_idx = next(i for i, r in enumerate(rows) if r == ["Category", "Amount", "% of Revenue"])
        data = rows[header_idx + 1]
        assert data == ["Rent", "1200.00", "12.50%"]

    def test_layout_with_prior_period(self):
        ec = ExpenseCategoryCSVInput(
            categories=[
                {
                    "label": "Rent",
                    "amount": 1200.0,
                    "pct_of_revenue": 12.5,
                    "prior_amount": 1000.0,
                    "dollar_change": 200.0,
                    "exceeds_threshold": True,
                },
            ],
            prior_available=True,
        )
        rows = _parse(serialize_expense_category_csv(ec))
        # Check that prior period header is used
        assert ["Category", "Amount", "% of Revenue", "Prior Amount", "Dollar Change", "Exceeds Materiality"] in rows
        data_row = next(r for r in rows if r and r[0] == "Rent")
        assert data_row[3] == "1000.00"
        assert data_row[4] == "200.00"
        assert data_row[5] == "Yes"

    def test_na_when_pct_of_revenue_missing(self):
        ec = ExpenseCategoryCSVInput(
            categories=[{"label": "Unknown", "amount": 100.0}],  # no pct_of_revenue
        )
        rows = _parse(serialize_expense_category_csv(ec))
        data_row = next(r for r in rows if r and r[0] == "Unknown")
        assert data_row[2] == "N/A"


# ---------------------------------------------------------------------------
# serialize_accrual_completeness_csv
# ---------------------------------------------------------------------------


class TestSerializeAccrualCompletenessCsv:
    def test_minimal_payload_renders(self):
        ac = AccrualCompletenessCSVInput(
            accrual_account_count=2,
            total_accrued_balance=5000.0,
            threshold_pct=50.0,
            below_threshold=True,
        )
        rows = _parse(serialize_accrual_completeness_csv(ac))
        assert any(r and r[0] == "ACCRUAL COMPLETENESS ESTIMATOR" for r in rows)
        below = next(r for r in rows if r and r[0] == "Below Threshold")
        assert below[1] == "Yes"

    def test_optional_run_rate_metrics_conditional(self):
        ac_with = AccrualCompletenessCSVInput(
            monthly_run_rate=1000.0,
            accrual_to_run_rate_pct=42.0,
            prior_available=True,
            prior_operating_expenses=12000.0,
        )
        rows_with = _parse(serialize_accrual_completeness_csv(ac_with))
        labels_with = [r[0] for r in rows_with if r]
        assert "Monthly Run-Rate" in labels_with
        assert "Accrual-to-Run-Rate %" in labels_with
        assert "Prior Operating Expenses" in labels_with

        ac_without = AccrualCompletenessCSVInput()
        rows_without = _parse(serialize_accrual_completeness_csv(ac_without))
        labels_without = [r[0] for r in rows_without if r]
        assert "Monthly Run-Rate" not in labels_without
        assert "Accrual-to-Run-Rate %" not in labels_without
        assert "Prior Operating Expenses" not in labels_without

    def test_accrual_accounts_section(self):
        ac = AccrualCompletenessCSVInput(
            accrual_accounts=[
                {"account_name": "Accrued Wages", "balance": 3500.0, "matched_keyword": "accrued wages"},
            ],
        )
        rows = _parse(serialize_accrual_completeness_csv(ac))
        account_row = next(r for r in rows if r and r[0] == "Accrued Wages")
        assert account_row[1] == "3500.00"
        assert account_row[2] == "accrued wages"

    def test_narrative_appended_when_present(self):
        ac = AccrualCompletenessCSVInput(narrative="Two months of accruals posted.")
        rows = _parse(serialize_accrual_completeness_csv(ac))
        assert any(r and r[0] == "NARRATIVE" for r in rows)
        narrative_row = next(r for i, r in enumerate(rows) if i > 0 and rows[i - 1] and rows[i - 1][0] == "NARRATIVE")
        assert "Two months" in narrative_row[0]

    def test_no_narrative_section_when_blank(self):
        ac = AccrualCompletenessCSVInput(narrative="")
        rows = _parse(serialize_accrual_completeness_csv(ac))
        assert not any(r and r[0] == "NARRATIVE" for r in rows)


# ---------------------------------------------------------------------------
# Encoding contract
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "serializer,payload",
    [
        (serialize_trial_balance_csv, _make_audit_result()),
        (serialize_anomalies_csv, _make_audit_result()),
        (serialize_preflight_issues_csv, PreFlightCSVInput(issues=[])),
        (serialize_population_profile_csv, PopulationProfileCSVInput()),
        (serialize_expense_category_csv, ExpenseCategoryCSVInput()),
        (serialize_accrual_completeness_csv, AccrualCompletenessCSVInput()),
    ],
)
def test_all_serializers_emit_utf8_sig_bom(serializer, payload):
    """Every CSV serializer must emit UTF-8 BOM for Excel compatibility."""
    out = serializer(payload)
    assert isinstance(out, bytes)
    assert out.startswith(b"\xef\xbb\xbf")  # UTF-8-sig BOM
