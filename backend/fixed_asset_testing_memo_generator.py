"""
Fixed Asset Testing Memo PDF Generator (Sprint 115)

Auto-generated testing memo per ISA 500 / ISA 540 / PCAOB AS 2501.
Renaissance Ledger aesthetic consistent with existing PDF exports.

Fixed asset register analysis covers PP&E assertions including
depreciation, useful life, and residual value estimates. This memo
documents automated fixed asset anomaly indicators — it does NOT
constitute a depreciation adequacy opinion or impairment determination.

Audit Standards References:
- IAS 16: Property, Plant and Equipment
- IAS 36: Impairment of Assets
- ASC 360: Property, Plant, and Equipment
- ISA 500: Audit Evidence
- ISA 540: Auditing Accounting Estimates
- PCAOB AS 2501: Auditing Accounting Estimates

Sections:
1. Header (client, period, preparer)
2. Scope (assets tested, data quality)
3. Methodology (tests applied with descriptions)
4. Results Summary (composite score, flags by test)
5. Findings (top flagged fixed asset items)
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


def generate_fixed_asset_testing_memo(
    fa_result: dict[str, Any],
    filename: str = "fixed_asset_testing",
    client_name: Optional[str] = None,
    period_tested: Optional[str] = None,
    prepared_by: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    workpaper_date: Optional[str] = None,
) -> bytes:
    """Generate a PDF testing memo for fixed asset testing results.

    Args:
        fa_result: FATestingResult.to_dict() output
        filename: Base filename for the report
        client_name: Client/entity name
        period_tested: Period description (e.g., "FY 2025")
        prepared_by: Preparer name
        reviewed_by: Reviewer name
        workpaper_date: Date string (ISO format)

    Returns:
        PDF bytes
    """
    log_secure_operation("fa_memo_generate", f"Generating fixed asset testing memo: {filename}")

    styles = create_memo_styles()
    buffer = io.BytesIO()
    reference = generate_reference_number().replace("PAC-", "FAT-")

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=1.0 * inch,
        bottomMargin=0.8 * inch,
    )

    story = []
    composite = fa_result.get("composite_score", {})
    test_results = fa_result.get("test_results", [])
    data_quality = fa_result.get("data_quality", {})

    # 1. HEADER
    build_memo_header(
        story, styles, doc.width,
        "Fixed Asset Register Analysis Memo",
        reference, client_name,
    )

    # 2. SCOPE
    build_scope_section(
        story, styles, doc.width, composite, data_quality,
        entry_label="Total Fixed Assets Tested",
        period_tested=period_tested,
    )

    # 3. METHODOLOGY
    build_methodology_section(
        story, styles, doc.width, test_results, FA_TEST_DESCRIPTIONS,
        "The following automated tests were applied to the fixed asset register "
        "in accordance with professional auditing standards "
        "(IAS 16: Property, Plant and Equipment, "
        "ISA 500: Audit Evidence, ISA 540: Auditing Accounting Estimates — "
        "depreciation methods, useful life, and residual value estimation, "
        "PCAOB AS 2501: Auditing Accounting Estimates). "
        "Results represent fixed asset anomaly indicators, not depreciation adequacy conclusions:",
    )

    # 4. RESULTS SUMMARY
    build_results_summary_section(
        story, styles, doc.width, composite, test_results,
        flagged_label="Total Fixed Assets Flagged",
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
            "Based on the automated fixed asset register analysis procedures applied, "
            "the PP&E data exhibits a LOW risk profile. "
            "No material fixed asset anomaly indicators requiring further investigation were identified."
        )
    elif score_val < 25:
        assessment = (
            "Based on the automated fixed asset register analysis procedures applied, "
            "the PP&E data exhibits an ELEVATED risk profile. "
            "Select flagged assets should be reviewed for proper capitalization treatment "
            "and supporting documentation."
        )
    elif score_val < 50:
        assessment = (
            "Based on the automated fixed asset register analysis procedures applied, "
            "the PP&E data exhibits a MODERATE risk profile. "
            "Flagged assets warrant focused review as PP&E anomaly indicators, "
            "particularly depreciation estimates and useful life assumptions."
        )
    else:
        assessment = (
            "Based on the automated fixed asset register analysis procedures applied, "
            "the PP&E data exhibits a HIGH risk profile. "
            "Significant fixed asset anomaly indicators were identified that require "
            "detailed investigation and may warrant expanded PP&E audit procedures "
            "per ISA 540 and PCAOB AS 2501."
        )

    story.append(Paragraph(assessment, styles['MemoBody']))
    story.append(Spacer(1, 12))

    # WORKPAPER SIGN-OFF
    build_workpaper_signoff(story, styles, doc.width, prepared_by, reviewed_by, workpaper_date)

    # DISCLAIMER
    build_disclaimer(
        story, styles,
        domain="fixed asset register analysis",
        isa_reference="ISA 500 (Audit Evidence) and ISA 540 (Auditing Accounting Estimates)",
    )

    # Build PDF
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    log_secure_operation("fa_memo_complete", f"Fixed asset memo generated: {len(pdf_bytes)} bytes")
    return pdf_bytes
