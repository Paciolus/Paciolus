"""
SUM Schedule memo generator — Sprint 729a (ISA 450).

Produces the Summary of Uncorrected Misstatements workpaper PDF.
Reads from the persisted ``UncorrectedMisstatement`` rows; aggregates
in-process.

Layout:
  1. Disclaimer banner
  2. Cover page
  3. I. Engagement Overview (period + materiality cascade)
  4. II. Misstatements grouped by classification (factual, judgmental, projected)
  5. III. Aggregate + materiality bucket
  6. IV. Authoritative References (ISA 450, AU-C 450, ISA 320)
  7. Sign-off (DRAFT watermark when items remain unreviewed)

ENTERPRISE BRANDING: Wrapped in apply_pdf_branding by the route layer.
"""

from io import BytesIO
from typing import Any, Optional

from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy.orm import Session

from engagement_model import Engagement
from models import Client
from pdf_generator import ClassicalColors, LedgerRule, generate_reference_number
from shared.framework_resolution import ResolvedFramework
from shared.memo_base import create_memo_styles
from shared.report_chrome import (
    ReportMetadata,
    build_cover_page,
    find_logo,
    make_branded_page_footer,
)
from uncorrected_misstatements_model import (
    MisstatementClassification,
    MisstatementDisposition,
    MisstatementSourceType,
    UncorrectedMisstatement,
)

DISCLAIMER_TEXT = (
    "DATA ANALYTICS REPORT — NOT AN AUDIT COMMUNICATION. "
    "This workpaper records the auditor's Summary of Uncorrected Misstatements per "
    "ISA 450 / AU-C 450. Materiality bucketing reflects the auditor's documented "
    "judgments at the time of generation. Final disposition and the decision whether "
    "to require correction are matters of auditor judgment and engagement scope."
)

AUTHORITATIVE_REFERENCES = [
    ("AICPA", "AU-C § 450", "Evaluation of Misstatements Identified During the Audit"),
    ("IAASB", "ISA 450", "Evaluation of Misstatements Identified During the Audit"),
    ("AICPA", "AU-C § 320", "Materiality in Planning and Performing an Audit"),
    ("IAASB", "ISA 320", "Materiality in Planning and Performing an Audit"),
    ("PCAOB", "AS 2810", "Evaluating Audit Results"),
]

_CLASSIFICATION_LABEL = {
    MisstatementClassification.FACTUAL: "Factual",
    MisstatementClassification.JUDGMENTAL: "Judgmental",
    MisstatementClassification.PROJECTED: "Projected",
}

_SOURCE_LABEL = {
    MisstatementSourceType.ADJUSTING_ENTRY_PASSED: "Passed AJE",
    MisstatementSourceType.SAMPLE_PROJECTION: "Sample Projection",
    MisstatementSourceType.KNOWN_ERROR: "Known Error",
}

_DISPOSITION_LABEL = {
    MisstatementDisposition.NOT_YET_REVIEWED: "Not Yet Reviewed",
    MisstatementDisposition.AUDITOR_PROPOSES_CORRECTION: "Auditor Proposes Correction",
    MisstatementDisposition.AUDITOR_ACCEPTS_AS_IMMATERIAL: "Auditor Accepts as Immaterial",
}

_BUCKET_LABEL = {
    "clearly_trivial": "Clearly Trivial",
    "immaterial": "Immaterial",
    "approaching_material": "Approaching Material",
    "material": "Material",
}


def _generate_reference() -> str:
    return generate_reference_number().replace("PAC-", "SUM-")


def _format_money(value: Any) -> str:
    if value is None:
        return "—"
    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return str(value)


def _format_signed_money(value: Any) -> str:
    """Show sign explicitly for F/S impacts (negative = decrease)."""
    if value is None:
        return "—"
    try:
        v = float(value)
        if v == 0:
            return "$0.00"
        return f"({_format_money(abs(v))})" if v < 0 else _format_money(v)
    except (TypeError, ValueError):
        return str(value)


class SumScheduleMemoGenerator:
    """Generates the ISA 450 SUM schedule workpaper PDF."""

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
    ) -> bytes:
        from shared.pdf_branding import current_pdf_branding
        from uncorrected_misstatements_manager import UncorrectedMisstatementsManager

        branding = current_pdf_branding()

        engagement = self._verify_engagement_access(user_id, engagement_id)
        if not engagement:
            raise ValueError("Engagement not found or access denied")

        client = self.db.query(Client).filter(Client.id == engagement.client_id).first()
        client_name = client.name if client else f"Client #{engagement.client_id}"

        items = (
            self.db.query(UncorrectedMisstatement)
            .filter(
                UncorrectedMisstatement.engagement_id == engagement_id,
                UncorrectedMisstatement.archived_at.is_(None),
            )
            .order_by(
                UncorrectedMisstatement.classification,
                UncorrectedMisstatement.created_at.asc(),
            )
            .all()
        )

        # Pull aggregate via the manager so memo + API stay in sync
        try:
            schedule = UncorrectedMisstatementsManager(self.db).compute_sum_schedule(user_id, engagement_id)
        except ValueError:
            schedule = None

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
            items,
            schedule,
            resolved_framework=resolved_framework,
            custom_logo_bytes=branding.effective_logo_bytes(),
        )

        footer_cb = make_branded_page_footer(
            header_text=branding.effective_header_text(),
            footer_text=branding.effective_footer_text(),
        )
        doc.build(story, onFirstPage=footer_cb, onLaterPages=footer_cb)

        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    def _build_story(
        self,
        styles: dict,
        doc_width: float,
        client_name: str,
        engagement: Engagement,
        items: list[UncorrectedMisstatement],
        schedule: Optional[dict],
        resolved_framework: ResolvedFramework = ResolvedFramework.FASB,
        custom_logo_bytes: Optional[bytes] = None,
    ) -> list:
        story: list = []

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

        period_start = engagement.period_start.strftime("%b %d, %Y") if engagement.period_start else "N/A"
        period_end = engagement.period_end.strftime("%b %d, %Y") if engagement.period_end else "N/A"
        period_desc = f"{period_start} – {period_end}"
        reference = _generate_reference()
        logo_path = find_logo()

        metadata = ReportMetadata(
            title="Summary of Uncorrected Misstatements",
            client_name=client_name,
            engagement_period=period_desc,
            source_document="Auditor-recorded misstatements (ISA 450)",
            source_document_title="Engagement workpaper",
            reference=reference,
        )
        build_cover_page(story, styles, metadata, doc_width, logo_path, custom_logo_bytes=custom_logo_bytes)

        # --- Section I: Overview ---
        story.append(Paragraph("I. Engagement Overview", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))
        story.append(Paragraph(f"<b>Engagement Period:</b> {period_desc}", styles["MemoBody"]))
        story.append(
            Paragraph(
                f"<b>Total Misstatements Recorded:</b> {len(items)}",
                styles["MemoBody"],
            )
        )

        if schedule is not None:
            mat = schedule["materiality"]
            story.append(
                Paragraph(
                    f"<b>Overall Materiality:</b> {_format_money(mat['overall'])} &nbsp;&bull;&nbsp; "
                    f"<b>Performance:</b> {_format_money(mat['performance'])} &nbsp;&bull;&nbsp; "
                    f"<b>Trivial Threshold:</b> {_format_money(mat['trivial'])}",
                    styles["MemoBody"],
                )
            )
            unreviewed = schedule["unreviewed_count"]
            story.append(
                Paragraph(
                    f"<b>Unreviewed Items:</b> {unreviewed}",
                    styles["MemoBody"],
                )
            )

        story.append(Spacer(1, 8))

        # --- Section II: Items grouped by classification ---
        story.append(Paragraph("II. Misstatement Items", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))

        if not items:
            story.append(
                Paragraph(
                    "<i>No uncorrected misstatements recorded for this engagement.</i>",
                    styles["MemoBody"],
                )
            )
        else:
            by_cls: dict[MisstatementClassification, list[UncorrectedMisstatement]] = {}
            for m in items:
                by_cls.setdefault(m.classification, []).append(m)

            for cls in MisstatementClassification:
                rows = by_cls.get(cls, [])
                if not rows:
                    continue
                story.append(
                    Paragraph(
                        f"<b>{_CLASSIFICATION_LABEL[cls]}</b> ({len(rows)})",
                        styles["MemoBody"],
                    )
                )
                table_data = [
                    [
                        "Source",
                        "Description",
                        "Net Income Δ",
                        "Net Assets Δ",
                        "Disposition",
                    ]
                ]
                for m in rows:
                    table_data.append(
                        [
                            Paragraph(
                                _SOURCE_LABEL.get(m.source_type, m.source_type.value),
                                styles["MemoTableCell"],
                            ),
                            Paragraph(m.description[:240], styles["MemoTableCell"]),
                            Paragraph(
                                _format_signed_money(m.fs_impact_net_income),
                                styles["MemoTableCell"],
                            ),
                            Paragraph(
                                _format_signed_money(m.fs_impact_net_assets),
                                styles["MemoTableCell"],
                            ),
                            Paragraph(
                                _DISPOSITION_LABEL.get(m.cpa_disposition, "—"),
                                styles["MemoTableCell"],
                            ),
                        ]
                    )
                table = Table(
                    table_data,
                    colWidths=[
                        1.1 * inch,
                        2.6 * inch,
                        1.0 * inch,
                        1.0 * inch,
                        1.5 * inch,
                    ],
                )
                table.setStyle(
                    TableStyle(
                        [
                            ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                            ("FONTNAME", (0, 1), (-1, -1), "Times-Roman"),
                            ("FONTSIZE", (0, 0), (-1, -1), 9),
                            ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                            ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                            ("LINEBELOW", (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("ALIGN", (2, 0), (3, -1), "RIGHT"),
                            ("TOPPADDING", (0, 0), (-1, -1), 3),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                        ]
                    )
                )
                story.append(table)
                story.append(Spacer(1, 8))

                # Per-row reference + auditor notes
                for m in rows:
                    refnote = (
                        f"<b>{_CLASSIFICATION_LABEL[cls]} — {_SOURCE_LABEL.get(m.source_type, m.source_type.value)}.</b> "
                        f"<i>Reference:</i> {m.source_reference}"
                    )
                    if m.cpa_notes:
                        refnote += f" <i>Auditor notes:</i> {m.cpa_notes}"
                    story.append(Paragraph(refnote, styles["MemoBodySmall"]))
                    story.append(Spacer(1, 4))

                story.append(Spacer(1, 8))

        # --- Section III: Aggregate + Bucket ---
        story.append(Paragraph("III. Aggregate Evaluation", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))

        if schedule is None:
            story.append(
                Paragraph(
                    "<i>Materiality not configured — aggregate bucket cannot be computed.</i>",
                    styles["MemoBody"],
                )
            )
        else:
            agg = schedule["aggregate"]
            sub = schedule["subtotals"]
            bucket = schedule["bucket"]
            bucket_label = _BUCKET_LABEL.get(bucket, bucket)

            agg_table = Table(
                [
                    ["Subtotal", "Net Income", "Net Assets"],
                    [
                        Paragraph("Factual + Judgmental", styles["MemoTableCell"]),
                        Paragraph(
                            _format_signed_money(sub["factual_judgmental_net_income"]),
                            styles["MemoTableCell"],
                        ),
                        Paragraph(
                            _format_signed_money(sub["factual_judgmental_net_assets"]),
                            styles["MemoTableCell"],
                        ),
                    ],
                    [
                        Paragraph("Projected (sampling)", styles["MemoTableCell"]),
                        Paragraph(
                            _format_signed_money(sub["projected_net_income"]),
                            styles["MemoTableCell"],
                        ),
                        Paragraph(
                            _format_signed_money(sub["projected_net_assets"]),
                            styles["MemoTableCell"],
                        ),
                    ],
                    [
                        Paragraph("<b>Aggregate</b>", styles["MemoTableCell"]),
                        Paragraph(
                            f"<b>{_format_signed_money(agg['net_income'])}</b>",
                            styles["MemoTableCell"],
                        ),
                        Paragraph(
                            f"<b>{_format_signed_money(agg['net_assets'])}</b>",
                            styles["MemoTableCell"],
                        ),
                    ],
                ],
                colWidths=[2.6 * inch, 2.2 * inch, 2.2 * inch],
            )
            agg_table.setStyle(
                TableStyle(
                    [
                        ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                        ("FONTNAME", (0, 1), (-1, -1), "Times-Roman"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                        ("LINEBELOW", (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                        ("LINEABOVE", (0, -1), (-1, -1), 0.5, ClassicalColors.OBSIDIAN_DEEP),
                        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ]
                )
            )
            story.append(agg_table)
            story.append(Spacer(1, 12))

            # Bucket box
            box_color = ClassicalColors.CLAY if bucket in ("material", "approaching_material") else ClassicalColors.SAGE
            bucket_box = Table(
                [
                    [
                        Paragraph(
                            f"<b>MATERIALITY BUCKET: {bucket_label.upper()}</b>",
                            ParagraphStyle(
                                "_BucketLabel",
                                fontName="Times-Bold",
                                fontSize=11,
                                textColor=box_color,
                                alignment=TA_LEFT,
                                leading=14,
                            ),
                        )
                    ]
                ],
                colWidths=[doc_width],
            )
            bucket_box.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), ClassicalColors.OATMEAL_PAPER),
                        ("BOX", (0, 0), (-1, -1), 1, box_color),
                        ("TOPPADDING", (0, 0), (-1, -1), 8),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                        ("LEFTPADDING", (0, 0), (-1, -1), 12),
                    ]
                )
            )
            story.append(bucket_box)

            if bucket == "material":
                story.append(Spacer(1, 8))
                story.append(
                    Paragraph(
                        "<b>NOTE:</b> Aggregate misstatement exceeds overall materiality. "
                        "Per ISA 450 §11, the auditor should communicate uncorrected "
                        "misstatements to those charged with governance and consider whether "
                        "the financial statements as a whole are free from material misstatement.",
                        styles["MemoBodySmall"],
                    )
                )

        # --- Section IV: References ---
        story.append(Paragraph("IV. Authoritative References", styles["MemoSection"]))
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
                    ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                    ("LINEBELOW", (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        story.append(ref_table)
        story.append(Spacer(1, 12))

        # --- Sign-off ---
        story.append(Paragraph("Sign-Off", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))

        unreviewed_count = (
            schedule["unreviewed_count"]
            if schedule is not None
            else sum(1 for m in items if m.cpa_disposition == MisstatementDisposition.NOT_YET_REVIEWED)
        )
        if unreviewed_count > 0:
            story.append(
                Paragraph(
                    f"<b>DRAFT — INCOMPLETE:</b> {unreviewed_count} item(s) remain "
                    f"unreviewed. ISA 450 requires the auditor to reach a documented "
                    f"disposition for each uncorrected misstatement before this "
                    f"workpaper is included in the engagement file.",
                    ParagraphStyle(
                        "_DraftNote",
                        fontName="Times-Bold",
                        fontSize=9,
                        textColor=ClassicalColors.CLAY,
                        spaceAfter=8,
                    ),
                )
            )
        else:
            story.append(
                Paragraph(
                    "<i>All items dispositioned. Auditor sign-off below.</i>",
                    styles["MemoBody"],
                )
            )

        story.append(Spacer(1, 12))
        story.append(
            Paragraph(
                "Auditor: ____________________________ &nbsp; Date: __________",
                styles["MemoBody"],
            )
        )

        return story
