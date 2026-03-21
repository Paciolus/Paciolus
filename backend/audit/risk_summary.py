"""Diagnostic tier assignment, scoring, and summary assembly.

This module takes the merged list of anomaly findings and produces an
aggregate diagnostic summary: severity counts, anomaly-type breakdown, a numeric
diagnostic score (0-100), a human-readable diagnostic tier label, and the
contributing risk factors.  It is the final analytic stage before results are
returned to the API layer.
"""

from __future__ import annotations

from typing import Any


def build_risk_summary(abnormal_balances: list[dict[str, Any]]) -> dict[str, Any]:
    """Build risk summary dict from merged abnormal balances.

    Counts by severity (high/medium/low) and by anomaly type.
    """
    high_severity = sum(1 for ab in abnormal_balances if ab.get("severity") == "high")
    medium_severity = sum(1 for ab in abnormal_balances if ab.get("severity") == "medium")
    informational_count = sum(1 for ab in abnormal_balances if ab.get("severity") == "informational")
    low_severity = len(abnormal_balances) - high_severity - medium_severity - informational_count
    suspense_count = sum(
        1 for ab in abnormal_balances if ab.get("anomaly_type") == "suspense_account" or ab.get("is_suspense_account")
    )
    concentration_count = sum(
        1
        for ab in abnormal_balances
        if (ab.get("anomaly_type", "").endswith("_concentration")) or ab.get("has_concentration_risk")
    )
    rounding_count = sum(
        1 for ab in abnormal_balances if ab.get("anomaly_type") == "rounding_anomaly" or ab.get("has_rounding_anomaly")
    )
    # Sub-type counts for concentration categories
    revenue_concentration = sum(1 for ab in abnormal_balances if ab.get("anomaly_type") == "revenue_concentration")
    asset_concentration = sum(1 for ab in abnormal_balances if ab.get("anomaly_type") == "asset_concentration")
    liability_concentration = sum(1 for ab in abnormal_balances if ab.get("anomaly_type") == "liability_concentration")
    expense_concentration = sum(1 for ab in abnormal_balances if ab.get("anomaly_type") == "expense_concentration")
    # Sprint 526: Count new anomaly types
    related_party_count = sum(
        1 for ab in abnormal_balances if ab.get("anomaly_type") == "related_party" or ab.get("is_related_party")
    )
    intercompany_count = sum(
        1
        for ab in abnormal_balances
        if ab.get("anomaly_type") == "intercompany_imbalance" or ab.get("is_intercompany_imbalance")
    )
    equity_signal_count = sum(
        1 for ab in abnormal_balances if ab.get("anomaly_type") == "equity_signal" or ab.get("is_equity_signal")
    )

    return {
        "total_anomalies": len(abnormal_balances),
        "high_severity": high_severity,
        "medium_severity": medium_severity,
        "low_severity": low_severity,
        "informational_count": informational_count,
        "anomaly_types": {
            "natural_balance_violation": sum(
                1 for ab in abnormal_balances if ab.get("anomaly_type") == "natural_balance_violation"
            ),
            "suspense_account": suspense_count,
            "concentration_risk": concentration_count,
            "revenue_concentration": revenue_concentration,
            "asset_concentration": asset_concentration,
            "liability_concentration": liability_concentration,
            "expense_concentration": expense_concentration,
            "rounding_anomaly": rounding_count,
            "related_party": related_party_count,
            "intercompany_imbalance": intercompany_count,
            "equity_signal": equity_signal_count,
        },
    }
