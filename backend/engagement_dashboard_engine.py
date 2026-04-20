"""
Engagement Risk Dashboard Engine

Aggregates results from multiple report types into a cross-report risk dashboard.
Zero-storage compliant — results are passed in per request, not retrieved from database.

Data source: List of previously-generated report result dicts passed from frontend.
"""

from dataclasses import dataclass, field
from typing import Any, Optional

from shared.testing_enums import normalize_risk_tier

# ═══════════════════════════════════════════════════════════════
# Risk Thread Rules
# ═══════════════════════════════════════════════════════════════

RISK_THREAD_RULES: list[dict[str, Any]] = [
    {
        "name": "Revenue Recognition Risk",
        "conditions": [
            {"report_type": "revenue_testing", "test_key": "cutoff_risk", "min_severity": "medium"},
            {"report_type": "revenue_testing", "test_key": "year_end_concentration", "min_severity": "medium"},
            {"report_type": "revenue_testing", "test_key": "sign_anomalies", "min_severity": "low"},
        ],
        "narrative": (
            "Revenue recognition risk indicators were detected across multiple tests. "
            "Cut-off anomalies combined with year-end concentration patterns may suggest "
            "premature or accelerated revenue recognition. This thread warrants expanded "
            "substantive procedures per ISA 240 (presumed fraud risk in revenue)."
        ),
    },
    {
        "name": "AP / Cash Cycle Risk",
        "conditions": [
            {"report_type": "ap_payment_testing", "test_key": "payment_before_invoice", "min_severity": "medium"},
            {"report_type": "ap_payment_testing", "test_key": "vendor_name_variations", "min_severity": "low"},
            {"report_type": "bank_reconciliation", "field": "bank_only_count", "min_value": 5},
        ],
        "narrative": (
            "AP and cash cycle risk indicators span multiple reports. Payment timing "
            "anomalies combined with vendor name variations and outstanding bank items "
            "may indicate fictitious vendor activity or unauthorized disbursements. "
            "Cross-reference AP vendor master with bank payees."
        ),
    },
    {
        "name": "Concentration Risk",
        "conditions": [
            {"report_type": "ar_aging_testing", "test_key": "customer_concentration", "min_severity": "medium"},
            {"report_type": "revenue_testing", "test_key": "concentration_risk", "min_severity": "medium"},
            {"report_type": "inventory_testing", "test_key": "category_concentration", "min_severity": "low"},
        ],
        "narrative": (
            "Concentration risk was identified across revenue, receivables, and/or inventory. "
            "High dependence on a limited number of customers, products, or categories "
            "increases vulnerability to credit loss, demand shifts, and valuation risk. "
            "Consider expanded confirmation procedures and going concern indicators."
        ),
    },
]

SEVERITY_ORDER = {"high": 3, "medium": 2, "low": 1}


@dataclass
class ReportSummary:
    """Summary of a single report's results."""

    report_type: str
    report_title: str
    risk_score: float
    risk_tier: str
    total_flagged: int
    high_severity_count: int
    tests_run: int

    def to_dict(self) -> dict:
        return {
            "report_type": self.report_type,
            "report_title": self.report_title,
            "risk_score": round(self.risk_score, 1),
            "risk_tier": self.risk_tier,
            "total_flagged": self.total_flagged,
            "high_severity_count": self.high_severity_count,
            "tests_run": self.tests_run,
        }


@dataclass
class RiskThread:
    """A cross-report risk thread with matching evidence."""

    name: str
    narrative: str
    matched_conditions: list[str] = field(default_factory=list)
    severity: str = "medium"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "narrative": self.narrative,
            "matched_conditions": self.matched_conditions,
            "severity": self.severity,
        }


@dataclass
class DashboardResult:
    """Aggregated engagement risk dashboard result."""

    report_count: int
    total_high_findings: int
    overall_risk_score: float
    overall_risk_tier: str
    report_summaries: list[ReportSummary]
    risk_threads: list[RiskThread]
    priority_actions: list[str]

    def to_dict(self) -> dict:
        return {
            "report_count": self.report_count,
            "total_high_findings": self.total_high_findings,
            "overall_risk_score": round(self.overall_risk_score, 1),
            "overall_risk_tier": self.overall_risk_tier,
            "report_summaries": [r.to_dict() for r in self.report_summaries],
            "risk_threads": [t.to_dict() for t in self.risk_threads],
            "priority_actions": self.priority_actions,
        }


def _extract_report_summary(report: dict[str, Any]) -> Optional[ReportSummary]:
    """Extract a ReportSummary from a tool result dict."""
    composite = report.get("composite_score", {})
    if not composite:
        # Fallback for reports that lack composite_score (legacy bank rec, three-way match)
        summary = report.get("summary", {})
        if not summary:
            return None
        report_type = report.get("report_type", "unknown")

        # Derive score from rec_tests if available, rather than hardcoding 0
        risk_score = 0.0
        total_flagged = summary.get("total_unmatched", 0)
        high_sev = 0
        tests_run = 0
        rec_tests = report.get("rec_tests", [])
        if rec_tests:
            tests_run = len(rec_tests)
            for t in rec_tests:
                flagged = t.get("flagged_count", 0)
                total_flagged += flagged
                for item in t.get("flagged_items", []):
                    if item.get("severity") == "high":
                        high_sev += 1
            # Estimate risk: 3*high + 2*medium flagged items, capped at 100
            med_count = total_flagged - high_sev
            risk_score = min(high_sev * 3 + med_count * 2, 100)

        return ReportSummary(
            report_type=report_type,
            report_title=report.get("report_title", report_type.replace("_", " ").title()),
            risk_score=risk_score,
            risk_tier=normalize_risk_tier(summary.get("risk_assessment", "low")),
            total_flagged=total_flagged,
            high_severity_count=high_sev,
            tests_run=tests_run,
        )

    flags_by_severity = composite.get("flags_by_severity", {})
    return ReportSummary(
        report_type=report.get("report_type", "unknown"),
        report_title=report.get("report_title", "Unknown Report"),
        risk_score=composite.get("score", 0),
        risk_tier=normalize_risk_tier(composite.get("risk_tier", "low")),
        total_flagged=composite.get("total_flagged", 0),
        high_severity_count=flags_by_severity.get("high", 0),
        tests_run=composite.get("tests_run", 0),
    )


def _evaluate_risk_threads(
    reports: list[dict[str, Any]],
) -> list[RiskThread]:
    """Evaluate cross-report risk thread rules against report results."""
    threads: list[RiskThread] = []

    # Index reports by type for quick lookup
    reports_by_type: dict[str, list[dict]] = {}
    for r in reports:
        rtype = r.get("report_type", "")
        reports_by_type.setdefault(rtype, []).append(r)

    for rule in RISK_THREAD_RULES:
        matched: list[str] = []
        max_severity = "low"

        for condition in rule["conditions"]:
            rtype = condition.get("report_type", "")
            matching_reports = reports_by_type.get(rtype, [])

            for report in matching_reports:
                # Check test_key conditions
                if "test_key" in condition:
                    test_results = report.get("test_results", [])
                    for tr in test_results:
                        if tr.get("test_key") == condition["test_key"]:
                            # Severity taxonomy here (Severity enum) is 3-tier
                            # high/medium/low — do NOT normalize to the 4-tier
                            # RiskTier scale used at report aggregation level.
                            sev = tr.get("severity", "low")
                            min_sev = condition.get("min_severity", "low")
                            if SEVERITY_ORDER.get(sev, 0) >= SEVERITY_ORDER.get(min_sev, 0):
                                if tr.get("entries_flagged", 0) > 0:
                                    matched.append(f"{rtype}:{condition['test_key']}")
                                    if SEVERITY_ORDER.get(sev, 0) > SEVERITY_ORDER.get(max_severity, 0):
                                        max_severity = sev

                # Check field value conditions
                if "field" in condition:
                    summary = report.get("summary", {})
                    val = summary.get(condition["field"], 0)
                    if val >= condition.get("min_value", 0):
                        matched.append(f"{rtype}:{condition['field']}")

        # Thread is active if at least 2 conditions match
        if len(matched) >= 2:
            threads.append(
                RiskThread(
                    name=rule["name"],
                    narrative=rule["narrative"],
                    matched_conditions=matched,
                    severity=max_severity,
                )
            )

    return threads


def _compute_overall_tier(score: float) -> str:
    """Map overall diagnostic score to tier (matching 4-tier scale)."""
    if score <= 10:
        return "low"
    elif score <= 25:
        return "moderate"
    elif score <= 50:
        return "elevated"
    else:
        return "high"


def _generate_priority_actions(
    summaries: list[ReportSummary],
    threads: list[RiskThread],
) -> list[str]:
    """Generate recommended audit response priority list."""
    actions: list[str] = []

    # Actions from high-risk reports
    high_reports = [s for s in summaries if s.risk_tier == "high"]
    for report in sorted(high_reports, key=lambda r: r.risk_score, reverse=True):
        actions.append(
            f"Investigate {report.report_title} — {report.high_severity_count} high-severity findings "
            f"(diagnostic score: {report.risk_score:.1f})"
        )

    # Actions from risk threads
    for thread in threads:
        actions.append(
            f"Address {thread.name} — cross-report pattern detected ({len(thread.matched_conditions)} indicators)"
        )

    # Actions from elevated reports
    elevated_reports = [s for s in summaries if s.risk_tier == "elevated"]
    for report in sorted(elevated_reports, key=lambda r: r.risk_score, reverse=True)[:3]:
        actions.append(f"Review {report.report_title} flagged items — {report.total_flagged} items for review")

    return actions[:10]  # Cap at 10 actions


def compute_engagement_dashboard(
    reports: list[dict[str, Any]],
    *,
    client_name: Optional[str] = None,
    engagement_period: Optional[str] = None,
) -> DashboardResult:
    """Compute the Engagement Risk Dashboard from multiple report results.

    Args:
        reports: List of tool result dicts (each must include "report_type" and "report_title")
        client_name: Optional client name for context
        engagement_period: Optional period description

    Returns:
        DashboardResult with aggregated metrics and cross-report analysis
    """
    summaries: list[ReportSummary] = []
    for report in reports:
        summary = _extract_report_summary(report)
        if summary:
            summaries.append(summary)

    # Sort by risk score descending
    summaries.sort(key=lambda s: s.risk_score, reverse=True)

    # Overall metrics
    total_high = sum(s.high_severity_count for s in summaries)
    if summaries:
        overall_score = sum(s.risk_score for s in summaries) / len(summaries)
    else:
        overall_score = 0

    # Cross-report risk threads
    threads = _evaluate_risk_threads(reports)

    # Boost overall score if risk threads are active
    thread_boost = len(threads) * 5
    overall_score = min(overall_score + thread_boost, 100)

    overall_tier = _compute_overall_tier(overall_score)

    # Priority actions
    priority_actions = _generate_priority_actions(summaries, threads)

    return DashboardResult(
        report_count=len(summaries),
        total_high_findings=total_high,
        overall_risk_score=overall_score,
        overall_risk_tier=overall_tier,
        report_summaries=summaries,
        risk_threads=threads,
        priority_actions=priority_actions,
    )
