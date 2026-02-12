# Paciolus Development Roadmap

> **Protocol:** Every directive MUST begin with a Plan Update to this file and end with a Lesson Learned in `lessons.md`.

---

## Completed Phases

### Phase I (Sprints 1-24) — COMPLETE
> Core platform: Zero-Storage TB analysis, streaming, classification, brand, risk dashboard, multi-sheet Excel, PDF/Excel export, JWT auth, activity logging, client management, practice settings, deployment prep.

### Phase II (Sprints 25-40) — COMPLETE
> Test suite, 9 ratios (Current/Quick/D2E/Gross/Net/Operating/ROA/ROE/DSO), IFRS/GAAP docs, trend analysis + viz, industry ratios (6 industries), rolling windows, batch upload, benchmark RFC.

### Phase III (Sprints 41-47) — COMPLETE
> Anomaly detection (suspense, concentration, rounding, balance sheet), benchmark engine + API + UI + integration.

### Phase IV (Sprints 48-55) — COMPLETE
> User profile, security hardening, lead sheets (A-Z), prior period comparison, adjusting entries, DSO ratio, CSV export, frontend test foundation.

### Phase V (Sprints 56-60) — COMPLETE
> UX polish, email verification (backend + frontend), endpoint protection, homepage demo mode. **Tests: 625 backend + 26 frontend.**

### Phase VI (Sprints 61-70) — COMPLETE
> Multi-Period TB Comparison (Tool 2), Journal Entry Testing (Tool 3, 18-test battery + stratified sampling), platform rebrand to suite, diagnostic zone protection. Tests added: 268 JE + multi-period.

### Phase VII (Sprints 71-80) — COMPLETE
> Financial Statement Builder (Tool 1 enhancement), AP Payment Testing (Tool 4, 13-test battery), Bank Reconciliation (Tool 5). Tests added: 165 AP + 55 bank rec.

### Phase VIII (Sprints 81-89) — COMPLETE
> Cash Flow Statement (indirect method, ASC 230/IAS 7), Payroll & Employee Testing (Tool 6, 11-test battery), code quality sprints (81-82). Tests added: 139 payroll.

### Phase IX (Sprints 90-96) — COMPLETE
> Shared testing utilities extraction (enums/memo/round-amounts), Three-Way Match Validator (Tool 7), Classification Validator (TB Enhancement). Tests added: 114 three-way match + 52 classification.

### Phase X (Sprints 96.5-102) — COMPLETE
> The Engagement Layer: engagement model + materiality cascade, follow-up items tracker (narratives-only), workpaper index, anomaly summary report (PDF), diagnostic package export (ZIP with SHA-256), engagement workspace frontend. 8 AccountingExpertAuditor guardrails satisfied. Tests added: 158 engagement/follow-up/workpaper/export.

### Phase XI (Sprints 103-110) — COMPLETE
> Tool-Engagement Integration (frontend auto-link via EngagementProvider), Revenue Testing (Tool 8, 12-test battery, ISA 240), AR Aging Analysis (Tool 9, 11-test battery, dual-input TB + sub-ledger). Tests added: 110 revenue + 28 memo + 131 AR + 34 memo.

### Phase XII (Sprints 111-120) — COMPLETE
> Nav overflow infrastructure, FileDropZone extraction, Finding Comments + Assignments (collaboration), Fixed Asset Testing (Tool 10, 9-test battery, IAS 16), Inventory Testing (Tool 11, 9-test battery, IAS 2). Tests added: 41 comments + 15 assignments + 133 FA + 38 FA memo + 136 inventory + 38 inv memo.

### Phase XIII (Sprints 121-130) — COMPLETE
> Platform polish + dual-theme "The Vault Interior" architecture. Security hardening (26 rate-limited exports, upload validation, error sanitization). CSS custom property + Tailwind semantic token infrastructure. Light theme migration (all tool + authenticated pages). VaultTransition login animation. Export consolidation + Bank Rec/Multi-Period memos (11/11 tools with PDF memos). WCAG AAA accessibility + 60 frontend test backfill. **Version: 1.2.0. Tests: 2,593 backend + 128 frontend.**

### Phase XIV (Sprints 131-135) — COMPLETE
> Professional Threshold: 6 public marketing/legal pages (Privacy, Terms, Contact, About, Approach, Pricing, Trust). Shared MarketingNav/Footer. Contact backend with honeypot + rate limiting. All pages dark-themed (vault exterior).

### Phase XV (Sprints 136-141) — COMPLETE
> Code Deduplication: shared parsing helpers, shared types, 4 shared testing components (DataQualityBadge, ScoreCard, TestResultGrid, FlaggedTable), context consolidation. ~4,750 lines removed (81% deduplication), 100% backward compatible.

### Phase XVI (Sprints 142-150) — COMPLETE
> API Hygiene: semantic token migration, API call consolidation (15 direct fetch → apiClient), N+1 query fix, Docker hardening (.dockerignore, multi-stage fix, SQLite path).

### Phase XVII (Sprints 151-163) — COMPLETE
> Code Smell Refactoring: 7 backend shared modules (column_detector, data_quality, test_aggregator, benford, export_schemas, testing_route, memo_template), 8 frontend decompositions (TB page 1,219→215, export 1,497→32, practice 1,203→665, multi-period 897→470, FinancialStatements 772→333), hook factory, centralized constants. 15 new shared files, 9,298 added / 8,849 removed. **Tests: 2,716 backend + 128 frontend.**

**Test Coverage at Phase XVII End:** 2,716 backend tests + 128 frontend tests | Version 1.2.0

> **Detailed checklists:** `tasks/archive/phases-vi-ix-details.md` | `tasks/archive/phases-x-xii-details.md` | `tasks/archive/phases-xiii-xvii-details.md`

---

## Post-Sprint Checklist

**MANDATORY:** Complete these steps after EVERY sprint before declaring it done.

### Verification
- [ ] Run `npm run build` in frontend directory (must pass)
- [ ] Run `pytest` in backend directory (if tests modified)
- [ ] Verify Zero-Storage compliance for new data handling

### Documentation
- [ ] Update sprint status to COMPLETE in todo.md
- [ ] Add Review section with Files Created/Modified
- [ ] Add lessons to lessons.md if corrections occurred

### Git Commit
- [ ] Stage relevant files: `git add <specific-files>`
- [ ] Commit with sprint reference: `git commit -m "Sprint X: Brief Description"`
- [ ] Verify commit: `git log -1`

---

## Phase XVIII — Async Architecture Remediation (Sprints 164–170)

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

- [ ] **routes/audit.py — `audit_trial_balance`:** Wrap `audit_trial_balance_streaming()` call in `asyncio.to_thread()`
- [ ] **routes/audit.py — `inspect_workbook_endpoint`:** Wrap `inspect_workbook()` call in `asyncio.to_thread()`
- [ ] **routes/audit.py — `flux_analysis`:** Wrap `run_flux_analysis()` in `asyncio.to_thread()`
- [ ] **shared/testing_route.py — `run_single_file_testing()`:** Wrap engine callback + `parse_uploaded_file()` in `asyncio.to_thread()` (covers 6 tools: JE, AP, Payroll, Revenue, Fixed Asset, Inventory)
- [ ] **routes/ar_aging.py:** Wrap `run_ar_aging()` in `asyncio.to_thread()`
- [ ] **routes/three_way_match.py:** Wrap `run_three_way_match()` in `asyncio.to_thread()`
- [ ] **routes/bank_reconciliation.py:** Wrap engine call in `asyncio.to_thread()`
- [ ] **routes/multi_period.py:** Wrap comparison engine calls in `asyncio.to_thread()`
- [ ] **routes/financial_statements.py:** Wrap builder call in `asyncio.to_thread()`
- [ ] Verify: `pytest` passes
- [ ] Verify: `npm run build` passes

#### Review
> **Status:** NOT STARTED
> **Files Modified:**
> **Notes:**

---

### Sprint 166 — Wrap ReportLab/openpyxl export generation in `asyncio.to_thread()`
> **Complexity:** 4/10 | **Risk:** Low (export endpoints are isolated)
> **Rationale:** PDF generation (ReportLab) and Excel generation (openpyxl) are CPU-bound. 12+ export endpoints block the event loop for 2–30s per request.

- [ ] **routes/export_memos.py:** Wrap all 10 memo generators in `asyncio.to_thread()` (`generate_je_testing_memo`, `generate_ap_testing_memo`, `generate_payroll_testing_memo`, `generate_three_way_match_memo`, `generate_revenue_testing_memo`, `generate_ar_aging_memo`, `generate_fixed_asset_testing_memo`, `generate_inventory_testing_memo`, `generate_bank_rec_memo`, `generate_multi_period_memo`)
- [ ] **routes/export_diagnostics.py:** Wrap `generate_audit_report()` (PDF), `generate_workpaper()` (Excel), `generate_leadsheets()` (Excel), `generate_financial_statements_pdf()`, `generate_financial_statements_excel()` in `asyncio.to_thread()`
- [ ] **routes/engagements.py — `export_engagement_package`:** Wrap `exporter.generate_zip()` in `asyncio.to_thread()`
- [ ] Consider: Extract a shared `async_generate(func, *args)` helper to reduce boilerplate
- [ ] Verify: `pytest` passes
- [ ] Verify: All 24 export endpoints return correct content

#### Review
> **Status:** NOT STARTED
> **Files Modified:**
> **Notes:**

---

### Sprint 167 — Add BackgroundTasks for email sending + tool run recording
> **Complexity:** 4/10 | **Risk:** Low (deferred work is non-critical metadata)
> **Rationale:** Email sending blocks 100–500ms (sync SendGrid HTTP call). Tool run recording blocks 10–50ms (sync DB INSERT). Neither affects response payload — perfect candidates for `BackgroundTasks`.

- [ ] **routes/auth_routes.py — `register`:** Inject `BackgroundTasks`, defer `send_verification_email()` via `background_tasks.add_task()`
- [ ] **routes/auth_routes.py — `resend_verification`:** Defer `send_verification_email()` via `background_tasks.add_task()`
- [ ] **routes/contact.py — `submit_contact_form`:** Defer `send_contact_form_email()` via `background_tasks.add_task()`
- [ ] **shared/testing_route.py:** Defer `maybe_record_tool_run()` via `BackgroundTasks` (covers 6 tools)
- [ ] **routes/audit.py:** Defer `maybe_record_tool_run()` calls in `audit_trial_balance` and `flux_analysis`
- [ ] **routes/ar_aging.py:** Defer `maybe_record_tool_run()` calls
- [ ] **routes/three_way_match.py:** Defer `maybe_record_tool_run()` calls
- [ ] **routes/bank_reconciliation.py:** Defer `maybe_record_tool_run()` calls
- [ ] **routes/multi_period.py:** Defer `maybe_record_tool_run()` calls
- [ ] Add error logging in background tasks (email failures, tool run failures) so silent failures are observable
- [ ] Verify: `pytest` passes
- [ ] Verify: Email still arrives in dev/staging

#### Review
> **Status:** NOT STARTED
> **Files Modified:**
> **Notes:**

---

### Sprint 168 — `clear_memory()` context manager + error handling cleanup
> **Complexity:** 3/10 | **Risk:** Low
> **Rationale:** `clear_memory()` is called manually in 15+ try/except blocks. If an exception occurs before the call, memory leaks. A context manager guarantees cleanup. Also centralizes the repeated `sanitize_error()` pattern.

- [ ] **shared/helpers.py:** Create `memory_cleanup()` context manager (sync, using `contextlib.contextmanager`)
- [ ] **routes/audit.py:** Replace 5 manual `clear_memory()` calls with context manager
- [ ] **routes/je_testing.py:** Replace 3 manual calls
- [ ] **routes/three_way_match.py:** Replace 2 manual calls
- [ ] **routes/ar_aging.py:** Replace 2 manual calls
- [ ] **routes/bank_reconciliation.py:** Replace manual calls
- [ ] **routes/multi_period.py:** Replace manual calls
- [ ] **routes/financial_statements.py:** Replace manual calls
- [ ] **All remaining routes with `clear_memory()`:** Migrate to context manager
- [ ] Consider: Global exception handler in `main.py` for `sanitize_error()` pattern (evaluate if it reduces boilerplate meaningfully without hiding route-specific error context)
- [ ] Verify: `pytest` passes

#### Review
> **Status:** NOT STARTED
> **Files Modified:**
> **Notes:**

---

### Sprint 169 — Rate limiting gaps + DI consistency
> **Complexity:** 2/10 | **Risk:** Low
> **Rationale:** 8 adjustment routes lack rate limits. `require_client()` dependency exists but isn't used in all client-path-param routes. JSON parsing boilerplate can be extracted.

- [ ] **routes/adjustments.py:** Add `@limiter.limit("60/minute")` to all 8 unprotected endpoints (`GET /audit/adjustments`, `GET .../reference/next`, `GET .../types`, `GET .../statuses`, `GET .../{entry_id}`, `PUT .../{entry_id}/status`, `DELETE .../{entry_id}`, `DELETE /audit/adjustments`)
- [ ] **shared/helpers.py:** Create `parse_json_list(raw: str, label: str) -> list` helper
- [ ] **routes/audit.py:** Replace JSON parsing boilerplate with `parse_json_list()`
- [ ] **routes/je_testing.py:** Replace JSON parsing boilerplate with `parse_json_list()`
- [ ] **routes/settings.py:** Evaluate migrating to `Depends(require_client)` for client validation
- [ ] **routes/clients.py:** Evaluate migrating `update_client`/`delete_client` to `Depends(require_client)`
- [ ] Verify: `pytest` passes

#### Review
> **Status:** NOT STARTED
> **Files Modified:**
> **Notes:**

---

### Sprint 170 — Phase XVIII Wrap — Regression + Documentation
> **Complexity:** 2/10 | **Risk:** Low
> **Rationale:** Final verification sprint. Run full test suite, verify no regressions, update documentation.

- [ ] Run full `pytest` suite (2,716+ tests must pass)
- [ ] Run `npm run build` (must pass)
- [ ] Load-test sanity check: verify concurrent requests don't block (manual or scripted)
- [ ] Update CLAUDE.md Phase XVIII section
- [ ] Update version if warranted
- [ ] Archive Phase XVIII checklists to `tasks/archive/`
- [ ] Add lessons learned to `tasks/lessons.md`
- [ ] Final commit: `Sprint 170: Phase XVIII Wrap — async architecture remediation`

#### Review
> **Status:** NOT STARTED
> **Files Modified:**
> **Notes:**

---

## Not Currently Pursuing

> **Reviewed:** Agent Council + Future State Consultant (2026-02-09)
> **Criteria:** Deprioritized due to low leverage, niche markets, regulatory burden, or off-brand positioning.

| Feature | Status | Reason |
|---------|--------|--------|
| Loan Amortization Generator | Not pursuing | Commodity calculator; off-brand |
| Depreciation Calculator | Not pursuing | MACRS table maintenance; better served by Excel |
| 1099 Preparation Helper | Not pursuing | US-only, seasonal, annual IRS rule changes |
| Book-to-Tax Adjustment Calculator | Not pursuing | Tax preparer persona; regulatory complexity |
| W-2/W-3 Reconciliation Tool | Not pursuing | Payroll niche; seasonal; different persona |
| Segregation of Duties Checker | Not pursuing | IT audit persona; different user base |
| Expense Allocation Testing | DROPPED | 2/5 market demand; niche applicability |
| Cross-Tool Composite Risk Scoring | REJECTED | ISA 315 violation — requires auditor risk inputs |
| Management Letter Generator | REJECTED | ISA 265 violation — deficiency classification is auditor judgment |
| Heat Map / Risk Visualization | REJECTED | Depends on composite scoring (rejected) |

### Deferred to Phase XIX+

| Feature | Reason | Earliest Phase |
|---------|--------|----------------|
| Budget Variance Deep-Dive | Multi-Period page tab refactor prerequisite | Phase XIX |
| Accrual Reasonableness Testing (Tool 12) | Dual-input fuzzy matching complexity | Phase XIX |
| Intercompany Transaction Testing (Tool 13) | Cycle-finding algorithm; narrow applicability | Phase XIX |
| Multi-Currency Conversion | Cross-cutting 11+ engine changes; needs dedicated RFC | Phase XIX |
| Engagement Templates | Premature until engagement workflow has real user feedback | Phase XIX |
| Lease Accounting (ASC 842) | 8/10 complexity; high value but needs research sprint | Phase XIX |
| Cash Flow Projector | Requires AR/AP aging + payment history | Phase XIX |
| Cash Flow — Direct Method | Requires AP/payroll detail integration | Phase XIX |
| Related Party Transaction Screening | Needs external data APIs; 8/10 complexity | Phase XIX+ |
| Finding Attachments | File storage contradicts Zero-Storage philosophy | Phase XIX+ |
| Real-Time Collaboration | WebSocket infrastructure; 9/10 complexity | Phase XIX+ |
| Custom Report Builder | Rich text editor + templating engine | Phase XIX+ |
| Historical Engagement Comparison | Requires persistent aggregated data | Phase XIX+ |
| User-toggleable dark/light mode | CEO vision is route-based, not preference | Phase XIX (if demand) |
| Homepage redesign | Homepage stays dark; separate initiative | Phase XIX |
| Mobile hamburger menu for ToolNav | Current overflow dropdown sufficient | Phase XIX |
| Print stylesheet | Out of scope for completed phases | Phase XIX |
| Component library / Storybook | Lower priority than shipping features | Phase XIX |
| Onboarding flow | UX research needed | Phase XIX |
| Batch export all memos | ZIP already bundles anomaly summary | Phase XIX |
| Async SQLAlchemy migration | Full AsyncSession + aiosqlite migration if threadpool proves insufficient | Phase XIX |
| Async email client | Replace sync SendGrid SDK with httpx async or aiosmtplib | Phase XIX |
