"""
Sampling Memo PDF Generator — Sprint 269, enriched Sprint 506/508
Phase XXXVI: Statistical Sampling (Tool 12)

Custom PDF structure (NOT using testing_memo_template — different workflow):
  Design report ("STATISTICAL SAMPLING MEMO — DESIGN"):
    I. Scope, II. Design Parameters, III. Stratification,
    IV. Methodology, V. Status, VI. Sample Selection Preview,
    VII. Next Steps (design-phase), Signoff, Disclaimer

  Evaluation report ("STATISTICAL SAMPLING MEMO — EVALUATION"):
    I. Scope, II. Design Parameters, III. Stratification,
    IV. Evaluation Results (+ Error Details + Summary + UEL Derivation),
    V. Methodology, VI. Conclusion (PASS/FAIL visual),
    VII. Next Steps (evaluation-phase), Signoff, Disclaimer
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

# Incremental change factors for Stringer bound (95% confidence)
# Used in UEL derivation display — must match sampling_engine.py
_INCREMENTAL_FACTORS_95: list[float] = [
    1.58,
    1.30,
    1.15,
    1.06,
    1.00,
    0.95,
    0.92,
    0.89,
    0.87,
    0.85,
    0.83,
]

# Error nature options for practitioners
ERROR_NATURE_OPTIONS: list[str] = [
    "Pricing error",
    "Cut-off",
    "Existence",
    "Valuation",
    "Classification",
    "Other",
]

# Next steps templates keyed by population type (DESIGN phase)
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


def _build_evaluation_next_steps(
    evaluation_result: dict[str, Any],
    design_result: Optional[dict[str, Any]],
) -> list[dict[str, str]]:
    """Build evaluation-phase next steps dynamically from results."""
    errors_found = evaluation_result.get("errors_found", 0)
    total_misstatement = evaluation_result.get("total_misstatement", 0)
    uel = evaluation_result.get("upper_error_limit", 0)
    tm = evaluation_result.get("tolerable_misstatement", 0)
    conclusion = evaluation_result.get("conclusion", "")
    conf_level = evaluation_result.get("confidence_level", 0.95)
    errors = evaluation_result.get("errors", [])

    error_ids = [e.get("item_id", "") for e in errors[:10]]
    error_id_text = ", ".join(error_ids) if error_ids else "the identified items"

    # Determine all-same direction
    directions = set()
    for e in errors:
        d = e.get("direction", "")
        if not d:
            if e.get("recorded_amount", 0) > e.get("audited_amount", 0):
                d = "Overstatement"
            elif e.get("recorded_amount", 0) < e.get("audited_amount", 0):
                d = "Understatement"
        directions.add(d)

    # Intro text
    if conclusion == "pass":
        intro = (
            f"Sampling evaluation is complete. UEL of ${uel:,.2f} does not exceed "
            f"Tolerable Misstatement of ${tm:,.2f}. The population is accepted at the "
            f"{conf_level:.0%} confidence level. The following actions are required to "
            "close out the sampling workpaper:"
        )
    else:
        intro = (
            f"Sampling evaluation is complete. UEL of ${uel:,.2f} exceeds "
            f"Tolerable Misstatement of ${tm:,.2f}. The population cannot be accepted "
            f"at the {conf_level:.0%} confidence level. Expand the sample or perform "
            "alternative procedures per ISA 530.17. If expanding, the following actions "
            "apply to errors already identified:"
        )

    pop_type = ""
    if design_result:
        pop_type = design_result.get("population_type", "").upper()

    # Build cross-reference step body based on population type
    cross_ref_body = (
        f"Cross-reference the {errors_found} identified errors to the related testing "
        f"memo. Confirm whether any of the sampled items ({error_id_text}) "
        "relate to findings in other workpapers."
    )

    steps = [
        {
            "title": "Step 1 — Communicate Identified Errors to Management",
            "body": (
                f"Present the {errors_found} identified errors "
                f"(${total_misstatement:,.2f} total) to management for their response. "
                "Request confirmation of whether management agrees the items are "
                "misstated and whether correcting entries will be posted. Document "
                "management's response in the engagement file."
            ),
        },
        {
            "title": "Step 2 — Obtain Evidence of Correction",
            "body": (
                "For any errors management agrees to correct, obtain the correcting "
                "journal entry or amended invoice before the engagement is finalized. "
                "If corrections relate to a subsequent period, confirm the adjustment "
                "was recorded in the correct period per ASC 250-10."
            ),
        },
        {
            "title": "Step 3 — Assess Uncorrected Misstatements",
            "body": (
                "If management declines to correct any identified error, accumulate "
                "the uncorrected amount in the summary of uncorrected misstatements "
                "per ISA 450. Assess whether the aggregate of uncorrected misstatements "
                "is material to the financial statements as a whole."
            ),
        },
        {
            "title": "Step 4 — Update Management Representation Letter",
            "body": (
                "Ensure the management representation letter (ISA 580) addresses the "
                "completeness of the population, management's acknowledgment of the "
                f"{errors_found} errors identified in sampling, and any related "
                "valuation or collectibility assertions."
            ),
        },
        {
            "title": "Step 5 — Cross-Reference to Related Workpapers",
            "body": cross_ref_body,
        },
    ]

    return steps, intro


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

    is_evaluation = evaluation_result is not None

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

    # ─── BUG-01: Phase-specific title ─────────────────────────
    if is_evaluation:
        report_title = "STATISTICAL SAMPLING MEMO \u2014 EVALUATION"
    else:
        report_title = "STATISTICAL SAMPLING MEMO \u2014 DESIGN"

    # ─── 0. Cover Page ───────────────────────────────────────
    logo_path = find_logo()
    cover_metadata = ReportMetadata(
        title=report_title,
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
        title=report_title,
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

        # ─── BUG-05: Error Details Table (with Nature + Direction) ──
        errors = evaluation_result.get("errors", [])
        if errors:
            story.append(Paragraph("Error Details", styles["MemoSection"]))
            story.append(LedgerRule(doc_width))

            # Check if any error has nature/direction fields
            has_nature = any(e.get("error_nature") for e in errors)
            has_direction = any(e.get("direction") for e in errors)

            if has_nature or has_direction:
                # 8-column table with Nature + Direction
                error_data = [
                    ["#", "Item ID", "Recorded", "Audited", "Misstatement", "Tainting", "Nature", "Direction"]
                ]
                total_misstatement_sum = 0.0
                all_directions = set()
                for i, err in enumerate(errors[:20], 1):
                    nature = err.get("error_nature", "Not specified")
                    direction = err.get("direction", "")
                    if not direction:
                        if err.get("recorded_amount", 0) > err.get("audited_amount", 0):
                            direction = "Overstatement"
                        elif err.get("recorded_amount", 0) < err.get("audited_amount", 0):
                            direction = "Understatement"
                        else:
                            direction = "N/A"
                    all_directions.add(direction)
                    total_misstatement_sum += err.get("misstatement", 0)
                    error_data.append(
                        [
                            str(i),
                            Paragraph(str(err.get("item_id", "")), styles["MemoTableCell"]),
                            f"${err.get('recorded_amount', 0):,.2f}",
                            f"${err.get('audited_amount', 0):,.2f}",
                            f"${err.get('misstatement', 0):,.2f}",
                            f"{err.get('tainting', 0):.1%}",
                            Paragraph(str(nature), styles["MemoTableCell"]),
                            Paragraph(str(direction), styles["MemoTableCell"]),
                        ]
                    )

                # Totals row
                dir_summary = (
                    "All overstated"
                    if all_directions == {"Overstatement"}
                    else ("All understated" if all_directions == {"Understatement"} else "Mixed")
                )
                error_data.append(
                    [
                        "",
                        Paragraph("<b>Total</b>", styles["MemoTableCell"]),
                        "",
                        "",
                        f"${total_misstatement_sum:,.2f}",
                        "",
                        "",
                        Paragraph(f"<b>{dir_summary}</b>", styles["MemoTableCell"]),
                    ]
                )

                col_widths = [
                    0.25 * inch,
                    0.75 * inch,
                    0.85 * inch,
                    0.85 * inch,
                    0.85 * inch,
                    0.6 * inch,
                    0.95 * inch,
                    0.9 * inch,
                ]
                error_table = Table(error_data, colWidths=col_widths, repeatRows=1)
                total_row_idx = len(error_data) - 1
                error_table.setStyle(
                    TableStyle(
                        [
                            ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                            ("FONTNAME", (0, 1), (-1, -1), "Times-Roman"),
                            ("FONTSIZE", (0, 0), (-1, -1), 8),
                            ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                            ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                            ("LINEBELOW", (0, 1), (-1, -2), 0.25, ClassicalColors.LEDGER_RULE),
                            ("LINEABOVE", (0, total_row_idx), (-1, total_row_idx), 1, ClassicalColors.OBSIDIAN_DEEP),
                            ("FONTNAME", (0, total_row_idx), (-1, total_row_idx), "Times-Bold"),
                            ("ALIGN", (2, 0), (5, -1), "RIGHT"),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("TOPPADDING", (0, 0), (-1, -1), 3),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                            ("LEFTPADDING", (0, 0), (0, -1), 0),
                        ]
                    )
                )
            else:
                # 6-column table (legacy — no nature/direction)
                error_data = [["#", "Item ID", "Recorded", "Audited", "Misstatement", "Tainting"]]
                total_misstatement_sum = 0.0
                for i, err in enumerate(errors[:20], 1):
                    total_misstatement_sum += err.get("misstatement", 0)
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

                # Totals row
                error_data.append(
                    [
                        "",
                        Paragraph("<b>Total</b>", styles["MemoTableCell"]),
                        "",
                        "",
                        f"${total_misstatement_sum:,.2f}",
                        "",
                    ]
                )

                col_widths = [0.3 * inch, 1.2 * inch, 1.1 * inch, 1.1 * inch, 1.1 * inch, 0.8 * inch]
                error_table = Table(error_data, colWidths=col_widths, repeatRows=1)
                total_row_idx = len(error_data) - 1
                error_table.setStyle(
                    TableStyle(
                        [
                            ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                            ("FONTNAME", (0, 1), (-1, -1), "Times-Roman"),
                            ("FONTSIZE", (0, 0), (-1, -1), 9),
                            ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                            ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                            ("LINEBELOW", (0, 1), (-1, -2), 0.25, ClassicalColors.LEDGER_RULE),
                            ("LINEABOVE", (0, total_row_idx), (-1, total_row_idx), 1, ClassicalColors.OBSIDIAN_DEEP),
                            ("FONTNAME", (0, total_row_idx), (-1, total_row_idx), "Times-Bold"),
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

            # ─── IMP-01: Error Summary Statistics ────────────────
            _build_error_summary(story, styles, doc_width, evaluation_result)

        # ─── BUG-03: UEL Derivation ─────────────────────────────
        _build_uel_derivation(story, styles, doc_width, evaluation_result, design_result)

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

    # ─── IMP-02: ASC 450-20 relevance footnote ────────────────
    if is_evaluation:
        story.append(
            Paragraph(
                "<i>\u2020 ASC 450-20 applies when identified misstatements indicate a "
                "probable loss contingency meeting recognition criteria under "
                "ASC 450-20-25. Relevant if projected misstatements suggest a probable "
                "loss contingency requiring accrual or disclosure.</i>",
                styles["MemoBodySmall"],
            )
        )
        story.append(Spacer(1, 8))

    # ─── 6. Conclusion / Status ───────────────────────────────
    if evaluation_result:
        next_num2 = _roman_after(next_num)
        story.append(Paragraph(f"{next_num2}. Conclusion", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))

        conclusion = evaluation_result.get("conclusion", "")
        detail = evaluation_result.get("conclusion_detail", "")
        uel = evaluation_result.get("upper_error_limit", 0)
        tm = evaluation_result.get("tolerable_misstatement", 0)
        conf_level = evaluation_result.get("confidence_level", 0.95)
        errors_found = evaluation_result.get("errors_found", 0)

        # ─── BUG-04: PASS/FAIL Visual Conclusion Block ──────────
        is_pass = conclusion == "pass"
        _build_pass_fail_block(story, styles, doc_width, is_pass, uel, tm, conf_level, errors_found)
        story.append(Spacer(1, 8))

        if is_pass:
            conclusion_label = "UEL Within Tolerable Misstatement"
            color = ClassicalColors.SAGE
        else:
            conclusion_label = "UEL Exceeds Tolerable Misstatement \u2014 Further Evaluation Required"
            color = ClassicalColors.CLAY

        story.append(
            Paragraph(
                f'<font color="{color.hexval()}">{conclusion_label}</font>',
                styles["MemoSection"],
            )
        )
        story.append(Paragraph(detail, styles["MemoBody"]))
        story.append(Spacer(1, 6))

        # ─── BUG-06: Conditional correction status ───────────────
        correction_status = evaluation_result.get("correction_status")
        if correction_status == "confirmed":
            correction_note = evaluation_result.get("correction_note", "")
            story.append(
                Paragraph(
                    f"<i>Management has indicated the identified errors were corrected in "
                    f"the subsequent period. {correction_note}"
                    "Obtain written confirmation and the correcting journal entry reference "
                    "before relying on this assertion. Document in the engagement file "
                    "per ISA 450.</i>",
                    styles["MemoBody"],
                )
            )
        else:
            story.append(
                Paragraph(
                    "<i>Correction status: Not confirmed. Obtain management's response to "
                    "the identified errors and document whether correcting entries were "
                    "posted. See Next Steps \u2014 Step 1.</i>",
                    styles["MemoBody"],
                )
            )

        story.append(Spacer(1, 12))
    elif design_result:
        next_num2 = _roman_after(next_num)
        story.append(Paragraph(f"{next_num2}. Status", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))
        story.append(
            Paragraph(
                f"Sample of {design_result.get('actual_sample_size', 0)} items has been selected. "
                "Evaluation pending \u2014 auditor must complete testing of selected items and "
                "upload results for evaluation.",
                styles["MemoBody"],
            )
        )
        story.append(Spacer(1, 12))

    # ─── 7. Sample Selection Preview (DESIGN ONLY) ────────────
    if design_result and not is_evaluation:
        selected_items = design_result.get("selected_items", [])
        if selected_items:
            preview_num = _roman_after(next_num2)

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
                    "systematic selection order \u2014 the random start was generated using a "
                    "cryptographically secure method (Python secrets module) to ensure "
                    "defensible randomness per ISA 530.</i>",
                    styles["MemoBodySmall"],
                )
            )
            story.append(Spacer(1, 12))

    # ─── 8. Next Steps ─────────────────────────────────────────
    # Determine section number for Next Steps
    if not is_evaluation and design_result and design_result.get("selected_items"):
        next_steps_num = _roman_after(preview_num)
    elif evaluation_result or design_result:
        next_steps_num = _roman_after(next_num2)
    else:
        next_steps_num = _roman_after(next_num)

    story.append(Paragraph(f"{next_steps_num}. Next Steps", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    # ─── BUG-02: Evaluation-phase next steps ─────────────────
    if is_evaluation:
        eval_steps, intro_text = _build_evaluation_next_steps(evaluation_result, design_result)
        story.append(Paragraph(intro_text, styles["MemoBody"]))
        story.append(Spacer(1, 6))
        for step in eval_steps:
            story.append(Paragraph(f"<b>{step['title']}</b>", styles["MemoBody"]))
            story.append(Paragraph(step["body"], styles["MemoBody"]))
            story.append(Spacer(1, 4))
    else:
        # Design-phase: population-type-specific steps
        pop_type = ""
        if design_result:
            pop_type = design_result.get("population_type", "")
        steps = NEXT_STEPS_BY_POPULATION_TYPE.get(pop_type.upper(), _NEXT_STEPS_GENERIC)

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


# ═══════════════════════════════════════════════════════════════
# Section Builders
# ═══════════════════════════════════════════════════════════════


def _build_pass_fail_block(
    story: list,
    styles: dict,
    doc_width: float,
    is_pass: bool,
    uel: float,
    tm: float,
    confidence_level: float,
    errors_found: int,
) -> None:
    """BUG-04: Render a prominent PASS/FAIL visual conclusion block."""
    if is_pass:
        symbol = "\u2713"  # checkmark
        label = "PASS"
        comparison = f"UEL ${uel:,.2f}  <  TM ${tm:,.2f}"
        border_color = ClassicalColors.SAGE
        text_color = ClassicalColors.SAGE
    else:
        symbol = "\u2717"  # X mark
        label = "FAIL"
        comparison = f"UEL ${uel:,.2f}  \u2265  TM ${tm:,.2f}"
        border_color = ClassicalColors.CLAY
        text_color = ClassicalColors.CLAY

    conclusion_line = f"SAMPLING CONCLUSION:  {symbol} {label}"
    detail_line = f"Confidence: {confidence_level:.0%}   |   Errors: {errors_found}"

    block_data = [
        [
            Paragraph(
                f'<font color="{text_color.hexval()}" size="12"><b>{conclusion_line}</b></font>', styles["MemoBody"]
            )
        ],
        [Paragraph(f'<font size="10">{comparison}</font>', styles["MemoBody"])],
        [
            Paragraph(
                f'<font size="9" color="{ClassicalColors.OBSIDIAN_500.hexval()}">{detail_line}</font>',
                styles["MemoBody"],
            )
        ],
    ]

    if not is_pass:
        block_data.append(
            [
                Paragraph(
                    '<font size="8" color="#616161">Expand sample or perform alternative procedures per ISA 530.17</font>',
                    styles["MemoBody"],
                )
            ]
        )

    block_table = Table(block_data, colWidths=[doc_width - 0.4 * inch])
    block_table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1.5, border_color),
                ("BACKGROUND", (0, 0), (-1, -1), ClassicalColors.OATMEAL_PAPER),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]
        )
    )
    story.append(block_table)


def _build_error_summary(
    story: list,
    styles: dict,
    doc_width: float,
    evaluation_result: dict[str, Any],
) -> None:
    """IMP-01: Error summary statistics block below error detail table."""
    errors = evaluation_result.get("errors", [])
    if not errors:
        return

    errors_found = evaluation_result.get("errors_found", len(errors))
    sample_size = evaluation_result.get("sample_size", 0)
    total_misstatement = evaluation_result.get("total_misstatement", 0)
    projected = evaluation_result.get("projected_misstatement", 0)
    expected = evaluation_result.get("expected_misstatement", 0)
    uel = evaluation_result.get("upper_error_limit", 0)
    tm = evaluation_result.get("tolerable_misstatement", 0)

    # Determine direction summary
    directions = set()
    natures = []
    largest_error = None
    largest_amount = 0
    for e in errors:
        d = e.get("direction", "")
        if not d:
            if e.get("recorded_amount", 0) > e.get("audited_amount", 0):
                d = "Overstatement"
            elif e.get("recorded_amount", 0) < e.get("audited_amount", 0):
                d = "Understatement"
        directions.add(d)
        if e.get("error_nature"):
            natures.append(e["error_nature"])
        m = abs(e.get("misstatement", 0))
        if m > largest_amount:
            largest_amount = m
            largest_error = e

    error_rate = errors_found / sample_size * 100 if sample_size > 0 else 0

    dir_text = (
        "Overstatements"
        if directions == {"Overstatement"}
        else ("Understatements" if directions == {"Understatement"} else "Mixed (over + under)")
    )

    story.append(Paragraph("<b>Error Summary</b>", styles["MemoBody"]))

    summary_lines = [
        create_leader_dots(
            "Errors Found", f"{errors_found} of {sample_size} items tested   ({error_rate:.1f}% error rate)"
        ),
        create_leader_dots("Total Actual Misstatement", f"${total_misstatement:,.2f}"),
        create_leader_dots("All errors", dir_text),
    ]

    # Nature summary
    if natures:
        from collections import Counter

        nature_counts = Counter(natures)
        nature_parts = [f"{n} ({c} of {len(natures)})" for n, c in nature_counts.most_common()]
        summary_lines.append(create_leader_dots("Error nature", "; ".join(nature_parts)))

    # Largest single error
    if largest_error:
        largest_pct = largest_amount / total_misstatement * 100 if total_misstatement > 0 else 0
        summary_lines.append(
            create_leader_dots(
                "Largest single error",
                f"{largest_error.get('item_id', '')}  ${largest_amount:,.2f}  ({largest_pct:.1f}% of total misstatement)",
            )
        )

    # Projected vs expected
    summary_lines.append(create_leader_dots("Projected misstatement", f"${projected:,.2f}"))
    if expected > 0:
        diff = projected - expected
        direction_word = "above" if diff > 0 else "below"
        favorability = "unfavorable" if diff > 0 else "favorable"
        summary_lines.append(
            create_leader_dots(
                "Projection vs. expected",
                f"${abs(diff):,.2f} {direction_word} expected \u2014 {favorability}",
            )
        )

    # UEL headroom
    if tm > 0:
        headroom = tm - uel
        headroom_pct = uel / tm * 100
        remaining_pct = 100 - headroom_pct
        summary_lines.append(
            create_leader_dots(
                "UEL headroom",
                f"${tm:,.2f} - ${uel:,.2f} = ${headroom:,.2f}",
            )
        )
        summary_lines.append(
            create_leader_dots(
                "As % of TM",
                f"{headroom_pct:.1f}% of TM utilized   ({remaining_pct:.1f}% headroom)",
            )
        )

    for line in summary_lines:
        story.append(Paragraph(line, styles["MemoLeader"]))
    story.append(Spacer(1, 12))


def _build_uel_derivation(
    story: list,
    styles: dict,
    doc_width: float,
    evaluation_result: dict[str, Any],
    design_result: Optional[dict[str, Any]],
) -> None:
    """BUG-03: UEL derivation block showing Stringer bound computation."""
    errors = evaluation_result.get("errors", [])
    bp = evaluation_result.get("basic_precision", 0)
    projected = evaluation_result.get("projected_misstatement", 0)
    incremental = evaluation_result.get("incremental_allowance", 0)
    uel = evaluation_result.get("upper_error_limit", 0)
    tm = evaluation_result.get("tolerable_misstatement", 0)

    # Get sampling interval
    si = 0.0
    if design_result:
        si = design_result.get("sampling_interval", 0) or 0
    if si == 0:
        si = evaluation_result.get("sampling_interval", 0) or 0

    conf_factor = 3.0
    if design_result:
        conf_factor = design_result.get("confidence_factor", 3.0)

    story.append(Paragraph("<b>UEL Derivation (Stringer Bound Method)</b>", styles["MemoBody"]))
    story.append(Spacer(1, 4))

    # 1. Basic Precision
    story.append(Paragraph("<b>1. Basic Precision</b>", styles["MemoBody"]))
    if si > 0:
        bp_computed = si * conf_factor
        story.append(
            Paragraph(
                "Formula: Sampling Interval \u00d7 Confidence Factor at 0 errors",
                styles["MemoBody"],
            )
        )
        story.append(
            Paragraph(
                f"Computation: ${si:,.2f} \u00d7 {conf_factor:.4f} = ${bp_computed:,.2f}",
                styles["MemoBody"],
            )
        )
        story.append(
            Paragraph(
                "<i>Basic Precision represents the minimum precision achievable with "
                "this sample even if no errors are found. It equals the confidence "
                "factor multiplied by one sampling interval.</i>",
                styles["MemoBodySmall"],
            )
        )
    else:
        story.append(Paragraph(f"Basic Precision = ${bp:,.2f}", styles["MemoBody"]))
    story.append(Spacer(1, 6))

    # 2. Projected Misstatement
    story.append(Paragraph("<b>2. Projected Misstatement</b>", styles["MemoBody"]))
    if errors and si > 0:
        # Sort by tainting desc (Stringer method)
        sorted_errors = sorted(errors, key=lambda e: e.get("tainting", 0), reverse=True)
        projected_sum = 0.0
        for i, err in enumerate(sorted_errors, 1):
            tainting = err.get("tainting", 0)
            item_id = err.get("item_id", f"Error {i}")
            proj_amount = tainting * si
            projected_sum += proj_amount
            story.append(
                Paragraph(
                    f"Error {i} ({item_id}, tainting {tainting:.1%}): "
                    f"{tainting:.4f} \u00d7 ${si:,.2f} = ${proj_amount:,.2f}",
                    styles["MemoBody"],
                )
            )
        story.append(
            Paragraph(
                f"Total Projected Misstatement: ${projected_sum:,.2f}",
                styles["MemoBody"],
            )
        )
    else:
        story.append(Paragraph(f"Projected Misstatement = ${projected:,.2f}", styles["MemoBody"]))
    story.append(Spacer(1, 6))

    # 3. Incremental Allowance
    if incremental > 0:
        story.append(Paragraph("<b>3. Incremental Allowance</b>", styles["MemoBody"]))
        if errors and si > 0:
            story.append(
                Paragraph(
                    "Formula: \u03a3 (tainting \u00d7 sampling interval \u00d7 (incremental factor \u2212 1.0))",
                    styles["MemoBody"],
                )
            )
            story.append(
                Paragraph(
                    "<i>Per Poisson table (95% confidence), incremental factors decrease "
                    "with each successive error, reflecting the diminishing marginal impact "
                    "on the upper error limit.</i>",
                    styles["MemoBodySmall"],
                )
            )
            sorted_errors = sorted(errors, key=lambda e: e.get("tainting", 0), reverse=True)
            inc_sum = 0.0
            factors = _INCREMENTAL_FACTORS_95
            for i, err in enumerate(sorted_errors):
                tainting = err.get("tainting", 0)
                item_id = err.get("item_id", f"Error {i + 1}")
                factor = factors[i] if i < len(factors) else factors[-1]
                inc_amount = tainting * si * max(factor - 1.0, 0.0)
                inc_sum += inc_amount
                story.append(
                    Paragraph(
                        f"Error {i + 1} ({item_id}): factor {factor:.2f} \u2212 1.0 = {factor - 1.0:.2f}; "
                        f"{tainting:.4f} \u00d7 ${si:,.2f} \u00d7 {factor - 1.0:.2f} = ${inc_amount:,.2f}",
                        styles["MemoBody"],
                    )
                )
            story.append(Paragraph(f"Total Incremental Allowance: ${inc_sum:,.2f}", styles["MemoBody"]))
        else:
            story.append(Paragraph(f"Incremental Allowance = ${incremental:,.2f}", styles["MemoBody"]))
        story.append(Spacer(1, 6))

    # 4. Upper Error Limit
    step_num = "4" if incremental > 0 else "3"
    story.append(Paragraph(f"<b>{step_num}. Upper Error Limit</b>", styles["MemoBody"]))
    if incremental > 0:
        formula = "UEL = Basic Precision + Projected Misstatement + Incremental Allowance"
        computation = f"UEL = ${bp:,.2f} + ${projected:,.2f} + ${incremental:,.2f} = ${uel:,.2f}"
    else:
        formula = "UEL = Basic Precision + Projected Misstatement"
        computation = f"UEL = ${bp:,.2f} + ${projected:,.2f} = ${uel:,.2f}"
    story.append(Paragraph(formula, styles["MemoBody"]))
    story.append(Paragraph(computation, styles["MemoBody"]))

    # PASS/FAIL inline
    if uel <= tm:
        story.append(
            Paragraph(
                f'<font color="{ClassicalColors.SAGE.hexval()}">'
                f"UEL (${uel:,.2f}) &lt; TM (${tm:,.2f}) \u2192 PASS</font>",
                styles["MemoBody"],
            )
        )
    else:
        story.append(
            Paragraph(
                f'<font color="{ClassicalColors.CLAY.hexval()}">'
                f"UEL (${uel:,.2f}) \u2265 TM (${tm:,.2f}) \u2192 FAIL</font>",
                styles["MemoBody"],
            )
        )
    story.append(Spacer(1, 12))


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════


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


def _roman_after(current: str) -> str:
    """Return the next Roman numeral after the given one."""
    order = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
    try:
        idx = order.index(current)
        return order[idx + 1] if idx + 1 < len(order) else str(idx + 2)
    except ValueError:
        return current
