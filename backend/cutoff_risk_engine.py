"""Backward-compatibility shim for the cutoff risk engine.

The implementation moved to ``services.audit.cutoff_risk.analysis`` per
ADR-018. This module re-exports the public API so existing
``from cutoff_risk_engine import ...`` statements continue to work.

The private helpers (`_is_cutoff_sensitive`, `_test_*`) are also
re-exported for `tests/test_cutoff_risk.py`, which exercises them
directly.

New code should import from ``services.audit.cutoff_risk.analysis``.
"""

from services.audit.cutoff_risk.analysis import (  # noqa: F401
    CUTOFF_SENSITIVE_KEYWORDS,
    NEAR_ZERO,
    CutoffFlag,
    CutoffRiskReport,
    _is_cutoff_sensitive,
    _test_round_number,
    _test_spike,
    _test_zero_balance,
    compute_cutoff_risk,
)

__all__ = [
    "CUTOFF_SENSITIVE_KEYWORDS",
    "CutoffFlag",
    "CutoffRiskReport",
    "NEAR_ZERO",
    "_is_cutoff_sensitive",
    "_test_round_number",
    "_test_spike",
    "_test_zero_balance",
    "compute_cutoff_risk",
]
