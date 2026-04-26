# Paciolus Development Roadmap

> **Protocol:** See [`tasks/PROTOCOL.md`](PROTOCOL.md) for lifecycle rules, post-sprint checklist, and archival thresholds.
>
> **Completed eras:** See [`tasks/COMPLETED_ERAS.md`](COMPLETED_ERAS.md) for all historical phase summaries.
>
> **Executive blockers:** See [`tasks/EXECUTIVE_BLOCKERS.md`](EXECUTIVE_BLOCKERS.md) for CEO/legal/security pending decisions.
>
> **CEO actions:** All pending items requiring your direct action are tracked in [`tasks/ceo-actions.md`](ceo-actions.md).

---

## Hotfixes

> For non-sprint commits that fix accuracy, typos, or copy issues without
> new features or architectural changes. Each entry is one line.
> Format: `- [date] commit-sha: description (files touched)`

- [2026-04-24] record Sprint 716 COMPLETE — PR #103 merged as `6802bd63`, Render auto-deploy landed 12:51 UTC, Loki Logs Explorer confirmed 40 ingested lines with correct labels, all 6 saved queries authored. Runbook (`docs/runbooks/observability-loki.md`) §4 LogQL corrected to reflect what actually works against our ingested streams (line-filter + `| json | level="…"` instead of indexed-label selectors for level/logger, since Grafana Cloud's ingest layer doesn't index those at our volume). Lesson captured in `tasks/lessons.md` about verifying deployed code before debugging runtime (I burned ~15 min on label hypotheses before discovering the commit was local-only and Render was still running Sprint 713's image). Files: `tasks/todo.md`, `tasks/lessons.md`, `docs/runbooks/observability-loki.md`.
- [2026-04-23] archive_sprints.sh number-extraction fix + archive of Sprints 673–677 — replaced broken grep-pipeline (which filtered to Status lines first, losing the Sprint number on the preceding header) with an awk block that pairs each `### Sprint NNN` header to its Status body and emits the number when COMPLETE. Dry-run confirmed extraction (673, 674, 675, 676, 677); archival produced `tasks/archive/sprints-673-677-details.md` (142 lines, 5 sprint bodies) and reduced Active Phase to just Sprint 611 (PENDING). Unblocks Sprint 689a's `Sprint 689a:` commit under the archival gate. Files: `scripts/archive_sprints.sh`, `tasks/todo.md`, `tasks/archive/sprints-673-677-details.md`.
- [2026-04-23] Sprint 689 Path B decision — CEO chose full expansion (all 6 hidden backend tools + Multi-Currency standalone → 18-tool catalog). Execution split into 689a–g (one tool per session, single marketing-flip at 689g). Defaults rejected on evidence that the 6 routes carry ~4,500 LoC of real engine code + tests. Plan + deliverables template captured in Sprint 689 entry. Pre-requisite flagged: `scripts/archive_sprints.sh` grep-pipeline bug must be fixed (or sprints 673–677 manually archived) before the first `Sprint 689a:` commit can clear the archival gate.
- [2026-04-23] R2 provisioning — Cloudflare R2 buckets `paciolus-backups` + `paciolus-exports` (ENAM, Standard, private), two Account API tokens (Object R&W, per-bucket scoped). 8 env vars wired on Render `paciolus-api` (`R2_{BACKUPS,EXPORTS}_{BUCKET,ENDPOINT,ACCESS_KEY_ID,SECRET_ACCESS_KEY}`) — 19→27 vars, deploy live in 1 min, zero service disruption (9× /health all 200 <300ms). Unblocks Sprint 611 ExportShare migration + Phase 4.4 pg_dump cron. Mid-provisioning incident: screenshotted Render edit form while EXPORTS credentials were unmasked → rolled `paciolus-exports-rw` token before saving, only uncompromised values persisted. Full pattern captured in `tasks/lessons.md` (2026-04-23 entry). Details in `tasks/ceo-actions.md` "Backlog Blockers" section.
- [2026-04-23] d74db7c: record Sprint 673 COMPLETE — DB_TLS_OVERRIDE removed from Render prod, 2026-05-09 fuse cleared (tasks/todo.md, tasks/ceo-actions.md)
- [2026-04-22] b0ddbf6: dep hygiene + Sprint 684 tail — 3 backend pins bumped (uvicorn 0.44.0→0.45.0, pydantic 2.13.2→2.13.3, psycopg2-binary 2.9.11→2.9.12), 3 backend transitives refreshed in venv (idna 3.11→3.13, pydantic_core 2.46.2→2.46.3, pypdfium2 5.7.0→5.7.1), mypy dev-pin bumped 1.20.1→1.20.2; 4 frontend caret pins bumped (@typescript-eslint/eslint-plugin + parser ^8.58.0→^8.59.0, @tailwindcss/postcss + tailwindcss ^4.2.2→^4.2.4). Sprint 684 deferred memo-copy item landed: `sampling_memo_generator.py` Expected Misstatement Derivation section now cites AICPA Audit Sampling Guide Table A-1 explicitly. Backend `pytest` 8046 passed / 0 failed; frontend `jest` 1887 passed / 0 failed; `npm run build` clean.
- [2026-04-22] nightly audit artifacts — 2026-04-22 batch (original RED report + 4 sentinel JSONs + run_log). Preserved as historical evidence of the false-green incident that motivated Sprint 712. `.qa_warden_2026-04-22.json`, `.coverage_sentinel_2026-04-22.json`, and `.baseline.json` were committed in Sprint 712 (5d29cce) with the post-fix genuine-green values.
- [2026-04-21] 9820bb2: nightly audit artifacts — 2026-04-19, 2026-04-20, 2026-04-21 batch. Commits daily report .md + 6 sentinel JSONs + run_log per day, plus .baseline.json update to capture the Sprints 677–710 test-count growth (8028 backend / 1845 frontend).
- [2026-04-19] 9f00070: nightly dep hygiene (part 2) — remaining 3 majors cleared in venv (numpy 1.26→2.4, pip 25.3→26.0.1, pytz 2025.2→2026.1.post1). Verified zero direct imports for numpy/pytz; pandas 3.0.2 compatible with numpy 2.x; pytz has no current dependents. pytest 7836 passed / 0 failed. Venv-only change (no requirements.txt edits needed).
- [2026-04-19] 8fd93bb: nightly dep hygiene — 26 safe package bumps (19 backend venv: anthropic, anyio, docstring_parser, greenlet, hypothesis, jiter, librt, lxml, Mako, mypy, packaging, prometheus_client, pypdf, pypdfium2, pytest, python-multipart, ruff, sentry-sdk, uvicorn; 6 frontend via npm update: @sentry/nextjs, eslint-plugin-react-hooks, @typescript-eslint/*, postcss, typescript). Deferred: numpy 2.x, pip 26, pytz 2026 (majors). frontend/package-lock.json only.
- [2026-04-18] 7915d77: nightly audit artifacts — commit 2026-04-18 report + sentinel JSONs (qa_warden, coverage, dependency, scout, sprint_shepherd, report_auditor) + run_log (reports/nightly/)
- [2026-04-16] 22e16dc: backlog hygiene — Sprint 611 R2/S3 bucket added to ceo-actions Backlog Blockers; Sprint 672 placeholder for Loan Amortization XLSX/PDF export (Sprint 625 deferred work)
- [2026-04-14] a32f566: hallucination audit hotfix — /auth/refresh handler 401→403 for X-Requested-With mismatch (aligns with CSRF middleware); added .claude/agents/LLM_HALLUCINATION_AUDIT_PROMPT.md
- [2026-04-07] 73aaa51: dependency patch — uvicorn 0.44.0, python-multipart 0.0.24 (nightly report remediation)
- [2026-04-06] 39791ec: secret domain separation — AUDIT_CHAIN_SECRET_KEY independent from JWT, backward-compat verification fallback, TLS evidence signing updated
- [2026-04-04] 29f768e: dependency upgrades — 14 packages updated, 3 security-relevant (fastapi 0.135.3, SQLAlchemy 2.0.49, stripe 15.0.1), tzdata 2026.1, uvicorn 0.43.0, pillow 12.2.0, next watchlist patch
- [2026-03-26] e04e63e: full sweep remediation — sessionStorage financial data removal, CSRF on /auth/refresh, billing interval base-plan fix, Decimal float-cast elimination (13 files, 16 tests added)
- [2026-03-21] 8b3f76d: resolve 25 test failures (4 root causes: StyleSheet1 iteration, Decimal returns, IIF int IDs, ActivityLog defaults), 5 report bugs (procedure rotation, risk tier labels, PDF overflow, population profile, empty drill-downs), dependency updates (Next.js 16.2.1, Sentry, Tailwind, psycopg2, ruff)
- [2026-03-21] 8372073: resolve all 1,013 mypy type errors — Mapped annotations, Decimal/float casts, return types, stale ignores (#49)
- [2026-03-20] AUDIT-07-F5: rate-limit 5 unprotected endpoints — webhook (10/min), health (60/min), metrics (30/min); remove webhook exemption from coverage test
- [2026-03-19] CI fix: 8 test failures — CircularDependencyError (use_alter), scheduler_locks mock, async event loop, rate limit decorators, seat enforcement assertion, perf budget, PG boolean literals
- [2026-03-18] 7fa8a21: AUDIT-07-F1 bind Docker ports to loopback only (docker-compose.yml)
- [2026-03-18] 52ddfe0: AUDIT-07-F2 replace curl healthcheck with python-native probe (backend/Dockerfile)
- [2026-03-18] 5fc0453: AUDIT-07-F3 create /app/data with correct ownership before USER switch (backend/Dockerfile)
- [2026-03-07] fb8a1fa: accuracy remediation — test count, storage claims, performance copy (16 frontend files)
- [2026-02-28] e3d6c88: Sprint 481 — undocumented (retroactive entry per DEC F-019)

---

## Deferred Items

| Item | Reason | Source |
|------|--------|--------|
| Preflight cache Redis migration | In-memory cache is not cluster-safe; will break preview→audit flow under horizontal scaling. Migrate to Redis when scaling beyond single worker. | Security Review 2026-03-24 |
| `PeriodFileDropZone.tsx` deferred type migration | TODO open for 3+ consecutive audit cycles. Benign incomplete type migration, not a hack. Revisit when touching the upload surface for another reason. | Project-Auditor Audit 35 (2026-04-14) |
| `routes/billing.py::stripe_webhook` decomposition (signature-verify / dedup / error-mapping triad) | Already touched lightly in the 2026-04-20 refactor pass; full extraction pairs better with the deferred webhook-coverage sprint flagged in Sprint 676 review (handler is currently exercised by 6 route-test files but lacks unit coverage). Bundle both then. | Refactor Pass 2026-04-20 |
| `useTrialBalanceUpload` decomposition into composable hooks | Hook's state machine (progress indicator, recalc debounce, mapping-required preflight handoff) is tightly coupled to consumer semantics. Not a drop-in extraction — needs Playwright coverage of the mapping-required flow before a split is safe. | Refactor Pass 2026-04-20 |
| Move client-access helpers (`is_authorized_for_client`, `get_accessible_client`, `require_client`) out of `shared/helpers.py` shim | Three helpers depend on `User` / `Client` / `OrganizationMember` / `require_current_user`; a dedicated `shared/client_access.py` module isn't justified under the "prefer moving code, avoid new abstractions" guidance. Revisit if a fourth helper joins them, or if the shim grows another responsibility. | Refactor Pass 2026-04-20 |
| `routes/auth_routes.py` cookie/CSRF helper extraction | Module is already reasonably thin; cookie/token primitives (`_set_refresh_cookie`, `_set_access_cookie`, etc.) are security-critical. Touching them without a specific bug or audit finding is net-negative. Revisit only if a follow-up auth/CSRF audit produces an actionable finding. | Refactor Pass 2026-04-20 |

---

## Active Phase
> **Launch-readiness Council Review — 2026-04-16.** 8-agent consensus: code is launch-ready; gating path is CEO calendar (Phase 3 validation → Phase 4.1 Stripe cutover → legal sign-off). **Recommended path: ship on ~3-week ETA** with two engineering amendments — Sprint 673 below removes the 2026-05-09 TLS-override fuse before it collides with launch week, and Guardian's 5-item production-behavior checklist runs in parallel with Phase 3/4.1 (tracked in [`ceo-actions.md`](ceo-actions.md) "This Week's Action Map"). Full verdict tradeoff map in conversation transcript.
> **Prior sprint detail:** All pre-Sprint-673 work archived under `tasks/archive/`. See [`tasks/COMPLETED_ERAS.md`](COMPLETED_ERAS.md) for the era index and archive file pointers.
> **CEO remediation brief 2026-04-15** — Sprints 665–671 cleared the blocking TB-intake issues from the six-file test sweep. Sprints 668–671 remaining pending items archived alongside — no longer blocking launch.
> Sprints 673–677 archived to `tasks/archive/sprints-673-677-details.md`.
> Sprint 611 + Sprints 677–714 archived 2026-04-24 to `tasks/archive/sprints-611-714-details.md` (eight post-Sprint-673 batches: Post-Audit Remediation, Anomaly Framework Hardening, Security Hardening Follow-Ups, Design Refresh, Production Bug Triage, Nightly Agent Remediation, Branding Coverage Completion, P2 Sentry Sweep). Only Sprint 715 remains pending.
> Sprints 716–720 archived to `tasks/archive/sprints-716-720-details.md`.
> Sprints 721–725 archived to `tasks/archive/sprints-721-725-details.md`.

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

### Sprint 728: ISA 520 Expectation-Formation Workflow
**Status:** PENDING — feature-shaped; CPA retention concern, not a launch blocker.
**Priority:** P3 (post-launch product gap; differentiator).
**Source:** Agent sweep 2026-04-24, punch list 4.1 + Accounting Methodology Audit.

**Scope:**
- New engagement-layer entity `AnalyticalExpectation` with: procedure target (account/balance/ratio), expected value, expected range / precision threshold, corroboration basis (free text + structured tags: industry data, prior period, budget, regression model), CPA notes.
- Wire into flux, ratio, and multi-period TB tools so the tool prompts (or reads pre-supplied) expectations. Tool output flags variance > precision threshold.
- New memo generator `analytical_expectation_memo_generator.py` producing the expectation workpaper.
- Engagement-completion-gate update: any engagement that used analytical procedures as primary substantive evidence requires expectations on file.
- Documentation: `docs/04-compliance/isa-520-coverage.md`.

**Effort estimate:** Feature-sized — model + migration + 3 tool integrations + memo generator + completion gate update + tests. Realistically 2–3 sub-sprints.

**Why pending:** Not a launch blocker (no current customer is doing primary-substantive analytics). Closes a methodology gap CPAs will hit when completing engagements; the platform can ship without it but loses points on the "complete vs scratch-built" comparison.

**Pre-requisites:**
- Engagement layer is stable (✅ already shipped).
- Pattern from Sprint 728 carries forward to Sprint 729 (SUM schedule) — designing the entity API + memo template once benefits both.

---

### Sprint 729: ISA 450 Summary of Uncorrected Misstatements (SUM) Schedule
**Status:** PENDING — feature-shaped; CPA retention concern, not a launch blocker.
**Priority:** P3 (post-launch product gap; differentiator).
**Source:** Agent sweep 2026-04-24, punch list 4.2 + Accounting Methodology Audit.

**Scope:**
- New engagement-layer entity `UncorrectedMisstatement`: source (adjusting entry passed / sample projection / known error), amount, account(s) affected, classification (factual / judgmental / projected), F/S impact, materiality assessment.
- SUM schedule view in the engagement layer — auto-aggregates from `AdjustingEntry` (status=passed), `SampleProjection` (UEL > tolerable), and CPA-entered known errors.
- Materiality comparison surface: SUM aggregate vs engagement materiality (set at planning), with bucket: clearly trivial / immaterial / approaching material / material.
- New memo generator `sum_schedule_memo_generator.py` producing the SUM workpaper for archival.
- Engagement completion-gate update: completion requires SUM review on file (CPA marks each item as "auditor proposes correction" or "auditor accepts as immaterial").

**Effort estimate:** Feature-sized — model + migration + aggregation logic + materiality comparison UI + memo generator + completion gate update + tests. Realistically 2–3 sub-sprints, similar to Sprint 728.

**Why pending:** Same shape as Sprint 728 — methodology gap that hurts CPA retention but doesn't block launch. Every engagement-completing CPA reaches for the SUM and finds nothing today; the gap is real but bounded.

**Pre-requisites:**
- Adjusting entries (status=passed flow) — ✅ already shipped.
- Sampling UEL output — ✅ already shipped.
- Engagement-layer entity pattern from Sprint 728 reused.

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

### Sprint 715: SendGrid 403 root-cause investigation (24h post-deploy watch)
**Status:** PENDING — investigable starting **2026-04-25 ~14:29 UTC** (24h after Sprint 713 merge `2b92b771` on 2026-04-24 14:29 UTC).
**Priority:** P2 (observability follow-up — no user-facing impact, but worth knowing which recipient/path triggers the 403)
**Source:** Sprint 713 Bug C review — the fix caught the exception but did not investigate the root cause. The 403 means SendGrid is refusing a specific send; until we know *why*, users on the affected path silently never receive their email.

**Why pending (not "now"):** Sprint 713's warn-path (`log_secure_operation("email_error", f"SendGrid HTTPError status=403")`) is what makes the root cause investigable. We need 24h of production traffic with the new logs in place to see *which* send triggers the 403 and *how often*. Pre-deploy, we'd be guessing.

**Plan when triggered (CEO signal: if warn log count > 0 after 24h):**
- Pull Render logs for `"SendGrid HTTPError status=403"` over the post-deploy window. Identify the sender function (verification / password-reset / contact / email-change) and recipient masking pattern.
- Check SendGrid Dashboard → Suppressions → Blocks / Bounces / Spam Reports for the 403 recipients. Most likely cause: addresses on the global bounce list from the pre-Domain-Authentication era (SendGrid carried the `@gmail.com` bounce history into the paciolus.com domain).
- Check SendGrid API key scope on the Paciolus production key — `Mail Send: Full Access` is required; a read-only or Marketing-scoped key would 403 on transactional sends.
- Fix depends on finding: suppression-list cleanup (one-time; then add a `/admin/email-suppressions` endpoint to view current state), API key re-scope, or sender-domain re-verification.

**Out of scope:**
- Proactive suppression-list sync (would need a scheduled cron polling SendGrid API; not worth the infrastructure until we see meaningful 403 volume).
- Email deliverability SLA tracking (a separate observability sprint if Sentry breadcrumbs aren't sufficient).

---

