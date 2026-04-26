"""
Analytical Expectation memo generator — Sprint 728a (ISA 520).

Produces the workpaper PDF for an engagement's analytical-procedure
expectations. Reads from the persisted ``AnalyticalExpectation`` rows;
no underlying tool data touched.

Layout:
  1. Disclaimer banner (DATA ANALYTICS REPORT — NOT AN AUDIT COMMUNICATION)
  2. Cover page (client / period / reference)
  3. I. Engagement Overview (period, materiality cascade)
  4. II. Analytical Expectations (table grouped by target type)
  5. III. ISA 520 Methodology Reference (authoritative citations)
  6. Sign-off block

ENTERPRISE BRANDING: Routes wrap the call in ``apply_pdf_branding(...)``;
this generator reads ``current_pdf_branding()`` for logo + header/footer.
"""

import json
from io import BytesIO
from typing import Any, Optional

from reportlab.lib.enums import TA_CENTER
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

from analytical_expectations_model import (
    AnalyticalExpectation,
    ExpectationCorroborationTag,
    ExpectationResultStatus,
    ExpectationTargetType,
)
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

DISCLAIMER_TEXT = (
    "DATA ANALYTICS REPORT — NOT AN AUDIT COMMUNICATION. "
    "This workpaper records the auditor's analytical procedure expectations and "
    "outcomes per ISA 520 / AU-C 520. It does not constitute an audit opinion. "  # allow-deny-phrase: disclaiming what the report is NOT (ISA 265 negative use)
    "Classification of variances and the sufficiency of analytical evidence "
    "are matters of auditor judgment."
)

AUTHORITATIVE_REFERENCES = [
    ("AICPA", "AU-C § 520", "Analytical Procedures"),
    ("IAASB", "ISA 520", "Analytical Procedures"),
    ("PCAOB", "AS 2305", "Substantive Analytical Procedures"),
    ("AICPA", "AU-C § 330", "Performing Audit Procedures in Response to Assessed Risks"),
    ("IAASB", "ISA 320", "Materiality in Planning and Performing an Audit"),
]

_TARGET_TYPE_LABEL = {
    ExpectationTargetType.ACCOUNT: "Account",
    ExpectationTargetType.BALANCE: "Balance",
    ExpectationTargetType.RATIO: "Ratio",
    ExpectationTargetType.FLUX_LINE: "Flux Line",
}

_STATUS_LABEL = {
    ExpectationResultStatus.NOT_EVALUATED: "Not Evaluated",
    ExpectationResultStatus.WITHIN_THRESHOLD: "Within Threshold",
    ExpectationResultStatus.EXCEEDS_THRESHOLD: "Exceeds Threshold",
}

_TAG_LABEL = {
    ExpectationCorroborationTag.INDUSTRY_DATA.value: "Industry Data",
    ExpectationCorroborationTag.PRIOR_PERIOD.value: "Prior Period",
    ExpectationCorroborationTag.BUDGET.value: "Budget",
    ExpectationCorroborationTag.REGRESSION_MODEL.value: "Regression Model",
    ExpectationCorroborationTag.OTHER.value: "Other",
}


def _generate_reference() -> str:
    return generate_reference_number().replace("PAC-", "AEM-")


def _format_money(value: Any) -> str:
    if value is None:
        return "—"
    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return str(value)


def _format_threshold(exp: AnalyticalExpectation) -> str:
    if exp.precision_threshold_amount is not None:
        return _format_money(exp.precision_threshold_amount)
    if exp.precision_threshold_percent is not None:
        return f"{exp.precision_threshold_percent:.2f}%"
    return "—"


def _format_expected(exp: AnalyticalExpectation) -> str:
    if exp.expected_value is not None:
        return _format_money(exp.expected_value)
    if exp.expected_range_low is not None and exp.expected_range_high is not None:
        return f"{_format_money(exp.expected_range_low)} – {_format_money(exp.expected_range_high)}"
    return "—"


def _format_tags(exp: AnalyticalExpectation) -> str:
    try:
        raw = json.loads(exp.corroboration_tags_json) if exp.corroboration_tags_json else []
    except (ValueError, TypeError):
        raw = []
    return ", ".join(_TAG_LABEL.get(t, t) for t in raw) or "—"


class AnalyticalExpectationMemoGenerator:
    """Generates the ISA 520 analytical-expectations workpaper PDF."""

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
        """Render the workpaper. Returns raw PDF bytes."""
        from shared.pdf_branding import current_pdf_branding

        branding = current_pdf_branding()

        engagement = self._verify_engagement_access(user_id, engagement_id)
        if not engagement:
            raise ValueError("Engagement not found or access denied")

        client = self.db.query(Client).filter(Client.id == engagement.client_id).first()
        client_name = client.name if client else f"Client #{engagement.client_id}"

        expectations = (
            self.db.query(AnalyticalExpectation)
            .filter(
                AnalyticalExpectation.engagement_id == engagement_id,
                AnalyticalExpectation.archived_at.is_(None),
            )
            .order_by(
                AnalyticalExpectation.procedure_target_type,
                AnalyticalExpectation.created_at.asc(),
            )
            .all()
        )

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
            expectations,
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
        expectations: list[AnalyticalExpectation],
        resolved_framework: ResolvedFramework = ResolvedFramework.FASB,
        custom_logo_bytes: Optional[bytes] = None,
    ) -> list:
        story: list = []

        # --- Disclaimer banner ---
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

        # --- Cover ---
        period_start = engagement.period_start.strftime("%b %d, %Y") if engagement.period_start else "N/A"
        period_end = engagement.period_end.strftime("%b %d, %Y") if engagement.period_end else "N/A"
        period_desc = f"{period_start} – {period_end}"
        reference = _generate_reference()
        logo_path = find_logo()

        metadata = ReportMetadata(
            title="Analytical Expectations Workpaper",
            client_name=client_name,
            engagement_period=period_desc,
            source_document="Auditor-supplied analytical procedure expectations (ISA 520)",
            source_document_title="Engagement workpaper",
            reference=reference,
        )
        build_cover_page(
            story,
            styles,
            metadata,
            doc_width,
            logo_path,
            custom_logo_bytes=custom_logo_bytes,
        )

        # --- Section I: Engagement Overview ---
        story.append(Paragraph("I. Engagement Overview", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))

        story.append(
            Paragraph(
                f"<b>Engagement Period:</b> {period_desc}",
                styles["MemoBody"],
            )
        )
        story.append(
            Paragraph(
                f"<b>Total Expectations Documented:</b> {len(expectations)}",
                styles["MemoBody"],
            )
        )

        unevaluated_count = sum(1 for e in expectations if e.result_status == ExpectationResultStatus.NOT_EVALUATED)
        within_count = sum(1 for e in expectations if e.result_status == ExpectationResultStatus.WITHIN_THRESHOLD)
        exceeds_count = sum(1 for e in expectations if e.result_status == ExpectationResultStatus.EXCEEDS_THRESHOLD)

        story.append(
            Paragraph(
                f"<b>Status:</b> Not Evaluated: {unevaluated_count} &nbsp;&bull;&nbsp; "
                f"Within Threshold: {within_count} &nbsp;&bull;&nbsp; "
                f"Exceeds Threshold: {exceeds_count}",
                styles["MemoBody"],
            )
        )

        if engagement.materiality_amount is not None:
            try:
                from engagement_manager import EngagementManager

                materiality = EngagementManager(self.db).compute_materiality(engagement)
                story.append(
                    Paragraph(
                        f"<b>Overall Materiality:</b> "
                        f"{_format_money(materiality['overall_materiality'])} &nbsp;&bull;&nbsp; "
                        f"<b>Performance Materiality:</b> "
                        f"{_format_money(materiality['performance_materiality'])} &nbsp;&bull;&nbsp; "
                        f"<b>Trivial Threshold:</b> "
                        f"{_format_money(materiality['trivial_threshold'])}",
                        styles["MemoBody"],
                    )
                )
            except Exception:
                # Materiality is optional context — never let it block the workpaper
                pass

        story.append(Spacer(1, 8))

        # --- Section II: Expectations Table ---
        story.append(Paragraph("II. Analytical Expectations", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))

        if not expectations:
            story.append(
                Paragraph(
                    "<i>No analytical expectations have been recorded for this engagement.</i>",
                    styles["MemoBody"],
                )
            )
        else:
            # Group by target type for readability
            by_type: dict[ExpectationTargetType, list[AnalyticalExpectation]] = {}
            for e in expectations:
                by_type.setdefault(e.procedure_target_type, []).append(e)

            for target_type in ExpectationTargetType:
                items = by_type.get(target_type, [])
                if not items:
                    continue

                story.append(
                    Paragraph(
                        f"<b>{_TARGET_TYPE_LABEL[target_type]}</b> ({len(items)})",
                        styles["MemoBody"],
                    )
                )

                table_data = [
                    [
                        "Target",
                        "Expected",
                        "Threshold",
                        "Basis Tags",
                        "Actual",
                        "Variance",
                        "Status",
                    ]
                ]
                for e in items:
                    table_data.append(
                        [
                            Paragraph(e.procedure_target_label, styles["MemoTableCell"]),
                            Paragraph(_format_expected(e), styles["MemoTableCell"]),
                            Paragraph(_format_threshold(e), styles["MemoTableCell"]),
                            Paragraph(_format_tags(e), styles["MemoTableCell"]),
                            Paragraph(_format_money(e.result_actual_value), styles["MemoTableCell"]),
                            Paragraph(_format_money(e.result_variance_amount), styles["MemoTableCell"]),
                            Paragraph(
                                _STATUS_LABEL.get(e.result_status, "—"),
                                styles["MemoTableCell"],
                            ),
                        ]
                    )

                table = Table(
                    table_data,
                    colWidths=[
                        1.6 * inch,
                        0.95 * inch,
                        0.85 * inch,
                        1.3 * inch,
                        0.95 * inch,
                        0.85 * inch,
                        1.0 * inch,
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
                            ("TOPPADDING", (0, 0), (-1, -1), 3),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                        ]
                    )
                )
                story.append(table)
                story.append(Spacer(1, 8))

                # Per-row corroboration narrative + CPA notes block
                for e in items:
                    narrative = (
                        f"<b>{_TARGET_TYPE_LABEL[target_type]} — {e.procedure_target_label}.</b> "
                        f"<i>Corroboration:</i> {e.corroboration_basis_text}"
                    )
                    if e.cpa_notes:
                        narrative += f" <i>Auditor notes:</i> {e.cpa_notes}"
                    story.append(Paragraph(narrative, styles["MemoBodySmall"]))
                    story.append(Spacer(1, 4))

                story.append(Spacer(1, 8))

        # --- Section III: Authoritative References ---
        story.append(Paragraph("III. Authoritative References", styles["MemoSection"]))
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
                ]
            )
        )
        story.append(ref_table)
        story.append(Spacer(1, 12))

        # --- Sign-off ---
        story.append(Paragraph("Sign-Off", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))

        if unevaluated_count > 0:
            story.append(
                Paragraph(
                    f"<b>DRAFT — INCOMPLETE:</b> {unevaluated_count} expectation(s) "
                    f"remain unevaluated. ISA 520 requires the auditor to complete the "
                    f"analytical procedure (capture actual + assess variance) before this "
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
                    "<i>All expectations evaluated. Auditor sign-off below.</i>",
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
