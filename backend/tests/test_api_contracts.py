"""
API Contract Tests — Sprint 222
Phase XXIX: API Integration Hardening

Validates that Pydantic response models have the expected field structure,
types, and Literal values. These tests catch type drift between backend
models and frontend expectations WITHOUT making HTTP requests.

Strategy: Test model schemas directly via model_fields and model_json_schema.
"""
from typing import get_args, get_origin

import pytest

from routes.engagements import (
    EngagementListResponse,
    EngagementResponse,
    MaterialityResponse,
    WorkpaperDocumentResponse,
    WorkpaperIndexResponse,
)
from routes.follow_up_items import (
    FollowUpItemListResponse,
    FollowUpItemResponse,
    FollowUpSummaryResponse,
)
from routes.settings import MaterialityPreviewResponse
from shared.diagnostic_response_schemas import (
    AccountMovementResponse,
    AdjustedTrialBalanceResponse,
    AdjustingEntryResponse,
    BalanceSheetValidationResponse,
    BudgetVarianceResponse,
    FluxAnalysisResponse,
    FluxItemResponse,
    MovementSummaryResponse,
    PeriodComparisonResponse,
    ReconScoreResponse,
    ThreeWayMovementSummaryResponse,
    TrialBalanceResponse,
)
from shared.testing_response_schemas import (
    APTestingResponse,
    APTestResultResponse,
    ARAgingResponse,
    ARTestResultResponse,
    BankRecResponse,
    BenfordAnalysisResponse,
    CompositeScoreResponse,
    DataQualityResponse,
    FATestingResponse,
    FATestResultResponse,
    InvTestingResponse,
    InvTestResultResponse,
    JETestingResponse,
    JETestResultResponse,
    PayrollTestingResponse,
    PayrollTestResultResponse,
    RevenueTestingResponse,
    RevenueTestResultResponse,
    ThreeWayMatchItemResponse,
    ThreeWayMatchResponse,
)

# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════

def get_field_names(model_cls) -> set:
    """Get all field names from a Pydantic model."""
    return set(model_cls.model_fields.keys())


def get_literal_values(model_cls, field_name: str) -> tuple:
    """Extract Literal values from a model field annotation."""
    annotation = model_cls.model_fields[field_name].annotation
    # Unwrap Optional[Literal[...]]
    origin = get_origin(annotation)
    if origin is type(None):
        return ()
    # Handle Optional (Union with None)
    args = get_args(annotation)
    for arg in args if args else [annotation]:
        inner_args = get_args(arg)
        if inner_args and all(isinstance(a, str) for a in inner_args):
            return inner_args
    return get_args(annotation)


# ═══════════════════════════════════════════════════════════════
# Testing Tool Response Models
# ═══════════════════════════════════════════════════════════════

class TestTestingToolContracts:
    """Validate testing tool response models have expected structure."""

    @pytest.mark.parametrize("model_cls,expected_fields", [
        (JETestingResponse, {"composite_score", "test_results", "data_quality"}),
        (APTestingResponse, {"composite_score", "test_results", "data_quality"}),
        (PayrollTestingResponse, {"composite_score", "test_results", "data_quality"}),
        (RevenueTestingResponse, {"composite_score", "test_results", "data_quality"}),
        (FATestingResponse, {"composite_score", "test_results", "data_quality"}),
        (InvTestingResponse, {"composite_score", "test_results", "data_quality"}),
    ])
    def test_standard_testing_response_fields(self, model_cls, expected_fields):
        """All standard testing tools must have composite_score, test_results, data_quality."""
        fields = get_field_names(model_cls)
        for field in expected_fields:
            assert field in fields, f"{model_cls.__name__} missing required field '{field}'"

    def test_je_testing_has_benford_and_sampling(self):
        """JE Testing uniquely has benford_result and sampling_result."""
        fields = get_field_names(JETestingResponse)
        assert "benford_result" in fields
        assert "sampling_result" in fields

    def test_ar_aging_has_ar_summary(self):
        """AR Aging uniquely has ar_summary and dual column detection."""
        fields = get_field_names(ARAgingResponse)
        assert "ar_summary" in fields
        assert "tb_column_detection" in fields
        assert "sl_column_detection" in fields

    def test_bank_rec_has_summary_and_column_detection(self):
        """Bank Rec has summary and dual column detection."""
        fields = get_field_names(BankRecResponse)
        assert "summary" in fields
        assert "bank_column_detection" in fields
        assert "ledger_column_detection" in fields

    def test_three_way_match_has_match_lists(self):
        """Three-Way Match has full_matches, partial_matches, unmatched lists."""
        fields = get_field_names(ThreeWayMatchResponse)
        assert "full_matches" in fields
        assert "partial_matches" in fields
        assert "unmatched_pos" in fields
        assert "unmatched_invoices" in fields
        assert "unmatched_receipts" in fields
        assert "summary" in fields
        assert "variances" in fields
        assert "config" in fields


class TestCompositeScoreContract:
    """Validate composite score models."""

    def test_shared_composite_score_fields(self):
        fields = get_field_names(CompositeScoreResponse)
        assert "score" in fields
        assert "risk_tier" in fields
        assert "tests_run" in fields
        assert "total_entries" in fields

    def test_risk_tier_literal_values(self):
        values = get_literal_values(CompositeScoreResponse, "risk_tier")
        expected = {"low", "elevated", "moderate", "high", "critical"}
        assert set(values) == expected, f"risk_tier values {values} != {expected}"


class TestDataQualityContract:
    """Validate data quality model."""

    def test_data_quality_fields(self):
        fields = get_field_names(DataQualityResponse)
        assert "total_rows" in fields
        assert "completeness_score" in fields
        assert "detected_issues" in fields


class TestBenfordAnalysisContract:
    """Validate Benford analysis model."""

    def test_benford_has_required_fields(self):
        fields = get_field_names(BenfordAnalysisResponse)
        for required in ("mad", "chi_squared", "conformity_level", "expected_distribution", "actual_distribution"):
            assert required in fields, f"BenfordAnalysisResponse missing '{required}'"


class TestTestResultContracts:
    """Validate test result models have consistent structure."""

    @pytest.mark.parametrize("model_cls", [
        JETestResultResponse,
        APTestResultResponse,
        ARTestResultResponse,
        PayrollTestResultResponse,
        RevenueTestResultResponse,
        FATestResultResponse,
        InvTestResultResponse,
    ])
    def test_test_result_has_core_fields(self, model_cls):
        """All test result models must have test_name, test_key, test_tier, entries_flagged."""
        fields = get_field_names(model_cls)
        assert "test_name" in fields, f"{model_cls.__name__} missing 'test_name'"
        assert "test_key" in fields, f"{model_cls.__name__} missing 'test_key'"
        assert "test_tier" in fields, f"{model_cls.__name__} missing 'test_tier'"
        assert "entries_flagged" in fields, f"{model_cls.__name__} missing 'entries_flagged'"
        assert "severity" in fields, f"{model_cls.__name__} missing 'severity'"

    @pytest.mark.parametrize("model_cls", [
        JETestResultResponse,
        APTestResultResponse,
        ARTestResultResponse,
        PayrollTestResultResponse,
        FATestResultResponse,
        InvTestResultResponse,
    ])
    def test_test_tier_literal_values(self, model_cls):
        """Test tier must be structural, statistical, or advanced."""
        values = get_literal_values(model_cls, "test_tier")
        expected = {"structural", "statistical", "advanced"}
        assert set(values) == expected, f"{model_cls.__name__}.test_tier values {values} != {expected}"

    def test_revenue_test_tier_includes_contract(self):
        """Revenue test tier includes 'contract' for ASC 606 / IFRS 15 tests."""
        values = get_literal_values(RevenueTestResultResponse, "test_tier")
        expected = {"structural", "statistical", "advanced", "contract"}
        assert set(values) == expected, f"RevenueTestResultResponse.test_tier values {values} != {expected}"


# ═══════════════════════════════════════════════════════════════
# Diagnostic Tool Response Models
# ═══════════════════════════════════════════════════════════════

class TestDiagnosticContracts:
    """Validate diagnostic tool response models."""

    def test_trial_balance_core_fields(self):
        fields = get_field_names(TrialBalanceResponse)
        for required in (
            "status", "balanced", "total_debits", "total_credits",
            "difference", "row_count", "timestamp", "message",
            "abnormal_balances", "materiality_threshold",
            "risk_summary", "classification_quality", "balance_sheet_validation",
        ):
            assert required in fields, f"TrialBalanceResponse missing '{required}'"

    def test_flux_analysis_has_flux_and_recon(self):
        fields = get_field_names(FluxAnalysisResponse)
        assert "flux" in fields
        assert "recon" in fields

    def test_period_comparison_has_variance_lists(self):
        fields = get_field_names(PeriodComparisonResponse)
        assert "balance_sheet_variances" in fields
        assert "income_statement_variances" in fields
        assert "ratio_variances" in fields
        assert "diagnostic_variances" in fields

    def test_movement_summary_has_movement_data(self):
        fields = get_field_names(MovementSummaryResponse)
        assert "prior_label" in fields
        assert "current_label" in fields
        assert "all_movements" in fields
        assert "lead_sheet_summaries" in fields
        assert "significant_movements" in fields
        assert "new_accounts" in fields
        assert "closed_accounts" in fields

    def test_three_way_movement_summary_fields(self):
        fields = get_field_names(ThreeWayMovementSummaryResponse)
        assert "prior_label" in fields
        assert "current_label" in fields
        assert "budget_label" in fields

    def test_adjusting_entry_has_status_literal(self):
        values = get_literal_values(AdjustingEntryResponse, "status")
        expected = {"proposed", "approved", "rejected", "posted"}
        assert set(values) == expected

    def test_adjusting_entry_has_type_literal(self):
        values = get_literal_values(AdjustingEntryResponse, "adjustment_type")
        expected = {"accrual", "deferral", "estimate", "error_correction", "reclassification", "other"}
        assert set(values) == expected


class TestFluxLiteralContracts:
    """Validate Literal values in flux/recon models."""

    def test_flux_item_risk_level(self):
        values = get_literal_values(FluxItemResponse, "risk_level")
        expected = {"high", "medium", "low", "none"}
        assert set(values) == expected

    def test_recon_score_band(self):
        values = get_literal_values(ReconScoreResponse, "band")
        expected = {"high", "medium", "low"}
        assert set(values) == expected

    def test_balance_sheet_validation_status(self):
        values = get_literal_values(BalanceSheetValidationResponse, "status")
        expected = {"balanced", "minor_imbalance", "moderate_imbalance", "significant_imbalance"}
        assert set(values) == expected


class TestMovementLiteralContracts:
    """Validate Literal values in movement models."""

    def test_account_movement_type(self):
        values = get_literal_values(AccountMovementResponse, "movement_type")
        expected = {"new_account", "closed_account", "sign_change", "increase", "decrease", "unchanged"}
        assert set(values) == expected

    def test_account_movement_significance(self):
        values = get_literal_values(AccountMovementResponse, "significance")
        expected = {"material", "significant", "minor"}
        assert set(values) == expected

    def test_budget_variance_significance(self):
        values = get_literal_values(BudgetVarianceResponse, "variance_significance")
        expected = {"material", "significant", "minor"}
        assert set(values) == expected


# ═══════════════════════════════════════════════════════════════
# Engagement + Follow-Up Models
# ═══════════════════════════════════════════════════════════════

class TestEngagementContracts:
    """Validate engagement response models."""

    def test_engagement_response_fields(self):
        fields = get_field_names(EngagementResponse)
        for required in (
            "id", "client_id", "period_start", "period_end", "status",
            "materiality_basis", "performance_materiality_factor",
            "trivial_threshold_factor", "created_by", "created_at",
        ):
            assert required in fields, f"EngagementResponse missing '{required}'"

    def test_engagement_status_literal(self):
        values = get_literal_values(EngagementResponse, "status")
        assert set(values) == {"active", "archived"}

    def test_engagement_materiality_basis_literal(self):
        values = get_literal_values(EngagementResponse, "materiality_basis")
        assert set(values) == {"revenue", "assets", "manual"}

    def test_engagement_list_response_fields(self):
        fields = get_field_names(EngagementListResponse)
        assert "engagements" in fields
        assert "total_count" in fields
        assert "page" in fields
        assert "page_size" in fields

    def test_workpaper_index_fields(self):
        fields = get_field_names(WorkpaperIndexResponse)
        assert "engagement_id" in fields
        assert "document_register" in fields
        assert "follow_up_summary" in fields
        assert "sign_off" in fields

    def test_workpaper_document_status_literal(self):
        values = get_literal_values(WorkpaperDocumentResponse, "status")
        assert set(values) == {"completed", "not_started"}

    def test_materiality_response_fields(self):
        fields = get_field_names(MaterialityResponse)
        for required in (
            "overall_materiality", "performance_materiality",
            "trivial_threshold", "performance_materiality_factor",
        ):
            assert required in fields


class TestFollowUpContracts:
    """Validate follow-up item response models."""

    def test_follow_up_item_fields(self):
        fields = get_field_names(FollowUpItemResponse)
        for required in (
            "id", "engagement_id", "description", "tool_source",
            "severity", "disposition", "created_at", "updated_at",
        ):
            assert required in fields, f"FollowUpItemResponse missing '{required}'"

    def test_follow_up_severity_literal(self):
        values = get_literal_values(FollowUpItemResponse, "severity")
        assert set(values) == {"high", "medium", "low"}

    def test_follow_up_disposition_literal(self):
        values = get_literal_values(FollowUpItemResponse, "disposition")
        expected = {
            "not_reviewed",
            "investigated_no_issue",
            "investigated_adjustment_posted",
            "investigated_further_review",
            "immaterial",
        }
        assert set(values) == expected

    def test_follow_up_list_response_fields(self):
        fields = get_field_names(FollowUpItemListResponse)
        assert "items" in fields
        assert "total_count" in fields
        assert "page" in fields

    def test_follow_up_summary_fields(self):
        fields = get_field_names(FollowUpSummaryResponse)
        assert "total_count" in fields
        assert "by_severity" in fields
        assert "by_disposition" in fields


# ═══════════════════════════════════════════════════════════════
# Settings Response Models
# ═══════════════════════════════════════════════════════════════

class TestSettingsContracts:
    """Validate settings response models."""

    def test_materiality_preview_fields(self):
        fields = get_field_names(MaterialityPreviewResponse)
        assert "threshold" in fields
        assert "formula_display" in fields
        assert "explanation" in fields
        assert "formula" in fields


# ═══════════════════════════════════════════════════════════════
# Three-Way Match Literal Contracts
# ═══════════════════════════════════════════════════════════════

class TestThreeWayMatchLiterals:
    """Validate Three-Way Match Literal values."""

    def test_match_item_match_type(self):
        values = get_literal_values(ThreeWayMatchItemResponse, "match_type")
        expected = {"exact_po", "fuzzy", "partial"}
        assert set(values) == expected


# ═══════════════════════════════════════════════════════════════
# Schema Generation Smoke Tests
# ═══════════════════════════════════════════════════════════════

class TestSchemaGeneration:
    """Ensure all response models can generate valid JSON schemas."""

    @pytest.mark.parametrize("model_cls", [
        # Diagnostic
        TrialBalanceResponse,
        FluxAnalysisResponse,
        PeriodComparisonResponse,
        MovementSummaryResponse,
        ThreeWayMovementSummaryResponse,
        AdjustingEntryResponse,
        AdjustedTrialBalanceResponse,
        # Testing
        JETestingResponse,
        APTestingResponse,
        BankRecResponse,
        ThreeWayMatchResponse,
        ARAgingResponse,
        PayrollTestingResponse,
        RevenueTestingResponse,
        FATestingResponse,
        InvTestingResponse,
        # Engagement
        EngagementResponse,
        WorkpaperIndexResponse,
        FollowUpItemResponse,
    ])
    def test_model_generates_json_schema(self, model_cls):
        """Every response model must produce a valid JSON schema for OpenAPI."""
        schema = model_cls.model_json_schema()
        assert "properties" in schema, f"{model_cls.__name__} schema has no properties"
        assert "title" in schema, f"{model_cls.__name__} schema has no title"
        assert len(schema["properties"]) > 0, f"{model_cls.__name__} schema has empty properties"
