"""Backward-compatibility shim — re-exports from audit.rules subpackage.

All anomaly detection functions have been split into per-family modules under
``audit/rules/``.  This module re-exports everything so that existing consumers
(StreamingAuditor, pipeline.py, tests) continue to work without changes.

New code should import directly from ``audit.rules`` or the specific submodule.
"""

from __future__ import annotations

# Re-export all detection functions and the merger
from audit.rules.balance import detect_abnormal_balances_streaming
from audit.rules.concentration import (
    detect_concentration_risk,
    detect_expense_concentration,
    detect_revenue_concentration,
)
from audit.rules.equity import detect_equity_signals
from audit.rules.merger import _merge_anomalies
from audit.rules.relationships import (
    detect_intercompany_imbalances,
    detect_related_party_accounts,
)
from audit.rules.rounding import detect_rounding_anomalies
from audit.rules.suspense import detect_suspense_accounts

# Legacy backward-compatibility attributes
from classification_rules import ROUND_NUMBER_TIER1_SUPPRESS

_ROUNDING_TIER1_KEYWORDS: list[str] = ROUND_NUMBER_TIER1_SUPPRESS
_ROUNDING_TIER1_CATEGORIES: set[str] = set()
_ROUNDING_TIER3_KEYWORDS: list[str] = [
    "suspense",
    "clearing",
    "miscellaneous",
    "sundry",
    "unallocated",
    "unclassified",
]

__all__ = [
    "detect_abnormal_balances_streaming",
    "detect_suspense_accounts",
    "detect_concentration_risk",
    "detect_rounding_anomalies",
    "detect_related_party_accounts",
    "detect_intercompany_imbalances",
    "detect_equity_signals",
    "detect_revenue_concentration",
    "detect_expense_concentration",
    "_merge_anomalies",
    "_ROUNDING_TIER1_KEYWORDS",
    "_ROUNDING_TIER1_CATEGORIES",
    "_ROUNDING_TIER3_KEYWORDS",
]
