"""
Payroll Testing Memo PDF Generator (Sprint 88, refactored Sprint 90, simplified Sprint 157,
enriched Sprint 500)

Config-driven wrapper around shared memo template.
Domain: ISA 240 / ISA 500 / PCAOB AS 2401.

Sprint 500: Added high-severity detail tables (BUG-02), GL reconciliation (IMP-01),
headcount roll-forward (IMP-02), Benford interpretation (IMP-03), department summary
(IMP-04), overpayment quantification (IMP-05).
"""

import re
from decimal import Decimal
from typing import Any, Optional

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from pdf_generator import ClassicalColors, LedgerRule, create_leader_dots
from shared.drill_down import format_currency
from shared.memo_base import build_scope_section
from shared.memo_template import TestingMemoConfig, _roman, generate_testing_memo
from shared.parsing_helpers import safe_decimal
from shared.report_styles import ledger_table_style

PAYROLL_TEST_DESCRIPTIONS = {
    "PR-T1": "Identifies employee IDs associated with multiple different names, indicating possible data integrity issues.",
    "PR-T2": "Flags payroll entries with blank employee names, zero gross pay, or missing pay dates.",
    "PR-T3": "Flags round-dollar pay amounts ($100K, $50K, $25K, $10K multiples) that may indicate estimates.",
    "PR-T4": "Flags payments made after the employee's recorded termination date.",
    "PR-T5": "Detects gaps in sequential payroll check numbering that may indicate voided or missing checks.",
    "PR-T6": "Uses z-score analysis to identify statistically unusual pay amounts per department.",
    "PR-T7": "Flags employees with irregular pay spacing compared to the population cadence.",
    "PR-T8": "Applies Benford's Law first-digit analysis to gross pay amounts.",
    "PR-T9": "Flags employees with ghost employee indicators: no department, single entry, boundary-month-only payments.",
    "PR-T10": "Flags employees sharing the same bank account or similar addresses.",
    "PR-T11": "Flags employees sharing the same tax identification number.",
}

_PAYROLL_CONFIG = TestingMemoConfig(
    title="Payroll &amp; Employee Testing Memo",
    ref_prefix="PRT",
    entry_label="Total Payroll Entries Tested",
    flagged_label="Total Entries Flagged",
    log_prefix="payroll_memo",
    domain="payroll testing",
    test_descriptions=PAYROLL_TEST_DESCRIPTIONS,
    methodology_intro=(
        "The following automated tests were applied to the payroll register "
        "in accordance with professional auditing standards "
        "(ISA 240: Auditor's Responsibilities Relating to Fraud, "
        "ISA 500: Audit Evidence, PCAOB AS 2401: Consideration of Fraud):"
    ),
    risk_assessments={
        "low": (
            "Based on the automated payroll testing procedures applied, "
            "the payroll register returned LOW flag density across the automated tests. "
            "No anomalies exceeding the configured thresholds were detected by the automated tests applied."
        ),
        "elevated": (
            "Based on the automated payroll testing procedures applied, "
            "the payroll register returned ELEVATED flag density across the automated tests. "
            "Select flagged entries should be reviewed for proper authorization and documentation."
        ),
        "moderate": (
            "Based on the automated payroll testing procedures applied, "
            "the payroll register returned MODERATE flag density across the automated tests. "
            "Flagged entries warrant focused review, particularly ghost employee indicators."
        ),
        "high": (
            "Based on the automated payroll testing procedures applied, "
            "the payroll register returned HIGH flag density across the automated tests. "
            "Significant anomalies were detected that require detailed investigation. "
            "The engagement team should evaluate whether additional payroll procedures are appropriate."
        ),
    },
    isa_reference="ISA 240 (Fraud), ISA 500 (Audit Evidence), and PCAOB AS 2401",
    tool_domain="payroll_testing",
)

_MAX_DETAIL_ROWS = 20


def _format_payroll_finding(finding: Any) -> str:
    """Format payroll finding — handles both dict and string findings.

    Sprint 500: Includes gross_pay amount if available (IMPROVEMENT-05).
    """
    if isinstance(finding, dict):
        employee = finding.get("employee", "Unknown")
        issue = finding.get("issue", "")
        amount = finding.get("amount")
        if amount and amount > 0:
            return f"{employee} \u2014 {issue} (${amount:,.2f})"
        return f"{employee} \u2014 {issue}"
    return str(finding)


# ─────────────────────────────────────────────────────────────────────
# SCOPE ENRICHMENTS (IMPROVEMENT-01, 02, 04)
# ─────────────────────────────────────────────────────────────────────


def _build_gl_reconciliation(
    story: list,
    styles: dict,
    doc_width: float,
    result: dict[str, Any],
) -> None:
    """IMPROVEMENT-01: Payroll Register-to-GL Reconciliation subsection."""
    register_total = result.get("payroll_register_total", 0)
    if not register_total:
        return

    story.append(Paragraph("Payroll Register-to-GL Reconciliation", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    story.append(
        Paragraph(
            create_leader_dots("Payroll Register Total (computed)", format_currency(register_total)),
            styles["MemoLeader"],
        )
    )

    gl_balance = result.get("gl_salaries_wages")
    if gl_balance is not None:
        story.append(
            Paragraph(
                create_leader_dots("GL \u2014 Salaries &amp; Wages (Trial Balance)", format_currency(gl_balance)),
                styles["MemoLeader"],
            )
        )
        variance = register_total - gl_balance
        story.append(
            Paragraph(
                create_leader_dots("Variance", format_currency(variance)),
                styles["MemoLeader"],
            )
        )
        if abs(variance) < 0.01:
            story.append(
                Paragraph(
                    "\u2713 Reconciled \u2014 Payroll register agrees to GL balance.",
                    styles["MemoBody"],
                )
            )
        else:
            story.append(
                Paragraph(
                    f"\u26a0 Unreconciled difference of {format_currency(abs(variance))} requires investigation. "
                    "Confirm whether the variance represents payroll accruals, timing differences, "
                    "or recording errors.",
                    styles["MemoBody"],
                )
            )
    else:
        story.append(
            Paragraph(
                create_leader_dots(
                    "GL \u2014 Salaries &amp; Wages (Trial Balance)",
                    "[TB not uploaded \u2014 upload trial balance to complete reconciliation]",
                ),
                styles["MemoLeader"],
            )
        )

    story.append(Spacer(1, 8))


def _build_headcount_rollforward(
    story: list,
    styles: dict,
    doc_width: float,
    result: dict[str, Any],
) -> None:
    """IMPROVEMENT-02: Headcount Roll-Forward subsection."""
    hc = result.get("headcount_rollforward")
    if not hc:
        col_det = result.get("column_detection", {})
        if not col_det.get("has_hire_dates") or not col_det.get("has_term_dates"):
            story.append(Paragraph("Headcount Roll-Forward", styles["MemoSection"]))
            story.append(LedgerRule(doc_width))
            story.append(
                Paragraph(
                    "<i>Headcount roll-forward requires hire date and termination date fields "
                    "\u2014 not detected in uploaded payroll register.</i>",
                    styles["MemoBodySmall"],
                )
            )
            story.append(Spacer(1, 8))
        return

    story.append(Paragraph("Headcount Roll-Forward", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    ps = hc.get("period_start", "")
    pe = hc.get("period_end", "")

    story.append(
        Paragraph(
            create_leader_dots(f"Employees Active \u2014 Beginning of Period ({ps})", str(hc["beginning_headcount"])),
            styles["MemoLeader"],
        )
    )
    story.append(
        Paragraph(
            create_leader_dots("New Hires During Period", f"+ {hc['new_hires']}"),
            styles["MemoLeader"],
        )
    )
    story.append(
        Paragraph(
            create_leader_dots("Terminations During Period", f"- {hc['terminations']}"),
            styles["MemoLeader"],
        )
    )
    story.append(
        Paragraph(
            create_leader_dots(f"Employees Active \u2014 End of Period ({pe})", f"= {hc['computed_ending']}"),
            styles["MemoLeader"],
        )
    )
    story.append(
        Paragraph(
            create_leader_dots("Employees in Final Pay Period of Register", str(hc["final_period_headcount"])),
            styles["MemoLeader"],
        )
    )
    variance = hc.get("variance", 0)
    story.append(
        Paragraph(
            create_leader_dots("Variance", str(variance)),
            styles["MemoLeader"],
        )
    )

    if variance != 0:
        story.append(Spacer(1, 2))
        story.append(
            Paragraph(
                f"<i>Note: {abs(variance)}-employee variance between computed ending headcount "
                f"and final pay period register count under investigation \u2014 see Ghost "
                "Employee Indicators finding.</i>",
                styles["MemoBodySmall"],
            )
        )

    story.append(Spacer(1, 8))


def _build_department_summary(
    story: list,
    styles: dict,
    doc_width: float,
    result: dict[str, Any],
) -> None:
    """IMPROVEMENT-04: Salary Distribution by Department table."""
    dept_data = result.get("department_summary", [])
    if not dept_data:
        return

    story.append(Paragraph("Salary Distribution by Department", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    table_data = [["Department", "Employee Count", "Total Gross Pay", "% of Total Payroll"]]
    total_count = 0
    total_pay = 0.0
    high_concentration = None

    for dept in dept_data:
        count = dept["employee_count"]
        pay = dept["total_gross_pay"]
        pct = dept["pct_of_total"]
        total_count += count
        total_pay += pay
        if pct > 40:
            high_concentration = (dept["department"], pct)
        table_data.append(
            [
                Paragraph(dept["department"], styles["MemoTableCell"]),
                Paragraph(str(count), styles["MemoTableCell"]),
                Paragraph(format_currency(pay), styles["MemoTableCell"]),
                Paragraph(f"{pct:.1f}%", styles["MemoTableCell"]),
            ]
        )

    table_data.append(
        [
            Paragraph("<b>Total</b>", styles["MemoTableCell"]),
            Paragraph(f"<b>{total_count}</b>", styles["MemoTableCell"]),
            Paragraph(f"<b>{format_currency(total_pay)}</b>", styles["MemoTableCell"]),
            Paragraph("<b>100%</b>", styles["MemoTableCell"]),
        ]
    )

    dept_table = Table(
        table_data,
        colWidths=[2.5 * inch, 1.2 * inch, 1.5 * inch, 1.4 * inch],
        repeatRows=1,
    )
    style_cmds = ledger_table_style() + [
        ("LINEABOVE", (0, -1), (-1, -1), 1, ClassicalColors.OBSIDIAN_DEEP),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
    ]
    dept_table.setStyle(TableStyle(style_cmds))
    story.append(dept_table)

    # Reconciliation note: compare department table total to headcount roll-forward
    hc = result.get("headcount_rollforward")
    if hc:
        ending_headcount = hc.get("computed_ending", 0)
        if total_count != ending_headcount:
            diff = total_count - ending_headcount
            direction = "exceeds" if diff > 0 else "is below"
            story.append(
                Paragraph(
                    f"<i>Note: Department distribution total ({total_count}) {direction} "
                    f"roll-forward ending headcount ({ending_headcount}) by {abs(diff)} employee(s). "
                    "This variance may reflect terminated employees not yet removed from departmental "
                    "assignments, contractors included in department rosters, or data timing differences "
                    "between the payroll register and HR system.</i>",
                    styles["MemoBodySmall"],
                )
            )

    if high_concentration:
        name, pct = high_concentration
        story.append(
            Paragraph(
                f"<i>Single department ({name}) represents {pct:.1f}% of total payroll. "
                "Assess whether this concentration is consistent with the entity\u2019s "
                "operating structure.</i>",
                styles["MemoBodySmall"],
            )
        )

    story.append(Spacer(1, 8))


# ─────────────────────────────────────────────────────────────────────
# POST-RESULTS: BENFORD INTERPRETATION (IMPROVEMENT-03)
# ─────────────────────────────────────────────────────────────────────


def _build_benford_note(
    story: list,
    styles: dict,
    doc_width: float,
    result: dict[str, Any],
    _counter: int,
) -> int:
    """IMPROVEMENT-03: Benford's Law positive interpretation note."""
    test_results = result.get("test_results", [])
    for tr in test_results:
        if tr.get("test_key") == "PR-T8" and tr.get("entries_flagged", 0) == 0:
            desc = tr.get("description", "")
            mad_match = re.search(r"MAD[=:]?\s*([\d.]+)", desc, re.IGNORECASE)
            if mad_match:
                mad = mad_match.group(1)
                story.append(
                    Paragraph(
                        f"<i>Benford\u2019s Law analysis of gross pay amounts shows close conformity "
                        f"(MAD = {mad}). This provides analytical support for the completeness and "
                        "non-fabrication of gross pay amounts in the population. No further procedures "
                        "required for this test.</i>",
                        styles["MemoBodySmall"],
                    )
                )
                story.append(Spacer(1, 4))
            break
    return _counter


# ─────────────────────────────────────────────────────────────────────
# HIGH SEVERITY DETAIL TABLES (BUG-02)
# ─────────────────────────────────────────────────────────────────────

_DETAIL_PROCEDURES = {
    "PR-T4": (
        "Obtain HR termination documentation for the affected employee(s). Confirm whether "
        "payments were authorized severance, a system processing lag, or unauthorized "
        "disbursements. Calculate total overpayment amount and confirm whether recovery has "
        "been initiated."
    ),
    "PR-T9": (
        "Trace the flagged employee(s) to HR personnel file. Confirm physical existence "
        "of employee and legitimacy of the payment. Physical verification of employee existence, "
        "if warranted, must be performed by the engagement team directly and not delegated "
        "to management."
    ),
    "PR-T10": (
        "Obtain bank account authorization forms for all affected employees. Confirm whether "
        "the shared account represents a legitimate family arrangement with documented "
        "authorization, or an unauthorized diversion of payroll funds. Verify all employees "
        "are on the current active headcount."
    ),
    "PR-T1": (
        "Obtain HR records for the affected employee ID(s). Confirm whether the name change "
        "represents a legal name change with documentation, a data entry correction, or potential "
        "identity substitution. Review all pay transactions under this ID for the full period."
    ),
}

_DETAIL_TABLE_TITLES = {
    "PR-T4": "Pay After Termination \u2014 Employee Detail",
    "PR-T9": "Ghost Employee Indicators \u2014 Employee Detail",
    "PR-T10": "Duplicate Bank Accounts \u2014 Employee Detail",
    "PR-T1": "Duplicate Employee IDs \u2014 Employee Detail",
}


def _build_pay_after_term_table(
    story: list,
    styles: dict,
    flagged_entries: list[dict],
) -> None:
    """Render Pay After Termination detail table."""
    total_overpayment = Decimal("0")
    table_data = [["Employee ID", "Employee Name", "Termination Date", "Payment Date", "Gross Pay"]]

    for fe in flagged_entries[:_MAX_DETAIL_ROWS]:
        entry = fe.get("entry", {})
        table_data.append(
            [
                Paragraph(entry.get("employee_id", ""), styles["MemoTableCell"]),
                Paragraph(entry.get("employee_name", ""), styles["MemoTableCell"]),
                Paragraph(str(entry.get("term_date", "") or ""), styles["MemoTableCell"]),
                Paragraph(str(entry.get("pay_date", "") or ""), styles["MemoTableCell"]),
                Paragraph(format_currency(entry.get("gross_pay", 0)), styles["MemoTableCell"]),
            ]
        )
        total_overpayment += safe_decimal(entry.get("gross_pay", 0))

    style_cmds = ledger_table_style() + [("ALIGN", (4, 0), (4, -1), "RIGHT")]
    table = Table(
        table_data,
        colWidths=[1.0 * inch, 1.5 * inch, 1.2 * inch, 1.2 * inch, 1.2 * inch],
        repeatRows=1,
    )
    table.setStyle(TableStyle(style_cmds))
    story.append(table)

    if total_overpayment > 0:
        story.append(
            Paragraph(
                f"Total post-termination payments: {format_currency(total_overpayment)}",
                styles["MemoBody"],
            )
        )

    if len(flagged_entries) > _MAX_DETAIL_ROWS:
        story.append(
            Paragraph(
                f"<i>Showing {_MAX_DETAIL_ROWS} of {len(flagged_entries)} flagged entries.</i>",
                styles["MemoBodySmall"],
            )
        )


def _build_ghost_employee_table(
    story: list,
    styles: dict,
    flagged_entries: list[dict],
) -> None:
    """Render Ghost Employee Indicators detail table."""
    table_data = [["Employee ID", "Name", "Pay Date", "Gross Pay", "No Dept", "Single Entry", "Boundary Mo."]]

    for fe in flagged_entries[:_MAX_DETAIL_ROWS]:
        entry = fe.get("entry", {})
        details = fe.get("details", {})
        indicators = details.get("indicators", [])
        ind_lower = " ".join(indicators).lower()
        table_data.append(
            [
                Paragraph(entry.get("employee_id", ""), styles["MemoTableCell"]),
                Paragraph(entry.get("employee_name", ""), styles["MemoTableCell"]),
                Paragraph(str(entry.get("pay_date", "") or ""), styles["MemoTableCell"]),
                Paragraph(format_currency(entry.get("gross_pay", 0)), styles["MemoTableCell"]),
                Paragraph("\u2713" if "department" in ind_lower else "\u2014", styles["MemoTableCell"]),
                Paragraph("\u2713" if "single" in ind_lower else "\u2014", styles["MemoTableCell"]),
                Paragraph(
                    "\u2713" if "boundary" in ind_lower or "first/last" in ind_lower else "\u2014",
                    styles["MemoTableCell"],
                ),
            ]
        )

    style_cmds = ledger_table_style() + [
        ("ALIGN", (3, 0), (3, -1), "RIGHT"),
        ("ALIGN", (4, 0), (-1, -1), "CENTER"),
    ]
    table = Table(
        table_data,
        colWidths=[0.9 * inch, 1.0 * inch, 0.9 * inch, 0.9 * inch, 0.7 * inch, 0.8 * inch, 1.0 * inch],
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


def _build_duplicate_bank_table(
    story: list,
    styles: dict,
    flagged_entries: list[dict],
) -> None:
    """Render Duplicate Bank Accounts detail table."""
    table_data = [["Employee ID", "Employee Name", "Department", "Bank Account (last 4)"]]

    for fe in flagged_entries[:_MAX_DETAIL_ROWS]:
        entry = fe.get("entry", {})
        details = fe.get("details", {})
        acct_masked = details.get("account_masked", "")
        last4 = acct_masked[-4:] if len(acct_masked) >= 4 else acct_masked
        name = entry.get("employee_name", "")
        if not name:
            name = "[Employee name not available in payroll source data \u2014 obtain from HR master file]"
        table_data.append(
            [
                Paragraph(entry.get("employee_id", ""), styles["MemoTableCell"]),
                Paragraph(name, styles["MemoTableCell"]),
                Paragraph(entry.get("department", "") or "", styles["MemoTableCell"]),
                Paragraph(last4, styles["MemoTableCell"]),
            ]
        )

    table = Table(
        table_data,
        colWidths=[1.2 * inch, 2.0 * inch, 1.5 * inch, 1.5 * inch],
        repeatRows=1,
    )
    table.setStyle(TableStyle(ledger_table_style()))
    story.append(table)

    if len(flagged_entries) > _MAX_DETAIL_ROWS:
        story.append(
            Paragraph(
                f"<i>Showing {_MAX_DETAIL_ROWS} of {len(flagged_entries)} flagged entries.</i>",
                styles["MemoBodySmall"],
            )
        )


def _build_duplicate_id_table(
    story: list,
    styles: dict,
    flagged_entries: list[dict],
) -> None:
    """Render Duplicate Employee IDs detail table."""
    table_data = [["Employee ID", "Names Associated", "Entry Count"]]

    # Group by employee_id to show name variations
    id_groups: dict[str, dict] = {}
    for fe in flagged_entries:
        entry = fe.get("entry", {})
        details = fe.get("details", {})
        eid = entry.get("employee_id", "")
        if eid not in id_groups:
            id_groups[eid] = {
                "names": details.get("names", []),
                "entry_count": details.get("entry_count", 0),
            }

    for eid, info in list(id_groups.items())[:_MAX_DETAIL_ROWS]:
        names = info.get("names", [])
        table_data.append(
            [
                Paragraph(eid, styles["MemoTableCell"]),
                Paragraph(", ".join(str(n) for n in names), styles["MemoTableCell"]),
                Paragraph(str(info.get("entry_count", 0)), styles["MemoTableCell"]),
            ]
        )

    style_cmds = ledger_table_style() + [("ALIGN", (2, 0), (2, -1), "RIGHT")]
    table = Table(
        table_data,
        colWidths=[1.5 * inch, 3.5 * inch, 1.2 * inch],
        repeatRows=1,
    )
    table.setStyle(TableStyle(style_cmds))
    story.append(table)


_DETAIL_TABLE_BUILDERS = {
    "PR-T4": _build_pay_after_term_table,
    "PR-T9": _build_ghost_employee_table,
    "PR-T10": _build_duplicate_bank_table,
    "PR-T1": _build_duplicate_id_table,
}


def _build_high_severity_detail(
    story: list,
    styles: dict,
    doc_width: float,
    result: dict[str, Any],
    section_counter: int,
) -> int:
    """BUG-02: Build High Severity Employee Detail section."""
    test_results = result.get("test_results", [])

    high_tests = [
        tr
        for tr in test_results
        if tr.get("severity") == "high" and tr.get("entries_flagged", 0) > 0 and tr.get("flagged_entries")
    ]

    if not high_tests:
        return section_counter

    label = _roman(section_counter)
    story.append(Paragraph(f"{label}. High Severity Employee Detail", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    for tr in high_tests:
        test_key = tr.get("test_key", "")
        flagged = tr.get("flagged_entries", [])
        count = tr.get("entries_flagged", 0)

        title = _DETAIL_TABLE_TITLES.get(
            test_key,
            f"{tr.get('test_name', '')} \u2014 Employee Detail",
        )
        story.append(Paragraph(f"<b>{title} ({count} items)</b>", styles["MemoBody"]))
        story.append(Spacer(1, 4))

        if not flagged:
            # BUG-007: entries_flagged > 0 but flagged_entries not populated
            story.append(
                Paragraph(
                    f"<i>No entry-level detail available for: {title}</i>",
                    styles["MemoBodySmall"],
                )
            )
        else:
            builder = _DETAIL_TABLE_BUILDERS.get(test_key)
            if builder:
                builder(story, styles, flagged)
            else:
                # BUG-007 fix: generic detail table for tests without a dedicated builder
                gen_data = [
                    [
                        Paragraph("Employee ID", styles["MemoTableHeader"]),
                        Paragraph("Employee Name", styles["MemoTableHeader"]),
                        Paragraph("Issue", styles["MemoTableHeader"]),
                        Paragraph("Amount", styles["MemoTableHeader"]),
                    ]
                ]
                for fe in flagged[:_MAX_DETAIL_ROWS]:
                    entry = fe.get("entry", {})
                    amt = entry.get("gross_pay") or entry.get("amount") or entry.get("net_pay", "")
                    amt_str = format_currency(amt) if isinstance(amt, (int, float)) else str(amt)
                    gen_data.append(
                        [
                            Paragraph(str(entry.get("employee_id", "") or ""), styles["MemoTableCell"]),
                            Paragraph(str(entry.get("employee_name", "") or ""), styles["MemoTableCell"]),
                            Paragraph(str(fe.get("issue", "")), styles["MemoTableCell"]),
                            Paragraph(amt_str, styles["MemoTableCell"]),
                        ]
                    )
                gen_table = Table(
                    gen_data,
                    colWidths=[1.2 * inch, 1.8 * inch, 2.2 * inch, 1.0 * inch],
                    repeatRows=1,
                )
                gen_table.setStyle(TableStyle(ledger_table_style() + [("ALIGN", (3, 0), (3, -1), "RIGHT")]))
                story.append(gen_table)

        procedure = _DETAIL_PROCEDURES.get(test_key, "")
        if procedure:
            story.append(Paragraph(f"<i>{procedure}</i>", styles["MemoBodySmall"]))

        story.append(Spacer(1, 8))

    return section_counter + 1


# ─────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────────


def generate_payroll_testing_memo(
    payroll_result: dict[str, Any],
    filename: str = "payroll_testing",
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
    """Generate a PDF testing memo for payroll testing results."""

    def _payroll_scope(
        story: Any, styles: Any, doc_width: Any, composite: Any, data_quality: Any, period_tested_arg: Any
    ) -> None:
        build_scope_section(
            story,
            styles,
            doc_width,
            composite,
            data_quality,
            entry_label="Total Payroll Entries Tested",
            period_tested=period_tested_arg,
            source_document=filename,
            source_document_title=source_document_title,
        )
        _build_gl_reconciliation(story, styles, doc_width, payroll_result)
        _build_headcount_rollforward(story, styles, doc_width, payroll_result)
        _build_department_summary(story, styles, doc_width, payroll_result)

    return generate_testing_memo(
        payroll_result,
        _PAYROLL_CONFIG,
        filename=filename,
        client_name=client_name,
        period_tested=period_tested,
        prepared_by=prepared_by,
        reviewed_by=reviewed_by,
        workpaper_date=workpaper_date,
        source_document_title=source_document_title,
        source_context_note=source_context_note,
        fiscal_year_end=fiscal_year_end,
        build_scope=_payroll_scope,
        build_post_results=_build_benford_note,
        build_extra_sections=_build_high_severity_detail,
        format_finding=_format_payroll_finding,
        include_signoff=include_signoff,
    )
