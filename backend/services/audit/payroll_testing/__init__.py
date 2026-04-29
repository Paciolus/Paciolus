"""
Payroll Testing engine package (ADR-018 — testing engine relocation).

Hosts the per-tool layout for the `payroll_testing_engine` relocation:
  - `analysis.py` — full engine implementation (relocated from
    `backend/payroll_testing_engine.py`, which is now a backward-compat shim).

The legacy `backend/payroll_testing_engine` module re-exports the entire public
+ private symbol surface so existing
`from payroll_testing_engine import ...` statements (including underscore-prefixed
test helpers) continue to work without modification. New code should
import from `services.audit.payroll_testing.analysis` directly.
"""
