"""
Revenue Testing Memo PDF Generator (Sprint 105, simplified Sprint 157,
enriched Sprint 501)

Config-driven wrapper around shared memo template.
Domain: ISA 240 / ISA 500 / PCAOB AS 2401 — presumed fraud risk in revenue recognition.

Sprint 501: Added high-severity detail tables (IMPROVEMENT-01), Benford/SSP notes
(IMPROVEMENT-02), revenue quality indicators (IMPROVEMENT-03), contra-revenue
ratio (IMPROVEMENT-04), dollar amounts in findings (BUG-03).
"""

import re
from collections import Counter
from decimal import Decimal
from typing import Any, Optional

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from pdf_generator import LedgerRule, create_leader_dots
from shared.drill_down import (
    build_drill_down_table,
    format_currency,
    safe_str_value,
)
from shared.memo_base import build_scope_section
from shared.memo_template import TestingMemoConfig, _roman, generate_testing_memo
from shared.parsing_helpers import safe_decimal
from shared.report_styles import ledger_table_style

REVENUE_TEST_DESCRIPTIONS = {
    "large_manual_entries": (
        "Flags manual revenue entries exceeding performance materiality threshold (ISA 240 fraud risk indicator)."
    ),
    "year_end_concentration": (
        "Flags revenue concentrated in the last days of the period, a common revenue recognition anomaly indicator."
    ),
    "round_revenue_amounts": (
        "Flags revenue entries with round dollar amounts that may indicate estimated "
        "or manually entered values rather than actual contracted amounts."
    ),
    "sign_anomalies": (
        "Flags debit balances in revenue accounts (normally credit), indicating "
        "potential mispostings or contra-revenue entries requiring investigation."
    ),
    "unclassified_entries": ("Flags revenue entries missing account classification (unmapped to chart of accounts)."),
    "zscore_outliers": (
        "Uses z-score analysis to identify revenue transaction amounts that are "
        "statistically unusual relative to the account\u2019s historical distribution."
    ),
    "trend_variance": (
        "Compares monthly revenue totals to the period\u2019s trend line and flags "
        "months where actual revenue deviates materially from the expected trend."
    ),
    "concentration_risk": ("Flags single accounts representing a disproportionate share of total revenue."),
    "cutoff_risk": (
        "Flags revenue entries recorded within a configurable window of the "
        "period-end date, where timing of recognition is most susceptible to "
        "error or manipulation (ISA 240 cut-off fraud risk indicator)."
    ),
    "benford_law": ("Applies Benford\u2019s Law first-digit analysis to revenue transaction amounts."),
    "duplicate_entries": (
        "Flags revenue entries with identical amount, date, and account \u2014 potential duplicate postings."
    ),
    "contra_revenue_anomalies": (
        "Flags elevated returns/allowances relative to gross revenue, a fraud risk indicator."
    ),
    # Contract-aware tests (ASC 606 / IFRS 15 — Sprint 352)
    "recognition_before_satisfaction": (
        "Flags entries where available contract data suggests a performance "
        "obligation under ASC 606 may not have been satisfied prior to the "
        "recognition date."
    ),
    "missing_obligation_linkage": (
        "Flags revenue entries that cannot be linked to a corresponding contract "
        "or purchase order in the source data, indicating possible "
        "unsubstantiated revenue."
    ),
    "modification_treatment_mismatch": (
        "Flags revenue entries that appear to reflect contract modifications "
        "without evidence of updated transaction price allocation per "
        "ASC 606-10-25-10."
    ),
    "allocation_inconsistency": (
        "Tests whether revenue allocated across multiple performance obligations "
        "reflects standalone selling prices per ASC 606-10-32-28."
    ),
}

_REVENUE_CONFIG = TestingMemoConfig(
    title="Revenue Recognition Testing Memo",
    ref_prefix="RVT",
    entry_label="Total Revenue Entries Tested",
    flagged_label="Total Revenue Entries Flagged",
    log_prefix="revenue_memo",
    domain="revenue recognition testing",
    test_descriptions=REVENUE_TEST_DESCRIPTIONS,
    methodology_intro=(
        "The following automated tests were applied to the revenue GL extract "
        "in accordance with professional auditing standards "
        "(ISA 240: Auditor's Responsibilities Relating to Fraud \u2014 "
        "presumed fraud risk in revenue recognition, "
        "ISA 500: Audit Evidence, PCAOB AS 2401: Consideration of Fraud). "
        "Where contract data columns were detected, additional contract-aware tests "
        "were applied per ASC 606 / IFRS 15 revenue recognition standards. "
        "Results represent revenue anomaly indicators, not fraud detection conclusions:"
    ),
    isa_reference="ISA 240 (presumed fraud risk in revenue recognition) and ISA 500",
    tool_domain="revenue_testing",
    risk_assessments={
        "low": (
            "Based on the automated revenue testing procedures applied, "
            "the revenue GL extract returned LOW flag density across the automated tests. "
            "No revenue recognition anomalies exceeding the configured thresholds were detected by the automated tests applied."
        ),
        "elevated": (
            "Based on the automated revenue testing procedures applied, "
            "the revenue GL extract returned ELEVATED flag density across the automated tests. "
            "Select flagged entries should be reviewed for proper revenue recognition treatment "
            "and supporting documentation."
        ),
        "moderate": (
            "Based on the automated revenue testing procedures applied, "
            "the revenue GL extract returned MODERATE flag density across the automated tests. "
            "Flagged entries warrant focused review as revenue recognition anomaly indicators, "
            "particularly year-end concentration and cut-off items."
        ),
        "high": (
            "Based on the automated revenue testing procedures applied, "
            "the revenue GL extract returned HIGH flag density across the automated tests. "
            "Significant revenue recognition anomaly indicators were detected that require "
            "detailed investigation. The engagement team should evaluate whether additional "
            "revenue procedures are appropriate per ISA 240 and PCAOB AS 2401."
        ),
    },
)

_MAX_DETAIL_ROWS = 20

# ─────────────────────────────────────────────────────────────────────
# DETAIL PROCEDURES & TABLE TITLES (IMPROVEMENT-01)
# ─────────────────────────────────────────────────────────────────────

_DETAIL_PROCEDURES = {
    "cutoff_risk": (
        "For each flagged entry, inspect the underlying contract or delivery "
        "documentation. Confirm that the performance obligation under ASC 606-10-25-23 "
        "was satisfied prior to the period end. Entries lacking supporting evidence "
        "of satisfaction before period end should be assessed for potential deferral to "
        "the subsequent period."
    ),
    "recognition_before_satisfaction": (
        "Obtain contract documentation for each entry. Identify the specific "
        "performance obligation and confirm its satisfaction date. Where satisfied "
        "after recognition date, assess whether a correcting entry is required under "
        "ASC 606-10-25."
    ),
    "sign_anomalies": (
        "Confirm whether each debit represents a legitimate contra-revenue "
        "entry (return, allowance) or a misposting requiring correction."
    ),
    "concentration_risk": (
        "Obtain the master contract with this customer. Assess whether "
        "concentration represents a going concern or business continuity risk "
        "requiring disclosure under ASC 275-10. Evaluate collectibility of "
        "related receivables."
    ),
}

_DETAIL_TABLE_TITLES = {
    "cutoff_risk": "Cut-Off Risk \u2014 Entry Detail",
    "recognition_before_satisfaction": "Recognition Timing \u2014 Entry Detail",
    "sign_anomalies": "Sign Anomalies \u2014 Entry Detail",
    "concentration_risk": "Concentration Risk \u2014 Customer Detail",
}


def _sum_flagged_amounts(flagged_entries: list[dict]) -> Decimal:
    """Sum absolute amounts from flagged entries."""
    total = Decimal("0")
    for fe in flagged_entries:
        entry = fe.get("entry", {})
        amt = entry.get("amount", 0)
        try:
            total += abs(safe_decimal(amt))
        except (TypeError, ValueError):
            pass
    return total


# ─────────────────────────────────────────────────────────────────────
# SCOPE ENRICHMENTS (IMPROVEMENT-03)
# ─────────────────────────────────────────────────────────────────────


def _build_revenue_quality_indicators(
    story: list,
    styles: dict,
    doc_width: float,
    result: dict[str, Any],
) -> None:
    """IMPROVEMENT-03: Revenue Quality Indicators in Scope section."""
    total_revenue = result.get("total_revenue", 0)
    if not total_revenue:
        # Attempt to compute from test results
        test_results = result.get("test_results", [])
        for tr in test_results:
            for fe in tr.get("flagged_entries", []):
                details = fe.get("details", {})
                if "total_revenue" in details:
                    total_revenue = details["total_revenue"]
                    break
                if "gross_revenue" in details:
                    total_revenue = details["gross_revenue"]
                    break
            if total_revenue:
                break
    if not total_revenue:
        return

    # Compute HIGH-risk aggregate
    test_results = result.get("test_results", [])
    high_risk_amount = 0.0
    cutoff_amount = 0.0
    december_amount = 0.0
    december_pct = 0.0
    concentration_pct = 0.0
    concentration_amount = 0.0

    for tr in test_results:
        severity = tr.get("severity", "")
        test_key = tr.get("test_key", "")

        if severity == "high" and tr.get("entries_flagged", 0) > 0:
            high_risk_amount += _sum_flagged_amounts(tr.get("flagged_entries", []))

        if test_key == "cutoff_risk" and tr.get("entries_flagged", 0) > 0:
            cutoff_amount = _sum_flagged_amounts(tr.get("flagged_entries", []))

        if test_key == "year_end_concentration" and tr.get("entries_flagged", 0) > 0:
            flagged = tr.get("flagged_entries", [])
            december_amount = _sum_flagged_amounts(flagged)
            if flagged:
                details = flagged[0].get("details", {})
                december_pct = details.get("concentration_pct", 0)

        if test_key == "concentration_risk" and tr.get("entries_flagged", 0) > 0:
            flagged = tr.get("flagged_entries", [])
            if flagged:
                details = flagged[0].get("details", {})
                concentration_pct = details.get("concentration_pct", 0)
                concentration_amount = total_revenue * concentration_pct

    story.append(Paragraph("Revenue Quality Indicators", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    lines = [
        create_leader_dots("Total Revenue (Period)", format_currency(total_revenue)),
    ]
    if high_risk_amount > 0:
        pct = high_risk_amount / total_revenue if total_revenue else 0
        lines.append(
            create_leader_dots(
                "High-Risk Entries (HIGH severity)",
                f"{format_currency(high_risk_amount)} ({pct:.1%} of total)",
            )
        )
    if december_amount > 0:
        lines.append(
            create_leader_dots(
                "December Revenue Concentration",
                f"{format_currency(december_amount)} ({december_pct:.1%} of total)"
                if december_pct
                else format_currency(december_amount),
            )
        )
    if cutoff_amount > 0:
        pct = cutoff_amount / total_revenue if total_revenue else 0
        lines.append(
            create_leader_dots(
                "Cut-Off Window Revenue",
                f"{format_currency(cutoff_amount)} ({pct:.1%} of total)",
            )
        )
    if concentration_pct > 0:
        lines.append(
            create_leader_dots(
                "Single-Customer Concentration",
                f"{concentration_pct:.0%} (~{format_currency(concentration_amount)})",
            )
        )

    for line in lines:
        story.append(Paragraph(line, styles["MemoLeader"]))
    story.append(Spacer(1, 8))


# ─────────────────────────────────────────────────────────────────────
# POST-RESULTS: BENFORD/SSP NOTES & CONTRA-REVENUE RATIO (IMP-02, 04)
# ─────────────────────────────────────────────────────────────────────


def _build_post_results_notes(
    story: list,
    styles: dict,
    doc_width: float,
    result: dict[str, Any],
    _counter: int,
) -> int:
    """IMPROVEMENT-02: Benford/SSP pass notes. IMPROVEMENT-04: Contra ratio."""
    test_results = result.get("test_results", [])

    for tr in test_results:
        test_key = tr.get("test_key", "")

        # IMPROVEMENT-02: Benford pass note
        if test_key == "benford_law" and tr.get("entries_flagged", 0) == 0:
            desc = tr.get("description", "")
            mad_match = re.search(r"MAD[=:]?\s*([\d.]+)", desc, re.IGNORECASE)
            if mad_match:
                mad = mad_match.group(1)
                note = (
                    f"Benford\u2019s Law analysis of revenue transaction amounts shows close "
                    f"conformity (MAD = {mad}), providing analytical support for the "
                    "completeness and non-fabrication of revenue amounts in the population "
                    "tested. No further procedures required for this test."
                )
            else:
                note = (
                    "Benford\u2019s Law analysis of revenue transaction amounts shows close "
                    "conformity, providing analytical support for the completeness and "
                    "non-fabrication of revenue amounts in the population tested."
                )
            story.append(Paragraph(f"<i>{note}</i>", styles["MemoBodySmall"]))
            story.append(Spacer(1, 4))

        # IMPROVEMENT-02: SSP Allocation pass note
        if test_key == "allocation_inconsistency" and tr.get("entries_flagged", 0) == 0:
            story.append(
                Paragraph(
                    "<i>SSP Allocation testing identified no anomalies in transaction price "
                    "allocation across performance obligations. No further procedures "
                    "required for this test.</i>",
                    styles["MemoBodySmall"],
                )
            )
            story.append(Spacer(1, 4))

    # IMPROVEMENT-04: Contra-revenue ratio
    for tr in test_results:
        if tr.get("test_key") == "contra_revenue_anomalies":
            flagged = tr.get("flagged_entries", [])
            # Extract ratio from details or flagged entries
            contra_total = 0.0
            gross_revenue = 0.0
            for fe in flagged:
                details = fe.get("details", {})
                if "contra_total" in details:
                    contra_total = details["contra_total"]
                if "gross_revenue" in details:
                    gross_revenue = details["gross_revenue"]
                break  # All entries share the same ratio

            # Also check result-level enrichment
            if not contra_total:
                contra_total = result.get("contra_revenue_total", 0)
            if not gross_revenue:
                gross_revenue = result.get("total_revenue", 0)

            if contra_total and gross_revenue:
                ratio = contra_total / gross_revenue
                if ratio < 0.02:
                    interp = "Within normal range \u2014 document as baseline for trend analysis."
                elif ratio <= 0.05:
                    interp = "Warrants inquiry into the nature of returns and allowances."
                else:
                    interp = (
                        "Elevated \u2014 assess for channel stuffing reversal or aggressive prior-period recognition."
                    )
                story.append(
                    Paragraph(
                        f"<i>Contra-Revenue Ratio: {format_currency(contra_total)} / "
                        f"{format_currency(gross_revenue)} gross revenue = {ratio:.1%}. "
                        f"{interp}</i>",
                        styles["MemoBodySmall"],
                    )
                )
                story.append(Spacer(1, 4))
            break

    return _counter


# ─────────────────────────────────────────────────────────────────────
# HIGH SEVERITY DETAIL TABLES (IMPROVEMENT-01)
# ─────────────────────────────────────────────────────────────────────


def _build_cutoff_table(
    story: list,
    styles: dict,
    flagged_entries: list[dict],
) -> None:
    """Render Cut-Off Risk entry detail table, sorted by date descending."""
    table_data = [["Entry Ref", "Date", "Account", "Amount", "Customer", "Days to Year-End"]]

    # Sort by date descending
    sorted_entries = sorted(
        flagged_entries,
        key=lambda fe: fe.get("entry", {}).get("date", "") or "",
        reverse=True,
    )

    for fe in sorted_entries[:_MAX_DETAIL_ROWS]:
        entry = fe.get("entry", {})
        details = fe.get("details") or {}
        # Compute days from boundary
        days_from = details.get("days_from_boundary")
        if days_from is None:
            entry_date_str = details.get("entry_date") or entry.get("date")
            period_end_str = details.get("period_end")
            if entry_date_str and period_end_str:
                try:
                    from datetime import datetime

                    ed = datetime.strptime(str(entry_date_str)[:10], "%Y-%m-%d")
                    pe = datetime.strptime(str(period_end_str)[:10], "%Y-%m-%d")
                    days_from = abs((ed - pe).days)
                except (ValueError, TypeError):
                    days_from = None

        customer = safe_str_value(entry.get("description"), "")[:20]
        # Display absolute amount — sign convention not meaningful in cut-off detail context
        display_amount = abs(entry.get("amount", 0)) if isinstance(entry.get("amount"), (int, float)) else 0
        table_data.append(
            [
                Paragraph(safe_str_value(entry.get("reference")), styles["MemoTableCell"]),
                Paragraph(safe_str_value(entry.get("date")), styles["MemoTableCell"]),
                Paragraph(safe_str_value(entry.get("account_name"), "")[:20], styles["MemoTableCell"]),
                Paragraph(format_currency(display_amount), styles["MemoTableCell"]),
                Paragraph(customer, styles["MemoTableCell"]),
                Paragraph(str(days_from) if days_from is not None else "\u2014", styles["MemoTableCell"]),
            ]
        )

    style_cmds = ledger_table_style() + [
        ("ALIGN", (3, 0), (3, -1), "RIGHT"),
        ("ALIGN", (5, 0), (5, -1), "RIGHT"),
    ]
    table = Table(
        table_data,
        colWidths=[0.9 * inch, 0.8 * inch, 1.2 * inch, 1.0 * inch, 1.3 * inch, 1.0 * inch],
        repeatRows=1,
    )
    table.setStyle(TableStyle(style_cmds))
    story.append(table)

    if len(flagged_entries) > _MAX_DETAIL_ROWS:
        story.append(
            Paragraph(
                f"<i>Showing {_MAX_DETAIL_ROWS} of {len(flagged_entries)} flagged entries.</i>",
                styles["MemoBodySmall"],
            )
        )


def _build_recognition_table(
    story: list,
    styles: dict,
    flagged_entries: list[dict],
) -> None:
    """Render Recognition Timing entry detail table."""
    table_data = [["Entry Ref", "Date", "Account", "Amount", "Obligation Concern"]]

    for fe in flagged_entries[:_MAX_DETAIL_ROWS]:
        entry = fe.get("entry", {})
        concern = fe.get("issue", "")
        table_data.append(
            [
                Paragraph(safe_str_value(entry.get("reference")), styles["MemoTableCell"]),
                Paragraph(safe_str_value(entry.get("date")), styles["MemoTableCell"]),
                Paragraph(safe_str_value(entry.get("account_name"), "")[:20], styles["MemoTableCell"]),
                Paragraph(format_currency(entry.get("amount", 0)), styles["MemoTableCell"]),
                Paragraph(concern[:60] if concern else "\u2014", styles["MemoTableCell"]),
            ]
        )

    style_cmds = ledger_table_style() + [("ALIGN", (3, 0), (3, -1), "RIGHT")]
    table = Table(
        table_data,
        colWidths=[0.9 * inch, 0.8 * inch, 1.0 * inch, 1.0 * inch, 2.5 * inch],
        repeatRows=1,
    )
    table.setStyle(TableStyle(style_cmds))
    story.append(table)

    if len(flagged_entries) > _MAX_DETAIL_ROWS:
        story.append(
            Paragraph(
                f"<i>Showing {_MAX_DETAIL_ROWS} of {len(flagged_entries)} flagged entries.</i>",
                styles["MemoBodySmall"],
            )
        )


def _build_sign_anomalies_table(
    story: list,
    styles: dict,
    flagged_entries: list[dict],
) -> None:
    """Render Sign Anomalies entry detail table."""
    table_data = [["Entry Ref", "Date", "Account", "Debit Amount", "Expected Normal", "Description"]]

    for fe in flagged_entries[:_MAX_DETAIL_ROWS]:
        entry = fe.get("entry", {})
        table_data.append(
            [
                Paragraph(safe_str_value(entry.get("reference")), styles["MemoTableCell"]),
                Paragraph(safe_str_value(entry.get("date")), styles["MemoTableCell"]),
                Paragraph(safe_str_value(entry.get("account_name"), "")[:18], styles["MemoTableCell"]),
                Paragraph(format_currency(entry.get("amount", 0)), styles["MemoTableCell"]),
                Paragraph("Credit", styles["MemoTableCell"]),
                Paragraph(safe_str_value(entry.get("description"), "")[:25], styles["MemoTableCell"]),
            ]
        )

    style_cmds = ledger_table_style() + [("ALIGN", (3, 0), (3, -1), "RIGHT")]
    table = Table(
        table_data,
        colWidths=[0.8 * inch, 0.7 * inch, 1.1 * inch, 1.0 * inch, 0.9 * inch, 1.7 * inch],
        repeatRows=1,
    )
    table.setStyle(TableStyle(style_cmds))
    story.append(table)


def _build_concentration_table(
    story: list,
    styles: dict,
    flagged_entries: list[dict],
) -> None:
    """Render Concentration Risk customer detail table."""
    # Group by account to show one row per concentrated customer/account
    seen_accounts: dict[str, dict] = {}
    for fe in flagged_entries:
        entry = fe.get("entry", {})
        details = fe.get("details", {})
        acct = details.get("account", entry.get("account_name", "Unknown"))
        if acct not in seen_accounts:
            seen_accounts[acct] = {
                "total": details.get("account_total", abs(entry.get("amount", 0))),
                "pct": details.get("concentration_pct", 0),
                "accounts": entry.get("account_name", ""),
            }

    table_data = [["Customer / Account", "Total Revenue", "% of Total Revenue", "Revenue Accounts"]]

    for acct, info in list(seen_accounts.items())[:_MAX_DETAIL_ROWS]:
        table_data.append(
            [
                Paragraph(acct, styles["MemoTableCell"]),
                Paragraph(format_currency(info["total"]), styles["MemoTableCell"]),
                Paragraph(f"{info['pct']:.0%}" if info["pct"] else "\u2014", styles["MemoTableCell"]),
                Paragraph(info["accounts"][:20] if info["accounts"] else "\u2014", styles["MemoTableCell"]),
            ]
        )

    style_cmds = ledger_table_style() + [
        ("ALIGN", (1, 0), (2, -1), "RIGHT"),
    ]
    table = Table(
        table_data,
        colWidths=[2.0 * inch, 1.5 * inch, 1.5 * inch, 1.2 * inch],
        repeatRows=1,
    )
    table.setStyle(TableStyle(style_cmds))
    story.append(table)


_DETAIL_TABLE_BUILDERS = {
    "cutoff_risk": _build_cutoff_table,
    "recognition_before_satisfaction": _build_recognition_table,
    "sign_anomalies": _build_sign_anomalies_table,
    "concentration_risk": _build_concentration_table,
}


def _build_high_severity_detail(
    story: list,
    styles: dict,
    doc_width: float,
    result: dict[str, Any],
    section_counter: int,
) -> int:
    """IMPROVEMENT-01: Build High Severity Entry Detail section.

    Renders one table per HIGH severity test with flagged records.
    Also includes preparer concentration analysis (DRILL-06).
    """
    test_results = result.get("test_results", [])

    high_tests = [
        tr
        for tr in test_results
        if tr.get("severity") == "high" and tr.get("entries_flagged", 0) > 0 and tr.get("flagged_entries")
    ]

    has_detail = False

    if high_tests:
        label = _roman(section_counter)
        story.append(Paragraph(f"{label}. High Severity Entry Detail", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))
        has_detail = True

        for tr in high_tests:
            test_key = tr.get("test_key", "")
            flagged = tr.get("flagged_entries", [])
            count = tr.get("entries_flagged", 0)

            title = _DETAIL_TABLE_TITLES.get(
                test_key,
                f"{tr.get('test_name', '')} \u2014 Entry Detail",
            )
            story.append(Paragraph(f"<b>{title} ({count} items)</b>", styles["MemoBody"]))
            story.append(Spacer(1, 4))

            builder = _DETAIL_TABLE_BUILDERS.get(test_key)
            if builder:
                builder(story, styles, flagged)
            else:
                # BUG-007 fix: generic detail table for tests without a dedicated builder
                gen_data = [
                    [
                        Paragraph("Reference", styles["MemoTableHeader"]),
                        Paragraph("Date", styles["MemoTableHeader"]),
                        Paragraph("Issue", styles["MemoTableHeader"]),
                        Paragraph("Amount", styles["MemoTableHeader"]),
                    ]
                ]
                for fe in flagged[:_MAX_DETAIL_ROWS]:
                    entry = fe.get("entry", {})
                    gen_data.append(
                        [
                            Paragraph(safe_str_value(entry.get("reference")), styles["MemoTableCell"]),
                            Paragraph(safe_str_value(entry.get("date")), styles["MemoTableCell"]),
                            Paragraph(str(fe.get("issue", "")), styles["MemoTableCell"]),
                            Paragraph(format_currency(entry.get("amount", 0)), styles["MemoTableCell"]),
                        ]
                    )
                gen_table = Table(
                    gen_data,
                    colWidths=[1.3 * inch, 1.0 * inch, 2.5 * inch, 1.2 * inch],
                    repeatRows=1,
                )
                gen_table.setStyle(TableStyle(ledger_table_style() + [("ALIGN", (3, 0), (3, -1), "RIGHT")]))
                story.append(gen_table)

            procedure = _DETAIL_PROCEDURES.get(test_key, "")
            if procedure:
                story.append(Paragraph(f"<i>{procedure}</i>", styles["MemoBodySmall"]))

            story.append(Spacer(1, 8))

    # DRILL-06: Preparer concentration
    preparer_flagged: Counter[str] = Counter()
    total_flagged_with_preparer = 0
    total_flagged_count = 0

    for tr in test_results:
        for fe in tr.get("flagged_entries", []):
            total_flagged_count += 1
            posted_by = (fe.get("entry") or {}).get("posted_by")
            if posted_by:
                total_flagged_with_preparer += 1
                preparer_flagged[posted_by] += 1

    if total_flagged_count > 0 and total_flagged_with_preparer / total_flagged_count >= 0.6:
        if not has_detail:
            label = _roman(section_counter)
            story.append(Paragraph(f"{label}. High Severity Entry Detail", styles["MemoSection"]))
            story.append(LedgerRule(doc_width))
            has_detail = True

        story.append(
            Paragraph(
                f"{total_flagged_with_preparer} of {total_flagged_count} flagged entries "
                f"({total_flagged_with_preparer / total_flagged_count:.0%}) include preparer identification:",
                styles["MemoBody"],
            )
        )
        story.append(Spacer(1, 4))

        rows = []
        for name, flagged_count in preparer_flagged.most_common(5):
            flag_rate = flagged_count / total_flagged_with_preparer if total_flagged_with_preparer > 0 else 0
            rows.append([name, str(flagged_count), f"{flag_rate:.1%}"])

        build_drill_down_table(
            story,
            styles,
            doc_width,
            title="",
            headers=["Preparer", "Flagged Entries", "% of Flagged"],
            rows=rows,
            col_widths=[3.0 * inch, 1.5 * inch, 2.1 * inch],
            right_align_cols=[1, 2],
        )

    if has_detail:
        section_counter += 1

    return section_counter


# ─────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────────


def generate_revenue_testing_memo(
    revenue_result: dict[str, Any],
    filename: str = "revenue_testing",
    client_name: Optional[str] = None,
    period_tested: Optional[str] = None,
    prepared_by: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    workpaper_date: Optional[str] = None,
    source_document_title: Optional[str] = None,
    source_context_note: Optional[str] = None,
    fiscal_year_end: Optional[str] = None,
    include_signoff: bool = False,
) -> bytes:
    """Generate a PDF testing memo for revenue testing results."""

    def _revenue_scope(story, styles, doc_width, composite, data_quality, period_tested_arg):
        build_scope_section(
            story,
            styles,
            doc_width,
            composite,
            data_quality,
            entry_label="Total Revenue Entries Tested",
            period_tested=period_tested_arg,
            source_document=filename,
            source_document_title=source_document_title,
        )
        _build_revenue_quality_indicators(story, styles, doc_width, revenue_result)

    return generate_testing_memo(
        revenue_result,
        _REVENUE_CONFIG,
        filename=filename,
        client_name=client_name,
        period_tested=period_tested,
        prepared_by=prepared_by,
        reviewed_by=reviewed_by,
        workpaper_date=workpaper_date,
        source_document_title=source_document_title,
        source_context_note=source_context_note,
        fiscal_year_end=fiscal_year_end,
        build_scope=_revenue_scope,
        build_post_results=_build_post_results_notes,
        build_extra_sections=_build_high_severity_detail,
        include_signoff=include_signoff,
    )
