# Sprints 726–731 Details

> Archived from `tasks/todo.md` Active Phase on 2026-04-26.

---

### Sprint 726: AuditEngineBase Migration — Phase 1 (advisory lint + ADR)
**Status:** COMPLETE 2026-04-25 — agent-sweep wave 12, the engine-pattern foundation.
**Priority:** P2 (architectural; the migration's prevention story is foundational for all engine work post-Sprint-689).
**Source:** Agent sweep 2026-04-24, punch list 3.1 + BackendCritic 8/10.

**Problem class:** `engine_framework.py::AuditEngineBase` defines a 10-step pipeline ABC; only 3 of the ~16 testing-shape engines (JE, AP, Payroll) subclass it. The other 13 reimplement equivalent pipelines as top-level `run_*()` procedural functions, with each one's variation being mostly incidental. Sprint 689 added 7 more engines without anyone noticing the drift — the inconsistency compounds without a CI gate.

**Scope landed (Phase 1):**
- [x] **`scripts/lint_engine_base_adoption.py`** — AST scan that surfaces every `*_engine.py` / `*_testing_engine.py` module not subclassing `AuditEngineBase`. Detects both direct (`class X(AuditEngineBase)`) and aliased (`class X(framework.AuditEngineBase)`) subclass forms. Configurable `NON_TESTING_ENGINES` blocklist for engines that genuinely don't fit the pipeline (top-level orchestrator, indicator engines, tax-form preparers, side-cars). Default exit code: 0 (warning only); `--strict` flag flips to non-zero for Sprint 727's gate validation.
- [x] **`backend/tests/test_engine_base_lint.py`** — 12 tests: AST detection (5: direct + aliased + non-subclass + unrelated-base + syntax-error), testing-engine filter (4: testing_engine suffix always included, blocklist exclusion, non-blocklisted inclusion, non-engine files), known-migrated state (1: JE/AP/Payroll *not* in findings — catches regression), CLI (2: default exits 0, --strict exits 1 on findings).
- [x] **`docs/03-engineering/adr-013-audit-engine-base.md`** — ADR documenting the migration approach: Phase 1 (this commit, lint at warning), Phase 2+ (Sprint 727 onwards, one engine per sub-sprint with mandatory behavioral-parity tests), Phase 3 (lint exit-code flips to 1, becomes hard gate). Alternatives-considered section rejects big-bang migration and registry-of-wrappers approaches; mitigations note the parity test as the migration's correctness gate.
- [x] **CI integration** — wired into `.github/workflows/ci.yml` `openapi-drift-check` job as an advisory step with `continue-on-error: true`. Build log shows the off-pattern engine count without blocking PRs. Pin-promotion to required-status is deferred to Sprint 727.

**Lint findings (16 off-pattern engines as of 2026-04-25):**
`accrual_completeness_engine`, `ar_aging_engine`, `cash_flow_projector_engine`, `expense_category_engine`, `fixed_asset_testing_engine`, `inventory_testing_engine`, `lease_accounting_engine`, `lease_diagnostic_engine`, `loan_amortization_engine`, `population_profile_engine`, `ratio_engine`, `revenue_testing_engine`, `sampling_engine`, `sod_engine`, `three_way_match_engine`, `w2_reconciliation_engine`. Some of these (lease_*, sod, loan_amortization, ratio, w2_reconciliation, expense_category) may end up in the blocklist after closer review during Sprint 727 — they're surfaced now so the decision is explicit per-engine in a follow-up sprint, not silent drift.

**Recurrence prevention (the durable artifact):**
1. **Lint surfaces the migration backlog** — the script's output IS the migration roadmap. Engineers don't have to grep the codebase to find the next engine; they run the lint and pick from its output.
2. **`NON_TESTING_ENGINES` is in code, not config** — every change to the blocklist lands as a PR with the engineer's reasoning. Audit-reviewable.
3. **Phase progression is explicit** — Sprint 727 promotes exit code from 0 to 1; Sprint 727+sprints land migrations one engine at a time with mandatory parity tests. The ADR pins the schedule so a future sprint can't quietly skip the gate-promotion step.
4. **Tests pin the known-migrated state** — `test_je_ap_payroll_not_in_findings` would fail if any of the three migrated engines silently de-migrated (e.g., if a refactor removed the subclass declaration). Catches regressions in the other direction too.

**Out of scope (deferred to follow-up sprints):**
- **The actual engine migrations.** Per the ADR, each migration takes ~1 day of focused work + parity-fixture authoring; doing 9 in one commit concentrates regression risk. Sprint 727 picks up Revenue (the agent-sweep top-priority engine, 2,509 LoC) as the first migration. Subsequent sprints follow the agent-sweep order.
- **Lint exit-code promotion to error.** Belongs in Sprint 727 once at least one migration has shipped through the new pattern, so the gate has a real example to point at.
- **Some engines may end up in the blocklist** after Sprint 727's per-engine review concludes they don't fit `AuditEngineBase`'s 10-step pipeline (e.g., loan_amortization is purely a calculator, ratio_engine outputs continuous ratios not flagged-entry tests). Each blocklist add lands as a PR with rationale.

**Validation:**
- 12/12 lint tests pass
- Lint surfaces 16 off-pattern engines (audit-reviewable list captured above)
- ADR committed; references the lint script + tests
- CI integration is `continue-on-error: true` so builds don't break on the advisory output
- A synthetic `class X(AuditEngineBase)` source string returns True via AST detection; a synthetic `class X(SomethingElse)` returns False

**Lesson tie-in:** Same prevention pattern as Sprint 723 (per-file coverage floors locked at current state) and Sprint 731 (cadence-window deadlines): the gate ships first at warning level, the migrations land incrementally, and the gate flips to blocking once the backlog is clean. Avoids the "big-bang refactor that takes months and never lands" failure mode.


---

### Sprint 727a: AuditEngineBase Migration — inventory_testing_engine
**Status:** COMPLETE 2026-04-26 — first real engine migration; validates the pattern.
**Priority:** P2 (migration cadence ramp-up).
**Source:** ADR-013 Phase 2a sub-sprint.

**Why inventory first:** `run_inventory_testing()` was already a clean procedural pipeline with helper functions extracted for each step (detect_inv_columns / parse_inv_entries / assess_inv_data_quality / run_inv_test_battery / calculate_inv_composite_score). The migration was mostly plumbing — adding the subclass that delegates to those helpers — rather than a deep refactor. Picking it as the shake-down validates the pattern before the bigger engines (Revenue 2,509 LoC, AR 2,179 LoC, FA 1,666 LoC) get migrated.

**Scope landed:**
- [x] **`backend/inventory_testing_engine.py`** — new `InventoryTestingEngine(AuditEngineBase)` class added below the module-level helpers. Abstract methods delegate: `detect_columns` → `detect_inv_columns`, `apply_column_overrides` → loop over `_INV_OVERRIDABLE_COLUMNS`, `parse_data` → `parse_inv_entries`, `run_quality_checks` → `assess_inv_data_quality`, `run_tests` → `run_inv_test_battery(entries, self.config)`, `compute_score` → `calculate_inv_composite_score`, `build_result` → `InvTestingResult(...)`.
- [x] **`run_inventory_testing()` refactored** — body collapsed from ~38 lines of inline pipeline orchestration to 3 lines: `engine = InventoryTestingEngine(config); result = engine.run_pipeline(...); return result`. Caller-facing signature and behavior unchanged.
- [x] **`backend/tests/test_engine_base_lint.py` updated** — `TestKnownMigrated` renamed to `test_known_migrated_engines_not_in_findings` and asserts inventory is on-pattern alongside JE/AP/Payroll. `test_sprint_727_migration_targets_still_in_findings` now lists the four remaining targets (ar_aging, fixed_asset, revenue, sod).
- [x] **ADR-013 updated** with Phase 2a section recording the inventory migration as the pattern-validating shake-down.

**Behavioral parity:** Implicit by construction. The subclass methods call the SAME module-level helpers the procedural function used; no logic moved or changed. The existing 172-test inventory suite (`tests/test_inventory_testing.py` + `tests/test_inventory_testing_memo.py`) is the parity gate — it passes unchanged.

**Recurrence prevention (the durable artifact):**
1. **Migration pattern documented in ADR-013 Phase 2a** — future migrations follow the same shape: subclass + delegate + refactor entry. The pattern is concrete, not abstract.
2. **Lint count ratchet** — Sprint 727 set the post-triage finding count to 9; Sprint 727a brings it to 8. Each subsequent migration drops the count by 1. The `test_post_triage_finding_count` 5-12 range still passes (no false-failure on the migration), but the trend is visible.
3. **`test_known_migrated_engines_not_in_findings`** is now the canonical "engines on-pattern" list. Adding a new migration is a 1-line edit alongside the migration commit.

**Validation:**
- 172/172 inventory tests pass (parity gate)
- 16/16 lint tests pass with updated assertions
- Lint output: 9 → 8 findings (only the 4 remaining migration targets + 4 borderline)
- Behavioral parity by construction (subclass delegates to unchanged helpers)

**Lesson tie-in:** The "subclass delegating to existing helpers" pattern is the cheapest possible migration — no new logic, no parity-test fixture authoring needed because the existing test suite IS the parity gate. This makes the remaining 4 migrations tractable: each one is "add subclass + refactor entry" rather than "rebuild engine."


---

### Sprint 727: AuditEngineBase Migration — Phase 1.5 (per-engine triage)
**Status:** COMPLETE 2026-04-26 — re-scoped from "Phase 2 + lint promotion" to "triage + blocklist" once Sprint 726 surfaced 16 candidates and the per-engine review confirmed many genuinely don't fit `AuditEngineBase`.
**Priority:** P2 (architectural pre-requisite for actual migrations).
**Source:** Agent sweep 2026-04-24 punch list 3.1 + Sprint 726 ADR pre-requisite.

**Why re-scoped:** Sprint 726's ADR called out per-engine triage as a Sprint 727 pre-requisite. Doing the triage in its own sprint (rather than rushed inside the first migration) means each blocklist add lands as an audit-reviewable PR with rationale, and the migration backlog shrinks to its honest size before the per-engine migrations start.

**Scope landed:**
- [x] **Per-engine review of all 16 lint-flagged engines** against the 10-step `AuditEngineBase` pipeline shape (detect columns → parse → quality → tests → score → result with composite_score + flagged_entries).
- [x] **`scripts/lint_engine_base_adoption.py::NON_TESTING_ENGINES`** extended with 7 Sprint-727-classified blocklist entries with per-engine rationale comments:
  - `accrual_completeness_engine.py` — descriptive metrics + run-rate comparison; no test battery
  - `cash_flow_projector_engine.py` — 30/60/90-day deterministic forecast (calculator)
  - `expense_category_engine.py` — ISA 520 expense decomposition into ratios; analytical
  - `lease_accounting_engine.py` — ASC 842 classification + amortization (calculator)
  - `lease_diagnostic_engine.py` — four presence/absence checks; no scoring or flagging
  - `loan_amortization_engine.py` — period-by-period schedule generator (pure calculator)
  - `population_profile_engine.py` — descriptive stats (mean/median/Gini/Benford); aggregator
- [x] **`scripts/lint_engine_base_adoption.py::BORDERLINE_ENGINES`** new set documenting 4 engines that produce some testing-shaped output but require per-engine design decisions before migration: `ratio_engine.py`, `sampling_engine.py`, `three_way_match_engine.py`, `w2_reconciliation_engine.py`. Surfaced in findings (so they can't be silently forgotten); not in blocklist (so they can't be silently dismissed).
- [x] **`backend/tests/test_engine_base_lint.py`** — added 4 Sprint 727 triage-outcome tests in new `TestSprint727Triage` class: blocklist additions present, migration targets still in findings, borderline engines in findings but not blocklist, post-triage finding count in expected range (5–12). Tests bite if a future PR removes a blocklist entry without re-classifying or silently adds a new off-pattern engine.
- [x] **ADR-013 updated** with Phase 1.5 section recording the triage outcome (5 migration targets, 7 blocklist adds, 4 borderline).

**Migration backlog after triage (the honest list):**
1. `revenue_testing_engine.py` (2,509 LoC) — agent-sweep top priority
2. `ar_aging_engine.py` (2,179 LoC)
3. `fixed_asset_testing_engine.py` (1,666 LoC)
4. `inventory_testing_engine.py` (1,534 LoC)
5. `sod_engine.py` (452 LoC) — smallest, possibly first as a shake-down

Each of these is a follow-up sub-sprint with synthetic-TB parity fixtures + the migration. Numbered as 727a, 727b, ... in the schedule.

**Recurrence prevention (the durable artifact):**
1. **Triage decisions are tested, not just commented** — `test_sprint_727_blocklist_additions` and `test_borderline_engines_in_findings_not_blocklist` make the classification a contract. A future "let's clean up the blocklist" PR has to update the tests, making the rationale explicit.
2. **Post-triage count test (5–12 range)** catches drift in either direction: a migration drops the count (good), but a new off-pattern engine bumps it back up (bad without intent). The flexible range absorbs noise without losing visibility.
3. **`BORDERLINE_ENGINES` set is in code** — visible in the lint output's secondary roadmap. Forces the per-engine decision to land as a code change rather than a Slack thread.

**Out of scope:**
- **Lint exit-code promotion to error.** Now belongs in a Sprint 727a once the first real migration lands. The pre-triage 16-engine count was too high to flip the gate (would have blocked unrelated PRs); 9 is still too high. Promote when the count gets to ~3 (only borderline engines remain, and those require design discussion not blocking).
- **Actual engine migrations.** Each is a sub-sprint per the ADR. Sprint 727a (next) picks `sod_engine.py` (smallest at 452 LoC) as a shake-down migration to validate the parity-fixture pattern before the bigger engines land.
- **w2_reconciliation_engine classification finalization.** Default-classified as borderline; full review deferred to its migration sub-sprint.

**Validation:**
- Lint output dropped from 16 → 9 findings (5 migration targets + 4 borderline)
- 16/16 lint-script tests pass (12 from Sprint 726 + 4 new Sprint 727 triage tests)
- A synthetic blocklist-removal change (manually deleting `accrual_completeness_engine.py` from `NON_TESTING_ENGINES`) fails `test_sprint_727_blocklist_additions` as expected
- ADR-013 records the triage outcome alongside the original migration plan

**Lesson tie-in:** Same shape as Sprint 723 (foundational sprint that ships the gate before the work) and Sprint 726 (Phase 1 lint before Phase 2 migrations). Establishing the boundary is itself a deliverable; the migration cadence becomes tractable once the boundary exists. Re-scoping a sprint mid-flight (from "do the migration" to "do the triage that the migration needs") is the right call when the originally-planned scope wasn't actually doable in one commit.


---

### Sprint 731: Dependency Hygiene Cadence
**Status:** COMPLETE 2026-04-25 — agent-sweep wave 11, the dependency-cadence policy + first execution.
**Priority:** P2 (security-relevant patches available since 2026-04-22; first-execution-of-policy doubles as the policy validation).
**Source:** Agent sweep 2026-04-24, Tier 5 + Project Auditor security-patch flag.

**Problem class:** Two security-relevant updates (fastapi 0.136.0 → 0.136.1 patch, stripe 15.0.1 → 15.1.0 minor) had been available since 2026-04-22 with no movement. Dependency Sentinel surfaced them as YELLOW; the existing process treated YELLOW as "fyi" rather than "act," so security-relevant updates accumulated without deadline pressure.

**Scope landed:**
- [x] **Bumped fastapi 0.136.0 → 0.136.1** in `backend/requirements.txt` (the 7-day-deadline patch).
- [x] **Bumped stripe 15.0.1 → 15.1.0** in `backend/requirements.txt` (the 14-day-deadline minor).
- [x] **Verified bumps with regression run** — 145/145 billing + health + csv-export tests pass under the new pins.
- [x] **`docs/03-engineering/dependency-policy.md`** — cadence-window policy with detection sources, sentinel deadline gate, auto-PR (Dependabot) configuration reference, calendar-versioned soak rule, sprint-close hook, and explicit anti-patterns ("It's working in prod, why upgrade?").
- [x] **Dependency Sentinel deadline gate** in `scripts/overnight/agents/dependency_sentinel.py`:
  - New `CADENCE_DAYS = {"patch": 7, "minor": 14}` mapping (majors stay deadline-free; scheduled sprint work).
  - `_load_first_seen()` / `_save_first_seen()` round-trip the `dependency_sentinel.first_seen` map through `BASELINE_FILE`. Preserves other baseline sections (e.g., `coverage_sentinel.history`).
  - `_update_first_seen()` stamps new entries with today's date, prunes entries for packages no longer outdated, and attaches `first_seen` / `days_outdated` / `past_deadline` metadata to each watchlist package.
  - `_is_past_deadline(severity, first_seen_iso)` returns True when the cadence window is exceeded for the package's severity class. Invalid dates / missing severities return False (conservative default).
  - `run()` flips status to RED when any past-deadline watchlist package is detected (alongside the existing major-security RED path).
- [x] **`scripts/overnight/tests/test_dependency_sentinel_deadline.py`** — 13 tests: 6 cover `_is_past_deadline` (under/over 7d patch, under/over 14d minor, major no-deadline, invalid date), 3 cover the first_seen round-trip (save/load, missing-baseline empty, preserves other sections), 4 cover `_update_first_seen` (new stamping, known reuse, full pruning, partial pruning).
- [x] **Existing `.github/dependabot.yml` retained** — already configured (Sprint T1) with weekly pip + npm + github-actions schedules and minor-and-patch grouping. Policy doc references it rather than overwriting; Sprint 731 didn't touch the file.

**Recurrence prevention (the durable artifact):**
1. **`first_seen` state lives in the same baseline.json as coverage history** — same persistence shape, same write-preserves-other-sections discipline. A future sprint that adds a third sentinel (e.g., licence audit) plugs into the same baseline without colliding.
2. **Deadline gate flips status mechanically** — the moment a watchlist package crosses 7d (patch) or 14d (minor), the nightly job goes RED. No human discretion in the loop; "FYI" cannot persist past the deadline.
3. **Test fixture pins both windows** — `_is_past_deadline("patch", today-8d) is True` and `_is_past_deadline("minor", today-15d) is True` are committed test cases. A future "let's relax these to 30d" change has to break and update those tests, making the relaxation visible in the PR.
4. **Dates round-trip through baseline** — re-running the sentinel without a bump preserves the original `first_seen` date, so a deploy that happens to run the script late doesn't reset the clock. The 7d/14d window is real elapsed time, not "since we last looked."
5. **Auto-PR removes the cold-start cost of patch-bumping** — Dependabot opens the PR; the engineer's role is review + merge. The deadline forces the review to happen.

**Out of scope:**
- **A `routine` cadence (no-deadline) for non-watchlist deps** — left at the current "FYI on routine, deadline only on watchlist." Watchlist (`fastapi`, `stripe`, `pyjwt`, `cryptography`, `sqlalchemy`, `next`, `react`) covers the security-relevant surface; broadening to all packages would generate noise without adding signal.
- **Calendar-versioned package soak enforcement** — the policy doc describes the 30-day soak rule but the sentinel doesn't yet implement a soak-window check. Defer until a calendar-versioned package needs soak treatment in production.
- **Sprint-close hook for past-deadline awareness** — described in the policy doc §7 as a soft warning. Not implemented in Sprint 731; can be a small hotfix when the first warning would have been useful.

**Validation:**
- 13/13 deadline gate tests pass
- 145/145 billing + health + export-helper tests pass under the bumped fastapi 0.136.1 + stripe 15.1.0 pins
- Cadence policy doc committed; references the existing Dependabot config
- A synthetic past-deadline package (8 days old, patch severity) correctly produces `past_deadline=True` and would flip the sentinel to RED

**Lesson tie-in:** Closes the "this could be a recurring nag" gap that motivated several of the recent sprints. The pattern (state in baseline.json + windowed-comparison helper + AST/integration tests pinning the boundaries) is the same shape Sprint 723 used for coverage floors and Sprint 730 used for the Sprint Shepherd false-positive — once you have the shape, new gates are cheap to add.


---

### Sprint 730: Operational Observability Polish
**Status:** COMPLETE 2026-04-25 — agent-sweep wave 10, the operational-monitoring polish.
**Priority:** P2 (post-launch monitoring; closes the silent-failure gaps Guardian flagged).
**Source:** Agent sweep 2026-04-24, Tier 5 operational items.

**Problem class:** Several "silent failure" gaps where production state changes are not detectable until users complain. Each is small individually; together they leave gaps in the post-launch monitoring story. Sprint 730 closes the highest-yield 3 (Sprint Shepherd false-positive, Redis health probe, R2 health probe). The remaining 2 (R2 transient-vs-permanent in download(), lessons consolidation) are deferred — see Out of scope.

**Scope landed:**
- [x] **Sprint Shepherd risk-keyword regex fix** in `scripts/overnight/agents/sprint_shepherd.py`. Was substring match (`"TODO".lower() in c["message"].lower()`) which false-positived on `"fix: archive_sprints.sh ... (TODO list bug)"` (the canonical 2026-04-23 incident). Now uses `\b(WIP|TODO|...)\b` regex with word-boundary matching, AND skips conventional-commit prefixes (`fix:`, `chore:`, `docs:`, `style:`, `test:`, `build:`, `ci:`, `perf:`) since the prefix already pre-classifies intent.
- [x] **`scripts/overnight/tests/test_sprint_shepherd_regex.py`** — 13 regression tests: word-boundary matching (5 tests including punctuation boundaries + all 6 keywords), conventional-prefix skip (5 tests including the canonical 2026-04-23 commit message), edge cases (3 tests). Pins both the word-boundary fix and the prefix skip so a future "simplification" doesn't reintroduce either failure.
- [x] **`/health/redis` endpoint** in `backend/routes/health.py`. Soft-imports `redis`, calls `from_url(socket_timeout=2).ping()`. Returns 200 + `details.redis="not_configured"` when REDIS_URL unset (in-memory fallback is the intended degraded mode). Returns 200 + `connected` on success. Returns 503 + `DependencyStatus(status="unhealthy", details={"redis": "<exc_class_name>"})` on connection error. Catches all redis client exceptions broadly (the library raises many subclasses; per-class handling adds noise without value at the probe layer).
- [x] **`/health/r2` endpoint** — uses `export_share_storage.is_configured()` short-circuit when R2 env vars unset. When configured, calls S3-API `head_bucket` (canonical reachability + auth probe; doesn't list user data). Returns the same `healthy`/`unhealthy` shape as `/health/redis`. Distinguishes 200-with-honest-`unhealthy` (e.g., client init returned None) from 503-with-exception (connectivity failure).
- [x] **`backend/tests/test_health_redis_r2.py`** — 7 tests: not-configured paths (2), happy ping/head_bucket paths (2), 503 on connection error (2), 200-with-honest-unhealthy when client init returns None (1). Mocks `redis.from_url` and `export_share_storage._get_client` rather than spinning up real services.

**Recurrence prevention (the durable artifact):**
1. **Word-boundary regex + prefix skip = mechanical fix, not discipline-dependent** — the original substring match was a 1-line bug fixable in 1 line, but the *test* is the durable artifact: pinned commit messages (the canonical 2026-04-23 false-positive is a fixture) make the regression measurable. A future "simplification" back to substring match fails 13 tests at PR time.
2. **Health probes follow the existing `DependencyStatus` shape** — same response model as `/health/ready` so dashboards and uptime checks built against `/health/ready` work for the new probes without schema work.
3. **Probes are safe to invoke without auth** (rate-limited via `RATE_LIMIT_HEALTH`) so an external uptime monitor can hit them without managing tokens. The 503-on-failure semantics align with what most uptime providers expect.
4. **Honest reporting when configuration is incomplete** — the `client_not_initialized` path returns 200 with `details.status="unhealthy"` rather than 503. That distinction matters: a 503 should mean "transient outage, retry later"; an honest "we're misconfigured" should be visible in the dashboard but not page oncall.

**Out of scope (deferred to follow-up sprints):**
- **R2 transient-vs-permanent distinction in `export_share_storage.download()`** — currently returns `None` on any failure (collapses 404 + 5xx). The fix involves changing the return type to a Result-like or raising typed exceptions, plus updating route handlers to map 404→410 and 5xx→503. Multi-touchpoint refactor; deferred to a sprint that can isolate it. Current behavior is conservative (clients see "missing" rather than "broken") — operationally OK for now.
- **Lessons consolidation** — `tasks/lessons.md` is 1,063 lines; consolidating the three "verify against the live system" entries into one canonical lesson + a 4-line sprint-close checklist needs a careful read of the existing entries to preserve nuance. Not safely doable in-session under the current budget. Deferred to a hotfix-class commit later.

**Validation:**
- 13/13 sprint shepherd regex tests pass
- 7/7 new health probe tests pass
- 74/74 broader sweep pass (Sprint 722-730 tests + existing health tests)
- `/health/redis` and `/health/r2` smoke-test imports cleanly (FastAPI route registration succeeds)

**Lesson tie-in:** Same shape as Sprint 722's memo memory probe — the probe lives at the chokepoint (a single endpoint), exception-classes are stringified by class-name (no per-class handling), and the test mocks the dependency rather than spinning up the real one. The Sprint Shepherd fix continues the Sprint 717 SSOT pattern (the test fixture *is* the canonical false-positive commit message).


---

