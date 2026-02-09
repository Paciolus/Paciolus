"""
Inventory Testing Memo PDF Generator (Sprint 118)

Auto-generated testing memo per ISA 501 / ISA 540 / PCAOB AS 2501.
Renaissance Ledger aesthetic consistent with existing PDF exports.

Inventory register analysis covers inventory existence, completeness,
and valuation assertions. This memo documents automated inventory
anomaly indicators — it does NOT constitute an NRV adequacy opinion
or obsolescence determination.

Audit Standards References:
- IAS 2: Inventories
- ASC 330: Inventory
- ISA 501: Audit Evidence — Specific Considerations for Selected Items
- ISA 540: Auditing Accounting Estimates
- ISA 500: Audit Evidence
- PCAOB AS 2501: Auditing Accounting Estimates

Sections:
1. Header (client, period, preparer)
2. Scope (items tested, data quality)
3. Methodology (tests applied with descriptions)
4. Results Summary (composite score, flags by test)
5. Findings (top flagged inventory items)
6. Conclusion (professional assessment)
"""

import io
from typing import Any, Optional

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
)

from pdf_generator import (
    LedgerRule, generate_reference_number,
)
from shared.memo_base import (
    create_memo_styles, build_memo_header, build_scope_section,
    build_methodology_section, build_results_summary_section,
    build_workpaper_signoff, build_disclaimer,
)
from security_utils import log_secure_operation


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


def generate_inventory_testing_memo(
    inv_result: dict[str, Any],
    filename: str = "inventory_testing",
    client_name: Optional[str] = None,
    period_tested: Optional[str] = None,
    prepared_by: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    workpaper_date: Optional[str] = None,
) -> bytes:
    """Generate a PDF testing memo for inventory testing results.

    Args:
        inv_result: InvTestingResult.to_dict() output
        filename: Base filename for the report
        client_name: Client/entity name
        period_tested: Period description (e.g., "FY 2025")
        prepared_by: Preparer name
        reviewed_by: Reviewer name
        workpaper_date: Date string (ISO format)

    Returns:
        PDF bytes
    """
    log_secure_operation("inv_memo_generate", f"Generating inventory testing memo: {filename}")

    styles = create_memo_styles()
    buffer = io.BytesIO()
    reference = generate_reference_number().replace("PAC-", "INV-")

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=1.0 * inch,
        bottomMargin=0.8 * inch,
    )

    story = []
    composite = inv_result.get("composite_score", {})
    test_results = inv_result.get("test_results", [])
    data_quality = inv_result.get("data_quality", {})

    # 1. HEADER
    build_memo_header(
        story, styles, doc.width,
        "Inventory Register Analysis Memo",
        reference, client_name,
    )

    # 2. SCOPE
    build_scope_section(
        story, styles, doc.width, composite, data_quality,
        entry_label="Total Inventory Items Tested",
        period_tested=period_tested,
    )

    # 3. METHODOLOGY
    build_methodology_section(
        story, styles, doc.width, test_results, INV_TEST_DESCRIPTIONS,
        "The following automated tests were applied to the inventory register "
        "in accordance with professional auditing standards "
        "(IAS 2: Inventories, "
        "ISA 501: Audit Evidence — Specific Considerations for Selected Items, "
        "ISA 500: Audit Evidence, ISA 540: Auditing Accounting Estimates — "
        "NRV estimation and obsolescence indicators, "
        "PCAOB AS 2501: Auditing Accounting Estimates). "
        "Results represent inventory anomaly indicators, not NRV adequacy conclusions:",
    )

    # 4. RESULTS SUMMARY
    build_results_summary_section(
        story, styles, doc.width, composite, test_results,
        flagged_label="Total Inventory Items Flagged",
    )

    # 5. TOP FINDINGS
    top_findings = composite.get("top_findings", [])
    if top_findings:
        story.append(Paragraph("IV. KEY FINDINGS", styles['MemoSection']))
        story.append(LedgerRule(doc.width))
        for i, finding in enumerate(top_findings[:5], 1):
            story.append(Paragraph(f"{i}. {finding}", styles['MemoBody']))
        story.append(Spacer(1, 8))

    # 6. CONCLUSION
    conclusion_num = "V" if top_findings else "IV"
    story.append(Paragraph(f"{conclusion_num}. CONCLUSION", styles['MemoSection']))
    story.append(LedgerRule(doc.width))

    score_val = composite.get("score", 0)
    if score_val < 10:
        assessment = (
            "Based on the automated inventory register analysis procedures applied, "
            "the inventory data exhibits a LOW risk profile. "
            "No material inventory anomaly indicators requiring further investigation were identified."
        )
    elif score_val < 25:
        assessment = (
            "Based on the automated inventory register analysis procedures applied, "
            "the inventory data exhibits an ELEVATED risk profile. "
            "Select flagged items should be reviewed for proper valuation treatment "
            "and supporting documentation."
        )
    elif score_val < 50:
        assessment = (
            "Based on the automated inventory register analysis procedures applied, "
            "the inventory data exhibits a MODERATE risk profile. "
            "Flagged items warrant focused review as inventory anomaly indicators, "
            "particularly slow-moving items and unit cost outliers."
        )
    else:
        assessment = (
            "Based on the automated inventory register analysis procedures applied, "
            "the inventory data exhibits a HIGH risk profile. "
            "Significant inventory anomaly indicators were identified that require "
            "detailed investigation and may warrant expanded inventory audit procedures "
            "per ISA 501 and PCAOB AS 2501."
        )

    story.append(Paragraph(assessment, styles['MemoBody']))
    story.append(Spacer(1, 12))

    # WORKPAPER SIGN-OFF
    build_workpaper_signoff(story, styles, doc.width, prepared_by, reviewed_by, workpaper_date)

    # DISCLAIMER
    build_disclaimer(
        story, styles,
        domain="inventory register analysis",
        isa_reference="ISA 500 (Audit Evidence) and ISA 540 (Auditing Accounting Estimates)",
    )

    # Build PDF
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    log_secure_operation("inv_memo_complete", f"Inventory memo generated: {len(pdf_bytes)} bytes")
    return pdf_bytes
