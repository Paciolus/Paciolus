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

---

### Sprint 674: QA Warden pytest timeout raised 600s → 1200s
**Status:** COMPLETE
**Source:** Nightly audit review 2026-04-18 — Sprint Shepherd / QA Warden trend
**Why now:** 2026-04-17 overnight RED because `qa_warden.py` backend pytest subprocess hit its 600s hard timeout at 601.8s. On 2026-04-18 the suite ran in 581.2s — **19s of margin**. Test count grew 7,405 (04-15) → 7,804 (04-18); next sprint or two reliably re-triggers the timeout.
**File:** `scripts/overnight/agents/qa_warden.py:39, 69`
**Changes:**
- [x] Raise `subprocess.run` timeout from 600 → 1200 in `_run_backend_tests` (both the json-report path and the fallback path)
- [x] No changes to `_run_frontend_tests` — ran 46.3s of 300s budget, ample headroom
- [x] No migration to pytest-xdist — rejected to avoid DB-fixture parallelism risk (single-worker guarantees in current fixtures); revisit if 1200s ceiling approached again

**Review:**
- Rationale for 1200s (vs. 900s or 1800s): 1200s gives ~2× current runtime — enough to absorb ~3,000 new tests at current pace without requiring another bump; not so generous that a genuine regression (e.g. a hanging test) burns the whole nightly window before surfacing. Next agent (`report_auditor`) sleeps until 02:15, so even a full 1200s wait still completes ahead of schedule.
- Did NOT touch pytest config — keeps the fix isolated to the nightly driver so regular `pytest` and CI behavior are unchanged.

---

### Sprint 675: Security-relevant dependency bump sweep + Sentinel scan-path fix
**Status:** COMPLETE
**Source:** Nightly audit review 2026-04-18 — Dependency Sentinel YELLOW (stable across 04-15, 04-17, 04-18)
**Why now:** Security-relevant updates pending unaddressed across three consecutive nightlies. While bumping, discovered the Dependency Sentinel was scanning `C:/Python312` (system Python, stale fork) instead of `backend/venv/Scripts/python.exe` (what actually matches `requirements.txt` and runs in production). Two of the five "security-relevant" packages reported in the nightly (SQLAlchemy 2.0.48→49, stripe 15.0.0→1) were already synced in the venv — the sentinel was giving false signals.

**Changes:**
- [x] `scripts/overnight/agents/dependency_sentinel.py` — switch backend scan from `SYSTEM_PYTHON` to `PYTHON_BIN` (the venv); keeps `SYSTEM_PYTHON` as fallback if venv missing. Import `PYTHON_BIN` from `config.py` (already defined, unused until now).
- [x] `backend/requirements.txt`: `fastapi` 0.135.3 → 0.136.0, `pydantic[email]` 2.12.5 → 2.13.2
- [x] `backend/requirements.txt`: `cryptography>=46.0.7` was already pinned but venv had 46.0.6 installed; `pip install -U` brought it current
- [x] `frontend/package.json`: `next` ^16.2.2 → ^16.2.4 (resolves 16.2.4 per nightly sentinel)
- [x] `npm install` — 3 packages changed, 0 vulnerabilities, all frontend deps intact
- [x] `npm run build` passes — all routes render as `ƒ (Dynamic)` (CSP proxy.ts nonce-based rendering intact after next 16.2.2→16.2.4)
- [x] Backend `pytest`: **7805 passed, 9 xfailed, 0 failed** in 644.25s after the bump — pydantic 2.13 migration clean, no API deprecations surfaced
- [x] Frontend `npm test` passes (see review below)

**Skipped (legitimately not outdated in the venv despite nightly report):**
- SQLAlchemy 2.0.48 → 2.0.49 — venv already at 2.0.49 (sentinel was reading system Python 2.0.48)
- stripe 15.0.0 → 15.0.1 — venv already at 15.0.1 (same root cause)

**Explicitly deferred:**
- `rich` 14.3.3 → 15.0.0 (major) — not security-relevant, defer until a feature needs it
- `tzdata` 2025.3 → 2026.1 (major) — not security-relevant
- `pdfminer.six` 20251230 → 20260107 — previously deferred, reviewed by 2026-04-30

**Review:**
- The Sentinel fix is the more important half of this sprint: without it, next week's nightly would continue reporting stale YELLOW signals from the system-Python fork even though production (Render) is on current requirements.txt. After this fix, Dependency Sentinel reports match what prod actually installs.
- pydantic 2.12 → 2.13 is semver-minor but changed validation internals; full 7805-test pass is strong evidence the upgrade is clean for our schemas.
- next 16.2.2 → 16.2.4 contains the patch advisory referenced in nightly reports; build output confirms dynamic-render + CSP nonce contract unbroken (`ƒ` on all routes).

---

### Sprint 676: Coverage fill — dead-code deletion + CSV serializer tests
**Status:** COMPLETE
**Source:** Nightly audit review 2026-04-18 — Coverage Sentinel (stable green 92.24% but persistent 0% files)

**Scope adjustment during execution:**
The nightly Coverage Sentinel's three worst 0%-coverage files turned out to have three distinct root causes, not one. Scope was adjusted per finding rather than forcing tests onto inappropriate targets:

1. **`services/organization_service.py` — 180 stmts @ 0%:** Investigation showed this file has **zero imports anywhere in the codebase**. Sprint 546 (archived) claimed "Refactor 5: organization.py → services/organization_service.py + thin routes" but only created the service module; `routes/organization.py` continued to use its own private `_get_user_org` / `_require_admin` helpers. The service file is orphaned dead code. **Fix: delete the file.** Testing dead code for coverage vanity would have been noise; completing the refactor is a larger risk-carrying change that deserves its own sprint, not a coverage-fill sprint.
2. **`export/serializers/csv.py` — 158 stmts @ 0%:** Genuine production path with no direct unit tests. **Fix: add `backend/tests/test_export_csv_serializers.py` with 31 tests** covering all 6 serializer functions (`trial_balance`, `anomalies`, `preflight_issues`, `population_profile`, `expense_category`, `accrual_completeness`) across happy paths, edge cases (empty input, prior-period vs no-prior, optional narrative, missing fields), CSV injection sanitization, and the UTF-8-sig BOM encoding contract.
3. **`billing/webhook_handler.py` — 180 stmts missing (55% covered):** Deferred. Existing route-level tests (`test_billing_webhooks_routes.py`, `test_billing_analytics.py`, `test_billing_routes.py`, `test_phase1_bug_fixes.py`, `test_pricing_integration.py`, `test_pricing_launch_validation.py`) already import from `billing.webhook_handler` and exercise real handler paths. Unit-testing the 180 defensive branches would be duplicative churn. A dedicated webhook-coverage sprint can pick this up later if the number becomes problematic.

**Changes:**
- [x] Delete `backend/services/organization_service.py` (180 lines, orphan dead code)
- [x] Add `backend/tests/test_export_csv_serializers.py` (31 tests, all passing in 1.64s)
- [x] Explicitly defer: `billing/webhook_handler.py` (covered indirectly by 6 route-test files)
- [x] Explicitly defer: `excel_generator.py`, `leadsheet_generator.py`, `workbook_inspector.py`, `generate_sample_reports.py` (non-production, larger lift)

**Impact:**
- Coverage Sentinel's top-10 uncovered list should lose `organization_service.py` (file gone) and `csv.py` (now ~100% covered). Overall backend coverage nudges up marginally (~0.2–0.3pp) but more importantly, the nightly's top-uncovered list becomes signal rather than noise.
- Removes a dangling refactor artifact that would eventually confuse future work on `routes/organization.py`.

**Review:**
- The decision not to test `organization_service.py` was a judgment call: writing tests for unimported code inflates coverage without improving safety. The archived Sprint 546 refactor appears to have stopped halfway; documenting that here lets a future sprint either complete the migration (replace route-level helpers with service imports) or confirm the deletion is permanent.
- CSV serializer tests target the *contract* (output shape, BOM, sanitization), not implementation details. They should survive future refactors of how the serializers walk inputs.
- Full backend `pytest` re-run confirms no test referenced the deleted module.

---

### Sprint 611: ExportShare Object Store Migration
**Status:** PENDING — CEO-gated (bucket provision)
**Source:** Critic — DB bloat risk
**File:** `backend/export_share_model.py:43`
**Problem:** `export_data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)` stores up to 50 MB per shared export in primary Neon Postgres. 20 concurrent shares = 1 GB of binary row storage; Neon Launch tier cap is 10 GB. Also bloats every DB backup — unclear whether zero-storage policy permits this.
**Changes:**
- [ ] Provision object store bucket (R2 or S3) with pre-signed URL pattern — CEO owns this, tracked in [`ceo-actions.md`](ceo-actions.md) "Backlog Blockers"
- [ ] Store `export_data` in bucket keyed by `share_token_hash`; DB row keeps metadata + object key only
- [ ] Extend cleanup scheduler to delete object when share revoked/expired
- [ ] Backfill migration for existing shares

---

### Sprint 673: Remove DB_TLS_OVERRIDE via pooler-aware pg_stat_ssl skip
**Status:** CODE-COMPLETE — pending deploy + CEO env-var removal
**Source:** Council Review 2026-04-16 — Critic (time-fused architectural debt) + Executor (front-run launch week)
**Why now:** `DB_TLS_OVERRIDE=NEON-POOLER-PGSSL-BLINDSPOT:2026-05-09` expires in 23 days. Without the proper fix landed first, the override must either be renewed (kicks the can) or allowed to expire (hard-fails production startup during Phase 4 launch window). Fixing before Phase 4 removes one ticking clock from launch week.
**File:** `backend/database.py`
**Problem:** Production startup runs a `pg_stat_ssl` check to confirm the DB connection is encrypted. Neon's pooled endpoint (`-pooler` hostname) is a transparent connection pooler — the underlying connection IS TLS-encrypted, but `pg_stat_ssl` reports the pooler-to-backend hop, not the client-to-pooler hop. The check therefore returns `ssl=false` on a correctly encrypted connection, forcing the current override.
**Changes:**
- [x] Detect `-pooler` in `DATABASE_URL` hostname via new `_is_pooled_hostname()` helper (`backend/database.py`)
- [x] On pooled hostnames: skip the `pg_stat_ssl` assertion, log `tls=pooler-skip`, emit `db_tls_pooler_skip` secure event (sslmode still enforced in config.py)
- [x] On direct hostnames: retain the assertion (Neon direct endpoint, RDS, local postgres all continue to verify)
- [x] Unit tests cover all branches: pooler host with ssl_active=False doesn't crash, direct host with ssl_active=True still logs `db_tls_verified`, helper recognises pooler suffix (18/18 tests pass)
- [ ] **CEO deploy step:** Deploy; verify Render startup logs show `tls=pooler-skip` and no override warning
- [ ] **CEO env-var step:** Remove `DB_TLS_OVERRIDE` from Render env vars once startup is confirmed green
- [x] `DB_TLS_OVERRIDE` config path kept intact — it's a general break-glass used by both the `pg_stat_ssl` check AND the `sslmode` connection-string check in `config.py`; not pooler-specific, so deletion would lose a legitimate escape hatch.

**Review:**
- New helper `_is_pooled_hostname()` lives alongside imports in `backend/database.py`; it's a parse-and-substring test with no DB coupling (trivially unit-testable).
- The pooled branch short-circuits BEFORE the four-way `ssl_active / DB_TLS_OVERRIDE_VALID / DB_TLS_REQUIRED / else` logic, so `DB_TLS_REQUIRED=true` + pooler host no longer crashes startup.
- Secure event `db_tls_pooler_skip` added — distinct from `db_tls_verified` and `db_tls_override` so log audits can tell "TLS is actually on, just invisible" apart from "TLS is off, break-glass approved".
- Existing 15 TLS tests still pass unchanged; 3 new tests added (pooler skip, direct still runs, helper unit).

---


## Launch-Readiness Era (Sprints 673–710)

> Detail moved to [`tasks/archive/sprints-673-710-launch-readiness-era.md`](archive/sprints-673-710-launch-readiness-era.md) on 2026-04-22 as the four per-session sections (Post-Audit Remediation, Anomaly Framework Hardening, Security Hardening Follow-Ups, Design Refresh) totalled 1,160 lines. Only the still-open items are kept below so Active Phase scans cleanly.

### Archived-section open items

(Sprints 611 and 673 kept in Active Phase above with full detail — they're still-active work.)

- **Sprint 684 — MUS sampling Table A-1 compliance.** Shipped in bundle commit `9dd554a` alongside Sprint 682. Status in the archive doc reads "PENDING" from a stale checkbox; treat as COMPLETE.
- **Sprint 689 — Six hidden backend tools catalog reconciliation.** Decision brief at [`tasks/sprint-689-research-brief.md`](sprint-689-research-brief.md) with per-tool recommendation + evidence. **Default recommendations:** promote `sod` (already Enterprise-gated, ~1 sprint of UI); defer the other five (zero maintenance cost, no near-term ROI); correct CLAUDE.md "Tool #12" attribution (Statistical Sampling, not Multi-Currency — Multi-Currency is a deliberate side-car). CEO approves / overrides per tool.
- **Sprint 691 — Professional-tier DB enum + team-seat counting.** Research brief at [`tasks/sprint-691-research-brief.md`](sprint-691-research-brief.md). **Finding:** the one-line sprint title is underspecified — the schema is already in its clean Pricing-v3 state (`e3f4a5b6c7d8`, 2026-03-02), and no visible bug prompts a migration. Brief lays out three interpretations (add tier / rename tier / adjust seat counts) with file-level change lists. **Recommended:** CEO either (a) picks one interpretation or (b) closes the sprint as "superseded by Pricing v3 restructure."

### Design sprints — partial deliveries (follow-up work queued)

- **Sprint 702 — Auth-page polish.** Autofill fix + minimal wordmark landed (commit `8b75a86`). Full Vault framing (centered monogram, hairline card frame, "The Vault" italic) is a CEO stylistic pick; lands cleanly on top of the current commit when wanted.
- **Sprint 704 — Homepage composition rhythm.** `<EngravedStat>` + BottomProof retrofit shipped (`de6395b`). `<Section>` axis prop + full homepage re-sequence + `<Button>` variant system each deserve their own review PR — see archive for each deferred item's rationale.
- **Sprint 708 — Pricing page.** Brass foil Most Popular badge + editorial typography shipped (`87952dc`). Full page reorder (hero → FindYourPlan → sticky callout → SeatCalculator → plan cards) is a 914-line-file refactor deferred to its own sprint with design review.
- **Sprint 709 — Polish batch.** Demo copy + colophon + CTA label unification shipped (`1bfb868`). Favicon sharpness check deferred (requires manual browser-tab validation). Two items re-scoped after code inspection (contact alignment already correct; nav anchor hint premise didn't match code).

### Also queued

- **158 test-file type errors** surfaced by the Sprint 710 tsconfig split. Test runtime still green (1887/1887); fixing them would let `tsc --noEmit -p tsconfig.test.json` join CI as a gate. Dedicated clean-up sprint when the backlog allows.
- **Post-deploy smoke test** for the Sprint 696/697/698/699 end-to-end share-download flow — create a passcode-protected share from Enterprise, open `/shared/{token}` incognito, verify passcode prompt → download. Covers the Argon2id + per-token throttle + per-IP throttle + public share-receive page in one pass.

---

## Pending Actions (CEO-facing)

| # | Action | Unblocks |
|---|--------|----------|
| 1 | **Merge PR #93** at https://github.com/Paciolus/Paciolus/pull/93 | Sprints 703–709 design refresh to paciolus.com |
| 2 | **Watch first post-merge deploy** — expect one new alembic revision (`f7b3c91a04e2 → c1a5f0d7b4e2`) and the homepage `Every Test Cites Its Standard` section flipping from pill strip to specimen page | Sprint 696/697/698 schema + 705/706 homepage |
| 3 | **Post-deploy smoke test** — create one passcode share, download from `/shared/{token}` incognito | End-to-end Sprint 696–699 chain |
| 4 | **Remove `DB_TLS_OVERRIDE` env var** on Render once startup logs show `tls=pooler-skip` | Sprint 673 retire (override expires 2026-05-09) |
| 5 | **Stripe prod cutover** — drop the live-mode secret + publishable keys into Render env vars (`STRIPE_SECRET_KEY` + `STRIPE_PUBLISHABLE_KEY`) and ping for a test-charge verification | Sprint 447 |
| 6 | **Provision R2/S3 bucket** for ExportShare object-store | Sprint 611 |
| 7 | **Approve / override Sprint 689 decision brief** at [`tasks/sprint-689-research-brief.md`](sprint-689-research-brief.md) — per-tool recommendations with evidence; default path is promote `sod` + defer the other five + fix the "Tool #12" attribution | Sprint 689 + marketing copy truth |
| 8 | **Sprint 691 — pick an interpretation or close.** Brief at [`tasks/sprint-691-research-brief.md`](sprint-691-research-brief.md) names three possible intents (add tier / rename / adjust seat counts) with scope estimates. Default recommendation: close as superseded by Pricing v3 restructure unless a specific change is wanted. | Sprint 691 |
