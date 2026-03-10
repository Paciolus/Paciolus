"""
Paciolus — Expense Category Analytical Procedures PDF Memo Generator
Sprint 289: Phase XXXIX / Sprint 512: Enrichment

Custom memo using memo_base.py primitives. Pattern B (custom sections).
Sections: Header → Scope → Category Breakdown → Period-over-Period →
          Expense Ratio Analysis → Findings → Suggested Procedures →
          Methodology → Authoritative References →
          Workpaper Sign-Off → Disclaimer

ISA 520 / AU-C § 520 / AS 2305 documentation structure.
Guardrail: descriptive metrics only.
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
    find_logo,
)
from shared.scope_methodology import (
    build_authoritative_reference_block,
    build_methodology_statement,
    build_scope_statement,
)

# ═══════════════════════════════════════════════════════════════
# Shared table style helpers
# ═══════════════════════════════════════════════════════════════

NEAR_ZERO = 1e-10

# Benchmark ranges for expense ratios (professional services / capital management)
_RATIO_BENCHMARKS = {
    "COGS Ratio": (30, 55),
    "Payroll Ratio": (15, 35),
    "D&A Ratio": (2, 8),
    "Interest & Tax Ratio": (3, 10),
    "Other Operating Ratio": (5, 12),
}

_RATIO_KEYS = {
    "Cost of Goods Sold": "COGS Ratio",
    "Payroll & Benefits": "Payroll Ratio",
    "Payroll & Employee Costs": "Payroll Ratio",
    "Depreciation & Amortization": "D&A Ratio",
    "Interest & Tax": "Interest & Tax Ratio",
    "Other Operating Expenses": "Other Operating Ratio",
}


# _standard_table_style consolidated into shared.memo_base.standard_table_style (Sprint 527)
_standard_table_style = standard_table_style


def _pct_change(current: float, prior: float) -> Optional[float]:
    """Compute percentage change; returns None if prior is near-zero."""
    if abs(prior) < NEAR_ZERO:
        return None
    return (current - prior) / prior * 100


def _pct_change_str(pct: Optional[float]) -> str:
    """Format percentage change with directional indicator."""
    if pct is None:
        return "N/A"
    arrow = "\u2191" if pct > 0 else ("\u2193" if pct < 0 else "\u2013")
    return f"{abs(pct):.1f}% {arrow}"


def _assign_risk(pct_change_val: Optional[float], exceeds_materiality: bool) -> str:
    """Assign risk level based on percentage change and materiality."""
    if pct_change_val is None:
        return "Low"
    if abs(pct_change_val) >= 20 and exceeds_materiality:
        return "High"
    if abs(pct_change_val) >= 10 or exceeds_materiality:
        return "Moderate"
    return "Low"


def _benchmark_flag(ratio_name: str, value: float) -> str:
    """Check if a ratio is within, below, or above benchmark range."""
    bounds = _RATIO_BENCHMARKS.get(ratio_name)
    if bounds is None:
        return "N/A"
    low, high = bounds
    if value < low:
        return "Below Range"
    if value > high:
        return "Above Range"
    return "Within Range"


def _generate_variance_commentary(
    label: str, pct_change_val: float, dollar_change: float, pct_of_revenue: Optional[float], total_revenue: float
) -> str:
    """Generate dynamic per-category variance commentary."""
    direction = "increased" if dollar_change > 0 else "decreased"
    abs_change = abs(dollar_change)
    abs_pct = abs(pct_change_val)

    rev_context = ""
    if pct_of_revenue is not None:
        rev_context = f", representing {pct_of_revenue:.1f}% of current period revenue"

    base = f"{label} {direction} {abs_pct:.1f}% period-over-period (${abs_change:,.0f}){rev_context}. "

    label_lower = label.lower()
    if "cost of goods" in label_lower or "cogs" in label_lower:
        base += (
            "Gross margin implication: verify whether the change reflects volume growth, "
            "input cost inflation, or a shift in product/service mix."
        )
    elif "payroll" in label_lower or "employee" in label_lower:
        base += (
            "Reconcile to headcount changes, wage rate adjustments, and benefits enrollment shifts. "
            "Cross-reference with payroll testing results if available."
        )
    elif "depreciation" in label_lower or "amortization" in label_lower:
        base += (
            "Evaluate whether the change is consistent with capital expenditure activity, "
            "asset disposals, or changes in useful life estimates."
        )
    elif "interest" in label_lower or "tax" in label_lower:
        base += (
            "Assess whether the change is attributable to debt level changes, rate adjustments, "
            "or shifts in effective tax rate."
        )
    elif "other operating" in label_lower:
        base += (
            "This category may contain heterogeneous expense types. "
            "Request a sub-ledger breakdown to identify the primary drivers."
        )
    else:
        base += "Evaluate the underlying drivers and assess consistency with management expectations."

    return base


def _generate_procedures(findings: list[dict], categories: list[dict]) -> list[dict]:
    """Generate suggested audit procedures dynamically from findings."""
    procedures: list[dict] = []
    cat_map = {c.get("label", ""): c for c in categories if isinstance(c, dict)}

    for finding in findings:
        label = finding.get("category", "")
        risk = finding.get("risk", "Low")
        cat = cat_map.get(label, {})
        change = cat.get("dollar_change", 0)
        pct = cat.get("_pct_change")
        abs_change = abs(change) if change else 0
        pct_str = f"{abs(pct):.1f}%" if pct is not None else "N/A"

        label_lower = label.lower()

        if "cost of goods" in label_lower or "cogs" in label_lower:
            procedures.append(
                {
                    "priority": "High" if risk == "High" else "Moderate",
                    "area": "COGS Variance",
                    "procedure": (
                        f"COGS changed ${abs_change:,.0f} ({pct_str}) year-over-year. "
                        "Obtain and inspect vendor invoices supporting material purchases. "
                        "Recalculate gross margin and compare to management's representations. "
                        "Consider whether the change is consistent with reported revenue growth."
                    ),
                }
            )
        elif "payroll" in label_lower or "employee" in label_lower:
            procedures.append(
                {
                    "priority": "High" if risk == "High" else "Moderate",
                    "area": "Payroll Variance",
                    "procedure": (
                        f"Payroll & Benefits changed ${abs_change:,.0f} ({pct_str}). "
                        "Reconcile to headcount changes, wage rate increases, and benefits enrollment. "
                        "Cross-reference with Report 05 (Payroll & Employee Testing) findings."
                    ),
                }
            )
        elif "depreciation" in label_lower or "amortization" in label_lower:
            procedures.append(
                {
                    "priority": "Moderate",
                    "area": "D&A Variance",
                    "procedure": (
                        f"Depreciation & Amortization changed ${abs_change:,.0f} ({pct_str}). "
                        "Verify against the fixed asset register. Confirm any new capitalized assets, "
                        "disposals, or changes in depreciation methods or useful life estimates."
                    ),
                }
            )
        elif "interest" in label_lower or "tax" in label_lower:
            procedures.append(
                {
                    "priority": "Moderate",
                    "area": "Interest & Tax Variance",
                    "procedure": (
                        f"Interest & Tax changed ${abs_change:,.0f} ({pct_str}). "
                        "Confirm interest expense against debt agreements and outstanding balances. "
                        "Verify tax provision against the effective tax rate computation."
                    ),
                }
            )
        elif "other operating" in label_lower:
            procedures.append(
                {
                    "priority": "Moderate",
                    "area": "Other Operating Expenses",
                    "procedure": (
                        f"Other Operating Expenses changed ${abs_change:,.0f} ({pct_str}). "
                        "Request sub-ledger detail. Scan for non-recurring items, related-party "
                        "transactions, or expenses that may require separate disclosure."
                    ),
                }
            )
        else:
            procedures.append(
                {
                    "priority": "Moderate",
                    "area": f"{label} Variance",
                    "procedure": (
                        f"{label} changed ${abs_change:,.0f} ({pct_str}). "
                        "Investigate the underlying drivers and assess consistency with "
                        "management expectations and prior period trends."
                    ),
                }
            )

    # Add benchmark-driven procedures
    for cat in categories:
        if not isinstance(cat, dict):
            continue
        label = cat.get("label", "")
        pct_rev = cat.get("pct_of_revenue")
        if pct_rev is None:
            continue
        ratio_name = _RATIO_KEYS.get(label)
        if ratio_name is None:
            continue
        flag = _benchmark_flag(ratio_name, pct_rev)
        if flag == "Above Range":
            bounds = _RATIO_BENCHMARKS[ratio_name]
            # Only add if not already covered by a variance finding
            existing_areas = {p["area"] for p in procedures}
            area_name = f"{ratio_name} Benchmark"
            if area_name not in existing_areas:
                procedures.append(
                    {
                        "priority": "Moderate",
                        "area": area_name,
                        "procedure": (
                            f"{label} at {pct_rev:.1f}% of revenue exceeds the benchmark range "
                            f"of {bounds[0]}%\u2013{bounds[1]}%. Evaluate whether industry or "
                            "entity-specific factors justify the elevated ratio."
                        ),
                    }
                )

    # Sort: High first, then Moderate, then Low
    priority_order = {"High": 0, "Moderate": 1, "Low": 2}
    procedures.sort(key=lambda p: priority_order.get(p.get("priority", "Low"), 2))
    return procedures


def generate_expense_category_memo(
    report_result: dict,
    filename: str = "expense_category",
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
    """Generate an Expense Category Analytical Procedures PDF memo.

    Args:
        report_result: Dict from ExpenseCategoryReport.to_dict()
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
    reference = generate_reference_number().replace("PAC-", "ECA-")

    # ── Cover Page (diagonal color bands) ──
    logo_path = find_logo()
    cover_metadata = ReportMetadata(
        title="Expense Category Analytical Procedures",
        client_name=client_name or "",
        engagement_period=period_tested or "",
        source_document=filename,
        source_document_title=source_document_title or "",
        source_context_note=source_context_note or "",
        reference=reference,
    )
    build_cover_page(story, styles, cover_metadata, doc_width, logo_path)

    # ── Header ──
    story.append(Paragraph("Expense Category Analytical Procedures", styles["MemoTitle"]))
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

    # ── Extract data ──
    categories = report_result.get("categories", [])
    total_expenses = report_result.get("total_expenses", 0)
    total_revenue = report_result.get("total_revenue", 0)
    revenue_available = report_result.get("revenue_available", False)
    prior_available = report_result.get("prior_available", False)
    materiality = report_result.get("materiality_threshold", 0)
    category_count = report_result.get("category_count", 0)
    prior_revenue = report_result.get("prior_revenue")

    # Pre-compute % change for all categories
    for c in categories:
        if isinstance(c, dict) and c.get("prior_amount") is not None:
            c["_pct_change"] = _pct_change(c.get("amount", 0), c["prior_amount"])
        else:
            if isinstance(c, dict):
                c["_pct_change"] = None

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
        create_leader_dots("Expense Categories", f"{category_count} active"),
        create_leader_dots("Total Expenses", f"${total_expenses:,.2f}"),
        create_leader_dots("Total Revenue", f"${total_revenue:,.2f}" if revenue_available else "Not available"),
        create_leader_dots("Materiality Threshold", f"${materiality:,.2f}"),
        create_leader_dots("Prior Period Data", "Included" if prior_available else "Not provided"),
    ]
    if period_tested:
        scope_lines.insert(0, create_leader_dots("Period Tested", period_tested))

    for line in scope_lines:
        story.append(Paragraph(line, styles["MemoLeader"]))
    story.append(Spacer(1, 8))

    build_scope_statement(
        story,
        styles,
        doc_width,
        tool_domain="expense_category",
        framework=resolved_framework,
        domain_label="expense category analytical",
    )

    # ── II. CATEGORY BREAKDOWN ──
    story.append(Paragraph("II. Category Breakdown", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    if categories:
        has_prior = prior_available and any(
            isinstance(c, dict) and c.get("prior_amount") is not None for c in categories
        )

        if has_prior:
            cat_headers = [
                "Category",
                "Current Amount",
                "% of Rev",
                "Prior Amount",
                "$ Change",
                "% Change",
                "Exceeds Mat.",
            ]
            col_widths = [1.7 * inch, 1.0 * inch, 0.7 * inch, 1.0 * inch, 0.9 * inch, 0.9 * inch, 0.8 * inch]
        else:
            cat_headers = ["Category", "Amount", "% of Revenue"]
            col_widths = [3.0 * inch, 2.0 * inch, 1.5 * inch]

        cat_data = [cat_headers]
        for c in categories:
            if isinstance(c, dict):
                amount = c.get("amount", 0)
                pct = c.get("pct_of_revenue")
                pct_str = f"{pct:.2f}%" if pct is not None else "N/A"

                if has_prior:
                    prior_amt = c.get("prior_amount")
                    dollar_change = c.get("dollar_change")
                    exceeds = c.get("exceeds_threshold", False)
                    pct_chg = c.get("_pct_change")
                    pct_chg_str = _pct_change_str(pct_chg)

                    # Add warning marker for large % changes
                    pct_chg_display = pct_chg_str
                    if pct_chg is not None and abs(pct_chg) > 15:
                        pct_chg_display = f"\u26a0 {pct_chg_str}"

                    exceeds_display = "\u26a0 Yes" if exceeds else "No"

                    cat_data.append(
                        [
                            c.get("label", ""),
                            f"${amount:,.2f}",
                            pct_str,
                            f"${prior_amt:,.2f}" if prior_amt is not None else "N/A",
                            f"${dollar_change:,.2f}" if dollar_change is not None else "N/A",
                            pct_chg_display,
                            exceeds_display,
                        ]
                    )
                else:
                    cat_data.append(
                        [
                            c.get("label", ""),
                            f"${amount:,.2f}",
                            pct_str,
                        ]
                    )

        # Total row
        total_pct = (
            (total_expenses / total_revenue * 100) if revenue_available and abs(total_revenue) > NEAR_ZERO else None
        )
        total_pct_str = f"{total_pct:.2f}%" if total_pct is not None else "N/A"
        if has_prior:
            cat_data.append(["TOTAL", f"${total_expenses:,.2f}", total_pct_str, "", "", "", ""])
        else:
            cat_data.append(["TOTAL", f"${total_expenses:,.2f}", total_pct_str])

        courier_cols = [1, 3, 4] if has_prior else [1]
        cat_table = Table(cat_data, colWidths=col_widths, repeatRows=1)
        cat_style = _standard_table_style(courier_cols=courier_cols)
        # Bold the total row
        cat_style.add("FONTNAME", (0, -1), (-1, -1), "Times-Bold")
        cat_style.add("LINEBELOW", (0, -2), (-1, -2), 0.5, ClassicalColors.OBSIDIAN_DEEP)
        cat_table.setStyle(cat_style)
        story.append(cat_table)
        story.append(Spacer(1, 6))

        # Prior period source footnote
        if has_prior:
            story.append(
                Paragraph(
                    "<i>Prior period amounts sourced from management-provided comparative data. "
                    "Auditor should verify prior period figures against prior year audit documentation.</i>",
                    styles["MemoBodySmall"],
                )
            )
            story.append(Spacer(1, 8))

    # ── III. PERIOD-OVER-PERIOD COMPARISON (build out) ──
    has_prior_data = prior_available and any(
        isinstance(c, dict) and c.get("prior_amount") is not None for c in categories
    )
    findings: list[dict] = []
    finding_num = 0

    if has_prior_data:
        story.append(Paragraph("III. Period-Over-Period Comparison", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))

        story.append(
            Paragraph(
                "The following analysis presents period-over-period variances for each expense "
                "category, with risk-level assessments based on the magnitude of change and "
                f"materiality threshold of ${materiality:,.2f}. Categories with moderate or high "
                "risk designations require management explanation.",
                styles["MemoBody"],
            )
        )
        story.append(Spacer(1, 8))

        # III-A: Variance Summary Table
        story.append(Paragraph("III-A. Variance Summary", styles["MemoSection"]))
        story.append(Spacer(1, 4))

        variance_headers = ["Category", "$ Change", "% Change", "Direction", "Risk Level", "Explanation Req."]
        variance_widths = [1.8 * inch, 1.0 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch]
        variance_data = [variance_headers]

        for c in categories:
            if not isinstance(c, dict):
                continue
            label = c.get("label", "")
            dollar_change = c.get("dollar_change")
            pct_chg = c.get("_pct_change")
            exceeds = c.get("exceeds_threshold", False)

            if dollar_change is None:
                continue

            direction = "Increase" if dollar_change > 0 else ("Decrease" if dollar_change < 0 else "No Change")
            risk = _assign_risk(pct_chg, exceeds)
            explanation_req = "Yes" if risk in ("High", "Moderate") else "No"

            variance_data.append(
                [
                    label,
                    f"${dollar_change:,.2f}",
                    _pct_change_str(pct_chg),
                    direction,
                    risk,
                    explanation_req,
                ]
            )

            # Collect findings for Section V
            if risk in ("High", "Moderate"):
                finding_num += 1
                finding_source = "III-A"
                findings.append(
                    {
                        "num": finding_num,
                        "category": label,
                        "finding": (
                            f"{label} changed ${abs(dollar_change):,.0f} "
                            f"({_pct_change_str(pct_chg)}) period-over-period"
                        ),
                        "risk": risk,
                        "priority": risk,
                        "source": finding_source,
                    }
                )

        var_table = Table(variance_data, colWidths=variance_widths, repeatRows=1)
        var_table.setStyle(_standard_table_style(courier_cols=[1]))
        story.append(var_table)
        story.append(Spacer(1, 10))

        # III-B: Per-Category Variance Commentary
        high_mod_cats = [
            c
            for c in categories
            if isinstance(c, dict)
            and c.get("_pct_change") is not None
            and _assign_risk(c["_pct_change"], c.get("exceeds_threshold", False)) in ("High", "Moderate")
        ]

        if high_mod_cats:
            story.append(Paragraph("III-B. Variance Commentary", styles["MemoSection"]))
            story.append(Spacer(1, 4))

            for c in high_mod_cats:
                label = c.get("label", "")
                pct_chg = c["_pct_change"]
                dollar_change = c.get("dollar_change", 0)
                pct_of_rev = c.get("pct_of_revenue")
                commentary = _generate_variance_commentary(label, pct_chg, dollar_change, pct_of_rev, total_revenue)
                story.append(
                    Paragraph(
                        f"<b>{label}:</b> {commentary}",
                        styles["MemoBody"],
                    )
                )
                story.append(Spacer(1, 4))

            story.append(Spacer(1, 6))

        # III-C: Other Operating Expenses Decomposition Flag
        for c in categories:
            if not isinstance(c, dict):
                continue
            label = c.get("label", "")
            label_lower = label.lower()
            if "other operating" not in label_lower and "other expenses" not in label_lower:
                continue
            pct_rev = c.get("pct_of_revenue")
            pct_chg = c.get("_pct_change")
            dollar_change = c.get("dollar_change", 0)
            if pct_rev is not None and pct_rev > 10 and pct_chg is not None and pct_chg > 15:
                story.append(
                    Paragraph(
                        f"<b>Decomposition Flag — {label}:</b> "
                        f"This category represents a high-growth, high-value catch-all at "
                        f"{pct_rev:.1f}% of revenue with {pct_chg:.1f}% year-over-year growth. "
                        f"Auditor should request a detailed sub-ledger breakdown to identify "
                        f"the drivers of the ${abs(dollar_change):,.0f} increase. Categories to "
                        f"investigate may include: consulting fees, software/subscriptions, "
                        f"travel, legal, or one-time charges.",
                        styles["MemoBody"],
                    )
                )
                story.append(Spacer(1, 8))

        story.append(Spacer(1, 6))

    # ── IV. EXPENSE RATIO ANALYSIS ──
    if revenue_available:
        section_iv = "IV" if has_prior_data else "III"
        story.append(Paragraph(f"{section_iv}. Expense Ratio Analysis", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))

        story.append(
            Paragraph(
                "The following table presents expense-to-revenue ratios for each category, "
                "compared against indicative benchmark ranges for professional services "
                "and capital management firms. Benchmarks are illustrative and the auditor "
                "should apply engagement-specific context.",
                styles["MemoBody"],
            )
        )
        story.append(Spacer(1, 6))

        ratio_headers = ["Metric", "Current", "Prior", "Change", "Benchmark Flag"]
        ratio_widths = [2.0 * inch, 0.9 * inch, 0.9 * inch, 0.9 * inch, 1.3 * inch]
        ratio_data = [ratio_headers]

        # Total expense ratio
        total_ratio = (total_expenses / total_revenue * 100) if abs(total_revenue) > NEAR_ZERO else None
        prior_total_expenses = report_result.get("prior_total_expenses")
        prior_total_ratio = None
        if prior_revenue and abs(prior_revenue) > NEAR_ZERO and prior_total_expenses is not None:
            prior_total_ratio = prior_total_expenses / prior_revenue * 100

        total_ratio_str = f"{total_ratio:.2f}%" if total_ratio is not None else "N/A"
        prior_total_str = f"{prior_total_ratio:.2f}%" if prior_total_ratio is not None else "\u2014"
        total_change = None
        if total_ratio is not None and prior_total_ratio is not None:
            total_change = total_ratio - prior_total_ratio
        total_change_str = f"{total_change:+.2f}pp" if total_change is not None else "\u2014"

        ratio_data.append(["Total Expense Ratio", total_ratio_str, prior_total_str, total_change_str, "\u2014"])

        # Per-category ratios
        for c in categories:
            if not isinstance(c, dict):
                continue
            label = c.get("label", "")
            pct_rev = c.get("pct_of_revenue")
            prior_pct_rev = c.get("prior_pct_of_revenue")

            ratio_name = _RATIO_KEYS.get(label)
            if ratio_name is None:
                metric_name = f"{label} Ratio"
            else:
                metric_name = ratio_name

            current_str = f"{pct_rev:.2f}%" if pct_rev is not None else "N/A"
            prior_str = f"{prior_pct_rev:.2f}%" if prior_pct_rev is not None else "\u2014"

            change_val = None
            if pct_rev is not None and prior_pct_rev is not None:
                change_val = pct_rev - prior_pct_rev
            change_str = f"{change_val:+.2f}pp" if change_val is not None else "\u2014"

            flag = _benchmark_flag(metric_name, pct_rev) if pct_rev is not None else "N/A"

            ratio_data.append([metric_name, current_str, prior_str, change_str, flag])

            # Collect benchmark findings for Section V
            if flag == "Above Range" and ratio_name:
                bounds = _RATIO_BENCHMARKS[ratio_name]
                finding_num += 1
                findings.append(
                    {
                        "num": finding_num,
                        "category": label,
                        "finding": (
                            f"{ratio_name} at {pct_rev:.1f}% exceeds benchmark range ({bounds[0]}%\u2013{bounds[1]}%)"
                        ),
                        "risk": "Moderate",
                        "priority": "Moderate",
                        "source": section_iv,
                    }
                )

        ratio_table = Table(ratio_data, colWidths=ratio_widths, repeatRows=1)
        ratio_table.setStyle(_standard_table_style(courier_cols=[1, 2]))
        story.append(ratio_table)
        story.append(Spacer(1, 6))

        story.append(
            Paragraph(
                "<i>Benchmark ranges are indicative for professional services / capital management "
                "contexts and may not be applicable to all entities. The auditor should apply "
                "engagement-specific and industry-specific context when evaluating ratios.</i>",
                styles["MemoBodySmall"],
            )
        )
        story.append(Spacer(1, 10))

    # ── V. FINDINGS ──
    if findings:
        section_v = "V" if has_prior_data else "IV"
        story.append(Paragraph(f"{section_v}. Findings", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))

        story.append(
            Paragraph(
                "The following findings were identified from the variance analysis and ratio "
                "benchmarking performed in the preceding sections. Each finding requires "
                "evaluation by the engagement team.",
                styles["MemoBody"],
            )
        )
        story.append(Spacer(1, 6))

        # Sort by priority: High → Moderate → Low
        priority_order = {"High": 0, "Moderate": 1, "Low": 2}
        findings.sort(key=lambda f: priority_order.get(f.get("priority", "Low"), 2))

        finding_headers = ["#", "Category", "Finding", "Risk", "Priority"]
        finding_widths = [0.3 * inch, 1.4 * inch, 3.3 * inch, 0.7 * inch, 0.7 * inch]
        finding_data = [finding_headers]

        for i, f in enumerate(findings, 1):
            finding_data.append(
                [
                    str(i),
                    f.get("category", ""),
                    Paragraph(f.get("finding", ""), styles["MemoTableCell"]),
                    f.get("risk", ""),
                    f.get("priority", ""),
                ]
            )

        finding_table = Table(finding_data, colWidths=finding_widths, repeatRows=1)
        finding_table.setStyle(_standard_table_style(right_align_from=99))
        story.append(finding_table)
        story.append(Spacer(1, 10))

    # ── VI. SUGGESTED AUDIT PROCEDURES ──
    procedures = _generate_procedures(findings if findings else [], categories)
    if procedures:
        section_vi = "VI" if has_prior_data else "V"
        story.append(Paragraph(f"{section_vi}. Suggested Audit Procedures", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))

        story.append(
            Paragraph(
                "The following procedures are suggested based on the findings identified in "
                "the preceding analysis. Procedures are prioritized by risk level and reference "
                "specific dollar amounts and percentages from the current period data.",
                styles["MemoBody"],
            )
        )
        story.append(Spacer(1, 6))

        proc_headers = ["Priority", "Area", "Procedure"]
        proc_widths = [0.7 * inch, 1.5 * inch, 4.3 * inch]
        proc_data = [proc_headers]

        for p in procedures:
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

    # ── Methodology & Authoritative References ──
    build_methodology_statement(
        story,
        styles,
        doc_width,
        tool_domain="expense_category",
        framework=resolved_framework,
        domain_label="expense category analytical",
    )
    build_authoritative_reference_block(
        story,
        styles,
        doc_width,
        tool_domain="expense_category",
        framework=resolved_framework,
        domain_label="expense category analytical",
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
        domain="expense category analytical procedures",
        isa_reference="AU-C § 520 (Analytical Procedures) / AS 2305 (Substantive Analytical Procedures)",
    )

    doc.build(story, onFirstPage=draw_page_footer)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
