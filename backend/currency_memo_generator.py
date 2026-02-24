"""
Currency Conversion Memo PDF Generator — Sprint 259

Documents multi-currency conversion methodology, rates applied,
unconverted items, and includes mandatory Zero-Storage disclaimer.

Sections:
1. Header (client, period, preparer)
2. Conversion Parameters (presentation currency, rates, date)
3. Conversion Summary (accounts converted, unconverted count)
4. Rates Applied Table
5. Unconverted Items (if any)
6. Disclaimer
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
from shared.framework_resolution import ResolvedFramework
from shared.memo_base import (
    build_disclaimer,
    build_intelligence_stamp,
    build_memo_header,
    build_workpaper_signoff,
    create_memo_styles,
)
from shared.scope_methodology import (
    build_authoritative_reference_block,
    build_methodology_statement,
    build_scope_statement,
)

SEVERITY_COLORS = {
    "high": ClassicalColors.CLAY,
    "medium": ClassicalColors.GOLD_INSTITUTIONAL,
    "low": ClassicalColors.SAGE,
}


def generate_currency_conversion_memo(
    conversion_result: dict[str, Any],
    filename: str = "trial_balance",
    client_name: Optional[str] = None,
    period_tested: Optional[str] = None,
    prepared_by: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    workpaper_date: Optional[str] = None,
    source_document_title: Optional[str] = None,
    source_context_note: Optional[str] = None,
    resolved_framework: ResolvedFramework = ResolvedFramework.FASB,
) -> bytes:
    """Generate a PDF memo documenting the currency conversion methodology.

    Args:
        conversion_result: ConversionResult.to_dict() output
        filename: Source file name
        client_name: Client name for header
        period_tested: Period description
        prepared_by: Preparer name
        reviewed_by: Reviewer name
        workpaper_date: Date for workpaper

    Returns:
        PDF bytes
    """
    log_secure_operation("currency_memo_start", f"Generating currency conversion memo for {filename}")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
    )

    styles = create_memo_styles()
    story: list = []

    doc_width = letter[0] - 1.5 * inch  # page width minus margins
    ref_number = generate_reference_number()

    # 1. Header
    build_memo_header(
        story,
        styles,
        doc_width,
        title="MULTI-CURRENCY CONVERSION MEMO",
        reference=ref_number,
        client_name=client_name,
    )

    story.append(Spacer(1, 12))

    # Source document transparency (Sprint 6)
    if source_document_title and filename:
        story.append(
            Paragraph(create_leader_dots("Source", f"{source_document_title} ({filename})"), styles["MemoLeader"])
        )
        story.append(Spacer(1, 4))
    elif source_document_title:
        story.append(Paragraph(create_leader_dots("Source", source_document_title), styles["MemoLeader"]))
        story.append(Spacer(1, 4))
    elif filename:
        story.append(Paragraph(create_leader_dots("Source", filename), styles["MemoLeader"]))
        story.append(Spacer(1, 4))

    # 2. Conversion Parameters
    story.append(LedgerRule())
    story.append(Spacer(1, 6))
    story.append(Paragraph("Conversion Parameters", styles["MemoSection"]))
    story.append(Spacer(1, 8))

    pres_currency = conversion_result.get("presentation_currency", "N/A")
    total_accounts = conversion_result.get("total_accounts", 0)
    converted_count = conversion_result.get("converted_count", 0)
    unconverted_count = conversion_result.get("unconverted_count", 0)

    params = [
        ("Presentation Currency", pres_currency),
        ("Total Accounts", f"{total_accounts:,}"),
        ("Accounts Converted", f"{converted_count:,}"),
        ("Accounts Unconverted", f"{unconverted_count:,}"),
    ]

    currencies_found = conversion_result.get("currencies_found", [])
    if currencies_found:
        params.append(("Currencies Detected", ", ".join(currencies_found)))

    for label, value in params:
        story.append(
            Paragraph(
                f"<b>{label}:</b> {value}",
                styles["MemoBody"],
            )
        )

    story.append(Spacer(1, 12))

    build_scope_statement(
        story,
        styles,
        doc_width,
        tool_domain="currency_conversion",
        framework=resolved_framework,
        domain_label="multi-currency conversion",
    )

    # 3. Rates Applied
    rates_applied = conversion_result.get("rates_applied", {})
    if rates_applied:
        story.append(LedgerRule())
        story.append(Spacer(1, 6))
        story.append(Paragraph("Exchange Rates Applied", styles["MemoSection"]))
        story.append(Spacer(1, 8))

        headers = ["Currency Pair", "Rate"]
        data = [headers]
        for pair, rate in sorted(rates_applied.items()):
            data.append([pair, rate])

        col_widths = [3.0 * inch, 2.0 * inch]
        table = Table(data, colWidths=col_widths)
        table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("BACKGROUND", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_700),
                    ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OATMEAL),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("GRID", (0, 0), (-1, -1), 0.5, ClassicalColors.OATMEAL_400),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(table)
        story.append(Spacer(1, 12))

    # 4. Unconverted Items
    unconverted_items = conversion_result.get("unconverted_items", [])
    if unconverted_items:
        story.append(LedgerRule())
        story.append(Spacer(1, 6))
        story.append(Paragraph("Unconverted Items", styles["MemoSection"]))
        story.append(Spacer(1, 8))

        story.append(
            Paragraph(
                f"{len(unconverted_items)} account(s) could not be converted. "
                "Results for these accounts reflect original (unconverted) amounts.",
                styles["MemoBody"],
            )
        )
        story.append(Spacer(1, 6))

        headers = ["Account", "Name", "Currency", "Issue", "Severity"]
        cell_style = styles["MemoTableCell"]
        data = [headers]
        for item in unconverted_items[:50]:  # Cap at 50
            data.append(
                [
                    str(item.get("account_number", "")),
                    Paragraph(str(item.get("account_name", "")), cell_style),
                    str(item.get("original_currency", "")),
                    str(item.get("issue", "")).replace("_", " ").title(),
                    str(item.get("severity", "")).title(),
                ]
            )

        col_widths = [1.2 * inch, 2.0 * inch, 0.8 * inch, 1.2 * inch, 0.8 * inch]
        table = Table(data, colWidths=col_widths, repeatRows=1)

        table_style = [
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BACKGROUND", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_700),
            ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OATMEAL),
            ("GRID", (0, 0), (-1, -1), 0.5, ClassicalColors.OATMEAL_400),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]

        # Color-code severity
        for i, item in enumerate(unconverted_items[:50], start=1):
            severity = item.get("severity", "low")
            color = SEVERITY_COLORS.get(severity, ClassicalColors.SAGE)
            table_style.append(("TEXTCOLOR", (4, i), (4, i), color))

        table.setStyle(TableStyle(table_style))
        story.append(table)

        if len(unconverted_items) > 50:
            story.append(Spacer(1, 4))
            story.append(
                Paragraph(
                    f"... and {len(unconverted_items) - 50} more unconverted items.",
                    styles["MemoBodySmall"],
                )
            )

    story.append(Spacer(1, 16))

    # 5. Conclusion
    story.append(LedgerRule())
    story.append(Spacer(1, 6))
    story.append(Paragraph("Methodology & Limitations", styles["MemoSection"]))
    story.append(Spacer(1, 8))

    pct_converted = (converted_count / total_accounts * 100) if total_accounts > 0 else 0

    story.append(
        Paragraph(
            f"This memo documents the currency conversion applied to the uploaded trial balance. "
            f"All amounts were converted to {pres_currency} using user-provided closing exchange rates. "
            f"{converted_count:,} of {total_accounts:,} accounts ({pct_converted:.0f}%) were successfully converted.",
            styles["MemoBody"],
        )
    )
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(
            "Conversion Method: Closing rate applied uniformly to all account balances. "
            "No distinction is made between monetary and non-monetary items in this MVP. "
            "Rounding uses banker's rounding (round half to even) with 4 decimal places internally "
            "and 2 decimal places for display.",
            styles["MemoBody"],
        )
    )

    story.append(Spacer(1, 12))

    # Methodology & Authoritative References
    build_methodology_statement(
        story,
        styles,
        doc_width,
        tool_domain="currency_conversion",
        framework=resolved_framework,
        domain_label="multi-currency conversion",
    )
    build_authoritative_reference_block(
        story,
        styles,
        doc_width,
        tool_domain="currency_conversion",
        framework=resolved_framework,
        domain_label="multi-currency conversion",
    )

    # 6. Workpaper Signoff
    build_workpaper_signoff(
        story,
        styles,
        doc_width,
        prepared_by=prepared_by,
        reviewed_by=reviewed_by,
        workpaper_date=workpaper_date,
    )

    story.append(Spacer(1, 12))

    # Intelligence Stamp
    build_intelligence_stamp(story, styles, client_name=client_name, period_tested=period_tested)

    # 7. Disclaimer
    build_disclaimer(
        story,
        styles,
        domain="multi-currency conversion",
        isa_reference="IAS 21 (Effects of Changes in Foreign Exchange Rates)",
    )

    # Build PDF
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    log_secure_operation("currency_memo_complete", f"Currency conversion memo generated ({len(pdf_bytes)} bytes)")

    return pdf_bytes
