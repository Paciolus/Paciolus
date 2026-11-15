# Sprint Plan — Agent Sweep Remediation (2026-04-24)

**Purpose:** Convert the consolidated punch list (`reports/agent-sweep-consolidated-2026-04-24.md`) into discrete sprints with explicit recurrence-prevention. Each sprint has ONE prevention boundary so the same class of bug cannot silently return.

**Sprint design rules used:**
1. Group items by **prevention story**, not by file or by effort. A sprint should leave behind a guardrail (CI test, lint rule, runbook gate, or architectural invariant) that catches the problem next time.
2. Every fix lands with a **regression test** that would have caught it.
3. Every guardrail is **mechanical** (CI / hook / lint), not procedural ("remember to…").
4. Documentation drift is treated as a class of bug — fix the underlying coupling, don't manually re-sync.

**Sequencing principle:** Pre-Stripe-cutover sprints first (717–720), then pre-Phase-3-completion (721–722), then architectural cleanup while traffic is light (723–727), then post-launch product (728–729), then ongoing ops/hygiene (730–731). Time estimates omitted intentionally.

---

## Sprint 717 — Catalog & Citation Single-Source-of-Truth

**Origin:** Punch list 1.1, 1.2, 2.2 + Hallucination Audit + Accounting Methodology Audit.

**Problem class:** Stated truth in marketing/docs/memos drifts from actual code behavior. Today's symptoms are tool-count drift (12 vs 18 across 11 surfaces), the AS 1215 fabricated citation on 5 customer-facing files, and PR-T12/T13 missing from `PAYROLL_TEST_DESCRIPTIONS`. Each is a hand-maintained mirror of code state.

**Goal:** Eliminate the mirrors. Make every claim in marketing/docs/memos either (a) generated from code, or (b) verified against code by CI.

### Scope
- **Tool catalog single source.** Create `backend/tools_registry.py` that enumerates the 18 tools with: slug, display name, engine module, test count (computed from the engine's test list, not hand-typed), tier requirement, and citation list.
- **Generate `frontend/src/content/tool-ledger.ts` from registry** via a build-step or `scripts/generate_tool_ledger.py`. Tool counts, test counts, and tier badges all derive from one source.
- **Bump `CANONICAL_TOOL_COUNT`** to be a derived constant, not a hand-edited literal.
- **Citation registry.** `backend/standards_registry.py` lists every PCAOB AS / ISA / ASC / AICPA standard the platform actually cites, with the codepoint(s) where each is used. Marketing pages, Trust page, USER_GUIDE, and CLAUDE.md may cite only standards that appear in the registry.
- **Replace AS 1215 with AS 2401** in the 5 customer-facing surfaces; verify each by registry lookup, not text search.
- **Backfill PR-T12 and PR-T13 in `payroll_testing_memo_generator.py::PAYROLL_TEST_DESCRIPTIONS`.**
- **Sync `CLAUDE.md` "Key Capabilities"** + `memory/MEMORY.md` Project Status to derive from registry (or be checked against it).
- **Update `tasks/ceo-actions.md` Phase 3 checklist** to enumerate all 18 tools by name.

### Recurrence prevention (the work that ensures this never happens again)
1. **CI test `tests/test_catalog_consistency.py`:**
   - Reads `tools_registry.py`. Asserts every tool's `test_count` equals `len(engine.TESTS)` at runtime.
   - Asserts every test ID in every engine has a matching key in the corresponding memo's descriptions dict.
   - Asserts `tool-ledger.ts` is byte-identical to the generator output (i.e., committers cannot hand-edit it).
2. **CI test `tests/test_citation_consistency.py`:**
   - Reads `standards_registry.py`. Greps every customer-facing surface (`frontend/src/app/(marketing)/**`, `docs/07-user-facing/**`, `CLAUDE.md`, `frontend/src/content/standards-specimen.ts`, the trust page) for any `AS \d+` / `ISA \d+` / `ASC \d+` token. Fails if a cited standard is not in the registry.
3. **Pre-commit hook addition:** if any of `tool-ledger.ts`, marketing pricing/terms pages, or the trust page are staged but the registry is not, warn the committer to regenerate.
4. **`BANNED_PATTERNS` extension** in memo generators: literal "AS 1215" added as a banned token unless `# allow-citation: AS 1215` annotation is present (for legitimate retention-rule references, if they ever exist).
5. **Sprint-close template addition:** "registry diff reviewed; CI catalog tests green" checkbox.

### Definition of Done
- All 11 drift surfaces in 1.1 corrected; AS 1215 removed from 5 surfaces; PR-T12/T13 added to memo.
- Catalog and citation CI tests authored, green, and required-status on `main`.
- `tool-ledger.ts` and `tools-page.tsx` test counts derive from registry.
- A failing test exists demonstrating each guardrail's bite (i.e., temporarily flip a count → CI fails → revert).

### Acceptance evidence
- `git log` shows `tools_registry.py` and `standards_registry.py` introduced.
- CI run on a deliberately-bad-registry branch fails with the expected error message.
- `frontend/src/content/tool-ledger.ts` header comment says "GENERATED — do not edit by hand."

---

## Sprint 718 — Auth Surface Hardening + Cookie-Bearer Parity

**Origin:** Punch list 1.3, 2.4, 2.5, 2.6 + Security Review.

**Problem class:** Auth helpers were written assuming Bearer-token clients (the original CLI/test path), but the production browser path uses HttpOnly cookies. The mismatch surfaces as silently-degraded security guarantees.

**Goal:** Make every auth helper Bearer/cookie-symmetric by construction. Eliminate process-local auth state. Make admin recovery a tested feature.

### Scope
- **Fix `_extract_user_id_from_auth`** at `backend/security_middleware.py:485-509` to read `ACCESS_COOKIE_NAME` cookie when no `Authorization: Bearer` header is present.
- **Verify and document** every other auth-context-extracting function: `require_current_user`, `require_verified_user`, `get_current_user_optional`, CSRF token binding, audit-log user attribution, rate-limit keying, share-passcode IP throttle. Each must work for both Bearer and cookie clients.
- **Migrate `_ip_failure_tracker`** at `backend/security_middleware.py:619-674` from process-local `dict` to Redis (reuse `slowapi` storage URI). Per-IP throttle survives deploys and is shared across workers.
- **Collapse share-endpoint enumeration** at `backend/routes/export_sharing.py:471-481`: passcode-protected and unknown share tokens both return 404. Move "passcode required" signal to a separate authenticated probe endpoint.
- **Add admin lockout-recovery endpoint** `/admin/security/clear-throttle` (CEO-only): clears per-IP and per-token throttle counters for a specified key. Authenticated, audit-logged, rate-limited 1/min.

### Recurrence prevention
1. **CI test `tests/test_auth_parity.py`:** every auth-extracting helper is invoked twice per test, once with Bearer and once with cookie; both must yield identical user resolution. Parametrized over the full helper list.
2. **CI test `tests/test_no_process_local_auth_state.py`:** AST scan of `backend/security_middleware.py` and `backend/auth.py` for module-level mutable state (`dict`, `list`, `set`, `OrderedDict`). Allowlist any read-only constants. Fails on new mutable globals.
3. **CI test `tests/test_share_enumeration.py`:** asserts that every error response from `routes/export_sharing.py` for unknown / expired / passcode-required / IP-throttled / token-revoked tokens is byte-identical (modulo the response timing).
4. **Auth helper invariant added to `backend/auth.py` module docstring:** "Every helper must accept Bearer headers AND HttpOnly cookies. Adding a new helper without the symmetric path will fail `test_auth_parity.py`."
5. **Admin lockout-recovery is itself tested** — admin-recovery endpoint integration test in `test_admin_routes.py`.

### Definition of Done
- All 4 fixes landed, regression tests added, parity test green for the full helper list.
- A failing test demonstrating each guardrail (e.g., add a mutable global → `test_no_process_local_auth_state.py` fails).
- Runbook `docs/05-runbooks/admin-lockout-recovery.md` documents how to use the recovery endpoint.

### Acceptance evidence
- `tests/test_auth_parity.py` parametrize list includes every auth helper imported by any route.
- Redis `iptracker:*` keys visible in Upstash dashboard after a deliberate failed-login burst.

---

## Sprint 719 — Stripe Live-Mode Webhook Resilience

**Origin:** Punch list 1.5, 1.6, 3.4 + Guardian.

**Problem class:** The webhook handler is the single point where Stripe live-mode events become Paciolus state changes. Today it has 57.4% coverage, an off-by-one, and silent failure on misconfigured secret.

**Goal:** Make the webhook handler the most-tested file in the codebase. Make secret misconfiguration impossible to deploy. Make every event type idempotent and replay-safe.

### Scope
- **Fix off-by-one** at `backend/billing/webhook_handler.py:978`: `event_time < sub_updated` → `event_time <= sub_updated` with a fixture replay test for equal-time events.
- **Add startup secret validation:** on production boot, `STRIPE_WEBHOOK_SECRET` is ping-tested against Stripe's secret-format regex (`whsec_…`); a bare `whsec_test_…` secret in `production` mode hard-fails startup.
- **Cover every webhook event type the handler claims to handle:** `customer.subscription.created/updated/deleted`, `invoice.paid/payment_failed`, `customer.subscription.trial_will_end`, `charge.dispute.created/closed`, `customer.deleted`. One fixture-replay test per event type, including the "duplicate event" replay-safety case.
- **Webhook coverage floor:** raise `backend/billing/webhook_handler.py` to ≥80% in `coverage_sentinel`. Coverage floor is a CI-blocking check, not advisory.
- **Wire and verify Sentry alert** on the log message "Webhook signature verification failed."
- **Add 24h rolling 4xx-rate alert** on `/billing/webhook` at >5%. Tested by deliberately sending malformed signatures during a smoke window.
- **Pre-cutover smoke runner** `scripts/stripe_live_preflight.py`: invokes Stripe CLI to fire every event type once against the live endpoint and asserts each returns 200. Mandatory pre-cutover step in Phase 4.1.

### Recurrence prevention
1. **CI gate: webhook handler coverage ≥80%** is required-status. Drop below → red build.
2. **Idempotency contract test `tests/test_webhook_idempotency.py`:** every handler is invoked twice with identical event payload and identical event_id; the second invocation must produce zero state change. Parametrized over every supported event type.
3. **Equal-time guard test:** event_time == sub_updated must be processed exactly once, never both skipped and processed depending on race.
4. **Pre-cutover gate in `tasks/ceo-actions.md` Phase 4.1:** "preflight script run with all-200 output captured" is a checklist item, not optional.
5. **Sentry alert validation test** — an integration test that posts a malformed signature, then asserts the Sentry SDK was invoked with the expected error class. Catches alert regressions.
6. **Webhook secret format check at startup** — production env-var validation in `backend/config.py` with a hard-fail on test-prefix in prod mode.

### Definition of Done
- Webhook coverage ≥80% (currently 57.4%).
- Idempotency, off-by-one, secret-format CI tests added and green.
- `scripts/stripe_live_preflight.py` runnable against live mode; output captured in Phase 4.1 checklist as evidence.
- Sentry alert and 4xx-rate alert configured and verified in dashboard.

### Acceptance evidence
- Coverage report shows handler at ≥80%.
- Stripe CLI replay shows duplicate events produce no second state mutation.
- `STRIPE_WEBHOOK_SECRET=whsec_test_xxx ENV_MODE=production python -c "import backend.config"` exits non-zero.

---

## Sprint 720 — Multi-Worker State Discipline

**Origin:** Punch list 1.4 + Guardian.

**Problem class:** `bulk_upload.py` carries job state in a module-global `OrderedDict`, which works in a single worker but breaks under multi-worker Render. The class is "in-process state used in a request handler" — easy to introduce, hard to spot in review.

**Goal:** Move bulk-upload state to durable storage and make this entire class of bug mechanically catchable.

### Scope
- **Migrate `_bulk_jobs` and friends to Postgres.** New tables: `bulk_upload_jobs` (job_id, user_id, tier, created_at, expires_at, status, total_files, completed_files, error_summary) and `bulk_upload_files` (job_id, file_index, filename, status, finding_count, error). Eviction handled by a `cleanup_scheduler` job, not in-process LRU.
- **Replace `asyncio.create_task` fire-and-forget** with a queue-driven worker (Postgres-backed via `cleanup_scheduler` task table, or Redis queue if simpler). A worker recycle does not lose job state.
- **Multi-worker pytest harness** `tests/test_multiworker_bulk_upload.py`: spins up two FastAPI app instances against shared test Postgres, POSTs to A and polls from B, asserts state visible.
- **Document the invariant** — `docs/architecture/runtime-state.md` (new file) states: "Mutable runtime state lives in Postgres or Redis. Module-global mutable state in route handlers is forbidden."

### Recurrence prevention
1. **AST lint rule `scripts/lint_no_module_global_state.py`:** scans `backend/routes/**.py` and `backend/security_middleware.py` for module-level assignments to mutable types (`dict`, `list`, `set`, `OrderedDict`, `defaultdict`, `Lock`, `RLock`). Allowlist read-only constants by `Final[…]` annotation or all-caps name. Wired into `ci.yml` as a required check.
2. **CI test `tests/test_routes_multiworker_safe.py`:** loads each route module twice in separate processes, asserts no shared in-memory state observed.
3. **PR template addition:** "Does this change introduce in-process state? If yes, justify why Postgres/Redis is unsuitable."
4. **`scripts/find_module_global_state.py` runbook entry** — quick scan for periodic audits.

### Definition of Done
- Bulk upload survives a worker recycle and works on Render's multi-worker config.
- Multi-worker harness test green.
- Lint rule wired into CI; a deliberately-bad commit (re-add `_bulk_jobs = {}`) fails the lint check.
- ADR or runtime-state doc committed.

### Acceptance evidence
- Render deploy with `numInstances=2` (or `gunicorn workers=2`) accepting bulk-upload POSTs and serving status polls cross-worker.
- Lint rule output captures the historical bad pattern as a known violation if reintroduced.

---

## Sprint 721 — Memo Output Quality & ISA 265 Boundary

**Origin:** Punch list 2.3 + Accounting Methodology Audit.

**Problem class:** Memo generators contain language that drifts toward auditor-judgment territory (deficiency classification, misstatement conclusions). Today's `BANNED_PATTERNS` regex catches the hardest cases, but softer phrases slip through.

**Goal:** Make boundary phrasing mechanically detectable. Establish an "auditing lexicon" so future memo authors know what's safe.

### Scope
- **Rephrase `three_way_match_memo_generator.py`** to drop "systemic review of procure-to-pay controls recommended" → anomaly-indicator language ("match-rate threshold breached; auditor judgment required to determine cause").
- **Rephrase `ar_aging_memo_generator.py`** to drop "potential understatement of credit loss expense" → "aging-bucket distribution suggests further inquiry into credit-loss estimation."
- **Build `docs/03-engineering/auditing-lexicon.md`** with explicit allow/deny phrase list, organized by ISA/AS reference. Allow: "anomaly indicator," "data signal," "warrants inquiry," "threshold breached." Deny: "deficiency," "misstatement," "control failure," "should be," "recommended remediation."
- **Strengthen `BANNED_PATTERNS`** in memo generators to include the "soft" cases caught by the audit. Pattern list reviewed against the auditing lexicon's deny list.
- **Snapshot tests** for every memo generator: render against synthetic engagement fixtures, assert the rendered text contains zero banned-pattern hits.

### Recurrence prevention
1. **CI test `tests/test_memo_boundary_phrasing.py`:** every memo generator runs against a standardized synthetic engagement; the output text is grepped against the full deny list. Fails on any hit.
2. **Sprint-close template addition:** "memo language reviewed against auditing lexicon" checkbox for any sprint that touches a `*_memo_generator.py`.
3. **PR template gate:** PRs touching memo generators must link to the lexicon entry justifying any new phrase that pattern-matches the deny regex.

### Definition of Done
- Both flagged memo generators rephrased.
- Auditing lexicon committed.
- BANNED_PATTERNS regex extended; snapshot tests green for all 18 memo generators against synthetic fixtures.
- A deliberately-bad memo edit (insert "deficiency") fails CI.

### Acceptance evidence
- Diff of `BANNED_PATTERNS` + auditing-lexicon entries.
- CI run on a memo-edit branch with bad phrasing fails with the expected pattern hit.

---

## Sprint 722 — Memory Budget for Memo Generation

**Origin:** Punch list 2.1 + Guardian.

**Problem class:** ReportLab + openpyxl accumulate in RAM. On Render Standard 2 GB, generating 18 memos back-to-back risks OOM-killing the worker. The risk is invisible until production load hits it.

**Goal:** Establish and enforce a per-request memory budget; recycle workers before they breach it; regression-test the back-to-back path.

### Scope
- **Add `gc.collect()` between memo generations** in any handler that produces multiple memos sequentially (e.g., diagnostic-package ZIP generation).
- **Configure Render `maxRequestsPerWorker`** so workers recycle every N requests before pressure builds. N tuned via load test.
- **Add memory probe logging** at memo-generator boundaries: log RSS before and after each memo. Threshold-exceeded → Sentry warning.
- **Sentry alert on worker memory >85%** of dyno limit.
- **Memory regression test `tests/test_memo_generation_memory.py`:** generates all 18 memos sequentially in CI, fails if peak RSS exceeds budget (e.g., 1.2 GB headroom on Render's 2 GB).
- **Runbook `docs/05-runbooks/memory-pressure.md`:** how to read memory probe logs, what to do when the alert fires.

### Recurrence prevention
1. **Memory budget CI test** runs on every PR that touches `*_memo_generator.py`, `pdf/sections/**`, or `excel_generator.py`. Regression caught at PR time, not deploy time.
2. **Sentry alert wired and tested** with a deliberate memory burn fixture (only in staging).
3. **Runbook entry** in the memory-pressure doc points future engineers to the test and the alert.

### Definition of Done
- Memory regression test green; deliberately-bad change (remove `gc.collect`) fails the test.
- Render `maxRequestsPerWorker` set; deploy logs show worker recycling at expected cadence.
- Sentry alert configured and tested.

### Acceptance evidence
- CI artifact showing peak RSS per-memo over the 18-memo run.
- Render deploy log showing `maxRequestsPerWorker` recycling.

---

## Sprint 723 — Coverage Floor Enforcement (Foundational)

**Origin:** Punch list 3.5 + Guardian + Coverage Sentinel report.

**Problem class:** The 10 lowest-coverage files in the codebase are also the most production-critical (parsers, generators, webhook handler). Coverage degradation goes unnoticed because coverage_sentinel is informational, not blocking.

**Goal:** Establish per-file coverage floors for the high-risk files. Make sentinels blocking. Catch coverage regressions at PR time.

### Scope
- **Set per-file coverage floors** for the 10 lowest-coverage critical files:
  - `excel_generator.py` (45.7% → floor 70%)
  - `billing/webhook_handler.py` (57.4% → floor 80%, see Sprint 719)
  - `population_profile_memo.py` (39.7% → floor 70%)
  - `workbook_inspector.py` (18.6% → floor 75%) — first-touch on every upload, highest priority
  - `pdf/sections/diagnostic.py` (64.9% → floor 80%)
  - `leadsheet_generator.py` (11.4% → floor 75%)
  - `config.py` (54.5% → floor 75%)
  - `main.py` (44.2% → floor 70%)
  - `preflight_engine.py` (84.1% → floor 85%)
  - `routes/bulk_upload.py` (after Sprint 720) → floor 80%
- **Add backfill tests** for `workbook_inspector.py` adversarial inputs: password-protected xlsx, malformed ods, XML bombs, zip slip, corrupted CSV, Unicode normalization edge cases.
- **Add backfill tests** for `leadsheet_generator.py` style-collision path (`_register_styles` swallowing ValueError on duplicate NamedStyle — surface and fix).
- **Backfill tests** for the remaining 6 files following the same adversarial-fixture pattern.
- **Promote `coverage_sentinel`** from advisory nightly artifact to PR-blocking CI check. Floors stored in `coverage_floors.yaml`; lowering a floor requires CODEOWNERS approval.

### Recurrence prevention
1. **Coverage-floor CI gate:** any file in `coverage_floors.yaml` that drops below its floor fails CI. Lowering a floor requires a PR with explicit CODEOWNERS approval.
2. **Floor-list expansion gate:** a PR that adds a new high-risk module (parser, generator, webhook handler, route module) must add it to `coverage_floors.yaml`. Enforced by a CI script that diffs new module additions against the floor list.
3. **Adversarial fixture corpus** added to `backend/tests/fixtures/adversarial/` with a README pointing future authors to use it.

### Definition of Done
- 10 floors set; all 10 files at or above floor.
- `coverage_floors.yaml` is a required-status gate.
- A deliberately-bad PR (delete a test) fails CI with the expected floor-drop message.

### Acceptance evidence
- `coverage_floors.yaml` committed; CI run shows floor enforcement passing.
- Adversarial fixture corpus has at least 5 inputs per high-risk parser.

---

## Sprint 724 — `shared/helpers.py` Shim Removal

**Origin:** Punch list 3.2 + BackendCritic.

**Problem class:** A decomposition refactor (2026-04-20) split `helpers.py` into domain modules but left a 35-symbol re-export shim for backwards compatibility. 62 call sites still go through the shim vs 6 direct. The shim is winning because there is no mechanical pressure to migrate.

**Goal:** Delete the shim entirely. Make new shim imports impossible.

### Scope
- **Sweep all 62 call sites** and rewrite imports to point at the appropriate domain module.
- **Delete `backend/shared/helpers.py`** and its tests.
- **Verify private symbols (`_XLS_MAGIC`, `_parse_csv`, `_log_tool_activity`)** that were re-exported are now properly scoped to their owning module; if they had legitimate cross-module callers, promote them to public names in their owning module.

### Recurrence prevention
1. **Import-ban CI rule** in `pyproject.toml` (ruff `flake8-tidy-imports` or equivalent): `from backend.shared.helpers import …` is a hard error after the deletion. Catches accidental resurrection.
2. **CI test `tests/test_no_shared_helpers_import.py`:** AST scan of `backend/**.py` for `import backend.shared.helpers` or `from backend.shared.helpers`. Fails on any match.
3. **Architecture doc update:** `docs/03-engineering/module-boundaries.md` documents the domain-module pattern and explicitly notes that `shared/helpers.py` is deprecated forever.

### Definition of Done
- `backend/shared/helpers.py` deleted.
- All 62 call sites migrated and tests still green.
- Lint rule + AST test both fail on a deliberately-bad PR (re-add the shim).

### Acceptance evidence
- `git log -- backend/shared/helpers.py` ends with the deletion commit.
- `grep -r "shared.helpers" backend/ src/` returns zero matches.

---

## Sprint 725 — Export Endpoint Consolidation

**Origin:** Punch list 3.3 + BackendCritic.

**Problem class:** `routes/export_diagnostics.py` (689 LoC) has 7 copy-pasted CSV-writer endpoints. Sister `routes/export_testing.py` already collapsed the same pattern via `csv_export_handler()` (Sprints 218-219). Every bug fix or schema change today hits 7 sites in `export_diagnostics.py`.

**Goal:** Apply the existing `csv_export_handler()` pattern to `export_diagnostics.py`. Make the pattern mandatory for any future export route.

### Scope
- **Refactor `routes/export_diagnostics.py`** so all 7 CSV endpoints route through `csv_export_handler()`.
- **Golden-file test per endpoint** (snapshot of CSV output) so the refactor is byte-identical, not just behaviorally equivalent.
- **Promote `csv_export_handler()`** from `routes/export_testing.py` to `backend/shared/csv_export.py` if not already there, so both routers use the same canonical implementation.

### Recurrence prevention
1. **CI test `tests/test_export_routes_use_handler.py`:** AST scan of `backend/routes/export_*.py`. Any function-decorated-with-`@router.get` whose body does not call `csv_export_handler` (or other approved factory) fails the check.
2. **CODEOWNERS rule:** PRs touching `routes/export_*.py` require export-domain owner review; reduces "I'll just inline this one" drift.
3. **Architecture doc update:** `docs/03-engineering/export-pattern.md` describes the handler factory pattern; PR template asks "are you adding a new export endpoint? If so, why isn't it using `csv_export_handler`?"

### Definition of Done
- `routes/export_diagnostics.py` LoC reduced ~50%.
- Golden-file tests green; output byte-identical pre/post refactor.
- Lint rule fails on a deliberately-bad PR (inline a CSV writer).

### Acceptance evidence
- Diff shows 7 hand-written endpoints replaced by 7 calls to `csv_export_handler`.
- Golden-file fixture set committed.

---

## Sprint 726 — `AuditEngineBase` Migration, Phase 1 (Revenue, AR, FA, Inventory)

**Origin:** Punch list 3.1 + BackendCritic.

**Problem class:** `engine_framework.py` defines a clean 10-step pipeline ABC, but only 3 of 12 testing engines (JE, AP, Payroll) subclass it. The other 9 reimplement the pipeline as top-level `run_*()` procedural functions. Sprint 689 expanded the catalog to 18 tools while this fork was still open, so the inconsistency is now broader.

**Goal:** Convert the 4 largest off-pattern engines (Revenue, AR, FA, Inventory — combined ~7,800 LoC) onto `AuditEngineBase`. Establish a lint rule so the remaining 5 follow in Phase 2.

### Scope
- **Migrate Revenue, AR Aging, Fixed Assets, Inventory engines** to subclass `AuditEngineBase`.
- **Behavioral parity tests** for each: regression suite of synthetic TBs run against pre- and post-migration engine; output must match modulo dataclass field ordering.
- **Add `engine_base_lint.py`** that scans `backend/*_engine.py` and `backend/*_testing_engine.py` for top-level `run_*()` functions that should be class methods. Phase 1 wires it as a CI **warning** (not blocking) so the remaining 5 engines still build.
- **Phase 1 ADR `docs/03-engineering/adr-013-audit-engine-base.md`** explains the pattern, the migration approach, and the lint rule.

### Recurrence prevention
1. **`engine_base_lint.py`** as a CI warning in Phase 1. Promoted to error in Sprint 727 (Phase 2).
2. **Behavioral parity test pattern** documented; any future engine refactor must produce a parity test before being merged.
3. **PR template gate:** "Are you adding a new engine? Subclass `AuditEngineBase`."

### Definition of Done
- 4 engines migrated; parity tests green.
- Engine-base lint rule landed as warning.
- ADR committed.

### Acceptance evidence
- `git log` shows the 4 engine migrations as discrete commits (one per engine for bisect-friendliness).
- Parity test artifacts in CI runs.

---

## Sprint 727 — `AuditEngineBase` Migration, Phase 2 + Lint Promotion

**Origin:** Sprint 726 follow-on.

**Goal:** Migrate the remaining 5 off-pattern engines (3-way match, accrual completeness, population profile, sampling, cash flow projector) and promote the lint rule to error.

### Scope
- **Migrate the 5 remaining engines** following Sprint 726's pattern with parity tests for each.
- **Promote `engine_base_lint.py`** from CI warning to CI error.
- **Update ADR-013** to mark the migration complete.

### Recurrence prevention
1. **Lint rule promoted to error** — any future engine that does not subclass `AuditEngineBase` fails CI.
2. **Engine pattern is now load-bearing** — any new tool added to the catalog must follow it. Reinforces Sprint 717's catalog single-source.

### Definition of Done
- All 12 testing engines on `AuditEngineBase` (or 18 if Sprint 689's promoted tools count as engines — verify against `tools_registry.py`).
- Lint rule at error.
- ADR-013 marked complete.

### Acceptance evidence
- A deliberately-bad PR (top-level `run_*` engine function) fails CI with the lint error.

---

## Sprint 728 — ISA 520 Expectation-Formation Workflow

**Origin:** Punch list 4.1 + Accounting Methodology Audit.

**Problem class:** The platform's analytical procedures (flux, ratio, multi-period TB) produce observed-vs-prior comparisons. ISA 520.5(a) / AS 2305.10 require a **structured expectation with stated precision and corroboration basis** when analytics are used as a primary substantive procedure. CPAs intending to rely on flux/ratio output as their primary procedure evidence will hit this gap immediately.

**Goal:** Add an expectation-formation surface to the analytical tools that satisfies ISA 520. This is a feature-shaped product gap, not a bug.

### Scope
- **New engagement-layer entity `AnalyticalExpectation`:** procedure target (account/balance/ratio), expected value, expected range / precision threshold, corroboration basis (free text + structured tags: industry data, prior period, budget, regression model), CPA notes.
- **Wire into flux, ratio, and multi-period TB tools:** before running, the tool prompts (or reads pre-supplied) expectations. Tool output compares actual vs expected, flags variance > precision threshold.
- **New memo generator `analytical_expectation_memo_generator.py`** producing the expectation workpaper.
- **Engagement-completion-gate update:** any engagement that used analytical procedures as primary substantive evidence requires expectations to be on file.
- **Methodology gap closure** documented in `docs/04-compliance/isa-520-coverage.md`.

### Recurrence prevention
1. **Methodology coverage CI test** (extends Sprint 717's citation registry): any tool whose memo cites ISA 520 must have an expectation-input surface.
2. **Engagement completion gate test:** an engagement that used analytical tools as primary procedure but has no `AnalyticalExpectation` records fails the completion gate.

### Definition of Done
- Feature shipped; flux/ratio/multi-period prompt for or accept expectations.
- Memo generator outputs the expectation workpaper.
- Completion gate enforces expectation presence when applicable.

### Acceptance evidence
- End-to-end test: engagement using flux as primary procedure cannot reach completion without expectations on file.

---

## Sprint 729 — ISA 450 Summary of Uncorrected Misstatements (SUM) Schedule

**Origin:** Punch list 4.2 + Accounting Methodology Audit.

**Problem class:** ISA 450 / AU-C 450 requires a running SUM schedule consolidating passed adjustments + sample-projected misstatements + aggregate vs materiality. Today the platform has approval-gated adjusting entries and sampling UEL output, but no consolidation surface. Every CPA completing an engagement reaches for this and finds nothing.

**Goal:** Add the SUM consolidation surface. Wire into the engagement completion gate.

### Scope
- **New engagement-layer entity `UncorrectedMisstatement`:** source (adjusting entry passed / sample projection / known error), amount, account(s) affected, classification (factual / judgmental / projected), F/S impact, materiality assessment.
- **SUM schedule view** in the engagement layer that auto-aggregates from `AdjustingEntry` (status=passed), `SampleProjection` (UEL > tolerable), and CPA-entered known errors.
- **Materiality comparison surface:** SUM aggregate vs engagement materiality (set at planning), with bucket: clearly trivial / immaterial / approaching material / material.
- **New memo generator `sum_schedule_memo_generator.py`** producing the SUM workpaper for archival.
- **Engagement completion gate update:** completion requires SUM review on file (CPA marks each item as "auditor proposes correction" or "auditor accepts as immaterial").

### Recurrence prevention
1. **Engagement completion gate test:** an engagement with passed adjustments or sampling UEL output but no SUM review fails the gate.
2. **SUM aggregate sanity test:** if total SUM > materiality and engagement is marked complete, hard-error.

### Definition of Done
- Feature shipped; SUM aggregates from existing data sources automatically.
- Memo generator outputs the SUM workpaper.
- Completion gate enforces SUM review.

### Acceptance evidence
- End-to-end test: engagement with $X of passed adjustments and Y sample-projected misstatements produces SUM = X + Y in the workpaper.

---

## Sprint 730 — Operational Observability Polish

**Origin:** Punch list Tier 5 + Guardian post-launch monitoring gaps.

**Problem class:** Several "operational" gaps surfaced where production state changes are not detectable until users complain. Each is small individually; together they leave gaps in the post-launch monitoring story.

**Goal:** Close the four operational gaps with mechanical health checks and tested alerts.

### Scope
- **Redis (Upstash) blip detection:** add `/health/redis` ping endpoint; Sentry alert on `RedisStorage` exceptions (slowapi fail-open warning is currently silent).
- **R2 transient-vs-permanent distinction in `export_share_storage.download()`:** transient (5xx from R2 / connection error) → 503 to client; permanent (404) → 410 to client. Mass 410s currently look like permanent data loss.
- **`/health/r2` sentinel GET:** lightweight HEAD against a fixed sentinel object in `paciolus-exports`. Cron'd uptime check hits this.
- **Sprint Shepherd regex fix:** today's risk-signal regex matches the literal substring `TODO` even inside hotfix descriptions (false-positive on commit `a275fa58`). Tighten to require word-boundaries and exclude descriptions.
- **Lessons consolidation:** roll up the three Sprint 716-era "verify against live system" lessons (`tasks/lessons.md`) into one canonical lesson titled "Trust the live system over the documented contract." Add a 4-line verify-against-live checklist to the sprint-close template.

### Recurrence prevention
1. **Health-endpoint test pattern:** every `/health/*` endpoint has a dedicated integration test that simulates the failure mode and asserts the alert fires.
2. **Sprint Shepherd regex unit-test:** the false-positive commit message is committed as a fixture; regression test asserts no false positive.
3. **Sprint-close checklist** with the 4-line verify-against-live block; lessons.md no longer accumulates near-duplicates.

### Definition of Done
- All 4 health/alert gaps closed and tested.
- Sprint Shepherd no longer YELLOWs on hotfix descriptions containing "TODO."
- Three near-duplicate lessons consolidated.

### Acceptance evidence
- `/health/redis` and `/health/r2` documented in `docs/05-runbooks/health-endpoints.md`.
- A deliberately-flaky Redis simulation in staging triggers Sentry alert as expected.

---

## Sprint 731 — Dependency Hygiene Cadence

**Origin:** Punch list Tier 5 (security-relevant patches) + Project Auditor.

**Problem class:** Two security-relevant updates have been available since 2026-04-22 (fastapi 0.136.0 → 0.136.1 patch, stripe 15.0.1 → 15.1.0 minor). Today's nightly Dependency Sentinel is YELLOW. The current process treats sentinel YELLOW as "fyi" rather than "act."

**Goal:** Land the available patches and codify a cadence policy so security-relevant updates land within a fixed window.

### Scope
- **Patch fastapi 0.136.0 → 0.136.1, stripe 15.0.1 → 15.1.0** (with regression run).
- **Add cadence policy to `docs/03-engineering/dependency-policy.md`:**
  - Security-relevant patch (CVE-tagged or marked security-relevant by sentinel): land within **7 days** of detection.
  - Security-relevant minor: land within **14 days**.
  - Major dep upgrades: scheduled sprint, no deadline pressure.
  - Calendar-versioned packages (e.g., pdfminer.six): default 30-day soak before update.
- **Dependency Sentinel becomes blocking** for security-relevant items past the deadline. Prior to deadline, status is YELLOW; past deadline, RED → CI block.
- **Auto-PR bot** (Dependabot, Renovate, or a tiny GitHub Action) opens a PR per security-relevant update on detection, so the engineer step is review + merge, not authoring.

### Recurrence prevention
1. **Sentinel deadline gate** turns "fyi" into "deadline." Past deadline → CI red.
2. **Auto-PR removes the cold-start cost** of patch-bumping; the deadline forces review.
3. **Policy doc** is the canonical reference for "do I need to act on this dep?"

### Definition of Done
- Patches landed, regression green.
- Policy doc committed; Sentinel deadline gate live.
- Auto-PR bot configured and producing PRs against `main`.

### Acceptance evidence
- A deliberately-late simulated dep (fixture) produces a RED sentinel and CI block.
- Auto-PR bot has opened ≥1 successful PR by sprint close.

---

## Sequencing Summary

| Sprint | Title | Why now |
|---|---|---|
| 717 | Catalog & Citation SSOT | Production-visible drift; legal-surface (ToS) involvement |
| 718 | Auth Surface Hardening | High-severity CSRF binding bug; pre-Stripe |
| 719 | Stripe Live-Mode Webhook Resilience | Real-money traffic about to fly |
| 720 | Multi-Worker State Discipline | Bulk upload broken in production right now |
| 721 | Memo Output Quality & ISA 265 | Pre-Phase-3 walkthrough; legal/methodology risk |
| 722 | Memory Budget for Memo Generation | Pre-Phase-3 walkthrough; OOM risk on 18-memo run |
| 723 | Coverage Floor Enforcement | Foundational for all later refactors |
| 724 | `shared/helpers.py` Shim Removal | Should land before engine refactors that may import shim |
| 725 | Export Endpoint Consolidation | Independent; can land any time post-723 |
| 726 | AuditEngineBase Phase 1 | After 723's coverage floors are protecting refactor |
| 727 | AuditEngineBase Phase 2 + lint promotion | Closes the engine-pattern fork |
| 728 | ISA 520 Expectation Workflow | Post-launch product feature; CPA retention |
| 729 | ISA 450 SUM Schedule | Post-launch product feature; CPA retention |
| 730 | Operational Observability Polish | Continuous; anytime post-launch |
| 731 | Dependency Hygiene Cadence | Continuous; first execution lands the two pending patches |

---

## Cross-cutting Prevention Themes

After grouping, four prevention patterns recur across multiple sprints. Naming them explicitly so they become reusable:

**1. Single Source of Truth + CI consistency check.** (Sprints 717, 723) Every claim in human-edited content must derive from machine-readable source, or be CI-verified against it.

**2. Symmetry/parity tests.** (Sprints 718, 719, 720) Every code path that has two surface forms (Bearer/cookie, single-event/duplicate-event, single-worker/multi-worker) gets a parity test that runs both forms and asserts equivalence.

**3. AST/lint guardrails for "easy to reintroduce" bugs.** (Sprints 718, 720, 724, 725, 726, 727) Anywhere a bug class can be reintroduced via an innocent-looking PR, a mechanical scanner makes the bug class impossible to merge.

**4. Sentinel YELLOW → CI RED with deadlines.** (Sprints 723, 731) Coverage and dependency sentinels become blocking past their deadline thresholds. "FYI" becomes "act."

These four patterns should be cited in any future sprint that introduces a new prevention guardrail, so the codebase accumulates a recognizable shape rather than ad-hoc one-offs.

---

*Generated 2026-04-24 by IntegratorLead from the consolidated agent-sweep punch list.*
