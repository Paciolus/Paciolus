# Architectural Remediation Initiative — COMPLETE 2026-04-29

> **Source:** 8-phase remediation strategy (transcript 2026-04-29) translated into Paciolus sprint format. **All 18 sprints (742-759) shipped.** Initiative scorecard at `reports/architectural-remediation-scorecard-2026-04-29.md`.
>
> **Outcome (TL;DR):** Phases 0/1/4/6/7/8 fully resolved; Phases 2/3/5 partial with explicit follow-up scope filed in `## Refactor Intake` (in `tasks/todo.md`). 6 ADRs (014-018 + quality thresholds), 3 advisory CI lint scans, ~150 new pytest + ~50 new jest tests. Net code shrinkage: `auth_routes.py` 778 → ~270; `routes/export_diagnostics.py` 661 → 358; multi-period page 501 → 423; dashboard page 519 → 383; `useFormValidation.ts` 516 → 280.
>
> **Governance going forward:** quarterly architecture health review (run the 3 advisory lints, check deferred-items triggers, file ≤2 follow-up sprints if warranted); "no new god files" policy (code-review enforced); refactor intake lane visible in `## Refactor Intake` of `tasks/todo.md`. Subsequent sprints should be product-driven, not architecture-driven.
>
> **Sprint 741 was reserved** for cleanup-scheduler root-cause work (Sprint 740 follow-up). Initiative ran 742-759.

### Sprint 742: ADRs + quality thresholds (Phase 0 — Baseline & Guardrails 1/2)
**Status:** COMPLETE 2026-04-29. Documents patterns Sprint 744–746a already established (ADR-014, 015) + sets target for Sprint 748–749 (ADR-016).
**Priority:** P3.
**Source:** Architectural Remediation Plan phase 0.

**What landed:**
- `docs/03-engineering/adr-014-canonical-frontend-network-layer.md` — Accepted (Sprint 744). Direct `fetch()` banned outside the 6-file allowlist; ESLint rule enforces. Documents the canonical entrypoints (`apiGet`/`apiPost`/`apiDownload`/`uploadFetch`) and the rationale for each allowlist entry.
- `docs/03-engineering/adr-015-backend-route-service-boundaries.md` — Accepted (Sprint 745 + 746a). Three patterns: `db_transaction` for DB writes, `raise_http_error` for non-DB error paths, `services/<domain>/<workflow>.py` for multi-step business logic. Honors the cookie/CSRF boundary deferral.
- `docs/03-engineering/adr-016-export-architecture.md` — Proposed (target for Sprint 748+749). Mapper / generator separation. Routes become slim controllers. `export_memos.py` dynamic-vs-explicit ambiguity must be resolved (pick one strategy).
- `docs/03-engineering/quality-thresholds.md` — Module size targets (route 500/800, service 300/500, page 400/700, hook 200/400), function complexity (cyclomatic 8/12), hook surface (4/8 useState declarations), advisory until Sprint 756 wires CI.
- `CONTRIBUTING.md` — new "Architectural Patterns" section linking to all 4 docs.

**Out of scope:**
- Numbering — only ADR-013 existed previously, so the new 014/015/016 sit naturally next to it. No retroactive numbering of pre-existing implicit decisions.
- CI enforcement — quality thresholds remain advisory until Sprint 756.

**Exit met:** ADRs merged; threshold defaults documented; Sprints 743–759 can reference these as authority.

---

### Sprint 743: Characterization test gap analysis (Phase 0 — Baseline & Guardrails 2/2)
**Status:** COMPLETE 2026-04-29. One filed gap-fill (DashboardPage smoke test); all other surfaces sufficiently covered.
**Priority:** P3.
**Source:** Architectural Remediation Plan phase 0.

**What landed:**
- `reports/test-coverage-gap-analysis-2026-04-29.md` — full gap report. Inventoried 199 frontend test files + relevant backend modules against surfaces named in Sprints 747–752.
- `frontend/src/__tests__/DashboardPage.test.tsx` — smoke test for `app/dashboard/page.tsx` (519 lines, target of Sprint 751 decomposition). Pins: three GET requests on mount, welcome header + Quick Launch render, unauthenticated → `/login` redirect, stats-failure toast handling. 4/4 tests pass.

**Coverage findings:**
- **Auth (Sprints 746b/c/d, 747):** 214 backend tests across 13 routes + frontend `AuthContext.test.tsx`, `useAuthSession.test.ts`, `LoginPage.test.tsx`, `ForgotPasswordPage.test.tsx`. Strong regression net.
- **Exports (Sprints 748, 749):** 173 backend tests + per-page interaction tests. Sprint 749's contract tests are not pre-existing gaps (Sprint 749 produces them).
- **Dashboard + tool pages (Sprints 750, 751):** 18 tool-page tests cover Sprint 750's surface; **dashboard frontend was the one genuine gap** — backed up by 30 backend dashboard/activity tests but no targeted `app/dashboard/page.tsx` test until this sprint.
- **API error envelope:** Sprint 745's `test_route_errors.py` + `test_db_unit_of_work.py` (14 tests) + `test_log_sanitizer.py`. Covered.
- **Hooks for Sprint 752:** all named candidates (`useStatisticalSampling`, `useAccountRiskHeatmap`, `useUncorrectedMisstatements`, `useAnalyticalExpectations`) have direct tests.

**Non-gaps (rejected as pre-existing):**
- Memo PDF schema contract tests (Sprint 749 produces them).
- Export endpoint contract tests (same).
- API error envelope snapshot test (existing route tests exercise the envelope).
- `useFetchData` decomposition coverage (Sprint 752 hasn't picked the candidate yet).

**Methodology note:** the Sprint 744 test churn (4 test files pinning pre-Sprint-661 Bearer-header behavior) was a separate class of issue — outdated assertions, not missing coverage. That class self-corrects when migrations run (assertions fail loudly, get fixed). Sprint 743 does not address it.

**Exit met:** Gap report filed; one gap-fill landed; pre-refactor regression net acknowledged sufficient.

---

### Sprint 744: Frontend canonical `apiClient` enforcement (Phase 1 — Cross-Cutting 1/2)
**Status:** COMPLETE 2026-04-29. Phase 0 ADR skipped per CEO directive — proceeded directly to enforcement.
**Priority:** P3.
**Source:** Architectural Remediation Plan phase 1.

**What landed:**
- Migrated 4 direct-`fetch` outliers to canonical layers:
  - `hooks/useAccountRiskHeatmap.ts` `downloadCsv` → `apiDownload` + `downloadBlob` (was 27 lines of manual blob-anchor handling).
  - `app/tools/depreciation/page.tsx` `onDownloadCsv` → `apiDownload` + `downloadBlob`.
  - `app/tools/loan-amortization/page.tsx` `downloadExport` → `apiDownload` + `downloadBlob`.
  - `hooks/useStatisticalSampling.ts` `executeSamplingUpload` → `uploadFetch` from `uploadTransport`.
- Renamed shadowed local `fetch` in `hooks/useRollingWindow.ts` → `fetchRollingData` (was destructured from `useFetchData`, tripping the new lint rule).
- ESLint rule (`no-restricted-syntax` `CallExpression[callee.name="fetch"]`) banning direct `fetch()` outside the allowlist. Per-file override block exempts the canonical transport/auth modules.
- Allowlist (escaped `[token]` for minimatch): `utils/transport.ts`, `utils/authMiddleware.ts`, `utils/downloadAdapter.ts`, `utils/uploadTransport.ts`, `contexts/AuthSessionContext.tsx`, `app/shared/[token]/page.tsx` (public passcode-flow share page — intentionally low-level for 429 Retry-After parsing).
- Updated 4 affected test files to mock at the `apiDownload`/`downloadBlob` boundary instead of `global.fetch` (the old assertions checked `Authorization: Bearer` headers, but the canonical pattern uses HttpOnly cookie auth via `credentials: 'include'` — tests were pinning obsolete behavior).

**Verification:**
- `npx eslint src/**/*.{ts,tsx}` → exit 0 (clean).
- `npx tsc --noEmit` → exit 0.
- 4 affected jest suites: 26/26 passing (`useAccountRiskHeatmap`, `useStatisticalSampling`, `DepreciationPage`, `AccountRiskHeatmapPage`); `LoanAmortizationPage`: 8/8.

**Out of scope (deferred):**
- Unify user-facing error normalization through one path — partially achieved (the canonical `apiDownload`/`uploadFetch`/`apiPost` already return structured `{ ok, error }`), but consumer-side error UX is still per-page. Full unification is bundled into Sprint 752 (render-perf + decomposition pass).
- ADR document (Phase 0 deliverable) — skipped. The lint rule + allowlist comments serve as the canonical record.

**Exit met:** Single fetch pattern; CI enforces it via ESLint rule.

---

### Sprint 745: Backend transaction + route-error standardization (Phase 1 — Cross-Cutting 2/2)
**Status:** COMPLETE 2026-04-29.
**Priority:** P3.
**Source:** Architectural Remediation Plan phase 1.

**What landed:**
- `backend/shared/db_unit_of_work.py` — `db_transaction(db, *, log_label, log_message=None)` context manager. Replaces the `try: db.commit(); except SQLAlchemyError as e: db.rollback(); logger.exception(...); raise HTTPException(500, detail=sanitize_error(e, log_label=...))` triad copy-pasted across ~12 route modules.
- `backend/shared/route_errors.py` — `raise_http_error(status_code, *, label, user_message, exception, operation, allow_passthrough)` helper. Centralizes 4xx + non-DB 5xx error responses with sanitized detail + structured-log metadata. Complements `db_transaction` (DB) with the non-DB error path.
- Pilot migration on `routes/activity.py` — 4 sites (`db_activity_create`, `db_activity_clear`, `db_tool_activity`, `db_prefs_update`) converted to `with db_transaction(...)`. Removed unused `SQLAlchemyError` + `sanitize_error` imports. Net `-30` lines on activity.py.

**Verification:**
- `tests/test_db_unit_of_work.py` — 7 tests covering: clean commit, SQLAlchemyError rollback+500, non-SQLAlchemy propagation (no rollback), IntegrityError handling, sanitization (no SQL/PII leak), log message override, default log message.
- `tests/test_route_errors.py` — 7 tests covering: user_message wins, default fallback, exception-only path uses `sanitize_error`, passthrough returns safe original message, passthrough blocks internal-detail leakage, status code propagation across 9 codes.
- `tests/test_activity_api.py` (13) + `tests/qa/test_activity_recent.py` (5) — all 18 pre-existing route tests still pass post-migration. 32/32 total.

**Out of scope (deferred to Sprint 755 or later):**
- Migrating the remaining ~11 route modules (`auth_routes.py`, `billing.py`, `diagnostics.py`, etc.) to `db_transaction`. Sprint 745 ships the pattern + pilot; broad adoption is incremental and naturally folds into Sprints 746–747 (auth) and follow-up cleanup work.
- The deferred `routes/billing.py::stripe_webhook` decomposition can now use both helpers — re-evaluate that deferred item once the auth refactor (Sprint 746) lands.

**Exit met:** One transaction pattern + one route-error pattern; pilot on `activity.py` demonstrates parity (18/18 pre-existing tests pass); pattern documented for incremental adoption via module docstrings.

---

### Sprint 746: Auth service-layer extraction (Phase 2 — Auth Decomposition 1/2)
**Status:** **COMPLETE** 2026-04-29 — All four sub-sprints (746a recovery, 746b identity, 746c registration, 746d sessions) shipped this session.
**Priority:** **P2** — security-sensitive surface; highest-risk refactor in plan.
**Source:** Architectural Remediation Plan phase 2.

Extract service layer from `auth_routes.py` into focused subdomains:
- ✅ **Sprint 746a — `services/auth/recovery.py`** (password reset lifecycle). Shipped 2026-04-29. `forgot_password` and `reset_password` routes are now ~10 lines each (validate → call service → return response). Service exposes `initiate_password_reset(db, email) → PasswordResetInitiation` and `complete_password_reset(db, token, new_password) → User` (raises `PasswordResetError` for invalid/used/expired/inactive — route maps to `HTTPException(400)`). Both 41 pre-existing password tests pass.
- ✅ **Sprint 746b — `services/auth/identity.py`** (login/logout/refresh + token issuance/rotation). Shipped 2026-04-29. `IdentityIssuance` dataclass + `authenticate_login`, `refresh_session`, `revoke_session_token`. login route shrunk 60 → 22 lines; refresh ~30 → ~22 lines. `/auth/me` already thin (no extraction needed). Cookie writes stay in route. 10 unused imports removed from `auth_routes.py`. 219 auth tests pass (172 + 47 verification).
- ✅ **Sprint 746c — `services/auth/registration.py`** (registration + verification lifecycle). Shipped 2026-04-29. `register_user`, `complete_email_verification`, `resend_verification_email` + 4 domain exception classes (`RegistrationError`, `EmailVerificationError`, `EmailAlreadyVerifiedError`, `VerificationCooldownError`). register route shrunk 86 → 33 lines; verify-email 40 → 9 lines; resend-verification 53 → 27 lines. 11 unused imports removed (`EmailVerificationToken`, `is_disposable_email`, `generate_verification_token`, `ENV_MODE`, `hash_token`, `create_user`, `create_access_token`, `create_refresh_token`, `sanitize_error`, `SQLAlchemyError`, `get_user_by_email`). Two test patches updated to point at `services.auth.registration` instead of `routes.auth_routes`. 189/189 auth tests pass.
- ✅ **Sprint 746d — `services/auth/sessions.py`** (session inventory + revocation). Shipped 2026-04-29. `list_user_sessions` (returns `SessionEntry` list), `revoke_session_by_id` (raises `SessionNotFoundError` for unknown / cross-user / already-revoked), `revoke_all_user_sessions`. list_sessions route 32 → 16 lines; revoke_session 22 → 12 lines; revoke_all_sessions 12 → 7 lines. Removed 4 unused imports (`datetime`, `UTC`, `_revoke_all_user_tokens`, `RefreshToken`). 233/233 auth + helper tests pass.

**Honors deferred-items boundary:** Sprint 746a moves only business logic. Cookie/CSRF primitives (`_set_refresh_cookie`, `_set_access_cookie`, etc.) remain in the route layer per the deferred-items guidance. Token issuance + cookie writes will need careful handling in Sprint 746b.

**What landed in 746a:**
- `backend/services/auth/__init__.py` — package marker + roadmap docstring.
- `backend/services/auth/recovery.py` — 156 lines. `PasswordResetError` (subclass of `ValueError`), `PasswordResetInitiation` dataclass, `initiate_password_reset`, `complete_password_reset`. Uses `db_transaction` from Sprint 745 for the commit/rollback path. Preserves Sprint 594/595 diagnostic (total-user-count log on unknown-email lookup).
- `backend/routes/auth_routes.py` — `forgot_password` shrunk from 60 → 19 lines; `reset_password` from 50 → 14 lines. Removed unused imports (`generate_password_reset_token`).
- 41/41 pre-existing password tests still pass.

**Exit (partial):** One auth subdomain (recovery) extracted as proof-of-pattern. Identity / registration / sessions remaining.

---

### Sprint 747: Auth route thinning + security response normalization (Phase 2 — Auth Decomposition 2/2)
**Status:** **COMPLETE** 2026-04-29. Sprint 747a (enumeration-safe helper) + Sprints 746b/c/d (which fully thinned login/refresh/logout/register/verify-email/resend/sessions handlers as a side effect of service extraction) collectively delivered the sprint's scope.
**Priority:** P2.
**Source:** Architectural Remediation Plan phase 2.

**What landed in 747a:**
- `backend/services/auth/security_responses.py` — `raise_invalid_credentials()` helper. Single source of truth for the AUDIT-07 F4 enumeration-safe 401 response (same body + `WWW-Authenticate: Bearer` header for wrong-password / unknown-email / locked-account / IP-blocked).
- `routes/auth_routes.py::login` — three duplicated `HTTPException(401, ...)` raises (lines 276/289/301) collapsed to `raise_invalid_credentials()` calls. Behavior preserved verbatim.
- `backend/tests/test_auth_security_responses.py` — 3 tests pinning the stable body, header, and inter-call-shape consistency. Plus 36 pre-existing auth route + parity tests still pass (39/39).

**Final state (after 746b/c/d):**
- All 13 auth route handlers are now orchestration-only (~10–25 lines each). Cookie writes + HTTP plumbing in routes; business logic + DB persistence in services.
- AUDIT-07 F4 enumeration-safe 401 response is a single helper (`raise_invalid_credentials`) called from inside the identity service.
- 4 service modules in `backend/services/auth/`: `recovery`, `identity`, `registration`, `sessions` (+ `security_responses` shared helper).
- 233/233 auth + helper tests pass after the full Phase 2 sweep.

**Out of scope (deferred to a future cleanup sprint, low priority):**
- `check_ip_blocked` + `check_lockout_status` consolidation into a single `pre_auth_check_or_raise()` helper. Sequential calls in `authenticate_login` are clear in context; consolidation would be cosmetic, and the two calls have distinct logging + recording semantics (only the lockout-failure branch calls `record_ip_failure`). Revisit only if a fifth pre-auth check joins them.

**Exit met:** All auth handlers are thin orchestration layers; security-critical behaviors covered by focused service-level tests; no monolithic-route assumptions remain.

---

### Sprint 748: Export mapper layer + diagnostics refactor (Phase 3 — Export Rationalization 1/2)
**Status:** **COMPLETE** 2026-04-29 (748a + 748b). 6 CSV routes + PDF/Excel/Leadsheets/FinStmts (10 routes total) all delegate to `export.pipeline`. `routes/export_diagnostics.py` 661 → 218 lines.
**Priority:** P3.
**Source:** Architectural Remediation Plan phase 3.

**Discovery:** `backend/export/` package already exists (Sprint 539+) with `pipeline.py` + `serializers/` implementing the mapper/generator separation per ADR-016. Routes had drifted into a parallel inline implementation. Sprint 748 is therefore a delegation migration, not a new layer build.

**What landed in 748a:**
- 6 CSV routes in `routes/export_diagnostics.py` migrated to delegate to `export.pipeline`:
  - `export_csv_trial_balance` (66 lines → 2)
  - `export_csv_anomalies` (71 lines → 2)
  - `export_csv_preflight_issues` (24 lines → 2)
  - `export_csv_population_profile` (58 lines → 2)
  - `export_csv_expense_category` (64 lines → 2)
  - `export_csv_accrual_completeness` (45 lines → 2)
- Net `export_diagnostics.py` shrunk 661 → 358 lines (~46% reduction).
- Removed unused `sanitize_csv_value` import (no longer referenced after migration).
- 119/119 export tests pass (`test_export_diagnostics_routes`, `test_export_routes`, `test_export_csv_serializers`).

**What landed in 748b (post-initiative finishing pass, commit `66e4ae2f`):**
- Pipeline now accepts optional `branding`; PDF/Excel/Leadsheets/FinStmts routes are 1-3 line delegates.
- `routes/export_diagnostics.py` 358→218 lines (661→218 across 748a+748b combined).

**Exit met:** All 10 diagnostic export routes are slim controllers delegating to the existing pipeline. Transformation logic is consistently owned by `export.serializers.*`.

---

### Sprint 749: Export endpoint skeleton standardization + memos harmonization (Phase 3 — Export Rationalization 2/2)
**Status:** COMPLETE 2026-04-29.
**Priority:** P3.
**Source:** Architectural Remediation Plan phase 3.

**What landed:**
- **ADR-016 promoted from Proposed → Accepted.** Documents the registry-driven memo dispatch as canonical: standard memos use `_STANDARD_REGISTRY` + `_register_standard_routes()` (16 routes today, 1-line entry per memo); non-standard memos that need custom Pydantic preprocessing get an explicit `@router.post(...)` decorator that calls the shared `_memo_export_handler` with a `CustomPreprocessor` (2 routes today: sampling-evaluation, flux-expectations). The mixed-style pattern is intentional, not drift.
- **PDF contract test pattern demonstrated.** New `backend/tests/test_export_pdf_contract.py` extracts text from generated memo PDFs via `pypdf.PdfReader` and asserts required section labels appear. Catches regressions where a section is silently removed or renamed (which CI/lint cannot detect). Sprint 749 ships the pattern with the JE Testing memo (5 required labels: title, "Tier", "Conclusion", "Findings", "Composite"); subsequent sprints extend to the remaining 17 memos as they're touched.
- Inline note on the contract-test file documents the multi-column PDF layout caveat: `pypdf` can split phrases across column boundaries, so prefer single-word anchors over multi-word phrases.

**Out of scope (deferred or covered elsewhere):**
- Standardize endpoint skeleton across PDF/Excel/Leadsheets/FinStmts routes — Sprint 748b's scope (needs pipeline branding-context plumbing).
- Move existing tests into a dedicated `tests/contract/` directory — pure churn; the per-file `_export_pdf_contract.py` naming is sufficient signal.
- Contract tests for all 18 memos — demonstrate the pattern, extend incrementally. (Post-initiative: 17/18 memos covered via commit `60946271`; flux_expectations remaining as Sprint 762.)

**Verification:** `tests/test_export_pdf_contract.py` 2/2 pass.

**Exit met:** Export endpoint shape consistency landed via Sprint 748a + memo registry pattern; ADR-016 documents the canonical strategy; PDF contract-test pattern in place with one demo memo.

---

### Sprint 750: Tool page architecture template + multi-period refactor (Phase 4 — Frontend Decomposition 1/3)
**Status:** COMPLETE 2026-04-29.
**Priority:** P3.
**Source:** Architectural Remediation Plan phase 4.

**What landed:**
- **ADR-017** (`docs/03-engineering/adr-017-tool-page-architecture-template.md`) — documents the canonical tool-page composition pattern: domain workflow hooks (uploads / comparison / export) + local UI/form state + thin orchestration callbacks + render-only JSX. Defines the local-state-vs-hook decision criteria (>15 lines, reused, async op, must be unit-testable).
- **`frontend/src/hooks/usePeriodUploads.ts`** (142 lines) — owns the three-slot `PeriodState` upload state machine for multi-period: prior / current / budget. Exposes derived `canCompare` / `anyLoading`, `toggleBudget` (clears stale state on OFF), `reset`, and an optional `onBeforeUpload` callback so consumers can clear stale comparison results when a new file lands.
- **`frontend/src/hooks/useMultiPeriodMemoExport.ts`** (81 lines) — owns the memo PDF export workflow: lead-sheet field stripping, metadata fallback to "Not specified", `apiDownload` invocation, `downloadBlob` trigger. Tracks `exporting` for button disabling.
- **Multi-period page refactored to composition root** — 501 → 423 lines. Inline 30-line `auditFile` machine, three `setPeriod` state buckets, `showBudget` toggle, and 44-line memo export gone. Page is now: auth + 3 hook calls + form state + thin orchestration callbacks + JSX.
- **8 hook tests for `usePeriodUploads`** (`__tests__/usePeriodUploads.test.ts`) covering: idle init, success transition, error transition, canCompare without/with budget, toggleBudget OFF clears state, reset, onBeforeUpload callback hook.
- **8 hook tests for `useMultiPeriodMemoExport`** (`__tests__/useMultiPeriodMemoExport.test.ts`) covering: starts idle, no-op on null token, lead-sheet stripping, metadata fallback, server filename use, default filename fallback, ok=false skip, error reset.
- Existing 8 multi-period page tests updated to mock the two new hooks. All 24 tests pass.

**Out of scope (deferred):**
- The deferred `useTrialBalanceUpload` decomposition — Sprint 750 didn't touch it. Multi-period uses the `uploadTrialBalance` utility function, not the `useTrialBalanceUpload` hook. The deferred-items entry remains valid as separate scope.
- Filter/metadata state extraction. Per ADR-017's local-state criteria, simple `useState` for filter strings and form labels stays inline — wrapping in a hook would be aesthetic-only.

**Verification:** `tsc --noEmit` clean, ESLint clean, 24/24 affected jest tests pass.

**Exit met:** Multi-period page is composition-only; ADR-017 documents the template; both pilot hooks have direct unit tests. Sprint 751 (dashboard decomposition) replicates the pattern next.

---

### Sprint 751: Dashboard decomposition (Phase 4 — Frontend Decomposition 2/3)
**Status:** COMPLETE 2026-04-29. Applies the ADR-017 template to `app/dashboard/page.tsx`.
**Priority:** P3.
**Source:** Architectural Remediation Plan phase 4.

**What landed:**
- **`frontend/src/content/dashboard-tools.ts`** — `DASHBOARD_TOOLS` (13 entries) + `DEFAULT_FAVORITES` + types. Single SoT for the dashboard's view of the catalog (decoupled from marketing `tool-ledger.ts`).
- **`frontend/src/components/dashboard/ToolIcon.tsx`** — `<ToolIcon iconKey={...} />` presentational component wrapping `TOOL_ICON_PATHS`. The 14 SVG path strings live here instead of inline in the page. Unknown keys fall back to `cube`.
- **3 new hooks** (`frontend/src/hooks/`):
  - `useDashboardStats(token, { onError })` → `{ stats, loading, error, retry }`. Auto-fetches `/dashboard/stats` on mount.
  - `useActivityFeed(token, { limit?, onError })` → `{ activity, loading, error, retry }`. Default `limit=8`.
  - `useUserPreferences(token, { onError })` → `{ favorites, toggleFavorite }`. Optimistic update + revert on PUT failure.
- **`app/dashboard/page.tsx` refactored to composition root** — 519 → 383 lines (-26%). Inline 78-line `TOOLS` catalog, 22-line `getToolIcon` SVG dump, two retry callbacks, three-fetch `useEffect`, and `toggleFavorite` machine all gone.
- **17 new hook tests** (4 + 5 + 8) covering happy path, null-token no-op, error → onError, retry, custom limit, optimistic-add/remove, revert on PUT failure.
- **DashboardPage smoke test (Sprint 743) still passes 4/4** — test mocks `apiGet`/`apiPut` directly, so the new hooks work transparently.

**Verification:** `tsc --noEmit` clean, ESLint clean, 21/21 affected jest tests pass.

**Exit met:** Dashboard logic in 3 narrow workflow hooks + presentational icon component + content-layer catalog. Tool metadata cannot drift across surfaces.

---

### Sprint 752: Oversized hook decomposition + render-perf guards (Phase 4 — Frontend Decomposition 3/3)
**Status:** COMPLETE 2026-04-29.
**Priority:** P3.
**Source:** Architectural Remediation Plan phase 4.

**Hook decomposition (`useFormValidation` 516 → 280 lines):**
- **`frontend/src/lib/validation/engine.ts`** (95 lines) — pure validation engine. No React imports. `validateFieldValue`, `validateAllFields`, `isFormValid`, `isFormDirty` + the type union (`ValidationRule`, `ValidationRules`, `FormErrors`, `TouchedFields`, `FormValues`). Deterministic, side-effect-free, reusable outside React (CLI scripts, server-side validation).
- **`frontend/src/lib/validation/validators.ts`** (87 lines) — `commonValidators` factory exports (8 reusable rules: required, minLength, maxLength, email, matches, min, max, pattern). Decoupled from the hook so they're unit-testable as plain function calls.
- **`frontend/src/hooks/useFormValidation.ts`** (280 lines, was 516) — React adapter. Owns `useState` slots + event handlers + render-stable getters. Delegates all validation to the pure engine. Re-exports types + `commonValidators` for backward compatibility (existing call sites unchanged).
- **Bug fix bundled in:** the legacy `setValue`'s `setTimeout(() => ..., 0)` for `validateOnChange` captured stale `values` in closure. The adapter now validates inside the `setValuesState` callback against the post-update values — eliminates the stale-closure race the timer was masking.
- **19 new pure-engine tests** (`__tests__/validationEngine.test.ts`) covering each pure function + every commonValidator. Existing 47 useFormValidation tests still pass without rewrites.

**Render-perf guards (dashboard hot path):**
- **`app/dashboard/page.tsx`** — memoized 3 derivations that previously reallocated on every render:
  - `summaryLine` (depends on `stats`)
  - `displayTools` (depends on `favorites`)
  - `toolByKey` Map for activity-feed lookup (constant — was O(n) `DASHBOARD_TOOLS.find` per row, now O(1) `toolByKey.get`)
- The activity feed renders up to 8 rows; the find-per-row pattern was negligible alone but compounded with mega-component rerenders. Memoized once at composition root.
- Hooks declared BEFORE the `if (!authenticated) return …` early return per `react-hooks/rules-of-hooks` (caught by ESLint).

**Verification:** `tsc --noEmit` clean, ESLint clean (3 violations caught + fixed during the sprint), 112/112 affected jest tests pass (47 useFormValidation + 19 validationEngine + 4 DashboardPage smoke + 42 consumer tests across LoginPage / RegisterPage / CreateClientModal / EditClientModal).

**Out of scope (deferred):**
- `getFieldProps(field)` allocates a new options object per call — child components rerender even when nothing relevant changed because the prop object identity changes. Per-field memoization via a Map is non-trivial because `field` is a runtime parameter; defer until profiling actually surfaces it as a hotspot.

**Exit met:** Form validation engine is testable without React; commonValidators are independently importable; dashboard derivations no longer reallocate per render. Hook responsibilities are narrow.

---

### Sprint 753: Domain package relocation (Phase 5 — Domain Consolidation 1/2)
**Status:** COMPLETE 2026-04-29 — pilot only; full migration is incremental per ADR-018.
**Priority:** P3.
**Source:** Architectural Remediation Plan phase 5.

**What landed:**
- **ADR-018** (`docs/03-engineering/adr-018-domain-package-relocation.md`) — documents the per-tool target layout (`services/audit/<tool>/{analysis,schemas,export}.py`), references `audit_engine.py` shim + `services/audit/flux_service.py` as existing precedents, and adopts ADR-013's incremental-migration discipline. Default: keep flat unless reorganization adds clear value.
- **Pilot relocation** — `recon_engine.py` (193 lines, 4 public symbols) moved to `backend/services/audit/flux/recon.py`. Selected because it's small, self-contained (only depends on `flux_engine.FluxResult` + `security_utils`), and pairs with the existing `flux_service.py` orchestrator.
- **Backward-compat shim** at `backend/recon_engine.py` (~25 lines) re-exports the 4 public symbols. All 6 existing callers (`routes/export_diagnostics.py`, `shared/helpers.py`, `leadsheet_generator.py`, `export/serializers/excel.py`, `services/audit/flux_service.py`, `tests/test_recon_engine.py`) work without modification.
- **Shim contract test** (`tests/test_recon_engine_shim.py`, 3 tests) asserts shim symbols are identical to canonical objects + `__all__` matches. A future edit that drops a symbol surfaces here loudly.

**Verification:** 60/60 tests across `test_recon_engine`, `test_recon_engine_shim`, `test_audit_flux_routes`, `test_export_routes` all pass.

**Out of scope (deferred):**
- Lint scan for top-level engines not in `services/audit/<tool>/` — folded into Sprint 756 (architecture conformance CI). Mirrors `scripts/lint_engine_base_adoption.py`.
- The remaining ~33 top-level `*_engine.py` files. Each is a separate sub-sprint per ADR-018's incremental discipline. (Post-initiative: `flux_engine`, `cutoff_risk_engine`, and 7 testing engines added — total 10 relocated.)

**Exit met:** Per-tool layout pattern documented (ADR-018) + proven (recon pilot). Top-level `recon_engine.py` is now a thin shim. Subsequent engines migrate one at a time without coordinated PRs across consumers.

---

### Sprint 754: Common analysis interfaces + helper dedup (Phase 5 — Domain Consolidation 2/2)
**Status:** **PARTIAL** 2026-04-29 — client-access relocation shipped (the explicit deferred-items condition); shared analysis interfaces + broader helper dedup deferred to dedicated follow-ups since they need more design work than fits in one sprint without compromising quality. **Sprint 754b (post-initiative)** subsequently shipped the shared interfaces (commit `8cbdc03a`).
**Priority:** P3.
**Source:** Architectural Remediation Plan phase 5.

**What landed (client-access relocation — resolves the deferred-items condition):**
- The deferred-items entry in `tasks/todo.md` (2026-04-20) said: "revisit only if a fourth helper joins them." Sprint 735 added `require_client_owner` as the fourth, so Sprint 754 made the move.
- **`backend/shared/client_access.py`** (new, 100 lines) — owns `is_authorized_for_client`, `get_accessible_client`, `require_client`, `require_client_owner`. Module docstring documents the org-scoped vs direct-only access policy distinction.
- **`backend/shared/helpers.py`** — removed all client-access definitions; module is now pure parsing/coercion utilities (`try_parse_risk`, `try_parse_risk_band`, `parse_json_list`, `parse_json_mapping`).
- **All 6 callers migrated** to import from `shared.client_access` directly: `routes/clients.py`, `routes/diagnostics.py`, `routes/prior_period.py`, `routes/settings.py`, `routes/trends.py`, `tests/test_sprint_735_require_client_owner.py`. **No shim maintained on `shared.helpers`** — matches the Sprint 724 discipline of avoiding re-export shims.
- **`tests/test_no_helpers_reexports.py`** — `ALLOWED_HELPER_NAMES` shrunk to the four parsing helpers. The guardrail keeps enforcing that no other names get re-introduced into `shared.helpers`.
- **`tests/test_refactor_2026_04_20.py::test_json_form_and_client_access_symbols`** — split the import statement into two: parsing helpers from `shared.helpers`, client-access helpers from `shared.client_access`. Test still passes (asserts both modules' surface).

**Verification:** 70/70 tests pass (`test_no_helpers_reexports`, `test_sprint_735_require_client_owner`, `test_refactor_2026_04_20`, plus 51 consumer-route tests across `test_clients_api`, `test_diagnostics_api`, `test_prior_period_api`, `test_settings_api`, `test_trends_api`).

**Out of scope (deferred):**
- **Shared analysis interfaces** (input contract / result envelope / error semantics for tool services). Each tool's `<tool>Result` dataclass has its own shape; converging them needs a careful design pass and a per-tool migration. ADR-018's per-tool package layout is a prerequisite (`schemas.py` is the natural home). File as Sprint 754b when there are 2+ tools relocated under the new layout to compare shapes. **(Done 2026-04-29 post-initiative — ADR-019 + Protocols.)**
- **Broader numeric/threshold helper dedup.** Survey found no obvious 1:1 duplications across engines — `round(x, 2)` is too simple to dedupe (more abstraction than it saves), and the existing `try_parse_risk*` helpers already cover risk-band parsing. The "threshold handling" surface is genuinely engine-specific (each tool's materiality logic is bespoke). No churn-worthy targets identified.
- **Module-boundary tests** asserting routes don't bypass service contracts. Depends on having shared interfaces defined first (Sprint 754b). Folds naturally into Sprint 756's CI conformance work.

**Exit met (partial scope):** The deferred-items condition is resolved (4th helper triggered the move; relocation complete). Boundary discipline + shared interfaces remain as future work but don't block subsequent sprints — they're additive improvements, not pre-requisites for Phases 6-8.

---

### Sprint 755: Dead code + duplicate type cleanup (Phase 6 — Drift Elimination 1/2)
**Status:** COMPLETE 2026-04-29. Survey-driven sprint — found a single dead alias to remove and confirmed the rest of the codebase is already clean from Sprint 724's prior helpers-shim removal + ruff-F401 enforcement in CI.
**Priority:** P3.
**Source:** Architectural Remediation Plan phase 6.

**What landed:**
- **Removed `_build_risk_summary` legacy alias from `audit_engine.py`.** It was a deprecated alias for the renamed `build_risk_summary` function — zero callers remained anywhere in the codebase. ~3 lines + the `__all__` entry. 69/69 audit-core + audit-anomalies tests still pass.

**Survey results (most of Sprint 755's planned scope was already clean):**
- **`ruff check --select F401` passes cleanly.** No unused Python imports anywhere. CI's lint-baseline gate enforces this — Sprint 724's helpers-shim removal already drove the codebase to F401-clean.
- **No duplicate frontend types.** Sprint 752's `lib/validation/engine.ts` exports each type once; `useFormValidation.ts` re-exports them. Verified with grep — `ValidationRule`, `FormErrors`, `TouchedFields`, `FormValues` all defined in exactly one place.
- **Deprecated markers surveyed:** 4 hits in backend (`audit_engine.py` legacy alias — removed; `routes/activity.py` "Legacy TB-only stats" — backward-compat for client API contract; `shared/parsing_helpers.py` DEPRECATED note for `safe_decimal` — has explicit transition rationale; `shared/passcode_security.py` legacy bcrypt path — explicit transition window note). Only the first was safe to remove without coordination.
- **Frontend `motionTokens.DISTANCE` `@deprecated`** — survey confirmed `subtle`/`standard`/`dramatic` are unused externally, but `state` is still used internally by `STATE_CROSSFADE` in the same file. Removing the deprecated keys would force a rename of the constant and a test update — too cosmetic to justify the churn this sprint.

**Out of scope (deferred):**
- Broader sweep across 800+ files needs tool-assisted analysis (e.g., per-symbol reachability across the import graph). The cheap wins from `ruff F401` are already gone. Sprint 756's CI conformance work is the natural place to add stronger drift detectors (forbidden imports, banned re-export shims) that catch dead code at PR time rather than retrospectively.
- Constant/magic-string dedup — survey didn't surface a critical mass of duplicate magic strings worth a dedicated typed-config module. The existing `shared/csv_export.py`, `tools_registry.py`, `standards_registry.py` already centralize the high-traffic constants. Defer to Sprint 759's convergence scorecard, which will revisit this from the catalog-consistency angle.

**Verification:** `ruff check` clean; 69/69 affected pytest tests pass.

**Exit met (within survey scope):** Confirmed dead code removed. The "broader cleanup" this sprint was originally scoped for turns out to already be done — credit to Sprints 519, 539, 661, 717, 720, 724, and the F401 baseline gate that's been running in CI through this initiative.

---

### Sprint 756: Architecture conformance CI + docs refresh (Phase 6 — Drift Elimination 2/2)
**Status:** COMPLETE 2026-04-29.
**Priority:** P3.
**Source:** Architectural Remediation Plan phase 6.

**What landed:**
- **`scripts/lint_domain_relocation.py`** (ADR-018, Sprint 753 deferral) — advisory CI scan that flags top-level `backend/*_engine.py` modules not yet relocated to `services/audit/<tool>/`. Detection: AST scan classifies a module as a "shim" (imports + `__all__` + docstring only) or as still-housing-the-implementation. Blocklist (`NON_RELOCATABLE_ENGINES`) for cross-cutting engines that don't fit the per-tool layout (`audit_engine`, `engine_framework`, `benchmark_engine`). Currently surfaces 31 findings (recon is correctly excluded after Sprint 753's pilot).
- **`scripts/lint_route_layer_purity.py`** (ADR-015) — advisory CI scan that flags route modules importing engine orchestration symbols (`*Engine` classes, `run_*`, `process_*`, `audit_trial_balance_*`). Routes legitimately importing dataclasses for type annotations (`FluxResult`, `ReconScore`, etc.) are NOT flagged. Currently surfaces 16 violations across ~12 route files — exactly the route-thinning backlog.
- Both scripts mirror `lint_engine_base_adoption.py`'s discipline: warning-only (exit 0) by default, `--strict` flag flips exit code for manual verification before promotion to hard gates.
- **CI wired**: both scans added to `.github/workflows/ci.yml` `backend-tests` job with `continue-on-error: true`.
- **31 lint-script tests** (`test_lint_domain_relocation.py` 18 tests + `test_lint_route_layer_purity.py` 13 tests) covering candidate filters, AST detection (shim vs. implementation, engine-class vs. dataclass heuristics), CLI flow (default exit 0 / `--strict` exit 1), and smoke checks against the actual repo.
- **`CONTRIBUTING.md` updated** — "Architectural Patterns" section now lists ADRs 014–018 and a new "Architecture conformance lints (advisory)" subsection with all three scans.

**Out of scope (deferred):**
- **Banned direct network calls (backend)** — Sprint 744's ESLint rule already enforces frontend; backend's HTTP client surface is bounded to `httpx`/`stripe` SDKs and doesn't need a parallel scan.
- **Duplicate route patterns** — would need full route-table analysis (FastAPI `app.routes` inspection at import time). Filed as Sprint 759 candidate (convergence scorecard) where it fits the broader catalog-consistency angle.
- **CLAUDE.md architecture-section update** — the file is operator-protocol authority that the existing architecture-pointers section already covers via "Key Capabilities" + sprint era summaries. No update needed; the new ADRs are linked from CONTRIBUTING.md which is the contributor-facing doc.

**Verification:** 31/31 lint-script tests pass. Both scans run successfully against the live repo (31 + 16 advisory findings).

**Exit met:** Drift detectors enforced in CI (advisory mode, ready for promotion to hard gates as their respective backlogs clear). Contributor docs reference the new ADRs + lint scripts.

---

### Sprint 757: Network duplication + transformation hotspot audit (Phase 7 — Performance Hardening 1/2)
**Status:** COMPLETE 2026-04-29.
**Priority:** P3 — structural perf only; not a micro-tuning sprint.
**Source:** Architectural Remediation Plan phase 7.

**What landed (one concrete consolidation + survey findings):**

**Frontend:** `app/tools/page.tsx` favorite-management consolidated onto `useUserPreferences` (Sprint 751). Eliminated 30+ lines of duplicated state machinery: `useState<string[]>([])`, `useEffect` fetching `/settings/preferences`, inline `apiPut` toggle with revert. Both `/dashboard` and `/tools` now compose the same hook, sharing apiClient cache + dedup. Bonus: side-effect bug fixed where the two pages could diverge mid-session if user toggled a favorite on one tab while the other had stale state.

**Bonus render-perf guard:** precomputed `favoritesSet = new Set(favorites)` so the per-card `.includes(tool.key)` check is O(1) instead of O(favorites) × N tools.

**Survey results:**
- **Frontend network duplication.** Survey of `apiGet` callers in `app/` found `/dashboard`, `/tools`, `/settings/team`, `/status`, and the engagement workspace page. Only the dashboard ↔ tools-catalog pair shared an endpoint (`/settings/preferences`) — fixed via this sprint. The others fetch endpoint-specific data with no overlap. apiClient's existing in-flight dedup + stale-while-revalidate cache already handles the same-component-mounting-twice case at the transport layer.
- **Repeated transformations.** Sprint 752 already memoized the dashboard's hot derivations (`summaryLine`, `displayTools`, `toolByKey`). Sprint 757 added `favoritesSet` to tools-page. No further per-render allocation hotspots surfaced in a survey of remaining pages.
- **Backend route-layer shaping.** Surveyed top-by-line-count + top-by-loop-count routes. The largest loops (e.g., `routes/activity.py::get_tool_activity_feed`) are straightforward DB-row → Pydantic-response transforms, request-time by definition, capped at `limit=8` for the dashboard's primary call. Sprint 748a already moved 6 CSV diagnostic routes to delegate to `export.pipeline`. The remaining inline shaping (PDF/Excel/Leadsheets/FinancialStatements routes) is captured by Sprint 748b's filed scope.

**Out of scope (deferred):**
- **Sentry breadcrumbs / browser perf-panel instrumentation** — would need a profiling sprint with real production traffic to identify hotspots beyond what static analysis surfaces. The codebase already emits Sentry breadcrumbs at the apiClient layer (Sprint 562); deeper instrumentation is an investigation task, not a refactor.
- **Sprint 748b's PDF/Excel migration** — separate filed sprint with its own scope (pipeline branding-context plumbing).

**Verification:** `tsc --noEmit` clean; 12/12 affected jest tests pass (8 useUserPreferences + 4 DashboardPage smoke). No tests existed for `app/tools/page.tsx`; tsc + the unchanged useUserPreferences tests are the regression net.

**Exit met:** Duplicate `/settings/preferences` fetch + optimistic-update logic eliminated. The single concrete duplication this initiative had created across Sprints 750-751 is consolidated. Sprint 758's pagination + cache invalidation coherence is the natural next step.

---

### Sprint 758: Pagination + cache invalidation coherence (Phase 7 — Performance Hardening 2/2)
**Status:** COMPLETE 2026-04-29 — survey-driven; no code changes warranted, both patterns already coherent.
**Priority:** P3.
**Source:** Architectural Remediation Plan phase 7.

**What landed:**
- **`docs/03-engineering/pagination-and-cache-conventions.md`** — documents the two server-side pagination patterns (`PaginationParams` for browsable lists vs. bare `limit` for bounded feeds) and the client-side cache invalidation contract (`invalidateRelatedCaches` clears endpoint + parent path on every successful mutation). Includes the picking-between-them table, edge cases, and a checklist for new endpoints.

**Survey results:**
- **Pagination patterns are already coherent.** Sprint 544 established `PaginatedResponse[T]` + `PaginationParams` for browsable lists; 4 routes use it (`activity` history, `clients`, `analytical_expectations`, `follow_up_items`). 7 routes use bare `limit` for feed surfaces (latest N items, no paging — `activity/tool-feed`, `diagnostics/recent`, `trends`, `prior_period`, `internal_admin` × 2). No mixing; no third pattern. The two are intentionally distinct.
- **Cache invalidation contract is already correct.** `apiPost`/`apiPut`/`apiPatch`/`apiDelete` in `apiClient.ts` all call `invalidateRelatedCaches(endpoint)` on `result.ok`. The helper clears (a) the endpoint path itself and (b) the parent collection path — catches the standard "mutate single resource, list view goes stale" pattern.

**Documented limitations (out of scope):**
- Cross-component React `useState` doesn't auto-sync after mutations — `useUserPreferences` on dashboard stays stale until remount when `/tools` toggles a favorite, even though apiClient cache invalidates correctly. Live-sync would need a shared store (Zustand/Redux); out of scope for this initiative.
- Mutation-cascade across unrelated endpoints (`/clients/123` change → `/dashboard/stats` recompute) is bounded by cache TTL (~30s), not invalidated automatically. If immediate consistency matters, the route handler returns enriched data the caller consumes.

**Verification:** No code changes; doc-only sprint. Survey + audit confirmed convention compliance.

**Exit met:** Conventions documented; new endpoints + mutations have explicit picking criteria + a checklist.

---

### Sprint 759: Convergence scorecard + governance lane (Phase 8 — Convergence) — INITIATIVE END
**Status:** COMPLETE 2026-04-29. Final sprint.
**Priority:** P3.
**Source:** Architectural Remediation Plan phase 8.

**What landed:**
- **`reports/architectural-remediation-scorecard-2026-04-29.md`** — full scorecard mapping each phase + each original weakness to RESOLVED / PARTIAL / OPEN status with explicit follow-up scope. TL;DR: 18 sprints planned, 18 shipped; phases 0/1/4/6/7/8 fully resolved; phases 2/3/5 partial with explicit follow-up sprints filed. 6 ADRs landed (014-018 + quality thresholds + pagination/cache conventions); 3 advisory CI lints; ~150 new pytest + ~50 new jest tests.
- **Governance cadence** documented in the scorecard:
  - Quarterly architecture health review — runs 3 advisory lints, checks deferred-items triggers, reviews quality-threshold deviations, files ≤2 follow-up sprints if warranted. Output: one-page `reports/arch-health-YYYY-QN.md`.
  - "No new god files" policy — new files exceeding hard caps need either a follow-up sprint reference OR an explicit decomposition-not-applicable docstring. Code-review enforced.
  - Refactor intake lane — new findings filed in `## Refactor Intake` section (in `tasks/todo.md`); surface via the existing lint scans + quarterly review.

**Refactor intake lane established** — see `## Refactor Intake` in `tasks/todo.md`.

**Exit met:** Every weakness in the original plan has a mapped outcome with explicit follow-up scope where work remains. Governance cadence + intake lane prevent relapse without spawning a Phase II.

**Initiative end.** Subsequent sprints should be product-driven, not architecture-driven. The remaining items in the scorecard's "Open follow-up scope" table are incremental hygiene visible through CI lints + the deferred-items list.

---

## Post-initiative finishing pass (2026-04-29)

Closed 4 partial-sprint follow-ups and shipped 7 testing-engine relocations as a standalone batch — work captured in the same finishing pass session, all on top of Sprint 759's INITIATIVE END marker.

- **Sprint 748b** (commit `66e4ae2f`) — PDF/Excel/Leadsheets/FinStmts routes onto `export.pipeline` (closes Sprint 748 partial scope).
- **`db_transaction` adoption sweep** (commit `3e967f17`) — 4 remaining route sites migrated; **zero `except SQLAlchemyError` blocks remain in `routes/*.py`**.
- **Sprint 754b** (commit `8cbdc03a`) — ADR-019 + Protocols (`IndicatorResult`, `TestingBatteryResult`, `CompositeScoreLike`, `TestResultLike`) + `ToolError(ValueError)` base. 16 conformance tests assert the 3 relocated indicators + 4 testing engines satisfy the contracts. Existing 18 tool dataclasses conform without code changes.
- **Memo PDF contract tests 1/18 → 17/18** (commits `9fdfba46` + `60946271`) — flux_expectations remaining as Sprint 762.
- **Engine relocation batch** (commits `bd074f1c` + `fae3e3e9`) — flux + cutoff_risk indicators + 7 testing engines (AP, AR, FA, Inv, JE, Payroll, Revenue) under ADR-018 with the dynamic-namespace shim pattern. Total relocated: 10. `lint_domain_relocation.py` extended to recognize the new shim pattern.
