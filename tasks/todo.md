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
> Sprints 726–731 archived to `tasks/archive/sprints-726-731-details.md`.
> Sprints 715–729 archived to `tasks/archive/sprints-715-729-details.md`.

### Sprint 732: cleanup_scheduler recurring InternalError triage
**Status:** STEP 1 COMPLETE 2026-04-27 — observability fix shipped; awaiting next ~1h of Render logs to identify the actual underlying exception class.
**Priority:** P2 → P1 once Phase 4.1 lands (silent recurring failure on `dunning_grace_period` blocks delinquent-subscription auto-cancellation, which becomes customer-visible the moment real money flows).
**Source:** Sprint 715 Render-log sweep 2026-04-26.

**Observed signal (2026-04-25 to 2026-04-26 in Render logs, srv-d6ie9l56ubrc73c7eq2g):**
```
ERROR cleanup_scheduler  Cleanup job failed: {... 'job_name': 'reset_upload_quotas',  'error': 'InternalError: scheduled cleanup failed'}
ERROR cleanup_scheduler  Cleanup job failed: {... 'job_name': 'dunning_grace_period', 'error': 'InternalError: scheduled cleanup failed'}
```
Both jobs fire roughly every hour; each invocation completes in 30–80ms with `records_processed: 0` and the same `InternalError`. **Diagnosis (2026-04-27):** the bare class name `InternalError` is ambiguous — Python's `builtins`, `sqlalchemy.exc`, and `psycopg2` all expose it. `cleanup_scheduler._run_cleanup_job` was using `sanitize_exception(exc, context="scheduled cleanup")` (correct PII-safe choice) but that strips both the message and the module path, leaving the log fingerprint useless for triage.

**Step 1 — Observability fix (DONE):**
- `backend/cleanup_scheduler.py::CleanupTelemetry` — added `error_type_fqn` field (e.g. `sqlalchemy.exc.InternalError`, `psycopg2.errors.SerializationFailure`). Module-path metadata only; no PII risk.
- `_run_cleanup_job` populates `error_type_fqn` from `caught_exc` so the structured log carries the disambiguating fingerprint without leaking exception messages.
- `tests/test_cleanup_scheduler.py::test_failure_log_includes_traceback_exc_info` extended to assert `error_type_fqn` appears with the FQN (`builtins.RuntimeError` for the test's deliberate `RuntimeError`). 28/28 cleanup-scheduler tests passing.

**Step 2 — Root cause investigation (IN PROGRESS):**
- Sub-step 2a (DONE 2026-04-27 17:14 UTC): Pulled Render logs filtered to `error_type_fqn` after Step 1's deploy (`dep-d7nom57avr4c73fgn9ig`, live 16:14:41 UTC). **Result: `sqlalchemy.exc.InternalError` on both jobs** (`reset_upload_quotas` + `dunning_grace_period`, both at 17:14 UTC). This is the SQLAlchemy wrapper — the leaf cause sits one level deeper inside `caught_exc.__cause__` / `caught_exc.orig`. Pre-deploy logs (13:01–16:04 UTC, 6 cleanup cycles) lack the field as expected.
- Sub-step 2b (DONE 2026-04-27): Extend cleanup_scheduler observability to also capture `__cause__` (raise-from chain), `.orig` (SQLAlchemy DBAPIError attribute holding the wrapped psycopg2 exception), and `orig.pgcode` (Postgres SQLSTATE — standardized 5-char code, no PII). Lands the leaf class + SQL error condition in the next cleanup cycle's logs without another debugging deploy round-trip. `CleanupTelemetry` gains 3 fields (`error_cause_fqn`, `error_orig_fqn`, `error_orig_pgcode`); `_run_cleanup_job` extracts them from `caught_exc`; `test_failure_log_captures_wrapped_cause_and_orig` synthesizes a SQLAlchemy DBAPIError-shaped exception and asserts all three surface. 29/29 cleanup-scheduler tests passing.
- Sub-step 2c (NEXT, ~30 min post-deploy of Step 2b): Pull cleanup logs after Step 2b lands; read `error_orig_fqn` + `error_orig_pgcode`. Most likely candidates given the 30–80ms latency + 0 records processed and the SQLAlchemy wrapper: `psycopg2.OperationalError` with pgcode `08006` (connection_failure) — matches Sentry's recurring `SSLEOFError` signal — or `psycopg2.errors.SerializationFailure` / `InFailedSqlTransaction`.
- Sub-step 2d: Cross-check with Sentry (the wrapper already calls `sentry_sdk.capture_exception(exc)`; full tracebacks should be there for the past 48h's worth of failures).

**Step 3 — Fix + coverage (AFTER step 2):**
- Land the underlying fix per the unwrapped class.
- Add an integration test that runs each cleanup job against a SQLite fixture and asserts no exception escapes the wrapper.
- Verify dunning escalation end-to-end on a staging-equivalent fixture (subscription past grace period → cancellation triggered).

**Effort estimate:** 0.5 sprint for step 1 (DONE), 0.5–1 sprint for step 2+3 depending on what the unwrapped error reveals. Total ≤1.5 sprints.

**Pre-requisites:** Step 1 deployed to Render — triggers automatically on PR merge to main.

---

### Sprint 733: Stripe webhook unit-coverage gap fill (pre-cutover)
**Status:** PENDING — pre-4.1 sequence position 2 (after Sprint 737). Gated only on Sprint 732 Step 2 not stealing capacity (independent code paths).
**Priority:** P2 → bumps to P1 the moment Phase 4.1 cutover schedule firms up. **Must land BEFORE Phase 4.1 (`sk_live_` keys)** — adds the safety net around the handler about to begin processing live revenue.
**Source:** Refactor pass 2026-04-27 (Codex directive, scope-revised after Sprint 710/724 + `## Deferred Items` reconciliation).

Add focused unit tests around `routes/billing.py::stripe_webhook` for the four boundaries currently exercised only at route level:
- missing `Stripe-Signature` header → 400
- invalid signature (forged HMAC) → 400
- duplicate event-id claim path → 200, no double-processing
- downstream operational failure (DB error mid-processing) → 500

Existing route-level tests (`test_billing_webhooks_routes.py`, `test_webhook_event_ordering.py`, `test_billing_routes.py`) remain untouched.

**Out of scope (per Deferred Items policy, line 54):** No handler decomposition. The signature-verify / dedup-claim / error-mapping triad stays in-route until bundled with the deferred webhook-coverage sprint flagged in Sprint 676.

**Verification:** All new tests green; existing 3 webhook test files unchanged; no behavioral change on `/billing/webhook`.

---

### Sprint 734: Playwright mapping-required upload flow coverage
**Status:** PENDING — pre-4.1 sequence position 4 (last of pre-4.1 batch). Gated only on Sprint 732 Step 2 not stealing capacity. Originally gated post-cutover by analogy with Codex's grouping; CEO blocker audit 2026-04-27 found no real dependency on 732/4.1 close (pure additive frontend test, zero production code change, Playwright already configured).
**Priority:** P3.
**Source:** Refactor pass 2026-04-27. Prerequisite for the deferred `useTrialBalanceUpload` decomposition (Deferred Items, line 55).

Add E2E coverage for the mapping-required preflight handoff in Trial Balance upload. **Playwright already configured** (`frontend/playwright.config.ts`, `@playwright/test ^1.59.0`, existing `frontend/e2e/smoke.spec.ts`) — this sprint writes the spec, not the harness.

Cover:
- mapping-required preflight detection (incomplete header set)
- mapping modal render + user mapping submission
- handoff back to upload pipeline + rerun behavior
- success path assertions (recalc fires once, not twice; no debounce-induced duplicate runs)
- no regression in existing debounce/recalc UX contract

**Out of scope (per Deferred Items policy, line 55):** No decomposition of `useTrialBalanceUpload`. This sprint exists to *enable* a future decomposition sprint by closing the coverage gap that currently makes the split unsafe.

**Verification:** New Playwright spec passes locally + in CI; existing `smoke.spec.ts` unaffected.

---

### Sprint 735: `require_client` adoption in diagnostics + trends routes
**Status:** PENDING — pre-4.1 sequence position 3 (after Sprint 733). Gated only on Sprint 732 Step 2 not stealing capacity. Originally gated post-cutover; CEO blocker audit 2026-04-27 reclassified the "muddier incident triage during cutover window" concern as soft (change-management hygiene, not a technical dependency) and accepted the tradeoff. Diagnostics + trends are read-only endpoints — no money flows through them, so a latent issue is recoverable.
**Priority:** P3.
**Source:** Refactor pass 2026-04-27.

Adopt the existing `require_client` dependency at call sites in `backend/routes/diagnostics.py` and `backend/routes/trends.py` (and any sibling routes with the same `Client.id == ... user_id == ...` boilerplate). Reduces duplicated query-then-404 patterns at call sites only.

**Constraint:** Use the existing helper in-place. Do **not** move `require_client` / `get_accessible_client` / `is_authorized_for_client` out of `backend/shared/helpers.py` — that move is explicitly rejected in Deferred Items (line 56), and remains rejected unless module scope grows beyond three helpers.

Add regression tests for tenant isolation + 404 vs 403 response shape parity.

**Verification:** No change to any response code, header, or body shape; tenant-isolation tests still pass.

---

### Sprint 736: `init_db()` schema-patch inventory (read-only research)
**Status:** COMPLETE 2026-04-27 — deliverable landed at `docs/03-engineering/init-db-inventory.md`. Recommendation: **(b) consolidate behind Alembic-only**, executed via Sprint 737 below. 7 of 10 branches classified `migration-disguised-as-init`; all are dead code in production today (Sprint 544c wired `alembic upgrade head` into Dockerfile CMD) and in CI (`conftest.py` uses `create_all()`). Patches only fire on a stale local dev SQLite path that bypasses both. CEO authorized pre-4.1 execution after blocker audit found no legitimate technical dependencies.
**Priority:** P3 (research-only).
**Source:** Refactor pass 2026-04-27, scope-narrowed from Codex's "startup-path safety hardening" directive after evidence the directive was overscoped.

Read-only inventory of `backend/database.py::init_db()` branches. Classify each as:
- `idempotent-init` (legitimate startup)
- `schema-patch` (ALTER TABLE / ADD COLUMN against existing tables)
- `migration-disguised-as-init` (schema-patch that references a specific Alembic revision and exists because Alembic isn't running on startup)

**Deliverable:** `docs/03-engineering/init-db-inventory.md` — classification table, references to the Alembic revisions involved, cost/risk profile, and a recommendation choosing exactly one of:
- (a) keep current dual-path (Alembic + in-process patcher),
- (b) consolidate behind Alembic-only with a startup migration-version assertion,
- (c) leave alone with documented rationale.

**Out of scope (per "prefer moving code, avoid new abstractions" rule):** No code changes. No structural rewrite of DB bootstrap. No migration-policy decision in this sprint — the inventory is the deliverable; the policy decision is a follow-up sprint if appetite emerges.

**Verification:** Doc exists, classification covers every branch in `init_db()`, recommendation is one of (a)/(b)/(c) with explicit reopen criteria.

---

### Sprint 737: `init_db()` Alembic consolidation (pre-4.1)
**Status:** PENDING — pre-4.1 sequence position 1 (first of pre-4.1 batch). Gated only on Sprint 732 Step 2 not stealing capacity (independent code paths).
**Priority:** P3 (dead-code removal + drift detection). No customer-visible behavior change.
**Source:** Sprint 736 inventory recommendation (b). Reverses the conservative (c) framing once Sprint 544c + Dockerfile evidence confirmed the in-process patches are dead code in production.

Consolidate database bootstrap behind Alembic-as-single-authority. Remove the 7 schema-patch blocks at `backend/database.py:148–278` that exist as a stale-dev-DB safety net but are dead code in production (Dockerfile CMD runs `alembic upgrade head` on every deploy per Sprint 544c) and in tests (`conftest.py` uses `Base.metadata.create_all()`).

**Step 1 (verification gate, FIRST — DO NOT SKIP):**
- Pull last 3 Render deploys' startup logs (service `srv-d6ie9l56ubrc73c7eq2g`).
- Confirm each shows the Dockerfile CMD's `Running: alembic upgrade head` (or `Running: alembic stamp head` for fresh DBs) before gunicorn starts.
- If yes → proceed to Step 2.
- If no → STOP. Sprint 737 pivots to "restore alembic-on-deploy" before any deletion.

**Step 2 (deletion):**
- Delete the 7 patch blocks in `init_db()` (lines 148–278 of `backend/database.py`, ~130 lines).
- Keep model imports + `Base.metadata.create_all()` (idempotent table creation for fresh DBs — still legitimate).
- Keep TLS verification + version logging (load-bearing startup health check).
- Keep completion log marker.
- Post-deletion `database.py` size estimate: ~230 lines (down from 360).

**Step 3 (drift detection):**
- Add CI test: `alembic upgrade head` against fresh in-memory SQLite produces a schema matching `Base.metadata.create_all()` against the same fresh in-memory SQLite. Compare table set + column set per table via `sqlalchemy.inspect()`.
- Catches "developer added a model column without an Alembic migration" — the only real future risk this consolidation creates.

**Step 4 (documentation):**
- Add note to `CONTRIBUTING.md` (or equivalent dev setup doc): "After pulling, run `python -m alembic upgrade head` if you have a local SQLite file from before the pulled changes. The in-process auto-patch was removed in Sprint 737."
- Update `docs/03-engineering/init-db-inventory.md` to record Sprint 737 outcome (which subset shipped, any deviations from plan).

**Out of scope:**
- No startup migration-version assertion. Dockerfile already fail-closes on alembic failure (emergency-playbook §4); a runtime assertion would duplicate that mode and add operational complexity for marginal benefit.
- No changes to existing Alembic migrations.
- No changes to `conftest.py`. The new CI drift test guarantees Alembic-vs-models parity.

**Verification:**
- All existing tests green (backend `pytest` + frontend `jest`).
- New CI drift test passes on current main.
- Production deploy after Sprint 737 lands shows the Dockerfile alembic step still runs (regression check on the verification gate's premise).
- `init_db()` size drops to ~230 lines.

---

