"""
Anomaly Summary Report Generator — Sprint 101
Phase X: Engagement Layer

Generates a PDF anomaly summary report for an engagement.

Structure:
  1. Disclaimer (14pt bold, non-dismissible)
  2. Scope — tools run, dates, run counts
  3. Data Anomalies by Tool — follow-up items grouped by tool with severity
  4. [BLANK — For Auditor Assessment] — full-page blank section
  5. Sign-off (blank fields)

GUARDRAIL 3: This template does NOT mimic ISA 265 structure.
  - No "Material Weaknesses" section
  - No "Significant Deficiencies" section
  - No "Control Environment Assessment" section
  - The auditor section is deliberately BLANK.

ZERO-STORAGE: Reads engagement metadata and follow-up item narratives only.
"""

from io import BytesIO
from typing import Optional

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
)

from sqlalchemy.orm import Session

from models import Client
from engagement_model import Engagement, ToolRun, ToolName
from follow_up_items_model import FollowUpItem
from workpaper_index_generator import TOOL_LABELS
from pdf_generator import ClassicalColors, DoubleRule, LedgerRule, format_classical_date
from shared.memo_base import create_memo_styles


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DISCLAIMER_TEXT = (
    "DATA ANALYTICS REPORT \u2014 NOT AN AUDIT COMMUNICATION. "
    "This report lists data anomalies detected through automated testing. It does not "
    "constitute an audit opinion, internal control assessment, or management letter per "
    "ISA 265/PCAOB AS 1305. The auditor must perform additional procedures and provide "
    "all deficiency classifications in the blank section below."
)

AUDITOR_INSTRUCTIONS = (
    "The auditor should document their assessment of the data anomalies above, "
    "including any implications for the audit approach, control testing, or "
    "substantive procedures."
)


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

class AnomalySummaryGenerator:
    """Generates anomaly summary PDF for an engagement."""

    def __init__(self, db: Session):
        self.db = db

    def _verify_engagement_access(
        self, user_id: int, engagement_id: int
    ) -> Optional[Engagement]:
        return (
            self.db.query(Engagement)
            .join(Client, Engagement.client_id == Client.id)
            .filter(
                Engagement.id == engagement_id,
                Client.user_id == user_id,
            )
            .first()
        )

    def generate_pdf(self, user_id: int, engagement_id: int) -> bytes:
        """Generate anomaly summary PDF. Returns raw PDF bytes."""
        engagement = self._verify_engagement_access(user_id, engagement_id)
        if not engagement:
            raise ValueError("Engagement not found or access denied")

        client = self.db.query(Client).filter(Client.id == engagement.client_id).first()
        client_name = client.name if client else f"Client #{engagement.client_id}"

        # Gather data
        tool_runs = (
            self.db.query(ToolRun)
            .filter(ToolRun.engagement_id == engagement_id)
            .order_by(ToolRun.run_at.desc())
            .all()
        )

        follow_up_items = (
            self.db.query(FollowUpItem)
            .filter(FollowUpItem.engagement_id == engagement_id)
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
            styles, doc_width, client_name, engagement, tool_runs, follow_up_items,
        )

        doc.build(story)
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
    ) -> list:
        story = []

        # --- Section 0: Disclaimer banner (14pt bold, first page) ---
        disclaimer_style = ParagraphStyle(
            'DisclaimerBanner',
            fontName='Times-Bold',
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

        # --- Header ---
        story.append(Paragraph("Anomaly Summary Report", styles['MemoTitle']))
        story.append(Paragraph(client_name, styles['MemoSubtitle']))

        period_start = engagement.period_start.strftime("%b %d, %Y") if engagement.period_start else "N/A"
        period_end = engagement.period_end.strftime("%b %d, %Y") if engagement.period_end else "N/A"
        story.append(Paragraph(
            f"{format_classical_date()} &nbsp;&bull;&nbsp; Period: {period_start} \u2013 {period_end}",
            styles['MemoRef'],
        ))
        story.append(DoubleRule(doc_width))
        story.append(Spacer(1, 12))

        # --- Section 1: Scope ---
        story.append(Paragraph("I. SCOPE", styles['MemoSection']))
        story.append(LedgerRule(doc_width))

        # Group runs by tool
        runs_by_tool: dict[str, list] = {}
        for run in tool_runs:
            tool_val = run.tool_name.value if run.tool_name else "unknown"
            runs_by_tool.setdefault(tool_val, []).append(run)

        tools_run = len(runs_by_tool)
        total_runs = len(tool_runs)

        story.append(Paragraph(
            f"<b>Tools Executed:</b> {tools_run} of {len(ToolName)} available tools",
            styles['MemoBody'],
        ))
        story.append(Paragraph(
            f"<b>Total Tool Runs:</b> {total_runs}",
            styles['MemoBody'],
        ))

        if tool_runs:
            scope_data = [["Tool", "Runs", "Last Run"]]
            for tool_name in ToolName:
                runs = runs_by_tool.get(tool_name.value, [])
                if runs:
                    latest = max(runs, key=lambda r: r.run_at if r.run_at else r.id)
                    last_date = latest.run_at.strftime("%b %d, %Y %H:%M") if latest.run_at else "N/A"
                    scope_data.append([
                        TOOL_LABELS.get(tool_name, tool_name.value),
                        str(len(runs)),
                        last_date,
                    ])

            if len(scope_data) > 1:
                scope_table = Table(scope_data, colWidths=[3.0 * inch, 0.8 * inch, 2.5 * inch])
                scope_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
                    ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('TEXTCOLOR', (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                    ('LINEBELOW', (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                    ('LINEBELOW', (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                    ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                    ('LEFTPADDING', (0, 0), (0, -1), 0),
                ]))
                story.append(Spacer(1, 6))
                story.append(scope_table)

        story.append(Spacer(1, 12))

        # --- Section 2: Data Anomalies by Tool ---
        story.append(Paragraph("II. DATA ANOMALIES BY TOOL", styles['MemoSection']))
        story.append(LedgerRule(doc_width))

        if not follow_up_items:
            story.append(Paragraph(
                "No data anomalies were flagged during the analytical procedures.",
                styles['MemoBody'],
            ))
        else:
            # Group follow-up items by tool source
            items_by_tool: dict[str, list] = {}
            for item in follow_up_items:
                items_by_tool.setdefault(item.tool_source, []).append(item)

            # Summary counts
            severity_counts = {"high": 0, "medium": 0, "low": 0}
            for item in follow_up_items:
                sev = item.severity.value if item.severity else "medium"
                severity_counts[sev] = severity_counts.get(sev, 0) + 1

            story.append(Paragraph(
                f"<b>Total Anomalies:</b> {len(follow_up_items)} &nbsp;&nbsp;|&nbsp;&nbsp; "
                f"High: {severity_counts['high']} &nbsp;&nbsp;|&nbsp;&nbsp; "
                f"Medium: {severity_counts['medium']} &nbsp;&nbsp;|&nbsp;&nbsp; "
                f"Low: {severity_counts['low']}",
                styles['MemoBody'],
            ))
            story.append(Spacer(1, 8))

            # Per-tool anomaly tables
            for tool_source, items in sorted(items_by_tool.items()):
                tool_label = TOOL_LABELS.get(
                    ToolName(tool_source) if tool_source in [t.value for t in ToolName] else None,
                    tool_source,
                )
                story.append(Paragraph(
                    f"<b>{tool_label}</b> ({len(items)} items)",
                    styles['MemoBody'],
                ))

                anomaly_data = [["#", "Severity", "Description"]]
                for idx, item in enumerate(items, 1):
                    sev = item.severity.value.upper() if item.severity else "MEDIUM"
                    desc = item.description[:200]
                    anomaly_data.append([
                        str(idx),
                        sev,
                        Paragraph(desc, styles['MemoTableCell']),
                    ])

                anomaly_table = Table(
                    anomaly_data,
                    colWidths=[0.4 * inch, 0.8 * inch, 5.2 * inch],
                )
                anomaly_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
                    ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('TEXTCOLOR', (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                    ('LINEBELOW', (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                    ('LINEBELOW', (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                    ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                    ('LEFTPADDING', (0, 0), (0, -1), 0),
                ]))
                story.append(anomaly_table)
                story.append(Spacer(1, 10))

        # --- Section 3: BLANK — For Auditor Assessment ---
        story.append(PageBreak())
        story.append(Paragraph(
            "III. FOR PRACTITIONER ASSESSMENT",
            styles['MemoSection'],
        ))
        story.append(LedgerRule(doc_width))
        story.append(Paragraph(
            "<i>" + AUDITOR_INSTRUCTIONS + "</i>",
            styles['MemoBody'],
        ))
        story.append(Spacer(1, 24))

        # Blank ruled lines for auditor to write on
        for _ in range(20):
            story.append(LedgerRule(doc_width))
            story.append(Spacer(1, 18))

        # --- Sign-off (blank) ---
        story.append(Spacer(1, 12))
        story.append(LedgerRule(doc_width))
        signoff_data = [
            ["", "Name", "Date"],
            ["Prepared By:", "", ""],
            ["Reviewed By:", "", ""],
        ]
        signoff_table = Table(signoff_data, colWidths=[1.2 * inch, 3.0 * inch, 2.0 * inch])
        signoff_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('LINEBELOW', (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
            ('LINEBELOW', (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(signoff_table)

        # --- Disclaimer footer (repeated) ---
        story.append(Spacer(1, 16))
        story.append(Paragraph(DISCLAIMER_TEXT, styles['MemoDisclaimer']))

        return story
