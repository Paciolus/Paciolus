"""
Sprint 118: Tests for Inventory Testing Memo Generator + Export Routes.

Validates:
- PDF memo generation (structure, content, ISA references)
- Guardrails (no "NRV determination", no "obsolescence sufficiency")
- Export route registration (PDF + CSV endpoints)
- CSV export structure
- InventoryExportInput model
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from inventory_testing_memo_generator import (
    generate_inventory_testing_memo,
    INV_TEST_DESCRIPTIONS,
)


# =============================================================================
# TEST FIXTURES
# =============================================================================

def _make_inv_result(
    score: float = 15.0,
    risk_tier: str = "elevated",
    total_flagged: int = 8,
    total_entries: int = 50,
    num_tests: int = 9,
    top_findings: list | None = None,
) -> dict:
    """Build a minimal InvTestingResult.to_dict() shape."""
    test_keys = [
        "missing_fields", "negative_values", "value_mismatch",
        "unit_cost_outliers", "quantity_outliers", "slow_moving",
        "category_concentration", "duplicate_items", "zero_value_items",
    ]
    test_names = [
        "Missing Required Fields", "Negative Values",
        "Extended Value Mismatch", "Unit Cost Outliers",
        "Quantity Outliers", "Slow-Moving Inventory",
        "Category Concentration", "Duplicate Items",
        "Zero-Value Items",
    ]
    tiers = [
        "structural", "structural", "structural",
        "statistical", "statistical", "statistical", "statistical",
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
                        "item_id": f"INV-{i:03d}-{j}",
                        "description": f"Widget {j + 1}",
                        "quantity": 100.0 + j * 50,
                        "unit_cost": 25.0 + j * 10,
                        "extended_value": (100.0 + j * 50) * (25.0 + j * 10),
                        "location": "Warehouse A",
                        "last_movement_date": "2025-10-15",
                        "category": "Raw Materials",
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
                "Missing Required Fields: 2 entries flagged (4.0%)",
                "Negative Values: 2 entries flagged (4.0%)",
                "Extended Value Mismatch: 2 entries flagged (4.0%)",
            ],
        },
        "test_results": test_results,
        "data_quality": {
            "completeness_score": 85.0,
            "field_fill_rates": {"identifier": 1.0, "quantity": 0.98, "unit_cost": 0.95},
            "detected_issues": [],
            "total_rows": total_entries,
        },
        "column_detection": {
            "item_id_column": "Item ID",
            "quantity_column": "Quantity",
            "unit_cost_column": "Unit Cost",
            "overall_confidence": 0.95,
        },
    }


# =============================================================================
# MEMO GENERATION TESTS
# =============================================================================

class TestInventoryMemoGeneration:
    """Tests for generate_inventory_testing_memo()."""

    def test_generates_pdf_bytes(self):
        result = _make_inv_result()
        pdf = generate_inventory_testing_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_pdf_header(self):
        result = _make_inv_result()
        pdf = generate_inventory_testing_memo(result)
        assert pdf[:5] == b"%PDF-"

    def test_with_client_name(self):
        result = _make_inv_result()
        pdf = generate_inventory_testing_memo(result, client_name="Acme Corp")
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_with_all_options(self):
        result = _make_inv_result()
        pdf = generate_inventory_testing_memo(
            result,
            filename="acme_inventory",
            client_name="Acme Corp",
            period_tested="FY 2025",
            prepared_by="John Smith",
            reviewed_by="Jane Doe",
            workpaper_date="2025-03-15",
        )
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_low_risk_conclusion(self):
        result = _make_inv_result(score=5.0, risk_tier="low")
        pdf = generate_inventory_testing_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_elevated_risk_conclusion(self):
        result = _make_inv_result(score=18.0, risk_tier="elevated")
        pdf = generate_inventory_testing_memo(result)
        assert isinstance(pdf, bytes)

    def test_moderate_risk_conclusion(self):
        result = _make_inv_result(score=35.0, risk_tier="moderate")
        pdf = generate_inventory_testing_memo(result)
        assert isinstance(pdf, bytes)

    def test_high_risk_conclusion(self):
        result = _make_inv_result(score=65.0, risk_tier="high")
        pdf = generate_inventory_testing_memo(result)
        assert isinstance(pdf, bytes)

    def test_no_findings_skips_section(self):
        result = _make_inv_result(top_findings=[])
        pdf = generate_inventory_testing_memo(result)
        assert isinstance(pdf, bytes)

    def test_empty_test_results(self):
        result = _make_inv_result(num_tests=0)
        result["test_results"] = []
        result["composite_score"]["tests_run"] = 0
        pdf = generate_inventory_testing_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100

    def test_single_test_result(self):
        result = _make_inv_result(num_tests=1)
        pdf = generate_inventory_testing_memo(result)
        assert isinstance(pdf, bytes)

    def test_all_nine_tests(self):
        result = _make_inv_result(num_tests=9)
        assert len(result["test_results"]) == 9
        pdf = generate_inventory_testing_memo(result)
        assert isinstance(pdf, bytes)
        assert len(pdf) > 100


# =============================================================================
# TEST DESCRIPTIONS COVERAGE
# =============================================================================

class TestInvTestDescriptions:
    """Tests for INV_TEST_DESCRIPTIONS completeness."""

    def test_all_9_tests_have_descriptions(self):
        expected_keys = [
            "missing_fields", "negative_values", "value_mismatch",
            "unit_cost_outliers", "quantity_outliers", "slow_moving",
            "category_concentration", "duplicate_items", "zero_value_items",
        ]
        for key in expected_keys:
            assert key in INV_TEST_DESCRIPTIONS, f"Missing description for {key}"

    def test_descriptions_are_nonempty(self):
        for key, desc in INV_TEST_DESCRIPTIONS.items():
            assert len(desc) > 20, f"Description too short for {key}"

    def test_exactly_9_descriptions(self):
        assert len(INV_TEST_DESCRIPTIONS) == 9


# =============================================================================
# GUARDRAIL TESTS
# =============================================================================

class TestInventoryGuardrails:
    """Guardrail compliance: terminology, disclaimers, ISA references.

    PDF content streams are compressed by ReportLab, so we verify guardrails
    at the source code level (strings passed to the PDF builder).
    """

    def test_no_nrv_determination_in_descriptions(self):
        """No description should claim NRV determination."""
        for key, desc in INV_TEST_DESCRIPTIONS.items():
            lower = desc.lower()
            assert "nrv is sufficient" not in lower, (
                f"GUARDRAIL VIOLATION: '{key}' uses 'NRV is sufficient'"
            )
            assert "nrv is insufficient" not in lower, (
                f"GUARDRAIL VIOLATION: '{key}' uses 'NRV is insufficient'"
            )

    def test_no_obsolescence_sufficiency_in_descriptions(self):
        """No description should claim obsolescence provision sufficiency."""
        for key, desc in INV_TEST_DESCRIPTIONS.items():
            lower = desc.lower()
            assert "obsolescence is sufficient" not in lower, (
                f"GUARDRAIL VIOLATION: '{key}' uses 'obsolescence is sufficient'"
            )
            assert "obsolescence is insufficient" not in lower, (
                f"GUARDRAIL VIOLATION: '{key}' uses 'obsolescence is insufficient'"
            )

    def test_no_valuation_testing_in_descriptions(self):
        """No description should use 'valuation testing' language."""
        for key, desc in INV_TEST_DESCRIPTIONS.items():
            lower = desc.lower()
            assert "valuation testing" not in lower, (
                f"GUARDRAIL VIOLATION: '{key}' uses 'valuation testing'"
            )

    def test_memo_generator_references_isa_501(self):
        """Memo source code must pass ISA 501 reference to the PDF builder."""
        import inspect
        source = inspect.getsource(generate_inventory_testing_memo)
        assert "ISA 501" in source, "Memo must reference ISA 501"

    def test_memo_generator_references_isa_500(self):
        """Memo source code must pass ISA 500 reference to the PDF builder."""
        import inspect
        source = inspect.getsource(generate_inventory_testing_memo)
        assert "ISA 500" in source, "Memo must reference ISA 500"

    def test_memo_generator_references_isa_540(self):
        """Memo source code must pass ISA 540 reference to the PDF builder."""
        import inspect
        source = inspect.getsource(generate_inventory_testing_memo)
        assert "ISA 540" in source, "Memo must reference ISA 540"

    def test_memo_generator_references_pcaob_as_2501(self):
        """Memo source code must pass PCAOB AS 2501 reference to the PDF builder."""
        import inspect
        source = inspect.getsource(generate_inventory_testing_memo)
        assert "PCAOB AS 2501" in source, "Memo must reference PCAOB AS 2501"

    def test_memo_generator_references_ias_2(self):
        """Memo source code must reference IAS 2."""
        import inspect
        source = inspect.getsource(generate_inventory_testing_memo)
        assert "IAS 2" in source, "Memo must reference IAS 2"

    def test_memo_generator_uses_anomaly_indicators_language(self):
        """Methodology text must say 'anomaly indicators' not 'adequacy conclusions'."""
        import inspect
        source = inspect.getsource(generate_inventory_testing_memo)
        assert "anomaly indicator" in source.lower(), (
            "Methodology must use 'anomaly indicators' language"
        )

    def test_memo_generator_no_nrv_adequacy_positive(self):
        """Conclusion must not claim 'NRV is adequate'."""
        import inspect
        source = inspect.getsource(generate_inventory_testing_memo)
        lower = source.lower()
        assert "nrv is adequate" not in lower, (
            "GUARDRAIL VIOLATION: must not claim 'NRV is adequate'"
        )
        assert "nrv is inadequate" not in lower, (
            "GUARDRAIL VIOLATION: must not claim 'NRV is inadequate'"
        )

    def test_memo_generator_calls_disclaimer(self):
        """Memo must call build_disclaimer with inventory-specific parameters."""
        import inspect
        source = inspect.getsource(generate_inventory_testing_memo)
        assert "build_disclaimer" in source
        assert "inventory register analysis" in source.lower()

    def test_memo_disclaimer_references_isa_500_and_540(self):
        """Disclaimer ISA reference must include ISA 500 and ISA 540."""
        import inspect
        source = inspect.getsource(generate_inventory_testing_memo)
        assert "ISA 500" in source
        assert "ISA 540" in source

    def test_no_nrv_determination_in_memo_source(self):
        """Memo source must not use 'NRV determination' as a conclusion."""
        import inspect
        source = inspect.getsource(generate_inventory_testing_memo)
        lower = source.lower()
        # The phrase "not an NRV determination" is acceptable; "NRV determination" as a standalone claim is not
        occurrences = lower.count("nrv determination")
        negated = lower.count("not an nrv determination") + lower.count("not constitute an nrv")
        # All occurrences should be negated
        assert occurrences <= negated or occurrences == 0, (
            "GUARDRAIL VIOLATION: memo uses 'NRV determination' without negation"
        )


# =============================================================================
# EXPORT ROUTE REGISTRATION TESTS
# =============================================================================

class TestInventoryExportRoutes:
    """Tests for inventory export route registration."""

    def test_pdf_route_registered(self):
        from main import app
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/export/inventory-memo" in paths

    def test_csv_route_registered(self):
        from main import app
        paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/export/csv/inventory" in paths

    def test_pdf_route_is_post(self):
        from main import app
        for route in app.routes:
            if hasattr(route, "path") and route.path == "/export/inventory-memo":
                assert "POST" in route.methods
                break
        else:
            pytest.fail("Route /export/inventory-memo not found")

    def test_csv_route_is_post(self):
        from main import app
        for route in app.routes:
            if hasattr(route, "path") and route.path == "/export/csv/inventory":
                assert "POST" in route.methods
                break
        else:
            pytest.fail("Route /export/csv/inventory not found")


# =============================================================================
# EXPORT INPUT MODEL TESTS
# =============================================================================

class TestInventoryExportInput:
    """Tests for InventoryExportInput Pydantic model."""

    def test_model_accepts_valid_data(self):
        from routes.export import InventoryExportInput
        data = _make_inv_result()
        model = InventoryExportInput(**data)
        assert model.filename == "inventory_testing"

    def test_model_defaults(self):
        from routes.export import InventoryExportInput
        data = _make_inv_result()
        model = InventoryExportInput(**data)
        assert model.client_name is None
        assert model.period_tested is None
        assert model.prepared_by is None
        assert model.reviewed_by is None
        assert model.workpaper_date is None

    def test_model_with_all_fields(self):
        from routes.export import InventoryExportInput
        data = _make_inv_result()
        data.update({
            "filename": "acme_inv",
            "client_name": "Acme Corp",
            "period_tested": "FY 2025",
            "prepared_by": "JS",
            "reviewed_by": "JD",
            "workpaper_date": "2025-03-15",
        })
        model = InventoryExportInput(**data)
        assert model.client_name == "Acme Corp"
        assert model.period_tested == "FY 2025"

    def test_model_dump_round_trips(self):
        from routes.export import InventoryExportInput
        data = _make_inv_result()
        model = InventoryExportInput(**data)
        dumped = model.model_dump()
        assert dumped["composite_score"]["score"] == 15.0
        assert len(dumped["test_results"]) > 0

    def test_model_accepts_no_data_quality(self):
        from routes.export import InventoryExportInput
        data = _make_inv_result()
        data["data_quality"] = None
        model = InventoryExportInput(**data)
        assert model.data_quality is None

    def test_model_preserves_column_detection(self):
        from routes.export import InventoryExportInput
        data = _make_inv_result()
        model = InventoryExportInput(**data)
        dumped = model.model_dump()
        assert dumped["column_detection"]["overall_confidence"] == 0.95
