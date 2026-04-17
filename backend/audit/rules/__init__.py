"""Anomaly detection rules — split by family.

Each module contains one or more detection functions that take account-balance
mappings and return lists of finding dicts.  The merger module combines
findings from all detectors into a single de-duplicated list.
"""

from audit.rules.balance import detect_abnormal_balances_streaming
from audit.rules.concentration import (
    detect_concentration_risk,
    detect_expense_concentration,
    detect_revenue_concentration,
)
from audit.rules.equity import detect_equity_signals
from audit.rules.gaps import AccountGap, detect_account_number_gaps
from audit.rules.merger import _merge_anomalies
from audit.rules.relationships import (
    detect_intercompany_imbalances,
    detect_related_party_accounts,
)
from audit.rules.rounding import detect_rounding_anomalies
from audit.rules.suspense import detect_suspense_accounts

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
    "detect_account_number_gaps",
    "AccountGap",
    "_merge_anomalies",
]
