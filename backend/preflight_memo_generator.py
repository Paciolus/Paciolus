"""
Paciolus — Pre-Flight Report PDF Memo Generator
Sprint 283: Phase XXXVIII

Custom memo using memo_base.py primitives. Not TestingMemoConfig — preflight
is a diagnostic check, not a testing tool.

Sections: Header → Scope → Column Detection → Issues → Workpaper Sign-Off → Disclaimer
"""

from typing import Optional

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from pdf_generator import ClassicalColors, LedgerRule, create_leader_dots
from shared.framework_resolution import ResolvedFramework
from shared.memo_base import build_auditor_conclusion_block, build_disclaimer, build_intelligence_stamp, build_workpaper_signoff, create_memo_styles
from shared.report_chrome import ReportMetadata, build_cover_page, draw_page_footer, find_logo
from shared.scope_methodology import (
    build_authoritative_reference_block,
    build_methodology_statement,
    build_scope_statement,
)


def generate_preflight_memo(
    preflight_result: dict,
    filename: str = "preflight_report",
    client_name: Optional[str] = None,
    period_tested: Optional[str] = None,
    prepared_by: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    workpaper_date: Optional[str] = None,
    source_document_title: Optional[str] = None,
    source_context_note: Optional[str] = None,
    resolved_framework: ResolvedFramework = ResolvedFramework.FASB,
    include_signoff: bool = False,
) -> bytes:
    """Generate a Pre-Flight Report PDF memo.

    Args:
        preflight_result: Dict from PreFlightReport.to_dict()
        filename: Source filename
        client_name: Optional client name for header
        period_tested: Optional period label
        prepared_by: Preparer name for sign-off
        reviewed_by: Reviewer name for sign-off
        workpaper_date: Date for sign-off

    Returns:
        PDF bytes
    """
    import io

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=(8.5 * inch, 11 * inch),
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    doc_width = doc.width
    styles = create_memo_styles()
    story: list = []

    # ── Cover Page ──
    logo_path = find_logo()
    metadata = ReportMetadata(
        title="Data Quality Pre-Flight Report",
        client_name=client_name or "",
        engagement_period=period_tested or "",
        source_document=filename,
        source_document_title=source_document_title or "",
        source_context_note=source_context_note or "",
        reference="WP-PF-001",
    )
    build_cover_page(story, styles, metadata, doc_width, logo_path)

    # ── I. SCOPE ──
    story.append(Paragraph("I. Scope", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    readiness = preflight_result.get("readiness_score", 0)
    label = preflight_result.get("readiness_label", "Unknown")

    # Source document transparency (Sprint 6)
    if source_document_title and filename:
        source_line = create_leader_dots("Source", f"{source_document_title} ({filename})")
    elif source_document_title:
        source_line = create_leader_dots("Source", source_document_title)
    else:
        source_line = create_leader_dots("Source File", filename)

    scope_lines = [
        source_line,
        create_leader_dots("Total Rows", f"{preflight_result.get('row_count', 0):,}"),
        create_leader_dots("Total Columns", str(preflight_result.get("column_count", 0))),
        create_leader_dots("Readiness Score", f"{readiness:.1f} / 100"),
        create_leader_dots("Assessment", label),
    ]
    # Qualification: readiness reflects automated testing scope only
    scope_qualification = (
        "This readiness assessment reflects data completeness for automated testing "
        "procedures only and does not indicate whether the data is suitable for "
        "purposes beyond this platform's analytics."
    )
    if period_tested:
        scope_lines.insert(0, create_leader_dots("Period Tested", period_tested))

    for line in scope_lines:
        story.append(Paragraph(line, styles["MemoLeader"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph(scope_qualification, styles["MemoBodySmall"]))
    story.append(Spacer(1, 8))

    build_scope_statement(
        story,
        styles,
        doc_width,
        tool_domain="data_quality_preflight",
        framework=resolved_framework,
        domain_label="data quality assessment",
    )

    # ── II. COLUMN DETECTION ──
    columns = preflight_result.get("columns", [])
    if columns:
        story.append(Paragraph("II. Column Detection", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))

        col_data = [["Role", "Detected Column", "Confidence", "Status"]]
        for col in columns:
            conf = col.get("confidence", 0)
            col_data.append(
                [
                    col.get("role", "").title(),
                    col.get("detected_name") or "—",
                    f"{conf:.0%}",
                    col.get("status", "").replace("_", " ").title(),
                ]
            )

        col_table = Table(col_data, colWidths=[1.2 * inch, 2.5 * inch, 1.2 * inch, 1.5 * inch])
        col_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                    ("FONTNAME", (0, 1), (-1, -1), "Times-Roman"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                    ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                    ("LINEBELOW", (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("LEFTPADDING", (0, 0), (0, -1), 0),
                ]
            )
        )
        story.append(col_table)
        story.append(Spacer(1, 8))

    # ── III. DATA QUALITY ISSUES ──
    issues = preflight_result.get("issues", [])
    story.append(Paragraph("III. Data Quality Issues", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    if not issues:
        story.append(Paragraph("No data quality issues detected.", styles["MemoBody"]))
    else:
        issue_data = [["Category", "Severity", "Description", "Affected", "Remediation"]]
        for issue in sorted(issues, key=lambda i: {"high": 0, "medium": 1, "low": 2}.get(i.get("severity", "low"), 3)):
            issue_data.append(
                [
                    Paragraph(issue.get("category", "").replace("_", " ").title(), styles["MemoTableCell"]),
                    Paragraph(issue.get("severity", "").upper(), styles["MemoTableCell"]),
                    Paragraph(issue.get("message", ""), styles["MemoTableCell"]),
                    str(issue.get("affected_count", 0)),
                    Paragraph(issue.get("remediation", ""), styles["MemoTableCell"]),
                ]
            )

        issue_table = Table(
            issue_data, colWidths=[1.0 * inch, 0.7 * inch, 2.0 * inch, 0.6 * inch, 2.3 * inch], repeatRows=1
        )
        issue_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                    ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                    ("LINEBELOW", (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("LEFTPADDING", (0, 0), (0, -1), 0),
                ]
            )
        )
        story.append(issue_table)

    story.append(Spacer(1, 12))

    # ── Methodology & Authoritative References ──
    build_methodology_statement(
        story,
        styles,
        doc_width,
        tool_domain="data_quality_preflight",
        framework=resolved_framework,
        domain_label="data quality assessment",
    )
    build_authoritative_reference_block(
        story,
        styles,
        doc_width,
        tool_domain="data_quality_preflight",
        framework=resolved_framework,
        domain_label="data quality assessment",
    )

    # ── Practitioner Assessment ──
    build_auditor_conclusion_block(story, styles, doc_width)

    # ── Workpaper Sign-Off ──
    build_workpaper_signoff(
        story, styles, doc_width, prepared_by, reviewed_by, workpaper_date, include_signoff=include_signoff
    )

    # ── Intelligence Stamp ──
    build_intelligence_stamp(story, styles, client_name=client_name, period_tested=period_tested)

    # ── Disclaimer ──
    build_disclaimer(
        story,
        styles,
        domain="data quality assessment",
        isa_reference="ISA 500 (Audit Evidence) and ISA 330 (Auditor's Responses)",
    )

    doc.build(story, onFirstPage=draw_page_footer, onLaterPages=draw_page_footer)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
