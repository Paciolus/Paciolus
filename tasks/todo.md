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

> Non-sprint commits that fix accuracy, typos, or copy issues without new features or architectural changes. One line per entry: `- [date] commit-sha: description (files touched)`.
>
> Pre-April 2026 entries archived to [`tasks/archive/hotfix-log-pre-april-2026.md`](archive/hotfix-log-pre-april-2026.md).

- [2026-04-30] post-PR-128 cleanup — closed 4 stale Apr-22 PRs (#94 superseded, #96 already on main, #97 partially superseded, #99 slot stale) + their remote/local branches. Captured the still-relevant gaps as one `fix:` commit: `.gitignore` adds `.hypothesis/` (root), `.claude/worktrees/`, `frontend/playwright-report/` (the PR #97 leftovers); `tasks/todo.md` adds Refactor Intake row for the Postgres enum-case drift bug originally filed as PR #99 (Sprint 715 slot was already taken by the SendGrid 403 investigation). Files: `.gitignore`, `tasks/todo.md`.
- [2026-04-29] PR #126 follow-up — `lint_engine_base_adoption.py` taught to follow ADR-018 shims to `services/audit/<tool>/analysis.py`. After `fae3e3e9` relocated 7 engines to dynamic-namespace shims, the AST-only check found no classes at the legacy path and false-flagged the 4 already-migrated engines (JE/AP/Payroll/Inventory) as off-pattern, breaking `test_engine_base_lint.py::TestKnownMigrated` on both Python 3.11 and Postgres 15 jobs. New `_resolve_shim_canonical()` helper detects both shim shapes (static `from services.audit.<tool>.analysis import *` and dynamic `from services.audit.<tool> import analysis as _impl`) and re-checks the canonical file. Findings drop 12→8 — the 4 unmigrated targets (AR Aging, FA, Revenue, SoD) and 4 borderline engines remain, matching `test_post_triage_finding_count` expectations. File: `scripts/lint_engine_base_adoption.py`.
- [2026-04-29] 016aafed: PR #126 CI gate alignment — `accounting_policy.toml` `[rules.revenue_contract_fields].file` repointed `revenue_testing_engine.py` → `services/audit/revenue_testing/analysis.py` (the legacy path is now a dynamic-namespace shim after `fae3e3e9` ADR-018 batch, so AST-based class detection found nothing and false-flagged ASC 606/IFRS 15 regression). OpenAPI snapshot regenerated to absorb 4 operation-description refreshes (`/export/{excel,pdf,leadsheets,financial-statements}` Sprint 748b pipeline-delegation docstrings); paths/schemas counts unchanged at 220/422. Files: `backend/guards/accounting_policy.toml`, `scripts/openapi-snapshot.json`.
- [2026-04-28] nightly QA Warden green-restore — `test_security_hardening_2026_04_20.py::TestRateLimitFailClosed` `_prod_env()` fixture now sets `STRIPE_PUBLISHABLE_KEY` and `STRIPE_WEBHOOK_SECRET` placeholders alongside `STRIPE_SECRET_KEY`. Without them, the subprocess env was missing those vars, python-dotenv backfilled from `backend/.env` (developer's test-mode Stripe key), and Sprint 719's production format guard hard-failed config import — surfacing as 2 test failures in the 2026-04-28 nightly. Companion to `e6627567` (helpers-allowlist) — together both nightly RED items resolved. File: `backend/tests/test_security_hardening_2026_04_20.py`.
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

---

## Deferred Items

| Item | Reason | Source |
|------|--------|--------|
| Preflight cache Redis migration | In-memory cache is not cluster-safe; will break preview→audit flow under horizontal scaling. Migrate to Redis when scaling beyond single worker. | Security Review 2026-03-24 |
| `PeriodFileDropZone.tsx` deferred type migration | TODO open for 3+ consecutive audit cycles. Benign incomplete type migration, not a hack. Revisit when touching the upload surface for another reason. | Project-Auditor Audit 35 (2026-04-14) |
| `routes/billing.py::stripe_webhook` decomposition (signature-verify / dedup / error-mapping triad) | Already touched lightly in the 2026-04-20 refactor pass; full extraction pairs better with the deferred webhook-coverage sprint flagged in Sprint 676 review (handler is currently exercised by 6 route-test files but lacks unit coverage). Bundle both then. | Refactor Pass 2026-04-20 |
| `useTrialBalanceUpload` decomposition into composable hooks | Hook's state machine (progress indicator, recalc debounce, mapping-required preflight handoff) is tightly coupled to consumer semantics. Not a drop-in extraction — needs Playwright coverage of the mapping-required flow before a split is safe. | Refactor Pass 2026-04-20 |
| `routes/auth_routes.py` cookie/CSRF helper extraction | Module is already reasonably thin; cookie/token primitives (`_set_refresh_cookie`, `_set_access_cookie`, etc.) are security-critical. Touching them without a specific bug or audit finding is net-negative. Revisit only if a follow-up auth/CSRF audit produces an actionable finding. | Refactor Pass 2026-04-20 |

---

## Architectural Remediation Initiative — COMPLETE 2026-04-29

> **All 18 sprints (742-759) shipped + post-initiative finishing pass closed 4 partial follow-ups.** Detail archived to [`tasks/archive/sprints-742-759-details.md`](archive/sprints-742-759-details.md). Scorecard at `reports/architectural-remediation-scorecard-2026-04-29.md`.
>
> **Outcome (TL;DR):** Phases 0/1/4/6/7/8 fully resolved; Phases 2/3/5 partial with explicit follow-up scope filed in `## Refactor Intake` below. 6 ADRs (014-019 + quality thresholds), 3 advisory CI lints, ~150 new pytest + ~50 new jest tests. Net code shrinkage: `auth_routes.py` 778 → ~270; `routes/export_diagnostics.py` 661 → 218; multi-period page 501 → 423; dashboard page 519 → 383; `useFormValidation.ts` 516 → 280.
>
> **Governance going forward:** quarterly architecture health review (run the 3 advisory lints, check deferred-items triggers, file ≤2 follow-up sprints if warranted); "no new god files" policy (code-review enforced); refactor intake lane visible in `## Refactor Intake` below. Subsequent sprints should be product-driven, not architecture-driven.

---

## Refactor Intake

> Visible landing zone for new architectural-debt findings between
> initiatives. Surface via the advisory CI lints, the quarterly arch
> health review, or organic discovery during product work. Reviewed
> quarterly; items reaching critical mass (e.g., 5+ targeting the same
> surface) roll up into a sprint entry under `## Active Phase`.
>
> Same shape as the `## Deferred Items` table above — the discipline
> is that intake is visible and gets reviewed.

| Item | Reason | Source |
|------|--------|--------|
| Postgres enum-case drift (Alembic vs prod) | Production Postgres enum types store **uppercase** values (`FREE, SOLO, PROFESSIONAL, ENTERPRISE`); every Alembic migration in `backend/migrations/alembic/versions/` references **lowercase** literals. No user impact today (SQLAlchemy reads/writes consistently), but: (1) future migrations touching enum literals fail on prod with `22P02` (observed during 2026-04-22 CEO Phase 3 tier upgrade — `UPDATE users SET tier = 'enterprise'` was rejected); (2) `alembic upgrade head` against a fresh DB emits lowercase, so DR rebuild produces an enum shape the app can't populate; (3) same drift likely exists on every Postgres enum (`subscription_tier`, `userrole`, `subscriptionstatus`, etc.). Sprint scope when triggered: enumerate prod enums, decide canonical direction (`values_callable=[e.name]` vs `[e.value]`), one-shot reconciliation migration + rollback path, drift-guard pytest. Originally filed as PR #99 (closed — slot stale; Sprint 715 was actually used for SendGrid 403 investigation). | 2026-04-22 production tier-upgrade incident |
| ~22 engines awaiting per-tool relocation per ADR-018 | 10 relocated total (recon + flux + cutoff_risk + 7 testing engines AP/AR/FA/Inv/JE/Payroll/Revenue). Remaining are mostly calculators/indicators where ADR-018 says "default keep flat" — per-tool relocation justified only when reorganization adds clear value beyond a shim. | `lint_domain_relocation.py` (advisory CI) — count 22 |
| 16 route handlers still importing engine orchestration symbols | Engine relocations alone don't fix this. Each route needs a service-layer extraction (`services/audit/<tool>/service.py` with orchestrator + thin route delegate) per ADR-015. Heavier per-tool refactor work; pattern is established by Sprint 745 (`activity.py`) + Sprint 746 (auth services). | `lint_route_layer_purity.py` (advisory CI) — count 16 |
| 9 testing engines not subclassing `AuditEngineBase` | Pre-existing backlog from Sprint 726 | `lint_engine_base_adoption.py` (advisory CI) |
| `routes/billing.py::stripe_webhook` decomposition | Bundled with deferred webhook coverage sprint | `## Deferred Items` |

---

## Active Phase
> **Launch-readiness Council Review — 2026-04-16.** 8-agent consensus: code is launch-ready; gating path is CEO calendar (Phase 3 validation → Phase 4.1 Stripe cutover → legal sign-off). Full verdict tradeoff map in conversation transcript.
>
> **Prior sprint detail:** All pre-Sprint-738 work archived under `tasks/archive/`. See [`tasks/COMPLETED_ERAS.md`](COMPLETED_ERAS.md) for the era index and archive file pointers. Sprints 732/739/740 archived to [`tasks/archive/sprints-732-740-details.md`](archive/sprints-732-740-details.md). Sprints 742–759 (architectural remediation) archived to [`tasks/archive/sprints-742-759-details.md`](archive/sprints-742-759-details.md).
> **Source:** External Financial Calculation Correctness audit (2026-04-30). Discovery pass confirmed substantial portions of the brief were already remediated (RPT-02 thresholds dataclass, RPT-11 epsilon separation, AR aging non-midpoint bucket bounds). Path B targets the genuinely outstanding defects + Decimal hardening of the bank-rec outlier and the multi-period output boundary. Conflict Loop captured in conversation transcript (2026-04-30).
>
> **Acceptance bar:** monetary decision logic Decimal-safe in the touched surfaces; materiality/threshold behavior dynamic + emitted in responses (active_thresholds + source); variance basis declared explicitly; intercompany layered with metadata + confidence + explainability; tests proving each fix and preventing regression.
> Sprints 763–767 archived to `tasks/archive/sprints-763-767-details.md`.

### Sprint 738: Alembic migration drift cleanup
**Status:** PENDING — pre-4.1 sequence position 1.5. Could slip post-4.1 if priority shifts; not customer-visible either way.
**Priority:** P3. Catches up on dormant tech debt surfaced by Sprint 737's drift test.
**Source:** Sprint 737's parity test (`backend/tests/test_alembic_models_parity.py`) discovered 4 tables and 6 columns defined on models with no corresponding Alembic migration.

Write Alembic migrations for the documented drift in `PRE_EXISTING_DRIFT_TABLES` and `PRE_EXISTING_DRIFT_COLUMNS`. As each migration lands, remove the corresponding entry from the allow-list. When both allow-lists are empty, the parity test enforces full Alembic-models equivalence going forward.

**Tables needing CREATE TABLE migrations (4):**
- `password_reset_tokens` — defined in `backend/models.py`
- `processed_webhook_events` — defined in `backend/subscription_model.py`
- `tool_activities` — defined in `backend/models.py`
- `waitlist_signups` — defined in `backend/models.py`

**Columns needing ADD COLUMN migrations (6):**
- `engagements.completed_at` + `engagements.completed_by` — defined in `backend/engagement_model.py`
- `diagnostic_summaries.ccc` + `dio` + `dpo` + `dso` (cash-conversion-cycle ratios) — defined in `backend/models.py`

**Step 1 — production verification gate (FIRST, DO NOT SKIP):** Before writing any migration, query production Postgres via Render MCP `query_render_postgres` (or `psql` against `paciolus-api-db`) to confirm whether each of these 10 schema objects already exists in production. Three possible outcomes per object:
1. **Object exists in production but not in Alembic** → write a migration whose `op.create_table` / `op.add_column` is wrapped in an existence check (or use Alembic's `op.execute` with `IF NOT EXISTS`) so it's idempotent on re-run. The migration's job is to bring Alembic's recorded history into sync with production reality, not to actually mutate production schema.
2. **Object missing in production** → write a normal `op.create_table` / `op.add_column` migration; production gains the column on next deploy.
3. **Object never accessed in production** (model is dead code) → consider removing the model definition instead of writing the migration. Verify via grep + Render request-log analysis.

**Out of scope:**
- No model-side changes (the models are the source of truth; Alembic catches up to them).
- No removal of `Base.metadata.create_all()` from `init_db()` — it currently creates the 4 orphan tables on fresh DBs, and removing it before the migrations exist would break local dev / CI fixtures.

**Verification:**
- After Sprint 738 lands, `PRE_EXISTING_DRIFT_TABLES` and `PRE_EXISTING_DRIFT_COLUMNS` are both empty in `test_alembic_models_parity.py`.
- Test still passes (full parity now enforced).
- Production deploy logs after the migrations run show the relevant `op.create_table` / `op.add_column` log lines (or `already exists, skipping` for outcome (1) cases).

---

### Sprint 741: cleanup_scheduler real-root structural fix (post-Sprint-740 follow-up)
**Status:** PENDING — depends on Sprint 740 post-deploy log read to identify the actual cleanup_func failure.
**Priority:** P2 → P1 once Phase 4.1 lands.
**Source:** Sprint 732 / 740 (archived to [`tasks/archive/sprints-732-740-details.md`](archive/sprints-732-740-details.md)).

Sprint 740 unmasked the cascade — `psycopg2.errors.InFailedSqlTransaction` (SQLSTATE 25P02) was the visible symptom; the real first failure inside `cleanup_func(db)` was hidden behind it. After Sprint 740's deploy + 1h, pull `error_orig_fqn` from the next cleanup-cycle failure log. Expected leaf class: probably `psycopg2.errors.SerializationFailure`, `psycopg2.OperationalError` with pgcode `08006` (matches Sentry's SSLEOFError signal), or something genuinely surprising. **That class names the structural fix.**

**Pre-requisite:** Sprint 740 production deploy completed + at least one post-deploy cleanup cycle observed with the new field populated.

**Once root class is known, scope is:**
1. Fix the actual failing statement in the cleanup_func body for whichever job (`reset_upload_quotas`, `dunning_grace_period`, or both).
2. Add a regression test that reproduces the underlying root cause and asserts the cleanup cycle completes without raising.
3. Verify dunning escalation end-to-end on a staging-equivalent fixture once the cascade is fixed.

---

### Sprint 760: Dependency hygiene — patches + safe minors (2026-04-29 nightly)
**Status:** PENDING. Sourced from 2026-04-29 nightly Dependency Sentinel (RED only signal — all other agents GREEN).
**Priority:** P3. Routine maintenance batch; no security urgency at the patch/minor level.
**Source:** `reports/nightly/2026-04-29.md` Dependency Sentinel section.

Bundle the 19 patch + safe-minor updates into one commit, mirroring the 2026-04-19/2026-04-22 hygiene-batch pattern.

**Backend (15):**
- Patches: `click` 8.3.2→8.3.3, `fastapi` 0.136.0→0.136.1 (security-relevant, but patch-level), `hypothesis` 6.152.1→6.152.4, `Mako` 1.3.11→1.3.12, `python-multipart` 0.0.26→0.0.27, `ruff` 0.15.11→0.15.12.
- Minors: `anthropic` 0.96.0→0.97.0, `certifi` 2026.2.25→2026.4.22, `greenlet` 3.4.0→3.5.0, `packaging` 26.1→26.2, `pathspec` 1.0.4→1.1.1, `pip` 26.0.1→26.1, `stripe` 15.0.1→15.1.0 (security-relevant), `tzdata` 2026.1→2026.2, `uvicorn` 0.45.0→0.46.0.

**Frontend (4):** `@sentry/nextjs` 10.49.0→10.50.0, `@typescript-eslint/eslint-plugin` 8.59.0→8.59.1, `@typescript-eslint/parser` 8.59.0→8.59.1, `postcss` 8.5.10→8.5.12.

**Excluded from this sprint:**
- `cryptography` 46.0.7→47.0.0 (MAJOR — own sprint, see 761).
- `pdfminer.six` 20251230→20260107 (deferred, calendar version, review by 2026-04-30).

**Verification:**
- `pip install -r backend/requirements.txt && cd backend && pytest -q` clean.
- `cd frontend && npm install && npm run build && npm test` clean.
- Stripe SDK upgrade: confirm no breaking change in 15.1.0 vs 15.0.1 (CHANGELOG sweep + smoke-test billing webhook fixture).
- FastAPI patch: confirm no behavior change in `Depends`/middleware semantics (regression-suite covers this implicitly).
- Render deploy logs after merge: zero new ImportErrors, /health 200 within 60s.

**Out of scope:**
- Major upgrades (cryptography 47).
- Frontend `next` / `react` major sweeps (no action needed in this nightly).

---

### Sprint 761: cryptography 47.0.0 major upgrade (security-relevant)
**Status:** PENDING. Standalone sprint per dep-hygiene policy: majors get isolated risk + verification windows.
**Priority:** P2 (security-relevant; pyca/cryptography ships CVE fixes via majors and the lib underpins JWT signing, password hashing, TLS evidence chain).
**Source:** `reports/nightly/2026-04-29.md` Dependency Sentinel — flagged as security-relevant + major.

**Pre-flight:**
1. Pull pyca/cryptography 47.0.0 release notes; flag any signature on `cryptography.hazmat.primitives.*` we depend on (JWT library, audit_chain TLS evidence, password reset token signing).
2. Audit direct imports: `Grep -r "from cryptography" backend/`. Cross-reference each call site against the 47.0.0 deprecation/removal list.
3. Identify transitive consumers (PyJWT, pyOpenSSL, requests-toolbelt, etc.) and confirm each is compatible with cryptography 47.x — pin floor in `requirements.txt` if any consumer requires <47.

**What lands:**
- `backend/requirements.txt` — `cryptography==47.0.0` (pin exact, not floor; Paciolus convention).
- Any compatibility shims for hazmat primitives that changed signature (unlikely for a properly-maintained version-bump, but possible).
- New regression test if a hazmat surface we depend on changed shape.

**Verification:**
- Backend `pytest` clean (especially: `tests/test_auth*.py`, `tests/test_password_reset*.py`, `tests/test_audit_chain*.py`, `tests/test_csrf*.py`, `tests/test_security_hardening*.py`).
- Manual: register → verify-email → login → logout → refresh-token → password-reset round-trip on a local instance.
- Render preview deploy: 24h soak before promoting to prod (per Paciolus prod-cutover policy for security-critical deps — same caution we used for the FastAPI 0.135.x bump in Sprint 263 era).

**Out of scope:**
- Bundling with the patch/minor batch (Sprint 760). Majors get their own sprint so a regression doesn't taint a 19-package roll-back.
- Migrating to `joserfc` or another JWT library — out of scope; we're upgrading the underlying primitive, not the wrapper.

---

### Sprint 762: flux_expectations memo PDF contract test (close 17/18 → 18/18)
**Status:** COMPLETE — landed on branch `sprint-762-flux-expectations-memo-contract-test`.
**Priority:** P3.
**Source:** Post-Sprint-754b memo contract test sweep (commit `60946271`). 17/18 memos covered; flux_expectations skipped because its dataclass was thought to nest typed Pydantic sub-models needing a non-trivial fixture. **Reality check during execution:** `generate_flux_expectations_memo` takes plain dicts (`flux_result` + `expectations`), so the fixture is the same shape as every other memo contract test. No nested Pydantic build needed.

**What landed:**
- `backend/tests/test_export_pdf_contract.py::test_flux_expectations_memo_pdf_contains_all_required_section_labels` — single test mirroring the established memo-contract pattern (extract PDF text, assert required section labels present).
- `_FLUX_EXPECTATIONS_FIXTURE` inline dict fixture with one high-risk flagged item + one practitioner expectation block, exercising the full template path (cover, scope, expectation/variance block with conclusion checkboxes, sign-off, disclaimer).
- `FLUX_EXPECTATIONS_MEMO_REQUIRED_SECTIONS` covers the six section anchors verified via pypdf extraction: `Flux`, `Expectation`, `Scope`, `Variance`, `Conclusion`, `Practitioner` (single-word anchors per the file's own pypdf-column-split guidance).
- Coverage-status comment block updated from "17/18 — flux_expectations skipped" to "18/18 (Sprint 762 closed the gap)".

**Verification:**
- `cd backend && python -m pytest tests/test_export_pdf_contract.py -v` → **19 passed, 0 failed** (3.56s) — was 18 tests, now 19; flux_expectations is the new one.
- No production code touched — pure test addition.

**Out of scope:**
- Refactoring the memo generator.
- Adding contract tests for the 3 non-memo report PDFs (combined audit, financial statements, anomaly summary) — separate filing if motivated.

**Commit SHA:** see branch `sprint-762-flux-expectations-memo-contract-test` (filled at PR merge).

---

### Sprint 768: Targeted security remediation — auth body-token, audit-chain key separation, /health/live fingerprinting, slowapi posture
**Status:** COMPLETE — landed on branch `sprint-768-security-remediation-auth-config-health-rl`.
**Priority:** P1 (security).
**Source:** External targeted security remediation brief (2026-04-30) — four findings flagged for immediate fix with minimal-change discipline.

**What landed:**

1. **Browser-default auth responses no longer carry `access_token` in JSON.**
   - `AuthResponse.access_token` → `Optional[str] = None` (`backend/auth.py`).
   - `/auth/register`, `/auth/login`, `/auth/refresh` only emit a JSON `access_token` when the caller sends `X-Token-Response: bearer` (default OFF; explicit non-browser API-client opt-in). Cookie issuance (`_set_access_cookie`, `_set_refresh_cookie`) unchanged — the HttpOnly cookie remains the browser carrier.
   - Frontend (`AuthSessionContext`) now uses `data.user` as the success marker instead of `data.access_token`; cookie auth via `credentials: 'include'` is the load-bearing path. `AuthResponse` TypeScript type marks `access_token` optional.
   - 4 new pytest tests pin the opt-in contract; existing register/login/refresh assertions updated.

2. **`AUDIT_CHAIN_SECRET_KEY` cryptographic separation enforced in production.**
   - `backend/config.py` hard-fails when the key is missing/blank in production, *and* when it equals `JWT_SECRET_KEY` (sharing collapses the SOC 2 CC7.4 boundary and ties audit-chain integrity to JWT rotation cadence).
   - Non-production keeps the dev fallback but emits an explicit `WARNING` per boot.
   - 4 new subprocess-based tests in `test_security_hardening_2026_04_20.py::TestAuditChainKeySeparation` cover both failure modes plus the happy path.

3. **Public `/health/live` no longer exposes exact platform version.**
   - `LivenessResponse` no longer includes `version`; `/health/ready` (operationally scoped) continues to expose it.
   - Reduces external fingerprinting surface — orchestrator restart decisions don't need version, scanners no longer pin exploit attempts to a known build.

4. **slowapi unmaintained-status surfaced explicitly + fail-closed coverage strengthened.**
   - `shared/rate_limits.py` emits a startup banner on import: `WARNING` in production, `INFO` in non-production. Substring `"slowapi is unmaintained"` is intentionally pinned for monitoring rules.
   - New `test_rate_limit_strict_mode.py::TestStrictModeFailClosedRedisStorageInit` covers the `RedisStorage` constructor-raises path under strict mode.
   - New `TestSlowApiUnmaintainedWarning` asserts severity-by-env semantics.
   - `docs/runbooks/rate-limiter-modernization.md` adds an "Operator Posture" section documenting the temporary acceptance posture and the entry criteria for the deferred migration sprint (canary failure on green main, slowapi CVE ≥ 7.0, or Starlette major-version incompat).
   - Full slowapi → custom-Starlette migration explicitly **deferred** in this patch (123 decorator sites, no CVE, `limits` engine is actively maintained and pinned `>=3.0.0`).

**Files touched (13):**
- `backend/auth.py`, `backend/routes/auth_routes.py`, `backend/config.py`, `backend/routes/health.py`, `backend/shared/rate_limits.py`
- `backend/tests/test_auth_routes_api.py`, `backend/tests/test_health_api.py`, `backend/tests/test_rate_limit_strict_mode.py`, `backend/tests/test_security_hardening_2026_04_20.py`
- `frontend/src/types/auth.ts`, `frontend/src/contexts/AuthSessionContext.tsx`, `frontend/src/__tests__/AuthContext.test.tsx`
- `docs/runbooks/rate-limiter-modernization.md`

**Verification:**
- `cd backend && python -m pytest -q` → **8,685 passed, 0 failed** (829s).
- `cd backend && python -m pytest tests/test_auth_routes_api.py tests/test_auth_parity.py tests/test_auth_security_responses.py tests/test_health_api.py tests/test_health_redis_r2.py tests/test_rate_limit_*.py tests/test_security_hardening_2026_04_20.py tests/test_audit_chain.py -q` → **216 passed, 0 failed**.
- `cd frontend && npm test -- --watch=false` → **207 suites, 2,013 tests, 0 failed**.
- `cd frontend && npx tsc --noEmit` → exit 0.
- `cd frontend && npm run build` → exit 0; routes correctly dynamic (`ƒ`).

**Out of scope / deferred:**
- Server-side gating of the `X-Token-Response: bearer` opt-in to non-browser User-Agents — out of minimal-change scope; cookie remains authoritative regardless.
- Full slowapi migration — entry criteria documented in the runbook; defer until trigger fires.

**Commit SHA:** `fbec7a61` (branch `sprint-768-security-remediation-auth-config-health-rl`).

---

### Sprint 769: Frontend context memoization (render-perf hotfix)
**Status:** PENDING
**Priority:** P2. No user-visible bug, but cascade re-renders measurably affect interactive latency in tools that mount under DiagnosticProvider/EngagementProvider.
**Source:** Frontend efficiency audit (2026-05-01) findings 1.1 + 1.2.

`DiagnosticContext` (`frontend/src/contexts/DiagnosticContext.tsx:39`) and `EngagementContext` (`frontend/src/contexts/EngagementContext.tsx:117–128`) build a fresh `value` object literal on every provider render. With `setResult`/`clearResult` also fresh closures (lines 30, 34), every consumer re-renders whenever the provider's parent re-renders, regardless of whether the carried state actually changed.

**What lands:**
- `DiagnosticContext.tsx:30, 34` — wrap `setResult` / `clearResult` in `useCallback`.
- `DiagnosticContext.tsx:39` — wrap `value` in `useMemo`, deps `[result, isLoading]`.
- `EngagementContext.tsx:117–128` — wrap `contextValue` in `useMemo` with full dep array (`activeEngagement, toolRuns, materiality, isLoading, toastMessage, selectEngagement, clearEngagement, refreshToolRuns, triggerLinkToast, dismissToast`).
- Investigate the `// eslint-disable-line react-hooks/exhaustive-deps` at `EngagementContext.tsx:115` — the suppressed deps (`searchParams`, `router`, `pathname`, `selectEngagement`) hide a stale-closure risk; either fix properly or document why the suppression is intentional.

**Verification:**
- `npm run build` and `npm test` clean — value shape unchanged, existing context tests should still pass.
- React DevTools Profiler: open `/tools/journal-entry-testing`, trigger an unrelated re-render (e.g. theme toggle); confirm `<DiagnosticProvider>` consumers no longer fire.
- Optional: dev-only render-counter test asserting consumer renders track only state changes, not parent renders.

**Out of scope:**
- Splitting either context into state-vs-dispatch halves — bigger refactor, not warranted by current symptoms.
- The other render-perf findings (row mappings, table memoization, result-subtree wraps) — bundled in Sprint 773.

---

### Sprint 770: FileDropZone consolidation across testing tool pages
**Status:** PENDING
**Priority:** P3. No functional bug — pure DRY win + drift prevention as upload requirements evolve.
**Source:** Frontend efficiency audit (2026-05-01) finding 2.1.

The shared primitive at `frontend/src/components/shared/FileDropZone.tsx` is consumed by `bank-rec`, `three-way-match`, and `multi-period`. Seven other tool pages still inline the same ~30-line `border-2 border-dashed rounded-2xl p-12 cursor-pointer` block with hand-rolled `onDrop`/`onDragOver`/`onDragLeave`/hidden file input + duplicate SVG. Diverging upload-format support (e.g. when adding a new accepted extension or sub-ledger optional-pairing) means seven separate edits today.

**Migration targets:**
- `app/tools/ap-testing/page.tsx:101–139`
- `app/tools/journal-entry-testing/page.tsx:107–153`
- `app/tools/payroll-testing/page.tsx:108–159`
- `app/tools/revenue-testing/page.tsx:130–185`
- `app/tools/fixed-assets/page.tsx:93–139`
- `app/tools/inventory-testing/page.tsx:93–139`
- `app/tools/ar-aging/page.tsx:110–207` (dual zone — TB required + sub-ledger optional)

**What lands:**
- AR aging requires a `dual-zone` variant of `FileDropZone` (or a small `<DualFileDropZone>` composing two instances). Pick whichever shape fits existing prop conventions; document the choice in the component file.
- All seven pages refactored to render `<FileDropZone>` instead of inline markup. Hidden `<input type="file">` behavior, drag-state styling, accept-string, click-to-browse all preserved 1:1.

**Verification:**
- `npm test` — existing tests for each tool page pass with the same drop/click/upload semantics.
- Manual smoke: drop a file into each of the seven migrated pages; confirm drop-state border transitions, file selection, and downstream `runTests` invocation behave identically.
- Net line delta target: ~−400 lines across the seven page.tsx files.

**Out of scope:**
- Touching the existing three consumers (`bank-rec`, `three-way-match`, `multi-period`) — already correct.
- Refactoring `useFileUpload` itself.

---

### Sprint 771: UI primitives — Button, ToolHeroHeader, ToolLoadingState, ToolErrorState
**Status:** PENDING
**Priority:** P3.
**Source:** Frontend efficiency audit (2026-05-01) findings 2.2, 2.3, 2.4.

Three Tailwind class-string patterns are copy-pasted across the tool-page suite, plus the hero-header markup. None of these primitives exist in `components/ui/` (only `Reveal.tsx` lives there today). Without primitives, brand-token migrations or hover-state changes require touching ~20 files.

**What lands (`components/ui/`):**
- `Button.tsx` — `variant: 'primary' | 'secondary' | 'ghost'`, `size: 'sm' | 'md'`, with disabled-state classes baked in. Replace 7 primary-button copies (e.g. `ap-testing/page.tsx:185`, `ar-aging/page.tsx:276`, `fixed-assets/page.tsx:173`, `inventory-testing/page.tsx:173`, `payroll-testing/page.tsx:188`, `revenue-testing/page.tsx:210`, `statistical-sampling/page.tsx:241`) and ~20 secondary-button copies.
- `ToolHeroHeader.tsx` — props `{ standard, title, description, actions? }`. Render the inline-flex pill + `h1.type-tool-title` + description-p block. Replace in ~19 tool pages.
- `ToolLoadingState.tsx` — props `{ message }`. Render the `text-center py-16 → spinner → message` block. Replace in 9 tool pages (incl. `ap-testing:144`, `ar-aging:231`, `fixed-assets:150`, `inventory-testing:150`, `journal-entry-testing:161`, `payroll-testing:167`, `revenue-testing:189`).
- `ToolErrorState.tsx` — props `{ message, onRetry? }`. Render the `bg-theme-error-bg border-l-clay-500` alert with optional retry button. Replace in 10 pages (incl. `account-risk-heatmap/page.tsx:373`, `composite-risk/page.tsx:330`).

**What does NOT change:**
- `ToolStatePresence` orchestrator stays — it composes the new primitives instead of inlining markup.
- `GuestCTA` / `UnverifiedCTA` / `UpgradeGate` already abstracted; left alone.

**Verification:**
- `npm run build` and `npm test` clean.
- Visual diff: page-snapshot at least one tool page per state (idle/loading/error/success) before and after; confirm pixel-equivalence under both Vault themes.
- Net line delta target: ~−700 lines across page.tsx files; ~+250 in `components/ui/`. Bundle size should drop slightly from class-string deduplication.

**Out of scope:**
- Page-private `RiskPill` / `Stat` / `TierPill` / `StatBox` mini-components in `composite-risk` and `account-risk-heatmap` — flagged separately in Sprint 773.
- A full design-system rewrite — primitives are surgical, brand-token semantic only.

---

### Sprint 772: Bundle wins — lazy-load Recharts, CommandPalette + LazyMotion evaluation
**Status:** PENDING
**Priority:** P2. Each chunk is ≥30 kB gzipped; cumulative is meaningful for first-paint on tool pages.
**Source:** Frontend efficiency audit (2026-05-01) findings 3.1, 3.2, 3.3.

Three bundle-bloat issues with measurable user-visible cost:

1. **Recharts loaded eagerly in JE-testing and dashboard.** `app/tools/journal-entry-testing/page.tsx:5` synchronously imports `BenfordChart` (which pulls `recharts` ~90 kB gzipped) even though the chart only renders inside the success branch (`page.tsx:227`). Same shape for `analytics/TrendSparkline.tsx` consumers (dashboard, multi-period).
2. **GlobalCommandPalette mounted on every route.** `app/providers.tsx:9, 32` ships the palette to marketing, auth, error, and every tool page; users invoke it via ⌘K only on workspace pages.
3. **framer-motion imported in 139 files with no LazyMotion.** Each `'use client'` page that does any reveal pulls the full `motion` runtime (~30 kB).

**What lands:**
- `BenfordChart` and `TrendSparkline` converted to `next/dynamic` with `{ ssr: false, loading: () => <ChartSkeleton /> }`. Add `ChartSkeleton` to `components/shared/skeletons/`.
- `GlobalCommandPalette` converted to `next/dynamic({ ssr: false })` in `app/providers.tsx`. Confirm the ⌘K listener is registered eagerly (lightweight) and only the palette UI is deferred. If the listener lives inside the palette today, hoist it.
- LazyMotion evaluation: prototype `<LazyMotion features={domAnimation}>` at `app/providers.tsx`, migrate one page (e.g. `/tools/ap-testing`) to `m.div` instead of `motion.div`, measure bundle delta with `next build` size report. **Decision in this sprint:** ship LazyMotion app-wide if savings >20 kB first-paint *and* SSR/animation parity holds; otherwise defer with documented findings.

**Verification:**
- `next build` analyze report before/after. Target: ~−90 kB on `/tools/journal-entry-testing` first-load JS, similar on dashboard, ~−20 kB on every page (palette).
- Sentry RUM (if available): no regression in `LCP` or `CLS`.
- Manual: `/tools/journal-entry-testing` upload→success path renders the chart with the skeleton flash; ⌘K still opens the palette on first invocation; reduced-motion preference still respected.

**Out of scope:**
- Replacing recharts with a lighter chart library — the lazy-load is sufficient win.
- Migrating all 139 framer call sites to `m.*` — only `app/providers.tsx` and one validation page in this sprint; broader migration becomes a follow-up if LazyMotion ships.

---

### Sprint 773: Type disambiguation, dead-code cleanup, residual render-perf
**Status:** PENDING
**Priority:** P3.
**Source:** Frontend efficiency audit (2026-05-01) findings 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 2.5, 2.6, 4.1.

Grab-bag of smaller maintainability fixes that pair naturally — none warrant a standalone sprint, but together they close out the remaining audit findings.

**What lands:**

- **Type disambiguation —**
  - `types/accountRiskHeatmap.ts:9` `Severity` (3-value) collides with the canonical `types/shared.ts:16` (4-value). Rename local to `HeatmapSeverity` or import the canonical and constrain at the consumer.
  - `RiskLevel` is defined three times with different shapes:
    - `utils/themeUtils.ts:186` (`high | medium | low | none`) → rename to `ThresholdRiskLevel`.
    - `types/compositeRisk.ts:10` (`low | moderate | elevated | high`) → rename to `CompositeRiskLevel`.
    - `contexts/DiagnosticContext.tsx:10` re-export from `types/diagnostic` → rename to `DiagnosticRiskLevel`.
  - Update all importers; eslint catches missed references.

- **Dead-code —**
  - `utils/motionTokens.ts:60` deprecated `DISTANCE` map: inline `DISTANCE.state = 8` into `STATE_CROSSFADE` / `EMPHASIS_SETTLE` and delete the export.

- **Residual render-perf —**
  - `app/tools/multi-period/page.tsx:358–359` — wrap `<MovementSummaryCards>` and `<BudgetSummaryCards>` with `React.memo` so dashboard filter/sort interactions don't cascade through the result tree.
  - `app/tools/account-risk-heatmap/page.tsx:397` `HeatmapResults` and `app/tools/composite-risk/page.tsx:354` `CompositeRiskResults` — same `React.memo` treatment; these subtrees don't need to re-render on filter inputs.
  - `app/tools/composite-risk/page.tsx:180–212` and `app/tools/account-risk-heatmap/page.tsx:198–290` — extract `<RowEditor>` / `<SignalRow>` as `React.memo` children receiving `(row, idx, updateRow)`. Today, every keystroke in any input on the page re-renders all rows and rebuilds option JSX `n×3` per render.
  - `components/shared/testing/FlaggedEntriesTable.tsx:263–296` — extract `<FlaggedRow>` as `React.memo`, hoist motion `initial`/`animate`/`transition` literals to module scope.
  - `components/multiPeriod/AccountMovementTable.tsx:24–39` — hoist the sort comparator factory outside the `useMemo` body (currently re-created on every memo run).
  - `components/multiPeriod/MovementSummaryCards.tsx:15–19` — hoist `borderAccentMap` to module scope `as const`.
  - `Reveal` placement (composite-risk + heatmap pages) — move `Reveal` inside the memoized result subtree so reveal-state work doesn't redo on parent state changes.

- **Inline mini-component extraction (optional in this sprint, defer if scope creeps) —**
  - `RiskPill` (`composite-risk/page.tsx:452`) + `TierPill` (`account-risk-heatmap/page.tsx:532`) → unified `<RiskBadge level=…>` in `components/shared`.
  - `Stat` (`composite-risk/page.tsx:462`) + `StatBox` (`account-risk-heatmap/page.tsx:542`) → `<StatTile>` in `components/shared`.

**Verification:**
- `npm run build`, `npm test`, `npm run lint` all clean.
- Type-rename diff stays in `types/`, `utils/`, importers; no logic changes.
- Render-perf wins confirmed via React DevTools Profiler on `/tools/multi-period`, `/tools/account-risk-heatmap`, `/tools/composite-risk` — sibling-state changes no longer re-render the result subtree; row keystrokes only re-render the active row.

**Out of scope:**
- The 4 `eslint-disable react-hooks/exhaustive-deps` suppressions — not all are bugs; leave for a separate audit pass unless one is confirmed stale-closure.
- Inline-SVG icon consolidation (audit finding 3.4, ~459 occurrences) — separate sprint if/when motivated by a token migration.
- Barrel-export reorganization (audit finding 3.5) — production tree-shakes correctly today; intervention only if a dev/test perf issue surfaces.
- Per-tool ScoreCard / DataQualityBadge wrappers (audit finding 2.7) — verified healthy adapter pattern; no action.

---

