"""
Paciolus — Pre-Flight Report PDF Memo Generator
Sprint 283: Phase XXXVIII
Sprint 510: Balance check, conclusion, score breakdown, affected items,
            severity column fix, low-confidence notes, tests_affected column

Custom memo using memo_base.py primitives. Not TestingMemoConfig — preflight
is a diagnostic check, not a testing tool.

Sections: Cover → Scope (with score breakdown) → TB Balance Check →
          Column Detection (with low-confidence notes) → Issues (sorted by
          tests_affected) → Methodology → Authoritative References →
          Conclusion → Sign-Off → Disclaimer
"""

from typing import Optional

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from pdf_generator import ClassicalColors, LedgerRule, create_leader_dots, generate_reference_number
from shared.framework_resolution import ResolvedFramework
from shared.memo_base import (
    build_disclaimer,
    build_intelligence_stamp,
    build_workpaper_signoff,
    create_memo_styles,
    wrap_table_strings,
)
from shared.memo_template import _roman
from shared.report_chrome import ReportMetadata, build_cover_page, draw_page_footer, find_logo
from shared.scope_methodology import (
    build_authoritative_reference_block,
    build_methodology_statement,
    build_scope_statement,
)

# ═══════════════════════════════════════════════════════════════
# Component display names for score breakdown
# ═══════════════════════════════════════════════════════════════

_COMPONENT_DISPLAY_NAMES: dict[str, str] = {
    "tb_balance": "TB Balance Check",
    "column_detection": "Column Detection",
    "null_values": "Data Completeness",
    "duplicates": "Duplicate Detection",
    "encoding": "Encoding Quality",
    "mixed_signs": "Sign Convention",
    "zero_balance": "Active Balances",
}


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
    fiscal_year_end: Optional[str] = None,
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
    reference = generate_reference_number().replace("PAC-", "PFR-")

    # ── Cover Page ──
    logo_path = find_logo()
    metadata = ReportMetadata(
        title="Data Quality Pre-Flight Report",
        client_name=client_name or "",
        engagement_period=period_tested or "",
        source_document=filename,
        source_document_title=source_document_title or "",
        source_context_note=source_context_note or "",
        reference=reference,
        fiscal_year_end=fiscal_year_end or "",
    )
    build_cover_page(story, styles, metadata, doc_width, logo_path)

    section_counter = 1

    # ── I. SCOPE ──
    story.append(Paragraph(f"{_roman(section_counter)}. Scope", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    readiness = preflight_result.get("readiness_score", 0)
    label = preflight_result.get("readiness_label", "Unknown")

    # Source document transparency
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
    if period_tested:
        scope_lines.insert(0, create_leader_dots("Period Tested", period_tested))

    for line in scope_lines:
        story.append(Paragraph(line, styles["MemoLeader"]))
    story.append(Spacer(1, 8))

    # ── Score Breakdown (IMP-01) ──
    score_breakdown = preflight_result.get("score_breakdown", [])
    if score_breakdown:
        story.append(Paragraph("Readiness Score Breakdown", styles["MemoTableHeader"]))
        story.append(Spacer(1, 4))

        breakdown_data = [["Component", "Weight", "Score", "Contribution"]]
        total_contribution = 0.0
        for sc in score_breakdown:
            weight_pct = f"{sc.get('weight', 0) * 100:.0f}%"
            score_val = f"{sc.get('score', 0):.1f}"
            contribution = sc.get("contribution", 0)
            total_contribution += contribution
            component_name = _COMPONENT_DISPLAY_NAMES.get(sc.get("component", ""), sc.get("component", ""))
            breakdown_data.append([component_name, weight_pct, score_val, f"{contribution:.1f}"])

        breakdown_data.append(["Total", "100%", "", f"{total_contribution:.1f} / 100"])

        breakdown_data = wrap_table_strings(breakdown_data, styles)
        breakdown_table = Table(
            breakdown_data,
            colWidths=[2.2 * inch, 0.8 * inch, 0.8 * inch, 1.2 * inch],
        )
        breakdown_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                    ("FONTNAME", (0, 1), (-1, -2), "Times-Roman"),
                    ("FONTNAME", (0, -1), (-1, -1), "Times-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                    ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                    ("LINEBELOW", (0, 1), (-1, -2), 0.25, ClassicalColors.LEDGER_RULE),
                    ("LINEABOVE", (0, -1), (-1, -1), 1, ClassicalColors.OBSIDIAN_DEEP),
                    ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("LEFTPADDING", (0, 0), (0, -1), 0),
                ]
            )
        )
        story.append(breakdown_table)
        story.append(Spacer(1, 8))

    build_scope_statement(
        story,
        styles,
        doc_width,
        tool_domain="data_quality_preflight",
        framework=resolved_framework,
        domain_label="data quality assessment",
    )

    section_counter += 1

    # ── II. TB BALANCE CHECK (BUG-04) ──
    balance_check = preflight_result.get("balance_check")
    if balance_check is not None:
        story.append(Paragraph(f"{_roman(section_counter)}. Trial Balance Integrity Check", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))

        total_debits = balance_check.get("total_debits", 0)
        total_credits = balance_check.get("total_credits", 0)
        difference = balance_check.get("difference", 0)
        balanced = balance_check.get("balanced", True)

        balance_lines = [
            create_leader_dots("Total Debits", f"${total_debits:,.2f}"),
            create_leader_dots("Total Credits", f"${total_credits:,.2f}"),
            create_leader_dots("Difference", f"${difference:,.2f}"),
        ]
        for line in balance_lines:
            story.append(Paragraph(line, styles["MemoLeader"]))

        story.append(Spacer(1, 4))
        if balanced:
            story.append(
                Paragraph(
                    "Status: Balanced — Total debits equal total credits within "
                    f"rounding tolerance (${balance_check.get('tolerance', 0.01):.2f}).",
                    styles["MemoBody"],
                )
            )
        else:
            story.append(
                Paragraph(
                    f"CRITICAL — Trial balance is out of balance by ${abs(difference):,.2f}. "
                    "Downstream diagnostic results will be unreliable. Obtain a corrected TB "
                    "before proceeding.",
                    styles["MemoBody"],
                )
            )
        story.append(Spacer(1, 8))
        section_counter += 1

    # ── III. COLUMN DETECTION ──
    columns = preflight_result.get("columns", [])
    if columns:
        story.append(Paragraph(f"{_roman(section_counter)}. Column Detection", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))

        col_data = [["Role", "Detected Column", "Confidence", "Status"]]
        low_confidence_columns = []
        for col in columns:
            conf = col.get("confidence", 0)
            col_data.append(
                [
                    col.get("role", "").title(),
                    col.get("detected_name") or "\u2014",
                    f"{conf:.0%}",
                    col.get("status", "").replace("_", " ").title(),
                ]
            )
            # Track low-confidence columns for remediation note (IMP-02)
            if col.get("status") == "low_confidence" or (0 < conf < 0.80):
                low_confidence_columns.append(col)

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
        story.append(Spacer(1, 4))

        # Low-confidence remediation notes (IMP-02)
        for lc_col in low_confidence_columns:
            role = lc_col.get("role", "").title()
            detected = lc_col.get("detected_name", "")
            conf = lc_col.get("confidence", 0)
            story.append(
                Paragraph(
                    f"<i>{role} detection confidence ({conf:.0%}) is below the 80% threshold. "
                    f"The '{detected}' column was matched to {role} with moderate confidence. "
                    f"Confirm the column mapping is correct before running tests that filter by {role.lower()}. "
                    f"Use the column override feature to manually assign the correct column if needed.</i>",
                    styles["MemoBodySmall"],
                )
            )

        story.append(Spacer(1, 8))
        section_counter += 1

    # ── IV. DATA QUALITY ISSUES ──
    issues = preflight_result.get("issues", [])
    story.append(Paragraph(f"{_roman(section_counter)}. Data Quality Issues", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    if not issues:
        story.append(Paragraph("No data quality issues detected.", styles["MemoBody"]))
    else:
        # Sort by tests_affected descending (IMP-04)
        sorted_issues = sorted(
            issues,
            key=lambda i: i.get("tests_affected", 0),
            reverse=True,
        )

        issue_data = [["Category", "Severity", "Description", "Affected", "Tests", "Remediation", "Downstream Impact"]]
        for issue in sorted_issues:
            issue_data.append(
                [
                    Paragraph(issue.get("category", "").replace("_", " ").title(), styles["MemoTableCell"]),
                    Paragraph(issue.get("severity", "").upper(), styles["MemoTableCell"]),
                    Paragraph(issue.get("message", ""), styles["MemoTableCell"]),
                    str(issue.get("affected_count", 0)),
                    str(issue.get("tests_affected", 0)),
                    Paragraph(issue.get("remediation", ""), styles["MemoTableCell"]),
                    Paragraph(issue.get("downstream_impact", ""), styles["MemoTableCell"]),
                ]
            )

        # BUG-01 fix: Severity column widened from 0.55 to 0.75 inch
        # IMP-04: Added narrow "Tests" column (0.4 inch)
        issue_table = Table(
            issue_data,
            colWidths=[0.7 * inch, 0.75 * inch, 1.3 * inch, 0.4 * inch, 0.4 * inch, 1.5 * inch, 1.95 * inch],
            repeatRows=1,
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
                    ("ALIGN", (3, 0), (4, -1), "CENTER"),
                ]
            )
        )
        story.append(issue_table)
        story.append(Spacer(1, 4))

        # Affected account lists (IMP-03)
        for issue in sorted_issues:
            items = issue.get("affected_items", [])
            if not items:
                continue
            category = issue.get("category", "").replace("_", " ").title()
            total = issue.get("affected_items_total", len(items))
            display_items = items[:10]
            items_str = ", ".join(display_items)
            if total > 10:
                items_str += f" ... and {total - 10} more"
            story.append(
                Paragraph(
                    f"<i>{category} — Affected: {items_str}</i>",
                    styles["MemoBodySmall"],
                )
            )

    story.append(Spacer(1, 12))
    section_counter += 1

    # ── Methodology & Authoritative References ──
    build_methodology_statement(
        story,
        styles,
        doc_width,
        tool_domain="data_quality_preflight",
        framework=resolved_framework,
        domain_label="data quality assessment",
    )

    ref_label = _roman(section_counter)
    build_authoritative_reference_block(
        story,
        styles,
        doc_width,
        tool_domain="data_quality_preflight",
        framework=resolved_framework,
        domain_label="data quality assessment",
        section_label=f"{ref_label}.",
    )
    section_counter += 1

    # ── CONCLUSION (BUG-03) ──
    story.append(Paragraph(f"{_roman(section_counter)}. Conclusion", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    conclusion_text = _build_conclusion(preflight_result, filename)
    story.append(Paragraph(conclusion_text, styles["MemoBody"]))
    story.append(Spacer(1, 12))

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
        isa_reference="ISA 500 (Audit Evidence), ISA 330 (Auditor's Responses), and ISA 315 (Risk Assessment)",
    )

    doc.build(story, onFirstPage=draw_page_footer, onLaterPages=draw_page_footer)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def _build_conclusion(preflight_result: dict, filename: str) -> str:
    """Build dynamic conclusion text based on preflight results.

    Sprint 667 Issue 4: Conclusion is keyed off the highest-severity issue
    actually present, not the readiness score alone. The historic logic
    qualified every multi-issue file as "Ready with minor issues" and
    appended the phrase "do not prevent diagnostic testing from proceeding"
    even on files with high-severity blockers — directly contradicting
    the Downstream Impact section that flagged the same issues as
    invalidating. The new contract:

    * No issues at all → "Ready"
    * Only low/medium severity, no high → "Ready with caveats"
    * Any high-severity issue → "Review Required" (forbidden phrase
      removed; the conclusion explicitly states downstream testing
      should not proceed until the high-severity items are resolved)

    The blocking out-of-balance message is unchanged in spirit, but is
    suppressed when the balance check was skipped (multi-column TB
    layout — see Issue 12) so we don't report "$0.00 out of balance"
    on files where we didn't actually check.
    """
    readiness = preflight_result.get("readiness_score", 0)
    row_count = preflight_result.get("row_count", 0)
    issues = preflight_result.get("issues", [])

    # ── Hard blocker: TB does not reconcile ───────────────────────
    # Skip-path balance checks (multi-column layout) carry skipped=True
    # and must not be reported as out of balance — the variance is
    # unknown, not zero.
    balance_check = preflight_result.get("balance_check")
    if balance_check and not balance_check.get("balanced", True) and not balance_check.get("skipped", False):
        diff = abs(balance_check.get("difference", 0))
        return (
            f"The trial balance file ({filename}) is out of balance by ${diff:,.2f}. "
            "This is a critical data integrity failure that prevents any downstream "
            "diagnostic testing from proceeding. Obtain a corrected trial balance "
            "where total debits equal total credits before running any analysis."
        )

    # ── Severity tally drives the conclusion tier ────────────────
    high_issues = [i for i in issues if i.get("severity") == "high"]
    medium_issues = [i for i in issues if i.get("severity") == "medium"]

    # Build per-issue caveats once so both medium-only and high-severity
    # branches can render them.
    def _caveat(issue: dict, idx: int) -> str:
        category = issue.get("category", "")
        message = issue.get("message", "")
        suffix_map = {
            "null_values": "Fill in missing values before running tests that rely on account classification.",
            "column_detection": "Confirm the column mapping or use the override feature before proceeding.",
            "mixed_signs": "Tests that rely on debit/credit separation may produce reduced accuracy.",
            "duplicates": "Review for unintended duplicates before running balance-dependent tests.",
            "encoding": "Account matching in lead sheets and classification may be affected.",
            "zero_balance": "Consider filtering inactive accounts before statistical testing.",
            "tb_balance": (
                "Map all balance columns explicitly, or re-export the trial balance "
                "with a single Debit/Credit pair before re-uploading."
            ),
        }
        suffix = suffix_map.get(category, "")
        return f"({idx}) {message}." + (f" {suffix}" if suffix else "")

    # ── No issues → Ready ─────────────────────────────────────────
    if not issues:
        return (
            f"The trial balance file ({filename}) achieved a Readiness Score of "
            f"{readiness:.1f}/100 \u2014 assessed as Ready. The file contains "
            f"{row_count:,} accounts and is suitable for all downstream diagnostic "
            "testing with no caveats."
        )

    # ── Any high-severity issue → Review Required ────────────────
    # The forbidden phrase is intentionally absent. When a high-severity
    # issue is present the report must NOT claim downstream testing can
    # proceed, because that contradicts the Downstream Impact section.
    if high_issues:
        ranked = sorted(
            high_issues + medium_issues,
            key=lambda i: (
                {"high": 0, "medium": 1, "low": 2}.get(i.get("severity", "low"), 2),
                -i.get("tests_affected", 0),
            ),
        )
        items_text = " ".join(_caveat(it, idx + 1) for idx, it in enumerate(ranked))
        item_word = "issue" if len(ranked) == 1 else "issues"
        plural_invalidate = "invalidates" if len(high_issues) == 1 else "invalidate"
        return (
            f"The trial balance file ({filename}) achieved a Readiness Score of "
            f"{readiness:.1f}/100 \u2014 assessed as Review Required. The file "
            f"contains {row_count:,} accounts and presents {len(ranked)} "
            f"{item_word} that must be resolved before downstream diagnostic "
            f"testing can be relied upon: {items_text} The high-severity "
            f"finding(s) above {plural_invalidate} downstream test results; "
            "do not record conclusions against the affected figures until "
            "the issues are remediated and the file is re-processed."
        )

    # ── Medium-only → Ready with caveats ─────────────────────────
    ranked_medium = sorted(medium_issues, key=lambda i: -i.get("tests_affected", 0))
    items_text = " ".join(_caveat(it, idx + 1) for idx, it in enumerate(ranked_medium))
    caveat_word = "caveat" if len(ranked_medium) == 1 else "caveats"
    return (
        f"The trial balance file ({filename}) achieved a Readiness Score of "
        f"{readiness:.1f}/100 \u2014 assessed as Ready with caveats. The file "
        f"is suitable for downstream diagnostic testing subject to the "
        f"following {caveat_word}: {items_text} Remediate before final "
        "workpaper sign-off."
    )
