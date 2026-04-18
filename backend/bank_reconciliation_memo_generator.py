"""
Bank Reconciliation Testing Memo PDF Generator (Sprint 128 / Sprint 503 rewrite)

Auto-generated reconciliation memo per ISA 500 (Audit Evidence) /
ISA 505 (External Confirmations) / PCAOB AS 2310.
Renaissance Ledger aesthetic consistent with existing PDF exports.

Sections:
1. Scope (bank transactions, ledger transactions, column detection, proof summary)
2. Methodology (8 tests documented)
3. Reconciliation Results (matched, outstanding, reconciling difference,
   ending balance reconciliation, reconciling difference characterization)
4. Outstanding Items (aging tables with per-item priority flags)
5. Results Summary (composite diagnostic score, tier, severity counts)
6. Key Findings (reconciling difference, outstanding volume, dynamic test findings)
7. Authoritative References
8. Conclusion
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
    build_proof_summary_section,
    build_workpaper_signoff,
    create_memo_styles,
    wrap_table_strings,
)
from shared.report_chrome import (
    ReportMetadata,
    build_cover_page,
    draw_page_footer,
    find_logo,
)
from shared.report_styles import ledger_table_style
from shared.scope_methodology import (
    build_authoritative_reference_block,
    build_methodology_statement,
    build_scope_statement,
)

# =============================================================================
# CONSTANTS
# =============================================================================

_MAX_AGING_ROWS = 20

# Methodology descriptions for all 8 tests
_TEST_DESCRIPTIONS: dict[str, str] = {
    "exact_match": (
        "Reconciles bank statement transactions to general ledger entries using "
        "exact amount matching with configurable date tolerance. Greedy algorithm "
        "matches largest amounts first to minimize residual differences."
    ),
    "bank_only_items": (
        "Identifies transactions present on the bank statement but absent from the "
        "general ledger. These represent outstanding deposits in transit that have "
        "not yet been recorded in the books."
    ),
    "ledger_only_items": (
        "Identifies transactions recorded in the general ledger but not yet cleared "
        "at the bank. These represent outstanding checks or disbursements pending "
        "bank clearance."
    ),
    "stale_deposits": (
        "Flags outstanding deposits older than 10 days before the statement date. "
        "Deposits in transit older than 10 days may indicate fictitious deposits "
        "recorded in the ledger but not yet cleared at the bank."
    ),
    "stale_checks": (
        "Flags outstanding checks older than 90 days. Stale checks may require "
        "escheatment review under applicable unclaimed property laws and may "
        "indicate fictitious disbursements recorded in the ledger."
    ),
    "nsf_items": (
        "Searches transaction description fields for keywords indicating returned "
        "or dishonored items (NSF, RETURN, INSUFFICIENT, R01, R02, CHARGEBACK, "
        "REVERSED, DISHONORED). NSF items may indicate customer financial distress "
        "or payment fraud per ISA 240."
    ),
    "interbank_transfers": (
        "Flags same-day matching debit/credit pairs above $10,000 as potential "
        "check kiting indicators per ISA 240 (A40). Kiting involves exploiting "
        "float between accounts to artificially inflate balances."
    ),
    "high_value_transactions": (
        "Flags individual transactions exceeding performance materiality. High-value "
        "items warrant individual verification per ISA 500 to confirm proper "
        "authorization and recording."
    ),
}


# =============================================================================
# SECTION BUILDERS
# =============================================================================


def _build_methodology_table(
    story: list,
    styles: dict,
    doc_width: float,
    test_results: list[dict],
) -> None:
    """Build Section II: Methodology table with all 8 tests."""
    story.append(Paragraph("II. Methodology", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))
    story.append(
        Paragraph(
            "The following automated reconciliation tests were applied to the "
            "bank statement and general ledger transaction data. Each test is "
            "classified by tier (structural, statistical, or advanced) and "
            "described below:",
            styles["MemoBody"],
        )
    )
    story.append(Spacer(1, 4))

    method_data = [["Test", "Tier", "Description"]]
    for tr in test_results:
        test_key = tr.get("test_key", "")
        desc = _TEST_DESCRIPTIONS.get(test_key, tr.get("description", ""))
        method_data.append(
            [
                Paragraph(tr.get("test_name", ""), styles["MemoTableCell"]),
                Paragraph(tr.get("test_tier", "structural").title(), styles["MemoTableCell"]),
                Paragraph(desc, styles["MemoTableCell"]),
            ]
        )

    method_table = Table(method_data, colWidths=[1.5 * inch, 0.8 * inch, 4.3 * inch], repeatRows=1)
    method_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                ("LINEBELOW", (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (0, -1), 0),
            ]
        )
    )
    story.append(method_table)
    story.append(Spacer(1, 8))


def _build_reconciliation_results(
    story: list,
    styles: dict,
    doc_width: float,
    summary: dict,
    rec_result: dict,
) -> None:
    """Build Section III: Reconciliation Results with ending balance tie and characterization."""
    story.append(Paragraph("III. Reconciliation Results", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    matched = summary.get("matched_count", 0)
    bank_only = summary.get("bank_only_count", 0)
    ledger_only = summary.get("ledger_only_count", 0)
    total_txns = matched + bank_only + ledger_only
    matched_amount = summary.get("matched_amount", 0)
    bank_only_amount = summary.get("bank_only_amount", 0)
    ledger_only_amount = summary.get("ledger_only_amount", 0)
    rec_diff = summary.get("reconciling_difference", 0)
    total_bank = summary.get("total_bank", 0)
    total_ledger = summary.get("total_ledger", 0)
    match_rate = matched / total_txns if total_txns > 0 else 0

    result_lines = [
        create_leader_dots("Matched Transactions", f"{matched:,} ({match_rate:.1%})"),
        create_leader_dots("Matched Amount", f"${abs(matched_amount):,.2f}"),
        create_leader_dots("Bank-Only (Outstanding Deposits)", f"{bank_only:,}"),
        create_leader_dots("Ledger-Only (Outstanding Checks)", f"{ledger_only:,}"),
        create_leader_dots("Reconciling Difference", f"${abs(rec_diff):,.2f}"),
    ]

    for line in result_lines:
        story.append(Paragraph(line, styles["MemoLeader"]))
    story.append(Spacer(1, 6))

    # Balance summary table
    balance_data = [
        ["Category", "Amount"],
        ["Bank Statement Total", f"${total_bank:,.2f}"],
        ["General Ledger Total", f"${total_ledger:,.2f}"],
        ["Reconciling Difference", f"${rec_diff:,.2f}"],
    ]
    balance_data = wrap_table_strings(balance_data, styles)
    balance_table = Table(balance_data, colWidths=[3.0 * inch, 2.5 * inch])
    balance_table.setStyle(TableStyle(ledger_table_style() + [("ALIGN", (1, 0), (-1, -1), "RIGHT")]))
    story.append(balance_table)
    story.append(Spacer(1, 2))
    story.append(
        Paragraph(
            "Note: Bank Statement and General Ledger totals above represent aggregate "
            "transaction activity (sum of matched and unmatched items), not ending account balances.",
            styles["MemoBodySmall"],
        )
    )
    story.append(Spacer(1, 8))

    # IMPROVEMENT-02: Ending Balance Reconciliation
    ending_balance = rec_result.get("ending_balance_reconciliation")
    if ending_balance:
        story.append(Paragraph("Ending Balance Reconciliation", styles["MemoSection"]))
        story.append(Spacer(1, 4))

        bank_ending = ending_balance.get("bank_ending_balance")
        gl_ending = ending_balance.get("gl_ending_balance")

        if bank_ending is not None:
            adjusted_bank = bank_ending - bank_only_amount + ledger_only_amount
            story.append(
                Paragraph(
                    create_leader_dots("Bank Balance (per statement)", f"${bank_ending:,.2f}"),
                    styles["MemoLeader"],
                )
            )
            story.append(
                Paragraph(
                    create_leader_dots("Less: Outstanding Deposits (in transit)", f"${bank_only_amount:,.2f}"),
                    styles["MemoLeader"],
                )
            )
            story.append(
                Paragraph(
                    create_leader_dots("Plus: Outstanding Checks", f"+ ${ledger_only_amount:,.2f}"),
                    styles["MemoLeader"],
                )
            )
            story.append(
                Paragraph(
                    create_leader_dots("Adjusted Bank Balance", f"= ${adjusted_bank:,.2f}"),
                    styles["MemoLeader"],
                )
            )
            story.append(Spacer(1, 4))
        else:
            story.append(
                Paragraph(
                    "<i>Ending balance not determinable from transaction data — obtain from bank statement.</i>",
                    styles["MemoBodySmall"],
                )
            )

        if gl_ending is not None:
            story.append(
                Paragraph(
                    create_leader_dots("Book Balance (per GL)", f"${gl_ending:,.2f}"),
                    styles["MemoLeader"],
                )
            )
            story.append(
                Paragraph(
                    create_leader_dots("Adjusted Book Balance", f"${gl_ending:,.2f}"),
                    styles["MemoLeader"],
                )
            )
            story.append(Spacer(1, 4))

            if bank_ending is not None:
                variance = adjusted_bank - gl_ending
                if abs(variance) < 0.01:
                    story.append(
                        Paragraph(
                            "&#x2713; Reconciled — adjusted bank balance agrees to book balance.",
                            styles["MemoBody"],
                        )
                    )
                else:
                    story.append(
                        Paragraph(
                            f"&#x26A0; Adjusted balances do not reconcile — "
                            f"investigate residual difference of ${abs(variance):,.2f}",
                            styles["MemoBody"],
                        )
                    )
        else:
            story.append(
                Paragraph(
                    "<i>Upload trial balance to complete ending balance reconciliation.</i>",
                    styles["MemoBodySmall"],
                )
            )

        story.append(Spacer(1, 8))

    # IMPROVEMENT-03: Reconciling Difference Characterization
    if abs(rec_diff) > 0.01:
        story.append(Paragraph("Reconciling Difference Analysis", styles["MemoSection"]))
        story.append(Spacer(1, 4))

        direction = (
            "Bank > GL (bank shows more activity than ledger)"
            if rec_diff > 0
            else "GL > Bank (ledger shows more activity than bank)"
        )
        pct_of_activity = abs(rec_diff) / abs(total_bank) * 100 if abs(total_bank) > 0 else 0

        char_lines = [
            create_leader_dots("Amount", f"${abs(rec_diff):,.2f}"),
            create_leader_dots("Direction", direction),
            create_leader_dots("As % of Total Activity", f"{pct_of_activity:.2f}%"),
        ]
        for line in char_lines:
            story.append(Paragraph(line, styles["MemoLeader"]))
        story.append(Spacer(1, 4))

        story.append(Paragraph("Potential Explanations:", styles["MemoBody"]))
        explanations = [
            "GL recording omission — transaction present in bank, not in GL",
            "Bank error — transaction on bank statement not belonging to this account",
            "Timing difference — transaction outside the matching window",
            "Fraudulent transaction — unauthorized transaction cleared at bank",
        ]
        for exp in explanations:
            story.append(Paragraph(f"&#x25A2;  {exp}", styles["MemoBody"]))

        # Cross-reference to AR difference (conditional)
        ar_cross_ref = rec_result.get("ar_cross_reference")
        if ar_cross_ref and ar_cross_ref.get("ar_reconciling_difference", 0) > 0:
            ar_diff = ar_cross_ref["ar_reconciling_difference"]
            ar_ref = ar_cross_ref.get("ar_reference", "")
            story.append(Spacer(1, 4))
            story.append(
                Paragraph(
                    f"<i>Note: An unreconciled AR subledger difference of "
                    f"${ar_diff:,.2f} was identified in the AR Aging Analysis memo "
                    f"(Ref: {ar_ref}). The bank and AR differences should be "
                    f"investigated concurrently to determine whether they are related.</i>",
                    styles["MemoBodySmall"],
                )
            )

        story.append(Spacer(1, 8))


def _build_outstanding_aging_tables(
    story: list,
    styles: dict,
    doc_width: float,
    rec_result: dict,
    summary: dict,
) -> None:
    """Build Section IV: Outstanding Items with full aging tables."""
    bank_only = summary.get("bank_only_count", 0)
    ledger_only = summary.get("ledger_only_count", 0)
    bank_only_amount = summary.get("bank_only_amount", 0)
    ledger_only_amount = summary.get("ledger_only_amount", 0)

    if bank_only == 0 and ledger_only == 0:
        return

    story.append(Paragraph("IV. Outstanding Items", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    # Outstanding Deposits aging table
    deposits = rec_result.get("outstanding_deposits", [])
    if deposits:
        story.append(Paragraph("Outstanding Deposits (Bank-Only) — Aging Analysis", styles["MemoSection"]))
        story.append(Spacer(1, 4))

        # Sort by days outstanding descending
        sorted_deposits = sorted(deposits, key=lambda d: d.get("days_outstanding", 0), reverse=True)
        display_deposits = sorted_deposits[:_MAX_AGING_ROWS]

        cell_style = styles["MemoTableCell"]
        dep_data = [["Transaction Date", "Days Outstanding", "Description", "Amount", "Priority"]]
        for dep in display_deposits:
            days = dep.get("days_outstanding")
            if days is not None and days > 30:
                tier_key = "high"
            elif days is not None and days > 10:
                tier_key = "moderate"
            else:
                tier_key = "low"
            tier_label = RISK_TIER_DISPLAY[tier_key][0]
            priority = f"{tier_label} ({days}d)" if days is not None else tier_label

            dep_data.append(
                [
                    Paragraph(str(dep.get("date", "N/A")), cell_style),
                    Paragraph(str(days) if days is not None else "N/A", cell_style),
                    Paragraph(dep.get("description", "")[:40], cell_style),
                    Paragraph(f"${abs(dep.get('amount', 0)):,.2f}", cell_style),
                    Paragraph(priority, cell_style),
                ]
            )

        dep_data.append(
            [
                Paragraph("Total", cell_style),
                Paragraph("", cell_style),
                Paragraph("", cell_style),
                Paragraph(f"${abs(bank_only_amount):,.2f}", cell_style),
                Paragraph("", cell_style),
            ]
        )

        dep_table = Table(
            dep_data,
            colWidths=[1.2 * inch, 1.0 * inch, 2.0 * inch, 1.2 * inch, 0.8 * inch],
            repeatRows=1,
        )
        dep_table.setStyle(TableStyle(ledger_table_style() + [("ALIGN", (1, 0), (-1, -1), "RIGHT")]))
        # Bold total row
        dep_table.setStyle(TableStyle([("FONTNAME", (0, -1), (-1, -1), "Times-Bold")]))
        story.append(dep_table)

        if len(sorted_deposits) > _MAX_AGING_ROWS:
            story.append(Spacer(1, 2))
            story.append(
                Paragraph(
                    f"Showing {_MAX_AGING_ROWS} of {len(sorted_deposits)} items. "
                    "Full listing available in source data export.",
                    styles["MemoBodySmall"],
                )
            )
        story.append(Spacer(1, 8))
    elif bank_only > 0:
        # Fallback: summary only
        story.append(
            Paragraph(
                f"Outstanding Deposits: {bank_only:,} items totaling ${abs(bank_only_amount):,.2f}",
                styles["MemoBody"],
            )
        )
        story.append(Spacer(1, 4))

    # Outstanding Checks aging table
    checks = rec_result.get("outstanding_checks", [])
    if checks:
        story.append(Paragraph("Outstanding Checks (Ledger-Only) — Aging Analysis", styles["MemoSection"]))
        story.append(Spacer(1, 4))

        sorted_checks = sorted(checks, key=lambda c: c.get("days_outstanding", 0), reverse=True)
        display_checks = sorted_checks[:_MAX_AGING_ROWS]

        cell_style_chk = styles["MemoTableCell"]
        chk_data = [["Transaction Date", "Days Outstanding", "Description", "Amount", "Priority"]]
        for chk in display_checks:
            days = chk.get("days_outstanding")
            if days is not None and days > 90:
                tier_key = "high"
            elif days is not None and days > 30:
                tier_key = "moderate"
            else:
                tier_key = "low"
            tier_label = RISK_TIER_DISPLAY[tier_key][0]
            priority = f"{tier_label} ({days}d)" if days is not None else tier_label

            chk_data.append(
                [
                    Paragraph(str(chk.get("date", "N/A")), cell_style_chk),
                    Paragraph(str(days) if days is not None else "N/A", cell_style_chk),
                    Paragraph(chk.get("description", "")[:40], cell_style_chk),
                    Paragraph(f"${abs(chk.get('amount', 0)):,.2f}", cell_style_chk),
                    Paragraph(priority, cell_style_chk),
                ]
            )

        chk_data.append(
            [
                Paragraph("Total", cell_style_chk),
                Paragraph("", cell_style_chk),
                Paragraph("", cell_style_chk),
                Paragraph(f"${abs(ledger_only_amount):,.2f}", cell_style_chk),
                Paragraph("", cell_style_chk),
            ]
        )

        chk_table = Table(
            chk_data,
            colWidths=[1.2 * inch, 1.0 * inch, 2.0 * inch, 1.2 * inch, 0.8 * inch],
            repeatRows=1,
        )
        chk_table.setStyle(TableStyle(ledger_table_style() + [("ALIGN", (1, 0), (-1, -1), "RIGHT")]))
        chk_table.setStyle(TableStyle([("FONTNAME", (0, -1), (-1, -1), "Times-Bold")]))
        story.append(chk_table)

        if len(sorted_checks) > _MAX_AGING_ROWS:
            story.append(Spacer(1, 2))
            story.append(
                Paragraph(
                    f"Showing {_MAX_AGING_ROWS} of {len(sorted_checks)} items. "
                    "Full listing available in source data export.",
                    styles["MemoBodySmall"],
                )
            )
        story.append(Spacer(1, 8))
    elif ledger_only > 0:
        story.append(
            Paragraph(
                f"Outstanding Checks: {ledger_only:,} items totaling ${abs(ledger_only_amount):,.2f}",
                styles["MemoBody"],
            )
        )
        story.append(Spacer(1, 4))

    # Outstanding Items Summary block
    aging_summary = rec_result.get("aging_summary")
    if aging_summary:
        story.append(Paragraph("Outstanding Items Summary", styles["MemoSection"]))
        story.append(Spacer(1, 4))

        dep_over_10 = aging_summary.get("deposits_over_10_days", {})
        dep_over_30 = aging_summary.get("deposits_over_30_days", {})
        chk_over_30 = aging_summary.get("checks_over_30_days", {})
        chk_over_90 = aging_summary.get("checks_over_90_days", {})

        summary_lines = [
            create_leader_dots(
                "Deposits > 10 days old",
                f"{dep_over_10.get('count', 0)}   ${dep_over_10.get('amount', 0):,.2f}"
                f"   ({dep_over_10.get('pct', 0):.0f}% of total deposits)",
            ),
            create_leader_dots(
                "Deposits > 30 days old",
                f"{dep_over_30.get('count', 0)}   ${dep_over_30.get('amount', 0):,.2f}   Priority: HIGH",
            ),
            create_leader_dots(
                "Checks > 90 days old",
                f"{chk_over_90.get('count', 0)}   ${chk_over_90.get('amount', 0):,.2f}   Priority: HIGH (stale)",
            ),
            create_leader_dots(
                "Checks > 30 days old",
                f"{chk_over_30.get('count', 0)}   ${chk_over_30.get('amount', 0):,.2f}",
            ),
        ]
        for line in summary_lines:
            story.append(Paragraph(line, styles["MemoLeader"]))
        story.append(Spacer(1, 8))

    story.append(
        Paragraph(
            "Outstanding items represent transactions present in one source but not the other. "
            "These may represent timing differences, recording errors, or items requiring investigation.",
            styles["MemoBodySmall"],
        )
    )
    story.append(Spacer(1, 8))


def _build_key_findings(
    story: list,
    styles: dict,
    doc_width: float,
    rec_result: dict,
    summary: dict,
    composite: dict,
) -> None:
    """Build Section VI: Key Findings."""
    story.append(Paragraph("VI. Key Findings", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    finding_num = 0
    rec_diff = summary.get("reconciling_difference", 0)
    total_bank = summary.get("total_bank", 0)
    total_ledger = summary.get("total_ledger", 0)
    bank_only = summary.get("bank_only_count", 0)
    ledger_only = summary.get("ledger_only_count", 0)
    bank_only_amount = summary.get("bank_only_amount", 0)
    ledger_only_amount = summary.get("ledger_only_amount", 0)

    # Finding 1: Reconciling Difference (always present if nonzero)
    if abs(rec_diff) > 0.01:
        finding_num += 1
        story.append(
            Paragraph(
                f"<b>{finding_num}. Reconciling Difference of ${abs(rec_diff):,.2f} (HIGH)</b>",
                styles["MemoBody"],
            )
        )
        story.append(
            Paragraph(
                f"A reconciling difference of ${abs(rec_diff):,.2f} exists between bank statement "
                f"activity (${abs(total_bank):,.2f}) and general ledger activity "
                f"(${abs(total_ledger):,.2f}). This difference has not been explained by the "
                f"automated matching process.",
                styles["MemoBody"],
            )
        )
        procedure = get_follow_up_procedure("reconciling_difference", rotation_index=finding_num)
        if procedure:
            story.append(Paragraph(f"<i>Suggested follow-up: {procedure}</i>", styles["MemoBodySmall"]))

        # Cross-reference to AR difference
        ar_cross_ref = rec_result.get("ar_cross_reference")
        if ar_cross_ref and ar_cross_ref.get("ar_reconciling_difference", 0) > 0:
            ar_diff = ar_cross_ref["ar_reconciling_difference"]
            ar_ref = ar_cross_ref.get("ar_reference", "")
            story.append(
                Paragraph(
                    f"<i>Note: An unreconciled AR subledger difference of ${ar_diff:,.2f} "
                    f"was identified in the AR Aging Analysis (Ref: {ar_ref}). "
                    f"These two differences may be related — investigate concurrently.</i>",
                    styles["MemoBodySmall"],
                )
            )
        story.append(Spacer(1, 4))

    # Finding 2: Outstanding Items Volume (always present if outstanding > 0)
    total_outstanding = bank_only + ledger_only
    if total_outstanding > 0:
        finding_num += 1
        story.append(
            Paragraph(
                f"<b>{finding_num}. Outstanding Items Volume (MEDIUM)</b>",
                styles["MemoBody"],
            )
        )
        story.append(
            Paragraph(
                f"{total_outstanding} outstanding items remain unmatched "
                f"({bank_only} deposits totaling ${abs(bank_only_amount):,.2f}; "
                f"{ledger_only} checks totaling ${abs(ledger_only_amount):,.2f}). "
                f"Aging analysis in Section IV identifies items requiring priority investigation.",
                styles["MemoBody"],
            )
        )
        procedure = get_follow_up_procedure("outstanding_volume", rotation_index=finding_num)
        if procedure:
            story.append(Paragraph(f"<i>Suggested follow-up: {procedure}</i>", styles["MemoBodySmall"]))
        story.append(Spacer(1, 4))

    # Dynamic findings from rec_tests
    rec_tests = rec_result.get("rec_tests", [])
    test_key_map = {
        "Stale Deposits (>10 days)": "stale_deposits",
        "Stale Checks (>90 days)": "stale_checks",
        "NSF / Returned Items": "nsf_items",
        "Interbank Transfers": "interbank_transfers",
        "High Value (>Materiality)": "high_value_transactions",
    }

    for rt in rec_tests:
        flagged = rt.get("flagged_count", 0)
        if flagged == 0:
            continue

        finding_num += 1
        test_name = rt.get("test_name", "")
        severity = rt.get("severity", "medium").upper()
        story.append(
            Paragraph(
                f"<b>{finding_num}. {test_name} ({severity})</b>",
                styles["MemoBody"],
            )
        )
        story.append(
            Paragraph(
                f"{flagged} item(s) flagged by the {test_name} test.",
                styles["MemoBody"],
            )
        )
        test_key = test_key_map.get(test_name, "")
        procedure = get_follow_up_procedure(test_key, rotation_index=finding_num)
        if procedure:
            story.append(Paragraph(f"<i>Suggested follow-up: {procedure}</i>", styles["MemoBodySmall"]))
        story.append(Spacer(1, 4))

    if finding_num == 0:
        story.append(
            Paragraph(
                "No items requiring further investigation were identified.",
                styles["MemoBody"],
            )
        )

    story.append(Spacer(1, 8))


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================


def generate_bank_rec_memo(
    rec_result: dict[str, Any],
    filename: str = "bank_reconciliation",
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
    """Generate a PDF testing memo for bank reconciliation results.

    Args:
        rec_result: BankRecResult.to_dict() output, enriched with
            test_results, composite_score, outstanding_deposits/checks,
            ending_balance_reconciliation, aging_summary, ar_cross_reference
        filename: Base filename for the report
        client_name: Client/entity name
        period_tested: Period description (e.g., "December 2025")

    Returns:
        PDF bytes
    """
    log_secure_operation("bank_rec_memo_generate", f"Generating bank reconciliation memo: {filename}")

    styles = create_memo_styles()
    buffer = io.BytesIO()
    reference = generate_reference_number().replace("PAC-", "REC-")

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=1.0 * inch,
        bottomMargin=0.8 * inch,
    )

    story: list[Any] = []
    summary = rec_result.get("summary", {})
    bank_detection = rec_result.get("bank_column_detection", {})
    ledger_detection = rec_result.get("ledger_column_detection", {})
    test_results = rec_result.get("test_results", [])
    composite = rec_result.get("composite_score", {})

    matched = summary.get("matched_count", 0)
    bank_only = summary.get("bank_only_count", 0)
    ledger_only = summary.get("ledger_only_count", 0)
    total_txns = matched + bank_only + ledger_only

    # 0. COVER PAGE
    logo_path = find_logo()
    cover_metadata = ReportMetadata(
        title="Bank Reconciliation Memo",
        client_name=client_name or "",
        engagement_period=period_tested or "",
        fiscal_year_end=fiscal_year_end or "",
        source_document=filename,
        source_document_title=source_document_title or "",
        source_context_note=source_context_note or "",
        reference=reference,
    )
    build_cover_page(story, styles, cover_metadata, doc.width, logo_path)

    # ──────────────────────────────────────────────────────────────
    # I. SCOPE
    # ──────────────────────────────────────────────────────────────
    story.append(Paragraph("I. Scope", styles["MemoSection"]))
    story.append(LedgerRule(doc.width))

    scope_lines = []
    if source_document_title and filename:
        scope_lines.append(create_leader_dots("Source", f"{source_document_title} ({filename})"))
    elif source_document_title:
        scope_lines.append(create_leader_dots("Source", source_document_title))
    elif filename:
        scope_lines.append(create_leader_dots("Source", filename))
    if period_tested:
        scope_lines.append(create_leader_dots("Period Tested", period_tested))

    scope_lines.extend(
        [
            create_leader_dots("Total Transactions Analyzed", f"{total_txns:,}"),
            create_leader_dots("Bank Statement Transactions", f"{matched + bank_only:,}"),
            create_leader_dots("General Ledger Transactions", f"{matched + ledger_only:,}"),
        ]
    )

    bank_conf = bank_detection.get("overall_confidence", 0)
    ledger_conf = ledger_detection.get("overall_confidence", 0)
    if bank_conf or ledger_conf:
        scope_lines.extend(
            [
                create_leader_dots("Bank Column Detection Confidence", f"{bank_conf:.0%}"),
                create_leader_dots("Ledger Column Detection Confidence", f"{ledger_conf:.0%}"),
            ]
        )

    for line in scope_lines:
        story.append(Paragraph(line, styles["MemoLeader"]))
    story.append(Spacer(1, 4))

    # Scope statement (framework-aware)
    build_scope_statement(
        story,
        styles,
        doc.width,
        tool_domain="bank_reconciliation",
        framework=resolved_framework,
        domain_label="bank reconciliation analysis",
    )

    # Proof Summary (uses test_results for accurate counts)
    build_proof_summary_section(story, styles, doc.width, rec_result)

    # ──────────────────────────────────────────────────────────────
    # II. METHODOLOGY
    # ──────────────────────────────────────────────────────────────
    if test_results:
        _build_methodology_table(story, styles, doc.width, test_results)
    else:
        # Fallback: build from rec_tests
        story.append(Paragraph("II. Methodology", styles["MemoSection"]))
        story.append(LedgerRule(doc.width))
        story.append(
            Paragraph(
                "Automated reconciliation tests were applied to the bank statement "
                "and general ledger transaction data.",
                styles["MemoBody"],
            )
        )
        story.append(Spacer(1, 8))

    # Methodology statement
    build_methodology_statement(
        story,
        styles,
        doc.width,
        tool_domain="bank_reconciliation",
        framework=resolved_framework,
        domain_label="bank reconciliation analysis",
    )

    # ──────────────────────────────────────────────────────────────
    # III. RECONCILIATION RESULTS
    # ──────────────────────────────────────────────────────────────
    _build_reconciliation_results(story, styles, doc.width, summary, rec_result)

    # ──────────────────────────────────────────────────────────────
    # IV. OUTSTANDING ITEMS
    # ──────────────────────────────────────────────────────────────
    _build_outstanding_aging_tables(story, styles, doc.width, rec_result, summary)

    # ──────────────────────────────────────────────────────────────
    # V. RESULTS SUMMARY
    # ──────────────────────────────────────────────────────────────
    if composite:
        # Override section title to "V." (shared builder defaults to "III.")
        story.append(Paragraph("V. Results Summary", styles["MemoSection"]))
        story.append(LedgerRule(doc.width))

        risk_tier = str(composite.get("risk_tier", "low")).lower()
        base_tier_label, _ = RISK_TIER_DISPLAY.get(risk_tier, ("UNKNOWN", ClassicalColors.OBSIDIAN_500))
        tier_label = f"{base_tier_label} ({composite.get('score', 0):.0f}/100)"

        story.append(
            Paragraph(
                create_leader_dots("Composite Diagnostic Score", f"{composite.get('score', 0):.1f} / 100"),
                styles["MemoLeader"],
            )
        )
        story.append(
            Paragraph(
                create_leader_dots("Diagnostic Tier", tier_label),
                styles["MemoLeader"],
            )
        )
        story.append(Paragraph(RISK_SCALE_LEGEND, styles["MemoBodySmall"]))
        story.append(Spacer(1, 2))
        story.append(
            Paragraph(
                create_leader_dots("Total Items Flagged", f"{composite.get('total_flagged', 0):,}"),
                styles["MemoLeader"],
            )
        )

        sev = composite.get("flags_by_severity", {})
        story.append(
            Paragraph(
                create_leader_dots("High Severity Flags", str(sev.get("high", 0))),
                styles["MemoLeader"],
            )
        )
        story.append(
            Paragraph(
                create_leader_dots("Medium Severity Flags", str(sev.get("medium", 0))),
                styles["MemoLeader"],
            )
        )
        story.append(
            Paragraph(
                create_leader_dots("Low Severity Flags", str(sev.get("low", 0))),
                styles["MemoLeader"],
            )
        )
        story.append(Spacer(1, 6))

        # Results by test table (from rec_tests)
        rec_tests = rec_result.get("rec_tests", [])
        if rec_tests:
            cell_style_rt = styles["MemoTableCell"]
            results_data = [["Test", "Flagged", "Severity"]]
            for rt in rec_tests:
                results_data.append(
                    [
                        Paragraph(str(rt.get("test_name", "")), cell_style_rt),
                        Paragraph(str(rt.get("flagged_count", 0)), cell_style_rt),
                        Paragraph(rt.get("severity", "low").upper(), cell_style_rt),
                    ]
                )

            results_table = Table(
                results_data,
                colWidths=[3.5 * inch, 1.0 * inch, 1.5 * inch],
            )
            results_table.setStyle(TableStyle(ledger_table_style() + [("ALIGN", (1, 0), (-1, -1), "RIGHT")]))
            story.append(results_table)

        story.append(Spacer(1, 8))

    # ──────────────────────────────────────────────────────────────
    # VI. KEY FINDINGS
    # ──────────────────────────────────────────────────────────────
    _build_key_findings(story, styles, doc.width, rec_result, summary, composite)

    # ──────────────────────────────────────────────────────────────
    # VII. AUTHORITATIVE REFERENCES
    # ──────────────────────────────────────────────────────────────
    build_authoritative_reference_block(
        story,
        styles,
        doc.width,
        tool_domain="bank_reconciliation",
        framework=resolved_framework,
        domain_label="bank reconciliation analysis",
        section_label="VII.",
    )

    # ──────────────────────────────────────────────────────────────
    # VIII. CONCLUSION
    # ──────────────────────────────────────────────────────────────
    story.append(Paragraph("VIII. Conclusion", styles["MemoSection"]))
    story.append(LedgerRule(doc.width))

    risk_tier = str(composite.get("risk_tier", "low")).lower() if composite else "low"

    base_tier_label, _ = RISK_TIER_DISPLAY.get(risk_tier, ("LOW", ClassicalColors.SAGE))
    score_val = composite.get("score", 0) if composite else 0
    tier_label = f"{base_tier_label} ({score_val:.0f}/100)"

    # BUG-002: dict-based conclusion lookup (replaces if/elif chain)
    _bank_rec_suffixes = {
        "low": (
            "The reconciling difference is immaterial and the match rate is satisfactory. "
            "No items requiring further investigation were identified."
        ),
        "moderate": (
            "The reconciling difference and outstanding items should be reviewed "
            "to confirm they represent normal timing differences rather than errors or omissions."
        ),
        "elevated": (
            "The reconciling difference and/or outstanding item volume may indicate "
            "recording errors, omissions, or unusual transactions requiring detailed "
            "investigation per ISA 500 and ISA 505."
        ),
        "high": (
            "Significant reconciliation exceptions were identified. The reconciling "
            "difference and outstanding items require immediate investigation per "
            "ISA 500, ISA 505, and ISA 240."
        ),
    }

    suffix = _bank_rec_suffixes.get(risk_tier, _bank_rec_suffixes["low"])
    assessment = (
        f"Based on the automated reconciliation procedures applied, "
        f"the bank reconciliation returned {tier_label} flag density "
        f"(Composite Diagnostic Score: {score_val:.1f}/100) across the automated tests. "
        f"{suffix}"
    )

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
        domain="bank reconciliation analysis testing procedures",
        isa_reference="ISA 500 (Audit Evidence), ISA 505 (External Confirmations), and PCAOB AS 2310",
    )

    # Build PDF
    doc.build(story, onFirstPage=draw_page_footer, onLaterPages=draw_page_footer)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    log_secure_operation("bank_rec_memo_complete", f"Bank rec memo generated: {len(pdf_bytes)} bytes")
    return pdf_bytes
