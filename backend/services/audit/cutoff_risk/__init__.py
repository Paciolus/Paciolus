"""
Cutoff risk indicator package (ADR-018 — Sprint 759 follow-up).

Per-tool layout for the cutoff risk indicator engine. The
`backend/cutoff_risk_engine.py` shim re-exports `compute_cutoff_risk`,
`CutoffFlag`, `CutoffRiskReport`, and the test-private helpers that
`tests/test_cutoff_risk.py` depends on.

New code should import directly from
`services.audit.cutoff_risk.analysis`.
"""
