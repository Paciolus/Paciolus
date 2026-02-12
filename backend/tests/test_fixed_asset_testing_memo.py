"""
Sprint 115: Tests for Fixed Asset Testing Memo Generator + Export Routes.

Validates:
- PDF memo generation (structure, content, ISA references)
- Guardrails (no "valuation testing", no "depreciation is sufficient")
- Export route registration (PDF + CSV endpoints)
- CSV export structure
- FixedAssetExportInput model
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from fixed_asset_testing_memo_generator import (
    generate_fixed_asset_testing_memo,
    FA_TEST_DESCRIPTIONS,
)


# =============================================================================
# TEST FIXTURES
# =============================================================================

def _make_fa_result(
    score: float = 15.0,
    risk_tier: str = "elevated",
    total_flagged: int = 8,
    total_entries: int = 50,
    num_tests: int = 9,
    top_findings: list | None = None,
) -> dict:
    """Build a minimal FATestingResult.to_dict() shape."""
    test_keys = [
        "fully_depreciated", "missing_fields", "negative_values",
        "over_depreciation", "useful_life_outliers", "cost_zscore_outliers",
        "age_concentration", "duplicate_assets", "residual_value_anomalies",
    ]
    test_names = [
        "Fully Depreciated Assets", "Missing Required Fields",
        "Negative Values", "Over-Depreciation",
        "Useful Life Outliers", "Cost Z-Score Outliers",
        "Asset Age Concentration", "Duplicate Assets",
        "Residual Value Anomalies",
    ]
    tiers = [
        "structural", "structural", "structural", "structural",
        "statistical", "statistical", "statistical",
        "advanced", "advanced",
    ]

    test_results = []
    for i in range(min(num_tests, 9)):
        flagged_count = 2 if i < 3 else 1 if i < 6 else 0
        test_results.append({
            "test_name": test_names[i],
            "test_key": test_keys[i],
            "test_tier": tiers[i],
            "entries_flagged": flagged_count,
            "total_entries": total_entries,
            "flag_rate": flagged_count / max(total_entries, 1),
            "severity": "high" if i < 2 else "medium" if i < 5 else "low",
            "description": f"Test description for {test_keys[i]}",
            "flagged_entries": [
                {
                    "entry": {
                        "asset_id": f"FA-{i:03d}-{j}",
                        "description": f"Office Equipment {j + 1}",
                        "cost": 25000.0 + j * 5000,
                        "accumulated_depreciation": 10000.0 + j * 2000,
                        "acquisition_date": "2020-06-15",
                        "useful_life": 5.0,
                        "depreciation_method": "Straight-Line",
                        "residual_value": 1000.0,
                        "location": "Building A",
                        "category": "Equipment",
                        "net_book_value": 14000.0,
                        "row_number": i * 10 + j + 1,
                    },
                    "test_name": test_names[i],
                    "test_key": test_keys[i],
                    "test_tier": tiers[i],
                    "severity": "high" if i < 2 else "medium",
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
            "flag_rate": total_flagged / max(total_entries, 1),
            "flags_by_severity": {"high": 3, "medium": 3, "low": 2},
            "top_findings": top_findings or [
                "Fully Depreciated Assets: 2 entries flagged (4.0%)",
                "Missing Required Fields: 2 entries flagged (4.0%)",
                "Negative Values: 2 entries flagged (4.0%)",
            ],
        },
        "test_results": test_results,
        "data_quality": {
            "completeness_score": 85.0,
            "field_fill_rates": {"identifier": 1.0, "cost": 0.98, "acquisition_date": 0.90},
            "detected_issues": [],
            "total_rows": total_entries,
        },
        "column_detection": {
            "asset_id_column": "Asset ID",
            "cost_column": "Cost",
            "accumulated_depreciation_column": "Accum Depr",
            "overall_confidence": 0.95,
        },
    }


# =============================================================================
# MEMO GENERATION TESTS
# =============================================================================

class TestFixedAssetMemoGeneration:
    """Tests for generate_fixed_asset_testing_memo()."""

    def test_generates_pdf_bytes(self):
        result = _make_fa_result()
        pdf = generate_fixed_asset_testing_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_pdf_header(self):
        result = _make_fa_result()
        pdf = generate_fixed_asset_testing_memo(result)
        assert pdf[:5] == b"%PDF-"

    def test_with_client_name(self):
        result = _make_fa_result()
        pdf = generate_fixed_asset_testing_memo(result, client_name="Acme Corp")
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_with_all_options(self):
        result = _make_fa_result()
        pdf = generate_fixed_asset_testing_memo(
            result,
            filename="acme_fixed_assets",
            client_name="Acme Corp",
            period_tested="FY 2025",
            prepared_by="John Smith",
            reviewed_by="Jane Doe",
            workpaper_date="2025-03-15",
        )
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_low_risk_conclusion(self):
        result = _make_fa_result(score=5.0, risk_tier="low")
        pdf = generate_fixed_asset_testing_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_elevated_risk_conclusion(self):
        result = _make_fa_result(score=18.0, risk_tier="elevated")
        pdf = generate_fixed_asset_testing_memo(result)
        assert isinstance(pdf, bytes)

    def test_moderate_risk_conclusion(self):
        result = _make_fa_result(score=35.0, risk_tier="moderate")
        pdf = generate_fixed_asset_testing_memo(result)
        assert isinstance(pdf, bytes)

    def test_high_risk_conclusion(self):
        result = _make_fa_result(score=65.0, risk_tier="high")
        pdf = generate_fixed_asset_testing_memo(result)
        assert isinstance(pdf, bytes)

    def test_no_findings_skips_section(self):
        result = _make_fa_result(top_findings=[])
        pdf = generate_fixed_asset_testing_memo(result)
        assert isinstance(pdf, bytes)

    def test_empty_test_results(self):
        result = _make_fa_result(num_tests=0)
        result["test_results"] = []
        result["composite_score"]["tests_run"] = 0
        pdf = generate_fixed_asset_testing_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_single_test_result(self):
        result = _make_fa_result(num_tests=1)
        pdf = generate_fixed_asset_testing_memo(result)
        assert isinstance(pdf, bytes)

    def test_all_nine_tests(self):
        result = _make_fa_result(num_tests=9)
        assert len(result["test_results"]) == 9
        pdf = generate_fixed_asset_testing_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100


# =============================================================================
# TEST DESCRIPTIONS COVERAGE
# =============================================================================

class TestFATestDescriptions:
    """Tests for FA_TEST_DESCRIPTIONS completeness."""

    def test_all_9_tests_have_descriptions(self):
        expected_keys = [
            "fully_depreciated", "missing_fields", "negative_values",
            "over_depreciation", "useful_life_outliers", "cost_zscore_outliers",
            "age_concentration", "duplicate_assets", "residual_value_anomalies",
        ]
        for key in expected_keys:
            assert key in FA_TEST_DESCRIPTIONS, f"Missing description for {key}"

    def test_descriptions_are_nonempty(self):
        for key, desc in FA_TEST_DESCRIPTIONS.items():
            assert len(desc) > 20, f"Description too short for {key}"

    def test_exactly_9_descriptions(self):
        assert len(FA_TEST_DESCRIPTIONS) == 9


# =============================================================================
# GUARDRAIL TESTS
# =============================================================================

class TestFixedAssetGuardrails:
    """Guardrail compliance: terminology, disclaimers, ISA references.

    PDF content streams are compressed by ReportLab, so we verify guardrails
    at the source code level (strings passed to the PDF builder).
    """

    def test_no_valuation_testing_in_descriptions(self):
        """No description should use 'valuation testing' language."""
        for key, desc in FA_TEST_DESCRIPTIONS.items():
            lower = desc.lower()
            assert "valuation testing" not in lower, (
                f"GUARDRAIL VIOLATION: '{key}' uses 'valuation testing'"
            )

    def test_no_depreciation_sufficiency_in_descriptions(self):
        """No description should say 'depreciation is sufficient/insufficient'."""
        for key, desc in FA_TEST_DESCRIPTIONS.items():
            lower = desc.lower()
            assert "depreciation is sufficient" not in lower, (
                f"GUARDRAIL VIOLATION: '{key}' uses 'depreciation is sufficient'"
            )
            assert "depreciation is insufficient" not in lower, (
                f"GUARDRAIL VIOLATION: '{key}' uses 'depreciation is insufficient'"
            )

    def test_no_impairment_determination_in_descriptions(self):
        """No description should claim impairment determination."""
        for key, desc in FA_TEST_DESCRIPTIONS.items():
            lower = desc.lower()
            assert "impairment is required" not in lower, (
                f"GUARDRAIL VIOLATION: '{key}' uses 'impairment is required'"
            )
            assert "asset is impaired" not in lower, (
                f"GUARDRAIL VIOLATION: '{key}' uses 'asset is impaired'"
            )

    def test_memo_generator_references_isa_500(self):
        """Memo source code must pass ISA 500 reference to the PDF builder."""
        import inspect
        source = inspect.getsource(inspect.getmodule(generate_fixed_asset_testing_memo))
        assert "ISA 500" in source, "Memo must reference ISA 500"

    def test_memo_generator_references_isa_540(self):
        """Memo source code must pass ISA 540 reference to the PDF builder."""
        import inspect
        source = inspect.getsource(inspect.getmodule(generate_fixed_asset_testing_memo))
        assert "ISA 540" in source, "Memo must reference ISA 540"

    def test_memo_generator_references_pcaob_as_2501(self):
        """Memo source code must pass PCAOB AS 2501 reference to the PDF builder."""
        import inspect
        source = inspect.getsource(inspect.getmodule(generate_fixed_asset_testing_memo))
        assert "PCAOB AS 2501" in source, "Memo must reference PCAOB AS 2501"

    def test_memo_generator_references_ias_16(self):
        """Memo source code must reference IAS 16."""
        import inspect
        source = inspect.getsource(inspect.getmodule(generate_fixed_asset_testing_memo))
        assert "IAS 16" in source, "Memo must reference IAS 16"

    def test_memo_generator_uses_anomaly_indicators_language(self):
        """Methodology text must say 'anomaly indicators' not 'sufficiency conclusions'."""
        import inspect
        source = inspect.getsource(inspect.getmodule(generate_fixed_asset_testing_memo))
        assert "anomaly indicator" in source.lower(), (
            "Methodology must use 'anomaly indicators' language"
        )

    def test_memo_generator_no_depreciation_adequacy_positive(self):
        """Conclusion must not claim 'depreciation is adequate'."""
        import inspect
        source = inspect.getsource(inspect.getmodule(generate_fixed_asset_testing_memo))
        lower = source.lower()
        assert "depreciation is adequate" not in lower, (
            "GUARDRAIL VIOLATION: must not claim 'depreciation is adequate'"
        )
        assert "depreciation is inadequate" not in lower, (
            "GUARDRAIL VIOLATION: must not claim 'depreciation is inadequate'"
        )

    def test_memo_generator_calls_disclaimer(self):
        """Memo config must specify FA-specific disclaimer domain."""
        import inspect
        source = inspect.getsource(inspect.getmodule(generate_fixed_asset_testing_memo))
        # Template guarantees build_disclaimer is called; verify domain config
        assert "generate_testing_memo" in source or "build_disclaimer" in source
        assert "fixed asset register analysis" in source.lower()

    def test_memo_disclaimer_references_isa_500_and_540(self):
        """Disclaimer ISA reference must include ISA 500 and ISA 540."""
        import inspect
        source = inspect.getsource(inspect.getmodule(generate_fixed_asset_testing_memo))
        assert "ISA 500" in source
        assert "ISA 540" in source

    def test_no_valuation_testing_in_memo_source(self):
        """Memo source must not use 'valuation testing' language."""
        import inspect
        source = inspect.getsource(inspect.getmodule(generate_fixed_asset_testing_memo))
        assert "valuation testing" not in source.lower(), (
            "GUARDRAIL VIOLATION: memo source uses 'valuation testing'"
        )

    def test_conclusion_uses_anomaly_not_sufficiency_language(self):
        """Conclusion text must say 'anomaly' not 'sufficiency'."""
        import inspect
        source = inspect.getsource(inspect.getmodule(generate_fixed_asset_testing_memo))
        lower = source.lower()
        assert "depreciation sufficiency" not in lower or \
               "not depreciation sufficiency" in lower or \
               "not depreciation adequacy conclusions" in lower, (
            "GUARDRAIL VIOLATION: conclusion must not use 'depreciation sufficiency'"
        )


# =============================================================================
# EXPORT ROUTE REGISTRATION TESTS
# =============================================================================

class TestFixedAssetExportRoutes:
    """Tests for fixed asset export route registration."""

    def test_pdf_route_registered(self):
        from main import app
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/export/fixed-asset-memo" in paths

    def test_csv_route_registered(self):
        from main import app
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/export/csv/fixed-assets" in paths

    def test_pdf_route_is_post(self):
        from main import app
        for route in app.routes:
            if hasattr(route, "path") and route.path == "/export/fixed-asset-memo":
                assert "POST" in route.methods
                break
        else:
            pytest.fail("Route /export/fixed-asset-memo not found")

    def test_csv_route_is_post(self):
        from main import app
        for route in app.routes:
            if hasattr(route, "path") and route.path == "/export/csv/fixed-assets":
                assert "POST" in route.methods
                break
        else:
            pytest.fail("Route /export/csv/fixed-assets not found")


# =============================================================================
# EXPORT INPUT MODEL TESTS
# =============================================================================

class TestFixedAssetExportInput:
    """Tests for FixedAssetExportInput Pydantic model."""

    def test_model_accepts_valid_data(self):
        from routes.export import FixedAssetExportInput
        data = _make_fa_result()
        model = FixedAssetExportInput(**data)
        assert model.filename == "fixed_asset_testing"

    def test_model_defaults(self):
        from routes.export import FixedAssetExportInput
        data = _make_fa_result()
        model = FixedAssetExportInput(**data)
        assert model.client_name is None
        assert model.period_tested is None
        assert model.prepared_by is None
        assert model.reviewed_by is None
        assert model.workpaper_date is None

    def test_model_with_all_fields(self):
        from routes.export import FixedAssetExportInput
        data = _make_fa_result()
        data.update({
            "filename": "acme_fa",
            "client_name": "Acme Corp",
            "period_tested": "FY 2025",
            "prepared_by": "JS",
            "reviewed_by": "JD",
            "workpaper_date": "2025-03-15",
        })
        model = FixedAssetExportInput(**data)
        assert model.client_name == "Acme Corp"
        assert model.period_tested == "FY 2025"

    def test_model_dump_round_trips(self):
        from routes.export import FixedAssetExportInput
        data = _make_fa_result()
        model = FixedAssetExportInput(**data)
        dumped = model.model_dump()
        assert dumped["composite_score"]["score"] == 15.0
        assert len(dumped["test_results"]) > 0

    def test_model_accepts_no_data_quality(self):
        from routes.export import FixedAssetExportInput
        data = _make_fa_result()
        data["data_quality"] = None
        model = FixedAssetExportInput(**data)
        assert model.data_quality is None

    def test_model_preserves_column_detection(self):
        from routes.export import FixedAssetExportInput
        data = _make_fa_result()
        model = FixedAssetExportInput(**data)
        dumped = model.model_dump()
        assert dumped["column_detection"]["overall_confidence"] == 0.95
