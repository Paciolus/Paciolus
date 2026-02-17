"""
Payroll Testing Memo PDF Generator (Sprint 88, refactored Sprint 90, simplified Sprint 157)

Config-driven wrapper around shared memo template.
Domain: ISA 240 / ISA 500 / PCAOB AS 2401.

Uses custom finding formatter for dict-type top_findings (employee + issue).
"""

from typing import Any, Optional

from shared.memo_template import TestingMemoConfig, generate_testing_memo

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
            "the payroll register exhibits a LOW risk profile. "
            "No material anomalies requiring further investigation were identified."
        ),
        "elevated": (
            "Based on the automated payroll testing procedures applied, "
            "the payroll register exhibits an ELEVATED risk profile. "
            "Select flagged entries should be reviewed for proper authorization and documentation."
        ),
        "moderate": (
            "Based on the automated payroll testing procedures applied, "
            "the payroll register exhibits a MODERATE risk profile. "
            "Flagged entries warrant focused review, particularly ghost employee indicators."
        ),
        "high": (
            "Based on the automated payroll testing procedures applied, "
            "the payroll register exhibits a HIGH risk profile. "
            "Significant anomalies were identified that require detailed investigation "
            "and may warrant expanded payroll audit procedures."
        ),
    },
)


def _format_payroll_finding(finding: Any) -> str:
    """Format payroll finding — handles both dict and string findings."""
    if isinstance(finding, dict):
        return f"{finding.get('employee', 'Unknown')} \u2014 {finding.get('issue', '')}"
    return str(finding)


def generate_payroll_testing_memo(
    payroll_result: dict[str, Any],
    filename: str = "payroll_testing",
    client_name: Optional[str] = None,
    period_tested: Optional[str] = None,
    prepared_by: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    workpaper_date: Optional[str] = None,
) -> bytes:
    """Generate a PDF testing memo for payroll testing results."""
    return generate_testing_memo(
        payroll_result, _PAYROLL_CONFIG,
        filename=filename, client_name=client_name,
        period_tested=period_tested, prepared_by=prepared_by,
        reviewed_by=reviewed_by, workpaper_date=workpaper_date,
        format_finding=_format_payroll_finding,
    )
