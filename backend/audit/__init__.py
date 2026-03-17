"""Paciolus Audit Pipeline -- public API surface.

This package decomposes the monolithic ``audit_engine`` module into a staged
pipeline with explicit typed contracts between stages. No logic lives here;
this file exists solely to re-export the symbols that external code imports.

Modules:
    contracts        -- Typed dataclasses for inter-stage data flow
    ingestion        -- Raw file parsing, balance checking, DataFrame normalization
    classification   -- Account classification, CSV type resolution, BS validation
    anomaly_rules    -- All anomaly detection rules as composable functions
    risk_summary     -- Risk tier assignment, scoring, summary assembly
    streaming_auditor -- Stateful chunk-processing auditor class
    pipeline         -- Thin orchestrator wiring stages together
"""

# ── Re-exports (preserve exact import surface of old audit_engine) ───

from audit.anomaly_rules import _merge_anomalies
from audit.classification import (
    ASSET_KEYWORDS,
    BS_IMBALANCE_THRESHOLD_HIGH,
    BS_IMBALANCE_THRESHOLD_LOW,
    CONFIDENCE_HIGH,
    CONFIDENCE_MEDIUM,
    LIABILITY_KEYWORDS,
    validate_balance_sheet_equation,
)
from audit.ingestion import check_balance, detect_abnormal_balances
from audit.pipeline import audit_trial_balance_multi_sheet, audit_trial_balance_streaming
from audit.risk_summary import build_risk_summary
from audit.streaming_auditor import StreamingAuditor
from security_utils import DEFAULT_CHUNK_SIZE, process_tb_chunked

__all__ = [
    # Pipeline entry points
    "audit_trial_balance_streaming",
    "audit_trial_balance_multi_sheet",
    # Stateful auditor
    "StreamingAuditor",
    # Standalone helpers
    "check_balance",
    "detect_abnormal_balances",
    "validate_balance_sheet_equation",
    # Merge / summary
    "_merge_anomalies",
    "build_risk_summary",
    # Constants (re-exported)
    "DEFAULT_CHUNK_SIZE",
    "process_tb_chunked",
    "ASSET_KEYWORDS",
    "LIABILITY_KEYWORDS",
    "BS_IMBALANCE_THRESHOLD_LOW",
    "BS_IMBALANCE_THRESHOLD_HIGH",
    "CONFIDENCE_HIGH",
    "CONFIDENCE_MEDIUM",
]
