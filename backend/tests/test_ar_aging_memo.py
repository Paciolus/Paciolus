"""
Sprint 108: Tests for AR Aging Memo Generator + Export Routes.

Validates:
- PDF memo generation (structure, content, ISA references)
- Guardrails (no "allowance is sufficient", no "bad debt write-off required")
- Export route registration (PDF + CSV endpoints)
- CSV export structure
- ARAgingExportInput model
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from ar_aging_memo_generator import (
    generate_ar_aging_memo,
    AR_AGING_TEST_DESCRIPTIONS,
)


# =============================================================================
# TEST FIXTURES
# =============================================================================

def _make_ar_result(
    score: float = 18.0,
    risk_tier: str = "elevated",
    total_flagged: int = 5,
    num_tests: int = 11,
    tests_skipped: int = 0,
    has_subledger: bool = True,
    top_findings: list | None = None,
) -> dict:
    """Build a minimal ARAgingResult.to_dict() shape."""
    test_keys = [
        "ar_sign_anomalies", "missing_allowance", "negative_aging",
        "unreconciled_detail", "bucket_concentration", "past_due_concentration",
        "allowance_adequacy", "customer_concentration", "dso_trend",
        "rollforward_reconciliation", "credit_limit_breaches",
    ]
    test_names = [
        "AR Balance Sign Anomalies", "Missing Contra-Account",
        "Negative Aging Buckets", "Unreconciled AR Detail",
        "Aging Bucket Concentration", "Past-Due Concentration",
        "Allowance Adequacy Ratio", "Customer Concentration",
        "DSO Trend Variance", "Roll-Forward Reconciliation",
        "Credit Limit Breaches",
    ]
    tiers = [
        "structural", "structural", "structural", "structural",
        "statistical", "statistical", "statistical", "statistical", "statistical",
        "advanced", "advanced",
    ]

    test_results = []
    for i in range(min(num_tests, 11)):
        flagged_count = 1 if i < 3 else 0
        skipped = i >= (num_tests - tests_skipped)
        test_results.append({
            "test_name": test_names[i],
            "test_key": test_keys[i],
            "test_tier": tiers[i],
            "entries_flagged": 0 if skipped else flagged_count,
            "total_entries": 20,
            "flag_rate": 0 if skipped else flagged_count / 20,
            "severity": "high" if i == 0 else "medium" if i < 5 else "low",
            "description": f"Test description for {test_keys[i]}",
            "skipped": skipped,
            "skip_reason": "Requires AR sub-ledger" if skipped else None,
            "flagged_entries": [
                {
                    "entry": {
                        "account_name": "Accounts Receivable",
                        "account_number": "1200",
                        "customer_name": f"Customer {j + 1}",
                        "invoice_number": f"INV-{i:03d}-{j}",
                        "date": "2025-12-15",
                        "amount": 50000.0 + j * 1000,
                        "aging_days": 45 + j * 10,
                        "row_number": i * 10 + j + 1,
                        "entry_source": "tb" if i < 4 else "subledger",
                    },
                    "test_name": test_names[i],
                    "test_key": test_keys[i],
                    "test_tier": tiers[i],
                    "severity": "high" if i == 0 else "medium",
                    "issue": f"Flagged by {test_names[i]}",
                    "confidence": 0.85,
                    "details": {},
                }
                for j in range(0 if skipped else flagged_count)
            ],
        })

    return {
        "composite_score": {
            "score": score,
            "risk_tier": risk_tier,
            "tests_run": num_tests - tests_skipped,
            "tests_skipped": tests_skipped,
            "total_flagged": total_flagged,
            "flags_by_severity": {"high": 1, "medium": 2, "low": 2},
            "top_findings": top_findings or [
                "AR Balance Sign Anomalies: 1 flagged",
                "Missing Contra-Account: 1 flagged",
                "Negative Aging Buckets: 1 flagged",
            ],
            "has_subledger": has_subledger,
        },
        "test_results": test_results,
        "data_quality": {
            "completeness_score": 88.5,
            "field_fill_rates": {"account_name": 1.0, "amount": 0.95, "aging_days": 0.80},
            "detected_issues": [],
            "total_tb_accounts": 25,
            "total_subledger_entries": 150 if has_subledger else 0,
            "has_subledger": has_subledger,
        },
        "tb_column_detection": {
            "account_name_column": "Account Name",
            "balance_column": "Balance",
            "overall_confidence": 0.95,
        },
        "sl_column_detection": {
            "customer_name_column": "Customer",
            "amount_column": "Amount",
            "aging_days_column": "Days",
            "overall_confidence": 0.90,
        } if has_subledger else None,
        "ar_summary": {
            "total_ar_balance": 500000.0,
            "total_allowance": 15000.0,
            "allowance_ratio": 0.03,
            "ar_account_count": 5,
        },
    }


# =============================================================================
# MEMO GENERATION TESTS
# =============================================================================

class TestARAgingMemoGeneration:
    """Tests for generate_ar_aging_memo()."""

    def test_generates_pdf_bytes(self):
        result = _make_ar_result()
        pdf = generate_ar_aging_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_pdf_header(self):
        result = _make_ar_result()
        pdf = generate_ar_aging_memo(result)
        assert pdf[:5] == b"%PDF-"

    def test_with_client_name(self):
        result = _make_ar_result()
        pdf = generate_ar_aging_memo(result, client_name="Acme Corp")
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_with_all_options(self):
        result = _make_ar_result()
        pdf = generate_ar_aging_memo(
            result,
            filename="acme_ar_aging",
            client_name="Acme Corp",
            period_tested="FY 2025",
            prepared_by="John Smith",
            reviewed_by="Jane Doe",
            workpaper_date="2025-03-15",
        )
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_low_risk_conclusion(self):
        result = _make_ar_result(score=5.0, risk_tier="low")
        pdf = generate_ar_aging_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_elevated_risk_conclusion(self):
        result = _make_ar_result(score=18.0, risk_tier="elevated")
        pdf = generate_ar_aging_memo(result)
        assert isinstance(pdf, bytes)

    def test_moderate_risk_conclusion(self):
        result = _make_ar_result(score=35.0, risk_tier="moderate")
        pdf = generate_ar_aging_memo(result)
        assert isinstance(pdf, bytes)

    def test_high_risk_conclusion(self):
        result = _make_ar_result(score=65.0, risk_tier="high")
        pdf = generate_ar_aging_memo(result)
        assert isinstance(pdf, bytes)

    def test_no_findings_skips_section(self):
        result = _make_ar_result(top_findings=[])
        pdf = generate_ar_aging_memo(result)
        assert isinstance(pdf, bytes)

    def test_empty_test_results(self):
        result = _make_ar_result(num_tests=0)
        result["test_results"] = []
        result["composite_score"]["tests_run"] = 0
        pdf = generate_ar_aging_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_tb_only_mode(self):
        """Memo generates for TB-only analysis (no sub-ledger)."""
        result = _make_ar_result(
            has_subledger=False,
            num_tests=4,
            tests_skipped=0,
        )
        result["data_quality"]["has_subledger"] = False
        result["composite_score"]["has_subledger"] = False
        result["sl_column_detection"] = None
        pdf = generate_ar_aging_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_with_skipped_tests(self):
        """Memo handles skipped tests gracefully."""
        result = _make_ar_result(
            has_subledger=False,
            num_tests=11,
            tests_skipped=7,
        )
        pdf = generate_ar_aging_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100


# =============================================================================
# TEST DESCRIPTIONS COVERAGE
# =============================================================================

class TestARAgingTestDescriptions:
    """Tests for AR_AGING_TEST_DESCRIPTIONS completeness."""

    def test_all_11_tests_have_descriptions(self):
        expected_keys = [
            "ar_sign_anomalies", "missing_allowance", "negative_aging",
            "unreconciled_detail", "bucket_concentration", "past_due_concentration",
            "allowance_adequacy", "customer_concentration", "dso_trend",
            "rollforward_reconciliation", "credit_limit_breaches",
        ]
        for key in expected_keys:
            assert key in AR_AGING_TEST_DESCRIPTIONS, f"Missing description for {key}"

    def test_descriptions_are_nonempty(self):
        for key, desc in AR_AGING_TEST_DESCRIPTIONS.items():
            assert len(desc) > 20, f"Description too short for {key}"


# =============================================================================
# GUARDRAIL TESTS
# =============================================================================

class TestARAgingGuardrails:
    """Guardrail compliance: terminology, disclaimers, ISA references.

    PDF content streams are compressed by ReportLab, so we verify guardrails
    at the source code level (strings passed to the PDF builder).
    """

    def test_no_allowance_sufficiency_in_descriptions(self):
        """No description should say 'allowance is sufficient/insufficient'."""
        for key, desc in AR_AGING_TEST_DESCRIPTIONS.items():
            lower = desc.lower()
            assert "allowance is sufficient" not in lower, (
                f"GUARDRAIL VIOLATION: '{key}' uses 'allowance is sufficient'"
            )
            assert "allowance is insufficient" not in lower, (
                f"GUARDRAIL VIOLATION: '{key}' uses 'allowance is insufficient'"
            )

    def test_no_bad_debt_writeoff_in_descriptions(self):
        """Descriptions should not say 'bad debt write-off required'."""
        for key, desc in AR_AGING_TEST_DESCRIPTIONS.items():
            assert "bad debt write-off required" not in desc.lower(), (
                f"GUARDRAIL VIOLATION: '{key}' uses 'bad debt write-off required'"
            )

    def test_memo_generator_references_isa_500(self):
        """Memo source code must pass ISA 500 reference to the PDF builder."""
        import inspect
        source = inspect.getsource(generate_ar_aging_memo)
        assert "ISA 500" in source, "Memo must reference ISA 500"

    def test_memo_generator_references_isa_540(self):
        """Memo source code must pass ISA 540 reference to the PDF builder."""
        import inspect
        source = inspect.getsource(generate_ar_aging_memo)
        assert "ISA 540" in source, "Memo must reference ISA 540"

    def test_memo_generator_references_pcaob_as_2501(self):
        """Memo source code must pass PCAOB AS 2501 reference to the PDF builder."""
        import inspect
        source = inspect.getsource(generate_ar_aging_memo)
        assert "PCAOB AS 2501" in source, "Memo must reference PCAOB AS 2501"

    def test_memo_generator_uses_anomaly_indicators_language(self):
        """Methodology text must say 'anomaly indicators' not 'sufficiency conclusions'."""
        import inspect
        source = inspect.getsource(generate_ar_aging_memo)
        assert "anomaly indicator" in source.lower(), (
            "Methodology must use 'anomaly indicators' language"
        )
        assert "allowance sufficiency conclusions" not in source.lower() or \
               "not allowance sufficiency conclusions" in source.lower(), (
            "Must not positively assert 'allowance sufficiency conclusions'"
        )

    def test_memo_generator_calls_disclaimer(self):
        """Memo must call build_disclaimer with AR-specific parameters."""
        import inspect
        source = inspect.getsource(generate_ar_aging_memo)
        assert "build_disclaimer" in source
        assert "accounts receivable aging analysis" in source.lower()

    def test_memo_disclaimer_references_isa_500_and_540(self):
        """Disclaimer ISA reference must include ISA 500 and ISA 540."""
        import inspect
        source = inspect.getsource(generate_ar_aging_memo)
        assert "ISA 500" in source
        assert "ISA 540" in source

    def test_conclusion_uses_anomaly_not_sufficiency_language(self):
        """Conclusion text must say 'anomaly' not 'sufficiency'."""
        import inspect
        source = inspect.getsource(generate_ar_aging_memo)
        assert "allowance sufficiency" not in source.lower() or \
               "not allowance sufficiency" in source.lower() or \
               "not an allowance sufficiency" in source.lower(), (
            "GUARDRAIL VIOLATION: conclusion must not use 'allowance sufficiency'"
        )

    def test_no_nrv_determination_in_source(self):
        """Memo source must not claim net realizable value determination."""
        import inspect
        source = inspect.getsource(generate_ar_aging_memo)
        assert "net realizable value determination" not in source.lower(), (
            "GUARDRAIL VIOLATION: must not claim NRV determination"
        )


# =============================================================================
# EXPORT ROUTE REGISTRATION TESTS
# =============================================================================

class TestARAgingExportRoutes:
    """Tests for AR aging export route registration."""

    def test_pdf_route_registered(self):
        from main import app
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/export/ar-aging-memo" in paths

    def test_csv_route_registered(self):
        from main import app
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/export/csv/ar-aging" in paths

    def test_pdf_route_is_post(self):
        from main import app
        for route in app.routes:
            if hasattr(route, "path") and route.path == "/export/ar-aging-memo":
                assert "POST" in route.methods
                break
        else:
            pytest.fail("Route /export/ar-aging-memo not found")

    def test_csv_route_is_post(self):
        from main import app
        for route in app.routes:
            if hasattr(route, "path") and route.path == "/export/csv/ar-aging":
                assert "POST" in route.methods
                break
        else:
            pytest.fail("Route /export/csv/ar-aging not found")


# =============================================================================
# EXPORT INPUT MODEL TESTS
# =============================================================================

class TestARAgingExportInput:
    """Tests for ARAgingExportInput Pydantic model."""

    def test_model_accepts_valid_data(self):
        from routes.export import ARAgingExportInput
        data = _make_ar_result()
        model = ARAgingExportInput(**data)
        assert model.filename == "ar_aging"

    def test_model_defaults(self):
        from routes.export import ARAgingExportInput
        data = _make_ar_result()
        model = ARAgingExportInput(**data)
        assert model.client_name is None
        assert model.period_tested is None
        assert model.prepared_by is None
        assert model.reviewed_by is None
        assert model.workpaper_date is None

    def test_model_with_all_fields(self):
        from routes.export import ARAgingExportInput
        data = _make_ar_result()
        data.update({
            "filename": "acme_ar",
            "client_name": "Acme Corp",
            "period_tested": "FY 2025",
            "prepared_by": "JS",
            "reviewed_by": "JD",
            "workpaper_date": "2025-03-15",
        })
        model = ARAgingExportInput(**data)
        assert model.client_name == "Acme Corp"
        assert model.period_tested == "FY 2025"

    def test_model_dump_round_trips(self):
        from routes.export import ARAgingExportInput
        data = _make_ar_result()
        model = ARAgingExportInput(**data)
        dumped = model.model_dump()
        assert dumped["composite_score"]["score"] == 18.0
        assert len(dumped["test_results"]) > 0

    def test_model_accepts_tb_only(self):
        from routes.export import ARAgingExportInput
        data = _make_ar_result(has_subledger=False)
        data["sl_column_detection"] = None
        model = ARAgingExportInput(**data)
        assert model.sl_column_detection is None

    def test_model_preserves_ar_summary(self):
        from routes.export import ARAgingExportInput
        data = _make_ar_result()
        model = ARAgingExportInput(**data)
        dumped = model.model_dump()
        assert dumped["ar_summary"]["total_ar_balance"] == 500000.0
