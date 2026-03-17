"""
Multi-Period Comparison Memo PDF Generator (Sprint 128 / Sprint 505)

Auto-generated analytical procedures memo per ISA 520 (Analytical Procedures) /
PCAOB AS 2305 (Substantive Analytical Procedures).
Renaissance Ledger aesthetic consistent with existing PDF exports.

Sections:
1. Header (client, periods, preparer)
2. Scope (periods compared, total accounts, materiality, significance breakdown)
3. Movement Summary (counts by movement type)
4. Results Summary (composite risk score, risk tier, severity counts)
5. Significant Account Movements (material/significant items table, sign changes,
   dormant accounts, new/closed accounts, ratio trends, suggested procedures)
6. Lead Sheet Summary (net changes by lead sheet category with % change)
7. Authoritative References
8. Conclusion (risk-tier-based professional assessment)
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
from shared.follow_up_procedures import get_follow_up_procedure
from shared.framework_resolution import ResolvedFramework
from shared.memo_base import (
    RISK_SCALE_LEGEND,
    RISK_TIER_DISPLAY,
    build_disclaimer,
    build_intelligence_stamp,
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
from shared.testing_enums import score_to_risk_tier


def _format_currency(value: float) -> str:
    """Format a currency value for display."""
    if value >= 0:
        return f"${value:,.2f}"
    return f"-${abs(value):,.2f}"


# =============================================================================
# RISK SCORING
# =============================================================================


def compute_apc_risk_score(
    material_movement_count: int,
    sign_change_count: int,
    cash_increase_pct: float,
    cogs_growth_vs_revenue: bool,
    single_account_revenue_pct: float,
    high_growth_accounts: int,
    dormant_count: int,
    new_closed_count: int,
) -> float:
    """Compute a composite risk score (0-100) for analytical procedures.

    Args:
        material_movement_count: Number of material-tier movements.
        sign_change_count: Number of accounts that changed sign.
        cash_increase_pct: Cash increase as decimal (e.g., 0.603 for 60.3%).
        cogs_growth_vs_revenue: True if COGS grew faster than revenue.
        single_account_revenue_pct: Highest single account as % of total revenue (decimal).
        high_growth_accounts: Accounts with >25% YOY change.
        dormant_count: Number of dormant accounts.
        new_closed_count: Number of new + closed accounts.

    Returns:
        Score from 0 to 100.
    """
    score = 0.0
    score += min(material_movement_count * 3, 20)
    score += sign_change_count * 8
    if cash_increase_pct > 0.50:
        score += 6
    if cogs_growth_vs_revenue:
        score += 5
    if single_account_revenue_pct > 0.50:
        score += 8
    score += min(high_growth_accounts * 2, 10)
    score += dormant_count * 3
    score += min(new_closed_count * 2, 8)
    return min(score, 100)


_RISK_CONCLUSIONS: dict[str, str] = {
    "low": (
        "Based on the analytical procedures applied, the trial balance comparison "
        "returned LOW movement density. Account balances are consistent with prior "
        "period expectations. No additional substantive procedures are indicated."
    ),
    "moderate": (
        "Based on the analytical procedures applied, the trial balance comparison "
        "returned MODERATE movement density. Several accounts exhibit period-over-period "
        "changes that should be corroborated with management explanations and additional "
        "substantive procedures per ISA 520."
    ),
    "elevated": (
        "Based on the analytical procedures applied, the trial balance comparison "
        "returned ELEVATED movement density. Material movements and structural changes "
        "were detected that require focused investigation. The engagement team should "
        "evaluate whether expanded substantive procedures are appropriate per ISA 520 "
        "and PCAOB AS 2305."
    ),
    "high": (
        "Based on the analytical procedures applied, the trial balance comparison "
        "returned HIGH movement density. Significant variances, sign changes, and/or "
        "structural changes indicate potential misstatement risk across multiple account "
        "categories. Expanded substantive procedures are recommended per ISA 520 and "
        "PCAOB AS 2305."
    ),
}


# =============================================================================
# CONTENT: Significant Movements Table
# =============================================================================


def _build_significant_movements_table(
    story: list,
    styles: dict,
    movements: list[dict],
) -> None:
    """Build a table of significant account movements."""
    if not movements:
        story.append(Paragraph("No significant movements identified.", styles["MemoBodySmall"]))
        return

    headers = ["Account", "Prior", "Current", "Change", "% Change", "Type"]
    col_widths = [2.2 * inch, 1.0 * inch, 1.0 * inch, 1.0 * inch, 0.7 * inch, 0.8 * inch]

    data = [headers]
    # Show top 25 significant movements sorted by absolute change
    sorted_movements = sorted(movements, key=lambda m: abs(m.get("change_amount", 0)), reverse=True)[:25]

    for m in sorted_movements:
        name = m.get("account_name", "")
        prior = _format_currency(m.get("prior_balance", 0))
        current = _format_currency(m.get("current_balance", 0))
        change = _format_currency(m.get("change_amount", 0))
        pct = m.get("change_percent")
        pct_str = f"{pct:+.1f}%" if pct is not None else "N/A"
        movement = m.get("movement_type", "").replace("_", " ").title()
        data.append([Paragraph(name, styles["MemoTableCell"]), prior, current, change, pct_str, movement])

    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Times-Roman"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                ("LINEBELOW", (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                ("ALIGN", (1, 0), (4, -1), "RIGHT"),
                ("ALIGN", (5, 0), (5, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (0, -1), 0),
            ]
        )
    )
    story.append(table)

    total_sig = len(movements)
    if total_sig > 25:
        story.append(
            Paragraph(
                f"+ {total_sig - 25} additional significant movements (see CSV export for full list)",
                styles["MemoBodySmall"],
            )
        )


# =============================================================================
# CONTENT: Suggested Procedures for Material Movements
# =============================================================================

_MOVEMENT_PROCEDURES: dict[tuple[str, str], str] = {
    # Revenue
    ("revenue", "increase"): "apc_revenue_increase",
    ("revenue", "decrease"): "apc_revenue_decrease",
    ("revenue", "new"): "apc_revenue_increase",
    ("revenue", "closed"): "apc_revenue_decrease",
    # COGS
    ("cogs", "increase"): "apc_cogs_increase",
    ("cogs", "decrease"): "apc_cogs_decrease",
    ("cogs", "new"): "apc_cogs_increase",
    ("cogs", "closed"): "apc_cogs_decrease",
    # Assets
    ("asset", "increase"): "apc_asset_increase",
    ("asset", "decrease"): "apc_asset_decrease",
    ("asset", "new"): "apc_asset_increase",
    ("asset", "closed"): "apc_asset_decrease",
    # Cash
    ("cash", "increase"): "apc_cash_increase",
    ("cash", "decrease"): "apc_cash_decrease",
    ("cash", "new"): "apc_cash_increase",
    ("cash", "closed"): "apc_cash_decrease",
    # Liabilities
    ("liability", "increase"): "apc_liability_increase",
    ("liability", "decrease"): "apc_liability_decrease",
    ("liability", "new"): "apc_liability_increase",
    ("liability", "closed"): "apc_liability_decrease",
    # Expenses
    ("expense", "increase"): "apc_expense_increase",
    ("expense", "decrease"): "apc_expense_decrease",
    ("expense", "new"): "apc_expense_increase",
    ("expense", "closed"): "apc_expense_decrease",
}

_ACCOUNT_TYPE_KEYWORDS: dict[str, list[str]] = {
    "revenue": ["revenue", "sales", "service income", "fee income", "consulting"],
    "cogs": ["cost of goods", "cogs", "cost of sales", "cost of revenue"],
    "cash": ["cash"],
    "expense": ["marketing", "advertising", "salary", "salaries", "wages", "rent", "insurance", "utilities"],
    "liability": ["debt", "loan", "payable", "liability", "accrued"],
    "asset": ["receivable", "inventory", "fixed asset", "equipment", "property", "prepaid"],
}


def _classify_account_for_procedure(account_name: str) -> str:
    """Classify an account name into a category for procedure lookup."""
    lower = account_name.lower()
    for category, keywords in _ACCOUNT_TYPE_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return category
    return "asset"


def _build_suggested_procedures(
    story: list,
    styles: dict,
    movements: list[dict],
) -> None:
    """Build suggested procedures subsection for material movements."""
    material = [m for m in movements if m.get("significance") == "material"]
    if not material:
        return

    story.append(Paragraph("<b>Suggested Procedures for Material Movements</b>", styles["MemoBody"]))
    story.append(Spacer(1, 4))

    seen_procedures: set[str] = set()
    for m in sorted(material, key=lambda x: abs(x.get("change_amount", 0)), reverse=True):
        name = m.get("account_name", "")
        category = _classify_account_for_procedure(name)
        movement_type = m.get("movement_type", "")

        # Determine economic direction based on movement type and account category
        if movement_type == "new_account":
            direction = "new"
        elif movement_type == "closed_account":
            direction = "closed"
        elif movement_type == "sign_change":
            direction = "increase"  # sign changes use increase-side procedure
        else:
            change = m.get("change_amount", 0)
            # Credit-nature accounts (revenue, liability): negative change = economic increase
            if category in ("revenue", "liability"):
                direction = "increase" if change < 0 else "decrease"
            else:
                direction = "increase" if change > 0 else "decrease"

        procedure_key = _MOVEMENT_PROCEDURES.get((category, direction))
        if not procedure_key:
            procedure_key = "significant_movement"

        if procedure_key in seen_procedures:
            continue
        seen_procedures.add(procedure_key)

        procedure_text = get_follow_up_procedure(procedure_key, rotation_index=len(seen_procedures))
        if not procedure_text:
            procedure_text = get_follow_up_procedure("significant_movement")
        pct = m.get("change_percent")
        pct_str = f" ({pct:+.1f}%)" if pct is not None else ""

        story.append(
            Paragraph(
                f"<b>{name}</b>{pct_str}: <i>{procedure_text}</i>",
                styles["MemoBodySmall"],
            )
        )
        story.append(Spacer(1, 2))

    story.append(Spacer(1, 6))


# =============================================================================
# CONTENT: Ratio Trend Keyword Patterns
# =============================================================================

_REVENUE_KEYWORDS = [
    "revenue",
    "sales",
    "service income",
    "fee income",
    "interest income",
    "consulting income",
    "subscription",
    "commission income",
]
_REVENUE_EXCLUSIONS = [
    "deferred revenue",
    "unearned revenue",
    "deferred income",
]
_COGS_KEYWORDS = [
    "cost of goods",
    "cogs",
    "cost of sales",
    "cost of revenue",
    "cost of services",
    "direct cost",
    "purchases",
]
_SALARY_KEYWORDS = [
    "salary",
    "salaries",
    "wages",
    "payroll",
    "compensation",
    "employee benefits",
    "staff cost",
]
_MARKETING_KEYWORDS = [
    "marketing",
    "advertising",
    "promotion",
    "media",
    "sponsorship",
]
_CASH_KEYWORDS = [
    "cash",
    "bank",
    "money market",
    "petty cash",
]
_ASSET_KEYWORDS = [
    "receivable",
    "inventory",
    "equipment",
    "property",
    "prepaid",
    "fixed asset",
    "investment",
    "cash",
    "bank",
]


def _match_keyword(account_name: str, keywords: list[str]) -> bool:
    """Check if an account name matches any keyword (case-insensitive)."""
    lower = account_name.lower()
    return any(kw in lower for kw in keywords)


def _build_ratio_trends_table(
    story: list,
    styles: dict,
    all_movements: list[dict],
    prior_label: str,
    current_label: str,
) -> None:
    """Build an expanded ratio trends table from the full TB population.

    Computes 6 ratios from keyword-matched accounts across all movements
    (not just significant movements). Includes flag column for notable changes.
    """
    # Accumulate totals from ALL movements by keyword category
    # Uses account_type when available, falling back to keyword matching
    prior_revenue = 0.0
    current_revenue = 0.0
    prior_cogs = 0.0
    current_cogs = 0.0
    prior_salary = 0.0
    current_salary = 0.0
    prior_marketing = 0.0
    current_marketing = 0.0
    prior_cash = 0.0
    current_cash = 0.0
    prior_total_assets = 0.0
    current_total_assets = 0.0

    for m in all_movements:
        name = m.get("account_name", "")
        acct_type = m.get("account_type", "").lower()
        prior_bal = abs(m.get("prior_balance", 0))
        current_bal = abs(m.get("current_balance", 0))

        # Revenue: check account_type OR keyword match (not exclusive fallback)
        is_revenue = acct_type == "revenue" or (
            _match_keyword(name, _REVENUE_KEYWORDS) and not _match_keyword(name, _REVENUE_EXCLUSIONS)
        )
        # COGS: accounts may be typed as "expense" in the TB but contain COGS keywords
        is_cogs = acct_type == "cogs" or _match_keyword(name, _COGS_KEYWORDS)

        if is_revenue:
            prior_revenue += prior_bal
            current_revenue += current_bal
        if is_cogs:
            prior_cogs += prior_bal
            current_cogs += current_bal
        if _match_keyword(name, _SALARY_KEYWORDS):
            prior_salary += prior_bal
            current_salary += current_bal
        if _match_keyword(name, _MARKETING_KEYWORDS):
            prior_marketing += prior_bal
            current_marketing += current_bal
        if _match_keyword(name, _CASH_KEYWORDS):
            prior_cash += prior_bal
            current_cash += current_bal
        if _match_keyword(name, _ASSET_KEYWORDS):
            prior_total_assets += prior_bal
            current_total_assets += current_bal

    # Compute ratios: (name, prior_val, current_val, change_str, flag)
    ratios: list[tuple[str, str, str, str, str]] = []

    # 1. Gross Profit Margin
    if prior_revenue > 0 or current_revenue > 0:
        prior_gp = (prior_revenue - prior_cogs) / prior_revenue if prior_revenue > 0 else None
        current_gp = (current_revenue - current_cogs) / current_revenue if current_revenue > 0 else None
        prior_gp_str = f"{prior_gp:.1%}" if prior_gp is not None else "N/A"
        current_gp_str = f"{current_gp:.1%}" if current_gp is not None else "N/A"
        if prior_gp is not None and current_gp is not None:
            change_pp = (current_gp - prior_gp) * 100
            change_str = f"{change_pp:+.1f}pp"
        else:
            change_str = "N/A"
        ratios.append(("Gross Profit Margin", prior_gp_str, current_gp_str, change_str, ""))

    # 2. COGS as % of Revenue
    if prior_revenue > 0 or current_revenue > 0:
        prior_cogs_pct = prior_cogs / prior_revenue if prior_revenue > 0 else None
        current_cogs_pct = current_cogs / current_revenue if current_revenue > 0 else None
        prior_str = f"{prior_cogs_pct:.1%}" if prior_cogs_pct is not None else "N/A"
        current_str = f"{current_cogs_pct:.1%}" if current_cogs_pct is not None else "N/A"
        if prior_cogs_pct is not None and current_cogs_pct is not None:
            change_pp = (current_cogs_pct - prior_cogs_pct) * 100
            change_str = f"{change_pp:+.1f}pp"
            # Flag if COGS growing faster than revenue
            cogs_growth = (current_cogs - prior_cogs) / prior_cogs if prior_cogs > 0 else 0
            rev_growth = (current_revenue - prior_revenue) / prior_revenue if prior_revenue > 0 else 0
            flag = ""
            if cogs_growth > rev_growth and change_pp > 0:
                flag = "Margin compression"
        else:
            change_str = "N/A"
            flag = ""
        ratios.append(("COGS as % of Revenue", prior_str, current_str, change_str, flag))

    # 3. Salary-to-Revenue
    if (prior_revenue > 0 or current_revenue > 0) and (prior_salary > 0 or current_salary > 0):
        prior_r = prior_salary / prior_revenue if prior_revenue > 0 else None
        current_r = current_salary / current_revenue if current_revenue > 0 else None
        prior_str = f"{prior_r:.1%}" if prior_r is not None else "N/A"
        current_str = f"{current_r:.1%}" if current_r is not None else "N/A"
        if prior_r is not None and current_r is not None:
            change_pp = (current_r - prior_r) * 100
            change_str = f"{change_pp:+.1f}pp"
        else:
            change_str = "N/A"
        ratios.append(("Salary-to-Revenue", prior_str, current_str, change_str, ""))

    # 4. Marketing-to-Revenue
    if (prior_revenue > 0 or current_revenue > 0) and (prior_marketing > 0 or current_marketing > 0):
        prior_r = prior_marketing / prior_revenue if prior_revenue > 0 else None
        current_r = current_marketing / current_revenue if current_revenue > 0 else None
        prior_str = f"{prior_r:.1%}" if prior_r is not None else "N/A"
        current_str = f"{current_r:.1%}" if current_r is not None else "N/A"
        if prior_r is not None and current_r is not None:
            change_pp = (current_r - prior_r) * 100
            change_str = f"{change_pp:+.1f}pp"
            flag = ""
            if abs(change_pp) > 0.5:
                flag = "Material increase"
        else:
            change_str = "N/A"
            flag = ""
        ratios.append(("Marketing-to-Revenue", prior_str, current_str, change_str, flag))

    # 5. Revenue Growth Rate
    if prior_revenue > 0 and current_revenue > 0:
        growth = (current_revenue - prior_revenue) / prior_revenue
        growth_str = f"{growth:.1%}"
        flag = ""
        if growth > 0.25:
            flag = "Unusual — obtain explanation"
        ratios.append(("Revenue Growth Rate", "—", growth_str, "—", flag))

    # 6. Cash as % of Total Assets
    if current_total_assets > 0:
        prior_cash_pct = prior_cash / prior_total_assets if prior_total_assets > 0 else None
        current_cash_pct = current_cash / current_total_assets
        prior_str = f"{prior_cash_pct:.1%}" if prior_cash_pct is not None else "N/A"
        current_str = f"{current_cash_pct:.1%}"
        if prior_cash_pct is not None:
            change_pp = (current_cash_pct - prior_cash_pct) * 100
            change_str = f"{change_pp:+.1f}pp"
        else:
            change_str = "N/A"
        ratios.append(("Cash as % of Total Assets", prior_str, current_str, change_str, ""))

    if not ratios:
        return

    story.append(Paragraph("<b>Ratio Trends</b>", styles["MemoBody"]))
    story.append(Spacer(1, 4))

    headers = ["Ratio", prior_label, current_label, "Change", "Flag"]
    col_widths = [2.0 * inch, 1.0 * inch, 1.0 * inch, 0.8 * inch, 1.9 * inch]
    data: list[list] = [headers]
    for ratio_name, prior_val, current_val, change_val, flag in ratios:
        data.append([ratio_name, prior_val, current_val, change_val, flag])

    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Times-Roman"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                ("LINEBELOW", (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                ("ALIGN", (1, 0), (3, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (0, -1), 0),
            ]
        )
    )
    story.append(table)

    # Narrative paragraph about ratio trends
    narrative_parts = []
    if prior_revenue > 0 and current_revenue > 0 and prior_cogs > 0:
        cogs_growth_pct = ((current_cogs - prior_cogs) / prior_cogs) * 100
        rev_growth_pct = ((current_revenue - prior_revenue) / prior_revenue) * 100
        prior_gpm = ((prior_revenue - prior_cogs) / prior_revenue) * 100
        current_gpm = ((current_revenue - current_cogs) / current_revenue) * 100
        if cogs_growth_pct > rev_growth_pct:
            narrative_parts.append(
                f"COGS growth (+{cogs_growth_pct:.1f}%) outpaced revenue growth "
                f"(+{rev_growth_pct:.1f}%), compressing gross margin by "
                f"{abs(current_gpm - prior_gpm):.1f} percentage points "
                f"({prior_gpm:.1f}% to {current_gpm:.1f}%)."
            )
    if prior_marketing > 0 and current_marketing > 0 and prior_revenue > 0:
        mkt_growth_pct = ((current_marketing - prior_marketing) / prior_marketing) * 100
        rev_growth_pct = ((current_revenue - prior_revenue) / prior_revenue) * 100
        if mkt_growth_pct > rev_growth_pct * 2:
            prior_mkt_pct = (prior_marketing / prior_revenue) * 100
            current_mkt_pct = (current_marketing / current_revenue) * 100
            narrative_parts.append(
                f"Marketing expenditure increased {mkt_growth_pct:.1f}%, significantly above "
                f"the revenue growth rate, increasing marketing intensity from "
                f"{prior_mkt_pct:.1f}% to {current_mkt_pct:.1f}% of revenue."
            )
    if prior_cash > 0 and current_cash > 0:
        cash_growth_pct = ((current_cash - prior_cash) / prior_cash) * 100
        if cash_growth_pct > 50:
            narrative_parts.append(
                f"Cash increased {cash_growth_pct:.1f}% — see Cash Flow Statement for source of funds detail."
            )

    if narrative_parts:
        story.append(Spacer(1, 4))
        story.append(Paragraph(" ".join(narrative_parts), styles["MemoBodySmall"]))

    story.append(Spacer(1, 8))


# =============================================================================
# CONTENT: Sign Change & Dormant Account Detail Tables
# =============================================================================


def _build_sign_change_detail(
    story: list,
    styles: dict,
    movements: list[dict],
) -> None:
    """Build a detail table for accounts with sign changes, with suggested procedure."""
    sign_changes = [m for m in movements if m.get("movement_type") == "sign_change"]
    if not sign_changes:
        return

    story.append(Paragraph("<b>Sign Change Detail</b>", styles["MemoBody"]))
    story.append(Spacer(1, 2))
    story.append(
        Paragraph(
            "The following account(s) changed sign during the comparison period. A sign change "
            "indicates a shift from debit to credit balance (or vice versa), which may indicate "
            "a misclassification, an unusual transaction, or a legitimate business change "
            "requiring disclosure:",
            styles["MemoBodySmall"],
        )
    )
    story.append(Spacer(1, 4))

    headers = ["Account", "Prior Balance", "Current Balance", "Nature of Change"]
    col_widths = [2.4 * inch, 1.3 * inch, 1.3 * inch, 1.7 * inch]
    data: list[list] = [headers]

    for m in sign_changes[:20]:
        name = m.get("account_name", "")
        prior = m.get("prior_balance", 0)
        current = m.get("current_balance", 0)
        if prior >= 0 and current < 0:
            nature = "Debit to Credit"
        elif prior < 0 and current >= 0:
            nature = "Credit to Debit"
        else:
            nature = "Sign Reversal"
        data.append(
            [
                Paragraph(name, styles["MemoTableCell"]),
                _format_currency(prior),
                _format_currency(current),
                nature,
            ]
        )

    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Times-Roman"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                ("LINEBELOW", (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                ("ALIGN", (1, 0), (2, -1), "RIGHT"),
                ("ALIGN", (3, 0), (3, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (0, -1), 0),
            ]
        )
    )
    story.append(table)

    if len(sign_changes) > 20:
        story.append(
            Paragraph(
                f"+ {len(sign_changes) - 20} additional sign changes (see CSV export for full list)",
                styles["MemoBodySmall"],
            )
        )

    # Suggested procedure
    procedure = get_follow_up_procedure("apc_sign_change", rotation_index=1)
    if procedure:
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"<i>{procedure}</i>", styles["MemoBodySmall"]))

    story.append(Spacer(1, 8))


def _build_dormant_accounts_detail(
    story: list,
    styles: dict,
    dormant_accounts: list,
) -> None:
    """Build a detail table listing dormant account names with prior balances."""
    if not dormant_accounts:
        return

    story.append(Paragraph("<b>Dormant Account Detail</b>", styles["MemoBody"]))
    story.append(Spacer(1, 2))
    story.append(
        Paragraph(
            "The following accounts had balances in the prior period but show no "
            "activity or balance in the current period:",
            styles["MemoBodySmall"],
        )
    )
    story.append(Spacer(1, 4))

    # Support both simple strings and dicts with balance info
    has_balance = isinstance(dormant_accounts[0], dict) if dormant_accounts else False

    if has_balance:
        headers = ["#", "Account Name", "Prior Balance", "Current Balance", "Status"]
        col_widths = [0.3 * inch, 2.8 * inch, 1.2 * inch, 1.1 * inch, 1.3 * inch]
        data: list[list] = [headers]
        for idx, acct in enumerate(dormant_accounts[:20], 1):
            name = acct.get("account_name", "") if isinstance(acct, dict) else str(acct)
            prior_bal = acct.get("prior_balance", 0) if isinstance(acct, dict) else 0
            data.append(
                [
                    str(idx),
                    Paragraph(name, styles["MemoTableCell"]),
                    _format_currency(prior_bal),
                    "$0.00",
                    "Confirm: closed?",
                ]
            )
    else:
        headers = ["#", "Account Name"]
        col_widths = [0.5 * inch, 6.2 * inch]
        data = [headers]
        for idx, name in enumerate(dormant_accounts[:20], 1):
            data.append([str(idx), Paragraph(str(name), styles["MemoTableCell"])])

    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Times-Roman"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                ("LINEBELOW", (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (0, -1), 0),
            ]
        )
    )
    story.append(table)

    if len(dormant_accounts) > 20:
        story.append(
            Paragraph(
                f"+ {len(dormant_accounts) - 20} additional dormant accounts (see CSV export for full list)",
                styles["MemoBodySmall"],
            )
        )

    # Suggested procedure
    procedure = get_follow_up_procedure("apc_dormant_account", rotation_index=1)
    if procedure:
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"<i>{procedure}</i>", styles["MemoBodySmall"]))

    story.append(Spacer(1, 8))


# =============================================================================
# CONTENT: New and Closed Account Detail
# =============================================================================


def _build_new_closed_account_detail(
    story: list,
    styles: dict,
    new_accounts: list,
    closed_accounts: list,
) -> None:
    """Build detail tables for new and closed accounts."""
    if not new_accounts and not closed_accounts:
        return

    story.append(Paragraph("<b>New and Closed Account Detail</b>", styles["MemoBody"]))
    story.append(Spacer(1, 4))

    # New accounts
    if new_accounts:
        has_detail = isinstance(new_accounts[0], dict) if new_accounts else False
        story.append(
            Paragraph(
                f"<b>New Accounts ({len(new_accounts)} items)</b> — accounts present "
                "in the current period but not in the prior period:",
                styles["MemoBodySmall"],
            )
        )
        story.append(Spacer(1, 3))

        if has_detail:
            headers = ["Account Name", "Current Balance", "Account Type"]
            col_widths = [3.2 * inch, 1.5 * inch, 2.0 * inch]
            data: list[list] = [headers]
            for acct in new_accounts[:20]:
                name = acct.get("account_name", "") if isinstance(acct, dict) else str(acct)
                balance = acct.get("current_balance", 0) if isinstance(acct, dict) else 0
                acct_type = acct.get("account_type", "") if isinstance(acct, dict) else ""
                data.append(
                    [
                        Paragraph(name, styles["MemoTableCell"]),
                        _format_currency(balance),
                        acct_type.replace("_", " ").title(),
                    ]
                )
        else:
            headers = ["#", "Account Name"]
            col_widths = [0.5 * inch, 6.2 * inch]
            data = [headers]
            for idx, name in enumerate(new_accounts[:20], 1):
                data.append([str(idx), Paragraph(str(name), styles["MemoTableCell"])])

        table = Table(data, colWidths=col_widths, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                    ("FONTNAME", (0, 1), (-1, -1), "Times-Roman"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
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
        story.append(table)
        story.append(Spacer(1, 4))

    # Closed accounts
    if closed_accounts:
        has_detail = isinstance(closed_accounts[0], dict) if closed_accounts else False
        story.append(
            Paragraph(
                f"<b>Closed Accounts ({len(closed_accounts)} items)</b> — accounts present "
                "in the prior period but not in the current period:",
                styles["MemoBodySmall"],
            )
        )
        story.append(Spacer(1, 3))

        if has_detail:
            headers = ["Account Name", "Prior Balance", "Account Type"]
            col_widths = [3.2 * inch, 1.5 * inch, 2.0 * inch]
            data = [headers]
            for acct in closed_accounts[:20]:
                name = acct.get("account_name", "") if isinstance(acct, dict) else str(acct)
                balance = acct.get("prior_balance", 0) if isinstance(acct, dict) else 0
                acct_type = acct.get("account_type", "") if isinstance(acct, dict) else ""
                data.append(
                    [
                        Paragraph(name, styles["MemoTableCell"]),
                        _format_currency(balance),
                        acct_type.replace("_", " ").title(),
                    ]
                )
        else:
            headers = ["#", "Account Name"]
            col_widths = [0.5 * inch, 6.2 * inch]
            data = [headers]
            for idx, name in enumerate(closed_accounts[:20], 1):
                data.append([str(idx), Paragraph(str(name), styles["MemoTableCell"])])

        table = Table(data, colWidths=col_widths, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                    ("FONTNAME", (0, 1), (-1, -1), "Times-Roman"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
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
        story.append(table)
        story.append(Spacer(1, 4))

    # Suggested procedure
    procedure = get_follow_up_procedure("new_account", rotation_index=1)
    closed_procedure = get_follow_up_procedure("apc_closed_account", rotation_index=1)
    combined = []
    if new_accounts and procedure:
        combined.append(procedure)
    if closed_accounts and closed_procedure:
        combined.append(closed_procedure)
    if combined:
        story.append(Paragraph(f"<i>{' '.join(combined)}</i>", styles["MemoBodySmall"]))

    story.append(Spacer(1, 8))


# =============================================================================
# CONTENT: Lead Sheet Summary Table (with % Change)
# =============================================================================


def _build_lead_sheet_table(
    story: list,
    styles: dict,
    summaries: list[dict],
) -> None:
    """Build a table of lead sheet net changes with % Change column."""
    if not summaries:
        story.append(Paragraph("No lead sheet data available.", styles["MemoBodySmall"]))
        return

    # Cross-reference legend
    story.append(
        Paragraph(
            "The following lead sheet summary reflects aggregate movements by financial "
            "statement section. Letters correspond to the cross-reference index in the "
            "Financial Statements memo.",
            styles["MemoBodySmall"],
        )
    )
    story.append(Spacer(1, 4))

    headers = ["Lead", "Sheet Name", "Accounts", "Prior Total", "Current Total", "Net Change", "% Change"]
    col_widths = [0.4 * inch, 1.6 * inch, 0.6 * inch, 1.1 * inch, 1.1 * inch, 1.1 * inch, 0.8 * inch]

    data = [headers]
    for ls in summaries:
        code = ls.get("lead_sheet", "")
        name = ls.get("lead_sheet_name", "")
        count = str(ls.get("account_count", 0))
        prior_total = ls.get("prior_total", 0)
        current_total = ls.get("current_total", 0)
        net_change = ls.get("net_change", 0)

        # Compute % change
        if abs(prior_total) > 0.005:
            pct_change = (net_change / abs(prior_total)) * 100
            pct_str = f"{pct_change:+.1f}%"
        else:
            pct_str = "N/A"

        data.append(
            [
                code,
                Paragraph(name, styles["MemoTableCell"]),
                count,
                _format_currency(prior_total),
                _format_currency(current_total),
                _format_currency(net_change),
                pct_str,
            ]
        )

    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Times-Roman"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
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
    story.append(table)


# =============================================================================
# CONTENT: Cash Contextualization
# =============================================================================


def _build_cash_context(
    story: list,
    styles: dict,
    movements: list[dict],
) -> None:
    """Add cross-reference note for large cash increases."""
    cash_movements = [
        m
        for m in movements
        if _match_keyword(m.get("account_name", ""), _CASH_KEYWORDS)
        and m.get("change_percent") is not None
        and abs(m.get("change_percent", 0)) > 50
    ]
    if not cash_movements:
        return

    for m in cash_movements:
        change = _format_currency(abs(m.get("change_amount", 0)))
        pct = m.get("change_percent", 0)
        direction = "increase" if pct > 0 else "decrease"
        story.append(
            Paragraph(
                f"<i>Cash {direction} of {change} ({pct:+.1f}%). "
                "Cross-reference to Cash Flow Statement to confirm source of cash "
                "movement and assess whether operating, investing, or financing "
                "activities explain the change.</i>",
                styles["MemoBodySmall"],
            )
        )
    story.append(Spacer(1, 6))


# =============================================================================
# MAIN GENERATOR
# =============================================================================


def generate_multi_period_memo(
    comparison_result: dict[str, Any],
    filename: str = "multi_period_comparison",
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
    """Generate a PDF analytical procedures memo for multi-period comparison.

    Args:
        comparison_result: MovementSummaryResponse-shaped dict
        filename: Base filename for the report
        client_name: Client/entity name
        period_tested: Period description override
        prepared_by: Preparer name
        reviewed_by: Reviewer name
        workpaper_date: Date string (ISO format)

    Returns:
        PDF bytes
    """
    log_secure_operation("multi_period_memo_generate", f"Generating multi-period memo: {filename}")

    styles = create_memo_styles()
    buffer = io.BytesIO()
    reference = generate_reference_number().replace("PAC-", "APC-")

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=1.0 * inch,
        bottomMargin=0.8 * inch,
    )

    story = []
    prior_label = comparison_result.get("prior_label", "Prior")
    current_label = comparison_result.get("current_label", "Current")
    budget_label = comparison_result.get("budget_label")
    total_accounts = comparison_result.get("total_accounts", 0)
    movements_by_type = comparison_result.get("movements_by_type", {})
    movements_by_significance = comparison_result.get("movements_by_significance", {})
    significant_movements = comparison_result.get("significant_movements", [])
    all_movements = comparison_result.get("all_movements", significant_movements)
    lead_sheet_summaries = comparison_result.get("lead_sheet_summaries", [])
    dormant_count = comparison_result.get("dormant_account_count", 0)
    dormant_accounts = comparison_result.get("dormant_accounts", [])
    new_accounts = comparison_result.get("new_accounts", [])
    closed_accounts = comparison_result.get("closed_accounts", [])
    composite_data = comparison_result.get("composite", {})

    material_count = movements_by_significance.get("material", 0)
    significant_count = movements_by_significance.get("significant", 0)
    minor_count = movements_by_significance.get("minor", 0)
    sign_change_count = movements_by_type.get("sign_change", 0)
    new_count = movements_by_type.get("new_account", 0)
    closed_count = movements_by_type.get("closed_account", 0)

    # 1. COVER PAGE
    logo_path = find_logo()
    metadata = ReportMetadata(
        title="Analytical Procedures Memo",
        client_name=client_name or "",
        engagement_period=period_tested or "",
        source_document=filename,
        source_document_title=source_document_title or "",
        source_context_note=source_context_note or "",
        reference=reference,
        fiscal_year_end=fiscal_year_end or "",
    )
    build_cover_page(story, styles, metadata, doc.width, logo_path)

    # ================================================================
    # I. SCOPE
    # ================================================================
    story.append(Paragraph("I. Scope", styles["MemoSection"]))
    story.append(LedgerRule(doc.width))

    period_desc = period_tested or f"{prior_label} vs. {current_label}"
    if budget_label:
        period_desc += f" vs. {budget_label}"

    # Source document transparency
    source_scope_lines = []
    if source_document_title and filename:
        source_scope_lines.append(create_leader_dots("Source", f"{source_document_title} ({filename})"))
    elif source_document_title:
        source_scope_lines.append(create_leader_dots("Source", source_document_title))
    elif filename:
        source_scope_lines.append(create_leader_dots("Source", filename))

    scope_lines = source_scope_lines + [
        create_leader_dots("Periods Compared", period_desc),
        create_leader_dots("Total Accounts Analyzed", f"{total_accounts:,}"),
        create_leader_dots("Material Movements", str(material_count)),
        create_leader_dots("Significant Movements", str(significant_count)),
        create_leader_dots("Minor Movements", str(minor_count)),
    ]
    if sign_change_count > 0:
        scope_lines.append(create_leader_dots("Sign Changes", str(sign_change_count)))
    if new_count > 0 or closed_count > 0:
        scope_lines.append(
            create_leader_dots(
                "New/Closed Accounts", f"{new_count + closed_count} ({new_count} new, {closed_count} closed)"
            )
        )
    if dormant_count > 0:
        scope_lines.append(create_leader_dots("Dormant Accounts", str(dormant_count)))

    for line in scope_lines:
        story.append(Paragraph(line, styles["MemoLeader"]))
    story.append(Spacer(1, 8))

    build_scope_statement(
        story,
        styles,
        doc.width,
        tool_domain="multi_period_comparison",
        framework=resolved_framework,
        domain_label="analytical procedures and trend analysis",
    )

    # ================================================================
    # II. MOVEMENT SUMMARY
    # ================================================================
    story.append(Paragraph("II. Movement Summary", styles["MemoSection"]))
    story.append(LedgerRule(doc.width))

    type_labels = {
        "new_account": "New Accounts",
        "closed_account": "Closed Accounts",
        "sign_change": "Sign Changes",
        "increase": "Increases",
        "decrease": "Decreases",
        "unchanged": "Unchanged",
    }
    for type_key, type_label in type_labels.items():
        count = movements_by_type.get(type_key, 0)
        if count > 0:
            story.append(
                Paragraph(
                    create_leader_dots(type_label, str(count)),
                    styles["MemoLeader"],
                )
            )
    story.append(Spacer(1, 8))

    # ================================================================
    # III. RESULTS SUMMARY
    # ================================================================
    story.append(Paragraph("III. Results Summary", styles["MemoSection"]))
    story.append(LedgerRule(doc.width))

    # Compute risk score if not pre-computed
    if composite_data:
        risk_score = composite_data.get("score", 0)
        risk_tier = composite_data.get("risk_tier", "low")
    else:
        # Derive risk inputs from available data
        cash_increase_pct = 0.0
        cogs_growth_vs_revenue = False
        single_account_revenue_pct = 0.0
        high_growth_count = 0

        for m in significant_movements:
            pct = m.get("change_percent")
            if pct is not None and abs(pct) > 25:
                high_growth_count += 1
            name = m.get("account_name", "").lower()
            if "cash" in name and pct is not None:
                cash_increase_pct = max(cash_increase_pct, pct / 100.0)

        # Check COGS vs revenue growth from all_movements
        prior_rev = sum(
            abs(m.get("prior_balance", 0))
            for m in all_movements
            if _match_keyword(m.get("account_name", ""), _REVENUE_KEYWORDS)
        )
        curr_rev = sum(
            abs(m.get("current_balance", 0))
            for m in all_movements
            if _match_keyword(m.get("account_name", ""), _REVENUE_KEYWORDS)
        )
        prior_cogs = sum(
            abs(m.get("prior_balance", 0))
            for m in all_movements
            if _match_keyword(m.get("account_name", ""), _COGS_KEYWORDS)
        )
        curr_cogs = sum(
            abs(m.get("current_balance", 0))
            for m in all_movements
            if _match_keyword(m.get("account_name", ""), _COGS_KEYWORDS)
        )

        if prior_rev > 0 and prior_cogs > 0:
            rev_growth = (curr_rev - prior_rev) / prior_rev
            cogs_growth = (curr_cogs - prior_cogs) / prior_cogs
            cogs_growth_vs_revenue = cogs_growth > rev_growth

        # Single-account revenue concentration
        if curr_rev > 0:
            rev_accounts = [
                abs(m.get("current_balance", 0))
                for m in all_movements
                if _match_keyword(m.get("account_name", ""), _REVENUE_KEYWORDS)
            ]
            if rev_accounts:
                single_account_revenue_pct = max(rev_accounts) / curr_rev

        risk_score = compute_apc_risk_score(
            material_movement_count=material_count,
            sign_change_count=sign_change_count,
            cash_increase_pct=cash_increase_pct,
            cogs_growth_vs_revenue=cogs_growth_vs_revenue,
            single_account_revenue_pct=single_account_revenue_pct,
            high_growth_accounts=high_growth_count,
            dormant_count=dormant_count,
            new_closed_count=new_count + closed_count,
        )
        risk_tier = score_to_risk_tier(risk_score).value

    tier_label, _ = RISK_TIER_DISPLAY.get(risk_tier, ("UNKNOWN", ClassicalColors.OBSIDIAN_DEEP))

    story.append(Paragraph(create_leader_dots("Composite Risk Score", f"{risk_score:.1f} / 100"), styles["MemoLeader"]))
    story.append(Paragraph(create_leader_dots("Risk Tier", tier_label), styles["MemoLeader"]))
    story.append(Paragraph(RISK_SCALE_LEGEND, styles["MemoBodySmall"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph(create_leader_dots("Material Movements", str(material_count)), styles["MemoLeader"]))
    story.append(Paragraph(create_leader_dots("Significant Movements", str(significant_count)), styles["MemoLeader"]))
    story.append(Paragraph(create_leader_dots("Sign Changes", str(sign_change_count)), styles["MemoLeader"]))
    story.append(
        Paragraph(
            create_leader_dots(
                "New/Closed Accounts", f"{new_count + closed_count} ({new_count} new, {closed_count} closed)"
            ),
            styles["MemoLeader"],
        )
    )
    story.append(Paragraph(create_leader_dots("Dormant Accounts", str(dormant_count)), styles["MemoLeader"]))
    story.append(Spacer(1, 8))

    # ================================================================
    # IV. SIGNIFICANT ACCOUNT MOVEMENTS
    # ================================================================
    story.append(Paragraph("IV. Significant Account Movements", styles["MemoSection"]))
    story.append(LedgerRule(doc.width))
    _build_significant_movements_table(story, styles, significant_movements)
    story.append(Spacer(1, 6))

    # Suggested procedures for material movements
    _build_suggested_procedures(story, styles, significant_movements)

    # Cash contextualization
    _build_cash_context(story, styles, significant_movements)

    # Sign Change Detail
    _build_sign_change_detail(story, styles, all_movements)

    # Dormant Account Detail
    _build_dormant_accounts_detail(story, styles, dormant_accounts)

    # New and Closed Account Detail
    _build_new_closed_account_detail(story, styles, new_accounts, closed_accounts)

    # Ratio Trends (computed from full TB population)
    _build_ratio_trends_table(story, styles, all_movements, prior_label, current_label)

    # ================================================================
    # V. LEAD SHEET SUMMARY
    # ================================================================
    section_num = "V"
    if lead_sheet_summaries:
        stripped_summaries = []
        for ls in lead_sheet_summaries:
            stripped_summaries.append(
                {
                    "lead_sheet": ls.get("lead_sheet", ""),
                    "lead_sheet_name": ls.get("lead_sheet_name", ""),
                    "account_count": ls.get("account_count", 0),
                    "prior_total": ls.get("prior_total", 0),
                    "current_total": ls.get("current_total", 0),
                    "net_change": ls.get("net_change", 0),
                }
            )

        story.append(Paragraph(f"{section_num}. Lead Sheet Summary", styles["MemoSection"]))
        story.append(LedgerRule(doc.width))
        _build_lead_sheet_table(story, styles, stripped_summaries)
        story.append(Spacer(1, 8))
        section_num = "VI"

    # ================================================================
    # METHODOLOGY & AUTHORITATIVE REFERENCES
    # ================================================================
    build_methodology_statement(
        story,
        styles,
        doc.width,
        tool_domain="multi_period_comparison",
        framework=resolved_framework,
        domain_label="analytical procedures and trend analysis",
    )
    build_authoritative_reference_block(
        story,
        styles,
        doc.width,
        tool_domain="multi_period_comparison",
        framework=resolved_framework,
        domain_label="analytical procedures and trend analysis",
        section_label=f"{section_num}.",
    )
    # Increment past the references section
    section_num = {"V": "VI", "VI": "VII"}.get(section_num, section_num)

    # ================================================================
    # CONCLUSION
    # ================================================================
    story.append(Paragraph(f"{section_num}. Conclusion", styles["MemoSection"]))
    story.append(LedgerRule(doc.width))

    assessment = _RISK_CONCLUSIONS.get(risk_tier, _RISK_CONCLUSIONS["low"])
    story.append(Paragraph(assessment, styles["MemoBody"]))
    story.append(Spacer(1, 12))

    # WORKPAPER SIGN-OFF
    build_workpaper_signoff(
        story, styles, doc.width, prepared_by, reviewed_by, workpaper_date, include_signoff=include_signoff
    )

    # INTELLIGENCE STAMP
    build_intelligence_stamp(story, styles, client_name=client_name, period_tested=period_tested)

    # DISCLAIMER
    build_disclaimer(
        story,
        styles,
        domain="analytical procedures and trend analysis",
        isa_reference="ISA 520 (Analytical Procedures) and PCAOB AS 2305 (Substantive Analytical Procedures)",
    )

    # Build PDF (page footer on all pages)
    doc.build(story, onFirstPage=draw_page_footer, onLaterPages=draw_page_footer)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    log_secure_operation("multi_period_memo_complete", f"Multi-period memo generated: {len(pdf_bytes)} bytes")
    return pdf_bytes
