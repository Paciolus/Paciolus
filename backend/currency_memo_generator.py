"""
Currency Conversion Memo PDF Generator — Sprint 259 / Sprint 509

Documents multi-currency conversion methodology, rates applied,
unconverted items, and includes mandatory Zero-Storage disclaimer.

Sprint 509 restructure:
- Roman numeral section headers (I–VII)
- MCY- reference prefix (unique, non-colliding)
- Conversion Output table (currency exposure summary)
- Non-monetary account identification (IAS 21)
- CTA note (ASC 830-30 / IAS 21)
- Suggested rate sources for unconverted items
- Conclusion section
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
from shared.memo_template import _roman
from shared.report_chrome import (
    ReportMetadata,
    build_cover_page,
    draw_page_footer,
    find_logo,
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

# Non-monetary account keywords for IAS 21 / ASC 830-30 identification
_NON_MONETARY_KEYWORDS = [
    "inventory",
    "pp&e",
    "ppe",
    "property",
    "plant",
    "equipment",
    "intangible",
    "goodwill",
    "prepaid",
    "fixed asset",
    "right-of-use",
    "rou",
    "land",
    "building",
]


def _format_currency_amount(amount: float, currency: str = "USD") -> str:
    """Format a currency amount with appropriate symbol."""
    symbols = {"USD": "$", "EUR": "\u20ac", "GBP": "\u00a3", "JPY": "\u00a5", "CAD": "C$"}
    symbol = symbols.get(currency, "")
    if abs(amount) >= 1_000_000:
        return f"{symbol}{amount:,.0f}"
    return f"{symbol}{amount:,.2f}"


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
    fiscal_year_end: Optional[str] = None,
    resolved_framework: ResolvedFramework = ResolvedFramework.FASB,
    include_signoff: bool = False,
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
    ref_number = generate_reference_number().replace("PAC-", "MCY-")

    # Extract data from result
    pres_currency = conversion_result.get("presentation_currency", "N/A")
    total_accounts = conversion_result.get("total_accounts", 0)
    converted_count = conversion_result.get("converted_count", 0)
    unconverted_items = conversion_result.get("unconverted_items", [])
    rates_applied = conversion_result.get("rates_applied", {})
    currencies_found = conversion_result.get("currencies_found", [])
    currency_exposure = conversion_result.get("currency_exposure", [])

    # BUG-01 fix: separate truly unconverted from stale-rate warnings
    truly_unconverted = [
        item
        for item in unconverted_items
        if item.get("issue") in ("missing_rate", "missing_currency_code", "invalid_currency")
    ]
    stale_rate_warnings = [item for item in unconverted_items if item.get("issue") == "stale_rate"]
    # Derive count from actual items to prevent scope/table discrepancy
    unconverted_count = len(truly_unconverted)

    pct_converted = (converted_count / total_accounts * 100) if total_accounts > 0 else 0

    # ── 0. COVER PAGE ──
    logo_path = find_logo()
    cover_metadata = ReportMetadata(
        title="MULTI-CURRENCY CONVERSION MEMO",
        client_name=client_name or "",
        engagement_period=period_tested or "",
        source_document=filename,
        source_document_title=source_document_title or "",
        source_context_note=source_context_note or "",
        reference=ref_number,
        fiscal_year_end=fiscal_year_end or "",
    )
    build_cover_page(story, styles, cover_metadata, doc_width, logo_path)

    # ── HEADER ──
    build_memo_header(
        story,
        styles,
        doc_width,
        title="MULTI-CURRENCY CONVERSION MEMO",
        reference=ref_number,
        client_name=client_name,
    )

    story.append(Spacer(1, 12))

    # Source document transparency
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

    section_num = 1

    # ── SECTION I: SCOPE ──
    story.append(LedgerRule())
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"{_roman(section_num)}. Scope", styles["MemoSection"]))
    story.append(Spacer(1, 8))

    params = [
        ("Presentation Currency", pres_currency),
        ("Total Accounts", f"{total_accounts:,}"),
        ("Accounts Converted", f"{converted_count:,}"),
        ("Accounts Unconverted", f"{unconverted_count:,}"),
    ]

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
    section_num += 1

    # ── SECTION II: EXCHANGE RATES APPLIED ──
    if rates_applied:
        story.append(LedgerRule())
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"{_roman(section_num)}. Exchange Rates Applied", styles["MemoSection"]))
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
    section_num += 1

    # ── SECTION III: CONVERSION OUTPUT ──
    story.append(LedgerRule())
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"{_roman(section_num)}. Conversion Output", styles["MemoSection"]))
    story.append(Spacer(1, 8))

    if currency_exposure:
        _build_conversion_output_table(story, styles, currency_exposure, pres_currency)
    else:
        # Fallback: summary from available data
        story.append(
            Paragraph(
                f"{converted_count:,} of {total_accounts:,} accounts ({pct_converted:.1f}%) "
                f"were successfully converted to {pres_currency}.",
                styles["MemoBody"],
            )
        )
        if unconverted_count > 0:
            story.append(
                Paragraph(
                    f"{unconverted_count:,} account(s) could not be converted and retain their "
                    f"original foreign currency balances.",
                    styles["MemoBody"],
                )
            )
    story.append(Spacer(1, 12))
    section_num += 1

    # ── SECTION IV: UNCONVERTED ITEMS ──
    if truly_unconverted:
        story.append(LedgerRule())
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"{_roman(section_num)}. Unconverted Items", styles["MemoSection"]))
        story.append(Spacer(1, 8))

        story.append(
            Paragraph(
                f"{len(truly_unconverted)} account(s) could not be converted. "
                "Results for these accounts reflect original (unconverted) amounts.",
                styles["MemoBody"],
            )
        )
        story.append(Spacer(1, 6))

        _build_unconverted_items_table(story, styles, truly_unconverted)

        # IMP-04: HIGH severity intercompany note
        high_items = [i for i in truly_unconverted if i.get("severity") == "high"]
        intercompany_high = [i for i in high_items if "intercompany" in i.get("account_name", "").lower()]
        if intercompany_high:
            currencies = ", ".join(sorted({i.get("original_currency", "?") for i in intercompany_high}))
            story.append(Spacer(1, 6))
            story.append(
                Paragraph(
                    f"<i>HIGH severity unconverted items ({currencies}) relate to intercompany balances. "
                    "These require immediate rate resolution \u2014 intercompany balances that remain "
                    "unconverted will cause the consolidated trial balance to be out of balance in "
                    f"{pres_currency}. Add the missing rates and rerun the conversion before finalizing.</i>",
                    styles["MemoBodySmall"],
                )
            )
        story.append(Spacer(1, 12))

    # Stale rate warnings (separate from true failures)
    if stale_rate_warnings:
        story.append(
            Paragraph(
                f"<b>Stale Rate Warnings:</b> {len(stale_rate_warnings)} account(s) were converted "
                "using exchange rates older than 90 days from the target date. Review these rates "
                "for currency fluctuation risk.",
                styles["MemoBody"],
            )
        )
        story.append(Spacer(1, 8))
    section_num += 1

    # ── SECTION V: METHODOLOGY & LIMITATIONS ──
    story.append(LedgerRule())
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"{_roman(section_num)}. Methodology &amp; Limitations", styles["MemoSection"]))
    story.append(Spacer(1, 8))

    story.append(
        Paragraph(
            f"This memo documents the currency conversion applied to the uploaded trial balance. "
            f"All amounts were converted to {pres_currency} using closing exchange rates provided "
            f"by the practitioner. "
            f"{converted_count:,} of {total_accounts:,} accounts ({pct_converted:.0f}%) "
            f"were successfully converted.",
            styles["MemoBody"],
        )
    )
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(
            "Conversion Method: Closing rate applied uniformly to all account balances. "
            "Rounding uses banker's rounding (round half to even) with 4 decimal places internally "
            "and 2 decimal places for display.",
            styles["MemoBody"],
        )
    )

    # Monetary/non-monetary classification warning (IAS 21)
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(
            "<b>Monetary vs. Non-Monetary Note:</b> Under IAS 21, monetary items "
            "(cash, receivables, payables) should be translated at the closing rate, "
            "while non-monetary items (inventory, PP&amp;E, intangible assets) carried at "
            "historical cost should be translated at the historical rate. "
            "This conversion applies the closing rate uniformly to all accounts. "
            "Non-monetary accounts translated at the closing rate may produce "
            "translation differences that do not reflect economic reality. "
            "The auditor should evaluate whether material non-monetary balances "
            "require adjustment to historical rates.",
            styles["MemoBody"],
        )
    )

    # IMP-02: Non-monetary account identification
    story.append(Spacer(1, 8))
    story.append(
        Paragraph(
            "<b>Non-Monetary Account Identification:</b> "
            "Non-monetary account identification requires account type metadata "
            "(monetary/non-monetary classification per IAS 21.23 and ASC 830-30-45). "
            "Add an account_type column to the trial balance to enable automatic identification. "
            "Accounts likely requiring historical rate treatment include: "
            "Inventory, PP&amp;E, Intangible Assets, Goodwill, and Prepaid Expenses. "
            "The USD amounts shown for these accounts reflect the closing rate and may "
            "require adjustment. Obtain the historical exchange rates at the acquisition "
            "dates for these assets and compute the adjustment. The difference flows to "
            "the cumulative translation adjustment (CTA) in Other Comprehensive Income.",
            styles["MemoBody"],
        )
    )

    # IMP-03: CTA note
    story.append(Spacer(1, 8))
    story.append(
        Paragraph(
            "<b>Cumulative Translation Adjustment (CTA):</b> "
            "Under ASC 830-30 and IAS 21, the translation adjustment arising from "
            "the conversion of foreign currency financial statements to the reporting "
            f"currency ({pres_currency}) must be recognized in Other Comprehensive Income (OCI) "
            "as a cumulative translation adjustment. "
            "CTA computation requires prior period closing rates and opening "
            "net assets by currency. These were not provided in the current conversion. "
            "The practitioner should compute the CTA manually and record the adjusting entry "
            "to AOCI before finalizing the translated financial statements.",
            styles["MemoBody"],
        )
    )

    story.append(Spacer(1, 12))

    # Methodology statement (interpretive context)
    build_methodology_statement(
        story,
        styles,
        doc_width,
        tool_domain="currency_conversion",
        framework=resolved_framework,
        domain_label="multi-currency conversion",
    )
    section_num += 1

    # ── SECTION VI: AUTHORITATIVE REFERENCES ──
    build_authoritative_reference_block(
        story,
        styles,
        doc_width,
        tool_domain="currency_conversion",
        framework=resolved_framework,
        domain_label="multi-currency conversion",
        section_label=f"{_roman(section_num)}.",
    )
    section_num += 1

    # ── SECTION VII: CONCLUSION ──
    story.append(LedgerRule())
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"{_roman(section_num)}. Conclusion", styles["MemoSection"]))
    story.append(Spacer(1, 8))

    conclusion_parts = [
        f"Based on the automated multi-currency conversion procedures applied, "
        f"{converted_count:,} of {total_accounts:,} accounts ({pct_converted:.1f}%) "
        f"were successfully converted to {pres_currency} using closing rates"
    ]

    if period_tested:
        conclusion_parts.append(f" as of {period_tested}")
    conclusion_parts.append(". ")

    if unconverted_count > 0:
        missing_currencies = sorted(
            {i.get("original_currency", "?") for i in truly_unconverted if i.get("issue") == "missing_rate"}
        )
        curr_list = ", ".join(missing_currencies) if missing_currencies else "unknown currencies"
        conclusion_parts.append(
            f"{unconverted_count} account(s) could not be converted due to missing exchange rates "
            f"for {curr_list} \u2014 these accounts retain their unconverted foreign currency "
            "balances and require manual rate application before the TB can be considered "
            "fully translated."
        )
    else:
        conclusion_parts.append("All accounts were successfully converted. No missing exchange rates were identified.")

    conclusion_parts.append(
        " The conversion applies the closing rate uniformly. The auditor should evaluate "
        "whether material non-monetary balances (inventory, PP&amp;E) require adjustment "
        "to historical rates per IAS 21 and ASC 830-30 before issuing a conclusion "
        "on the translated balances."
    )

    story.append(Paragraph("".join(conclusion_parts), styles["MemoBody"]))
    story.append(Spacer(1, 16))

    # ── WORKPAPER SIGNOFF ──
    build_workpaper_signoff(
        story,
        styles,
        doc_width,
        prepared_by=prepared_by,
        reviewed_by=reviewed_by,
        workpaper_date=workpaper_date,
        include_signoff=include_signoff,
    )

    story.append(Spacer(1, 12))

    # Intelligence Stamp
    build_intelligence_stamp(story, styles, client_name=client_name, period_tested=period_tested)

    # Disclaimer
    build_disclaimer(
        story,
        styles,
        domain="multi-currency conversion",
        isa_reference="IAS 21 (Effects of Changes in Foreign Exchange Rates)",
    )

    # Build PDF
    doc.build(story, onFirstPage=draw_page_footer)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    log_secure_operation("currency_memo_complete", f"Currency conversion memo generated ({len(pdf_bytes)} bytes)")

    return pdf_bytes


def _build_conversion_output_table(
    story: list,
    styles: dict,
    currency_exposure: list[dict],
    pres_currency: str,
) -> None:
    """Build the foreign currency exposure summary table (Section III)."""
    headers = ["Currency", "Accounts", "Foreign Total", "Rate", f"{pres_currency} Equivalent", "% of Total"]
    data = [headers]

    total_usd = 0.0
    total_accounts = 0

    for exp in currency_exposure:
        curr = exp.get("currency", "")
        acct_count = exp.get("account_count", 0)
        foreign_total = exp.get("foreign_total", 0.0)
        rate = exp.get("rate", "N/A")
        usd_equiv = exp.get("usd_equivalent", 0.0)
        pct = exp.get("pct_of_total", 0.0)

        data.append(
            [
                curr,
                str(acct_count),
                _format_currency_amount(foreign_total, curr),
                str(rate),
                _format_currency_amount(usd_equiv, pres_currency),
                f"{pct:.1f}%",
            ]
        )
        total_usd += usd_equiv
        total_accounts += acct_count

    # Totals row
    cell_style = styles["MemoTableCell"]
    data.append(
        [
            Paragraph("Total", cell_style),
            str(total_accounts),
            "",
            "",
            _format_currency_amount(total_usd, pres_currency),
            "100.0%",
        ]
    )

    col_widths = [0.7 * inch, 0.7 * inch, 1.3 * inch, 0.9 * inch, 1.4 * inch, 0.8 * inch]
    table = Table(data, colWidths=col_widths, repeatRows=1)

    table_style = [
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BACKGROUND", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_700),
        ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OATMEAL),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, ClassicalColors.OATMEAL_400),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        # Bold totals row
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("LINEABOVE", (0, -1), (-1, -1), 1, ClassicalColors.OBSIDIAN),
    ]
    table.setStyle(TableStyle(table_style))
    story.append(table)


def _build_unconverted_items_table(
    story: list,
    styles: dict,
    items: list[dict],
) -> None:
    """Build the unconverted items table with suggested rate sources (Section IV)."""
    cell_style = styles["MemoTableCell"]
    headers = ["Account", "Name", "Currency", "Issue", "Severity", "Suggested Rate Source"]
    data = [headers]

    for item in items[:50]:
        issue_text = str(item.get("issue", "")).replace("_", " ").title()
        severity_text = str(item.get("severity", "")).title()
        currency = str(item.get("original_currency", ""))

        # IMP-04: Suggested rate source
        rate_source = f"Federal Reserve H.10 or Reuters for {currency}/USD" if currency else "N/A"

        data.append(
            [
                Paragraph(str(item.get("account_number", "")), cell_style),
                Paragraph(str(item.get("account_name", "")), cell_style),
                Paragraph(currency, cell_style),
                Paragraph(issue_text, cell_style),
                Paragraph(severity_text, cell_style),
                Paragraph(rate_source, cell_style),
            ]
        )

    col_widths = [0.7 * inch, 1.4 * inch, 0.6 * inch, 0.9 * inch, 0.6 * inch, 1.8 * inch]
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
    for i, item in enumerate(items[:50], start=1):
        severity = item.get("severity", "low")
        color = SEVERITY_COLORS.get(severity, ClassicalColors.SAGE)
        table_style.append(("TEXTCOLOR", (4, i), (4, i), color))

    table.setStyle(TableStyle(table_style))
    story.append(table)

    if len(items) > 50:
        story.append(Spacer(1, 4))
        story.append(
            Paragraph(
                f"... and {len(items) - 50} more unconverted items.",
                styles["MemoBodySmall"],
            )
        )

    # Rate source note
    story.append(Spacer(1, 6))
    story.append(
        Paragraph(
            "<i>Practitioner must obtain authoritative closing rates from the Federal Reserve H.10 "
            "release, Reuters, Bloomberg, or the entity's bank confirmation for the engagement date. "
            "Do not rely on approximate or estimated rates for final translated balances.</i>",
            styles["MemoBodySmall"],
        )
    )
