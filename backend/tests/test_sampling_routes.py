"""
Tests for Sampling Routes — Sprint 271
Phase XXXVI: Tool 12

Validates route registration, response models, and memo generator.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.export_schemas import (
    SamplingDesignMemoInput,
    SamplingEvaluationMemoInput,
    SamplingSelectionCSVInput,
)
from shared.testing_response_schemas import (
    SamplingDesignResponse,
    SamplingErrorResponse,
    SamplingEvaluationResponse,
    SamplingSelectedItemResponse,
    SamplingStratumSummaryResponse,
)

# =============================================================================
# Route Registration
# =============================================================================

class TestRouteRegistration:
    def test_sampling_routes_registered(self):
        from main import app
        route_paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/audit/sampling/design" in route_paths
        assert "/audit/sampling/evaluate" in route_paths

    def test_sampling_router_tags(self):
        from routes.sampling import router
        assert "sampling" in router.tags

    def test_export_routes_registered(self):
        from main import app
        route_paths = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/export/csv/sampling-selection" in route_paths
        assert "/export/sampling-design-memo" in route_paths
        assert "/export/sampling-evaluation-memo" in route_paths


# =============================================================================
# Response Models
# =============================================================================

class TestResponseModels:
    def test_selected_item_response(self):
        item = SamplingSelectedItemResponse(
            row_index=5,
            item_id="INV-001",
            description="Widget A",
            recorded_amount=1500.50,
            stratum="remainder",
            selection_method="mus_interval",
            interval_position=12500.0,
        )
        assert item.row_index == 5
        assert item.item_id == "INV-001"
        assert item.recorded_amount == 1500.50
        assert item.stratum == "remainder"
        assert item.selection_method == "mus_interval"

    def test_selected_item_high_value(self):
        item = SamplingSelectedItemResponse(
            row_index=1,
            item_id="HV-001",
            description="Large asset",
            recorded_amount=500000.0,
            stratum="high_value",
            selection_method="high_value_100pct",
            interval_position=None,
        )
        assert item.stratum == "high_value"
        assert item.interval_position is None

    def test_stratum_summary_response(self):
        stratum = SamplingStratumSummaryResponse(
            stratum="High Value",
            threshold=">= $100,000",
            count=5,
            total_value=750000.0,
            sample_size=5,
        )
        assert stratum.count == 5
        assert stratum.total_value == 750000.0

    def test_design_response(self):
        resp = SamplingDesignResponse(
            method="mus",
            confidence_level=0.95,
            confidence_factor=3.0,
            tolerable_misstatement=50000.0,
            expected_misstatement=0.0,
            population_size=1000,
            population_value=5000000.0,
            sampling_interval=16666.67,
            calculated_sample_size=300,
            actual_sample_size=300,
            high_value_count=0,
            high_value_total=0.0,
            remainder_count=1000,
            remainder_sample_size=300,
            selected_items=[],
            random_start=5432.10,
            strata_summary=[],
        )
        assert resp.method == "mus"
        assert resp.confidence_level == 0.95
        assert resp.population_size == 1000
        assert resp.sampling_interval == 16666.67

    def test_design_response_random_method(self):
        resp = SamplingDesignResponse(
            method="random",
            confidence_level=0.90,
            confidence_factor=2.31,
            tolerable_misstatement=25000.0,
            expected_misstatement=0.0,
            population_size=500,
            population_value=1000000.0,
            sampling_interval=None,
            calculated_sample_size=50,
            actual_sample_size=50,
            high_value_count=0,
            high_value_total=0.0,
            remainder_count=500,
            remainder_sample_size=50,
            selected_items=[],
            random_start=None,
            strata_summary=[],
        )
        assert resp.method == "random"
        assert resp.sampling_interval is None
        assert resp.random_start is None

    def test_error_response(self):
        err = SamplingErrorResponse(
            row_index=10,
            item_id="INV-042",
            recorded_amount=5000.0,
            audited_amount=4200.0,
            misstatement=800.0,
            tainting=0.16,
        )
        assert err.misstatement == 800.0
        assert err.tainting == 0.16

    def test_evaluation_response_pass(self):
        resp = SamplingEvaluationResponse(
            method="mus",
            confidence_level=0.95,
            tolerable_misstatement=50000.0,
            expected_misstatement=0.0,
            population_value=5000000.0,
            sample_size=300,
            sample_value=4500000.0,
            errors_found=0,
            total_misstatement=0.0,
            projected_misstatement=0.0,
            basic_precision=30000.0,
            incremental_allowance=0.0,
            upper_error_limit=30000.0,
            conclusion="pass",
            conclusion_detail="UEL $30,000.00 is within tolerable misstatement $50,000.00",
            errors=[],
            taintings_ranked=[],
        )
        assert resp.conclusion == "pass"
        assert resp.errors_found == 0
        assert resp.upper_error_limit == 30000.0

    def test_evaluation_response_fail(self):
        resp = SamplingEvaluationResponse(
            method="mus",
            confidence_level=0.95,
            tolerable_misstatement=50000.0,
            expected_misstatement=0.0,
            population_value=5000000.0,
            sample_size=300,
            sample_value=4500000.0,
            errors_found=3,
            total_misstatement=15000.0,
            projected_misstatement=25000.0,
            basic_precision=30000.0,
            incremental_allowance=8000.0,
            upper_error_limit=63000.0,
            conclusion="fail",
            conclusion_detail="UEL $63,000.00 exceeds tolerable misstatement $50,000.00",
            errors=[
                SamplingErrorResponse(
                    row_index=10, item_id="INV-042",
                    recorded_amount=5000.0, audited_amount=4200.0,
                    misstatement=800.0, tainting=0.16,
                ),
            ],
            taintings_ranked=[0.16],
        )
        assert resp.conclusion == "fail"
        assert resp.errors_found == 3
        assert len(resp.errors) == 1


# =============================================================================
# Export Schemas
# =============================================================================

class TestExportSchemas:
    def test_design_memo_input_defaults(self):
        inp = SamplingDesignMemoInput()
        assert inp.method == "mus"
        assert inp.confidence_level == 0.95
        assert inp.filename == "sampling_design"

    def test_design_memo_input_full(self):
        inp = SamplingDesignMemoInput(
            method="random",
            confidence_level=0.90,
            confidence_factor=2.31,
            tolerable_misstatement=25000.0,
            population_size=500,
            population_value=1000000.0,
            actual_sample_size=50,
            strata_summary=[
                {"stratum": "High Value", "count": 3, "sample_size": 3},
            ],
            client_name="Test Corp",
            prepared_by="Auditor A",
        )
        assert inp.method == "random"
        assert inp.client_name == "Test Corp"
        assert len(inp.strata_summary) == 1

    def test_evaluation_memo_input_defaults(self):
        inp = SamplingEvaluationMemoInput()
        assert inp.conclusion == ""
        assert inp.errors == []
        assert inp.design_result is None

    def test_evaluation_memo_input_with_design(self):
        inp = SamplingEvaluationMemoInput(
            method="mus",
            conclusion="pass",
            conclusion_detail="UEL within tolerance",
            errors_found=0,
            upper_error_limit=30000.0,
            tolerable_misstatement=50000.0,
            design_result={
                "population_size": 1000,
                "actual_sample_size": 300,
            },
        )
        assert inp.conclusion == "pass"
        assert inp.design_result is not None

    def test_selection_csv_input(self):
        inp = SamplingSelectionCSVInput(
            selected_items=[
                {"row_index": 1, "item_id": "A-001", "recorded_amount": 5000},
            ],
            method="mus",
            population_size=1000,
            population_value=5000000.0,
        )
        assert len(inp.selected_items) == 1
        assert inp.method == "mus"
        assert inp.filename == "sampling_selection"


# =============================================================================
# Memo Generator
# =============================================================================

class TestMemoGenerator:
    def test_design_memo_generates_pdf(self):
        from sampling_memo_generator import generate_sampling_design_memo
        result = generate_sampling_design_memo(
            design_result={
                "method": "mus",
                "confidence_level": 0.95,
                "confidence_factor": 3.0,
                "tolerable_misstatement": 50000.0,
                "expected_misstatement": 0.0,
                "population_size": 1000,
                "population_value": 5000000.0,
                "sampling_interval": 16666.67,
                "calculated_sample_size": 300,
                "actual_sample_size": 300,
                "high_value_count": 0,
                "high_value_total": 0.0,
                "remainder_count": 1000,
                "remainder_sample_size": 300,
                "strata_summary": [],
            },
            filename="test_design",
        )
        assert isinstance(result, bytes)
        assert len(result) > 100
        assert result[:5] == b"%PDF-"

    def test_design_memo_with_strata(self):
        from sampling_memo_generator import generate_sampling_design_memo
        result = generate_sampling_design_memo(
            design_result={
                "method": "mus",
                "confidence_level": 0.95,
                "confidence_factor": 3.0,
                "tolerable_misstatement": 50000.0,
                "expected_misstatement": 0.0,
                "population_size": 1000,
                "population_value": 5000000.0,
                "sampling_interval": 16666.67,
                "calculated_sample_size": 300,
                "actual_sample_size": 305,
                "high_value_count": 5,
                "high_value_total": 750000.0,
                "remainder_count": 995,
                "remainder_sample_size": 300,
                "strata_summary": [
                    {"stratum": "High Value", "threshold": ">= $100,000", "count": 5, "total_value": 750000, "sample_size": 5},
                    {"stratum": "Remainder", "threshold": "< $100,000", "count": 995, "total_value": 4250000, "sample_size": 300},
                ],
            },
            filename="test_strata",
            client_name="Test Corp",
            prepared_by="Auditor",
        )
        assert result[:5] == b"%PDF-"

    def test_evaluation_memo_generates_pdf(self):
        from sampling_memo_generator import generate_sampling_evaluation_memo
        result = generate_sampling_evaluation_memo(
            evaluation_result={
                "method": "mus",
                "confidence_level": 0.95,
                "tolerable_misstatement": 50000.0,
                "expected_misstatement": 0.0,
                "population_value": 5000000.0,
                "sample_size": 300,
                "sample_value": 4500000.0,
                "errors_found": 1,
                "total_misstatement": 800.0,
                "projected_misstatement": 2666.67,
                "basic_precision": 30000.0,
                "incremental_allowance": 1200.0,
                "upper_error_limit": 33866.67,
                "conclusion": "pass",
                "conclusion_detail": "UEL within tolerance",
                "errors": [
                    {"row_index": 10, "item_id": "INV-042", "recorded_amount": 5000, "audited_amount": 4200, "misstatement": 800, "tainting": 0.16},
                ],
                "taintings_ranked": [0.16],
            },
            filename="test_eval",
        )
        assert isinstance(result, bytes)
        assert result[:5] == b"%PDF-"

    def test_evaluation_memo_fail_conclusion(self):
        from sampling_memo_generator import generate_sampling_evaluation_memo
        result = generate_sampling_evaluation_memo(
            evaluation_result={
                "method": "mus",
                "confidence_level": 0.95,
                "tolerable_misstatement": 50000.0,
                "expected_misstatement": 0.0,
                "population_value": 5000000.0,
                "sample_size": 300,
                "sample_value": 4500000.0,
                "errors_found": 5,
                "total_misstatement": 25000.0,
                "projected_misstatement": 40000.0,
                "basic_precision": 30000.0,
                "incremental_allowance": 10000.0,
                "upper_error_limit": 80000.0,
                "conclusion": "fail",
                "conclusion_detail": "UEL exceeds tolerable misstatement",
                "errors": [],
                "taintings_ranked": [],
            },
            filename="test_fail",
        )
        assert result[:5] == b"%PDF-"

    def test_evaluation_memo_with_design_context(self):
        from sampling_memo_generator import generate_sampling_evaluation_memo
        result = generate_sampling_evaluation_memo(
            evaluation_result={
                "method": "mus",
                "confidence_level": 0.95,
                "tolerable_misstatement": 50000.0,
                "expected_misstatement": 0.0,
                "population_value": 5000000.0,
                "sample_size": 300,
                "sample_value": 4500000.0,
                "errors_found": 0,
                "total_misstatement": 0.0,
                "projected_misstatement": 0.0,
                "basic_precision": 30000.0,
                "incremental_allowance": 0.0,
                "upper_error_limit": 30000.0,
                "conclusion": "pass",
                "conclusion_detail": "UEL within tolerance",
                "errors": [],
                "taintings_ranked": [],
            },
            design_result={
                "population_size": 1000,
                "actual_sample_size": 300,
                "method": "mus",
                "sampling_interval": 16666.67,
            },
            filename="test_combined",
        )
        assert result[:5] == b"%PDF-"


# =============================================================================
# ToolName Enum
# =============================================================================

class TestToolNameEnum:
    def test_statistical_sampling_in_toolname(self):
        from engagement_model import ToolName
        assert ToolName.STATISTICAL_SAMPLING.value == "statistical_sampling"
