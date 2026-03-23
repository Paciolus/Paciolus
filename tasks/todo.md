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
| ~~Password reset flow (NEW-015)~~ | RESOLVED — Sprint 572 | Sprint 569 |

---

## Active Phase
> Sprints 478–531 archived to `tasks/archive/sprints-478-531-details.md` (consolidated).
> Sprints 532–561 archived to `tasks/archive/sprints-532-561-details.md` (consolidated).
> FIX-1A/1B, Sprint 562, FIX-2A/2B archived to `tasks/archive/fix-1-2-sprint562-details.md`.
> FIX-3–8B, AUDIT-09–10 archived to `tasks/archive/fix-3-8b-audit-09-10-details.md`.
> Sprints 563–569, CI-FIX archived to `tasks/archive/sprints-563-569-details.md`.
> Sprints 570–571 archived to `tasks/archive/sprints-570-571-details.md`.

### Sprint 572: Password Reset Flow
> Source: Launch Readiness Review item B-15 / Deferred NEW-015

#### Backend
- [x] `PasswordResetToken` model (SHA-256 hashed, 1-hour expiry, single-use)
- [x] `POST /auth/forgot-password` — rate-limited, always returns 200 (prevents enumeration)
- [x] `POST /auth/reset-password` — validates token, sets new password, revokes all sessions, clears lockout
- [x] Password reset email template (HTML + plaintext, Oat & Obsidian branding)
- [x] `generate_password_reset_token()` + `send_password_reset_email()` in email_service.py
- [x] CSRF exemption for both endpoints (pre-auth, no CSRF token available)

#### Frontend
- [x] `/forgot-password` page — email form, success screen (always shown to prevent enumeration)
- [x] `/reset-password` page — new password form with complexity validation, token capture + URL stripping
- [x] Login page "Forgot password?" link → `/forgot-password`

#### Tests
- [x] 12 backend tests: forgot-password (4), reset-password (5), CSRF exemption (2), lockout reset (1)
- [x] 10 frontend tests: ForgotPasswordPage (5), ResetPasswordPage (5)
- [x] Updated CSRF exemption snapshot test with 2 new paths

- **Tests:** 7,108 backend (12 new), 1,735 frontend (10 new) — 0 failures
- **Verification:** npm run build PASS, npm test PASS (1,735/1,735), backend tests PASS (106/106 auth+csrf+reset)
- **Status:** COMPLETE

### Sprint 573: Decimal Pipeline Refactor (AUDIT-06-F001, AUDIT-06-F003)
> Source: AUDIT-06 Findings F001 (float arithmetic in ingestion) and F003 (cross-engine float down-casts)

#### streaming_auditor.py
- [x] `_debit_chunks` / `_credit_chunks` → `list[Decimal]`
- [x] `account_balances` dict values → `Decimal` (was float)
- [x] `process_chunk()`: `Decimal(str(math.fsum(...)))` replaces `math.fsum()` float
- [x] Per-account accumulation: `Decimal(str(debit_sum))` replaces `float(Decimal(str(...)))`
- [x] `_finalize_balances()`: ensures Decimal (no longer converts to float)
- [x] `get_balance_result()`: `sum(Decimal)` replaces `math.fsum(float)`

#### pipeline.py
- [x] `_total_debits` / `_coverage_pct` / scoring inputs → Decimal arithmetic
- [x] Multi-sheet path: consolidated debits/credits/balances → Decimal
- [x] Coverage percentage: `Decimal.quantize()` replaces `round(float)`

#### ratio_engine.py
- [x] `CategoryTotals` fields → `Decimal` with `__post_init__` coercion
- [x] `from_dict()`: `_to_decimal()` replaces `_to_float()`
- [x] `extract_category_totals()`: `Decimal(str(...))` for balance values
- [x] `RatioResult.__post_init__`: coerce Decimal→float (ratios are dimensionless)
- [x] `VarianceResult.__post_init__`: coerce Decimal→float (display-only)
- [x] `_calculate_momentum()`: `float(variance)**0.5` fix
- [x] `_determine_trend_direction()`: `/ 100` replaces `* 0.01`

#### flux_engine.py
- [x] `NEAR_ZERO` → `Decimal("0.005")`
- [x] Balance extraction: `Decimal(str(...))` replaces `float(...)`
- [x] Percentage deltas remain float (display-only)
- [x] `FluxItem` construction: `float()` at boundary (dataclass stores float)

#### population_profile_engine.py
- [x] `compute_population_profile_from_rows()`: Decimal accumulation, no `float()` wrapper
- [x] Type annotations updated to `dict[str, dict[str, Any]]`

#### going_concern_engine.py
- [x] `/ 2` replaces `* 0.5` (Decimal-safe)

#### parsing_helpers.py
- [x] `safe_float()`: deprecation docstring for monetary use

- **Tests:** 7,107 backend — 0 failures (7,064 + 43 QA)
- **Verification:** Full backend test suite PASS
- **Status:** COMPLETE

### Sprint 574: Response Schema Reconciliation + Decimal Serialization (AUDIT-06-F002, AUDIT-11-F001, AUDIT-11-F005)
> Source: AUDIT-06 F002 (float serialization), AUDIT-11 F001 (undeclared fields), AUDIT-11 F005 (cast workarounds)

#### Backend (diagnostic_response_schemas.py)
- [x] `MonetaryDecimal` annotated type: Decimal field → float JSON serialization
- [x] `RiskSummaryResponse`: add risk_score, risk_tier, risk_factors, coverage_pct
- [x] `TrialBalanceResponse`: add informational_count, data_quality, all_accounts, account_balances, classified_accounts, account_subtypes, lease_diagnostic, cutoff_risk, going_concern
- [x] Monetary fields → `MonetaryDecimal`: TrialBalance, AbnormalBalance, FluxItem, BalanceSheetValidation, SheetResult
- [x] `category_totals` field type: `dict[str, float]` → `dict[str, str]` (matches actual output)

#### Frontend
- [x] `RiskSummary` (mapping.ts): add risk_score, risk_tier, risk_factors, coverage_pct
- [x] `AuditResult` (diagnostic.ts): add data_quality, all_accounts, account_balances, classified_accounts, account_subtypes, lease/cutoff/going_concern, balance_sheet_validation, category_totals; informational_count → required
- [x] `page.tsx`: replace `AuditResultCast` with canonical `AuditResult` import
- [x] `useMultiPeriodComparison.ts`: `AuditResultForComparison` → type alias to `AuditResult`

- **Tests:** 7,064 backend, 1,735 frontend — 0 failures
- **Verification:** npm run build PASS, npm test PASS, pytest PASS
- **Status:** COMPLETE

### Sprint 575: Account Identifier Preservation (AUDIT-06-F004)
> Source: AUDIT-06 F004 (leading-zero account codes corrupted by pandas dtype inference)

#### security_utils.py
- [x] `process_tb_in_memory()`: pass `dtype=str` to CSV and Excel readers
- [x] `process_tb_chunked()`: pass `dtype=str` to chunked CSV and Excel readers
- [x] Type hints updated: `read_csv_secure`, `read_excel_secure`, `read_csv_chunked`, `read_excel_chunked`, `read_excel_multi_sheet_chunked` accept `type` (e.g. `str`) in dtype parameter

#### Downstream compatibility
- [x] `StreamingAuditor.process_chunk()` already uses `pd.to_numeric(errors='coerce')` for debit/credit — no changes needed
- [x] All columns ingested as `str`; numeric conversion deferred to downstream consumers

#### Tests (test_account_identifier.py — 9 new tests)
- [x] CSV leading-zero preservation: `process_tb_in_memory`, `process_tb_chunked`, `read_csv_secure`
- [x] CSV mixed formats (alphanumeric + numeric): in-memory and chunked paths
- [x] Excel leading-zero preservation: in-memory and chunked paths
- [x] End-to-end StreamingAuditor: leading-zero and mixed-format account keys

- **Tests:** 7,073 backend (9 new) — 0 failures
- **Verification:** pytest PASS (7,073/7,073)
- **Status:** COMPLETE

### Sprint 577: Unified Error Schema & Frontend Error Handling (AUDIT-11-F004)
> Source: AUDIT-11 F004 (inconsistent error shapes, duplicated frontend error parsing)

#### Backend (main.py, shared/schemas.py)
- [x] `ErrorResponse` Pydantic model: code, message, request_id, detail
- [x] 500 handler → `ErrorResponse` envelope (code="INTERNAL_ERROR")
- [x] HTTPException handler → `ErrorResponse` envelope + backward-compat `detail` key
- [x] 422 handler → `ErrorResponse` envelope + legacy `error_code` alias

#### Frontend (transport.ts, uploadTransport.ts)
- [x] `ParsedApiError` interface + `parseErrorResponse()` shared parser in transport.ts
- [x] `performFetch` error path uses `parseErrorResponse()`
- [x] `uploadFetch` imports and uses `parseErrorResponse()` from transport.ts

- **Tests:** 7,073 backend, 1,735 frontend — 0 failures
- **Verification:** npm run build PASS, npx jest PASS (1,735/1,735), pytest PASS (7,073/7,073)
- **Status:** COMPLETE

### Sprint 576: Organization & Untyped Endpoint Response Models (AUDIT-11-F002, AUDIT-11-F003)
> Source: AUDIT-11 F002 (organization endpoints return raw dicts), F003 (admin/branding/bulk/export routes lack response_model)

#### Backend (shared/organization_schemas.py — new file)
- [x] `OrganizationResponse`, `OrganizationWithMemberCountResponse` — org CRUD
- [x] `OrganizationMemberResponse` — list-members, update-role (with enriched user_name/user_email)
- [x] `OrganizationInviteResponse`, `OrganizationInviteCreateResponse` — invite CRUD
- [x] `AdminOverviewResponse`, `TeamActivityEntryResponse`, `UsageByMemberResponse` — admin dashboard
- [x] `BrandingResponse` — branding GET/PUT/POST-logo
- [x] `BulkUploadStartResponse`, `BulkUploadStatusResponse` — bulk upload
- [x] `ExportShareResponse`, `ExportShareCreateResponse` — export sharing
- [x] `DetailResponse` — generic detail message (revoke invite, accept invite, remove member, delete logo, revoke share)

#### Route Decorators Updated
- [x] `organization.py` — 10 routes: response_model added
- [x] `admin_dashboard.py` — 3 JSON routes: response_model added (CSV export skipped — StreamingResponse)
- [x] `branding.py` — 4 routes: response_model added
- [x] `bulk_upload.py` — 2 routes: response_model added
- [x] `export_sharing.py` — 3 JSON routes: response_model added (download skipped — Response)

- **Status:** COMPLETE

### Sprint 578: Synthetic Anomaly Framework Expansion (AUDIT-06-F005)
> Source: AUDIT-06 F005 (anomaly framework covers only 6 families, missing claimed-but-untested types)

#### New Generators (4 new)
- [x] `related_party_activity` — intercompany/affiliate accounts with offsetting balances
- [x] `revenue_concentration` — 90% revenue in single account
- [x] `expense_concentration` — 89% expenses in single account
- [x] `balance_sheet_imbalance` — $10K unbalanced debit entry

#### Registry & Coverage Map
- [x] `registry.py`: 4 new generators registered with metadata
- [x] `COVERAGE_MAP.md`: 4 new rows (all COVERED), Blind Spots section with 7 documented future categories

- **Tests:** 7,077 backend (4 new detection tests via parametrized runner) — 0 failures
- **Verification:** Full backend test suite PASS
- **Status:** COMPLETE

