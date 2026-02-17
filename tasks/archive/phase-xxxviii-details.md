# Phase XXXVIII: Security & Accessibility Hardening + Lightweight Features (Sprints 279–286)

> **Focus:** Fix CVE-adjacent dependencies, close WCAG accessibility gaps, add 2 high-value features reusing existing infrastructure
> **Source:** 4-agent Council audit (BackendCritic, FrontendScout, QualityGuardian, AccountingExpertAuditor) — 2026-02-17
> **Version:** 1.6.0
> **Tests:** 3,440 backend + 931 frontend

| Sprint | Feature | Complexity | Status |
|--------|---------|:---:|:---:|
| 279 | Critical Security Fixes | 3/10 | COMPLETE |
| 280 | Backend Code Modernization | 3/10 | COMPLETE |
| 281 | Frontend Accessibility — Modals & Infrastructure | 4/10 | COMPLETE |
| 282 | Frontend Accessibility — Labels, Images & CSP | 4/10 | COMPLETE |
| 283 | Data Quality Pre-Flight Report | 4/10 | COMPLETE |
| 284 | Account-to-Statement Mapping Trace | 4/10 | COMPLETE |
| 285 | Backend Test Coverage Gaps | 3/10 | COMPLETE |
| 286 | Phase XXXVIII Wrap + v1.6.0 | 2/10 | COMPLETE |

---

## Sprint 279: Critical Security Fixes (3/10) — COMPLETE

- [x] Migrate `passlib` → raw `bcrypt` in `auth.py` (drop `passlib` dependency entirely)
- [x] Bump `python-multipart` 0.0.6 → 0.0.22 (CVE-2024-53498 ReDoS fix)
- [x] Fix X-Forwarded-For proxy trust: add `TRUSTED_PROXY_IPS` env var to `config.py`, custom `key_func` for slowapi that only trusts `X-Forwarded-For` from known proxies
- [x] Add `max_length=200` to `UserProfileUpdate.name`, `max_length=254` to email field
- [x] Hardcode `JWT_ALGORITHM = "HS256"` in `config.py` (remove operator configurability)
- [x] Bump `uvicorn` 0.40.0 → 0.41.0, `sendgrid` 6.11.0 → 6.12.5
- [x] Fix `datetime.utcnow()` in `test_tool_sessions.py:209`
- [x] Remove stale `sanitize_existing_sessions` full-table scan from `main.py` startup
- [x] All tests pass (3,396 backend)

**Review:** All 8 security items addressed. passlib fully removed (raw bcrypt 4.x), python-multipart CVE patched, X-Forwarded-For now only trusted from configured proxies, JWT algorithm no longer operator-configurable, stale startup scan eliminated. Test suite updated — bcrypt tests rewritten for raw bcrypt API, sanitize wiring test flipped to verify removal.

---

## Sprint 280: Backend Code Modernization (3/10) — COMPLETE

- [x] Expand `ruff.toml`: add `UP006`, `UP007`, `UP035` (typing modernization) + `I001` (import ordering)
- [x] Auto-fix typing modernization: 587 violations auto-fixed + 28 files manually cleaned (stale `from typing import` lines)
- [x] Remove global `F401` suppression; targeted `# noqa: F401` on `main.py` re-export. `F841` kept global (test fixtures)
- [x] Migrate 12 `backref=` → `back_populates` across `models.py`, `engagement_model.py`, `follow_up_items_model.py`
- [x] Add composite index `ix_diagnostic_summaries_client_user_period(client_id, user_id, period_date)` via Alembic migration
- [x] Fix stray `from typing import Optional` in `auth_routes.py` (auto-cleaned by ruff)
- [x] All tests pass (3,396 backend)

**Review:** Typing modernized across entire backend (~50 files touched). `Optional[X]` → `X | None`, `List[X]` → `list[X]`, `Dict[X]` → `dict[X]`, imports sorted. All 12 implicit `backref=` replaced with explicit `back_populates` — both sides now declare their relationships. Composite index migration added for diagnostic_summaries lookup optimization. Ruff now checks 0 violations.

---

## Sprint 281: Frontend Accessibility — Modals & Infrastructure (4/10) — COMPLETE

- [x] Install `eslint-plugin-jsx-a11y`, add to `eslint.config.mjs` (recommended rules spread)
- [x] Add `role="dialog"` + `aria-modal="true"` + `aria-labelledby` to 4 modals (CreateClientModal, EditClientModal, CreateEngagementModal, ComparisonSection/SavePeriodModal)
- [x] Implement `useFocusTrap` hook (Tab cycle containment, Escape key dismissal, focus-on-open, restore-on-close)
- [x] Apply `useFocusTrap` to all 5 modals (including ColumnMappingModal which already had dialog roles)
- [x] Add `error.tsx` for `(auth)`, `(diagnostic)`, `(marketing)` route groups
- [x] Delete `ThemeTest.tsx` + `app/theme-test/page.tsx` (dead code removed)
- [x] `npm run build` passes, `npm test` 918 tests pass

**Review:** All 5 modals now have WCAG-compliant `role="dialog"` + `aria-modal="true"` + `aria-labelledby` pointing to heading ids. New `useFocusTrap` hook provides Tab/Shift+Tab cycling, Escape dismissal, auto-focus on open, and focus restoration on close. 3 route group error boundaries added. eslint-plugin-jsx-a11y enforces a11y rules going forward. ThemeTest dead code deleted.

---

## Sprint 282: Frontend Accessibility — Labels, Images & CSP (4/10) — COMPLETE

- [x] Link ~65 `<label>` elements to `<input>` via `htmlFor`/`id` pairing across all form components
  - 19 files: practice/page, profile/page, CreateEngagementModal, AdjustmentEntryForm, SamplingDesignPanel, SamplingEvaluationPanel, ComparisonSection, multi-period/page, FollowUpItemsTable, WorkpaperIndex, SamplingPanel (JE), WeightedMaterialityEditor, TestingConfigSection, flux/page, MaterialityControl, PeriodFileDropZone, FileDropZone, login/page (already had htmlFor), register/page (already had htmlFor)
- [x] Replace 10 raw `<img>` tags with `next/image <Image>` component across 9 files
  - `ToolNav.tsx` (2, with `priority` flag — LCP element), `MarketingNav.tsx`, `MarketingFooter.tsx`, `ProfileDropdown.tsx`, `settings/page.tsx`, `settings/practice/page.tsx`, `settings/profile/page.tsx`, `portfolio/page.tsx`, `engagements/page.tsx`
- [x] Add `aria-live="polite"` regions on tool page loading states (12/12 now covered)
  - 10 tools already had aria-live; added to multi-period compare button + SamplingDesignPanel + SamplingEvaluationPanel
- [x] Add `aria-label` to `CurrencyRatePanel.tsx` drop zone
- [x] Add CSP headers to Next.js via `next.config.js` `headers()` function
  - CSP, X-Content-Type-Options, Referrer-Policy, Permissions-Policy
- [x] Remove `unsafe-inline` from backend CSP `script-src` in `security_middleware.py` (API serves JSON, not HTML)
- [x] `npm run build` passes, `npm test` 918 tests pass

**Review:** 19 files updated with htmlFor/id label accessibility pairing. All 10 raw `<img>` tags migrated to next/image `<Image>` with proper width/height (370x510 actual logo dimensions), ToolNav gets `priority` flag for LCP. All 12 tool pages now have aria-live coverage. CurrencyRatePanel drop zone has descriptive aria-label. Frontend CSP headers added via next.config.js headers(). Backend CSP script-src no longer allows unsafe-inline (API-only, no HTML served).

---

## Sprint 283: Data Quality Pre-Flight Report (4/10) — COMPLETE

> **Source:** AccountingExpertAuditor Recommendation E — highest leverage, reuses existing `column_detector.py` module

- [x] New endpoint: `POST /audit/preflight` — structured data quality assessment before full TB diagnostic
- [x] `PreFlightReport` dataclass in `preflight_engine.py` with 6 checks:
  - Column detection confidence scores per detected column (weight 30%)
  - Null/empty values per column (weight 20%)
  - Duplicate account code entries (weight 15%)
  - Encoding anomalies — non-ASCII in account names (weight 10%)
  - Mixed debit/credit sign conventions within single accounts (weight 15%)
  - Zero-balance rows count (weight 10%)
  - Overall data readiness score (weighted, 0-100: Ready/Review Recommended/Issues Found)
- [x] Pydantic response schema `PreFlightReportResponse` + 5 nested models
- [x] Frontend: `PreFlightSummary` component (score card + column grid + issues list with expandable remediation)
- [x] Frontend: `usePreflight` hook + integration in `useTrialBalanceAudit` (file drop → preflight → proceed → full analysis)
- [x] PDF export: `POST /export/preflight-memo` via `preflight_memo_generator.py`
- [x] CSV export: `POST /export/csv/preflight-issues`
- [x] Export input schemas: `PreFlightMemoInput`, `PreFlightCSVInput`
- [x] Tests: 11 backend (7 engine + 1 serialization + 3 route registration) + 6 frontend component
- [x] Zero-Storage: all computation in-memory during upload request, readiness score in ToolRun metadata

**Review:** All 6 quality checks implemented with weighted readiness scoring. Pre-flight runs automatically on file drop, displays before full TB analysis. User clicks "Proceed to Full Analysis" to continue to the full diagnostic. PDF memo follows memo_base.py pattern with Header/Scope/Column Detection/Issues/Sign-Off/Disclaimer sections. Tests: 3,407 backend + 924 frontend.

---

## Sprint 284: Account-to-Statement Mapping Trace (4/10) — COMPLETE

> **Source:** AccountingExpertAuditor Recommendation F — zero new computation, reuses existing lead_sheet_grouping + financial_statement_builder

- [x] Extend TB audit response with `mapping_trace` field
- [x] Generate line-by-line mapping: each financial statement line → contributing TB accounts + balances
- [x] PDF section appended to financial statements memo (workpaper-ready tie-out)
- [x] Excel tab (5th tab) in existing workpaper export structure
- [x] Frontend: `MappingTraceTable` component in financial statements view (collapsible per statement line)
- [x] Tests: mapping trace generation + frontend component
- [x] Zero-Storage: all data already in-memory during TB audit run

---

## Sprint 285: Backend Test Coverage Gaps (3/10) — COMPLETE

- [x] New `test_users_api.py` (8 tests): PUT /users/me (name update, max_length rejection, no-auth 401), PUT /users/me/password (success, wrong current 400, no-auth 401), 2 route registration
- [x] New `test_auth_routes_api.py` (17 tests): POST /auth/register (success 201, duplicate 400, disposable 400), POST /auth/login (success, invalid password 401, nonexistent 401), POST /auth/logout (success, invalid token), GET /auth/csrf (token + no-auth), GET /auth/verification-status (verified user, no-auth 401), 5 route registration
- [x] Narrow `except Exception:` in `routes/audit.py:267` → `(ValueError, KeyError, TypeError, AttributeError)`
- [x] Narrow `except Exception:` in `routes/health.py:59` → `(SQLAlchemyError, OSError)` + add import
- [x] Update `test_health_api.py` mock: `Exception("Connection refused")` → `OSError("Connection refused")`
- [x] All tests pass: 3,440 backend (25 new)

**Review:** Users route fully covered (profile update + password change with real bcrypt hashes). Auth routes covered at HTTP layer (register/login/logout/csrf/verification-status). Both remaining broad `except Exception:` blocks narrowed to specific types. Pre-existing health test mock updated to match narrowed exception.

---

## Sprint 286: Phase XXXVIII Wrap + v1.6.0 (2/10) — COMPLETE

- [x] `pytest tests/ -v` — 3,440 passed
- [x] `npm test` — 931 passed (85 suites)
- [x] `npm run build` — zero errors
- [x] Bump `backend/version.py` to 1.6.0
- [x] Align `frontend/package.json` version to 1.6.0
- [x] Archive to `tasks/archive/phase-xxxviii-details.md`
- [x] Update `CLAUDE.md`, `tasks/todo.md`, `MEMORY.md`
