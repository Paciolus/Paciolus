"""
Bank Reconciliation Testing Memo PDF Generator (Sprint 128)

Auto-generated reconciliation memo per ISA 500 (Audit Evidence) /
ISA 505 (External Confirmations) / PCAOB AS 2310.
Renaissance Ledger aesthetic consistent with existing PDF exports.

Sections:
1. Header (client, period, preparer)
2. Scope (bank transactions, ledger transactions, column detection)
3. Reconciliation Results (matched, outstanding, reconciling difference)
4. Outstanding Items (bank-only, ledger-only breakdown)
5. Conclusion (professional assessment based on reconciling difference)
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
    build_workpaper_signoff,
    create_memo_styles,
)


def generate_bank_rec_memo(
    rec_result: dict[str, Any],
    filename: str = "bank_reconciliation",
    client_name: Optional[str] = None,
    period_tested: Optional[str] = None,
    prepared_by: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    workpaper_date: Optional[str] = None,
) -> bytes:
    """Generate a PDF testing memo for bank reconciliation results.

    Args:
        rec_result: BankRecResult.to_dict() output
        filename: Base filename for the report
        client_name: Client/entity name
        period_tested: Period description (e.g., "FY 2025")
        prepared_by: Preparer name
        reviewed_by: Reviewer name
        workpaper_date: Date string (ISO format)

    Returns:
        PDF bytes
    """
    log_secure_operation("bank_rec_memo_generate", f"Generating bank reconciliation memo: {filename}")

    styles = create_memo_styles()
    buffer = io.BytesIO()
    reference = generate_reference_number().replace("PAC-", "REC-")

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=1.0 * inch,
        bottomMargin=0.8 * inch,
    )

    story = []
    summary = rec_result.get("summary", {})
    bank_detection = rec_result.get("bank_column_detection", {})
    ledger_detection = rec_result.get("ledger_column_detection", {})

    # 1. HEADER
    build_memo_header(story, styles, doc.width, "Bank Reconciliation Memo", reference, client_name)

    # 2. SCOPE
    story.append(Paragraph("I. SCOPE", styles['MemoSection']))
    story.append(LedgerRule(doc.width))

    matched = summary.get("matched_count", 0)
    bank_only = summary.get("bank_only_count", 0)
    ledger_only = summary.get("ledger_only_count", 0)
    total_txns = matched + bank_only + ledger_only

    scope_lines = []
    if period_tested:
        scope_lines.append(create_leader_dots("Period Tested", period_tested))

    scope_lines.extend([
        create_leader_dots("Total Transactions Analyzed", f"{total_txns:,}"),
        create_leader_dots("Bank Statement Transactions", f"{matched + bank_only:,}"),
        create_leader_dots("General Ledger Transactions", f"{matched + ledger_only:,}"),
    ])

    bank_conf = bank_detection.get("overall_confidence", 0)
    ledger_conf = ledger_detection.get("overall_confidence", 0)
    if bank_conf or ledger_conf:
        scope_lines.extend([
            create_leader_dots("Bank Column Detection Confidence", f"{bank_conf:.0%}"),
            create_leader_dots("Ledger Column Detection Confidence", f"{ledger_conf:.0%}"),
        ])

    for line in scope_lines:
        story.append(Paragraph(line, styles['MemoLeader']))
    story.append(Spacer(1, 8))

    # 3. RECONCILIATION RESULTS
    story.append(Paragraph("II. RECONCILIATION RESULTS", styles['MemoSection']))
    story.append(LedgerRule(doc.width))

    matched_amount = summary.get("matched_amount", 0)
    bank_only_amount = summary.get("bank_only_amount", 0)
    ledger_only_amount = summary.get("ledger_only_amount", 0)
    rec_diff = summary.get("reconciling_difference", 0)
    total_bank = summary.get("total_bank", 0)
    total_ledger = summary.get("total_ledger", 0)
    match_rate = matched / total_txns if total_txns > 0 else 0

    result_lines = [
        create_leader_dots("Matched Transactions", f"{matched:,} ({match_rate:.1%})"),
        create_leader_dots("Matched Amount", f"${abs(matched_amount):,.2f}"),
        create_leader_dots("Bank-Only (Outstanding Deposits)", f"{bank_only:,}"),
        create_leader_dots("Ledger-Only (Outstanding Checks)", f"{ledger_only:,}"),
        create_leader_dots("Reconciling Difference", f"${abs(rec_diff):,.2f}"),
    ]

    for line in result_lines:
        story.append(Paragraph(line, styles['MemoLeader']))
    story.append(Spacer(1, 6))

    # Balance summary table
    balance_data = [
        ["Category", "Amount"],
        ["Bank Statement Total", f"${total_bank:,.2f}"],
        ["General Ledger Total", f"${total_ledger:,.2f}"],
        ["Reconciling Difference", f"${rec_diff:,.2f}"],
    ]
    balance_table = Table(balance_data, colWidths=[3.0 * inch, 2.5 * inch])
    balance_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
        ('LINEBELOW', (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
        ('LINEBELOW', (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
        ('LINEBELOW', (0, -1), (-1, -1), 1, ClassicalColors.OBSIDIAN_DEEP),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (0, -1), 0),
    ]))
    story.append(balance_table)
    story.append(Spacer(1, 8))

    # 4. OUTSTANDING ITEMS
    has_outstanding = bank_only > 0 or ledger_only > 0
    if has_outstanding:
        story.append(Paragraph("III. OUTSTANDING ITEMS", styles['MemoSection']))
        story.append(LedgerRule(doc.width))

        outstanding_data = [["Category", "Count", "Amount"]]
        if bank_only > 0:
            outstanding_data.append([
                "Bank-Only (Outstanding Deposits)",
                str(bank_only),
                f"${abs(bank_only_amount):,.2f}",
            ])
        if ledger_only > 0:
            outstanding_data.append([
                "Ledger-Only (Outstanding Checks)",
                str(ledger_only),
                f"${abs(ledger_only_amount):,.2f}",
            ])

        outstanding_table = Table(outstanding_data, colWidths=[3.5 * inch, 1.0 * inch, 2.0 * inch])
        outstanding_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
            ('LINEBELOW', (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
            ('LINEBELOW', (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (0, -1), 0),
        ]))
        story.append(outstanding_table)

        if bank_only + ledger_only > 0:
            story.append(Spacer(1, 4))
            story.append(Paragraph(
                "Outstanding items represent transactions present in one source but not the other. "
                "These may represent timing differences, recording errors, or items requiring investigation.",
                styles['MemoBodySmall'],
            ))
        story.append(Spacer(1, 8))

    # 5. CONCLUSION
    conclusion_num = "IV" if has_outstanding else "III"
    story.append(Paragraph(f"{conclusion_num}. CONCLUSION", styles['MemoSection']))
    story.append(LedgerRule(doc.width))

    # Risk assessment based on reconciling difference and match rate
    if abs(rec_diff) < 1.0 and match_rate >= 0.95:
        assessment = (
            "Based on the automated reconciliation procedures applied, "
            "the bank reconciliation exhibits a LOW risk profile. "
            "The reconciling difference is immaterial and the match rate is satisfactory. "
            "No items requiring further investigation were identified."
        )
    elif abs(rec_diff) < 1000 and match_rate >= 0.80:
        assessment = (
            "Based on the automated reconciliation procedures applied, "
            "the bank reconciliation exhibits a MODERATE risk profile. "
            "The reconciling difference and outstanding items should be reviewed "
            "to confirm they represent normal timing differences rather than errors or omissions."
        )
    else:
        assessment = (
            "Based on the automated reconciliation procedures applied, "
            "the bank reconciliation exhibits an ELEVATED risk profile. "
            "The reconciling difference and/or outstanding item volume may indicate "
            "recording errors, omissions, or unusual transactions requiring detailed investigation "
            "per ISA 500 and ISA 505."
        )

    story.append(Paragraph(assessment, styles['MemoBody']))
    story.append(Spacer(1, 12))

    # WORKPAPER SIGN-OFF
    build_workpaper_signoff(story, styles, doc.width, prepared_by, reviewed_by, workpaper_date)

    # DISCLAIMER
    build_disclaimer(
        story, styles,
        domain="bank reconciliation analysis",
        isa_reference="ISA 500 (Audit Evidence), ISA 505 (External Confirmations), and PCAOB AS 2310",
    )

    # Build PDF
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    log_secure_operation("bank_rec_memo_complete", f"Bank rec memo generated: {len(pdf_bytes)} bytes")
    return pdf_bytes
