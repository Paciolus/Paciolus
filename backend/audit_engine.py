"""Backward-compatibility shim for the audit pipeline.

The monolithic audit_engine module has been decomposed into the ``audit``
package (backend/audit/).  This file re-exports every public symbol so that
existing ``from audit_engine import ...`` statements continue to work
without modification.

New code should import directly from the ``audit`` package:

    from audit import StreamingAuditor, audit_trial_balance_streaming
    from audit.anomaly_rules import _merge_anomalies
    from audit.classification import validate_balance_sheet_equation
"""

# Re-export the full public API from the audit package
from audit import (  # noqa: F401
    ASSET_KEYWORDS,
    BS_IMBALANCE_THRESHOLD_HIGH,
    BS_IMBALANCE_THRESHOLD_LOW,
    CONFIDENCE_HIGH,
    CONFIDENCE_MEDIUM,
    DEFAULT_CHUNK_SIZE,
    LIABILITY_KEYWORDS,
    StreamingAuditor,
    _merge_anomalies,
    audit_trial_balance_multi_sheet,
    audit_trial_balance_streaming,
    build_risk_summary,
    check_balance,
    detect_abnormal_balances,
    process_tb_chunked,
    validate_balance_sheet_equation,
)

__all__ = [
    "ASSET_KEYWORDS",
    "BS_IMBALANCE_THRESHOLD_HIGH",
    "BS_IMBALANCE_THRESHOLD_LOW",
    "CONFIDENCE_HIGH",
    "CONFIDENCE_MEDIUM",
    "DEFAULT_CHUNK_SIZE",
    "LIABILITY_KEYWORDS",
    "StreamingAuditor",
    "_merge_anomalies",
    "audit_trial_balance_multi_sheet",
    "audit_trial_balance_streaming",
    "build_risk_summary",
    "check_balance",
    "detect_abnormal_balances",
    "process_tb_chunked",
    "validate_balance_sheet_equation",
]
