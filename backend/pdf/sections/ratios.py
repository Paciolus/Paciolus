"""
Key Financial Ratios and Quality of Earnings section renderers.

Computes and renders up to 12 financial ratios from the balance sheet and
income statement, plus the OCF/NI cash-conversion quality indicator when
cash-flow data is present.
"""

from typing import Any, Optional

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from pdf.components import LedgerRule, create_leader_dots
from pdf.styles import ClassicalColors


def render_ratios(story: list, styles: dict, statements: Any) -> bool:
    """Append Key Financial Ratios to *story*.

    Returns ``True`` if the section was rendered (so downstream callers know
    whether a section ornament is needed).
    """
    if not statements.total_revenue or statements.total_revenue == 0:
        return False

    story.append(Spacer(1, 8))
    story.append(Paragraph("\u2767", styles["SectionOrnament"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Key Financial Ratios", styles["SectionHeader"]))
    story.append(LedgerRule(color=ClassicalColors.OBSIDIAN_DEEP, thickness=1))
    story.append(Spacer(1, 8))

    # Extract balance sheet components for ratio computation
    _current_assets = 0.0
    _current_liabilities = 0.0
    _total_cash = 0.0
    _total_ar = 0.0
    _found_ca = False
    _found_cl = False
    for item in statements.balance_sheet:
        if item.label == "Total Current Assets" and item.is_subtotal:
            _current_assets = item.amount
            _found_ca = True
        elif item.label == "Total Current Liabilities" and item.is_subtotal:
            _current_liabilities = item.amount
            _found_cl = True
        elif item.lead_sheet_ref == "A" and item.indent_level == 1:
            _total_cash = item.amount
        elif item.lead_sheet_ref == "B" and item.indent_level == 1:
            _total_ar = item.amount

    # Build ratio list in specified order (12 ratios)
    # Each entry: (label, current_value_str, prior_value_str_or_None)
    ratio_lines: list[tuple[str, str, Optional[str]]] = []
    _has_prior = statements.has_prior_period

    # 1. Gross Profit Margin
    if statements.gross_profit is not None:
        gp_margin = statements.gross_profit / statements.total_revenue
        prior_gp_margin_str = None
        if _has_prior and statements.prior_total_revenue and statements.prior_total_revenue != 0:
            prior_gp_margin_str = f"{statements.prior_gross_profit / statements.prior_total_revenue:.1%}"
        ratio_lines.append(("Gross Profit Margin", f"{gp_margin:.1%}", prior_gp_margin_str))

    # 2. Operating Margin
    if statements.operating_income is not None:
        op_margin = statements.operating_income / statements.total_revenue
        prior_op_str = None
        if _has_prior and statements.prior_total_revenue and statements.prior_total_revenue != 0:
            prior_op_str = f"{statements.prior_operating_income / statements.prior_total_revenue:.1%}"
        ratio_lines.append(("Operating Margin", f"{op_margin:.1%}", prior_op_str))

    # 3. Net Margin
    if statements.net_income is not None:
        net_margin = statements.net_income / statements.total_revenue
        prior_nm_str = None
        if _has_prior and statements.prior_total_revenue and statements.prior_total_revenue != 0:
            prior_nm_str = f"{statements.prior_net_income / statements.prior_total_revenue:.1%}"
        ratio_lines.append(("Net Margin", f"{net_margin:.1%}", prior_nm_str))

    # 4. EBITDA
    _depreciation = statements.depreciation_amount
    if statements.operating_income is not None:
        ebitda = statements.operating_income + _depreciation
        ratio_lines.append(("EBITDA", f"${ebitda:,.2f}", None))

        # 5. EBITDA Margin
        ebitda_margin = ebitda / statements.total_revenue
        ratio_lines.append(("EBITDA Margin", f"{ebitda_margin:.1%}", None))

    # 6. Debt-to-Equity Ratio
    if statements.total_equity and statements.total_equity != 0:
        de_ratio = statements.total_liabilities / statements.total_equity
        prior_de_str = None
        if _has_prior and statements.prior_total_equity and statements.prior_total_equity != 0:
            prior_de_str = f"{statements.prior_total_liabilities / statements.prior_total_equity:.2f}x"
        ratio_lines.append(("Debt-to-Equity Ratio", f"{de_ratio:.2f}x", prior_de_str))

    # 7. Interest Coverage
    _interest_exp = statements.interest_expense
    if statements.operating_income is not None and _interest_exp and _interest_exp != 0:
        interest_coverage = statements.operating_income / _interest_exp
        ratio_lines.append(("Interest Coverage", f"{interest_coverage:.1f}x", None))

    # 8. Asset Turnover
    if statements.total_assets and statements.total_assets != 0:
        asset_turnover = statements.total_revenue / statements.total_assets
        prior_at_str = None
        if _has_prior and statements.prior_total_assets and statements.prior_total_assets != 0:
            prior_at_str = f"{statements.prior_total_revenue / statements.prior_total_assets:.2f}x"
        ratio_lines.append(("Asset Turnover", f"{asset_turnover:.2f}x", prior_at_str))

    # 9. Current Ratio
    if _found_ca and _found_cl:
        if _current_liabilities != 0:
            current_ratio = _current_assets / _current_liabilities
            ratio_lines.append(("Current Ratio", f"{current_ratio:.2f}x", None))

        # 10. Quick Ratio
        if _current_liabilities != 0:
            quick_ratio = (_total_cash + _total_ar) / _current_liabilities
            ratio_lines.append(("Quick Ratio", f"{quick_ratio:.2f}x", None))

        # 11. Working Capital
        working_capital = _current_assets - _current_liabilities
        ratio_lines.append(("Working Capital", f"${working_capital:,.2f}", None))
    else:
        ratio_lines.append(("Current Ratio", "Requires current/non-current classification", None))

    # 12. DSO
    if _total_ar and statements.total_revenue != 0:
        dso = (_total_ar / statements.total_revenue) * 365
        ratio_lines.append(("Days Sales Outstanding (DSO)", f"{dso:.0f} days", None))

    # Render ratio table -- with prior year column if available
    if _has_prior and any(r[2] is not None for r in ratio_lines):
        _render_comparative_table(story, styles, ratio_lines)
    else:
        for label, value, _ in ratio_lines:
            line = create_leader_dots(f"      {label}", value)
            story.append(Paragraph(line, styles["LeaderLine"]))

    story.append(Spacer(1, 4))
    return True


def render_quality_of_earnings(story: list, styles: dict, statements: Any, has_ratios: bool) -> None:
    """Append the Quality of Earnings sub-section to *story*.

    No-ops if cash flow or net income data is unavailable.
    """
    if statements.cash_flow_statement is None:
        return
    if statements.net_income is None or statements.net_income == 0:
        return

    operating_cf = statements.cash_flow_statement.operating.subtotal

    if not has_ratios:
        story.append(Spacer(1, 8))
        story.append(Paragraph("\u2767", styles["SectionOrnament"]))
        story.append(Spacer(1, 8))

    story.append(Paragraph("Quality of Earnings", styles["SubsectionHeader"]))
    story.append(LedgerRule(color=ClassicalColors.OBSIDIAN_DEEP, thickness=0.5))
    story.append(Spacer(1, 4))

    ocf_ni_ratio = operating_cf / statements.net_income

    # Interpretation
    if ocf_ni_ratio > 1.0:
        interpretation = (
            f"The OCF/NI ratio of {ocf_ni_ratio:.2f}x indicates that cash earnings exceed reported "
            f"net income \u2014 strong earnings quality. Operating cash flow "
            f"(${operating_cf:,.2f}) exceeds net income (${statements.net_income:,.2f}), "
            f"suggesting conservative accrual practices and reliable cash conversion."
        )
    elif ocf_ni_ratio >= 0.8:
        interpretation = (
            f"The OCF/NI ratio of {ocf_ni_ratio:.2f}x indicates acceptable earnings quality. "
            f"Operating cash flow (${operating_cf:,.2f}) is reasonably aligned with "
            f"net income (${statements.net_income:,.2f})."
        )
    else:
        interpretation = (
            f"The OCF/NI ratio of {ocf_ni_ratio:.2f}x indicates that net income "
            f"(${statements.net_income:,.2f}) may not be fully supported by operating cash flows "
            f"(${operating_cf:,.2f}). This warrants investigation of accrual quality, "
            f"non-cash revenue recognition, or working capital management practices."
        )

    ocf_line = create_leader_dots("      Cash Conversion Ratio (OCF / Net Income)", f"{ocf_ni_ratio:.2f}x")
    story.append(Paragraph(ocf_line, styles["LeaderLine"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph(interpretation, styles["DocumentRef"]))
    story.append(Spacer(1, 4))

    # Benchmark context (Sprint 488)
    benchmark_text = (
        "A Cash Conversion Ratio consistently above 1.0x over multiple periods is generally considered "
        "a positive indicator of earnings quality. Ratios below 0.8x may indicate aggressive accrual "
        "accounting and warrant further analytical procedures."
    )
    story.append(Paragraph(f"<i>{benchmark_text}</i>", styles["DocumentRef"]))

    # Prior period Cash Conversion Ratio if available
    if statements.has_prior_period and statements.prior_net_income and statements.prior_net_income != 0:
        if statements.cash_flow_statement.has_prior_period:
            # Compute prior OCF from prior period data if available
            # Prior OCF isn't directly available, so note that
            pass
    story.append(Spacer(1, 8))


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _render_comparative_table(story: list, styles: dict, ratio_lines: list) -> None:
    ratio_data = [["Metric", "Current", "Prior", ""]]
    for label, current_val, prior_val in ratio_lines:
        change_indicator = ""
        if prior_val is not None:
            # Parse numeric values to compute change direction
            try:
                c_num = float(current_val.replace("%", "").replace("x", "").replace("$", "").replace(",", "").strip())
                p_num = float(prior_val.replace("%", "").replace("x", "").replace("$", "").replace(",", "").strip())
                if p_num != 0:
                    pct_change = abs((c_num - p_num) / p_num) * 100
                    if pct_change > 10:
                        change_indicator = "\u25b2" if c_num > p_num else "\u25bc"
            except (ValueError, ZeroDivisionError):
                pass
        ratio_data.append([label, current_val, prior_val or "\u2014", change_indicator])

    ratio_table = Table(ratio_data, colWidths=[2.8 * inch, 1.4 * inch, 1.4 * inch, 0.4 * inch])
    ratio_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                ("FONTNAME", (0, 1), (0, -1), "Times-Roman"),
                ("FONTNAME", (1, 1), (-1, -1), "Courier"),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
                ("TEXTCOLOR", (0, 1), (-1, -1), ClassicalColors.OBSIDIAN_600),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LINEBELOW", (0, -1), (-1, -1), 0.5, ClassicalColors.LEDGER_RULE),
            ]
        )
    )
    story.append(ratio_table)
