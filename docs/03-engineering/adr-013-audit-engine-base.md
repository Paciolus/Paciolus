# ADR-013: AuditEngineBase Adoption

**Status:** Accepted (Sprint 726 Phase 1, Sprint 727 triage)
**Date:** 2026-04-25 (Phase 1) / 2026-04-26 (triage)
**Decision-makers:** Engineering team

## Context

`backend/engine_framework.py` (Sprint 519) defines `AuditEngineBase`, an
abstract base class encoding a 10-step pipeline:

1. detect columns
2. apply manual column-mapping overrides
3. parse rows into typed domain objects
4. run quality checks
5. enrich data
6. run tool-specific test battery
7. compute composite score
8. assemble final result
9. (implicit) error/edge-case handling between steps
10. (implicit) instrumentation hooks

Three engines (JE, AP, Payroll) subclass `AuditEngineBase`. The other ~16
testing-shape engines re-implement equivalent pipelines as top-level
`run_*()` procedural functions, with each one's variation being mostly
incidental (different fixture-handling, slightly different error semantics,
ad-hoc instrumentation).

The agent-sweep audit (2026-04-24) flagged this as the single largest
architectural inconsistency in the backend, with veto-tier severity (8/10)
because:

- Bug fixes that should be uniform across engines (e.g., column-detection
  fallback semantics) have to be replicated 16 times.
- New engines added since Sprint 519 (e.g., the Sprint 689 expanded catalog)
  drifted onto the procedural pattern despite the ABC existing.
- Audit reviewers reading the codebase need to learn a different pipeline
  shape per engine — high cognitive overhead.

## Decision

Migrate the off-pattern engines to subclass `AuditEngineBase`, **incrementally,
one engine per sub-sprint**. Phase 1 (Sprint 726, this ADR) ships the
prevention guardrail; Phase 2+ ships the migrations.

### Phase 1 — Sprint 726 (this commit)

- `scripts/lint_engine_base_adoption.py` — AST scan that surfaces every
  `*_engine.py` / `*_testing_engine.py` module in `backend/` that does not
  subclass `AuditEngineBase`. Configurable blocklist (`NON_TESTING_ENGINES`)
  for engines that genuinely don't fit the pipeline shape (top-level
  orchestrator, indicator engines, tax-form preparers, side-cars).
- The script runs in CI as **advisory output** (warning-only, exit 0). Build
  log shows the off-pattern engine count; no PR blocks.
- Tests in `backend/tests/test_engine_base_lint.py` cover the AST detection
  (direct subclass + aliased base + syntax error → False) and the testing-
  engine filter (`*_testing_engine.py` always in scope; named blocklist
  takes precedence).
- This ADR documents the migration approach.

### Phase 1.5 — Sprint 727 triage (this commit)

Per-engine review of the 16 lint-flagged engines from Phase 1. Outcome:

**Migration targets (5 engines):** `ar_aging_engine`, `fixed_asset_testing_engine`,
`inventory_testing_engine`, `revenue_testing_engine`, `sod_engine`. These have
the testing-tool pipeline shape (test battery → composite_score → flagged
entries) and are valid Sprint 727+ migration candidates.

**Blocklist additions (7 engines):** `accrual_completeness_engine`,
`cash_flow_projector_engine`, `expense_category_engine`,
`lease_accounting_engine`, `lease_diagnostic_engine`,
`loan_amortization_engine`, `population_profile_engine`. These are
calculators, descriptive-stats aggregators, or indicator-only engines that
don't fit the 10-step pipeline. Added to `NON_TESTING_ENGINES` with
per-engine rationale comments.

**Borderline (4 engines):** `ratio_engine`, `sampling_engine`,
`three_way_match_engine`, `w2_reconciliation_engine`. These produce some
testing-shaped output but require design decisions before migration (e.g.,
"is each ratio threshold band a pass/fail test?"). Surfaced in
`BORDERLINE_ENGINES` set in the lint script as documentation; remain in the
findings (so they can't be silently forgotten) but are not migration-target
sprints' default queue.

After triage the lint reports **9 off-pattern engines** (5 migration targets
+ 4 borderline) — down from 16 in Phase 1. The honest migration backlog is
now visible.

### Phase 2 — Sprint 727 (sub-sprints) and onward

Each subsequent migration sprint:

1. Picks ONE off-pattern engine from the lint output (in the order
   prioritized by the agent-sweep: Revenue → AR → FA → Inventory → 3-way
   match → accrual completeness → population profile → sampling → cash
   flow projector).
2. Refactors that engine to subclass `AuditEngineBase`, adapting its
   `run_*()` procedural function into the abstract methods.
3. Lands a behavioral parity test: a fixture suite of synthetic TBs is run
   against both the pre-migration and post-migration engine; output must
   match modulo dataclass field ordering. The parity test is the
   migration's correctness gate; without it, the refactor is rejected.
4. Updates `scripts/lint_engine_base_adoption.py::NON_TESTING_ENGINES` if
   the migration concludes the engine doesn't fit (rare but possible).

### Phase 3 — Lint promotion

Once the agent-sweep-listed 9 engines are migrated:

- Flip the lint script's default exit code from 0 to 1 on findings.
- Add the script to CI as a blocking step.
- Future engine additions that don't subclass `AuditEngineBase` fail CI at
  PR time.

## Consequences

### Pros

- New engine authors inherit the pipeline shape; "build a `run_*()`"
  becomes a CI failure rather than tribal knowledge.
- Cross-cutting bug fixes (e.g., column-detection improvements) become
  one-place edits to `AuditEngineBase` rather than 16-place edits to
  procedural functions.
- Audit reviewers get one mental model per engine instead of one per
  file.
- Phase 1's lint output is itself the migration roadmap — running the
  script is how engineers know which engine to pick up next.

### Cons

- Migration is multi-sprint (1 engine ≈ 1 day of focused work + parity
  testing). The 9-engine queue translates to roughly 9 sub-sprints.
- Behavioral parity tests need synthetic TB fixtures per engine. Some
  engines (revenue, AR aging) accept large input shapes; building parity
  fixtures is non-trivial.
- The lint blocklist (`NON_TESTING_ENGINES`) is a curated decision per
  engine. Misclassification (excluding an engine that *should* migrate, or
  including one that shouldn't) is a possibility — but recoverable in
  the next sprint by adjusting the blocklist.

### Mitigations

- **Per-engine parity test** is the migration gate. A sprint that doesn't
  produce the parity artifact is not eligible to merge — the lint exit-code
  promotion (Phase 3) holds engineers honest.
- **Phase 1 advisory output** during the multi-sprint window keeps the
  off-pattern count visible. CI build log shows "16 testing engines off-
  pattern" → "12 off-pattern" → ... → "0 off-pattern" → flip to error.
- **Blocklist is in code, not config** — every change to
  `NON_TESTING_ENGINES` lands as a PR with the engineer's reasoning in
  the commit message.

## Alternatives considered

### A. Big-bang migration (one sprint, all 9 engines)
Rejected. The combined LoC is ~7,800 across the four largest engines
alone; an all-at-once migration concentrates regression risk and makes
the parity test suite a multi-week build before any engine ships.

### B. Generate `run_*()` wrappers from a registry (avoid the ABC entirely)
Rejected. The procedural pattern is what we're moving away from; adding
a wrapper layer adds indirection without solving the cognitive-overhead
problem. The `AuditEngineBase` ABC already exists and works for JE/AP/
Payroll — leverage what's there.

### C. Leave the procedural engines alone forever
Rejected. The drift cost compounds: every new engine added in a future
sprint either follows the ABC (good) or follows the procedural pattern
(bad). Without a CI gate, drift toward the procedural pattern is the
default. Phase 3's exit-code flip is what stops the drift.

## Related

- `backend/engine_framework.py` — the `AuditEngineBase` ABC.
- `backend/{je,ap,payroll}_testing_engine.py` — the three engines on
  pattern (Sprint 519).
- `scripts/lint_engine_base_adoption.py` — the Phase 1 advisory lint.
- `backend/tests/test_engine_base_lint.py` — lint script tests.
- `tasks/sprint-plan-agent-sweep-2026-04-24.md` — the multi-sprint plan
  this ADR codifies.
