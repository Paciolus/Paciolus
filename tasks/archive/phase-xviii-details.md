# Archived Sprint Details: Phase XVIII

> **Archived:** 2026-02-12 — Moved from todo.md to reduce context bloat.
> **These are completed sprint checklists. For current work, see todo.md.**

---

## Phase XVIII: Async Architecture Remediation (Sprints 164-170)

> **Focus:** Fix systemic async anti-patterns — sync I/O on event loop, missing BackgroundTasks, DI consistency
> **Source:** Comprehensive 5-agent async audit (2026-02-12)
> **Strategy:** Mechanical `async def` → `def` conversions first (zero-risk), then `asyncio.to_thread()` wrapping, then BackgroundTasks, then cleanup
> **Impact:** Unblocks event loop under concurrent load; 100–500ms faster registration/contact; eliminates memory leak risk

### Sprint 164 — Convert pure-DB routes from `async def` to `def`
> **Complexity:** 3/10 | **Risk:** Low (mechanical change, no behavior difference)
> **Rationale:** FastAPI auto-threadpools `def` handlers, making sync SQLAlchemy safe. Endpoints that never `await` gain nothing from `async def` and actively block the event loop.

- [x] **auth.py dependencies:** Convert `get_current_user()`, `require_current_user()`, `require_verified_user()` from `async def` → `def`; remove `await` in `require_verified_user`'s direct call
- [x] **routes/auth_routes.py:** Convert all 7 endpoints (`register`, `login`, `get_current_user_info`, `get_csrf_token`, `verify_email`, `resend_verification`, `get_verification_status`) to `def`
- [x] **routes/users.py:** Convert `update_profile`, `change_password` to `def`
- [x] **routes/clients.py:** Convert all 7 endpoints (`get_industries`, `get_lead_sheet_options_endpoint`, `get_clients`, `create_client`, `get_client`, `update_client`, `delete_client`) to `def`
- [x] **routes/activity.py:** Convert all 4 endpoints to `def`
- [x] **routes/settings.py:** Convert all 6 endpoints to `def`
- [x] **routes/engagements.py:** Convert all 10 endpoints to `def`
- [x] **routes/follow_up_items.py:** Convert all 11 endpoints to `def`
- [x] **routes/adjustments.py:** Convert all 10 endpoints to `def`
- [x] **shared/helpers.py:** Convert `require_client()` from `async def` → `def` (kept `validate_file_size` as `async def` — legitimately awaits `file.read()`)
- [x] Verify: `pytest` passes (2,716 tests — 0 failures)
- [x] Verify: `npm run build` passes

#### Review
> **Status:** COMPLETE
> **Files Modified:** `auth.py`, `shared/helpers.py`, `routes/{auth_routes,users,clients,activity,settings,engagements,follow_up_items,adjustments}.py` (10 files)
> **Notes:** 58 endpoint/dependency conversions total. All `async def` functions that never `await` converted to `def`. FastAPI auto-threadpools these, unblocking the event loop for concurrent requests. Zero behavior change — just better concurrency under load.

---

### Sprint 165 — Wrap Pandas/engine CPU-bound work in `asyncio.to_thread()`
> **Complexity:** 5/10 | **Risk:** Medium (requires keeping `async def` for endpoints that `await validate_file_size()`)
> **Rationale:** File upload endpoints must stay `async def` because they `await validate_file_size(file)`. The subsequent Pandas parsing + engine computation must be offloaded to avoid blocking the event loop for 5–60s on large files.

- [x] **routes/audit.py — `audit_trial_balance`:** Wrap `audit_trial_balance_streaming()` call in `asyncio.to_thread()`
- [x] **routes/audit.py — `inspect_workbook_endpoint`:** Wrap `inspect_workbook()` call in `asyncio.to_thread()`
- [x] **routes/audit.py — `flux_analysis`:** Wrap all StreamingAuditor + FluxEngine work in `asyncio.to_thread()`
- [x] **shared/testing_route.py — `run_single_file_testing()`:** Wrap `parse_uploaded_file()` + engine callback in `asyncio.to_thread()` (covers 6 tools: JE, AP, Payroll, Revenue, Fixed Asset, Inventory)
- [x] **routes/ar_aging.py:** Wrap `parse_uploaded_file()` + `run_ar_aging()` in `asyncio.to_thread()`
- [x] **routes/three_way_match.py:** Wrap parsing + matching in `asyncio.to_thread()`
- [x] **routes/bank_reconciliation.py:** Wrap parsing + reconciliation in `asyncio.to_thread()`
- [x] **routes/multi_period.py:** Convert 3 endpoints from `async def` → `def` (never `await`; FastAPI auto-threadpools)
- [x] **routes/je_testing.py:** Wrap sampling + preview endpoints in `asyncio.to_thread()`
- [x] ~~**routes/financial_statements.py:**~~ N/A — builder only used in export route (Sprint 166)
- [x] Verify: `pytest` passes (2,716 tests — 0 failures)
- [x] Verify: `npm run build` passes

#### Review
> **Status:** COMPLETE
> **Files Modified:** `shared/testing_route.py`, `routes/{audit,ar_aging,three_way_match,bank_reconciliation,multi_period,je_testing}.py` (7 files)
> **Notes:** Pattern: read file bytes with `await validate_file_size()` (async I/O), then wrap all Pandas parsing + engine computation in `asyncio.to_thread(_process)`. Multi-period endpoints converted to `def` instead — they receive JSON (not files) and never `await`, so FastAPI's auto-threadpool achieves the same concurrency benefit more cleanly. JE testing had 2 additional endpoints (sampling + preview) beyond the factory-covered main endpoint. Financial statements builder is only invoked in export routes, handled by Sprint 166.

---

### Sprint 166 — Convert export route `async def` → `def` (FastAPI auto-threadpool)
> **Complexity:** 3/10 | **Risk:** Low (mechanical change, no behavior difference)
> **Rationale:** All 24 export endpoints are `async def` but never `await`. Per Sprint 164/165 pattern, converting to `def` lets FastAPI auto-threadpool them, unblocking the event loop for concurrent requests.

- [x] **routes/export_memos.py:** Convert all 10 `async def` → `def` (PDF memo generators, never `await`)
- [x] **routes/export_diagnostics.py:** Convert all 6 `async def` → `def` (PDF/Excel/CSV generators, never `await`)
- [x] **routes/export_testing.py:** Convert all 8 `async def` → `def` (CSV generators, never `await`)
- [x] **routes/engagements.py — `export_engagement_package`:** Already `def` — no change needed (Sprint 164)
- [x] Verify: `pytest` passes (2,716 tests — 0 failures)
- [x] Verify: `npm run build` passes

#### Review
> **Status:** COMPLETE
> **Files Modified:** `routes/{export_memos,export_diagnostics,export_testing}.py` (3 files)
> **Notes:** 24 export endpoint conversions total. Same pattern as Sprint 164. `export_engagement_package` was already `def` from Sprint 164.

---

### Sprint 167 — Add BackgroundTasks for email sending + tool run recording
> **Complexity:** 4/10 | **Risk:** Low (deferred work is non-critical metadata)
> **Rationale:** Email sending blocks 100–500ms (sync SendGrid HTTP call). Tool run recording blocks 10–50ms (sync DB INSERT). Neither affects response payload — perfect candidates for `BackgroundTasks`.

- [x] **routes/auth_routes.py — `register`:** Inject `BackgroundTasks`, defer `send_verification_email()` via `background_tasks.add_task()`
- [x] **routes/auth_routes.py — `resend_verification`:** Defer `send_verification_email()` via `background_tasks.add_task()`; returns optimistically
- [x] **routes/contact.py — `submit_contact_form`:** Defer `send_contact_form_email()` via `background_tasks.add_task()`; converted `async def` → `def`
- [x] **shared/testing_route.py:** Defer success-path `maybe_record_tool_run()` via `BackgroundTasks` (covers 6 tools); error-path stays synchronous
- [x] **routes/audit.py:** Defer `maybe_record_tool_run()` in `audit_trial_balance`
- [x] **routes/ar_aging.py:** Defer `maybe_record_tool_run()` calls
- [x] **routes/three_way_match.py:** Defer `maybe_record_tool_run()` calls
- [x] **routes/bank_reconciliation.py:** Defer `maybe_record_tool_run()` calls
- [x] **routes/multi_period.py:** Defer `maybe_record_tool_run()` calls (both 2-way and 3-way endpoints)
- [x] Add error logging in background tasks: `safe_background_email()` wrapper in `shared/helpers.py`
- [x] Verify: `pytest` passes (2,716 tests — 0 failures)

#### Review
> **Status:** COMPLETE
> **Files Modified:** `shared/helpers.py` (+`safe_background_email`), `shared/testing_route.py` (+`BackgroundTasks` param), `routes/{auth_routes,contact,audit,ar_aging,three_way_match,bank_reconciliation,multi_period,ap_testing,payroll_testing,je_testing,revenue_testing,fixed_asset_testing,inventory_testing}.py` (13 route files)
> **Notes:** Success-path work deferred via `background_tasks.add_task()`, error-path stays synchronous for reliability. Email endpoints return optimistically — failures logged via `safe_background_email()` wrapper.

---

### Sprint 168 — `clear_memory()` context manager + error handling cleanup
> **Complexity:** 3/10 | **Risk:** Low
> **Rationale:** `clear_memory()` is called manually in 15+ try/except blocks. If an exception occurs before the call, memory leaks. A context manager guarantees cleanup.

- [x] **shared/helpers.py:** Create `memory_cleanup()` context manager (sync, using `contextlib.contextmanager`)
- [x] **routes/audit.py:** Replace 9 manual `clear_memory()` calls with 3 `with memory_cleanup()` blocks
- [x] **routes/je_testing.py:** Replace 4 manual calls with 2 `with memory_cleanup()` blocks
- [x] **routes/three_way_match.py:** Replace 2 manual calls with 1 `with memory_cleanup()` block
- [x] **routes/ar_aging.py:** Replace 2 manual calls with 1 `with memory_cleanup()` block
- [x] **routes/bank_reconciliation.py:** Replace 2 manual calls with 1 `with memory_cleanup()` block
- [x] **shared/testing_route.py:** Replace 2 manual calls with 1 `with memory_cleanup()` block (covers 6 tools)
- [x] Global exception handler evaluated and rejected (routes have different status codes, operation types, error keys)
- [x] Verify: `pytest` passes (2,716 tests — 0 failures)
- [x] Verify: `npm run build` passes

#### Review
> **Status:** COMPLETE
> **Files Modified:** `shared/helpers.py` (+`memory_cleanup` context manager), `shared/testing_route.py`, `routes/{audit,ar_aging,bank_reconciliation,je_testing,three_way_match}.py` (7 files)
> **Notes:** 21 manual `clear_memory()` calls replaced by 9 `with memory_cleanup()` blocks. Context manager guarantees gc.collect() via `finally` regardless of success/error/early return.

---

### Sprint 169 — Rate limiting gaps + DI consistency
> **Complexity:** 2/10 | **Risk:** Low
> **Rationale:** 8 adjustment routes lack rate limits. JSON parsing boilerplate can be extracted.

- [x] **routes/adjustments.py:** Add `@limiter.limit(RATE_LIMIT_DEFAULT)` to all 8 unprotected endpoints
- [x] **shared/helpers.py:** Create `parse_json_list()` helper
- [x] **routes/audit.py:** Replace `selected_sheets` JSON parsing boilerplate with `parse_json_list()`
- [x] **routes/je_testing.py:** Replace `stratify_by` JSON parsing boilerplate with `parse_json_list()`
- [x] **routes/settings.py:** Migrated `update_client_settings` to `Depends(require_client)`
- [x] **routes/clients.py:** Evaluated — NOT migrating (atomic manager methods are the better pattern)
- [x] Verify: `pytest` passes (2,716 tests — 0 failures)
- [x] Verify: `npm run build` passes

#### Review
> **Status:** COMPLETE
> **Files Modified:** `shared/helpers.py` (+`parse_json_list`), `routes/{adjustments,audit,je_testing,settings}.py` (4 route files)
> **Notes:** Used `RATE_LIMIT_DEFAULT` constant. Added `request: Request` parameter to all 8 adjustment endpoints for slowapi compatibility.

---

### Sprint 170 — Phase XVIII Wrap — Regression + Documentation
> **Complexity:** 2/10 | **Risk:** Low
> **Rationale:** Final verification sprint. Run full test suite, verify no regressions, update documentation.

- [x] Run full `pytest` suite (2,716 tests — 0 failures)
- [x] Run `npm run build` (passes)
- [x] Load-test sanity check: verified async patterns correct across all route files
- [x] Update CLAUDE.md Phase XVIII section
- [x] Version stays at 1.2.0 (internal refactoring, no user-facing changes)
- [x] Archive Phase XVIII checklists to `tasks/archive/phase-xviii-details.md`
- [x] Add lessons learned to `tasks/lessons.md`
- [x] Final commit: `Sprint 170: Phase XVIII Wrap — async architecture remediation`

#### Review
> **Status:** COMPLETE
> **Files Modified:** `CLAUDE.md`, `tasks/todo.md`, `tasks/lessons.md`, `tasks/archive/phase-xviii-details.md`
> **Notes:** 2,716 backend tests + 128 frontend tests all passing. Zero regressions across 7 sprints. Phase XVIII delivered: 82+ endpoint conversions, `asyncio.to_thread()` for CPU-bound work, `BackgroundTasks` for non-critical deferred work, `memory_cleanup()` context manager, rate limit gap closure.
