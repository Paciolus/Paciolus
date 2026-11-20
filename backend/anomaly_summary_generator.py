"""
Anomaly Summary Report Generator — Sprint 101 / Sprint 515 Enrichment / Sprint 887

Generates a PDF anomaly summary report for an engagement.

Structure:
  1. Disclaimer (14pt bold, non-dismissible)
  2. Cover page (full metadata: client, period, source, reference)
  3. Section I: Scope — captured follow-up items, follow-up item points, one result per catalog tool
  4. Section II: Captured Follow-Up Items by Tool
  5. Methodology & Authoritative References (AU-C/PCAOB auditing standards)
  6. Section III: Practitioner Worksheet — blank for the firm to complete by default;
     optionally filled from the dispositions and notes saved in Paciolus
  7. Section IV: Follow-Up Item Points — the points, their weights and band edges

Sprint 887 (review OUT-20, OUT-21): a tool is described from its latest
successful run and that run's recorded flag count — failed, not evaluated,
results unavailable, no exceptions flagged, or n items flagged — never as
"clean" from the absence of follow-up items. The engagement-level figure is
"Follow-Up Item Points": a weighted count of captured follow-up items plus a
coverage term, printed as points with its weights and band edges. It is not a
risk assessment and uses no risk or testing-tier words.

GUARDRAIL 3: This template does NOT mimic ISA 265 structure.
  - No "Material Weaknesses" section
  - No "Significant Deficiencies" section
  - No "Control Environment Assessment" section
  - Section III response fields are BLANK unless the firm asks for its own saved
    dispositions — the auditor owns classification.

ZERO-STORAGE: Reads engagement metadata and follow-up item narratives only.
"""

from datetime import datetime
from typing import Optional

from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from engagement_model import Engagement, ToolName, ToolRun, ToolRunStatus
from follow_up_items_model import FollowUpDisposition, FollowUpItem
from models import Client
from pdf import ClassicalColors, LedgerRule, generate_reference_number
from shared.framework_resolution import ResolvedFramework
from shared.memo_base import MemoContext, render_memo
from shared.report_chrome import (
    ReportMetadata,
    build_cover_page,
    find_logo,
)
from shared.report_styles import ledger_table_style
from shared.safe_paragraph import Paragraph, user_text
from shared.scope_methodology import (
    build_methodology_statement,
    build_scope_statement,
)
from tools_registry import MARKETING_AUDIT_TOOL_COUNT, TOOLS

# Slugs of the tools the catalog is sold as, i.e. the set MARKETING_AUDIT_TOOL_COUNT
# counts. Used to keep the coverage numerator and denominator over the same set.
CATALOG_TOOL_SLUGS: frozenset[str] = frozenset(t.slug for t in TOOLS if t.is_marketing_audit_tool)
from workpaper_index_generator import TOOL_LABELS

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DISCLAIMER_TEXT = (
    "DATA ANALYTICS REPORT — NOT AN AUDIT COMMUNICATION. "
    "This report lists data anomalies detected through automated testing. It does not "
    "constitute an audit opinion, internal control assessment, or management letter per "  # allow-deny-phrase: disclaiming what the report is NOT (ISA 265 negative use)
    "ISA 265/PCAOB AS 1305. Classification of these items as deficiencies, significant "  # allow-deny-phrase: disclaimer reserving classification to the auditor (ISA 265 negative use)
    "deficiencies, or material weaknesses is a matter of auditor judgment and is "  # allow-deny-phrase: disclaimer reserving classification to the auditor (ISA 265 negative use)
    "outside the scope of this report."
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
    # Sprint 787 — the Sprint 689 tools
    ToolName.SOD_CHECKER: "WP-SOD-001",
    ToolName.INTERCOMPANY_ELIMINATION: "WP-ICE-001",
    ToolName.W2_RECONCILIATION: "WP-W23-001",
    ToolName.FORM_1099: "WP-T99-001",
    ToolName.BOOK_TO_TAX: "WP-BTT-001",
    ToolName.CASH_FLOW_PROJECTOR: "WP-CFP-001",
}

# Auditing standards references (not FASB codification — these are audit procedure standards)
AUTHORITATIVE_REFERENCES = [
    ("AICPA", "AU-C § 265", "Communicating Internal Control Related Matters"),
    ("AICPA", "AU-C § 330", "Performing Audit Procedures in Response to Assessed Risks"),
    ("AICPA", "AU-C § 520", "Analytical Procedures"),
    ("PCAOB", "AS 1305", "Communications About Control Deficiencies"),  # allow-deny-phrase: AS 1305 title
    ("PCAOB", "AS 2305", "Substantive Analytical Procedures"),
]

# Sprint 887 (OUT-21, CEO 2026-11-20): Follow-Up Item Points. Weights per captured
# follow-up item by severity, plus a coverage term per catalog tool not run; the
# total is rounded down. Bands are named by their range only and depend on the
# points alone (the old "any 1 / any 3 high items" overrides are gone).
POINT_WEIGHTS: dict[str, int] = {"high": 3, "medium": 2, "low": 1}
POINTS_PER_TOOL_NOT_RUN = 1.5
# (lowest points in the band, label), highest band first.
POINT_BANDS: tuple[tuple[int, str], ...] = (
    (15, "15 points or more"),
    (8, "8–14 points"),
    (0, "Under 8 points"),
)
POINTS_BASIS_NOTE = (
    "Weights: 3 per high-severity, 2 per medium-severity and 1 per low-severity captured follow-up item; "
    "1.5 per catalog tool not run (total rounded down). "
    "Bands: under 8 points | 8–14 points | 15 points or more. "
    "The points count captured follow-up items and tool coverage; the auditor evaluates what they mean."
)

# Sprint 887 (OUT-20): the screen's disposition labels (frontend types/engagement.ts).
DISPOSITION_LABELS: dict[str, str] = {
    "not_reviewed": "Not Reviewed",
    "investigated_no_issue": "Investigated — No Issue",
    "investigated_adjustment_posted": "Investigated — Adjustment Posted",
    "investigated_further_review": "Investigated — Further Review",
    "immaterial": "Immaterial",
}

_TO_COMPLETE = "[FIRM TO COMPLETE]"


def _generate_reference() -> str:
    """Generate a unique ANS reference number."""
    return generate_reference_number("ANS")


def _compute_follow_up_points(
    high_count: int,
    medium_count: int,
    low_count: int,
    tools_not_run: int,
) -> tuple[int, str]:
    """Follow-Up Item Points and their band (Sprint 887 / OUT-21).

    ``tools_not_run`` counts catalog tools with no run on the engagement, so an
    engagement with no captured items can still carry points from coverage alone —
    which is why the memo prints the weights beside the figure.
    """
    points = (
        high_count * POINT_WEIGHTS["high"]
        + medium_count * POINT_WEIGHTS["medium"]
        + low_count * POINT_WEIGHTS["low"]
        + int(tools_not_run * POINTS_PER_TOOL_NOT_RUN)
    )
    band = next(label for floor, label in POINT_BANDS if points >= floor)
    return points, band


def _items_phrase(n: int) -> str:
    return f"{n:,} captured follow-up item{'' if n == 1 else 's'}"


def _tool_result(runs: list, captured: int) -> str:
    """One tool's result, from its latest successful run (Sprint 887 / OUT-20).

    A tool is never described as clean from the absence of follow-up items: a
    failed run, a run recorded without its flag count, and a run that flagged
    items nobody captured each print as what they are.
    """
    if not runs:
        return "Not evaluated — no run recorded for this engagement"
    completed = [r for r in runs if r.status == ToolRunStatus.COMPLETED]
    if not completed:
        n = len(runs)
        return f"Failed — {n} run{'' if n == 1 else 's'}, none completed; {_items_phrase(captured)}"
    latest = max(completed, key=lambda r: (r.run_at or datetime.min, r.run_number))
    when = latest.run_at.strftime("%b %d, %Y") if latest.run_at else "date not recorded"
    flag_count = getattr(latest, "flag_count", None)
    if flag_count is None:
        state = f"Results unavailable — the latest successful run ({when}) was recorded without its flag count"
    elif flag_count == 0:
        state = f"No exceptions flagged (latest successful run, {when})"
    else:
        state = f"{flag_count:,} item{'' if flag_count == 1 else 's'} flagged (latest successful run, {when})"
    return f"{state}; {_items_phrase(captured)}"


def _resolve_tool_name_from_source(tool_source: str) -> Optional[ToolName]:
    """Resolve a tool_source string to a ToolName enum value."""
    for tn in ToolName:
        if tn.value == tool_source:
            return tn
    return None


def _recorded_on(item: FollowUpItem) -> str:
    stamp = getattr(item, "updated_at", None) or getattr(item, "created_at", None)
    return f" (last recorded in Paciolus on {stamp.strftime('%b %d, %Y')})" if stamp else ""


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------


class AnomalySummaryGenerator:
    """Generates anomaly summary PDF for an engagement."""

    def __init__(self, db: Session):
        self.db = db

    def _verify_engagement_access(self, user_id: int, engagement_id: int) -> Optional[Engagement]:
        from engagement_manager import EngagementManager

        return EngagementManager(self.db).get_engagement(user_id, engagement_id)

    def generate_pdf(
        self,
        user_id: int,
        engagement_id: int,
        resolved_framework: ResolvedFramework = ResolvedFramework.FASB,
        fill_from_saved: bool = False,
    ) -> bytes:
        """Generate anomaly summary PDF. Returns raw PDF bytes.

        Sprint 679 (completion): reads the active ``PDFBrandingContext``
        via ``current_pdf_branding()`` — Enterprise firms get their logo
        on the cover and their header/footer on every non-cover page.
        Route handlers wrap this call in ``apply_pdf_branding(...)``.

        Sprint 887: ``fill_from_saved`` fills Section III from the dispositions
        and notes saved in Paciolus; by default it is a blank worksheet.
        """
        engagement = self._verify_engagement_access(user_id, engagement_id)
        if not engagement:
            raise ValueError("Engagement not found or access denied")

        client = self.db.query(Client).filter(Client.id == engagement.client_id).first()
        client_name = client.name if client else f"Client #{engagement.client_id}"
        return self.generate_pdf_for_engagement(engagement, client_name, resolved_framework, fill_from_saved)

    def generate_pdf_for_engagement(
        self,
        engagement: Engagement,
        client_name: str,
        resolved_framework: ResolvedFramework = ResolvedFramework.FASB,
        fill_from_saved: bool = False,
    ) -> bytes:
        """Render for an engagement the caller has **already** access-checked.

        Sprint 813: the engagement ZIP export verified access and loaded the
        client, then called ``generate_pdf``, which did both again.
        """
        # Gather data (active only — exclude archived records)
        tool_runs = (
            self.db.query(ToolRun)
            .filter(
                ToolRun.engagement_id == engagement.id,
                ToolRun.archived_at.is_(None),
            )
            .order_by(ToolRun.run_at.desc())
            .all()
        )

        follow_up_items = (
            self.db.query(FollowUpItem)
            .filter(
                FollowUpItem.engagement_id == engagement.id,
                FollowUpItem.archived_at.is_(None),
            )
            .order_by(FollowUpItem.created_at.asc())
            .all()
        )

        return render_anomaly_summary_pdf(
            client_name,
            engagement,
            tool_runs,
            follow_up_items,
            resolved_framework=resolved_framework,
            fill_from_saved=fill_from_saved,
        )

    @staticmethod
    def _build_story(
        styles: dict,
        doc_width: float,
        client_name: str,
        engagement: Engagement,
        tool_runs: list,
        follow_up_items: list,
        resolved_framework: ResolvedFramework = ResolvedFramework.FASB,
        custom_logo_bytes: Optional[bytes] = None,
        reference: Optional[str] = None,
        fill_from_saved: bool = False,
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
        period_desc = f"{period_start} – {period_end}"

        reference = reference or _generate_reference()

        logo_path = find_logo()
        metadata = ReportMetadata(
            title="Anomaly Summary Report",
            client_name=client_name,
            engagement_period=period_desc,
            source_document="All executed diagnostic tool outputs",
            source_document_title="Aggregated from individual tool runs",
            reference=reference,
        )
        build_cover_page(story, styles, metadata, doc_width, logo_path, custom_logo_bytes=custom_logo_bytes)

        # --- Pre-compute data structures ---
        runs_by_tool: dict[str, list] = {}
        for run in tool_runs:
            tool_val = run.tool_name.value if run.tool_name else "unknown"
            runs_by_tool.setdefault(tool_val, []).append(run)

        # Sprint 787 / PR #174 review: scope BOTH sides of the coverage fraction to the
        # marketing catalog. `ToolName` carries `flux_analysis`, which is a free-tier
        # diagnostic surface and not one of the 18 sold tools.
        catalog_tools = [t for t in ToolName if t.value in CATALOG_TOOL_SLUGS]
        executed_tools = {ToolName(k) for k in runs_by_tool if k in CATALOG_TOOL_SLUGS}
        not_executed_tools = [t for t in catalog_tools if t not in executed_tools]

        total_runs = len(tool_runs)

        items_by_tool: dict[str, list] = {}
        for item in follow_up_items:
            items_by_tool.setdefault(item.tool_source, []).append(item)

        severity_counts = {"high": 0, "medium": 0, "low": 0}
        for item in follow_up_items:
            sev = item.severity.value if item.severity else "medium"
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        points, band = _compute_follow_up_points(
            severity_counts["high"],
            severity_counts["medium"],
            severity_counts["low"],
            len(not_executed_tools),
        )
        points_label = f"{points:,} points (band: {band})"

        # --- Section I: Scope ---
        story.append(Paragraph("I. Scope", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))

        story.append(
            Paragraph(
                f"<b>Tools Run:</b> {user_text(len(executed_tools))} of {user_text(MARKETING_AUDIT_TOOL_COUNT)} "
                "available tools",
                styles["MemoBody"],
            )
        )
        story.append(Paragraph(f"<b>Total Tool Runs:</b> {user_text(total_runs)}", styles["MemoBody"]))
        story.append(
            Paragraph(
                f"<b>Captured Follow-Up Items:</b> {len(follow_up_items)} &nbsp;&nbsp;|&nbsp;&nbsp; "
                f"High: {user_text(severity_counts['high'])} &nbsp;&nbsp;|&nbsp;&nbsp; "
                f"Medium: {user_text(severity_counts['medium'])} &nbsp;&nbsp;|&nbsp;&nbsp; "
                f"Low: {user_text(severity_counts['low'])}",
                styles["MemoBody"],
            )
        )
        story.append(
            Paragraph(
                "<i>Captured follow-up items are the items saved to this engagement from tool results; a tool's "
                "flag count and its captured follow-up items can differ.</i>",
                styles["MemoBodySmall"],
            )
        )
        story.append(Paragraph(f"<b>Follow-Up Item Points:</b> {user_text(points_label)}", styles["MemoBody"]))
        story.append(Paragraph(POINTS_BASIS_NOTE, styles["MemoBodySmall"]))
        story.append(Spacer(1, 6))

        # Sprint 887 (OUT-20): one row per catalog tool, from its latest successful run.
        story.append(Paragraph("<b>Tool Results</b>", styles["MemoBody"]))
        result_data = [["Tool", "Result", "Runs"]]
        for tool_name in catalog_tools:
            runs = runs_by_tool.get(tool_name.value, [])
            captured = len(items_by_tool.get(tool_name.value, []))
            result_data.append(
                [
                    Paragraph(user_text(TOOL_LABELS.get(tool_name, tool_name.value)), styles["MemoTableCell"]),
                    Paragraph(user_text(_tool_result(runs, captured)), styles["MemoTableCell"]),
                    Paragraph(str(len(runs)), styles["MemoTableCell"]),
                ]
            )
        result_table = Table(result_data, colWidths=[1.9 * inch, 3.9 * inch, 0.6 * inch], repeatRows=1)
        result_table.setStyle(TableStyle(ledger_table_style(extra=[("ALIGN", (2, 0), (2, -1), "CENTER")])))
        story.append(result_table)
        story.append(Spacer(1, 4))
        story.append(
            Paragraph(
                "<i>Each result is taken from the tool's latest successful run. “Not evaluated”: no run "
                "was recorded for this engagement. “Results unavailable”: the run was recorded without its "
                "flag count. “Failed”: no run completed.</i>",
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

        # --- Section II: Captured Follow-Up Items by Tool ---
        story.append(Paragraph("II. Captured Follow-Up Items by Tool", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))

        if not follow_up_items:
            story.append(
                Paragraph(
                    "No follow-up items have been captured for this engagement. Section I gives each tool's result.",
                    styles["MemoBody"],
                )
            )
        else:
            for tool_source, items in sorted(items_by_tool.items()):
                resolved_tn = _resolve_tool_name_from_source(tool_source)
                tool_label = TOOL_LABELS.get(resolved_tn, tool_source) if resolved_tn else tool_source
                cross_ref = TOOL_CROSS_REFERENCES.get(resolved_tn, "") if resolved_tn else ""

                header_text = f"<b>{user_text(tool_label)}</b> ({user_text(_items_phrase(len(items)))})"
                if cross_ref:
                    header_text += f" &nbsp;—&nbsp; {user_text(cross_ref)}"
                story.append(Paragraph(header_text, styles["MemoBody"]))

                anomaly_data = [["Ref", "#", "Severity", "Description"]]
                for idx, item in enumerate(items, 1):
                    sev = item.severity.value.upper() if item.severity else "MEDIUM"
                    desc = item.description[:200]
                    anomaly_data.append(
                        [
                            Paragraph(cross_ref, styles["MemoTableCell"]),
                            Paragraph(user_text(str(idx)), styles["MemoTableCell"]),
                            Paragraph(sev, styles["MemoTableCell"]),
                            Paragraph(user_text(desc), styles["MemoTableCell"]),
                        ]
                    )

                anomaly_table = Table(
                    anomaly_data,
                    colWidths=[1.0 * inch, 0.4 * inch, 1.0 * inch, 4.0 * inch],
                )
                anomaly_table.setStyle(TableStyle(ledger_table_style(extra=[("ALIGN", (1, 0), (1, -1), "CENTER")])))
                story.append(anomaly_table)
                story.append(Spacer(1, 10))

        # --- Methodology & Authoritative References ---
        build_methodology_statement(
            story,
            styles,
            doc_width,
            tool_domain="anomaly_summary",
            framework=resolved_framework,
            domain_label="engagement anomaly summary",
        )

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
        ref_table.setStyle(TableStyle(ledger_table_style()))
        story.append(ref_table)
        story.append(Spacer(1, 8))

        # --- Section III: Practitioner Worksheet ---
        story.append(PageBreak())
        story.append(Paragraph("III. Practitioner Worksheet — for the firm to complete", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))

        total_items = len(follow_up_items)
        story.append(Paragraph(f"<b>Captured Follow-Up Items:</b> {user_text(total_items)}", styles["MemoBody"]))
        if fill_from_saved:
            recorded = sum(
                1 for i in follow_up_items if i.disposition and i.disposition != FollowUpDisposition.NOT_REVIEWED
            )
            story.append(
                Paragraph(
                    f"<b>Dispositions recorded in Paciolus:</b> {user_text(recorded)} of {user_text(total_items)}",
                    styles["MemoBody"],
                )
            )
            story.append(
                Paragraph(
                    "<i>The disposition and auditor notes below are filled from what was saved in Paciolus, with "
                    "the date each item was last recorded. The other fields are for the firm to complete.</i>",
                    styles["MemoBodySmall"],
                )
            )
        else:
            story.append(
                Paragraph(
                    "<i>This worksheet is blank for the firm to complete. Dispositions and notes saved in "
                    "Paciolus can be included by exporting this report with the saved dispositions.</i>",
                    styles["MemoBodySmall"],
                )
            )
        story.append(Spacer(1, 12))

        if follow_up_items:
            item_counter = 0
            for tool_source, items in sorted(items_by_tool.items()):
                resolved_tn = _resolve_tool_name_from_source(tool_source)
                cross_ref = TOOL_CROSS_REFERENCES.get(resolved_tn, "") if resolved_tn else ""

                for item in items:
                    item_counter += 1
                    sev = item.severity.value.upper() if item.severity else "MEDIUM"
                    desc = item.description[:200]

                    tool_label = TOOL_LABELS.get(resolved_tn, tool_source) if resolved_tn else tool_source
                    header = f"<b>Item {user_text(item_counter)}</b> ({user_text(sev)}) — {user_text(tool_label)}"
                    if cross_ref:
                        header += f" [{cross_ref}]"
                    story.append(Paragraph(header, styles["MemoBody"]))
                    story.append(Paragraph(user_text(desc), styles["MemoBodySmall"]))
                    story.append(Spacer(1, 4))

                    response_data: list = [["Field", "Response"]]
                    if fill_from_saved:
                        disposition = item.disposition.value if item.disposition else "not_reviewed"
                        disposition_text = DISPOSITION_LABELS.get(disposition, disposition)
                        if disposition != "not_reviewed":
                            disposition_text += _recorded_on(item)
                        notes = (item.auditor_notes or "").strip()
                        response_data += [
                            [
                                Paragraph("Disposition (saved in Paciolus)", styles["MemoTableCell"]),
                                Paragraph(user_text(disposition_text), styles["MemoTableCell"]),
                            ],
                            [
                                Paragraph("Auditor Notes (saved in Paciolus)", styles["MemoTableCell"]),
                                Paragraph(
                                    user_text(notes + _recorded_on(item)) if notes else _TO_COMPLETE,
                                    styles["MemoTableCell"],
                                ),
                            ],
                        ]
                    response_data += [
                        [
                            Paragraph("Management Explanation", styles["MemoTableCell"]),
                            Paragraph(_TO_COMPLETE, styles["MemoTableCell"]),
                        ],
                        [
                            Paragraph("Planned Response", styles["MemoTableCell"]),
                            Paragraph(
                                f"{_TO_COMPLETE}<br/>"
                                "<i>Document the response the engagement team intends to take "
                                "(e.g., no change to planned procedures, expanded substantive "
                                "testing, escalation, specialist referral). Whether control "
                                "testing is appropriate is a matter of auditor judgment and "
                                "engagement scope — this platform does not direct methodology.</i>",
                                styles["MemoTableCell"],
                            ),
                        ],
                        [
                            Paragraph("Practitioner Classification Notes", styles["MemoTableCell"]),
                            Paragraph(
                                f"{_TO_COMPLETE}<br/>"
                                "<i>Classification of these items (e.g., deficiency, exception, inquiry) "  # allow-deny-phrase: disclaimer reserving classification to the auditor (ISA 265 negative use)
                                "is a matter of auditor judgment and is outside the scope of this report.</i>",
                                styles["MemoTableCell"],
                            ),
                        ],
                        [
                            Paragraph("Follow-Up Procedures", styles["MemoTableCell"]),
                            Paragraph(_TO_COMPLETE, styles["MemoTableCell"]),
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
                    response_table.setStyle(TableStyle(ledger_table_style()))
                    story.append(response_table)
                    story.append(Spacer(1, 12))
        else:
            story.append(
                Paragraph(
                    "No follow-up items have been captured, so the worksheet has no entries.",
                    styles["MemoBody"],
                )
            )

        # --- Section IV: Follow-Up Item Points ---
        story.append(Spacer(1, 16))
        story.append(Paragraph("IV. Follow-Up Item Points", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))

        points_box = Table(
            [
                [
                    Paragraph(
                        f"<b>FOLLOW-UP ITEM POINTS: {user_text(points_label)}</b>",
                        ParagraphStyle(
                            "_PointsLabel",
                            fontName="Times-Bold",
                            fontSize=11,
                            textColor=ClassicalColors.OBSIDIAN_DEEP,
                            alignment=TA_LEFT,
                            leading=14,
                        ),
                    )
                ]
            ],
            colWidths=[doc_width],
        )
        points_box.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), ClassicalColors.OATMEAL_PAPER),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("LEFTPADDING", (0, 0), (-1, -1), 12),
                    ("BOX", (0, 0), (-1, -1), 1, ClassicalColors.OBSIDIAN_DEEP),
                ]
            )
        )
        story.append(points_box)
        story.append(Paragraph(POINTS_BASIS_NOTE, styles["MemoBodySmall"]))
        story.append(Spacer(1, 8))

        not_run_count = len(not_executed_tools)
        coverage_points = int(not_run_count * POINTS_PER_TOOL_NOT_RUN)
        breakdown = [
            f"High-severity captured follow-up items: {severity_counts['high']} × 3 = {severity_counts['high'] * 3}",
            f"Medium-severity captured follow-up items: {severity_counts['medium']} × 2 = "
            f"{severity_counts['medium'] * 2}",
            f"Low-severity captured follow-up items: {severity_counts['low']} × 1 = {severity_counts['low']}",
            f"Catalog tools not run: {not_run_count} of {MARKETING_AUDIT_TOOL_COUNT} × 1.5, rounded down "
            f"= {coverage_points}",
        ]
        for line in breakdown:
            story.append(Paragraph(f"• {user_text(line)}", styles["MemoBody"]))
        story.append(Spacer(1, 8))
        story.append(Paragraph("<i>The auditor evaluates these results.</i>", styles["MemoBody"]))

        # No trailing standalone disclaimer — prevents phantom blank page.
        # The disclaimer is already rendered via draw_page_footer on every page
        # and via the banner at the top of page 1.

        return story


def render_anomaly_summary_pdf(
    client_name: str,
    engagement: Engagement,
    tool_runs: list,
    follow_up_items: list,
    resolved_framework: ResolvedFramework = ResolvedFramework.FASB,
    fill_from_saved: bool = False,
) -> bytes:
    """Render the anomaly summary from already-loaded engagement data.

    Sprint 813: split out of ``generate_pdf`` so ``generate_sample_reports``
    renders through the production path rather than a hand-copied story
    whose disclaimer had drifted. Reads the active ``PDFBrandingContext``
    once, so the cover logo and every page footer see the same values.
    """
    from shared.pdf_branding import current_pdf_branding

    branding = current_pdf_branding()

    # Sprint 813: the disclaimer banner precedes the cover, so the story
    # builds its own cover; render_memo owns page setup and page chrome.
    def _body(memo: MemoContext) -> None:
        memo.story.extend(
            AnomalySummaryGenerator._build_story(
                memo.styles,
                memo.doc_width,
                client_name,
                engagement,
                tool_runs,
                follow_up_items,
                resolved_framework=resolved_framework,
                custom_logo_bytes=memo.branding.effective_logo_bytes(),
                reference=memo.reference,
                fill_from_saved=fill_from_saved,
            )
        )

    return render_memo("Anomaly Summary Report", "ANS", _body, branding=branding)
