"""
Revenue Testing Memo PDF Generator (Sprint 105, simplified Sprint 157)

Config-driven wrapper around shared memo template.
Domain: ISA 240 / ISA 500 / PCAOB AS 2401 — presumed fraud risk in revenue recognition.
"""

from typing import Any, Optional

from shared.memo_template import TestingMemoConfig, generate_testing_memo

REVENUE_TEST_DESCRIPTIONS = {
    "large_manual_entries": "Flags manual revenue entries exceeding performance materiality threshold (ISA 240 fraud risk indicator).",
    "year_end_concentration": "Flags revenue concentrated in the last days of the period, a common revenue recognition anomaly indicator.",
    "round_revenue_amounts": "Flags revenue entries at round dollar amounts that may indicate estimates or adjustments.",
    "sign_anomalies": "Flags debit balances in revenue accounts (normally credit), indicating potential mispostings.",
    "unclassified_entries": "Flags revenue entries missing account classification (unmapped to chart of accounts).",
    "zscore_outliers": "Uses z-score analysis to identify statistically unusual revenue amounts.",
    "trend_variance": "Flags significant period-over-period revenue changes that may indicate revenue recognition anomalies.",
    "concentration_risk": "Flags single accounts representing a disproportionate share of total revenue.",
    "cutoff_risk": "Flags revenue entries near period boundaries that may indicate cut-off anomalies.",
    "benford_law": "Applies Benford's Law first-digit analysis to revenue transaction amounts.",
    "duplicate_entries": "Flags revenue entries with identical amount, date, and account — potential duplicate postings.",
    "contra_revenue_anomalies": "Flags elevated returns/allowances relative to gross revenue, a fraud risk indicator.",
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
        "Results represent revenue anomaly indicators, not fraud detection conclusions:"
    ),
    isa_reference="ISA 240 (presumed fraud risk in revenue recognition) and ISA 500",
    risk_assessments={
        "low": (
            "Based on the automated revenue testing procedures applied, "
            "the revenue GL extract exhibits a LOW risk profile. "
            "No material revenue recognition anomalies requiring further investigation were identified."
        ),
        "elevated": (
            "Based on the automated revenue testing procedures applied, "
            "the revenue GL extract exhibits an ELEVATED risk profile. "
            "Select flagged entries should be reviewed for proper revenue recognition treatment "
            "and supporting documentation."
        ),
        "moderate": (
            "Based on the automated revenue testing procedures applied, "
            "the revenue GL extract exhibits a MODERATE risk profile. "
            "Flagged entries warrant focused review as revenue recognition anomaly indicators, "
            "particularly year-end concentration and cut-off items."
        ),
        "high": (
            "Based on the automated revenue testing procedures applied, "
            "the revenue GL extract exhibits a HIGH risk profile. "
            "Significant revenue recognition anomaly indicators were identified that require "
            "detailed investigation and may warrant expanded revenue audit procedures "
            "per ISA 240 and PCAOB AS 2401."
        ),
    },
)


def generate_revenue_testing_memo(
    revenue_result: dict[str, Any],
    filename: str = "revenue_testing",
    client_name: Optional[str] = None,
    period_tested: Optional[str] = None,
    prepared_by: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    workpaper_date: Optional[str] = None,
) -> bytes:
    """Generate a PDF testing memo for revenue testing results."""
    return generate_testing_memo(
        revenue_result, _REVENUE_CONFIG,
        filename=filename, client_name=client_name,
        period_tested=period_tested, prepared_by=prepared_by,
        reviewed_by=reviewed_by, workpaper_date=workpaper_date,
    )
