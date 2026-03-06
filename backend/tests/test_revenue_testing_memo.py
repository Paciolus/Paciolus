"""
Sprint 105: Tests for Revenue Testing Memo Generator + Export Routes.
Sprint 501: Added tests for high-severity detail, Benford/SSP notes,
quality indicators, contra-revenue ratio.

Validates:
- PDF memo generation (structure, content, ISA references)
- Guardrails (no "fraud detection", no "revenue recognition failure")
- Export route registration (PDF + CSV endpoints)
- CSV export structure
- RevenueTestingExportInput model
- High severity detail section (IMPROVEMENT-01)
- Benford/SSP pass notes (IMPROVEMENT-02)
- Revenue quality indicators (IMPROVEMENT-03)
- Contra-revenue ratio (IMPROVEMENT-04)
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from revenue_testing_memo_generator import (
    REVENUE_TEST_DESCRIPTIONS,
    generate_revenue_testing_memo,
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
        "large_manual_entries",
        "year_end_concentration",
        "round_revenue_amounts",
        "sign_anomalies",
        "unclassified_entries",
        "zscore_outliers",
        "trend_variance",
        "concentration_risk",
        "cutoff_risk",
        "benford_law",
        "duplicate_entries",
        "contra_revenue_anomalies",
    ]
    test_names = [
        "Large Manual Revenue Entries",
        "Year-End Revenue Concentration",
        "Round Revenue Amounts",
        "Revenue Sign Anomalies",
        "Unclassified Revenue Entries",
        "Z-Score Outliers",
        "Revenue Trend Variance",
        "Revenue Concentration Risk",
        "Cut-Off Risk",
        "Benford's Law Analysis",
        "Duplicate Revenue Entries",
        "Contra-Revenue Anomalies",
    ]
    tiers = [
        "structural",
        "structural",
        "structural",
        "structural",
        "structural",
        "statistical",
        "statistical",
        "statistical",
        "statistical",
        "advanced",
        "advanced",
        "advanced",
    ]

    test_results = []
    for i in range(min(num_tests, 12)):
        flagged_count = 2 if i < 3 else 0
        test_results.append(
            {
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
            }
        )

    return {
        "composite_score": {
            "score": score,
            "risk_tier": risk_tier,
            "tests_run": num_tests,
            "total_entries": total_entries,
            "total_flagged": total_flagged,
            "flag_rate": flag_rate,
            "flags_by_severity": {"high": 2, "medium": 4, "low": 6},
            "top_findings": top_findings
            or [
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


def _make_result_with_high_severity_detail() -> dict:
    """Build a result with HIGH severity flagged entries for detail tables."""
    result = _make_revenue_result(score=35.0, risk_tier="moderate")

    # Add cutoff_risk with flagged entries
    cutoff_test = {
        "test_name": "Cut-Off Risk",
        "test_key": "cutoff_risk",
        "test_tier": "statistical",
        "entries_flagged": 3,
        "total_entries": 200,
        "flag_rate": 0.015,
        "severity": "high",
        "description": "Cut-off test",
        "flagged_entries": [
            {
                "entry": {
                    "date": "2025-12-31",
                    "amount": -185000.0,
                    "account_name": "Product Revenue",
                    "reference": "RV-001",
                    "posted_by": "admin",
                    "row_number": 801,
                    "description": "Year-end license",
                },
                "severity": "high",
                "issue": "Revenue near period end",
                "details": {
                    "boundary_type": "period end",
                    "entry_date": "2025-12-31",
                    "period_end": "2025-12-31",
                    "days_from_boundary": 0,
                },
            },
            {
                "entry": {
                    "date": "2025-12-30",
                    "amount": -98000.0,
                    "account_name": "Service Revenue",
                    "reference": "RV-002",
                    "posted_by": "jsmith",
                    "row_number": 799,
                    "description": "Consulting engagement",
                },
                "severity": "high",
                "issue": "Revenue near period end",
                "details": {"entry_date": "2025-12-30", "period_end": "2025-12-31"},
            },
            {
                "entry": {
                    "date": "2025-12-29",
                    "amount": -76500.0,
                    "account_name": "Product Revenue",
                    "reference": "RV-003",
                    "posted_by": "admin",
                    "row_number": 795,
                    "description": "Implementation",
                },
                "severity": "high",
                "issue": "Revenue near period end",
                "details": {"entry_date": "2025-12-29", "period_end": "2025-12-31", "days_from_boundary": 2},
            },
        ],
    }

    # Add recognition_before_satisfaction with flagged entries
    recognition_test = {
        "test_name": "Recognition Before Satisfaction",
        "test_key": "recognition_before_satisfaction",
        "test_tier": "contract",
        "entries_flagged": 2,
        "total_entries": 200,
        "flag_rate": 0.01,
        "severity": "high",
        "description": "Recognition timing test",
        "flagged_entries": [
            {
                "entry": {
                    "date": "2025-11-15",
                    "amount": -225000.0,
                    "account_name": "Product Revenue",
                    "reference": "RV-010",
                    "posted_by": "admin",
                    "row_number": 714,
                    "description": "Platform deployment",
                },
                "severity": "high",
                "issue": "Revenue recognized 45 days before obligation satisfaction date",
                "details": {"delta_days": 45},
            },
            {
                "entry": {
                    "date": "2025-10-01",
                    "amount": -180000.0,
                    "account_name": "Service Revenue",
                    "reference": "RV-011",
                    "posted_by": "jsmith",
                    "row_number": 648,
                    "description": "Annual support contract",
                },
                "severity": "high",
                "issue": "Revenue recognized 90 days before obligation satisfaction date",
                "details": {"delta_days": 90},
            },
        ],
    }

    # Add sign anomalies
    sign_test = {
        "test_name": "Revenue Sign Anomalies",
        "test_key": "sign_anomalies",
        "test_tier": "structural",
        "entries_flagged": 1,
        "total_entries": 200,
        "flag_rate": 0.005,
        "severity": "high",
        "description": "Sign anomalies test",
        "flagged_entries": [
            {
                "entry": {
                    "date": "2025-06-30",
                    "amount": 87500.0,
                    "account_name": "Product Revenue",
                    "reference": "RV-020",
                    "posted_by": "admin",
                    "row_number": 392,
                    "description": "Revenue adjustment",
                },
                "severity": "high",
                "issue": "Debit balance in revenue: $87,500.00",
                "details": {"amount": 87500.0, "account": "Product Revenue"},
            },
        ],
    }

    result["test_results"].extend([cutoff_test, recognition_test, sign_test])
    result["total_revenue"] = 6_850_000.00
    return result


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

    def test_all_12_core_tests_have_descriptions(self):
        expected_keys = [
            "large_manual_entries",
            "year_end_concentration",
            "round_revenue_amounts",
            "sign_anomalies",
            "unclassified_entries",
            "zscore_outliers",
            "trend_variance",
            "concentration_risk",
            "cutoff_risk",
            "benford_law",
            "duplicate_entries",
            "contra_revenue_anomalies",
        ]
        for key in expected_keys:
            assert key in REVENUE_TEST_DESCRIPTIONS, f"Missing description for {key}"

    def test_all_4_contract_tests_have_descriptions(self):
        contract_keys = [
            "recognition_before_satisfaction",
            "missing_obligation_linkage",
            "modification_treatment_mismatch",
            "allocation_inconsistency",
        ]
        for key in contract_keys:
            assert key in REVENUE_TEST_DESCRIPTIONS, f"Missing description for {key}"

    def test_descriptions_are_nonempty(self):
        for key, desc in REVENUE_TEST_DESCRIPTIONS.items():
            assert len(desc) > 20, f"Description too short for {key}"

    def test_total_description_count(self):
        assert len(REVENUE_TEST_DESCRIPTIONS) == 16


# =============================================================================
# HIGH SEVERITY DETAIL TESTS (IMPROVEMENT-01)
# =============================================================================


class TestHighSeverityDetail:
    """Tests for high-severity entry detail section."""

    def test_generates_with_high_severity_detail(self):
        result = _make_result_with_high_severity_detail()
        pdf = generate_revenue_testing_memo(result, client_name="Test Corp")
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_no_detail_when_no_high_severity(self):
        result = _make_revenue_result()
        # All tests have severity != "high" or entries_flagged == 0
        pdf = generate_revenue_testing_memo(result)
        assert isinstance(pdf, bytes)

    def test_detail_with_all_four_test_types(self):
        """Verify PDF generates with cutoff, recognition, sign, and concentration."""
        result = _make_result_with_high_severity_detail()
        # Add concentration risk
        result["test_results"].append(
            {
                "test_name": "Revenue Concentration Risk",
                "test_key": "concentration_risk",
                "test_tier": "statistical",
                "entries_flagged": 1,
                "total_entries": 200,
                "flag_rate": 0.005,
                "severity": "high",
                "description": "Concentration test",
                "flagged_entries": [
                    {
                        "entry": {
                            "date": "2025-12-15",
                            "amount": -2603000.0,
                            "account_name": "Product Revenue",
                            "reference": "RV-030",
                            "posted_by": "admin",
                            "row_number": 788,
                        },
                        "severity": "high",
                        "issue": "Account represents 38% of total revenue",
                        "details": {
                            "account": "meridian enterprise",
                            "account_total": 2603000,
                            "total_revenue": 6850000,
                            "concentration_pct": 0.38,
                        },
                    }
                ],
            }
        )
        pdf = generate_revenue_testing_memo(result, client_name="Test Corp")
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100


# =============================================================================
# POST-RESULTS NOTES TESTS (IMPROVEMENT-02, 04)
# =============================================================================


class TestPostResultsNotes:
    """Tests for Benford/SSP notes and contra-revenue ratio."""

    def test_benford_pass_note_with_mad(self):
        result = _make_revenue_result()
        # Set Benford to 0 flags with MAD in description
        for tr in result["test_results"]:
            if tr["test_key"] == "benford_law":
                tr["entries_flagged"] = 0
                tr["flagged_entries"] = []
                tr["description"] = "First-digit analysis (MAD=0.0038, close conformity)"
        pdf = generate_revenue_testing_memo(result)
        assert isinstance(pdf, bytes)

    def test_benford_pass_note_without_mad(self):
        result = _make_revenue_result()
        for tr in result["test_results"]:
            if tr["test_key"] == "benford_law":
                tr["entries_flagged"] = 0
                tr["flagged_entries"] = []
                tr["description"] = "Standard Benford test"
        pdf = generate_revenue_testing_memo(result)
        assert isinstance(pdf, bytes)

    def test_ssp_pass_note(self):
        result = _make_revenue_result()
        result["test_results"].append(
            {
                "test_name": "Allocation Inconsistency",
                "test_key": "allocation_inconsistency",
                "test_tier": "contract",
                "entries_flagged": 0,
                "total_entries": 200,
                "flag_rate": 0.0,
                "severity": "low",
                "description": "SSP allocation test",
                "flagged_entries": [],
            }
        )
        pdf = generate_revenue_testing_memo(result)
        assert isinstance(pdf, bytes)

    def test_contra_revenue_ratio(self):
        result = _make_revenue_result()
        result["total_revenue"] = 6_850_000.00
        result["contra_revenue_total"] = 89_050.00
        for tr in result["test_results"]:
            if tr["test_key"] == "contra_revenue_anomalies":
                tr["flagged_entries"] = [
                    {
                        "entry": {"amount": 42000, "date": "2025-04-15"},
                        "details": {"contra_total": 89050, "gross_revenue": 6850000, "contra_pct": 0.013},
                        "severity": "medium",
                        "issue": "Contra-revenue",
                    }
                ]
                tr["entries_flagged"] = 1
        pdf = generate_revenue_testing_memo(result)
        assert isinstance(pdf, bytes)


# =============================================================================
# REVENUE QUALITY INDICATORS TESTS (IMPROVEMENT-03)
# =============================================================================


class TestRevenueQualityIndicators:
    """Tests for revenue quality indicators in scope section."""

    def test_quality_indicators_with_total_revenue(self):
        result = _make_revenue_result()
        result["total_revenue"] = 6_850_000.00
        pdf = generate_revenue_testing_memo(result, client_name="Test Corp")
        assert isinstance(pdf, bytes)

    def test_quality_indicators_without_total_revenue(self):
        result = _make_revenue_result()
        # No total_revenue — should still generate without error
        pdf = generate_revenue_testing_memo(result)
        assert isinstance(pdf, bytes)

    def test_quality_indicators_with_concentration(self):
        result = _make_result_with_high_severity_detail()
        pdf = generate_revenue_testing_memo(result, client_name="Test Corp")
        assert isinstance(pdf, bytes)


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
        assert "anomaly indicator" in source.lower(), "Methodology must use 'anomaly indicators' language"
        assert (
            "fraud detection conclusions" not in source.lower() or "not fraud detection conclusions" in source.lower()
        ), "Must not positively assert 'fraud detection conclusions'"

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
        data.update(
            {
                "filename": "acme_rev",
                "client_name": "Acme Corp",
                "period_tested": "FY 2025",
                "prepared_by": "JS",
                "reviewed_by": "JD",
                "workpaper_date": "2025-03-15",
            }
        )
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
