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

### Sprint 728: ISA 520 Expectation-Formation Workflow (parent — 728a/b/c)
**Status:** IN PROGRESS — split into 3 sub-sprints per CEO-approved plan `tasks/sprint-plan-728-729.md` (2026-04-26).
**Priority:** P3 (post-launch product gap; differentiator).
**Source:** Agent sweep 2026-04-24, punch list 4.1 + Accounting Methodology Audit.

Architecture decision (CEO-confirmed 2026-04-26): **snapshot model.** New entity holds *audit decisions* (expectation, threshold, corroboration, result, conclusion); flux / ratio / multi-period TB engines stay zero-storage. ISA 520 §A4–A8 frames this as a workpaper of decisions, not a database join.

#### Sprint 728a — Backend core
**Status:** COMPLETE 2026-04-26.
**Delivered:**
- `backend/analytical_expectations_model.py` — new `AnalyticalExpectation` entity (FK → engagements, soft-delete, JSON tag list, expected XOR range, threshold XOR percent, result status enum).
- `backend/analytical_expectations_manager.py` — CRUD manager with engagement-scoped multi-tenant ownership; pure-function `evaluate_status(actual, expected, threshold) → (variance, status)` reused later by 728c tool wiring.
- `backend/migrations/alembic/versions/f2a8e7d6c5b4_add_analytical_expectations.py` — Alembic migration; chains off prior head `e1a2b3c4d5f6`; upgrade + downgrade exercised end-to-end.
- `backend/schemas/analytical_expectation_schemas.py` — Pydantic Create/Update/Response.
- `backend/routes/analytical_expectations.py` — 5 CRUD endpoints (`POST` + `GET` list on `/engagements/{id}/analytical-expectations`, `GET` + `PATCH` + `DELETE` on `/analytical-expectations/{id}`); registered in `routes/__init__.py`.
- `backend/analytical_expectation_memo_generator.py` — ISA 520 workpaper PDF (cover, engagement overview, expectations table grouped by target type, authoritative references, sign-off block with DRAFT watermark when items remain unevaluated). Enterprise branding via `apply_pdf_branding`.
- `backend/routes/engagements_exports.py` — added `POST /engagements/{id}/export/analytical-expectations`.
- `backend/engagement_manager.py` — completion gate updated; engagements with non-archived `NOT_EVALUATED` expectations are blocked from completion (conditional — engagements with no expectations stay un-gated).
- `docs/04-compliance/isa-520-coverage.md` — methodology coverage doc.
- 6 test files, +61 tests covering model schema/defaults/soft-delete, manager CRUD/validation/`evaluate_status`, route happy-path + ownership + CSRF, memo PDF render, completion-gate matrix, export route.

**Verification:** Full backend `pytest` 8386 passed; the 4 unrelated failures in `test_security_hardening_2026_04_20.py` are pre-existing (`STRIPE_PUBLISHABLE_KEY` is `pk_test_*` while `IS_PRODUCTION=true` in dev env — clears once Sprint 447 cutover lands). Alembic upgrade head + downgrade -1 verified end-to-end against SQLite.

**Out of scope (carried to 728b/c):**
- Frontend section, capture form, hook (728b).
- Flux / ratio / multi-period TB engine wiring + auto-persist of result on tool run (728c).

#### Sprint 728b — Frontend
**Status:** PENDING — backend-first done, frontend next per execution order in plan.
**Scope:** Engagement-page section, capture form (XOR validation: value vs range, amount vs percent), Hook + Types, "Download workpaper" button, Oat & Obsidian tokens enforced, ~15–20 tests.

#### Sprint 728c — Tool wiring
**Status:** PENDING — last in 728 chain; depends on 728a + 728b shipping.
**Scope:** flux/ratio/multi-period engines accept pre-supplied expectations parameter, return variance flag inline; route layer auto-persists result back via the `evaluate_status` helper. Frontend tool result pages display "satisfied expectation #N" inline. New `backend/shared/expectation_evaluation.py` helper to keep entity types out of engine internals. ~25–30 tests.

---

### Sprint 729: ISA 450 SUM Schedule (parent — 729a/b/c)
**Status:** PENDING — split into 3 sub-sprints per CEO-approved plan `tasks/sprint-plan-728-729.md` (2026-04-26).
**Priority:** P3 (post-launch product gap; differentiator).
**Source:** Agent sweep 2026-04-24, punch list 4.2 + Accounting Methodology Audit.

Architecture decision: **snapshot model.** Because `AdjustingEntry` is in-memory (zero-storage dataclass per `backend/adjusting_entries.py`) and sampling output is ephemeral, the original "auto-aggregate from passed AJEs / sample projections" plan was infeasible without breaking zero-storage. CEO confirmed 2026-04-26: SUM is a CPA-captured workpaper of decisions, with 729c capture helpers added for ergonomics.

#### Sprint 729a — Backend core
**Status:** PENDING — next in queue after 728a (which lands first to validate the entity-pattern shared shape).
**Scope:** `UncorrectedMisstatement` entity (FK engagement, `source_type` enum: AJE_PASSED / SAMPLE_PROJECTION / KNOWN_ERROR, `classification` enum: FACTUAL / JUDGMENTAL / PROJECTED, `cpa_disposition` enum), Alembic migration, CRUD routes, `GET /engagements/{id}/sum-schedule` aggregation endpoint with materiality-bucket logic (CLEARLY_TRIVIAL / IMMATERIAL / APPROACHING_MATERIAL / MATERIAL based on `|aggregate|` vs trivial / performance / overall materiality), memo PDF, export route, completion gate (NOT_YET_REVIEWED block + override-required-for-MATERIAL), `docs/04-compliance/isa-450-coverage.md`, ~30–40 tests.

#### Sprint 729b — Frontend
**Status:** PENDING.
**Scope:** SUM schedule page in engagement layer, three-variant capture form (AJE-passed / sample-projection / known-error), materiality bucket UI with `clay`/`sage` token treatment ("approaching material" → reduced-opacity `clay` per design-mandate constraint), disposition controls, PDF download, ~20–25 tests.

#### Sprint 729c — Capture helpers
**Status:** PENDING.
**Scope:** "Add to SUM" buttons on AJE workflow + sampling tool (UEL > tolerable triggers a prompt) — pre-fills the SUM capture form. ~10 tests.

---

### Sprint 715: SendGrid 403 root-cause investigation (24h post-deploy watch)
**Status:** COMPLETE 2026-04-26.
**Priority:** P2 (observability follow-up).
**Source:** Sprint 713 Bug C review — the fix caught the exception but did not investigate the root cause.

**Investigation outcome:** Render logs over the 48h post-deploy window (2026-04-24 14:29 UTC → 2026-04-26 21:35 UTC) contain **zero matches** for `SendGrid`, `HTTPError`, `email_error`, `Verification email`, `Background … send failed`, and **zero requests** to `/auth/register`, `/auth/forgot-password`, `/contact`. Phase 3 functional validation hasn't exercised email paths yet, so the 403 trigger condition was never met. No root cause to chase.

**Secondary finding (fixed in this sprint):** While tracing the warn-path, discovered `shared/background_email.py` was logging `"Background <label> send failed: unknown"` because it read a non-existent `result.error` attribute. `EmailResult` exposes `success`/`message`/`message_id` — the SendGrid status code lives in `result.message`. Sprint 713's existing test only asserted `len(warning_records) >= 1`, never inspected the message text, so the regression slipped through. **If a 403 had occurred in the past 48h, the log line would not have surfaced the status code** — the warn-path Sprint 713 added was effectively non-investigable.

**Fix:**
- `backend/shared/background_email.py`: read `result.message` (the canonical attribute), with `"unknown"` only as the empty-string fallback.
- `backend/tests/test_sprint_713_sentry_sweep.py::test_background_email_logs_warning_not_error_on_failure`: strengthened to assert the warning is emitted by `shared.background_email`, contains the label, contains `"403"`, and does **not** fall back to `"unknown"`. Future regressions of this shape will fail the test.

**Out of scope (deferred):**
- Proactive SendGrid suppression-list sync (no infra justification until 403 volume is meaningful).
- Email deliverability SLA tracking.
- Cleanup_scheduler `InternalError: scheduled cleanup failed` on `reset_upload_quotas` and `dunning_grace_period`, observed every ~1h during this investigation. Unrelated system, separate signal — captured as a follow-up below.

**Verification:** `pytest tests/test_sprint_713_sentry_sweep.py tests/test_email_verification.py tests/test_contact_api.py tests/test_no_helpers_reexports.py tests/test_refactor_2026_04_20.py tests/test_log_sanitizer.py` — 106 passed.

**Review:** Sprint reframed from "find the 403 root cause" to "verify there *is* a 403 to investigate, then make the warn-path actually surface the status code when one happens". Net delta: 1 LoC fix in production code, +12 LoC of test assertions that prevent the silent-failure shape from re-emerging. Commit SHA recorded at commit time.

---

### Sprint 732: cleanup_scheduler recurring InternalError triage
**Status:** PENDING — discovered during Sprint 715 log review, not yet investigated.
**Priority:** P2 (silent recurring failure on production scheduled jobs; no user-facing impact today, but `dunning_grace_period` is the path that auto-cancels delinquent subscriptions, so a sustained outage means dunning escalation never advances).
**Source:** Sprint 715 Render-log sweep 2026-04-26.

**Observed signal (2026-04-25 to 2026-04-26 in Render logs, srv-d6ie9l56ubrc73c7eq2g):**
```
ERROR cleanup_scheduler  Cleanup job failed: {... 'job_name': 'reset_upload_quotas',  'error': 'InternalError: scheduled cleanup failed'}
ERROR cleanup_scheduler  Cleanup job failed: {... 'job_name': 'dunning_grace_period', 'error': 'InternalError: scheduled cleanup failed'}
```
Both jobs fire roughly every hour; each invocation completes in 30–80ms with `records_processed: 0` and the same `InternalError`. The error message itself (`"scheduled cleanup failed"`) is the wrapper's outer string — the actual underlying exception (likely a SQLAlchemy/DB error) is being swallowed before the structured-log emission.

**Scope:**
- Locate the scheduler's exception handler (`backend/cleanup_scheduler.py` or wherever the wrapper lives) and confirm it catches `Exception` then re-raises a generic `InternalError`. Surface the original exception class + message into the structured log line (mirror the `result.message` lesson from Sprint 715 — never log a sentinel without the underlying detail).
- Re-pull logs after the observability fix lands, identify the actual root cause for each job, fix.
- Add coverage so this can't re-surface silently: a test that runs each cleanup job against a SQLite fixture and asserts no `InternalError` is raised.
- Verify dunning escalation behavior end-to-end on a staging-equivalent fixture (subscription past grace period → cancellation triggered) once the underlying bug is known.

**Effort estimate:** 1 sprint, possibly 2 if the underlying bug is non-trivial (e.g., a missing migration or a connection-pool exhaustion). Step 1 (observability) is mechanical; step 2 (fix) depends on what the unwrapped error reveals.

**Why pending (not "now"):** This is a real production issue but it's been failing silently for at least 48h and has not produced user-visible symptoms. Sprint 728 + 729 are the user-directed work. Slot 732 in after the current directive completes.

**Pre-requisites:** None — diagnosable from logs once the wrapper unmasks the underlying exception.

---

