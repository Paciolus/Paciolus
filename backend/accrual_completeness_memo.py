"""
Paciolus — Accrual Completeness Estimator PDF Memo Generator
Sprint 290 / Sprint 513

Custom memo using memo_base.py primitives. Pattern B (custom sections).
Sections: Cover → Header → I. Scope → II. Accrual Accounts & Reasonableness →
          III. Expected Accrual Checklist → IV. Run-Rate Analysis →
          IV-A. Missing Accruals → IV-B. Deferred Revenue →
          V. Findings → VI. Suggested Procedures →
          Methodology → References → Sign-Off → Stamp → Disclaimer

ISA 520 documentation structure. Guardrail: descriptive metrics only.
"""

from typing import Optional

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from pdf_generator import (
    ClassicalColors,
    DoubleRule,
    LedgerRule,
    create_leader_dots,
    format_classical_date,
    generate_reference_number,
)
from shared.framework_resolution import ResolvedFramework
from shared.memo_base import build_disclaimer, build_intelligence_stamp, build_workpaper_signoff, create_memo_styles, standard_table_style
from shared.report_chrome import (
    ReportMetadata,
    build_cover_page,
    draw_page_footer,
    draw_page_header,
    find_logo,
)
from shared.scope_methodology import (
    build_authoritative_reference_block,
    build_methodology_statement,
    build_scope_statement,
)


# _standard_table_style consolidated into shared.memo_base.standard_table_style (Sprint 527)
_standard_table_style = standard_table_style


def generate_accrual_completeness_memo(
    report_result: dict,
    filename: str = "accrual_completeness",
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
    """Generate an Accrual Completeness Estimator PDF memo.

    Args:
        report_result: Dict from AccrualCompletenessReport.to_dict()
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

    reference = generate_reference_number().replace("PAC-", "ACE-")

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

    # ── Cover Page (diagonal color bands) ──
    logo_path = find_logo()
    cover_metadata = ReportMetadata(
        title="Accrual Completeness Estimator",
        client_name=client_name or "",
        engagement_period=period_tested or "",
        source_document=filename,
        source_document_title=source_document_title or "",
        source_context_note=source_context_note or "",
        reference=reference,
        fiscal_year_end=fiscal_year_end or "",
    )
    build_cover_page(story, styles, cover_metadata, doc_width, logo_path)

    # ── Header ──
    story.append(Paragraph("Accrual Completeness Estimator", styles["MemoTitle"]))
    if client_name:
        story.append(Paragraph(client_name, styles["MemoSubtitle"]))
    story.append(
        Paragraph(
            f"{format_classical_date()} &nbsp;&bull;&nbsp; {reference}",
            styles["MemoRef"],
        )
    )
    story.append(DoubleRule(doc_width))
    story.append(Spacer(1, 12))

    # ── Extract report data ──
    accrual_accounts = report_result.get("accrual_accounts", [])
    total_accrued = report_result.get("total_accrued_balance", 0)
    accrual_count = report_result.get("accrual_account_count", 0)
    monthly_run_rate = report_result.get("monthly_run_rate")
    ratio = report_result.get("accrual_to_run_rate_pct")
    threshold = report_result.get("threshold_pct", 50)
    meets_threshold = report_result.get("meets_threshold", False)
    prior_available = report_result.get("prior_available", False)
    prior_opex = report_result.get("prior_operating_expenses")
    deferred_revenue_accounts = report_result.get("deferred_revenue_accounts", [])
    total_deferred = report_result.get("total_deferred_revenue", 0)
    reasonableness_results = report_result.get("reasonableness_results", [])
    expected_checklist = report_result.get("expected_accrual_checklist", [])
    deferred_analysis = report_result.get("deferred_revenue_analysis")
    findings = report_result.get("findings", [])
    procedures = report_result.get("suggested_procedures", [])

    # ── I. SCOPE ──
    story.append(Paragraph("I. Scope", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    # Source document transparency
    if source_document_title and filename:
        source_line = create_leader_dots("Source", f"{source_document_title} ({filename})")
    elif source_document_title:
        source_line = create_leader_dots("Source", source_document_title)
    else:
        source_line = create_leader_dots("Source File", filename)

    scope_lines = [
        source_line,
        create_leader_dots("Accrual Accounts Identified", str(accrual_count)),
        create_leader_dots("Total Accrued Balance", f"${total_accrued:,.2f}"),
    ]

    if deferred_revenue_accounts:
        scope_lines.append(create_leader_dots("Deferred Revenue (Excluded)", f"${total_deferred:,.2f}"))

    scope_lines.extend(
        [
            create_leader_dots("Prior Period Data", "Included" if prior_available else "Not provided"),
            create_leader_dots("Threshold", f"{threshold:.0f}%"),
        ]
    )

    if period_tested:
        scope_lines.insert(0, create_leader_dots("Period Tested", period_tested))
    if prior_available and monthly_run_rate is not None:
        scope_lines.append(create_leader_dots("Monthly Run-Rate", f"${monthly_run_rate:,.2f}"))
    if ratio is not None:
        scope_lines.append(create_leader_dots("Accrual-to-Run-Rate", f"{ratio:.1f}%"))
        scope_lines.append(
            create_leader_dots(
                "Meets Minimum Accrual Threshold (\u226550%)",
                "Yes" if meets_threshold else "No",
            )
        )

    for line in scope_lines:
        story.append(Paragraph(line, styles["MemoLeader"]))
    story.append(Spacer(1, 8))

    build_scope_statement(
        story,
        styles,
        doc_width,
        tool_domain="accrual_completeness",
        framework=resolved_framework,
        domain_label="accrual completeness estimation",
    )

    # ── II. ACCRUAL ACCOUNTS & REASONABLENESS ──
    if accrual_accounts:
        story.append(Paragraph("II. Accrual Accounts &amp; Reasonableness", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))

        # Build enriched table with classification column
        acct_headers = ["Account", "Classification", "Balance", "Matched Keyword"]
        acct_data = [acct_headers]
        for a in accrual_accounts:
            if isinstance(a, dict):
                acct_data.append(
                    [
                        Paragraph(str(a.get("account_name", "")), styles["MemoTableCell"]),
                        a.get("classification", "Accrued Liability"),
                        f"${a.get('balance', 0):,.2f}",
                        a.get("matched_keyword", ""),
                    ]
                )

        # Total row
        acct_data.append(["TOTAL", "", f"${total_accrued:,.2f}", ""])

        acct_table = Table(
            acct_data,
            colWidths=[2.3 * inch, 1.4 * inch, 1.5 * inch, 1.3 * inch],
            repeatRows=1,
        )
        acct_style_cmds: list = [
            ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
            ("FONTNAME", (0, 1), (-1, -2), "Times-Roman"),
            ("FONTNAME", (0, -1), (-1, -1), "Times-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
            ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
            ("LINEBELOW", (0, -2), (-1, -2), 0.5, ClassicalColors.OBSIDIAN_DEEP),
            ("LINEBELOW", (0, 1), (-1, -2), 0.25, ClassicalColors.LEDGER_RULE),
            ("ALIGN", (2, 0), (2, -1), "RIGHT"),
            ("FONTNAME", (2, 1), (2, -1), "Courier"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (0, -1), 0),
        ]
        acct_table.setStyle(TableStyle(acct_style_cmds))
        story.append(acct_table)
        story.append(Spacer(1, 8))

        # Per-account reasonableness sub-table
        if reasonableness_results:
            story.append(Paragraph("<b>Per-Account Reasonableness Testing</b>", styles["MemoBody"]))
            story.append(Spacer(1, 4))

            reason_headers = ["Account", "Annual Driver", "Expected (1 mo)", "Recorded", "Variance", "Status"]
            reason_data = [reason_headers]

            for r in reasonableness_results:
                if isinstance(r, dict):
                    annual = f"${r.get('annual_driver', 0):,.0f}" if r.get("annual_driver") is not None else "\u2014"
                    expected = (
                        f"${r.get('expected_balance', 0):,.0f}" if r.get("expected_balance") is not None else "\u2014"
                    )
                    recorded = f"${r.get('recorded_balance', 0):,.0f}"
                    var_val = r.get("variance")
                    variance_str = f"${var_val:+,.0f}" if var_val is not None else "\u2014"
                    status = r.get("status", "")

                    reason_data.append(
                        [
                            Paragraph(str(r.get("account_name", "")), styles["MemoTableCell"]),
                            annual,
                            expected,
                            recorded,
                            variance_str,
                            Paragraph(status, styles["MemoTableCell"]),
                        ]
                    )

            reason_table = Table(
                reason_data,
                colWidths=[1.7 * inch, 1.1 * inch, 1.0 * inch, 1.0 * inch, 0.9 * inch, 1.2 * inch],
                repeatRows=1,
            )
            reason_table.setStyle(_standard_table_style(courier_cols=[1, 2, 3, 4]))
            story.append(reason_table)
            story.append(Spacer(1, 6))

            story.append(
                Paragraph(
                    "<i>Expected balances are analytical estimates based on run-rate logic and "
                    "may not reflect actual accrual timing, cutoff adjustments, or management's "
                    "specific accrual methodology. Auditor should obtain supporting schedules "
                    "for all material accruals.</i>",
                    styles["MemoBodySmall"],
                )
            )
            story.append(Spacer(1, 8))

    # ── III. EXPECTED ACCRUAL CHECKLIST ──
    if expected_checklist:
        story.append(Paragraph("III. Expected Accrual Checklist", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))

        checklist_data = [["Expected Accrual", "Detected?", "Balance", "Risk if Absent"]]
        for item in expected_checklist:
            if isinstance(item, dict):
                detected = item.get("detected", False)
                balance = item.get("balance")
                checklist_data.append(
                    [
                        Paragraph(str(item.get("expected_name", "")), styles["MemoTableCell"]),
                        "Yes" if detected else "No",
                        f"${balance:,.2f}" if balance is not None else "\u2014",
                        Paragraph(str(item.get("risk_if_absent", "")), styles["MemoTableCell"]),
                    ]
                )

        checklist_table = Table(
            checklist_data,
            colWidths=[1.8 * inch, 0.9 * inch, 1.3 * inch, 2.5 * inch],
            repeatRows=1,
        )
        checklist_table.setStyle(_standard_table_style(courier_cols=[2]))
        story.append(checklist_table)
        story.append(Spacer(1, 8))

    # ── IV. RUN-RATE ANALYSIS ──
    if prior_available and monthly_run_rate is not None:
        story.append(Paragraph("IV. Run-Rate Analysis", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))

        analysis_data = [["Metric", "Value"]]
        analysis_data.append(["Prior Operating Expenses (Annual)", f"${prior_opex:,.2f}" if prior_opex else "N/A"])
        analysis_data.append(["Monthly Run-Rate", f"${monthly_run_rate:,.2f}"])
        analysis_data.append(["Total Accrued Balance (excl. Deferred Revenue)", f"${total_accrued:,.2f}"])
        analysis_data.append(["Accrual-to-Run-Rate Ratio", f"{ratio:.1f}%" if ratio is not None else "N/A"])
        analysis_data.append(["Threshold", f"{threshold:.0f}%"])
        analysis_data.append(
            [
                "Meets Minimum Accrual Threshold (\u226550%)",
                "Yes" if meets_threshold else "No",
            ]
        )

        analysis_table = Table(analysis_data, colWidths=[3.5 * inch, 3.0 * inch])
        analysis_table.setStyle(_standard_table_style(courier_cols=[1]))
        story.append(analysis_table)
        story.append(Spacer(1, 8))

        # Dynamic conclusion
        if ratio is not None:
            if meets_threshold:
                conclusion = (
                    f"The accrual-to-run-rate ratio of {ratio:.1f}% meets the {threshold:.0f}% "
                    f"minimum threshold, indicating accrual balances are within a reasonable range "
                    f"relative to operating activity levels."
                )
            else:
                conclusion = (
                    f"The accrual-to-run-rate ratio of {ratio:.1f}% falls below the {threshold:.0f}% "
                    f"minimum threshold, suggesting accrual balances may require additional "
                    f"completeness procedures."
                )

                # Count missing accruals
                missing_count = sum(
                    1 for c in expected_checklist if isinstance(c, dict) and not c.get("detected", True)
                )
                if missing_count > 0:
                    conclusion += (
                        f" Combined with {missing_count} potential missing accrual "
                        f"categor{'y' if missing_count == 1 else 'ies'} identified in Section III, "
                        f"the engagement team should perform additional completeness procedures."
                    )

            story.append(Paragraph(conclusion, styles["MemoBody"]))
            story.append(Spacer(1, 8))

    # ── IV-A. MISSING ACCRUAL ESTIMATION ──
    missing_items = [c for c in expected_checklist if isinstance(c, dict) and not c.get("detected", True)]
    if missing_items:
        story.append(Paragraph("IV-A. Potential Missing Accruals", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))

        story.append(
            Paragraph(
                "The following expected accrual types were not identified in the trial balance. "
                "The absence of these accruals does not necessarily indicate an error — some may "
                "not be applicable to the entity's operations or tax structure.",
                styles["MemoBody"],
            )
        )
        story.append(Spacer(1, 6))

        missing_headers = ["Expected Accrual", "Basis", "Status", "Recommended Action"]
        missing_data = [missing_headers]
        for item in missing_items:
            missing_data.append(
                [
                    Paragraph(str(item.get("expected_name", "")), styles["MemoTableCell"]),
                    Paragraph(str(item.get("basis", "")), styles["MemoTableCell"]),
                    "Not Found",
                    Paragraph(str(item.get("recommended_action", "")), styles["MemoTableCell"]),
                ]
            )

        missing_table = Table(
            missing_data,
            colWidths=[1.5 * inch, 1.8 * inch, 0.8 * inch, 2.4 * inch],
            repeatRows=1,
        )
        missing_table.setStyle(_standard_table_style(right_align_from=99))
        story.append(missing_table)
        story.append(Spacer(1, 6))

        # Tax status footnote
        has_tax_missing = any("Tax" in str(item.get("expected_name", "")) for item in missing_items)
        if has_tax_missing:
            story.append(
                Paragraph(
                    "<i>Note: LLC pass-through status may explain the absence of Income Taxes Payable "
                    "at the entity level. Verify entity tax classification.</i>",
                    styles["MemoBodySmall"],
                )
            )
            story.append(Spacer(1, 8))

    # ── IV-B. DEFERRED REVENUE ANALYSIS ──
    if deferred_revenue_accounts and deferred_analysis:
        story.append(Paragraph("IV-B. Deferred Revenue", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))

        dr_data = [["Metric", "Value"]]
        dr_balance = deferred_analysis.get("deferred_balance", 0) if isinstance(deferred_analysis, dict) else 0
        dr_revenue = deferred_analysis.get("total_revenue") if isinstance(deferred_analysis, dict) else None
        dr_pct = deferred_analysis.get("deferred_pct_of_revenue") if isinstance(deferred_analysis, dict) else None

        dr_data.append(["Deferred Revenue Balance", f"${dr_balance:,.2f}"])
        if dr_revenue is not None:
            dr_data.append(["Total Revenue", f"${dr_revenue:,.2f}"])
        if dr_pct is not None:
            dr_data.append(["Deferred as % of Revenue", f"{dr_pct:.2f}%"])

        # List individual deferred revenue accounts
        for acct in deferred_revenue_accounts:
            if isinstance(acct, dict):
                dr_data.append(
                    [
                        f"  {acct.get('account_name', '')}",
                        f"${acct.get('balance', 0):,.2f}",
                    ]
                )

        dr_table = Table(dr_data, colWidths=[3.5 * inch, 3.0 * inch])
        dr_table.setStyle(_standard_table_style(courier_cols=[1]))
        story.append(dr_table)
        story.append(Spacer(1, 6))

        # ASC 606 narrative
        dr_narrative = f"Deferred Revenue of ${dr_balance:,.2f}"
        if dr_pct is not None and dr_revenue is not None:
            dr_narrative += f" represents {dr_pct:.2f}% of total revenue (${dr_revenue:,.0f})"
        dr_narrative += (
            ". Auditor should verify that all deferred amounts relate to unfulfilled "
            "performance obligations as of the balance sheet date, and that revenue "
            "recognition timing is consistent with ASC 606 requirements. "
            "Obtain the deferred revenue rollforward schedule."
        )
        story.append(Paragraph(dr_narrative, styles["MemoBody"]))
        story.append(Spacer(1, 8))

    # ── Narrative ──
    narrative = report_result.get("narrative", "")
    if narrative:
        story.append(Paragraph("Narrative", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))
        story.append(Paragraph(narrative, styles["MemoBody"]))
        story.append(Spacer(1, 8))

    # ── V. FINDINGS ──
    if findings:
        story.append(Paragraph("V. Findings", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))

        story.append(
            Paragraph(
                "The following findings were identified from the accrual completeness analysis, "
                "reasonableness testing, and missing accrual estimation performed in the "
                "preceding sections. Each finding requires evaluation by the engagement team.",
                styles["MemoBody"],
            )
        )
        story.append(Spacer(1, 6))

        # Sort by priority: High → Moderate → Low
        priority_order = {"High": 0, "Moderate": 1, "Low": 2}
        sorted_findings = sorted(
            findings if isinstance(findings, list) else [],
            key=lambda f: priority_order.get(f.get("risk", "Low") if isinstance(f, dict) else "Low", 2),
        )

        finding_headers = ["#", "Area", "Finding", "Risk", "Action Required"]
        finding_widths = [0.3 * inch, 1.2 * inch, 2.5 * inch, 0.7 * inch, 1.8 * inch]
        finding_data = [finding_headers]

        for i, f in enumerate(sorted_findings, 1):
            if isinstance(f, dict):
                finding_data.append(
                    [
                        str(i),
                        Paragraph(f.get("area", ""), styles["MemoTableCell"]),
                        Paragraph(f.get("finding", ""), styles["MemoTableCell"]),
                        f.get("risk", ""),
                        Paragraph(f.get("action_required", ""), styles["MemoTableCell"]),
                    ]
                )

        finding_table = Table(finding_data, colWidths=finding_widths, repeatRows=1)
        finding_table.setStyle(_standard_table_style(right_align_from=99))
        story.append(finding_table)
        story.append(Spacer(1, 10))

    # ── VI. SUGGESTED AUDIT PROCEDURES ──
    if procedures:
        story.append(Paragraph("VI. Suggested Audit Procedures", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))

        story.append(
            Paragraph(
                "The following procedures are suggested based on the findings identified in "
                "the preceding analysis. Procedures are prioritized by risk level.",
                styles["MemoBody"],
            )
        )
        story.append(Spacer(1, 6))

        proc_headers = ["Priority", "Area", "Procedure"]
        proc_widths = [0.7 * inch, 1.5 * inch, 4.3 * inch]
        proc_data = [proc_headers]

        for p in procedures:
            if isinstance(p, dict):
                proc_data.append(
                    [
                        p.get("priority", ""),
                        p.get("area", ""),
                        Paragraph(p.get("procedure", ""), styles["MemoTableCell"]),
                    ]
                )

        proc_table = Table(proc_data, colWidths=proc_widths, repeatRows=1)
        proc_table.setStyle(_standard_table_style(right_align_from=99))
        story.append(proc_table)
        story.append(Spacer(1, 12))

    story.append(Spacer(1, 12))

    # ── Methodology & Authoritative References ──
    build_methodology_statement(
        story,
        styles,
        doc_width,
        tool_domain="accrual_completeness",
        framework=resolved_framework,
        domain_label="accrual completeness estimation",
    )
    build_authoritative_reference_block(
        story,
        styles,
        doc_width,
        tool_domain="accrual_completeness",
        framework=resolved_framework,
        domain_label="accrual completeness estimation",
    )

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
        domain="accrual completeness estimation",
        isa_reference="ISA 520 (Analytical Procedures)",
    )

    def _on_later_pages(canvas, doc):
        draw_page_header(canvas, doc, title="Accrual Completeness Estimator", reference=reference)
        draw_page_footer(canvas, doc)

    doc.build(story, onFirstPage=draw_page_footer, onLaterPages=_on_later_pages)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
