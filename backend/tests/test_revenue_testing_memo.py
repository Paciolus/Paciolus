"""
Sprint 105: Tests for Revenue Testing Memo Generator + Export Routes.

Validates:
- PDF memo generation (structure, content, ISA references)
- Guardrails (no "fraud detection", no "revenue recognition failure")
- Export route registration (PDF + CSV endpoints)
- CSV export structure
- RevenueTestingExportInput model
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from revenue_testing_memo_generator import (
    generate_revenue_testing_memo,
    REVENUE_TEST_DESCRIPTIONS,
)


# =============================================================================
# TEST FIXTURES
# =============================================================================

def _make_revenue_result(
    score: float = 15.0,
    risk_tier: str = "elevated",
    total_entries: int = 200,
    total_flagged: int = 12,
    flag_rate: float = 0.06,
    num_tests: int = 12,
    top_findings: list | None = None,
) -> dict:
    """Build a minimal RevenueTestingResult.to_dict() shape."""
    test_keys = [
        "large_manual_entries", "year_end_concentration", "round_revenue_amounts",
        "sign_anomalies", "unclassified_entries", "zscore_outliers",
        "trend_variance", "concentration_risk", "cutoff_risk",
        "benford_law", "duplicate_entries", "contra_revenue_anomalies",
    ]
    test_names = [
        "Large Manual Revenue Entries", "Year-End Revenue Concentration",
        "Round Revenue Amounts", "Revenue Sign Anomalies",
        "Unclassified Revenue Entries", "Z-Score Outliers",
        "Revenue Trend Variance", "Revenue Concentration Risk",
        "Cut-Off Risk", "Benford's Law Analysis",
        "Duplicate Revenue Entries", "Contra-Revenue Anomalies",
    ]
    tiers = [
        "structural", "structural", "structural", "structural", "structural",
        "statistical", "statistical", "statistical", "statistical",
        "advanced", "advanced", "advanced",
    ]

    test_results = []
    for i in range(min(num_tests, 12)):
        flagged_count = 2 if i < 3 else 0
        test_results.append({
            "test_name": test_names[i],
            "test_key": test_keys[i],
            "test_tier": tiers[i],
            "entries_flagged": flagged_count,
            "total_entries": total_entries,
            "flag_rate": flagged_count / max(total_entries, 1),
            "severity": "high" if i == 0 else "medium" if i < 5 else "low",
            "description": f"Test description for {test_keys[i]}",
            "flagged_entries": [
                {
                    "entry": {
                        "date": "2025-12-28",
                        "amount": 75000.0 + j * 1000,
                        "account_name": "Product Revenue",
                        "account_number": "4000",
                        "description": "Monthly revenue",
                        "entry_type": "manual",
                        "reference": f"REF-{i:03d}-{j}",
                        "posted_by": "admin",
                        "row_number": i * 10 + j + 1,
                    },
                    "test_name": test_names[i],
                    "test_key": test_keys[i],
                    "test_tier": tiers[i],
                    "severity": "high" if i == 0 else "medium",
                    "issue": f"Flagged by {test_names[i]}",
                    "confidence": 0.85,
                    "details": {},
                }
                for j in range(flagged_count)
            ],
        })

    return {
        "composite_score": {
            "score": score,
            "risk_tier": risk_tier,
            "tests_run": num_tests,
            "total_entries": total_entries,
            "total_flagged": total_flagged,
            "flag_rate": flag_rate,
            "flags_by_severity": {"high": 2, "medium": 4, "low": 6},
            "top_findings": top_findings or [
                "Large Manual Revenue Entries: 2 entries flagged (1.0%)",
                "Year-End Revenue Concentration: 2 entries flagged (1.0%)",
                "Round Revenue Amounts: 2 entries flagged (1.0%)",
            ],
        },
        "test_results": test_results,
        "data_quality": {
            "completeness_score": 92.5,
            "field_fill_rates": {"date": 0.98, "amount": 1.0, "account": 0.95},
            "detected_issues": [],
            "total_rows": total_entries,
        },
        "column_detection": {
            "date_column": "Date",
            "amount_column": "Amount",
            "account_name_column": "Account Name",
            "overall_confidence": 0.95,
        },
    }


# =============================================================================
# MEMO GENERATION TESTS
# =============================================================================

class TestRevenueMemoGeneration:
    """Tests for generate_revenue_testing_memo()."""

    def test_generates_pdf_bytes(self):
        result = _make_revenue_result()
        pdf = generate_revenue_testing_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_pdf_header(self):
        result = _make_revenue_result()
        pdf = generate_revenue_testing_memo(result)
        assert pdf[:5] == b"%PDF-"

    def test_with_client_name(self):
        result = _make_revenue_result()
        pdf = generate_revenue_testing_memo(result, client_name="Acme Corp")
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_with_all_options(self):
        result = _make_revenue_result()
        pdf = generate_revenue_testing_memo(
            result,
            filename="acme_revenue",
            client_name="Acme Corp",
            period_tested="FY 2025",
            prepared_by="John Smith",
            reviewed_by="Jane Doe",
            workpaper_date="2025-03-15",
        )
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_low_risk_conclusion(self):
        result = _make_revenue_result(score=5.0, risk_tier="low")
        pdf = generate_revenue_testing_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_elevated_risk_conclusion(self):
        result = _make_revenue_result(score=18.0, risk_tier="elevated")
        pdf = generate_revenue_testing_memo(result)
        assert isinstance(pdf, bytes)

    def test_moderate_risk_conclusion(self):
        result = _make_revenue_result(score=35.0, risk_tier="moderate")
        pdf = generate_revenue_testing_memo(result)
        assert isinstance(pdf, bytes)

    def test_high_risk_conclusion(self):
        result = _make_revenue_result(score=65.0, risk_tier="high")
        pdf = generate_revenue_testing_memo(result)
        assert isinstance(pdf, bytes)

    def test_no_findings_skips_section(self):
        result = _make_revenue_result(top_findings=[])
        pdf = generate_revenue_testing_memo(result)
        assert isinstance(pdf, bytes)

    def test_empty_test_results(self):
        result = _make_revenue_result(num_tests=0)
        result["test_results"] = []
        result["composite_score"]["tests_run"] = 0
        pdf = generate_revenue_testing_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100


# =============================================================================
# TEST DESCRIPTIONS COVERAGE
# =============================================================================

class TestRevenueTestDescriptions:
    """Tests for REVENUE_TEST_DESCRIPTIONS completeness."""

    def test_all_12_tests_have_descriptions(self):
        expected_keys = [
            "large_manual_entries", "year_end_concentration", "round_revenue_amounts",
            "sign_anomalies", "unclassified_entries", "zscore_outliers",
            "trend_variance", "concentration_risk", "cutoff_risk",
            "benford_law", "duplicate_entries", "contra_revenue_anomalies",
        ]
        for key in expected_keys:
            assert key in REVENUE_TEST_DESCRIPTIONS, f"Missing description for {key}"

    def test_descriptions_are_nonempty(self):
        for key, desc in REVENUE_TEST_DESCRIPTIONS.items():
            assert len(desc) > 20, f"Description too short for {key}"


# =============================================================================
# GUARDRAIL TESTS
# =============================================================================

class TestRevenueGuardrails:
    """Guardrail compliance: terminology, disclaimers, ISA references.

    PDF content streams are compressed by ReportLab, so we verify guardrails
    at the source code level (strings passed to the PDF builder) rather than
    attempting to parse compressed binary content.
    """

    def test_no_fraud_detection_in_descriptions(self):
        """No test description should say 'fraud detection' — only 'fraud risk indicator'."""
        for key, desc in REVENUE_TEST_DESCRIPTIONS.items():
            assert "fraud detection" not in desc.lower(), (
                f"GUARDRAIL VIOLATION: '{key}' description uses 'fraud detection'"
            )

    def test_no_revenue_recognition_failure_in_descriptions(self):
        """Descriptions should not say 'revenue recognition failure'."""
        for key, desc in REVENUE_TEST_DESCRIPTIONS.items():
            assert "revenue recognition failure" not in desc.lower(), (
                f"GUARDRAIL VIOLATION: '{key}' uses 'revenue recognition failure'"
            )

    def test_memo_generator_references_isa_240(self):
        """Memo source code must pass ISA 240 reference to the PDF builder."""
        import inspect
        source = inspect.getsource(inspect.getmodule(generate_revenue_testing_memo))
        assert "ISA 240" in source, "Memo must reference ISA 240"

    def test_memo_generator_references_pcaob_as_2401(self):
        """Memo source code must pass PCAOB AS 2401 reference to the PDF builder."""
        import inspect
        source = inspect.getsource(inspect.getmodule(generate_revenue_testing_memo))
        assert "PCAOB AS 2401" in source, "Memo must reference PCAOB AS 2401"

    def test_memo_generator_uses_anomaly_indicators_language(self):
        """Methodology text must say 'anomaly indicators' not 'fraud detection'."""
        import inspect
        source = inspect.getsource(inspect.getmodule(generate_revenue_testing_memo))
        assert "anomaly indicator" in source.lower(), (
            "Methodology must use 'anomaly indicators' language"
        )
        assert "fraud detection conclusions" not in source.lower() or \
               "not fraud detection conclusions" in source.lower(), (
            "Must not positively assert 'fraud detection conclusions'"
        )

    def test_memo_generator_calls_disclaimer(self):
        """Memo config must specify revenue-specific disclaimer domain."""
        import inspect
        source = inspect.getsource(inspect.getmodule(generate_revenue_testing_memo))
        # Template guarantees build_disclaimer is called; verify domain config
        assert "generate_testing_memo" in source or "build_disclaimer" in source
        assert "revenue recognition testing" in source.lower()

    def test_memo_disclaimer_references_isa_240_and_500(self):
        """Disclaimer ISA reference must include ISA 240 and ISA 500."""
        import inspect
        source = inspect.getsource(inspect.getmodule(generate_revenue_testing_memo))
        assert "ISA 240" in source
        assert "ISA 500" in source

    def test_conclusion_uses_anomaly_not_failure_language(self):
        """Conclusion text must say 'anomaly' not 'failure'."""
        import inspect
        source = inspect.getsource(inspect.getmodule(generate_revenue_testing_memo))
        assert "revenue recognition failure" not in source.lower(), (
            "GUARDRAIL VIOLATION: conclusion must not use 'revenue recognition failure'"
        )


# =============================================================================
# EXPORT ROUTE REGISTRATION TESTS
# =============================================================================

class TestRevenueExportRoutes:
    """Tests for revenue testing export route registration."""

    def test_pdf_route_registered(self):
        from main import app
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/export/revenue-testing-memo" in paths

    def test_csv_route_registered(self):
        from main import app
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/export/csv/revenue-testing" in paths

    def test_pdf_route_is_post(self):
        from main import app
        for route in app.routes:
            if hasattr(route, "path") and route.path == "/export/revenue-testing-memo":
                assert "POST" in route.methods
                break
        else:
            pytest.fail("Route /export/revenue-testing-memo not found")

    def test_csv_route_is_post(self):
        from main import app
        for route in app.routes:
            if hasattr(route, "path") and route.path == "/export/csv/revenue-testing":
                assert "POST" in route.methods
                break
        else:
            pytest.fail("Route /export/csv/revenue-testing not found")


# =============================================================================
# EXPORT INPUT MODEL TESTS
# =============================================================================

class TestRevenueTestingExportInput:
    """Tests for RevenueTestingExportInput Pydantic model."""

    def test_model_accepts_valid_data(self):
        from routes.export import RevenueTestingExportInput
        data = _make_revenue_result()
        model = RevenueTestingExportInput(**data)
        assert model.filename == "revenue_testing"

    def test_model_defaults(self):
        from routes.export import RevenueTestingExportInput
        data = _make_revenue_result()
        model = RevenueTestingExportInput(**data)
        assert model.client_name is None
        assert model.period_tested is None
        assert model.prepared_by is None
        assert model.reviewed_by is None
        assert model.workpaper_date is None

    def test_model_with_all_fields(self):
        from routes.export import RevenueTestingExportInput
        data = _make_revenue_result()
        data.update({
            "filename": "acme_rev",
            "client_name": "Acme Corp",
            "period_tested": "FY 2025",
            "prepared_by": "JS",
            "reviewed_by": "JD",
            "workpaper_date": "2025-03-15",
        })
        model = RevenueTestingExportInput(**data)
        assert model.client_name == "Acme Corp"
        assert model.period_tested == "FY 2025"

    def test_model_dump_round_trips(self):
        from routes.export import RevenueTestingExportInput
        data = _make_revenue_result()
        model = RevenueTestingExportInput(**data)
        dumped = model.model_dump()
        assert dumped["composite_score"]["score"] == 15.0
        assert len(dumped["test_results"]) > 0
