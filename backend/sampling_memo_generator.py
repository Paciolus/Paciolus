"""
Sampling Memo PDF Generator — Sprint 269, enriched Sprint 506
Phase XXXVI: Statistical Sampling (Tool 12)

Custom PDF structure (NOT using testing_memo_template — different workflow):
  1. Header (client, period, reference)
  2. Scope (ISA 530 reference, parameters)
  3. Design Parameters (method, confidence, thresholds)
  4. Stratification Summary (if applicable)
  5. Evaluation Results (if Phase 2 completed)
  6. Error Details (if errors found)
  7. Methodology
  8. Conclusion / Status
  9. Sample Selection Preview (if design phase)
  10. Next Steps
  11. Workpaper Signoff
  12. Disclaimer
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

# ═══════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════

# Confidence factor derivation notes keyed by confidence level
CONFIDENCE_FACTOR_NOTES: dict[float, str] = {
    0.80: "1.6094 (-ln(0.20)) — 80% confidence level",
    0.85: "1.8971 (-ln(0.15)) — 85% confidence level",
    0.90: "2.3026 (-ln(0.10)) — 90% confidence level",
    0.95: "3.0000 (-ln(0.05), rounded) — 95% confidence level",
    0.97: "3.5066 (-ln(0.03)) — 97% confidence level",
    0.99: "4.6052 (-ln(0.01)) — 99% confidence level",
}

# Next steps templates keyed by population type
_NEXT_STEPS_AR: list[dict[str, str]] = [
    {
        "title": "Step 1 — Prepare Client Request",
        "body": (
            "Export the full sample listing and provide to the client as a formal "
            "document request. For each selected invoice, request: (a) original "
            "invoice copy, (b) customer purchase order or contract, (c) shipping "
            "or delivery confirmation, and (d) any subsequent cash receipts or "
            "credits applied to the balance."
        ),
    },
    {
        "title": "Step 2 — Perform Confirmation Procedures (ISA 505)",
        "body": (
            "Consider whether positive confirmation of selected balances is required. "
            "For balances over the materiality threshold, direct positive confirmation "
            "with the customer is the preferred procedure. For smaller balances, "
            "alternative procedures (subsequent receipts, invoice examination) may "
            "be substituted with documented rationale."
        ),
    },
    {
        "title": "Step 3 — Test Each Selected Item",
        "body": (
            "For each selected item, confirm: (a) the recorded amount agrees to the "
            "supporting invoice; (b) the transaction date falls within the period under "
            "examination; (c) goods or services were delivered prior to period end "
            "(cut-off assertion); (d) the customer has been billed and the receivable "
            "is valid (existence assertion); (e) the balance is collectible at the "
            "recorded amount (valuation assertion)."
        ),
    },
    {
        "title": "Step 4 — Record Results",
        "body": (
            "Document the audited amount for each item. Record any difference between "
            "the recorded amount and the audited amount as a misstatement. For each "
            "misstatement, record: the direction (overstatement / understatement), "
            "the nature (pricing error / cut-off / non-existent receivable / other), "
            "and whether the client has agreed to correct the item."
        ),
    },
    {
        "title": "Step 5 — Upload Results for Evaluation",
        "body": (
            "When testing is complete, upload the error results to the Paciolus "
            "Sampling Evaluation module (SSM Evaluation tab) to compute the Upper "
            "Error Limit (UEL) using the Stringer bound method and obtain a "
            "PASS / FAIL conclusion. If UEL exceeds Tolerable Misstatement, "
            "expand the sample or perform alternative procedures per ISA 530.17."
        ),
    },
]

_NEXT_STEPS_AP: list[dict[str, str]] = [
    {
        "title": "Step 1 — Prepare Client Request",
        "body": (
            "Export the full sample listing and provide to the client. For each "
            "selected payment, request: (a) original vendor invoice, (b) purchase "
            "order or approval documentation, (c) receiving report or proof of "
            "delivery, and (d) payment remittance or check copy."
        ),
    },
    {
        "title": "Step 2 — Perform Vendor Statement Reconciliation",
        "body": (
            "For significant vendor balances, obtain vendor statements and reconcile "
            "to the AP sub-ledger. Investigate and document any reconciling items."
        ),
    },
    {
        "title": "Step 3 — Test Each Selected Item",
        "body": (
            "For each selected item, confirm: (a) the recorded amount agrees to the "
            "vendor invoice; (b) the payment was properly authorized; (c) goods or "
            "services were received (completeness assertion); (d) the liability is "
            "valid (existence assertion); (e) the payment is recorded in the correct "
            "period (cut-off assertion)."
        ),
    },
    {
        "title": "Step 4 — Record Results",
        "body": (
            "Document the audited amount for each item. Record any difference between "
            "the recorded amount and the audited amount as a misstatement, including "
            "direction, nature, and client agreement to correct."
        ),
    },
    {
        "title": "Step 5 — Upload Results for Evaluation",
        "body": (
            "When testing is complete, upload the error results to the Paciolus "
            "Sampling Evaluation module to compute the Upper Error Limit (UEL) "
            "and obtain a PASS / FAIL conclusion per ISA 530.17."
        ),
    },
]

_NEXT_STEPS_INVENTORY: list[dict[str, str]] = [
    {
        "title": "Step 1 — Prepare Count Sheet",
        "body": (
            "Export the full sample listing as the test count sheet. For each "
            "selected item, the count team should physically verify: (a) quantity "
            "on hand, (b) item condition (obsolescence / damage), (c) location "
            "matches records, and (d) unit of measure consistency."
        ),
    },
    {
        "title": "Step 2 — Perform Physical Count or Observation",
        "body": (
            "Physically count each selected item or observe client count procedures "
            "per ISA 501. Record the actual quantity and note any discrepancies "
            "between the physical count and the perpetual inventory records."
        ),
    },
    {
        "title": "Step 3 — Test Valuation",
        "body": (
            "For each selected item, confirm: (a) cost is properly supported by "
            "purchase invoices; (b) NRV does not fall below cost (ASC 330 / IAS 2); "
            "(c) overhead allocation is reasonable; (d) obsolescence reserves are "
            "adequate for slow-moving or damaged items."
        ),
    },
    {
        "title": "Step 4 — Record Results",
        "body": (
            "Document the audited quantity and value for each item. Record any "
            "difference as a misstatement, including the nature (quantity error / "
            "valuation error / obsolescence) and direction."
        ),
    },
    {
        "title": "Step 5 — Upload Results for Evaluation",
        "body": (
            "When testing is complete, upload the error results to the Paciolus "
            "Sampling Evaluation module to compute the Upper Error Limit (UEL) "
            "and obtain a PASS / FAIL conclusion per ISA 530.17."
        ),
    },
]

_NEXT_STEPS_REVENUE: list[dict[str, str]] = [
    {
        "title": "Step 1 — Prepare Client Request",
        "body": (
            "Export the full sample listing and provide to the client. For each "
            "selected revenue transaction, request: (a) customer contract or "
            "agreement, (b) evidence of performance obligation satisfaction "
            "(delivery / acceptance), (c) invoice copy, and (d) proof of payment "
            "or cash receipt."
        ),
    },
    {
        "title": "Step 2 — Perform Cut-Off Testing",
        "body": (
            "For transactions near period end, confirm revenue was recognized in "
            "the correct period per ASC 606 / IFRS 15. Verify that performance "
            "obligations were satisfied before the recognition date."
        ),
    },
    {
        "title": "Step 3 — Test Each Selected Item",
        "body": (
            "For each selected item, confirm: (a) the transaction is supported by "
            "a valid contract (existence assertion); (b) the transaction price is "
            "correctly determined (valuation assertion); (c) revenue is recognized "
            "when performance obligations are satisfied (occurrence assertion); "
            "(d) the amount is correctly classified and disclosed."
        ),
    },
    {
        "title": "Step 4 — Record Results",
        "body": (
            "Document the audited amount for each item. Record any difference as a "
            "misstatement, including the nature (recognition timing / pricing / "
            "fictitious revenue / classification) and direction."
        ),
    },
    {
        "title": "Step 5 — Upload Results for Evaluation",
        "body": (
            "When testing is complete, upload the error results to the Paciolus "
            "Sampling Evaluation module to compute the Upper Error Limit (UEL) "
            "and obtain a PASS / FAIL conclusion per ISA 530.17."
        ),
    },
]

_NEXT_STEPS_GENERIC: list[dict[str, str]] = [
    {
        "title": "Step 1 — Select Sample Items",
        "body": "Select the sample items identified above from the source population.",
    },
    {
        "title": "Step 2 — Perform Planned Procedures",
        "body": "Perform the planned audit procedure on each selected item.",
    },
    {
        "title": "Step 3 — Document Results",
        "body": "Document the results and any deviations/misstatements found.",
    },
    {
        "title": "Step 4 — Evaluate Results",
        "body": "Evaluate the results using the sampling methodology (e.g., project misstatements).",
    },
    {
        "title": "Step 5 — Form Conclusion",
        "body": (
            "Form a conclusion on whether the account balance or transaction class requires further investigation."
        ),
    },
]

NEXT_STEPS_BY_POPULATION_TYPE: dict[str, list[dict[str, str]]] = {
    "AR": _NEXT_STEPS_AR,
    "AP": _NEXT_STEPS_AP,
    "INVENTORY": _NEXT_STEPS_INVENTORY,
    "REVENUE": _NEXT_STEPS_REVENUE,
}


def generate_sampling_design_memo(
    design_result: dict[str, Any],
    filename: str = "population",
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
    """Generate a PDF memo for the sampling design phase only."""
    return _generate_sampling_memo(
        design_result=design_result,
        evaluation_result=None,
        filename=filename,
        client_name=client_name,
        period_tested=period_tested,
        prepared_by=prepared_by,
        reviewed_by=reviewed_by,
        workpaper_date=workpaper_date,
        source_document_title=source_document_title,
        source_context_note=source_context_note,
        resolved_framework=resolved_framework,
        include_signoff=include_signoff,
    )


def generate_sampling_evaluation_memo(
    evaluation_result: dict[str, Any],
    design_result: Optional[dict[str, Any]] = None,
    filename: str = "sample",
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
    """Generate a PDF memo for the evaluation phase (optionally with design context)."""
    return _generate_sampling_memo(
        design_result=design_result,
        evaluation_result=evaluation_result,
        filename=filename,
        client_name=client_name,
        period_tested=period_tested,
        prepared_by=prepared_by,
        reviewed_by=reviewed_by,
        workpaper_date=workpaper_date,
        source_document_title=source_document_title,
        source_context_note=source_context_note,
        resolved_framework=resolved_framework,
        include_signoff=include_signoff,
    )


def _generate_sampling_memo(
    design_result: Optional[dict[str, Any]],
    evaluation_result: Optional[dict[str, Any]],
    filename: str,
    client_name: Optional[str],
    period_tested: Optional[str],
    prepared_by: Optional[str],
    reviewed_by: Optional[str],
    workpaper_date: Optional[str],
    source_document_title: Optional[str] = None,
    source_context_note: Optional[str] = None,
    resolved_framework: ResolvedFramework = ResolvedFramework.FASB,
    include_signoff: bool = False,
) -> bytes:
    """Internal: generate the combined sampling memo PDF."""
    log_secure_operation("sampling_memo_start", f"Generating sampling memo for {filename}")

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
    doc_width = letter[0] - 1.5 * inch
    ref_number = generate_reference_number().replace("PAC-", "SSM-")

    # ─── 0. Cover Page ───────────────────────────────────────
    logo_path = find_logo()
    cover_metadata = ReportMetadata(
        title="STATISTICAL SAMPLING MEMO",
        client_name=client_name or "",
        engagement_period=period_tested or "",
        source_document=filename,
        source_document_title=source_document_title or "",
        source_context_note=source_context_note or "",
        reference=ref_number,
    )
    build_cover_page(story, styles, cover_metadata, doc_width, logo_path)

    # ─── 1. Header ───────────────────────────────────────────
    build_memo_header(
        story,
        styles,
        doc_width,
        title="STATISTICAL SAMPLING MEMO",
        reference=ref_number,
        client_name=client_name,
    )

    # ─── 2. Scope ────────────────────────────────────────────
    story.append(Paragraph("I. Scope", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    # Source document transparency (Sprint 6)
    if source_document_title and filename:
        story.append(
            Paragraph(create_leader_dots("Source", f"{source_document_title} ({filename})"), styles["MemoLeader"])
        )
    elif source_document_title:
        story.append(Paragraph(create_leader_dots("Source", source_document_title), styles["MemoLeader"]))
    elif filename:
        story.append(Paragraph(create_leader_dots("Source", filename), styles["MemoLeader"]))

    scope_text = (
        "This memo documents the statistical sampling procedures performed in accordance with "
        "ISA 530 (Audit Sampling) and PCAOB AS 2315 (Audit Sampling). "
    )
    if period_tested:
        scope_text += f"Period under examination: {period_tested}. "

    # Determine method display name
    method = "N/A"
    if design_result:
        method = "Monetary Unit Sampling (MUS)" if design_result.get("method") == "mus" else "Simple Random Sampling"
    elif evaluation_result:
        method = (
            "Monetary Unit Sampling (MUS)" if evaluation_result.get("method") == "mus" else "Simple Random Sampling"
        )

    scope_text += f"Sampling method: {method}."
    story.append(Paragraph(scope_text, styles["MemoBody"]))
    story.append(Spacer(1, 8))

    build_scope_statement(
        story,
        styles,
        doc_width,
        tool_domain="statistical_sampling",
        framework=resolved_framework,
        domain_label="statistical sampling",
    )

    # ─── 3. Design Parameters ────────────────────────────────
    if design_result:
        story.append(Paragraph("II. Design Parameters", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))

        scope_lines = [
            create_leader_dots("Population Size", f"{design_result.get('population_size', 0):,}"),
            create_leader_dots("Population Value", f"${design_result.get('population_value', 0):,.2f}"),
        ]

        for line in scope_lines:
            story.append(Paragraph(line, styles["MemoLeader"]))

        # ─── BUG-02: Population value clarifying note ──────────
        pop_note = design_result.get("population_value_note")
        if pop_note:
            story.append(
                Paragraph(
                    f"<i>{pop_note}</i>",
                    styles["MemoBodySmall"],
                )
            )
            story.append(Spacer(1, 4))

        confidence_lines = [
            create_leader_dots("Confidence Level", f"{design_result.get('confidence_level', 0):.0%}"),
            create_leader_dots("Confidence Factor", f"{design_result.get('confidence_factor', 0):.4f}"),
        ]
        for line in confidence_lines:
            story.append(Paragraph(line, styles["MemoLeader"]))

        # ─── BUG-04: Confidence factor derivation note ──────────
        conf_level = design_result.get("confidence_level", 0)
        conf_note = CONFIDENCE_FACTOR_NOTES.get(conf_level)
        if conf_note:
            conf_factor = design_result.get("confidence_factor", 0)
            story.append(
                Paragraph(
                    f"<i>Confidence factor of {conf_factor:.4f} corresponds to the "
                    f"{conf_note}. Per the Poisson distribution table used in MUS, "
                    f"the factor is derived as -ln(1 - confidence level).</i>",
                    styles["MemoBodySmall"],
                )
            )
            story.append(Spacer(1, 4))

        tm_em_lines = [
            create_leader_dots("Tolerable Misstatement", f"${design_result.get('tolerable_misstatement', 0):,.2f}"),
            create_leader_dots("Expected Misstatement", f"${design_result.get('expected_misstatement', 0):,.2f}"),
        ]
        for line in tm_em_lines:
            story.append(Paragraph(line, styles["MemoLeader"]))

        interval = design_result.get("sampling_interval")
        if interval is not None:
            story.append(Paragraph(create_leader_dots("Sampling Interval", f"${interval:,.2f}"), styles["MemoLeader"]))

        story.append(
            Paragraph(
                create_leader_dots("Calculated Sample Size", str(design_result.get("calculated_sample_size", 0))),
                styles["MemoLeader"],
            )
        )
        story.append(
            Paragraph(
                create_leader_dots("Actual Sample Size", str(design_result.get("actual_sample_size", 0))),
                styles["MemoLeader"],
            )
        )

        # ─── BUG-03: Sample size gap explanation ───────────────
        calc_size = design_result.get("calculated_sample_size", 0)
        actual_size = design_result.get("actual_sample_size", 0)
        if actual_size != calc_size and actual_size > 0 and calc_size > 0:
            diff = actual_size - calc_size
            hv_count = design_result.get("high_value_count", 0)
            rem_sample = design_result.get("remainder_sample_size", 0)
            strata = design_result.get("strata_summary", [])
            hv_threshold = ""
            if strata:
                hv_threshold = strata[0].get("threshold", "")

            sample_size_note = design_result.get("sample_size_note")
            if sample_size_note:
                note_text = sample_size_note
            elif hv_count > 0:
                note_text = (
                    f"Actual sample size increased from calculated {calc_size} to {actual_size} "
                    f"(+{diff} items, +{diff / calc_size:.1%}) due to stratification. "
                    f"All {hv_count} items in the High Value stratum ({hv_threshold}) are tested "
                    f"100%, plus {rem_sample} items selected from the Remainder stratum via "
                    f"systematic interval selection ({hv_count} + {rem_sample} = {actual_size})."
                )
            else:
                note_text = (
                    f"Actual sample size ({actual_size}) differs from calculated size "
                    f"({calc_size}) by {diff:+d} items due to interval rounding."
                )
            story.append(Paragraph(f"<i>{note_text}</i>", styles["MemoBodySmall"]))
            story.append(Spacer(1, 4))

        story.append(Spacer(1, 8))

        # ─── TM Derivation Note (CONTENT-10) ──────────────────
        tm_value = design_result.get("tolerable_misstatement", 0)
        story.append(Paragraph("<b>Tolerable Misstatement Derivation</b>", styles["MemoBody"]))
        story.append(
            Paragraph(
                f"The tolerable misstatement of ${tm_value:,.2f} was entered by the practitioner "
                "based on the engagement's overall materiality assessment. Per ISA 320.11, "
                "tolerable misstatement is the amount set by the auditor at less than materiality "
                "for the financial statements as a whole to reduce to an appropriately low level "
                "the probability that the aggregate of uncorrected and undetected misstatements "
                "exceeds materiality. The practitioner should document the basis for this amount "
                "in the engagement's materiality workpaper (e.g., WP-MAT-001).",
                styles["MemoBody"],
            )
        )
        story.append(Spacer(1, 8))

        # ─── IMP-01: Expected Misstatement Derivation ──────────
        em_value = design_result.get("expected_misstatement", 0)
        if em_value > 0:
            story.append(Paragraph("<b>Expected Misstatement Derivation</b>", styles["MemoBody"]))
            em_note = design_result.get("expected_misstatement_note")
            if em_note:
                em_text = em_note
            elif tm_value > 0:
                em_pct = em_value / tm_value * 100
                em_text = (
                    f"The expected misstatement of ${em_value:,.2f} was entered by the practitioner. "
                    f"This represents {em_pct:.1f}% of tolerable misstatement (${tm_value:,.2f}), "
                    "which is a common planning estimate when no prior year misstatement history is "
                    "available. Per ISA 530.A4, the expected misstatement should be based "
                    "on the auditor's knowledge of the client, including misstatements "
                    "identified in prior periods. If prior year misstatement data is "
                    "available, it should be used to refine this estimate."
                )
            else:
                em_text = f"The expected misstatement of ${em_value:,.2f} was entered by the practitioner."
            story.append(Paragraph(em_text, styles["MemoBody"]))
            story.append(Spacer(1, 8))

        # ─── Stratification Table ─────────────────────────────
        strata = design_result.get("strata_summary", [])
        if strata:
            story.append(Paragraph("III. Stratification", styles["MemoSection"]))
            story.append(LedgerRule(doc_width))

            strata_data = [["Stratum", "Threshold", "Count", "Value", "Sample"]]
            for s in strata:
                strata_data.append(
                    [
                        s.get("stratum", ""),
                        s.get("threshold", ""),
                        str(s.get("count", 0)),
                        f"${s.get('total_value', 0):,.2f}",
                        str(s.get("sample_size", 0)),
                    ]
                )

            strata_table = Table(strata_data, colWidths=[1.6 * inch, 1.4 * inch, 0.7 * inch, 1.4 * inch, 0.7 * inch])
            strata_table.setStyle(
                TableStyle(
                    [
                        ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                        ("FONTNAME", (0, 1), (-1, -1), "Times-Roman"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                        ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                        ("LINEBELOW", (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ("LEFTPADDING", (0, 0), (0, -1), 0),
                    ]
                )
            )
            story.append(strata_table)
            story.append(Spacer(1, 8))

    # ─── 4. Evaluation Results ────────────────────────────────
    if evaluation_result:
        section_num = (
            "IV" if design_result and design_result.get("strata_summary") else ("III" if design_result else "II")
        )
        story.append(Paragraph(f"{section_num}. Evaluation Results", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))

        eval_lines = [
            create_leader_dots("Sample Size", str(evaluation_result.get("sample_size", 0))),
            create_leader_dots("Errors Found", str(evaluation_result.get("errors_found", 0))),
            create_leader_dots("Total Misstatement", f"${evaluation_result.get('total_misstatement', 0):,.2f}"),
            create_leader_dots("Projected Misstatement", f"${evaluation_result.get('projected_misstatement', 0):,.2f}"),
            create_leader_dots("Basic Precision", f"${evaluation_result.get('basic_precision', 0):,.2f}"),
        ]

        if evaluation_result.get("incremental_allowance", 0) > 0:
            eval_lines.append(
                create_leader_dots(
                    "Incremental Allowance",
                    f"${evaluation_result.get('incremental_allowance', 0):,.2f}",
                )
            )

        eval_lines.append(
            create_leader_dots(
                "Upper Error Limit (UEL)",
                f"${evaluation_result.get('upper_error_limit', 0):,.2f}",
            )
        )
        eval_lines.append(
            create_leader_dots(
                "Tolerable Misstatement",
                f"${evaluation_result.get('tolerable_misstatement', 0):,.2f}",
            )
        )

        for line in eval_lines:
            story.append(Paragraph(line, styles["MemoLeader"]))
        story.append(Spacer(1, 8))

        # ─── Error Details Table ──────────────────────────────
        errors = evaluation_result.get("errors", [])
        if errors:
            story.append(Paragraph("Error Details", styles["MemoSection"]))
            story.append(LedgerRule(doc_width))

            error_data = [["#", "Item ID", "Recorded", "Audited", "Misstatement", "Tainting"]]
            for i, err in enumerate(errors[:20], 1):
                error_data.append(
                    [
                        str(i),
                        Paragraph(str(err.get("item_id", "")), styles["MemoTableCell"]),
                        f"${err.get('recorded_amount', 0):,.2f}",
                        f"${err.get('audited_amount', 0):,.2f}",
                        f"${err.get('misstatement', 0):,.2f}",
                        f"{err.get('tainting', 0):.1%}",
                    ]
                )

            error_table = Table(
                error_data,
                colWidths=[0.3 * inch, 1.2 * inch, 1.1 * inch, 1.1 * inch, 1.1 * inch, 0.8 * inch],
                repeatRows=1,
            )
            error_table.setStyle(
                TableStyle(
                    [
                        ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                        ("FONTNAME", (0, 1), (-1, -1), "Times-Roman"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                        ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                        ("LINEBELOW", (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                        ("LEFTPADDING", (0, 0), (0, -1), 0),
                    ]
                )
            )
            story.append(error_table)

            if len(errors) > 20:
                story.append(
                    Paragraph(
                        f"... and {len(errors) - 20} additional errors.",
                        styles["MemoBodySmall"],
                    )
                )
            story.append(Spacer(1, 8))

    # ─── 5. Methodology ──────────────────────────────────────
    next_num = _next_section_number(design_result, evaluation_result)
    story.append(Paragraph(f"{next_num}. Methodology", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    build_methodology_statement(
        story,
        styles,
        doc_width,
        tool_domain="statistical_sampling",
        framework=resolved_framework,
        domain_label="statistical sampling",
    )

    if method.startswith("Monetary"):
        methodology_text = (
            "Monetary Unit Sampling (MUS) was applied in accordance with ISA 530 and "
            "PCAOB AS 2315. The sample was selected using systematic dollar-interval "
            "selection with a cryptographically secure random start (Python secrets module). "
            "Sample evaluation uses the Stringer bound method, which calculates the "
            "upper error limit as: Basic Precision + Projected Misstatement + "
            "Incremental Allowance for sampling risk."
        )
    else:
        methodology_text = (
            "Simple random sampling was applied using Fisher-Yates shuffle with "
            "cryptographically secure random number generation (Python secrets module). "
            "Sample evaluation uses ratio estimation to project the sample misstatement "
            "rate to the population, with precision adjustment based on the confidence level."
        )

    story.append(Paragraph(methodology_text, styles["MemoBody"]))
    story.append(Spacer(1, 8))

    build_authoritative_reference_block(
        story,
        styles,
        doc_width,
        tool_domain="statistical_sampling",
        framework=resolved_framework,
        domain_label="statistical sampling",
    )

    # ─── 6. Conclusion / Status ───────────────────────────────
    if evaluation_result:
        next_num2 = _roman_after(next_num)
        story.append(Paragraph(f"{next_num2}. Conclusion", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))

        conclusion = evaluation_result.get("conclusion", "")
        detail = evaluation_result.get("conclusion_detail", "")

        if conclusion == "pass":
            conclusion_label = "UEL Within Tolerable Misstatement"
            color = ClassicalColors.SAGE
        else:
            conclusion_label = "UEL Exceeds Tolerable Misstatement — Further Evaluation Required"
            color = ClassicalColors.CLAY

        story.append(
            Paragraph(
                f'<font color="{color.hexval()}">{conclusion_label}</font>',
                styles["MemoSection"],
            )
        )
        story.append(Paragraph(detail, styles["MemoBody"]))
        story.append(Spacer(1, 12))
    elif design_result:
        next_num2 = _roman_after(next_num)
        story.append(Paragraph(f"{next_num2}. Status", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))
        story.append(
            Paragraph(
                f"Sample of {design_result.get('actual_sample_size', 0)} items has been selected. "
                "Evaluation pending — auditor must complete testing of selected items and "
                "upload results for evaluation.",
                styles["MemoBody"],
            )
        )
        story.append(Spacer(1, 12))

    # ─── 7. Sample Selection Preview (IMP-02) ─────────────────
    if design_result:
        selected_items = design_result.get("selected_items", [])
        if selected_items:
            if evaluation_result or design_result:
                preview_num = _roman_after(next_num2)
            else:
                preview_num = _roman_after(next_num)

            actual_size = design_result.get("actual_sample_size", len(selected_items))
            story.append(Paragraph(f"{preview_num}. Sample Selection Preview", styles["MemoSection"]))
            story.append(LedgerRule(doc_width))

            preview_count = min(len(selected_items), 10)
            story.append(
                Paragraph(
                    f"The following table shows the first {preview_count} items selected for testing, "
                    f"sorted by sampling order. The complete sample of {actual_size} items is available "
                    "as a CSV export from this report.",
                    styles["MemoBody"],
                )
            )
            story.append(Spacer(1, 6))

            preview_data = [["#", "Item Ref", "Description", "Amount", "Stratum"]]
            for i, item in enumerate(selected_items[:10], 1):
                desc = str(item.get("description", ""))[:40]
                if len(str(item.get("description", ""))) > 40:
                    desc += "..."
                preview_data.append(
                    [
                        str(i),
                        Paragraph(str(item.get("item_id", "")), styles["MemoTableCell"]),
                        Paragraph(desc, styles["MemoTableCell"]),
                        f"${item.get('recorded_amount', 0):,.2f}",
                        _format_stratum(item.get("stratum", "")),
                    ]
                )

            preview_table = Table(
                preview_data,
                colWidths=[0.3 * inch, 1.1 * inch, 2.2 * inch, 1.1 * inch, 1.1 * inch],
                repeatRows=1,
            )
            preview_table.setStyle(
                TableStyle(
                    [
                        ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                        ("FONTNAME", (0, 1), (-1, -1), "Times-Roman"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                        ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                        ("LINEBELOW", (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                        ("ALIGN", (3, 0), (3, -1), "RIGHT"),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                        ("LEFTPADDING", (0, 0), (0, -1), 0),
                    ]
                )
            )
            story.append(preview_table)
            story.append(Spacer(1, 6))

            story.append(
                Paragraph(
                    f"<i>Full sample listing ({actual_size} items) should be exported and "
                    "provided to the client as a document request. Items are listed in "
                    "systematic selection order — the random start was generated using a "
                    "cryptographically secure method (Python secrets module) to ensure "
                    "defensible randomness per ISA 530.</i>",
                    styles["MemoBodySmall"],
                )
            )
            story.append(Spacer(1, 12))

    # ─── 8. Next Steps (IMP-03) ───────────────────────────────
    # Determine section number for Next Steps
    if design_result and design_result.get("selected_items"):
        if evaluation_result or design_result:
            next_steps_num = _roman_after(preview_num)
        else:
            next_steps_num = _roman_after(_roman_after(next_num))
    elif evaluation_result or design_result:
        next_steps_num = _roman_after(next_num2)
    else:
        next_steps_num = _roman_after(next_num)

    story.append(Paragraph(f"{next_steps_num}. Next Steps", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    # Select population-type-specific steps
    pop_type = ""
    if design_result:
        pop_type = design_result.get("population_type", "")
    steps = NEXT_STEPS_BY_POPULATION_TYPE.get(pop_type.upper(), _NEXT_STEPS_GENERIC)

    # Add intro text for typed populations
    actual_size = 0
    tm_value = 0.0
    if design_result:
        actual_size = design_result.get("actual_sample_size", 0)
        tm_value = design_result.get("tolerable_misstatement", 0)

    if pop_type and actual_size > 0:
        story.append(
            Paragraph(
                f"The following {actual_size} items have been selected for "
                f"{pop_type.upper()} balance testing using "
                f"{method}. To complete the sampling procedure:",
                styles["MemoBody"],
            )
        )
        story.append(Spacer(1, 6))

    for step in steps:
        story.append(Paragraph(f"<b>{step['title']}</b>", styles["MemoBody"]))
        body = step["body"]
        # Substitute TM value if referenced
        if tm_value > 0 and "Tolerable Misstatement" in body:
            body = body.replace(
                "exceeds Tolerable Misstatement",
                f"exceeds ${tm_value:,.2f} (Tolerable Misstatement)",
            )
        story.append(Paragraph(body, styles["MemoBody"]))
        story.append(Spacer(1, 4))

    story.append(Spacer(1, 8))

    # ─── 9. Workpaper Signoff ─────────────────────────────────
    build_workpaper_signoff(
        story,
        styles,
        doc_width,
        prepared_by=prepared_by,
        reviewed_by=reviewed_by,
        workpaper_date=workpaper_date,
        include_signoff=include_signoff,
    )

    # ─── Intelligence Stamp ────────────────────────────────────
    build_intelligence_stamp(story, styles, client_name=client_name, period_tested=period_tested)

    # ─── 10. Disclaimer ────────────────────────────────────────
    build_disclaimer(
        story,
        styles,
        domain="statistical sampling",
        isa_reference="ISA 530 (Audit Sampling) and PCAOB AS 2315",
    )

    # Build (cover page gets footer; existing pages unchanged)
    doc.build(story, onFirstPage=draw_page_footer)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    log_secure_operation("sampling_memo_complete", f"Sampling memo generated ({len(pdf_bytes)} bytes)")
    return pdf_bytes


def _format_stratum(stratum: str) -> str:
    """Format stratum value for display."""
    if stratum == "high_value":
        return "High Value"
    elif stratum == "remainder":
        return "Remainder"
    return stratum.replace("_", " ").title() if stratum else ""


def _next_section_number(
    design_result: Optional[dict],
    evaluation_result: Optional[dict],
) -> str:
    """Calculate the next Roman numeral section number."""
    n = 2  # After Scope (I)
    if design_result:
        n += 1  # Design Parameters (II)
        if design_result.get("strata_summary"):
            n += 1  # Stratification (III)
    if evaluation_result:
        n += 1  # Evaluation Results
        if evaluation_result.get("errors"):
            pass  # Error Details is a sub-section
    return _roman(n)


def _roman(n: int) -> str:
    numerals = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI", 7: "VII", 8: "VIII", 9: "IX", 10: "X"}
    return numerals.get(n, str(n))


def _roman_after(current: str) -> str:
    """Return the next Roman numeral after the given one."""
    order = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
    try:
        idx = order.index(current)
        return order[idx + 1] if idx + 1 < len(order) else str(idx + 2)
    except ValueError:
        return current
