# Test Coverage Gap Analysis

**Sprint:** 743 (Phase 0.2 — Architectural Remediation Initiative)
**Date:** 2026-04-29
**Scope:** Surfaces touched by Sprints 747–752.

## TL;DR

The Paciolus test suite is 7,363 backend + 1,751 frontend tests. Most surfaces
relevant to Sprints 747–752 are covered. **One genuine gap surfaced:** no
targeted frontend test for the 519-line `app/dashboard/page.tsx`, which
Sprint 751 is scheduled to decompose. Filed as a gap-fill in this sprint.

## Coverage by surface

### Auth flows (Sprints 746b/c/d, 747)

| Surface | Test module(s) | Tests | Status |
|---------|----------------|-------|--------|
| Registration | `test_auth_routes_api.py`, `test_email_verification.py` | (in 214) | Covered |
| Login + lockout | `test_auth_routes_api.py`, `test_auth_parity.py` | (in 214) | Covered |
| Token refresh + rotation | `test_auth_routes_api.py`, `test_no_process_local_auth_state.py` | (in 214) | Covered |
| Logout + revocation | `test_session_endpoints.py` | (in 214) | Covered |
| Password reset | `test_password_reset.py`, `test_password_revocation.py` | 41 | Covered |
| Email verification | `test_email_verification.py` | (in 214) | Covered |
| Session inventory + revocation | `test_session_endpoints.py` | (in 214) | Covered |
| CSRF | `test_csrf_middleware.py` | (in 214) | Covered |
| Frontend `AuthSessionContext` + `useAuthSession` | `AuthContext.test.tsx`, `useAuthSession.test.ts` | — | Covered |
| Frontend pages (Login, ForgotPassword) | `LoginPage.test.tsx`, `ForgotPasswordPage.test.tsx` | — | Covered |

**214 backend tests + frontend coverage** across the 13 auth routes. Sprints
746b/c/d and 747 have a strong regression net.

### Export endpoints (Sprints 748, 749)

| Surface | Test module(s) | Tests | Status |
|---------|----------------|-------|--------|
| Diagnostic CSV/PDF/Excel | `test_export_diagnostics_routes.py` | (in 173) | Covered |
| Memo PDFs (per tool) | `test_*_memo.py` × 18 | — | Covered (content-level) |
| Export sharing + passcode | `test_export_sharing_routes.py`, `test_export_sharing_ip_throttle.py` | (in 173) | Covered |
| Engagement exports | `test_engagements_exports_api.py`, `test_engagement_export_*.py` | (in 173) | Covered |
| CSV serializers / helpers | `test_export_csv_serializers.py`, `test_csv_export_helpers.py`, `test_export_helpers.py` | (in 173) | Covered |
| Loan amortization exports | `test_loan_amortization_exports.py` | (in 173) | Covered |
| Memo memory budget + boundary phrasing | `test_memo_memory_budget.py`, `test_memo_boundary_phrasing.py` | (in 173) | Covered |

**173 backend tests** across export routes/helpers/memos. Frontend has
per-page export interaction tests on most tool pages
(`*Page.test.tsx`).

**Note:** Sprint 749's contract tests (schema-level CSV header / PDF section
assertions) are not yet present, but Sprint 749 explicitly produces them.
That's not a Sprint 743 gap.

### Dashboard + tool pages (Sprints 750, 751)

| Surface | Test module(s) | Status |
|---------|----------------|--------|
| Multi-Period (Sprint 750 target) | `MultiPeriodPage.test.tsx` | Covered |
| Tool pages × 18 | `*Page.test.tsx` (e.g., `JournalEntryTestingPage`, `APTestingPage`, ...) | Covered |
| Dashboard backend (`/dashboard/stats`) | `test_activity_api.py`, `test_admin_dashboard_api.py` | 30 tests, covered |
| **Dashboard frontend (`app/dashboard/page.tsx`)** | **none** | **GAP** |
| Workspace shell, navigation | `WorkspaceContext.test.tsx`, `MarketingNav.test.tsx`, `ToolNav.test.tsx`, `BottomProof.test.tsx` | Covered |

### API error envelope

| Surface | Test module(s) | Status |
|---------|----------------|--------|
| Sanitization | `test_log_sanitizer.py` | Covered |
| `raise_http_error` + `db_transaction` (Sprint 745) | `test_route_errors.py`, `test_db_unit_of_work.py` | Covered (14 tests) |
| Per-route error responses | (covered in route-API tests) | Covered |

### Hooks targeted by Sprint 752

| Hook | Test module | Status |
|------|-------------|--------|
| `useAuditUpload` | (covered indirectly via tool-page tests) | Covered |
| `useTrialBalanceAudit` | (covered indirectly) | Covered |
| `useStatisticalSampling` | `useStatisticalSampling.test.ts` | Covered |
| `useAccountRiskHeatmap` | `useAccountRiskHeatmap.test.ts` | Covered |
| `useUncorrectedMisstatements` | `useUncorrectedMisstatements.test.ts` | Covered |
| `useAnalyticalExpectations` | `useAnalyticalExpectations.test.ts` | Covered |
| `useFetchData` (generic factory) | (covered by every hook that uses it) | Covered |

## Identified gaps

### Gap 1: `app/dashboard/page.tsx` smoke test

**Surface:** 519-line client-component dashboard page, target of Sprint 751
decomposition. Currently only covered indirectly via context/nav tests; no
test directly exercises the page's rendering, data loading, or favorite-tool
toggle.

**Risk:** Sprint 751 plans to extract:
- `TOOLS` constant → tool catalog registry
- Inline data fetching → `useDashboardStats`, `useActivityFeed`, `usePreferences` hooks
- Page logic → composition root only

Without a smoke test pinning the page's basic render contract, a structural
extraction could introduce regressions that ship silently.

**Action (this sprint):** Add `frontend/src/__tests__/DashboardPage.test.tsx`
with smoke-level coverage:
- Renders welcome header + stat cards + Quick Launch grid.
- Calls `apiGet('/dashboard/stats')` + `apiGet('/activity/recent')` + `apiGet('/settings/preferences')` on mount.
- Toggling a favorite tool calls `apiPut('/settings/preferences', ...)`.
- Empty state when no recent activity.

This is Sprint 743's only filed gap-fill. Other surfaces are sufficiently
covered.

### Non-gaps (rejected)

- **Memo PDF schema contract tests** — Sprint 749 produces them; not a
  pre-existing gap.
- **Export endpoint contract tests** — same as above.
- **API error envelope snapshot** — `raise_http_error` + `db_transaction`
  ship with their own unit tests (Sprint 745). Existing route tests
  exercise the envelope through real handlers.
- **`useFetchData` decomposition coverage** — Sprint 752 hasn't picked
  the candidate yet (form validation is the named candidate). When a
  decomposition target is chosen, that sprint owns adding tests.

## Methodology

- Inventoried 199 frontend test files under `frontend/src/__tests__/` and
  the relevant backend test modules under `backend/tests/`.
- Cross-referenced surfaces named in Sprint 747–752 entries against
  existing test names + collected pytest counts.
- Looked for direct test files matching the surface; downgraded to
  "covered indirectly" only when an obvious sibling test (page test,
  context test) exercises the surface.

## Conclusion

Phase 0.2 closes with one filed gap-fill (DashboardPage smoke test) and
~387 backend + per-page frontend tests confirming the surfaces touched by
Sprints 747–752 are sufficiently covered. The earlier observed test churn
in Sprint 744 (Bearer-header pinning becoming obsolete) was a different
class of issue — outdated assertions, not missing coverage. Phase 0.2
does not address that class because the assertions surface as failures
when the migration runs (as they did in Sprint 744), self-correcting.
