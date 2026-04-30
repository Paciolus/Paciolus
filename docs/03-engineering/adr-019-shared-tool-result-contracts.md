# ADR-019: Shared Tool-Result Contracts

**Status:** Accepted (Sprint 754b — post-initiative finishing pass)
**Date:** 2026-04-29
**Decision-makers:** Engineering team

## Context

Sprint 754 (Phase 5.2) was originally scoped to define shared analysis
interfaces (input contract / result envelope / error semantics) so tool
services could converge on a common shape. The sprint shipped partial
— it relocated the client-access helpers (the explicit deferred-items
trigger) but deferred the shared-interfaces work because **fewer than
2 tools had been relocated under ADR-018** at that point. Without
multiple relocated tools to compare shapes against, designing the
interfaces was speculative.

Sprint 754b is unblocked now (Sprint 753 + the post-initiative engine
relocation batch landed `recon`, `flux`, and `cutoff_risk` under
`services/audit/<tool>/`).

A survey of the 18 tool-result classes found **two distinct shapes**:

1. **Indicator results** — flux, recon, cutoff_risk, going_concern,
   account_risk_heatmap, expense_category. One analytical signal +
   aggregate counts + narrative.
2. **Testing-battery results** — JE Testing, AP Testing, Payroll
   Testing, Revenue Testing, AR Aging, Fixed Asset Testing, Inventory
   Testing. Composite score + list of test results + optional
   data-quality / column-detection blocks.

Trying to merge them into one shape required either (a) discarding
fields, or (b) making a base class with so many `Optional` fields that
it taught nothing.

## Decision

Define **Protocols** (PEP 544 — structural typing), not ABCs:

- **`ToolResult`** — base contract: every tool result has `to_dict() -> dict`.
- **`IndicatorResult(ToolResult)`** — single-signal result shape.
- **`TestingBatteryResult(ToolResult)`** — battery shape with
  `composite_score: CompositeScoreLike` + `test_results: list[TestResultLike]`.
- **`CompositeScoreLike`** — every per-tool composite score has
  `score: float` + `to_dict()`.
- **`TestResultLike`** — every per-tool test result has `test_name: str`
  + `entries_flagged: int` + `total_entries: int` + `to_dict()`.

All Protocols are `@runtime_checkable` so tests can `isinstance()`-verify
conformance without importing the Protocol's classes for inheritance.

**`ToolError(ValueError)`** — base exception class for tool-level
business-logic failures, mirroring the
`PasswordResetError(ValueError)` pattern from Sprint 746a. Tools may
subclass directly or continue to inherit from `ValueError` (both
accepted; existing call sites unchanged).

### Why Protocol, not ABC

The two shapes have meaningful per-tool variation in their fields:

- `CompositeScore` (JE) has `flags_by_severity`, `top_findings`.
- `APCompositeScore` adds `duplicate_payment_summary`.
- `PayrollCompositeScore` adds GL-reconciliation fields.

Forcing a common ABC would either:

- Discard those fields → real information loss.
- Make a base with `Optional` everywhere → so loose it teaches nothing
  about the shared contract.

Protocol-based structural typing gives us the documentation + runtime
isinstance + mypy support without forcing field-set convergence.

### Why two Protocols, not one

Tried the merged version — it had `Optional[CompositeScoreLike]` and
`Optional[list[TestResultLike]]` to accommodate indicator results that
don't have those, plus `Optional[items_list_alias]` to accommodate
indicator results that do. Two narrow Protocols beat one wide one.

### Conformance verification

`backend/tests/test_tool_contracts.py` (16 tests) asserts:

- The 3 relocated tools (`recon`, `flux`, `cutoff_risk`) satisfy
  `IndicatorResult` via `isinstance` checks on real instances.
- 4 testing engines (`JE`, `AP`, `Payroll`, `Revenue`, `AR`) have
  `composite_score` + `test_results` field annotations and `to_dict`
  methods (class-level shape checks since constructing real testing
  results requires full pipelines + fixtures).
- `ToolError` inherits from `ValueError` and supports both direct
  raise/catch and subclass patterns.

## Consequences

- New tools get a documented target shape — pick `IndicatorResult` or
  `TestingBatteryResult` based on whether they produce one signal or a
  battery.
- A new "service boundary helper" sprint (future) can introduce a
  shared `def execute_tool(...) -> ToolResult: ...` wrapper that
  catches `ToolError` and maps to `HTTPException` uniformly. ADR-019's
  contracts give that future sprint a discriminator.
- The 18 existing tool-result dataclasses already conform — no code
  changes needed.
- `mypy` can flag drift via the Protocol membership: a function typed
  `def f(r: IndicatorResult) -> None` will type-check any conforming
  tool result.

## Out of scope

- **Merging the per-tool `<Tool>CompositeScore` dataclasses.** Tried;
  loses per-tool fields. Each remains its own class implementing
  `CompositeScoreLike`.
- **Migrating the 7 testing engines' result classes to inherit from a
  base.** Same reason. Protocols give us the verification without the
  inheritance constraint.
- **Service-boundary helper that consumes `ToolResult`.** Filed for a
  future sprint; ADR-019 establishes the contract this helper would
  rely on.

## See also

- `backend/services/audit/contracts.py` — the Protocol + exception
  definitions.
- `backend/tests/test_tool_contracts.py` — conformance tests.
- ADR-015 — backend route/service boundaries (the larger pattern these
  contracts plug into).
- ADR-018 — domain package relocation (the relocations this sprint
  was waiting on).
- Sprint 746a / `services/auth/recovery.py::PasswordResetError` — the
  service-error pattern `ToolError` mirrors.
