"""
Inventory Testing Memo PDF Generator (Sprint 118, simplified Sprint 157)

Config-driven wrapper around shared memo template.
Domain: IAS 2 / ISA 501 / ISA 540 / PCAOB AS 2501.

CONTENT-08: Duration Breakdown (slow-moving age buckets) and
Inventory Turnover note via build_extra_sections callback.
"""

from typing import Any, Optional

from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from pdf_generator import ClassicalColors, LedgerRule
from shared.memo_template import TestingMemoConfig, _roman, generate_testing_memo

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

_INV_CONFIG = TestingMemoConfig(
    title="Inventory Register Analysis Memo",
    ref_prefix="INV",
    entry_label="Total Inventory Items Tested",
    flagged_label="Total Inventory Items Flagged",
    log_prefix="inv_memo",
    domain="inventory register analysis",
    test_descriptions=INV_TEST_DESCRIPTIONS,
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
            "Significant inventory anomaly indicators were identified that require "
            "detailed investigation and may warrant expanded inventory audit procedures "
            "per ISA 501 and PCAOB AS 2501."
        ),
    },
)


# =============================================================================
# CONTENT-08: Duration Breakdown & Inventory Turnover Note
# =============================================================================

_AGE_BUCKETS = [
    ("180\u2013365 days", 180, 365),
    ("365\u2013730 days", 365, 730),
    ("730+ days", 730, None),
]


def _build_inventory_extra_sections(
    story: list,
    styles: dict,
    doc_width: float,
    result: dict[str, Any],
    section_counter: int,
) -> int:
    """Build inventory-specific extra sections: Duration Breakdown and Turnover note.

    Returns the updated section_counter.
    """
    test_results = result.get("test_results", [])

    # Find the slow_moving test result to extract flagged entries
    slow_moving_flagged: list[dict] = []
    for tr in test_results:
        if tr.get("test_key") == "slow_moving":
            slow_moving_flagged = tr.get("flagged_entries", [])
            break

    has_duration = len(slow_moving_flagged) > 0

    if has_duration:
        # Group slow-moving items by age bucket
        buckets: dict[str, list[dict]] = {label: [] for label, _, _ in _AGE_BUCKETS}
        for fe in slow_moving_flagged:
            details = fe.get("details") or {}
            days = details.get("days_since_movement", 0)
            value = details.get("value", 0)
            entry = fe.get("entry", {})
            item_id = entry.get("item_id", "") or entry.get("description", "") or ""

            for label, low, high in _AGE_BUCKETS:
                if high is not None:
                    if low < days <= high:
                        buckets[label].append({"item": item_id, "days": days, "value": value})
                        break
                else:
                    if days > low:
                        buckets[label].append({"item": item_id, "days": days, "value": value})
                        break

        # Only render if at least one bucket has items
        non_empty_buckets = {k: v for k, v in buckets.items() if v}
        if non_empty_buckets:
            section_label = _roman(section_counter)
            story.append(Paragraph(f"{section_label}. Slow-Moving Inventory Duration Breakdown", styles["MemoSection"]))
            story.append(LedgerRule(doc_width))
            story.append(
                Paragraph(
                    "The following table groups slow-moving inventory items by the duration "
                    "since their last recorded movement, providing an age-based risk stratification "
                    "for obsolescence assessment per ISA 540.",
                    styles["MemoBody"],
                )
            )
            story.append(Spacer(1, 6))

            headers = ["Age Bucket", "Items", "Total Value"]
            col_widths = [2.5 * inch, 1.5 * inch, 2.7 * inch]
            data: list[list] = [headers]

            for label, _, _ in _AGE_BUCKETS:
                items = buckets.get(label, [])
                count = len(items)
                total_value = sum(i.get("value", 0) for i in items)
                value_str = f"${total_value:,.2f}" if total_value >= 0 else f"-${abs(total_value):,.2f}"
                data.append([label, str(count), value_str])

            table = Table(data, colWidths=col_widths, repeatRows=1)
            table.setStyle(
                TableStyle(
                    [
                        ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                        ("FONTNAME", (0, 1), (-1, -1), "Times-Roman"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                        ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                        ("LINEBELOW", (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                        ("LEFTPADDING", (0, 0), (0, -1), 0),
                    ]
                )
            )
            story.append(table)
            story.append(Spacer(1, 8))
            section_counter += 1

    # Inventory Turnover Note (always rendered)
    section_label = _roman(section_counter)
    story.append(Paragraph(f"{section_label}. Inventory Turnover", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))
    story.append(
        Paragraph(
            "<b>Inventory Turnover:</b> Requires COGS input \u2014 not available from inventory register. "
            "To compute inventory turnover (COGS / Average Inventory), cost of goods sold data "
            "from the income statement must be provided separately. This analysis is limited to "
            "the inventory register data and cannot derive turnover metrics without external COGS input.",
            styles["MemoBody"],
        )
    )
    story.append(Spacer(1, 8))
    section_counter += 1

    return section_counter


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
        build_extra_sections=_build_inventory_extra_sections,
        include_signoff=include_signoff,
    )
