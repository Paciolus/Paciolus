"""
Three-Way Match Testing Memo PDF Generator (Sprint 94)

Auto-generated matching memo per ISA 505 / ISA 500 / PCAOB AS 1105.
Renaissance Ledger aesthetic consistent with existing PDF exports.

Sections:
1. Header (client, period, preparer)
2. Scope (documents matched, file counts)
3. Match Results (match rates, risk assessment)
4. Material Variances (amount, quantity, price, date)
5. Unmatched Documents (orphan POs, invoices, receipts)
6. Conclusion (professional assessment)
"""

import io
from typing import Any, Optional

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from pdf_generator import (
    ClassicalColors,
    LedgerRule,
    create_leader_dots,
    generate_reference_number,
)
from security_utils import log_secure_operation
from shared.memo_base import (
    build_disclaimer,
    build_memo_header,
    build_proof_summary_section,
    build_workpaper_signoff,
    create_memo_styles,
)


def generate_three_way_match_memo(
    twm_result: dict[str, Any],
    filename: str = "three_way_match",
    client_name: Optional[str] = None,
    period_tested: Optional[str] = None,
    prepared_by: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    workpaper_date: Optional[str] = None,
) -> bytes:
    """Generate a PDF testing memo for three-way match results.

    Args:
        twm_result: ThreeWayMatchResult.to_dict() output
        filename: Base filename for the report
        client_name: Client/entity name
        period_tested: Period description (e.g., "FY 2025")
        prepared_by: Preparer name
        reviewed_by: Reviewer name
        workpaper_date: Date string (ISO format)

    Returns:
        PDF bytes
    """
    log_secure_operation("twm_memo_generate", f"Generating three-way match memo: {filename}")

    styles = create_memo_styles()
    buffer = io.BytesIO()
    reference = generate_reference_number().replace("PAC-", "TWM-")

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=1.0 * inch,
        bottomMargin=0.8 * inch,
    )

    story = []
    summary = twm_result.get("summary", {})
    variances = twm_result.get("variances", [])
    config = twm_result.get("config", {})
    data_quality = twm_result.get("data_quality", {})

    # 1. HEADER
    build_memo_header(story, styles, doc.width, "Three-Way Match Validator Memo", reference, client_name)

    # 2. SCOPE
    story.append(Paragraph("I. SCOPE", styles['MemoSection']))
    story.append(LedgerRule(doc.width))

    scope_lines = [
        create_leader_dots("Purchase Orders", f"{summary.get('total_pos', 0):,}"),
        create_leader_dots("Invoices", f"{summary.get('total_invoices', 0):,}"),
        create_leader_dots("Receipts / GRNs", f"{summary.get('total_receipts', 0):,}"),
    ]
    if period_tested:
        scope_lines.insert(0, create_leader_dots("Period Tested", period_tested))

    # Config info
    amt_tol = config.get("amount_tolerance", 0.01)
    price_tol = config.get("price_variance_threshold", 0.05)
    date_window = config.get("date_window_days", 30)
    fuzzy = config.get("enable_fuzzy_matching", True)

    scope_lines.extend([
        create_leader_dots("Amount Tolerance", f"${amt_tol:,.2f}"),
        create_leader_dots("Price Variance Threshold", f"{price_tol:.0%}"),
        create_leader_dots("Date Window", f"{date_window} days"),
        create_leader_dots("Fuzzy Matching", "Enabled" if fuzzy else "Disabled"),
    ])

    for line in scope_lines:
        story.append(Paragraph(line, styles['MemoLeader']))
    story.append(Spacer(1, 8))

    # PROOF SUMMARY
    col_detection = twm_result.get("column_detection", {})
    po_conf = col_detection.get("po", {}).get("overall_confidence", 0) if col_detection else 0
    inv_conf = col_detection.get("invoice", {}).get("overall_confidence", 0) if col_detection else 0
    rcpt_conf = col_detection.get("receipt", {}).get("overall_confidence", 0) if col_detection else 0
    avg_conf = (po_conf + inv_conf + rcpt_conf) / 3 if col_detection else 0

    total_docs = summary.get("total_pos", 0) + summary.get("total_invoices", 0) + summary.get("total_receipts", 0)
    unmatched_count = (
        len(twm_result.get("unmatched_pos", [])) +
        len(twm_result.get("unmatched_invoices", [])) +
        len(twm_result.get("unmatched_receipts", []))
    )

    _proof_result = {
        "composite_score": {
            "tests_run": 6,
            "total_flagged": unmatched_count + summary.get("material_variances_count", 0),
        },
        "data_quality": {
            "completeness_score": data_quality.get("overall_quality_score", 0),
        },
        "column_detection": {
            "overall_confidence": avg_conf,
        },
        "test_results": [
            {"test_name": "Full Matches", "entries_flagged": 0, "skipped": False},
            {"test_name": "Partial Matches", "entries_flagged": len(twm_result.get("partial_matches", [])), "skipped": False},
            {"test_name": "Material Variances", "entries_flagged": summary.get("material_variances_count", 0), "skipped": False},
            {"test_name": "Unmatched POs", "entries_flagged": len(twm_result.get("unmatched_pos", [])), "skipped": False},
            {"test_name": "Unmatched Invoices", "entries_flagged": len(twm_result.get("unmatched_invoices", [])), "skipped": False},
            {"test_name": "Unmatched Receipts", "entries_flagged": len(twm_result.get("unmatched_receipts", [])), "skipped": False},
        ],
    }
    build_proof_summary_section(story, styles, doc.width, _proof_result)

    # 3. MATCH RESULTS
    story.append(Paragraph("II. MATCH RESULTS", styles['MemoSection']))
    story.append(LedgerRule(doc.width))

    full_count = summary.get("full_match_count", 0)
    partial_count = summary.get("partial_match_count", 0)
    full_rate = summary.get("full_match_rate", 0)
    partial_rate = summary.get("partial_match_rate", 0)
    risk = summary.get("risk_assessment", "low")

    result_lines = [
        create_leader_dots("Full Matches (3-way)", f"{full_count:,} ({full_rate:.1%})"),
        create_leader_dots("Partial Matches (2-way)", f"{partial_count:,} ({partial_rate:.1%})"),
        create_leader_dots("Material Variances", f"{summary.get('material_variances_count', 0):,}"),
        create_leader_dots("Net Variance", f"${summary.get('net_variance', 0):,.2f}"),
        create_leader_dots("Risk Assessment", risk.upper()),
    ]

    for line in result_lines:
        story.append(Paragraph(line, styles['MemoLeader']))
    story.append(Spacer(1, 6))

    # Amount totals table
    amount_data = [
        ["Document Type", "Total Amount"],
        ["Purchase Orders", f"${summary.get('total_po_amount', 0):,.2f}"],
        ["Invoices", f"${summary.get('total_invoice_amount', 0):,.2f}"],
        ["Receipts", f"${summary.get('total_receipt_amount', 0):,.2f}"],
    ]
    amount_table = Table(amount_data, colWidths=[3.0 * inch, 2.5 * inch])
    amount_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
        ('LINEBELOW', (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
        ('LINEBELOW', (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (0, -1), 0),
    ]))
    story.append(amount_table)
    story.append(Spacer(1, 8))

    # 4. MATERIAL VARIANCES
    material_variances = [v for v in variances if v.get("severity") in ("high", "medium")]
    if material_variances:
        story.append(Paragraph("III. MATERIAL VARIANCES", styles['MemoSection']))
        story.append(LedgerRule(doc.width))

        story.append(Paragraph(
            f"{len(material_variances)} material variance(s) were identified requiring review:",
            styles['MemoBody'],
        ))

        var_data = [["Field", "PO Value", "Invoice Value", "Variance", "Severity"]]
        for v in material_variances[:15]:
            field = v.get("field", "amount")
            po_val = v.get("po_value")
            inv_val = v.get("invoice_value")

            if field == "date":
                po_str = str(po_val) if po_val is not None else "—"
                inv_str = str(inv_val) if inv_val is not None else "—"
                var_str = f"{v.get('variance_amount', 0):.0f} days"
            else:
                po_str = f"${po_val:,.2f}" if po_val is not None else "—"
                inv_str = f"${inv_val:,.2f}" if inv_val is not None else "—"
                var_str = f"${v.get('variance_amount', 0):,.2f}"

            var_data.append([
                field.title(),
                po_str,
                inv_str,
                var_str,
                v.get("severity", "low").upper(),
            ])

        var_table = Table(var_data, colWidths=[1.0 * inch, 1.4 * inch, 1.4 * inch, 1.4 * inch, 0.8 * inch])
        var_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
            ('LINEBELOW', (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
            ('LINEBELOW', (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (0, -1), 0),
        ]))
        story.append(var_table)

        if len(material_variances) > 15:
            story.append(Paragraph(
                f"+ {len(material_variances) - 15} additional material variances (see CSV export for full list)",
                styles['MemoBodySmall'],
            ))
        story.append(Spacer(1, 8))

    # 5. UNMATCHED DOCUMENTS
    unmatched_pos = twm_result.get("unmatched_pos", [])
    unmatched_invoices = twm_result.get("unmatched_invoices", [])
    unmatched_receipts = twm_result.get("unmatched_receipts", [])
    total_unmatched = len(unmatched_pos) + len(unmatched_invoices) + len(unmatched_receipts)

    section_num = "IV" if material_variances else "III"
    if total_unmatched > 0:
        story.append(Paragraph(f"{section_num}. UNMATCHED DOCUMENTS", styles['MemoSection']))
        story.append(LedgerRule(doc.width))

        unmatched_lines = [
            create_leader_dots("Unmatched POs", str(len(unmatched_pos))),
            create_leader_dots("Unmatched Invoices", str(len(unmatched_invoices))),
            create_leader_dots("Unmatched Receipts", str(len(unmatched_receipts))),
        ]
        for line in unmatched_lines:
            story.append(Paragraph(line, styles['MemoLeader']))

        if unmatched_invoices:
            story.append(Spacer(1, 4))
            story.append(Paragraph(
                "Unmatched invoices may indicate goods/services received without proper authorization "
                "or invoices submitted without a corresponding purchase order.",
                styles['MemoBodySmall'],
            ))

        story.append(Spacer(1, 8))
        next_section = chr(ord(section_num[0]) + 1)
    else:
        next_section = section_num

    # 6. CONCLUSION
    story.append(Paragraph(f"{next_section}. CONCLUSION", styles['MemoSection']))
    story.append(LedgerRule(doc.width))

    if risk == "low":
        assessment = (
            "Based on the automated three-way matching procedures applied, "
            "the procurement cycle exhibits a LOW risk profile. "
            "Match rates are satisfactory and no material variances requiring further investigation were identified."
        )
    elif risk == "medium":
        assessment = (
            "Based on the automated three-way matching procedures applied, "
            "the procurement cycle exhibits a MEDIUM risk profile. "
            "Select variances and unmatched documents should be reviewed for proper authorization and documentation."
        )
    else:
        assessment = (
            "Based on the automated three-way matching procedures applied, "
            "the procurement cycle exhibits a HIGH risk profile. "
            "Significant variances and/or unmatched documents were identified that require detailed investigation "
            "and may warrant expanded audit procedures per ISA 505 and PCAOB AS 1105."
        )

    story.append(Paragraph(assessment, styles['MemoBody']))
    story.append(Spacer(1, 12))

    # WORKPAPER SIGN-OFF
    build_workpaper_signoff(story, styles, doc.width, prepared_by, reviewed_by, workpaper_date)

    # DISCLAIMER
    build_disclaimer(story, styles, domain="three-way match validation", isa_reference="ISA 500 (Audit Evidence) and ISA 505 (External Confirmations)")

    # Build PDF
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    log_secure_operation("twm_memo_complete", f"TWM memo generated: {len(pdf_bytes)} bytes")
    return pdf_bytes
