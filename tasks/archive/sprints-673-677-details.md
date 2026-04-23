# Sprints 673–677 Details

> Archived from `tasks/todo.md` Active Phase on 2026-04-23.

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

### Sprint 677: Dead-code hygiene + route-wiring guardrail + deprecation register
**Status:** COMPLETE
**Source:** Targeted audit directive 2026-04-18 — safe dead-code pass, no behavior change

**Changes:**
- [x] Remove 11 unused locals flagged by ruff F841 across 7 production files:
  - `backend/bank_reconciliation_memo_generator.py` (rec_diff, match_rate)
  - `backend/je_testing_engine.py` (total_groups)
  - `backend/je_testing_memo_generator.py` (total_entries, preparer_total)
  - `backend/routes/three_way_match.py` (po_mapping, inv_mapping, rec_mapping — switched to `_ = ...` to preserve the `log_secure_operation` side effect inside `parse_json_mapping`)
  - `backend/sampling_memo_generator.py` (pop_type — both assignments unused)
  - `backend/shared/drill_down.py` (n_cols)
  - `backend/shared/tb_diagnostic_constants.py` (excess, and its only-feeder raw_sum)
- [x] Add `scripts/check_route_wiring.py` — scans `backend/routes/*.py`, flags modules not imported by `routes/__init__.py` or by the known aggregators (`audit.py`, `export.py`, `engagements.py`); exits non-zero on true orphans
- [x] Add `docs/runbooks/deprecations.md` — deprecation register with Active / Removed sections. Seeded with: `excel_generator.py` signoff fields, `pdf/orchestrator.py` signoff gating, `shared/schemas.py` signoff fields, `shared/parsing_helpers.py::safe_float` (monetary-unsafe), `frontend/src/utils/motionTokens.ts::DISTANCE`

**Verification:**
- `cd backend && python -m ruff check . --select F401,F841` on the seven target files: `All checks passed!` (target scope clean)
- `python scripts/check_route_wiring.py`: 58 modules scanned, 48 via `__init__.py`, 10 via aggregators, PASS
- Targeted pytest: `test_bank_rec_memo.py`, `test_je_testing_engine.py`, `test_je_testing_memo.py`, `test_three_way_match.py`, `test_sampling_memo.py`, `test_drill_down.py`, `test_diagnostics_api.py` → **315 passed, 1 warning in 10.53s**
- `test_contra_and_detection_fixes.py` (exercises `compute_tb_diagnostic_score`) → **69 passed in 0.82s**
- Backend smoke: `python -c "from main import app; ..."` → 239 routes registered, no regression

**Review:**
- `three_way_match` column mappings are intentionally discarded today (override wiring is a pre-existing gap). The `_ = ...` assignments keep `log_secure_operation` firing so the audit trail still shows receipt of the caller's JSON payload, and the inline comment flags the call site for whoever picks the wiring up.
- `raw_sum` in `tb_diagnostic_constants.py` was the sole feeder of the removed `excess`; the trimming algorithm that follows uses `capped` and `running` directly, so removing both cleans the function rather than leaving a dangling `raw_sum` warning for the next pass.
- `scripts/check_route_wiring.py` is wired to be CI-safe: no third-party deps, pure-stdlib regex, aggregator allowlist is explicit and easy to extend when a new aggregator pattern appears.
- The remaining 23 F841 warnings in `backend/tests/*.py` and 3 in `generate_sample_reports.py` are explicitly **out of scope** — cleaning test fixtures risks hiding intent (e.g., `user = make_user(...)` in webhook fixtures is descriptive even when the handle isn't referenced) and warrants a separate test-hygiene sprint.
- Residuals: `routes/three_way_match.py` override plumbing is now a documented follow-up rather than a silent drop; `backend/tests` F841 cleanup tracked for a future hygiene pass.


---

### Sprint 673: Remove DB_TLS_OVERRIDE via pooler-aware pg_stat_ssl skip
**Status:** COMPLETE (2026-04-23 — override removed from Render prod)
**Source:** Council Review 2026-04-16 — Critic (time-fused architectural debt) + Executor (front-run launch week)
**Why now:** `DB_TLS_OVERRIDE=NEON-POOLER-PGSSL-BLINDSPOT:2026-05-09` expires in 23 days. Without the proper fix landed first, the override must either be renewed (kicks the can) or allowed to expire (hard-fails production startup during Phase 4 launch window). Fixing before Phase 4 removes one ticking clock from launch week.
**File:** `backend/database.py`
**Problem:** Production startup runs a `pg_stat_ssl` check to confirm the DB connection is encrypted. Neon's pooled endpoint (`-pooler` hostname) is a transparent connection pooler — the underlying connection IS TLS-encrypted, but `pg_stat_ssl` reports the pooler-to-backend hop, not the client-to-pooler hop. The check therefore returns `ssl=false` on a correctly encrypted connection, forcing the current override.
**Changes:**
- [x] Detect `-pooler` in `DATABASE_URL` hostname via new `_is_pooled_hostname()` helper (`backend/database.py`)
- [x] On pooled hostnames: skip the `pg_stat_ssl` assertion, log `tls=pooler-skip`, emit `db_tls_pooler_skip` secure event (sslmode still enforced in config.py)
- [x] On direct hostnames: retain the assertion (Neon direct endpoint, RDS, local postgres all continue to verify)
- [x] Unit tests cover all branches: pooler host with ssl_active=False doesn't crash, direct host with ssl_active=True still logs `db_tls_verified`, helper recognises pooler suffix (18/18 tests pass)
- [x] **CEO deploy step (done 2026-04-23):** Sprint 673 code shipped to prod via the 2026-04-22 password-rotation redeploy (commit `937997a`); startup logs at 2026-04-22 16:49:08 UTC confirmed `tls=pooler-skip` on all 4 workers BEFORE today's env-var removal, so the override branch was already dead code.
- [x] **CEO env-var step (done 2026-04-23 10:26 UTC):** `DB_TLS_OVERRIDE` deleted from Render env vars; redeploy went green at 10:28 UTC (2 min). New instance `csfxr` — 4 fresh worker startups all logged `tls=pooler-skip`; zero matches for `DB_TLS_OVERRIDE` substring in last-hour logs; `/health` returns 200 in 355 ms. 2026-05-09 fuse cleared.
- [x] `DB_TLS_OVERRIDE` config path kept intact — it's a general break-glass used by both the `pg_stat_ssl` check AND the `sslmode` connection-string check in `config.py`; not pooler-specific, so deletion would lose a legitimate escape hatch.

**Review:**
- New helper `_is_pooled_hostname()` lives alongside imports in `backend/database.py`; it's a parse-and-substring test with no DB coupling (trivially unit-testable).
- The pooled branch short-circuits BEFORE the four-way `ssl_active / DB_TLS_OVERRIDE_VALID / DB_TLS_REQUIRED / else` logic, so `DB_TLS_REQUIRED=true` + pooler host no longer crashes startup.
- Secure event `db_tls_pooler_skip` added — distinct from `db_tls_verified` and `db_tls_override` so log audits can tell "TLS is actually on, just invisible" apart from "TLS is off, break-glass approved".
- Existing 15 TLS tests still pass unchanged; 3 new tests added (pooler skip, direct still runs, helper unit).
- **2026-04-23 verification chain:** env-var count 20 → 19 confirmed via DOM read; `DATABASE_URL` verified to still carry `sslmode=require` (config.py's URL-string TLS check remains satisfied independent of the override); fresh startup logs at 10:28:30–32 UTC on instance `csfxr` show `tls=pooler-skip` on all 4 workers; Render log search for `DB_TLS_OVERRIDE` returns "No matching logs" for the last hour — clean cut-over, no warnings.


---

