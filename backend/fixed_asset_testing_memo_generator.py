"""
Fixed Asset Testing Memo PDF Generator (Sprint 115, simplified Sprint 157)

Config-driven wrapper around shared memo template.
Domain: IAS 16 / ISA 500 / ISA 540 / PCAOB AS 2501.
"""

from typing import Any, Optional

from shared.memo_template import TestingMemoConfig, generate_testing_memo

FA_TEST_DESCRIPTIONS = {
    "fully_depreciated": "Flags assets where accumulated depreciation equals or exceeds cost (NBV zero or negative), indicating potential ghost assets or items requiring disposal review.",
    "missing_fields": "Flags fixed asset entries missing critical register fields (cost, identifier, acquisition date), a data completeness anomaly indicator.",
    "negative_values": "Flags assets with negative cost or negative accumulated depreciation, indicating data entry errors or improper adjustments.",
    "over_depreciation": "Flags assets where accumulated depreciation exceeds original cost by more than 1%, indicating possible calculation errors or improper depreciation entries.",
    "useful_life_outliers": "Flags assets with useful life estimates outside reasonable bounds (below 0.5 years or above 50 years), an estimation anomaly indicator per ISA 540.",
    "cost_zscore_outliers": "Uses z-score analysis to identify statistically unusual asset costs relative to the population mean.",
    "age_concentration": "Flags disproportionate concentration of total asset cost in a single acquisition year, indicating potential bulk capitalization anomalies.",
    "duplicate_assets": "Flags assets with identical cost, description, and acquisition date — potential duplicate capitalization or double-counting.",
    "residual_value_anomalies": "Flags assets with residual values exceeding 30% of cost or negative residual values, an estimation anomaly indicator.",
}

_FA_CONFIG = TestingMemoConfig(
    title="Fixed Asset Register Analysis Memo",
    ref_prefix="FAT",
    entry_label="Total Fixed Assets Tested",
    flagged_label="Total Fixed Assets Flagged",
    log_prefix="fa_memo",
    domain="fixed asset register analysis",
    test_descriptions=FA_TEST_DESCRIPTIONS,
    methodology_intro=(
        "The following automated tests were applied to the fixed asset register "
        "in accordance with professional auditing standards "
        "(IAS 16: Property, Plant and Equipment, "
        "ISA 500: Audit Evidence, ISA 540: Auditing Accounting Estimates \u2014 "
        "depreciation methods, useful life, and residual value estimation, "
        "PCAOB AS 2501: Auditing Accounting Estimates). "
        "Results represent fixed asset anomaly indicators, not depreciation adequacy conclusions:"
    ),
    isa_reference="ISA 500 (Audit Evidence) and ISA 540 (Auditing Accounting Estimates)",
    tool_domain="fixed_asset_testing",
    risk_assessments={
        "low": (
            "Based on the automated fixed asset register analysis procedures applied, "
            "the PP&E data exhibits a LOW risk profile. "
            "No material fixed asset anomaly indicators requiring further investigation were identified."
        ),
        "elevated": (
            "Based on the automated fixed asset register analysis procedures applied, "
            "the PP&E data exhibits an ELEVATED risk profile. "
            "Select flagged assets should be reviewed for proper capitalization treatment "
            "and supporting documentation."
        ),
        "moderate": (
            "Based on the automated fixed asset register analysis procedures applied, "
            "the PP&E data exhibits a MODERATE risk profile. "
            "Flagged assets warrant focused review as PP&E anomaly indicators, "
            "particularly depreciation estimates and useful life assumptions."
        ),
        "high": (
            "Based on the automated fixed asset register analysis procedures applied, "
            "the PP&E data exhibits a HIGH risk profile. "
            "Significant fixed asset anomaly indicators were identified that require "
            "detailed investigation and may warrant expanded PP&E audit procedures "
            "per ISA 540 and PCAOB AS 2501."
        ),
    },
)


def generate_fixed_asset_testing_memo(
    fa_result: dict[str, Any],
    filename: str = "fixed_asset_testing",
    client_name: Optional[str] = None,
    period_tested: Optional[str] = None,
    prepared_by: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    workpaper_date: Optional[str] = None,
    source_document_title: Optional[str] = None,
    source_context_note: Optional[str] = None,
) -> bytes:
    """Generate a PDF testing memo for fixed asset testing results."""
    return generate_testing_memo(
        fa_result,
        _FA_CONFIG,
        filename=filename,
        client_name=client_name,
        period_tested=period_tested,
        prepared_by=prepared_by,
        reviewed_by=reviewed_by,
        workpaper_date=workpaper_date,
        source_document_title=source_document_title,
        source_context_note=source_context_note,
    )
