"""
Thin orchestrator that assembles complete PDFs by calling section renderers.

Two public entry points mirror the original pdf_generator API:
  - generate_audit_report()      -- diagnostic intelligence summary
  - generate_financial_statements_pdf() -- balance sheet / income / cash flow
"""

import io
from datetime import UTC, datetime
from typing import Any, Optional

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from pdf.chrome import draw_diagnostic_watermark, draw_fs_decorations
from pdf.components import DoubleRule, LedgerRule, format_classical_date, generate_reference_number

# Section renderers -- financial statements
from pdf.sections.balance_sheet import render_balance_sheet
from pdf.sections.cash_flow import render_cash_flow

# Section renderers -- diagnostic
from pdf.sections.diagnostic import (
    render_anomaly_details,
    render_classical_footer,
    render_data_intake_summary,
    render_executive_summary,
    render_limitations,
    render_population_composition,
    render_risk_summary,
    render_table_of_contents,
)
from pdf.sections.income_statement import render_income_statement
from pdf.sections.mapping_trace import render_mapping_trace
from pdf.sections.notes import render_notes
from pdf.sections.ratios import render_quality_of_earnings, render_ratios
from pdf.sections.workpaper_signoff import render_workpaper_signoff
from pdf.styles import ClassicalColors, create_classical_styles
from security_utils import log_secure_operation

# ═══════════════════════════════════════════════════════════════════════════
# Diagnostic Intelligence Summary
# ═══════════════════════════════════════════════════════════════════════════


def generate_audit_report(
    audit_result: dict[str, Any],
    filename: str = "diagnostic",
    prepared_by: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    workpaper_date: Optional[str] = None,
    include_signoff: bool = False,
) -> bytes:
    """
    Generate a PDF diagnostic report from audit results.

    Sprint 53: Added workpaper fields for professional documentation.
    Sprint 7: Signoff deprecated -- gated by include_signoff (default False).
    """
    log_secure_operation("pdf_generator_init", f"Initializing Classical PDF generator for: {filename}")

    styles = create_classical_styles()
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=1.0 * inch,
        bottomMargin=1.0 * inch,
    )

    story: list = []

    # Cover page (shared chrome)
    from shared.report_chrome import ReportMetadata, build_cover_page, draw_page_footer, find_logo

    logo_path = find_logo()
    reference_number = generate_reference_number()

    metadata = ReportMetadata(
        title="DIAGNOSTIC INTELLIGENCE SUMMARY",
        subtitle=f"Analysis Report for {filename}",
        source_document=filename,
        reference=reference_number,
        prepared_by=prepared_by or "",
        reviewed_by=reviewed_by or "",
    )
    build_cover_page(story, styles, metadata, doc.width, logo_path)

    # Sections
    render_table_of_contents(story, styles)
    render_data_intake_summary(story, styles, audit_result, filename)
    render_executive_summary(story, styles, audit_result)

    story.append(LedgerRule(color=ClassicalColors.GOLD_INSTITUTIONAL, thickness=0.5, spaceBefore=12, spaceAfter=12))
    render_population_composition(story, styles, audit_result)

    story.append(LedgerRule(color=ClassicalColors.GOLD_INSTITUTIONAL, thickness=0.5, spaceBefore=12, spaceAfter=12))
    render_risk_summary(story, styles, audit_result)

    story.append(LedgerRule(color=ClassicalColors.GOLD_INSTITUTIONAL, thickness=0.5, spaceBefore=12, spaceAfter=12))
    render_anomaly_details(story, styles, audit_result)

    render_workpaper_signoff(
        story,
        styles,
        prepared_by,
        reviewed_by,
        workpaper_date=workpaper_date or datetime.now().strftime("%Y-%m-%d"),
        include_signoff=include_signoff,
    )

    render_limitations(story, styles)
    render_classical_footer(story, styles)

    # Page decorations
    def _on_first_page(canvas: Any, doc: Any) -> None:
        draw_diagnostic_watermark(canvas)
        draw_page_footer(canvas, doc)

    def _on_later_pages(canvas: Any, doc: Any) -> None:
        draw_diagnostic_watermark(canvas)
        draw_page_footer(canvas, doc)

    log_secure_operation("pdf_generate_start", "Starting Classical PDF generation")
    doc.build(story, onFirstPage=_on_first_page, onLaterPages=_on_later_pages)

    pdf_bytes = buffer.getvalue()
    buffer.close()

    log_secure_operation("pdf_generate_complete", f"Classical PDF generated: {len(pdf_bytes)} bytes")
    return pdf_bytes


# ═══════════════════════════════════════════════════════════════════════════
# Financial Statements PDF
# ═══════════════════════════════════════════════════════════════════════════


def generate_financial_statements_pdf(
    statements: Any,
    prepared_by: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    workpaper_date: Optional[str] = None,
    include_signoff: bool = False,
) -> bytes:
    """
    Generate a PDF with Balance Sheet, Income Statement, Cash Flow, Ratios,
    Notes, and Account Mapping Trace.

    Sprint 71: Financial Statements PDF using Renaissance Ledger aesthetic.
    """
    buffer = io.BytesIO()
    styles = create_classical_styles()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=1.0 * inch,
        bottomMargin=1.0 * inch,
    )

    story: list = []
    page_counter = [0]

    # Cover page
    from shared.report_chrome import ReportMetadata, build_cover_page, find_logo

    entity_name = statements.entity_name or "Financial Statements"
    fs_logo_path = find_logo()
    fs_metadata = ReportMetadata(
        title="FINANCIAL STATEMENTS",
        subtitle=entity_name,
        client_name=entity_name,
        engagement_period=statements.period_end or "",
        fiscal_year_end=statements.period_end or "",
    )
    build_cover_page(story, styles, fs_metadata, doc.width, fs_logo_path)

    # Header
    story.append(Paragraph("FINANCIAL STATEMENTS", styles["ClassicalTitle"]))
    story.append(Paragraph("\u2500\u2500\u2500 \u25c6 \u2500\u2500\u2500", styles["SectionOrnament"]))
    story.append(Paragraph(entity_name, styles["ClassicalSubtitle"]))

    if statements.period_end:
        story.append(Paragraph(f"Period Ending {statements.period_end}", styles["DocumentRef"]))

    ref_number = generate_reference_number()
    classical_date = format_classical_date()
    story.append(Paragraph(f"Prepared {classical_date}  \u00b7  Ref: {ref_number}", styles["DocumentRef"]))
    story.append(DoubleRule(width=6.5 * inch, color=ClassicalColors.GOLD_INSTITUTIONAL, spaceAfter=16))

    # Sections
    render_balance_sheet(story, styles, statements)
    render_income_statement(story, styles, statements)
    render_cash_flow(story, styles, statements)

    has_ratios = render_ratios(story, styles, statements)
    render_quality_of_earnings(story, styles, statements, has_ratios)

    render_notes(story, styles)
    render_mapping_trace(story, styles, statements)

    render_workpaper_signoff(
        story,
        styles,
        prepared_by,
        reviewed_by,
        workpaper_date=workpaper_date,
        include_signoff=include_signoff,
        section_ornament=True,
    )

    # Footer
    story.append(Spacer(1, 24))
    story.append(DoubleRule(width=6.5 * inch, color=ClassicalColors.LEDGER_RULE, thick=0.5, thin=0.25, spaceAfter=8))
    story.append(Paragraph('"Particularis de Computis et Scripturis"', styles["FooterMotto"]))
    story.append(Spacer(1, 8))
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    story.append(
        Paragraph(f"Generated by Paciolus\u00ae Financial Statement Builder  \u00b7  {timestamp}", styles["Footer"])
    )
    story.append(
        Paragraph(
            "Zero-Storage Architecture: Your financial data was processed in-memory and never stored.", styles["Footer"]
        )
    )

    # Build with page decorations
    def _fs_deco(canvas: Any, doc: Any) -> None:
        draw_fs_decorations(canvas, doc, page_counter)

    doc.build(story, onFirstPage=_fs_deco, onLaterPages=_fs_deco)

    pdf_bytes = buffer.getvalue()
    buffer.close()

    log_secure_operation(
        "financial_statements_pdf_complete", f"Financial statements PDF generated: {len(pdf_bytes)} bytes"
    )

    return pdf_bytes
