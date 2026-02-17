"""
Sampling Memo PDF Generator — Sprint 269
Phase XXXVI: Statistical Sampling (Tool 12)

Custom PDF structure (NOT using testing_memo_template — different workflow):
  1. Header (client, period, reference)
  2. Scope (ISA 530 reference, parameters)
  3. Design Parameters (method, confidence, thresholds)
  4. Stratification Summary (if applicable)
  5. Evaluation Results (if Phase 2 completed)
  6. Error Details (if errors found)
  7. Methodology
  8. Conclusion (color-coded Pass/Fail)
  9. Workpaper Signoff
  10. Disclaimer
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
    build_disclaimer,
    build_memo_header,
    build_workpaper_signoff,
    create_memo_styles,
)


def generate_sampling_design_memo(
    design_result: dict[str, Any],
    filename: str = "population",
    client_name: Optional[str] = None,
    period_tested: Optional[str] = None,
    prepared_by: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    workpaper_date: Optional[str] = None,
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

    # ─── 1. Header ───────────────────────────────────────────
    build_memo_header(
        story, styles, doc_width,
        title="STATISTICAL SAMPLING MEMO",
        reference=ref_number,
        client_name=client_name,
    )

    # ─── 2. Scope ────────────────────────────────────────────
    story.append(Paragraph("I. SCOPE", styles['MemoSection']))
    story.append(LedgerRule(doc_width))

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
        method = "Monetary Unit Sampling (MUS)" if evaluation_result.get("method") == "mus" else "Simple Random Sampling"

    scope_text += f"Sampling method: {method}."
    story.append(Paragraph(scope_text, styles['MemoBody']))
    story.append(Spacer(1, 8))

    # ─── 3. Design Parameters ────────────────────────────────
    if design_result:
        story.append(Paragraph("II. DESIGN PARAMETERS", styles['MemoSection']))
        story.append(LedgerRule(doc_width))

        scope_lines = [
            create_leader_dots("Population Size", f"{design_result.get('population_size', 0):,}"),
            create_leader_dots("Population Value", f"${design_result.get('population_value', 0):,.2f}"),
            create_leader_dots("Confidence Level", f"{design_result.get('confidence_level', 0):.0%}"),
            create_leader_dots("Confidence Factor", f"{design_result.get('confidence_factor', 0):.4f}"),
            create_leader_dots("Tolerable Misstatement", f"${design_result.get('tolerable_misstatement', 0):,.2f}"),
            create_leader_dots("Expected Misstatement", f"${design_result.get('expected_misstatement', 0):,.2f}"),
        ]

        interval = design_result.get("sampling_interval")
        if interval is not None:
            scope_lines.append(create_leader_dots("Sampling Interval", f"${interval:,.2f}"))

        scope_lines.append(create_leader_dots("Calculated Sample Size", str(design_result.get("calculated_sample_size", 0))))
        scope_lines.append(create_leader_dots("Actual Sample Size", str(design_result.get("actual_sample_size", 0))))

        for line in scope_lines:
            story.append(Paragraph(line, styles['MemoLeader']))
        story.append(Spacer(1, 8))

        # ─── Stratification Table ─────────────────────────────
        strata = design_result.get("strata_summary", [])
        if strata:
            story.append(Paragraph("III. STRATIFICATION", styles['MemoSection']))
            story.append(LedgerRule(doc_width))

            strata_data = [["Stratum", "Threshold", "Count", "Value", "Sample"]]
            for s in strata:
                strata_data.append([
                    s.get("stratum", ""),
                    s.get("threshold", ""),
                    str(s.get("count", 0)),
                    f"${s.get('total_value', 0):,.2f}",
                    str(s.get("sample_size", 0)),
                ])

            strata_table = Table(strata_data, colWidths=[
                1.6 * inch, 1.4 * inch, 0.7 * inch, 1.4 * inch, 0.7 * inch
            ])
            strata_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('TEXTCOLOR', (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                ('LINEBELOW', (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                ('LINEBELOW', (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LEFTPADDING', (0, 0), (0, -1), 0),
            ]))
            story.append(strata_table)
            story.append(Spacer(1, 8))

    # ─── 4. Evaluation Results ────────────────────────────────
    if evaluation_result:
        section_num = "IV" if design_result and design_result.get("strata_summary") else (
            "III" if design_result else "II"
        )
        story.append(Paragraph(f"{section_num}. EVALUATION RESULTS", styles['MemoSection']))
        story.append(LedgerRule(doc_width))

        eval_lines = [
            create_leader_dots("Sample Size", str(evaluation_result.get("sample_size", 0))),
            create_leader_dots("Errors Found", str(evaluation_result.get("errors_found", 0))),
            create_leader_dots("Total Misstatement", f"${evaluation_result.get('total_misstatement', 0):,.2f}"),
            create_leader_dots("Projected Misstatement", f"${evaluation_result.get('projected_misstatement', 0):,.2f}"),
            create_leader_dots("Basic Precision", f"${evaluation_result.get('basic_precision', 0):,.2f}"),
        ]

        if evaluation_result.get("incremental_allowance", 0) > 0:
            eval_lines.append(create_leader_dots(
                "Incremental Allowance",
                f"${evaluation_result.get('incremental_allowance', 0):,.2f}",
            ))

        eval_lines.append(create_leader_dots(
            "Upper Error Limit (UEL)",
            f"${evaluation_result.get('upper_error_limit', 0):,.2f}",
        ))
        eval_lines.append(create_leader_dots(
            "Tolerable Misstatement",
            f"${evaluation_result.get('tolerable_misstatement', 0):,.2f}",
        ))

        for line in eval_lines:
            story.append(Paragraph(line, styles['MemoLeader']))
        story.append(Spacer(1, 8))

        # ─── Error Details Table ──────────────────────────────
        errors = evaluation_result.get("errors", [])
        if errors:
            story.append(Paragraph("ERROR DETAILS", styles['MemoSection']))
            story.append(LedgerRule(doc_width))

            error_data = [["#", "Item ID", "Recorded", "Audited", "Misstatement", "Tainting"]]
            for i, err in enumerate(errors[:20], 1):
                error_data.append([
                    str(i),
                    str(err.get("item_id", ""))[:20],
                    f"${err.get('recorded_amount', 0):,.2f}",
                    f"${err.get('audited_amount', 0):,.2f}",
                    f"${err.get('misstatement', 0):,.2f}",
                    f"{err.get('tainting', 0):.1%}",
                ])

            error_table = Table(error_data, colWidths=[
                0.3 * inch, 1.2 * inch, 1.1 * inch, 1.1 * inch, 1.1 * inch, 0.8 * inch
            ])
            error_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('TEXTCOLOR', (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                ('LINEBELOW', (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                ('LINEBELOW', (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('LEFTPADDING', (0, 0), (0, -1), 0),
            ]))
            story.append(error_table)

            if len(errors) > 20:
                story.append(Paragraph(
                    f"... and {len(errors) - 20} additional errors.",
                    styles['MemoBodySmall'],
                ))
            story.append(Spacer(1, 8))

    # ─── 5. Methodology ──────────────────────────────────────
    next_num = _next_section_number(design_result, evaluation_result)
    story.append(Paragraph(f"{next_num}. METHODOLOGY", styles['MemoSection']))
    story.append(LedgerRule(doc_width))

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

    story.append(Paragraph(methodology_text, styles['MemoBody']))
    story.append(Spacer(1, 8))

    # ─── 6. Conclusion ────────────────────────────────────────
    if evaluation_result:
        next_num2 = _roman_after(next_num)
        story.append(Paragraph(f"{next_num2}. CONCLUSION", styles['MemoSection']))
        story.append(LedgerRule(doc_width))

        conclusion = evaluation_result.get("conclusion", "")
        detail = evaluation_result.get("conclusion_detail", "")

        if conclusion == "pass":
            conclusion_label = "PASS — POPULATION ACCEPTED"
            color = ClassicalColors.SAGE
        else:
            conclusion_label = "FAIL — POPULATION NOT ACCEPTED"
            color = ClassicalColors.CLAY

        story.append(Paragraph(
            f'<font color="{color.hexval()}">{conclusion_label}</font>',
            styles['MemoSection'],
        ))
        story.append(Paragraph(detail, styles['MemoBody']))
        story.append(Spacer(1, 12))
    elif design_result:
        next_num2 = _roman_after(next_num)
        story.append(Paragraph(f"{next_num2}. STATUS", styles['MemoSection']))
        story.append(LedgerRule(doc_width))
        story.append(Paragraph(
            f"Sample of {design_result.get('actual_sample_size', 0)} items has been selected. "
            "Evaluation pending — auditor must complete testing of selected items and "
            "upload results for evaluation.",
            styles['MemoBody'],
        ))
        story.append(Spacer(1, 12))

    # ─── 7. Workpaper Signoff ─────────────────────────────────
    build_workpaper_signoff(
        story, styles, doc_width,
        prepared_by=prepared_by,
        reviewed_by=reviewed_by,
        workpaper_date=workpaper_date,
    )

    # ─── 8. Disclaimer ────────────────────────────────────────
    build_disclaimer(
        story, styles,
        domain="statistical sampling",
        isa_reference="ISA 530 (Audit Sampling) and PCAOB AS 2315",
    )

    # Build
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    log_secure_operation("sampling_memo_complete", f"Sampling memo generated ({len(pdf_bytes)} bytes)")
    return pdf_bytes


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
    numerals = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V",
                6: "VI", 7: "VII", 8: "VIII", 9: "IX", 10: "X"}
    return numerals.get(n, str(n))


def _roman_after(current: str) -> str:
    """Return the next Roman numeral after the given one."""
    order = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
    try:
        idx = order.index(current)
        return order[idx + 1] if idx + 1 < len(order) else str(idx + 2)
    except ValueError:
        return current
