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

## Post-Audit Remediation Batch — 2026-04-20

> **Source:** Four-agent audit run 2026-04-20 (accounting-expert-auditor + backend/frontend/completeness Explore agents). 1 real CRITICAL backend bug, 5 CRITICAL accounting findings, 6 revenue-blocker gaps, ~15 HIGH, ~15 MEDIUM/LOW. Sprints below cluster findings by engine/theme to minimise touch-count and review overhead. Priority tags (P0/P1/P2) carry the audit's ranking; sprint order is execution-friendly, not strict priority.

---

### Sprint 677: Concentration % overflow + logo upload DB integrity
**Status:** PENDING
**Priority:** P0
**Source:** Backend-bugs agent (CRITICAL #1); Completeness agent (B-06)
**Why now:** One-line math bug publishes concentration percentages 100× too high (50% rendered as 5000%) in the API response and any persisted row — highest-impact / lowest-effort fix in the batch. Pair with the logo-upload integrity fix so the bundle is still one atomic PR.
**Files:**
- `backend/audit/rules/concentration.py:110`
- `backend/routes/branding.py:131-137`

**Changes:**
- [ ] `concentration.py:110` — drop the `* 100` multiplication; `concentration_pct` is already 0–1 (line 98 `:.1%` format string multiplies internally). Store the raw decimal in `"concentration_percent"` or rename the key to `"concentration_ratio"`.
- [ ] `branding.py:131-137` — only commit `branding.logo_s3_key` when `upload_bytes` actually returned True. Today an S3-unconfigured environment silently records a DB row that claims a logo exists but nothing is in storage. Combined with Sprint 679 this would become a data-integrity bug.
- [ ] Backfill check: add a migration note or admin script stub to null out `logo_s3_key` rows for which the S3 object is missing (defer actual cleanup to the Sprint 679 branch).
- [ ] Unit tests: concentration percentage under several balances (50%, 100%, 0.1%) to lock the new contract; `branding` upload failure path doesn't persist `logo_s3_key`.

---

### Sprint 678: Tier entitlement enforcement wire-up
**Status:** PENDING
**Priority:** P0 (revenue blocker)
**Source:** Completeness agent (B-02/B-03/B-04/B-05 + C-06)
**Why now:** Today a Free user can download every PDF/Excel/CSV export, upload every file format (OFX/QBO/PDF/ODS), and run 11 of 12 tools unbounded. The helpers exist; they're just never called. This single sprint closes the paid-tier moat without new engine work.
**Files:**
- `backend/shared/entitlement_checks.py` (reference — already defines helpers)
- `backend/routes/export_memos.py`, `export_diagnostics.py`, `export_testing.py`, `export_sharing.py`, `engagements_exports.py`, `loan_amortization.py`
- `backend/routes/multi_period.py`, `backend/routes/currency.py`
- All 11 testing-tool routes (JE/AP/Payroll/Revenue/AR/FA/Inventory/Bank Rec/Three-Way Match/Multi-Period/Sampling) — audit call sites for `check_upload_limit`
- `backend/routes/audit_pipeline.py` (already gated — reference pattern)

**Changes:**
- [ ] Wire `check_export_access` onto every export endpoint across all six export modules. Returns 403 when tier has `pdf_export=False and excel_export=False and csv_export=False` (i.e., Free).
- [ ] Wire `check_format_access` into the TB-upload and bulk-upload entrypoints so Free tier rejects OFX/QBO/IIF/PDF/ODS.
- [ ] Wire `check_upload_limit` (or `check_diagnostic_limit`) into the 11 testing-tool routes that currently bypass it. Use the `shared/testing_route.py:enforce_tool_access` pattern already in place on 6 of them.
- [ ] Add `enforce_tool_access` call sites to `routes/multi_period.py` and `routes/currency.py` (neither currently checks `tools_allowed`).
- [ ] Regression tests: a Free user (1) is rejected on all 18 memo exports, (2) is rejected on OFX/QBO/IIF/PDF/ODS upload, (3) trips the upload quota on JE/AP/Payroll job #11, (4) is rejected on `/audit/multi-period/compare` and `/audit/currency-rates`.
- [ ] Update `shared/entitlements.py:34-36,92-95` docstrings so the `pdf_export/excel_export/csv_export` booleans are noted as "enforced via `check_export_access`" — leaves no ambiguity for the next auditor.

---

### Sprint 679: Enterprise PDF branding end-to-end
**Status:** PENDING
**Priority:** P0 (feature-parity gap on Enterprise tier)
**Source:** Completeness agent (B-01)
**Why now:** Pricing page, Terms page, UpgradeModal, Settings, and `domain/pricing.ts` all sell "Custom PDF branding" as the Enterprise differentiator. The `FirmBranding` model, S3 upload, and entitlement gate all exist. **Zero PDF generator reads `logo_s3_key`, `header_text`, or `footer_text`.**
**Files:**
- `backend/routes/branding.py` (data source)
- `backend/pdf_generator.py` + every `backend/*_memo_generator.py` (~18 generators)
- `backend/shared/pdf_branding.py` — new helper
- `backend/shared/storage_client.py` — add signed-URL fetch helper if missing

**Changes:**
- [ ] New `backend/shared/pdf_branding.py` — loads the calling user's `FirmBranding` row (with org fallback), downloads logo bytes from S3, returns a `PDFBrandingContext` dataclass (`logo_bytes: bytes | None, header_text: str | None, footer_text: str | None, tier_has_branding: bool`).
- [ ] Extend base PDF generator header/footer to accept a `PDFBrandingContext` — when `tier_has_branding` is True, render the logo at top-left and `header_text`/`footer_text` at the margins; otherwise render Paciolus default.
- [ ] Wire the context load through every memo generator and the three report PDFs (combined audit, FS, anomaly summary). One call site per generator; data flows from the route `current_user`.
- [ ] E2E test: Enterprise user uploads logo → generates a memo → resulting PDF contains the logo at top-left and the configured `header_text`. Repeat for a Solo user → logo is ignored, default Paciolus branding appears.
- [ ] Sprint 677's `logo_s3_key` integrity fix must land first (or in the same PR) to avoid rendering a "missing logo" error when the S3 object was never persisted.
- [ ] Update CEO checklist in `ceo-actions.md` Phase 3 to note the branding round-trip is now live.

---

### Sprint 680: ISA 315 combined-risk matrix
**Status:** PENDING
**Priority:** P1 (standards compliance)
**Source:** Accounting-expert-auditor C-4
**Why now:** Current `compute_combined_risk_level` returns `max(IR, CR)`, which is not the ISA 315 Appendix 1 method. Moderate × moderate should yield elevated RMM; today it returns moderate, so the tool systematically undercounts elevated-risk account/assertion pairs. Composite risk scoring is in CLAUDE.md's "Key Capabilities" — misrepresenting ISA 315 is a defensibility issue.
**Files:**
- `backend/composite_risk_engine.py:109–119, 140–152`

**Changes:**
- [ ] Replace the `max()` branch with a 3×3 (or 4×4 if we carry a "low" granularity) RMM lookup table keyed on `(inherent_level, control_level)` per ISA 315 Appendix 1.
- [ ] Delete or correct the "(conservative approach)" comment — max is not conservative; the matrix is.
- [ ] Expand `overall_risk_tier` to factor in detection risk (audit risk = IR × CR × DR) or explicitly document that detection risk is outside scope of this engine.
- [ ] Regression tests: every IR×CR cell produces the expected RMM per the table; the aggregate tier changes for a test population where IR and CR are both moderate.
- [ ] Update the disclaimer shown in the composite-risk memo to reference ISA 315 Appendix 1 explicitly.

---

### Sprint 681: Ratio engine — average-balance denominators + ICR + DuPont
**Status:** PENDING
**Priority:** P1 (formula correctness)
**Source:** Accounting-expert-auditor C-2/C-3/H-1/H-4/L-1/L-2
**Why now:** ROA/ROE/DSO/DPO all use ending TB balances in places where standard formulas require averages. For any entity with movement in receivables/assets/equity the ratio is materially distorted. ICR double-counts interest expense when the chart of accounts nests it under operating expenses. DuPont decomposition's `verification_matches` likely uses exact float equality.
**Files:**
- `backend/ratio_engine.py:276-296, 679-680, 730-731, 785-786, 867, 924`
- `backend/ar_aging_engine.py:79-83` (DSO consumer)

**Changes:**
- [ ] Add optional `prior_period_totals` parameter to the `RatioEngine` constructor. When provided, ROA/ROE/DSO/DPO/DIO/CCC compute `(beginning + ending) / 2`; when absent, use ending balance and attach a `formula_disclosure` field explaining the approximation.
- [ ] DPO denominator: switch to Purchases = COGS + ΔInventory when both periods are available; otherwise COGS with disclosure note.
- [ ] ICR: subtract `interest_expense` from `operating_exp` before computing EBIT to avoid the double-penalty when COA nests interest under opex.
- [ ] DuPont `verification_matches`: compare with `math.isclose(roe, decomposed_roe, rel_tol=1e-6)` instead of exact equality.
- [ ] Regression tests: an entity with 20% AR growth shows different DSO under ending vs. average; DuPont `verification_matches=True` for all legitimate decompositions.
- [ ] Propagate `prior_period_totals` plumbing through `routes/audit_pipeline.py` and `routes/ratios.py` (accept optional uploaded prior-period TB; if absent, compute with disclosure).
- [ ] Update memo copy in every ratio memo generator to reference the disclosure when applicable.

---

### Sprint 682: Easy-win audit test additions (payroll + FA + AP + inventory)
**Status:** PENDING
**Priority:** P1 (tool completeness)
**Source:** Accounting-expert-auditor H-2/H-3/M-5/M-6
**Why now:** Four standard substantive procedures are trivially implementable from columns already detected. Each is a first-line fraud/impairment indicator cited in AICPA/IAS/ASC literature. All four share a "detect column → arithmetic check → flag" shape.
**Files:**
- `backend/payroll_testing_engine.py` — new test PR-T12
- `backend/fixed_asset_testing_engine.py` — new test FA-T10
- `backend/ap_testing_engine.py` — new test AP-T14
- `backend/inventory_testing_engine.py` — new test INV-T10

**Changes:**
- [ ] **PR-T12 Gross-to-Net Reconciliation:** flag rows where `|gross_pay − deductions − net_pay| > $0.01`. AICPA EBP Audit Guide Ch. 5.
- [ ] **FA-T10 Depreciation Recalculation:** when prior-period accum-depr + method + useful life are present, recalc expected annual depreciation (SL: `(cost − residual) / life`; DDB: `2/life × NBV`) and flag variance > 5%. IAS 16 / ASC 360.
- [ ] **AP-T14 Invoice Without PO:** when a "PO Number" column is detected, flag payments above materiality with blank PO. ACFE 2024 — billing schemes = 19% of occupational fraud.
- [ ] **INV-T10 LCM/NRV Indicator:** when a selling-price or NRV column is detected, flag rows where `unit_cost > selling_price × (1 − expected_margin_floor)`. IAS 2.9 / ASC 330-10.
- [ ] Register each new test in the engine's test catalog, memo generator, CSV export schema, and entitlement matrix.
- [ ] Tests per new test: happy path, edge cases (missing column → skip with status note, zero/negative values).
- [ ] Update marketing copy: "19 JE tests, 14 AP tests, 12 payroll tests, 10 FA tests, 10 inventory tests" etc. — flow through CLAUDE.md, pricing page, memo titles.

---

### Sprint 683: Revenue testing refinements (RT-07 + RT-09 + ASC 606 Steps 1/3)
**Status:** PENDING
**Priority:** P1
**Source:** Accounting-expert-auditor H-5/M-2/M-8
**Why now:** RT-09 mislabels prior-period entries as "cut-off risk" — two distinct assertions. RT-07 injects a synthetic `[Aggregate Revenue]` row (`row_number=0`) into `flagged_entries` so PDF memos render an aggregate observation as if it were a GL line. ASC 606 Step 1 (contract identification) and Step 3 (transaction price / variable consideration constraint) have no tests; these are the most common revenue-recognition fraud vectors.
**Files:**
- `backend/revenue_testing_engine.py:1194-1211, 1351-1382, 1660-1890`
- `backend/revenue_testing_memo_generator.py`

**Changes:**
- [ ] Split RT-09 into two tests: `RT-09 Cut-Off Risk` (near period end only) and `RT-09b Prior-Period Timing` (near period start only). Update test descriptions and assertion mapping.
- [ ] Refactor `RevenueTestResult` to add `aggregate_findings: list[AggregateFinding]`; move RT-07's variance finding out of `flagged_entries`. Update the memo generator detail tables to render aggregates in a separate section.
- [ ] **RT-17 Step 1 Contract Validity:** flag recognition entries with missing customer ID, missing commercial-substance indicator (when a column is provided), or recognition without a prior contract-inception date.
- [ ] **RT-18 Step 3 Variable Consideration Constraint:** flag entries where `recognition_method=point-in-time` but `satisfaction_date` is blank, or where recognized amount exceeds contract price without a modification flag.
- [ ] Regression tests for both splits and both new tests.

---

### Sprint 684: MUS sampling standards compliance
**Status:** PENDING
**Priority:** P1 (standards compliance — most material auditor-facing defect)
**Source:** Accounting-expert-auditor C-1/M-1/L-3
**Why now:** Sampling is workpaper-bearing — sample sizes and evaluations get cited in engagement files. Homemade expansion factor understates samples ~4.6% at e/TM=0.25 vs. AICPA Audit Sampling Guide Table A-1. Inline TODO already acknowledges this.
**Files:**
- `backend/sampling_engine.py:297-318, 349-350, 472`
- `backend/sampling_memo_generator.py`
- `backend/shared/aicpa_tables.py` — new

**Changes:**
- [ ] Create `shared/aicpa_tables.py` with AICPA Audit Sampling Guide Table A-1 as a dict keyed on `(confidence_level, e_over_tm_bucket)` where buckets = {0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50}. Linear-interpolate between buckets.
- [ ] Replace the scalar expansion-factor math with the table lookup; keep the old path behind a `use_legacy_expansion=False` default-off flag for one release, then remove.
- [ ] Fix `sample_value` in the Stringer-bound evaluation to sum the entire selected sample's recorded value, not just the error items.
- [ ] Reject negative-balance items from MUS selection with an explicit "MUS applies to positive-balance populations only" warning. Document that understatement testing on negative balances requires a separate stratum.
- [ ] Regression tests: size(N=1M, conf=95%, e/TM=0.25, TM=$50K) matches Table A-1 value within rounding; size with no expected misstatement unchanged from current; Stringer `sample_value` matches total recorded value of selected items; MUS with mixed-sign population returns the warning and excludes negatives.
- [ ] Memo copy update — reference "AICPA Audit Sampling Guide, Table A-1" explicitly.

---

### Sprint 685: ISA 570 going concern expansion + test dedup
**Status:** PENDING
**Priority:** P1
**Source:** Accounting-expert-auditor C-5/M-4
**Why now:** Tool ships 6 indicators vs. ISA 570.16's ~20. Tests 2 and 3 are mathematically equivalent (current ratio < 1.0 ⇔ negative working capital) so the "2-of-6 indicators" threshold is implicitly 1-of-5. An auditor using this tool as a checklist prompt would miss major ISA 570.16 categories.
**Files:**
- `backend/going_concern_engine.py`
- `backend/going_concern_memo_generator.py`

**Changes:**
- [ ] Consolidate tests 2 (current ratio < 1.0) and 3 (negative working capital) into one test; keep the dollar-magnitude working-capital output (more informative for GC).
- [ ] Add cash-flow-based indicator: when a cash flow statement is derived, flag negative operating cash flow ≥ materiality threshold.
- [ ] Add covenant-breach indicator: take user-configurable thresholds (interest coverage minimum, debt/equity maximum, current ratio minimum); flag breaches.
- [ ] Add qualitative prompts (not detectable from TB but auditor-entered): loss of key customer, loss of key management, labor disputes, pending litigation, non-compliance with capital requirements. These render as *unchecked* by default in the memo with a note "requires auditor judgment — not TB-derivable."
- [ ] Update the ISA 570 disclaimer to list which categories are TB-derived vs. auditor-judgment-required.
- [ ] Regression tests: 2/3 merger doesn't double-count; cash-flow indicator fires on synthetic negative-opcf data; threshold count matches the new indicator list.

---

### Sprint 686: JE test tuning — Benford minimum + reversal window
**Status:** PENDING
**Priority:** P2
**Source:** Accounting-expert-auditor H-6/H-7
**Why now:** JE T14 (reciprocal entries) uses a flat 7-day window with no period-boundary awareness — legitimate first-of-next-month accrual reversals trigger false positives. Benford minimum of 500 is overly conservative vs. Nigrini (2012) which specifies 300+ for first-digit tests.
**Files:**
- `backend/je_testing_engine.py:98, 133`

**Changes:**
- [ ] `benford_min_entries: int = 300` (down from 500) for first-digit JE analysis. Keep `benford_min_magnitude_range = 2` (already correct per Nigrini).
- [ ] Refactor T14 into three tiers: same-period reversal (high suspicion), first-day-of-next-month reversal (low suspicion — standard accrual reversal, flag with note only), mid-period cross-month reversal (medium suspicion). Output a `reversal_category` field.
- [ ] Regression tests: 400-entry population now runs Benford (previously skipped); accrual reversal on day 1 of next month renders as "low" category; mid-month reversal renders "medium."

---

### Sprint 687: AR-aging silent date default + ASSET_KEYWORDS cleanup
**Status:** PENDING
**Priority:** P2
**Source:** Accounting-expert-auditor M-3/M-7
**Why now:** When `as_of_date` is missing, AR aging silently falls back to `date.today()` — a TB uploaded in April for a December 31 year-end overstates aging by ~120 days across every bucket. Separately, the legacy `ASSET_KEYWORDS` list is missing "investments/securities/goodwill/intangible/rou asset/deferred tax asset" and is still in `__all__` so external callers can hit it.
**Files:**
- `backend/ar_aging_engine.py:863`
- `backend/audit/classification.py:31-41`
- `backend/audit_engine.py:17` (re-export)

**Changes:**
- [ ] `_compute_aging_days`: when `ref is None`, raise a `ValueError("AR aging requires an explicit as_of_date")` instead of silently defaulting to `date.today()`. Route handler catches and returns 400 with a clear message.
- [ ] Extend `ASSET_KEYWORDS` to include `investments, securities, deposits, goodwill, intangible, leasehold, right-of-use, rou asset, deferred tax asset, notes receivable, other receivable`.
- [ ] Either remove `ASSET_KEYWORDS` from `__all__` and re-exports (production uses weighted `AccountClassifier` now), or keep but document the legacy status in a module-level comment.
- [ ] Regression tests: AR aging with missing `as_of_date` returns 400; classifier correctly tags "Goodwill", "ROU Asset", "Deferred Tax Asset".

---

### Sprint 688: Composite Risk + Account Risk Heatmap frontend
**Status:** PENDING
**Priority:** P2 (feature completeness — marketed in CLAUDE.md)
**Source:** Completeness agent H-01/H-02
**Why now:** Both tools ship with full backend engines, routes, and tests; neither has a single line of frontend code. CLAUDE.md markets both under "Key Capabilities." Either wire the UI or stop marketing them.
**Files (new):**
- `frontend/src/types/compositeRisk.ts`, `hooks/useCompositeRisk.ts`, `components/compositeRisk/*`, `app/tools/composite-risk/page.tsx`
- `frontend/src/types/accountRiskHeatmap.ts`, `hooks/useAccountRiskHeatmap.ts`, `components/accountRiskHeatmap/*`, `app/tools/account-risk-heatmap/page.tsx`

**Changes:**
- [ ] Composite Risk: auditor-input workflow (inherent/control/fraud risk per account/assertion) → combine with TB/testing signals → render RMM matrix + priority table. Bind to existing `/composite-risk/*` endpoints.
- [ ] Account Risk Heatmap: render the heatmap + CSV download. Bind to existing `/account-risk-heatmap/*` endpoints.
- [ ] Add both to `app/tools/page.tsx` catalog and `lib/commandRegistry.ts`.
- [ ] Both pages use Oat & Obsidian tokens, Reveal scroll-reveal, and tier-gating per `useEntitlements`.
- [ ] Jest tests for hook + at least one components/page happy path per tool.

---

### Sprint 689: Hidden backend tools — catalog wire-up or removal
**Status:** PENDING
**Priority:** P2
**Source:** Completeness agent H-03/H-05 + Claim-reality C-03/C-04
**Why now:** Six backend tools have endpoints and no UI: `book_to_tax`, `cash_flow_projector`, `intercompany_elimination`, `form_1099`, `w2_reconciliation`, `sod`. Separately, Multi-Currency is marketed as Tool #12 but is only a side-car on TB upload — no standalone card. Decide per-tool: promote to catalog or remove the route.
**Files:**
- `backend/routes/{book_to_tax, cash_flow_projector, intercompany_elimination, form_1099, w2_reconciliation, sod}.py`
- `frontend/src/app/tools/page.tsx`, `lib/commandRegistry.ts`
- `shared/entitlements.py:14` (canonical tool count)

**Changes:**
- [ ] For each of the six: CEO decides [promote / defer / remove]. Default recommendation:
  - `sod` — already Enterprise-gated; promote with minimal UI.
  - `form_1099`, `w2_reconciliation` — payroll-adjacent; promote under the Payroll tool umbrella as sub-workflows.
  - `book_to_tax`, `cash_flow_projector`, `intercompany_elimination` — remove routes if not shipping Tool #13+, document rationale in a sprint archive entry.
- [ ] Multi-Currency: add a standalone `/tools/multi-currency` card with its own page; continue rendering the side-car on TB upload for convenience.
- [ ] Reconcile `CANONICAL TOOL COUNT` in `shared/entitlements.py:14` with the final catalog count; propagate to CLAUDE.md, pricing page, ceo-actions.md, and marketing surfaces.
- [ ] Regression tests: every cataloged tool has a route, hook, page, and entitlement-gate test.

---

### Sprint 690: Stripe trial-ending email
**Status:** PENDING
**Priority:** P2
**Source:** Completeness agent H-04
**Why now:** `webhook_handler.py` receives `customer.subscription.trial_will_end`, logs it, records a `TRIAL_ENDING` analytics event, and does nothing else. Docstring explicitly says "Notification email infrastructure deferred to a future sprint." Users don't get the standard 3-day warning.
**Files:**
- `backend/billing/webhook_handler.py:532-560`
- `backend/shared/email_client.py` (or wherever SendGrid calls live)
- `frontend/src/components/marketing/emails/trial-ending.mjml.tsx` (or equivalent template path)

**Changes:**
- [ ] New email template for trial ending with days-remaining, upgrade CTA, cancellation-instructions link.
- [ ] In the `trial_will_end` branch, call the SendGrid send helper with the template; retain the analytics event.
- [ ] Add a unit test (mock SendGrid) that verifies the send call + args; add an integration test that runs the webhook handler end-to-end.
- [ ] Update `tasks/pricing-launch-readiness.md:48` acceptance note — trial email no longer deferred.

---

### Sprint 691: Professional-tier DB enum + team-seat counting
**Status:** PENDING
**Priority:** P2
**Source:** Completeness agent H-07/H-08
**Why now:** `UserTier.PROFESSIONAL` is still in the DB enum but unpurchasable; legacy Professional users map to Solo entitlements. `pricing-launch-readiness.md:49-50` flagged team-member counting as a placeholder; hard-mode seat enforcement landed in `config.py:456` but the underlying counting logic was never verified.
**Files:**
- `backend/models.py` (UserTier enum)
- `backend/shared/entitlements.py` (Professional mapping)
- `backend/billing/seat_enforcement.py` or equivalent — wherever active-member counting lives
- Alembic migration (new)

**Changes:**
- [ ] Alembic migration: collapse `PROFESSIONAL` values to `SOLO` across `users.tier`; drop `PROFESSIONAL` from the enum (Postgres enum alter sequence: add new enum without PROFESSIONAL → copy → drop old). Backfill any Professional users to Solo with a logged event.
- [ ] Remove Professional-specific code paths from `shared/entitlements.py` and tests.
- [ ] Audit the active-member counting function: does it count pending invitations? terminated users? multi-org members? Build a concrete test matrix and exercise each.
- [ ] Verify Enterprise seat-hit returns 402 and frontend UpgradeModal surfaces it correctly.
- [ ] Sign-off note in `pricing-launch-readiness.md`.

---

### Sprint 692: Documentation drift correction
**Status:** PENDING
**Priority:** P2 (launch documentation hygiene)
**Source:** Completeness C-01/C-02/C-03/C-04/C-07 + Accounting H-8
**Why now:** "21 PDF memos" is actually 18 memos + 3 report PDFs. "24 export endpoints" is actually ~27. CLAUDE.md says 12 tools; frontend catalog shows 15. `pricing-launch-readiness.md` hasn't been re-signed since 2026-02-25 — pre-dates Phase 1 deploy, Pricing v3, Sprint 673, and Stripe live cutover.
**Files:**
- `CLAUDE.md`
- `frontend/src/app/(marketing)/pricing/page.tsx` + `components/marketing/ToolShowcase.tsx`
- `tasks/ceo-actions.md`
- `tasks/pricing-launch-readiness.md`
- `memory/*.md` (per-user)
- `backend/engagement_manager.py:163` + `backend/materiality_resolver.py:34` — materiality cascade disclosure

**Changes:**
- [ ] Replace "21 PDF memos" with "18 memo PDFs + 3 report PDFs (combined audit, financial statements, anomaly summary)" across CLAUDE.md, ceo-actions.md, marketing copy. Or reclassify and land on a single number.
- [ ] Recount export endpoints (`grep -rn "@router" backend/routes/export*.py engagements_exports.py loan_amortization.py`) and publish the exact number in CLAUDE.md.
- [ ] Reconcile "12 tools" vs. "15 catalog cards" — align after Sprint 689 lands.
- [ ] Materiality cascade: ensure every memo that references thresholds states explicitly that clearly-trivial = 5% of overall (not performance) materiality and PM = 75% of overall.
- [ ] `pricing-launch-readiness.md`: re-sign Section 7 after Sprints 677-679 (pricing enforcement + branding) are verified. Blocks Phase 4.1 per `ceo-actions.md:114`.
- [ ] Update `CLAUDE.md` test count to the current nightly total after all remediation sprints land.

---

### Sprint 693: Frontend polish — framer-motion + silent catches
**Status:** PENDING
**Priority:** P3
**Source:** Frontend-bugs agent (4 HIGH + 2 silent catches)
**Why now:** Five minor improvements, bundleable into one PR. No functional bugs; type-safety + observability only.
**Files:**
- `frontend/src/app/(auth)/verification-pending/page.tsx:70`
- `frontend/src/app/(auth)/verify-email/page.tsx:95, 112, 131`
- `frontend/src/app/tools/page.tsx:72`
- `frontend/src/hooks/useTrialBalanceUpload.ts:249`

**Changes:**
- [ ] Add `as const` to all four `type: 'spring'` framer-motion transitions in the auth pages.
- [ ] Replace `.catch(() => {})` in `tools/page.tsx:72` and `useTrialBalanceUpload.ts:249` with a structured logger call (`logger.warn(...)` or Sentry breadcrumb) — silent catches hide bugs in preference loading and telemetry.
- [ ] No new tests needed; existing suites cover behaviour.

---

### Sprint 695: High-assurance financial-report remediation (RPT-11 / DASH-01 / RPT-02 / RPT-07)
**Status:** COMPLETE
**Priority:** P0 (financial-calculation correctness)
**Source:** Post-audit high-assurance remediation brief 2026-04-20 — CPA-facing correctness bar, validate-then-fix.

**Why now:** Five confirmed defects in financial-report engines spanning three-way match variance math, dashboard taxonomy, and multi-period variance configuration — all in the CPA-facing output surface where a single wrong percentage erodes auditor trust.  Three additional suspicions required test-first validation before touching logic.

**Confirmed defects — FIXED:**
- [x] **RPT-11 price variance denominator** (`backend/three_way_match_engine.py`): replaced `config.price_variance_threshold` / `config.amount_tolerance` denominator guards with a monetary epsilon (`MONETARY_EPSILON = Decimal("0.005")`).  The 5% decision threshold was being used as a "$0.05 is close enough to zero" guard, mis-flagging every sub-$0.05 unit price at 100% variance.  Quantities use a separate count-space epsilon (`1e-6`).  Decimal-first arithmetic preserved.
- [x] **RPT-11 match-rate denominator** (same file, `run_three_way_match`): denominator now `max(len(pos), len(invoices), len(receipts), 1)`.  Added `match_rate_denominator` + `match_rate_denominator_source` response fields for audit-workpaper traceability.  Partial-delivery scenarios (receipts > POs) no longer inflate full-match rate above 1.0.
- [x] **RPT-11 route config overrides** (`backend/routes/three_way_match.py`): seven optional form fields + `_build_twm_config` with bounded validation (HTTP 400 on out-of-range); defaults preserved for every existing client.
- [x] **DASH-01 tier taxonomy mismatch** (`backend/shared/testing_enums.py` + `backend/engagement_dashboard_engine.py`): new shared `normalize_risk_tier` maps 3-tier `medium` → canonical 4-tier `moderate` plus defensive legacy-alias handling (`critical`/`minimal`/...).  Three-way-match reports no longer vanish from the dashboard priority-action list.
- [x] **RPT-02 configurable significance thresholds** (`backend/multi_period_comparison.py` + `backend/routes/multi_period.py`): new `SignificanceThresholds` dataclass; `compare_trial_balances` / `compare_three_periods` / `classify_significance` accept optional overrides.  API exposes `significant_variance_percent` / `significant_variance_amount` with bounded validation.  Active thresholds emitted in `active_thresholds` response field.

**Suspicions — resolved via test-first:**
- [x] **RPT-02 signed variance basis — REJECTED.** `abs(prior_balance)` denominator is intentional; pairs with credit-normal display sign-flip in `AccountMovement.to_dict`.  Locked behaviour in `TestRPT02SignedVarianceSuspicion` (5 tests, including sign-change + abs-symmetry properties the display layer depends on).
- [x] **RPT-07 non-deterministic aging — CONFIRMED.** `_compute_aging_days` no longer falls back to `date.today()`: returns `None` when no reference supplied, raises `ValueError` on unparseable dates.  Route rejects sub-ledger uploads without `as_of_date` (HTTP 400).  Lands the Sprint 687 fix early on CPA-correctness grounds.
- [x] **Cross-report float precision — ACCEPTED as-is with pinning tests.** Three-way match keeps Decimal end-to-end through the engine; multi-period converts at `calculate_movement`.  `TestCrossReportPrecisionBoundaries` pins the conversion boundaries so future refactors cannot silently drift.  Deeper Decimal migration across the other 15 engines is out-of-scope (no material-drift finding).

**Test additions:**
- `backend/tests/test_remediation_2026_04_20.py` — 39 tests, all pass.

**Validation:**
- `pytest tests/test_remediation_2026_04_20.py` → 39 passed.
- Touched-engine regression sweep (`test_three_way_match` + `test_multi_period_comparison` + `test_ar_aging_engine` + `test_flag_regressions`) → 269 passed.
- Route/memo sweep (`test_ar_aging*` + `test_multi_period_*` + `test_engagement_dashboard_memo` + `test_twm_memo` + `test_api_contracts` + `test_export_testing_routes`) → 424 passed.
- Broad touch-domain filter (`-k "dashboard or multi_period or three_way or ar_aging or movement or significance or variance"`) → 680 passed / 9 xfailed / 0 failed.

**Behaviour changes requiring stakeholder notice:**
1. Three-way match `full_match_rate` denominator now includes receipts — rates shift downward when receipt population exceeds PO/invoice (split deliveries).  Memos that quote the rate should cite the new `match_rate_denominator_source`.
2. AR-aging API rejects sub-ledger uploads without `as_of_date` (HTTP 400 instead of silent `date.today()` fallback).
3. Multi-period API adds `significant_variance_percent` / `significant_variance_amount` (both optional — historical 10% / $10,000 preserved when omitted); response now includes `active_thresholds` for audit traceability.
4. Engagement dashboard surfaces `medium` three-way-match findings as `moderate` — these previously never appeared in the priority-action list.

**Review:**
Nothing weakened — auth/security/zero-storage untouched, no tests silenced, every formula change has a paired test.  The RPT-02 "signed variance" suspicion turned out to be INTENTIONAL platform policy; rejecting it was the correct call per the test-first directive, and the pinning tests prevent a future "fix" from breaking the credit-normal display contract.

---

### Sprint 694: Coverage Sentinel non-prod ignore list
**Status:** PENDING
**Priority:** P3
**Source:** Completeness S-04
**Why now:** Nightly Coverage Sentinel top-10 includes `generate_sample_reports.py`, `scripts/validate_report_standards.py`, and the Alembic baseline migration every night. These are non-production but unlabelled — creates signal noise in the nightly report.
**Files:**
- `scripts/overnight/agents/coverage_sentinel.py` (or its config file)

**Changes:**
- [ ] Add an explicit ignore list for non-production files: `generate_sample_reports.py`, `scripts/validate_report_standards.py`, any `alembic/versions/*baseline*.py`.
- [ ] Emit a "non-production excluded: N files" line in the report so the exclusion is visible.
- [ ] Verify next-night report's top-10 becomes meaningful.

---
