"""
Anomaly Summary Report Generator — Sprint 101 / Sprint 515 Enrichment

Generates a PDF anomaly summary report for an engagement.

Structure:
  1. Disclaimer (14pt bold, non-dismissible)
  2. Cover page (full metadata: client, period, source, reference)
  3. Section I: Scope — tools executed/not executed, anomaly metrics, risk indicator
  4. Section II: Data Anomalies by Tool — cross-referenced findings + clean-result blocks
  5. Methodology & Authoritative References (AU-C/PCAOB auditing standards)
  6. Section III: Practitioner Assessment — per-anomaly response framework
  7. Section IV: Engagement Risk Assessment — computed risk indicator + narrative
  8. Sign-off block (DRAFT watermark until Section III complete)

GUARDRAIL 3: This template does NOT mimic ISA 265 structure.
  - No "Material Weaknesses" section
  - No "Significant Deficiencies" section
  - No "Control Environment Assessment" section
  - Section III response blocks are BLANK — auditor owns classification.

ZERO-STORAGE: Reads engagement metadata and follow-up item narratives only.
"""

from io import BytesIO
from typing import Optional

from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy.orm import Session

from engagement_model import Engagement, ToolName, ToolRun
from follow_up_items_model import FollowUpItem
from models import Client
from pdf_generator import ClassicalColors, LedgerRule, generate_reference_number
from shared.framework_resolution import ResolvedFramework
from shared.memo_base import create_memo_styles
from shared.report_chrome import ReportMetadata, build_cover_page, draw_page_footer, find_logo
from shared.scope_methodology import (
    build_methodology_statement,
    build_scope_statement,
)
from workpaper_index_generator import TOOL_LABELS

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DISCLAIMER_TEXT = (
    "DATA ANALYTICS REPORT \u2014 NOT AN AUDIT COMMUNICATION. "
    "This report lists data anomalies detected through automated testing. It does not "
    "constitute an audit opinion, internal control assessment, or management letter per "
    "ISA 265/PCAOB AS 1305. The auditor must perform additional procedures and provide "
    "all deficiency classifications in the assessment section below."
)

AUDITOR_INSTRUCTIONS = (
    "The auditor should document their assessment of the data anomalies above, "
    "including any implications for the audit approach, control testing, or "
    "substantive procedures."
)

# Cross-reference prefixes for each tool's workpaper
TOOL_CROSS_REFERENCES: dict[ToolName, str] = {
    ToolName.TRIAL_BALANCE: "WP-TBD-001",
    ToolName.MULTI_PERIOD: "WP-MPT-001",
    ToolName.JOURNAL_ENTRY_TESTING: "WP-JET-001",
    ToolName.AP_TESTING: "WP-APT-001",
    ToolName.BANK_RECONCILIATION: "WP-BRC-001",
    ToolName.PAYROLL_TESTING: "WP-PET-001",
    ToolName.THREE_WAY_MATCH: "WP-TWM-001",
    ToolName.REVENUE_TESTING: "WP-RRT-001",
    ToolName.AR_AGING: "WP-ARA-001",
    ToolName.FIXED_ASSET_TESTING: "WP-FAR-001",
    ToolName.INVENTORY_TESTING: "WP-INV-001",
    ToolName.STATISTICAL_SAMPLING: "WP-SSM-001",
    ToolName.FLUX_ANALYSIS: "WP-FEA-001",
}

# Auditing standards references (not FASB codification — these are audit procedure standards)
AUTHORITATIVE_REFERENCES = [
    ("AICPA", "AU-C \u00a7 265", "Communicating Internal Control Related Matters"),
    ("AICPA", "AU-C \u00a7 330", "Performing Audit Procedures in Response to Assessed Risks"),
    ("AICPA", "AU-C \u00a7 520", "Analytical Procedures"),
    ("PCAOB", "AS 1305", "Communications About Control Deficiencies"),
    ("PCAOB", "AS 2305", "Substantive Analytical Procedures"),
]


def _generate_reference() -> str:
    """Generate a unique ANS reference number."""
    return generate_reference_number().replace("PAC-", "ANS-")


def _compute_engagement_risk(
    high_count: int,
    medium_count: int,
    low_count: int,
    tools_not_run: int,
) -> tuple[str, int]:
    """Compute engagement risk indicator from anomaly profile.

    Returns (risk_label, total_score).
    """
    score = (high_count * 3) + (medium_count * 2) + (low_count * 1)
    coverage_penalty = int(tools_not_run * 1.5)
    total_score = score + coverage_penalty

    if total_score >= 15 or high_count >= 3:
        return "ELEVATED", total_score
    elif total_score >= 8 or high_count >= 1:
        return "MODERATE", total_score
    else:
        return "LOW", total_score


def _resolve_tool_name_from_source(tool_source: str) -> Optional[ToolName]:
    """Resolve a tool_source string to a ToolName enum value."""
    for tn in ToolName:
        if tn.value == tool_source:
            return tn
    return None


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------


class AnomalySummaryGenerator:
    """Generates anomaly summary PDF for an engagement."""

    def __init__(self, db: Session):
        self.db = db

    def _verify_engagement_access(self, user_id: int, engagement_id: int) -> Optional[Engagement]:
        return (
            self.db.query(Engagement)
            .join(Client, Engagement.client_id == Client.id)
            .filter(
                Engagement.id == engagement_id,
                Client.user_id == user_id,
            )
            .first()
        )

    def generate_pdf(
        self,
        user_id: int,
        engagement_id: int,
        resolved_framework: ResolvedFramework = ResolvedFramework.FASB,
    ) -> bytes:
        """Generate anomaly summary PDF. Returns raw PDF bytes."""
        engagement = self._verify_engagement_access(user_id, engagement_id)
        if not engagement:
            raise ValueError("Engagement not found or access denied")

        client = self.db.query(Client).filter(Client.id == engagement.client_id).first()
        client_name = client.name if client else f"Client #{engagement.client_id}"

        # Gather data (active only — exclude archived records)
        tool_runs = (
            self.db.query(ToolRun)
            .filter(
                ToolRun.engagement_id == engagement_id,
                ToolRun.archived_at.is_(None),
            )
            .order_by(ToolRun.run_at.desc())
            .all()
        )

        follow_up_items = (
            self.db.query(FollowUpItem)
            .filter(
                FollowUpItem.engagement_id == engagement_id,
                FollowUpItem.archived_at.is_(None),
            )
            .order_by(FollowUpItem.created_at.asc())
            .all()
        )

        # Build PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=0.75 * inch,
            rightMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )
        doc_width = letter[0] - 1.5 * inch

        styles = create_memo_styles()
        story = self._build_story(
            styles,
            doc_width,
            client_name,
            engagement,
            tool_runs,
            follow_up_items,
            resolved_framework=resolved_framework,
        )

        doc.build(story, onFirstPage=draw_page_footer, onLaterPages=draw_page_footer)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    def _build_story(
        self,
        styles: dict,
        doc_width: float,
        client_name: str,
        engagement: Engagement,
        tool_runs: list,
        follow_up_items: list,
        resolved_framework: ResolvedFramework = ResolvedFramework.FASB,
    ) -> list:
        story: list = []

        # --- Section 0: Disclaimer banner (above cover page) ---
        disclaimer_style = ParagraphStyle(
            "DisclaimerBanner",
            fontName="Times-Bold",
            fontSize=10,
            textColor=ClassicalColors.CLAY,
            alignment=TA_CENTER,
            leading=13,
            spaceAfter=12,
            spaceBefore=4,
            backColor=ClassicalColors.OATMEAL_PAPER,
            borderPadding=8,
        )
        story.append(Paragraph(DISCLAIMER_TEXT, disclaimer_style))
        story.append(Spacer(1, 8))

        # --- Cover Page ---
        period_start = engagement.period_start.strftime("%b %d, %Y") if engagement.period_start else "N/A"
        period_end = engagement.period_end.strftime("%b %d, %Y") if engagement.period_end else "N/A"
        period_desc = f"{period_start} \u2013 {period_end}"

        reference = _generate_reference()

        logo_path = find_logo()
        metadata = ReportMetadata(
            title="Anomaly Summary Report",
            client_name=client_name,
            engagement_period=period_desc,
            source_document="All executed diagnostic tool outputs",
            source_document_title="Aggregated from individual tool runs",
            reference=reference,
        )
        build_cover_page(story, styles, metadata, doc_width, logo_path)

        # --- Pre-compute data structures ---
        runs_by_tool: dict[str, list] = {}
        for run in tool_runs:
            tool_val = run.tool_name.value if run.tool_name else "unknown"
            runs_by_tool.setdefault(tool_val, []).append(run)

        executed_tools = {ToolName(k) for k in runs_by_tool if k in [t.value for t in ToolName]}
        not_executed_tools = [t for t in ToolName if t not in executed_tools]

        tools_run_count = len(executed_tools)
        total_runs = len(tool_runs)

        items_by_tool: dict[str, list] = {}
        for item in follow_up_items:
            items_by_tool.setdefault(item.tool_source, []).append(item)

        severity_counts = {"high": 0, "medium": 0, "low": 0}
        for item in follow_up_items:
            sev = item.severity.value if item.severity else "medium"
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        # Tools with runs but no anomalies
        tools_with_findings = {s for s in items_by_tool}
        clean_result_tools = [t for t in executed_tools if t.value not in tools_with_findings]

        risk_label, risk_score = _compute_engagement_risk(
            severity_counts["high"],
            severity_counts["medium"],
            severity_counts["low"],
            len(not_executed_tools),
        )

        # --- Section I: Scope ---
        story.append(Paragraph("I. Scope", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))

        # Engagement-level summary metrics
        story.append(
            Paragraph(
                f"<b>Tools Executed:</b> {tools_run_count} of {len(ToolName)} available tools",
                styles["MemoBody"],
            )
        )
        story.append(Paragraph(f"<b>Total Tool Runs:</b> {total_runs}", styles["MemoBody"]))
        story.append(
            Paragraph(
                f"<b>Total Anomalies Identified:</b> {len(follow_up_items)} &nbsp;&nbsp;|&nbsp;&nbsp; "
                f"High: {severity_counts['high']} &nbsp;&nbsp;|&nbsp;&nbsp; "
                f"Medium: {severity_counts['medium']} &nbsp;&nbsp;|&nbsp;&nbsp; "
                f"Low: {severity_counts['low']}",
                styles["MemoBody"],
            )
        )
        if clean_result_tools:
            clean_names = ", ".join(TOOL_LABELS.get(t, t.value) for t in clean_result_tools)
            story.append(
                Paragraph(
                    f"<b>Tools with Clean Results:</b> {len(clean_result_tools)} ({clean_names})",
                    styles["MemoBody"],
                )
            )
        story.append(
            Paragraph(
                f"<b>Engagement Risk Indicator:</b> {risk_label}",
                styles["MemoBody"],
            )
        )
        story.append(Spacer(1, 6))

        # Executed tools table
        if executed_tools:
            scope_data = [["Tool", "Runs", "Last Run"]]
            for tool_name in ToolName:
                runs = runs_by_tool.get(tool_name.value, [])
                if runs:
                    latest = max(runs, key=lambda r: r.run_at if r.run_at else r.id)
                    last_date = latest.run_at.strftime("%b %d, %Y %H:%M") if latest.run_at else "N/A"
                    scope_data.append(
                        [
                            TOOL_LABELS.get(tool_name, tool_name.value),
                            str(len(runs)),
                            last_date,
                        ]
                    )

            if len(scope_data) > 1:
                scope_table = Table(scope_data, colWidths=[3.0 * inch, 0.8 * inch, 2.5 * inch])
                scope_table.setStyle(
                    TableStyle(
                        [
                            ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                            ("FONTNAME", (0, 1), (-1, -1), "Times-Roman"),
                            ("FONTSIZE", (0, 0), (-1, -1), 9),
                            ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                            ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                            ("LINEBELOW", (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                            ("ALIGN", (1, 0), (1, -1), "CENTER"),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("TOPPADDING", (0, 0), (-1, -1), 3),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                            ("LEFTPADDING", (0, 0), (0, -1), 0),
                        ]
                    )
                )
                story.append(Spacer(1, 4))
                story.append(scope_table)

        # Not-executed tools table
        if not_executed_tools:
            story.append(Spacer(1, 10))
            story.append(Paragraph("<b>Tools Not Executed:</b>", styles["MemoBody"]))

            not_exec_data = [["Tool", "Status", "Note"]]
            for tool_name in not_executed_tools:
                not_exec_data.append(
                    [
                        TOOL_LABELS.get(tool_name, tool_name.value),
                        "Not Run",
                        "\u2014",
                    ]
                )

            not_exec_table = Table(not_exec_data, colWidths=[3.0 * inch, 1.0 * inch, 2.3 * inch])
            not_exec_table.setStyle(
                TableStyle(
                    [
                        ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                        ("FONTNAME", (0, 1), (-1, -1), "Times-Roman"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                        ("TEXTCOLOR", (1, 1), (1, -1), ClassicalColors.OBSIDIAN_500),
                        ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                        ("LINEBELOW", (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                        ("ALIGN", (1, 0), (1, -1), "CENTER"),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                        ("LEFTPADDING", (0, 0), (0, -1), 0),
                    ]
                )
            )
            story.append(not_exec_table)
            story.append(Spacer(1, 4))
            story.append(
                Paragraph(
                    "<i>Tools listed as \u201cNot Run\u201d were not executed for this engagement. "
                    "The auditor should consider whether the scope of analytics coverage is "
                    "sufficient given the identified risk profile. Unexecuted tools may represent "
                    "coverage gaps requiring alternative procedures.</i>",
                    styles["MemoBodySmall"],
                )
            )

        story.append(Spacer(1, 12))

        build_scope_statement(
            story,
            styles,
            doc_width,
            tool_domain="anomaly_summary",
            framework=resolved_framework,
            domain_label="engagement anomaly summary",
        )

        # --- Section II: Data Anomalies by Tool ---
        story.append(Paragraph("II. Data Anomalies by Tool", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))

        if not follow_up_items and not clean_result_tools:
            story.append(
                Paragraph(
                    "No data anomalies were flagged during the analytical procedures.",
                    styles["MemoBody"],
                )
            )
        else:
            # Summary counts
            if follow_up_items:
                story.append(
                    Paragraph(
                        f"<b>Total Anomalies:</b> {len(follow_up_items)} &nbsp;&nbsp;|&nbsp;&nbsp; "
                        f"High: {severity_counts['high']} &nbsp;&nbsp;|&nbsp;&nbsp; "
                        f"Medium: {severity_counts['medium']} &nbsp;&nbsp;|&nbsp;&nbsp; "
                        f"Low: {severity_counts['low']}",
                        styles["MemoBody"],
                    )
                )
                story.append(Spacer(1, 8))

            # Per-tool anomaly tables (tools WITH findings)
            for tool_source, items in sorted(items_by_tool.items()):
                resolved_tn = _resolve_tool_name_from_source(tool_source)
                tool_label = TOOL_LABELS.get(resolved_tn, tool_source) if resolved_tn else tool_source
                cross_ref = TOOL_CROSS_REFERENCES.get(resolved_tn, "") if resolved_tn else ""

                header_text = f"<b>{tool_label}</b> ({len(items)} items)"
                if cross_ref:
                    header_text += f" &nbsp;\u2014&nbsp; {cross_ref}"
                story.append(Paragraph(header_text, styles["MemoBody"]))

                # Table with Ref column
                anomaly_data = [["Ref", "#", "Severity", "Description"]]
                for idx, item in enumerate(items, 1):
                    sev = item.severity.value.upper() if item.severity else "MEDIUM"
                    desc = item.description[:200]
                    anomaly_data.append(
                        [
                            cross_ref,
                            str(idx),
                            sev,
                            Paragraph(desc, styles["MemoTableCell"]),
                        ]
                    )

                anomaly_table = Table(
                    anomaly_data,
                    colWidths=[1.0 * inch, 0.4 * inch, 1.0 * inch, 4.0 * inch],
                )
                anomaly_table.setStyle(
                    TableStyle(
                        [
                            ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                            ("FONTNAME", (0, 1), (-1, -1), "Times-Roman"),
                            ("FONTSIZE", (0, 0), (-1, -1), 9),
                            ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                            ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                            ("LINEBELOW", (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                            ("ALIGN", (1, 0), (1, -1), "CENTER"),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("TOPPADDING", (0, 0), (-1, -1), 3),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                            ("LEFTPADDING", (0, 0), (0, -1), 0),
                        ]
                    )
                )
                story.append(anomaly_table)
                story.append(Spacer(1, 10))

            # Clean-result tool blocks (tools with runs but no anomalies)
            if clean_result_tools:
                for tool_name in clean_result_tools:
                    tool_label = TOOL_LABELS.get(tool_name, tool_name.value)
                    cross_ref = TOOL_CROSS_REFERENCES.get(tool_name, "")
                    ref_note = f" See {cross_ref} for detail." if cross_ref else ""
                    story.append(
                        Paragraph(
                            f"<b>{tool_label}</b> (0 items)",
                            styles["MemoBody"],
                        )
                    )
                    story.append(LedgerRule(doc_width))
                    story.append(
                        Paragraph(
                            f"\u2713 No anomalies identified. Population passed all configured "
                            f"test thresholds.{ref_note}",
                            styles["MemoBody"],
                        )
                    )
                    story.append(Spacer(1, 8))

        # --- Methodology & Authoritative References ---
        build_methodology_statement(
            story,
            styles,
            doc_width,
            tool_domain="anomaly_summary",
            framework=resolved_framework,
            domain_label="engagement anomaly summary",
        )

        # Auditing standards references (not FASB codification)
        story.append(Paragraph("Authoritative References", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))

        ref_data = [["Body", "Reference", "Topic"]]
        for body, ref_id, topic in AUTHORITATIVE_REFERENCES:
            ref_data.append(
                [
                    Paragraph(body, styles["MemoTableCell"]),
                    Paragraph(ref_id, styles["MemoTableCell"]),
                    Paragraph(topic, styles["MemoTableCell"]),
                ]
            )

        ref_table = Table(ref_data, colWidths=[0.8 * inch, 1.4 * inch, 4.2 * inch])
        ref_table.setStyle(
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
        story.append(ref_table)
        story.append(Spacer(1, 8))

        # --- Section III: Practitioner Assessment ---
        story.append(PageBreak())
        story.append(Paragraph("III. Practitioner Assessment", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))

        # Completion tracker
        total_anomalies = len(follow_up_items)
        story.append(
            Paragraph(
                f"<b>Total Anomalies Requiring Response:</b> {total_anomalies}",
                styles["MemoBody"],
            )
        )
        story.append(
            Paragraph(
                "<b>Assessments Completed:</b> 0",
                styles["MemoBody"],
            )
        )
        story.append(
            Paragraph(
                "<b>Deficiency Classifications Made:</b> 0",
                styles["MemoBody"],
            )
        )
        if total_anomalies > 0:
            story.append(Spacer(1, 4))
            story.append(
                Paragraph(
                    "<i>Section III is INCOMPLETE. All anomalies require practitioner "
                    "assessment before this report may be included in the engagement file.</i>",
                    styles["MemoBodySmall"],
                )
            )
        story.append(Spacer(1, 12))

        if follow_up_items:
            # Per-anomaly response blocks
            anomaly_counter = 0
            for tool_source, items in sorted(items_by_tool.items()):
                resolved_tn = _resolve_tool_name_from_source(tool_source)
                cross_ref = TOOL_CROSS_REFERENCES.get(resolved_tn, "") if resolved_tn else ""

                for idx, item in enumerate(items, 1):
                    anomaly_counter += 1
                    sev = item.severity.value.upper() if item.severity else "MEDIUM"
                    desc = item.description[:200]

                    # Response block header
                    tool_label = TOOL_LABELS.get(resolved_tn, tool_source) if resolved_tn else tool_source
                    header = f"<b>Anomaly {anomaly_counter}</b> ({sev}) \u2014 {tool_label}"
                    if cross_ref:
                        header += f" [{cross_ref}]"
                    story.append(Paragraph(header, styles["MemoBody"]))
                    story.append(Paragraph(desc, styles["MemoBodySmall"]))
                    story.append(Spacer(1, 4))

                    # Structured response fields
                    response_data = [
                        ["Field", "Response"],
                        [
                            Paragraph("Management Explanation", styles["MemoTableCell"]),
                            Paragraph("[PRACTITIONER TO COMPLETE]", styles["MemoTableCell"]),
                        ],
                        [
                            Paragraph("Implication for Audit", styles["MemoTableCell"]),
                            Paragraph(
                                "[ ] No change to planned procedures<br/>"
                                "[ ] Expand scope of substantive testing<br/>"
                                "[ ] Add control testing procedures<br/>"
                                "[ ] Escalate to engagement partner<br/>"
                                "[ ] Refer to specialist",
                                styles["MemoTableCell"],
                            ),
                        ],
                        [
                            Paragraph("Deficiency Classification", styles["MemoTableCell"]),
                            Paragraph(
                                "[ ] Not a deficiency<br/>"
                                "[ ] Control deficiency<br/>"
                                "[ ] Significant deficiency<br/>"
                                "[ ] Material weakness<br/>"
                                "[ ] Inconclusive \u2014 requires further investigation<br/>"
                                "<i>(Per ISA 265 / PCAOB AS 1305)</i>",
                                styles["MemoTableCell"],
                            ),
                        ],
                        [
                            Paragraph("Follow-Up Procedures", styles["MemoTableCell"]),
                            Paragraph("[PRACTITIONER TO COMPLETE]", styles["MemoTableCell"]),
                        ],
                        [
                            Paragraph("Initials / Date", styles["MemoTableCell"]),
                            Paragraph("___ / ___/___/______", styles["MemoTableCell"]),
                        ],
                    ]

                    response_table = Table(
                        response_data,
                        colWidths=[1.8 * inch, 4.6 * inch],
                    )
                    response_table.setStyle(
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
                    story.append(response_table)
                    story.append(Spacer(1, 12))

            # Aggregate Deficiency Classification Summary
            story.append(
                Paragraph(
                    "Aggregate Deficiency Classification Summary (DRAFT)",
                    styles["MemoSection"],
                )
            )
            story.append(LedgerRule(doc_width))
            story.append(
                Paragraph(
                    "<i>This table auto-populates as the practitioner completes assessments above. "
                    "Marked as DRAFT until all anomalies are assessed.</i>",
                    styles["MemoBodySmall"],
                )
            )

            classification_data = [
                ["Classification", "Count", "Anomaly IDs"],
                ["Material Weakness", "\u2014", "\u2014"],
                ["Significant Deficiency", "\u2014", "\u2014"],
                ["Control Deficiency", "\u2014", "\u2014"],
                ["Not a Deficiency", "\u2014", "\u2014"],
                ["Inconclusive", "\u2014", "\u2014"],
            ]

            classification_table = Table(
                classification_data,
                colWidths=[2.4 * inch, 0.8 * inch, 3.2 * inch],
            )
            classification_table.setStyle(
                TableStyle(
                    [
                        ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                        ("FONTNAME", (0, 1), (-1, -1), "Times-Roman"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                        ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                        ("LINEBELOW", (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                        ("ALIGN", (1, 0), (1, -1), "CENTER"),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                        ("LEFTPADDING", (0, 0), (0, -1), 0),
                    ]
                )
            )
            story.append(Spacer(1, 4))
            story.append(classification_table)
        else:
            story.append(
                Paragraph(
                    "No anomalies were identified. No practitioner assessment is required.",
                    styles["MemoBody"],
                )
            )

        # --- Section IV: Engagement Risk Assessment ---
        story.append(Spacer(1, 16))
        story.append(Paragraph("IV. Engagement Risk Assessment", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))

        # Risk indicator box
        risk_box_data = [
            [
                Paragraph(
                    f"<b>ENGAGEMENT RISK INDICATOR: {risk_label}</b>",
                    ParagraphStyle(
                        "_RiskLabel",
                        fontName="Times-Bold",
                        fontSize=11,
                        textColor=ClassicalColors.OBSIDIAN_DEEP,
                        alignment=TA_LEFT,
                        leading=14,
                    ),
                )
            ]
        ]
        risk_box = Table(risk_box_data, colWidths=[doc_width])
        risk_box_bg = ClassicalColors.OATMEAL_PAPER
        risk_box.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), risk_box_bg),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("LEFTPADDING", (0, 0), (-1, -1), 12),
                    ("BOX", (0, 0), (-1, -1), 1, ClassicalColors.OBSIDIAN_DEEP),
                ]
            )
        )
        story.append(risk_box)
        story.append(Spacer(1, 8))

        # Risk details
        high_count = severity_counts["high"]
        not_run_count = len(not_executed_tools)

        risk_details: list[str] = []
        if high_count > 0:
            risk_details.append(f"{high_count} High-severity anomalies identified")
        if not_run_count > 0:
            risk_details.append(f"{not_run_count} of {len(ToolName)} tools not executed")
        if len(follow_up_items) > 0:
            risk_details.append(f"{len(follow_up_items)} total anomalies across {len(items_by_tool)} tools")

        for detail in risk_details:
            story.append(Paragraph(f"\u2022 {detail}", styles["MemoBody"]))

        story.append(Spacer(1, 8))

        # Narrative
        if follow_up_items or not_executed_tools:
            narrative_parts = []
            narrative_parts.append(f"The engagement risk indicator of {risk_label} reflects ")
            if high_count > 0:
                narrative_parts.append(f"the combination of {high_count} High-severity anomalies ")
            if not_run_count > 0:
                if high_count > 0:
                    narrative_parts.append("and ")
                narrative_parts.append(
                    f"incomplete tool coverage ({not_run_count} of {len(ToolName)} tools not executed). "
                )
            elif high_count > 0:
                narrative_parts.append("identified across the executed tool suite. ")
            narrative_parts.append(
                "The auditor should consider whether the current audit plan provides "
                "sufficient coverage given the identified risk profile, and should "
                "prioritize resolution of High-severity items before finalizing "
                "substantive procedures."
            )
            story.append(
                Paragraph(
                    "<i>" + "".join(narrative_parts) + "</i>",
                    styles["MemoBody"],
                )
            )
        else:
            story.append(
                Paragraph(
                    "<i>No anomalies were identified and all available tools were executed. "
                    "The engagement risk indicator is LOW.</i>",
                    styles["MemoBody"],
                )
            )

        # --- Sign-Off Block ---
        story.append(Spacer(1, 20))
        story.append(Paragraph("Sign-Off", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))

        # DRAFT watermark note
        if total_anomalies > 0:
            story.append(
                Paragraph(
                    "<b>DRAFT \u2014 INCOMPLETE:</b> This report is in draft status until all "
                    "Section III practitioner assessments are completed.",
                    ParagraphStyle(
                        "_DraftNote",
                        fontName="Times-Bold",
                        fontSize=9,
                        textColor=ClassicalColors.CLAY,
                        spaceAfter=8,
                    ),
                )
            )

        signoff_data = [
            ["Role", "Name", "Signature", "Date"],
            ["Prepared by", "", "", ""],
            ["Reviewed by", "", "", ""],
            ["Partner", "", "", ""],
        ]

        signoff_table = Table(
            signoff_data,
            colWidths=[1.2 * inch, 2.0 * inch, 2.0 * inch, 1.2 * inch],
        )
        signoff_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                    ("FONTNAME", (0, 1), (-1, -1), "Times-Roman"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                    ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                    ("LINEBELOW", (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (0, -1), 0),
                ]
            )
        )
        story.append(signoff_table)

        # No trailing standalone disclaimer — prevents phantom blank page.
        # The disclaimer is already rendered via draw_page_footer on every page
        # and via the banner at the top of page 1.

        return story
