"""
Engagement Risk Dashboard PDF Memo Generator (DASH-01)

Cross-report aggregation dashboard that summarizes risk findings across
multiple tool reports. Zero-storage compliant — results are passed in
per request, not retrieved from database.

Sections:
I. Engagement Summary (client, period, report count, HIGH findings, overall tier)
II. Report-by-Report Summary Table (sorted by risk score desc)
III. Cross-Report Risk Threads (configurable rules engine)
IV. Recommended Audit Response Priority
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
    RISK_SCALE_LEGEND,
    RISK_TIER_DISPLAY,
    build_disclaimer,
    build_intelligence_stamp,
    build_workpaper_signoff,
    create_memo_styles,
)
from shared.report_chrome import (
    ReportMetadata,
    build_cover_page,
    draw_page_footer,
    find_logo,
)


def generate_engagement_dashboard_memo(
    dashboard_result: dict[str, Any],
    *,
    client_name: Optional[str] = None,
    period_tested: Optional[str] = None,
    prepared_by: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    workpaper_date: Optional[str] = None,
    include_signoff: bool = False,
) -> bytes:
    """Generate the Engagement Risk Dashboard PDF.

    Args:
        dashboard_result: DashboardResult.to_dict() output
        client_name: Client/entity name
        period_tested: Engagement period
        prepared_by: Preparer name
        reviewed_by: Reviewer name
        workpaper_date: Date string

    Returns:
        PDF bytes
    """
    log_secure_operation("erd_memo_generate", "Generating engagement risk dashboard")

    styles = create_memo_styles()
    buffer = io.BytesIO()
    reference = generate_reference_number().replace("PAC-", "ERD-")

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=1.0 * inch,
        bottomMargin=0.8 * inch,
    )

    story: list = []

    # COVER PAGE
    logo_path = find_logo()
    metadata = ReportMetadata(
        title="Engagement Risk Dashboard",
        client_name=client_name or "",
        engagement_period=period_tested or "",
        source_document="",
        source_document_title="",
        source_context_note="",
        reference=reference,
    )
    build_cover_page(story, styles, metadata, doc.width, logo_path)

    # ═══════════════════════════════════════════════════════════
    # I. ENGAGEMENT SUMMARY
    # ═══════════════════════════════════════════════════════════
    story.append(Paragraph("I. Engagement Summary", styles["MemoSection"]))
    story.append(LedgerRule(doc.width))

    report_count = dashboard_result.get("report_count", 0)
    total_high = dashboard_result.get("total_high_findings", 0)
    overall_score = dashboard_result.get("overall_risk_score", 0)
    overall_tier = dashboard_result.get("overall_risk_tier", "low")

    base_tier_label, _ = RISK_TIER_DISPLAY.get(str(overall_tier).lower(), ("UNKNOWN", ClassicalColors.OBSIDIAN_500))
    tier_label = f"{base_tier_label} ({overall_score:.0f}/100)"

    summary_lines = [
        create_leader_dots("Reports Analyzed", str(report_count)),
        create_leader_dots("Overall Risk Score", f"{overall_score:.1f} / 100"),
        create_leader_dots("Overall Risk Tier", tier_label),
        create_leader_dots("Total High-Severity Findings", str(total_high)),
    ]
    if client_name:
        summary_lines.insert(0, create_leader_dots("Client", client_name))
    if period_tested:
        summary_lines.insert(1 if client_name else 0, create_leader_dots("Engagement Period", period_tested))

    for line in summary_lines:
        story.append(Paragraph(line, styles["MemoLeader"]))

    story.append(Paragraph(RISK_SCALE_LEGEND, styles["MemoBodySmall"]))
    story.append(Spacer(1, 8))

    # ═══════════════════════════════════════════════════════════
    # II. REPORT-BY-REPORT SUMMARY
    # ═══════════════════════════════════════════════════════════
    story.append(Paragraph("II. Report-by-Report Summary", styles["MemoSection"]))
    story.append(LedgerRule(doc.width))

    summaries = dashboard_result.get("report_summaries", [])
    if summaries:
        rpt_data = [["Report", "Risk Score", "Tier", "Flagged", "High", "Tests"]]
        for s in summaries:
            t_base, _ = RISK_TIER_DISPLAY.get(str(s.get("risk_tier", "low")).lower(), ("—", None))
            t_label = f"{t_base} ({s.get('risk_score', 0):.0f})" if t_base != "—" else "—"
            rpt_data.append(
                [
                    Paragraph(s.get("report_title", ""), styles["MemoTableCell"]),
                    f"{s.get('risk_score', 0):.1f}",
                    t_label,
                    str(s.get("total_flagged", 0)),
                    str(s.get("high_severity_count", 0)),
                    str(s.get("tests_run", 0)),
                ]
            )

        rpt_table = Table(
            rpt_data,
            colWidths=[2.4 * inch, 0.8 * inch, 0.8 * inch, 0.7 * inch, 0.6 * inch, 0.6 * inch],
            repeatRows=1,
        )
        rpt_table.setStyle(
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
        story.append(rpt_table)
    else:
        story.append(Paragraph("No report results provided.", styles["MemoBody"]))

    story.append(Spacer(1, 8))

    # ═══════════════════════════════════════════════════════════
    # III. CROSS-REPORT RISK THREADS
    # ═══════════════════════════════════════════════════════════
    story.append(Paragraph("III. Cross-Report Risk Threads", styles["MemoSection"]))
    story.append(LedgerRule(doc.width))

    threads = dashboard_result.get("risk_threads", [])
    if threads:
        story.append(
            Paragraph(
                f"{len(threads)} cross-report risk thread(s) were identified based on "
                "correlated findings across multiple reports:",
                styles["MemoBody"],
            )
        )
        story.append(Spacer(1, 4))

        for i, thread in enumerate(threads, 1):
            story.append(
                Paragraph(
                    f"<b>{i}. {thread.get('name', '')} ({thread.get('severity', 'medium').upper()})</b>",
                    styles["MemoBody"],
                )
            )
            story.append(Paragraph(thread.get("narrative", ""), styles["MemoBodySmall"]))
            indicators = thread.get("matched_conditions", [])
            if indicators:
                story.append(
                    Paragraph(
                        f"Evidence: {', '.join(indicators)}",
                        styles["MemoBodySmall"],
                    )
                )
            story.append(Spacer(1, 4))
    else:
        story.append(
            Paragraph(
                "No cross-report risk threads were identified. "
                "Individual report findings do not exhibit correlated patterns.",
                styles["MemoBody"],
            )
        )

    story.append(Spacer(1, 8))

    # ═══════════════════════════════════════════════════════════
    # IV. RECOMMENDED AUDIT RESPONSE PRIORITY
    # ═══════════════════════════════════════════════════════════
    story.append(Paragraph("IV. Recommended Audit Response Priority", styles["MemoSection"]))
    story.append(LedgerRule(doc.width))

    actions = dashboard_result.get("priority_actions", [])
    if actions:
        story.append(
            Paragraph(
                "Based on the aggregated findings, the following audit response actions "
                "are recommended in order of priority:",
                styles["MemoBody"],
            )
        )
        story.append(Spacer(1, 4))

        for i, action in enumerate(actions, 1):
            story.append(Paragraph(f"{i}. {action}", styles["MemoBody"]))
        story.append(Spacer(1, 4))

        story.append(
            Paragraph(
                "The auditor should evaluate each recommendation in the context of the "
                "engagement risk assessment and allocate audit resources accordingly.",
                styles["MemoBodySmall"],
            )
        )
    else:
        story.append(
            Paragraph(
                "No priority actions identified. All reports exhibit low risk profiles.",
                styles["MemoBody"],
            )
        )

    story.append(Spacer(1, 12))

    # WORKPAPER SIGN-OFF
    build_workpaper_signoff(
        story,
        styles,
        doc.width,
        prepared_by,
        reviewed_by,
        workpaper_date,
        include_signoff=include_signoff,
    )

    # INTELLIGENCE STAMP
    build_intelligence_stamp(story, styles, client_name=client_name, period_tested=period_tested)

    # DISCLAIMER
    build_disclaimer(
        story,
        styles,
        domain="engagement risk assessment",
        isa_reference="ISA 315 (Risk Assessment) and ISA 330 (Auditor's Responses)",
    )

    # Build PDF
    doc.build(story, onFirstPage=draw_page_footer, onLaterPages=draw_page_footer)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    log_secure_operation("erd_memo_complete", f"Engagement dashboard generated: {len(pdf_bytes)} bytes")
    return pdf_bytes
