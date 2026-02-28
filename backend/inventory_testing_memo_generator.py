"""
Inventory Testing Memo PDF Generator (Sprint 118, simplified Sprint 157)

Config-driven wrapper around shared memo template.
Domain: IAS 2 / ISA 501 / ISA 540 / PCAOB AS 2501.
"""

from typing import Any, Optional

from shared.memo_template import TestingMemoConfig, generate_testing_memo

INV_TEST_DESCRIPTIONS = {
    "missing_fields": "Flags inventory entries missing critical register fields (identifier, quantity, cost or value), a data completeness anomaly indicator per ISA 500.",
    "negative_values": "Flags items with negative quantity, unit cost, or extended value, indicating data entry errors, returns, or adjustments requiring review.",
    "value_mismatch": "Flags items where quantity times unit cost differs from extended value by more than the tolerance threshold, indicating calculation or data integrity anomalies.",
    "unit_cost_outliers": "Uses z-score analysis to identify statistically unusual unit costs relative to the population mean, an anomaly indicator for pricing data integrity.",
    "quantity_outliers": "Uses z-score analysis to identify statistically unusual quantities relative to the population mean, an anomaly indicator for potential count errors or obsolete stock.",
    "slow_moving": "Flags items with no movement activity beyond the configured threshold period, an obsolescence anomaly indicator per ISA 540 (not an NRV determination).",
    "category_concentration": "Flags disproportionate concentration of total inventory value in a single category, indicating potential valuation or diversification anomalies.",
    "duplicate_items": "Flags items with identical description and unit cost, indicating potential double-counting or duplicate record anomalies.",
    "zero_value_items": "Flags items with quantity on hand but zero value, indicating potential write-down anomalies or pricing data gaps (not an NRV conclusion).",
}

INV_TEST_PARAMETERS = {
    "missing_fields": "Required: ID, quantity, cost/value",
    "negative_values": "Qty, unit cost, or value < 0",
    "value_mismatch": "Qty \u00d7 unit cost \u2260 extended value",
    "unit_cost_outliers": "Z-score > 3.0",
    "quantity_outliers": "Z-score > 3.0",
    "slow_moving": "No movement in period",
    "category_concentration": "> 60% in single category",
    "duplicate_items": "Match: description + unit cost",
    "zero_value_items": "Qty > 0 and value = 0",
}

INV_TEST_ASSERTIONS = {
    "missing_fields": ["completeness"],
    "negative_values": ["accuracy"],
    "value_mismatch": ["accuracy", "valuation"],
    "unit_cost_outliers": ["valuation"],
    "quantity_outliers": ["existence"],
    "slow_moving": ["valuation"],
    "category_concentration": ["valuation"],
    "duplicate_items": ["existence"],
    "zero_value_items": ["valuation"],
}

_INV_CONFIG = TestingMemoConfig(
    title="Inventory Register Analysis Memo",
    ref_prefix="INV",
    entry_label="Total Inventory Items Tested",
    flagged_label="Total Inventory Items Flagged",
    log_prefix="inv_memo",
    domain="inventory register analysis",
    test_descriptions=INV_TEST_DESCRIPTIONS,
    test_parameters=INV_TEST_PARAMETERS,
    test_assertions=INV_TEST_ASSERTIONS,
    methodology_intro=(
        "The following automated tests were applied to the inventory register "
        "in accordance with professional auditing standards "
        "(IAS 2: Inventories, "
        "ISA 501: Audit Evidence \u2014 Specific Considerations for Selected Items, "
        "ISA 500: Audit Evidence, ISA 540: Auditing Accounting Estimates \u2014 "
        "NRV estimation and obsolescence indicators, "
        "PCAOB AS 2501: Auditing Accounting Estimates). "
        "Results represent inventory anomaly indicators, not NRV adequacy conclusions:"
    ),
    isa_reference="ISA 500 (Audit Evidence) and ISA 540 (Auditing Accounting Estimates)",
    tool_domain="inventory_testing",
    risk_assessments={
        "low": (
            "Based on the automated inventory register analysis procedures applied, "
            "the inventory data exhibits a LOW risk profile. "
            "No material inventory anomaly indicators requiring further investigation were identified."
        ),
        "elevated": (
            "Based on the automated inventory register analysis procedures applied, "
            "the inventory data exhibits an ELEVATED risk profile. "
            "Select flagged items should be reviewed for proper valuation treatment "
            "and supporting documentation."
        ),
        "moderate": (
            "Based on the automated inventory register analysis procedures applied, "
            "the inventory data exhibits a MODERATE risk profile. "
            "Flagged items warrant focused review as inventory anomaly indicators, "
            "particularly slow-moving items and unit cost outliers."
        ),
        "high": (
            "Based on the automated inventory register analysis procedures applied, "
            "the inventory data exhibits a HIGH risk profile. "
            "Significant inventory anomaly indicators were identified that may warrant "
            "detailed investigation and expanded inventory audit procedures "
            "at the engagement team's discretion per ISA 501 and PCAOB AS 2501."
        ),
    },
)


def generate_inventory_testing_memo(
    inv_result: dict[str, Any],
    filename: str = "inventory_testing",
    client_name: Optional[str] = None,
    period_tested: Optional[str] = None,
    prepared_by: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    workpaper_date: Optional[str] = None,
    source_document_title: Optional[str] = None,
    source_context_note: Optional[str] = None,
    include_signoff: bool = False,
) -> bytes:
    """Generate a PDF testing memo for inventory testing results."""
    return generate_testing_memo(
        inv_result,
        _INV_CONFIG,
        filename=filename,
        client_name=client_name,
        period_tested=period_tested,
        prepared_by=prepared_by,
        reviewed_by=reviewed_by,
        workpaper_date=workpaper_date,
        source_document_title=source_document_title,
        source_context_note=source_context_note,
        include_signoff=include_signoff,
    )
