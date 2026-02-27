# Coverage Gap Report — Sprint 445

**Date:** 2026-02-26
**Backend:** 92.8% statements (54,008/58,178) — 5,444 tests, 1 skipped
**Frontend:** 42.9% statements, 34.8% branches, 35.0% functions, 44.5% lines — 1,333 tests (1 pre-existing failure fixed this sprint)

---

## Backend: Top 10 Gaps (Ranked by Risk)

| # | File | Coverage | Missing Lines | Priority | Suggested Test Type |
|---|------|----------|---------------|----------|---------------------|
| 1 | `routes/billing.py` | 34.8% | 167/256 | **P1** | Route integration tests — entitlement enforcement paths, seat add/remove edge cases, portal redirect, Stripe error paths |
| 2 | `shared/entitlement_checks.py` | 40.5% | 50/84 | **P1** | Unit tests — limit enforcement at each tier boundary (free→solo→team), tool-gating for uncovered tiers |
| 3 | `routes/export_diagnostics.py` | 17.2% | 246/297 | **P1** | Route integration tests — each of the 15+ export endpoints, auth guard, rate-limit responses, malformed input |
| 4 | `routes/export_testing.py` | 19.1% | 169/209 | **P1** | Route integration tests — per-tool export (JE, AP, Payroll, Revenue, AR, TWM, Fixed Asset, Inventory, Bank Rec, Sampling) |
| 5 | `secrets_manager.py` | 32.8% | 83/92 | **P1** | Unit tests — secret retrieval fallbacks, env var override paths, missing-secret error handling |
| 6 | `expense_category_memo.py` | 9.8% | 83/92 | **P2** | Unit tests — PDF memo generation for each of 5 expense categories, framework-aware citation rendering |
| 7 | `leadsheet_generator.py` | 11.4% | 124/140 | **P2** | Unit tests — lead sheet PDF rendering, A-Z code coverage, each tool section |
| 8 | `workbook_inspector.py` | 21.9% | 107/137 | **P2** | Unit tests — column inspection for each supported format (CSV, XLSX, ODS, PDF, IIF, OFX), schema validation |
| 9 | `routes/export_memos.py` | 36.0% | 146/228 | **P2** | Route integration tests — 11 memo types, auth guard, download response headers, engagement context injection |
| 10 | `excel_generator.py` | 45.7% | 328/604 | **P2** | Unit tests — sheet-per-tool generation, conditional column inclusion, column formatting, error row highlighting |

### Additional Gaps Requiring Monitoring

| File | Coverage | Risk |
|------|----------|------|
| `routes/audit.py` | 55.5% | P2 — Core TB diagnostic route; 134 missing lines |
| `routes/adjustments.py` | 51.6% | P2 — Approval gating paths; 92 missing lines |
| `routes/follow_up_items.py` | 52.3% | P2 — Engagement workflow; 82 missing lines |
| `routes/sampling.py` | 30.7% | P2 — Statistical sampling route; 52 missing lines |
| `billing/webhook_handler.py` | 85.2% | P2 — Stripe webhook; missing 23 lines (event edge cases) |
| `routes/currency.py` | 57.5% | P3 — Currency conversion routes; 45 missing |
| `config.py` | 55.7% | P3 — App config; 70 missing (mostly env var branches) |

### Non-Risk Zero-Coverage Files (Skip)

`format_utils.py`, `generate_large_tb.py`, `generate_sample_reports.py`, `scripts/validate_report_standards.py` — dev/CI utility scripts with no production code paths; testing not needed.

---

## Frontend: Top 10 Gaps (Ranked by Risk)

| # | File | Coverage | Stmts | Priority | Suggested Test Type |
|---|------|----------|-------|----------|---------------------|
| 1 | `components/financialStatements/useStatementBuilder.ts` | 0% | 169 | **P1** | Unit tests — BS/IS/CF computation logic, sign flip rules, empty account handling, framework-specific line items |
| 2 | `components/shared/testing/FlaggedEntriesTable.tsx` | 0% | 101 | **P1** | RTL tests — renders flagged rows, severity color mapping, sort/filter, empty state, pagination |
| 3 | `app/settings/billing/page.tsx` | 0% | 60 | **P1** | RTL tests — tier display, manage billing button, seat usage meter, upgrade prompts, cancel flow |
| 4 | `components/workspace/QuickSwitcher.tsx` | 0% | 111 | **P2** | RTL tests — Cmd+K trigger, fuzzy search, arrow key nav, tier-gated guard, recency ranking |
| 5 | `hooks/useWorkspaceInsights.ts` | 0% | 63 | **P2** | Unit tests — risk signal aggregation, follow-up open count, tool coverage calculation |
| 6 | `contexts/WorkspaceContext.tsx` | 0% | 25 | **P2** | Unit tests — provider state, useWorkspaceContext throw-without-provider, client/engagement sync |
| 7 | `app/(diagnostic)/flux/page.tsx` | 0% | 77 | **P2** | RTL tests — upload flow, flux table rendering, period selector, empty state |
| 8 | `app/settings/profile/page.tsx` | 0% | 78 | **P2** | RTL tests — form pre-population, save confirmation, email change flow, password change |
| 9 | `app/(workspace)/layout.tsx` | 0% | 46 | **P2** | RTL tests — auth redirect when unauthenticated, WorkspaceShell rendered, keyboard shortcut setup |
| 10 | `components/batch/BatchDropZone.tsx` | 0% | 72 | **P3** | RTL tests — drag-and-drop events, file-type rejection, progress state |

### Additional Zero-Coverage Hooks/Contexts

| File | Stmts | Risk |
|------|-------|------|
| `hooks/useKeyboardShortcuts.ts` | 19 | P2 — Global shortcut handling; no test at all |
| `hooks/useRegisterCommands.ts` | 13 | P2 — Command palette registry |
| `hooks/useARAging.ts` | 10 | P3 — AR aging tool hook |
| `components/shared/testing/TestingScoreCard.tsx` | 11 | P3 — Used across 9 tool pages |
| `components/shared/testing/TestResultGrid.tsx` | 18 | P3 — Used across 9 tool pages |
| `components/shared/testing/DataQualityBadge.tsx` | 18 | P3 — Used across 9 tool pages |
| `app/(auth)/verify-email/page.tsx` | 34 | P2 — Email verification flow |
| `app/history/page.tsx` | 12 | P3 — Activity history page |

---

## Summary & Recommended Action List

### Immediate (P1 — this sprint or next)
1. **`routes/export_diagnostics.py` + `routes/export_testing.py`** — These 2 export routes account for 415 missing backend lines; a `test_export_routes.py` file with one integration test per endpoint would close the largest single gap.
2. **`routes/billing.py` + `shared/entitlement_checks.py`** — Billing enforcement is the highest-revenue-risk path. Seat limit enforcement and tier-downgrade paths are untested.
3. **`components/financialStatements/useStatementBuilder.ts`** — 169-statement hook with no test coverage; used by the Balance Sheet, Income Statement, and Cash Flow pages.

### Next Sprint (P2)
4. **`secrets_manager.py`** — Security-critical; fallback/error paths untested.
5. **`expense_category_memo.py` + `leadsheet_generator.py`** — Both memo generators are < 12% covered; a single `test_memo_generators.py` covering the main render path for each would reach 80%+.
6. **`components/shared/testing/FlaggedEntriesTable.tsx`** — Used across 9 testing tools; no tests at all.
7. **`app/settings/billing/page.tsx`** — Billing UI page; tier display and seat usage entirely uncovered.

### Deferred (P3)
8. **`excel_generator.py`** (45.7%) — Large file; a targeted test for 5 most-used sheet types would move to 75%+.
9. **Frontend marketing/static pages** (`trust`, `contact`, `about`, `approach`) — Low-logic pages; snapshot tests sufficient but not urgent.
10. **Frontend hooks** (`useARAging`, `useFixedAssetTesting`, etc.) — Simple data-fetch wrappers; mock-heavy unit tests add low value unless logic diverges.

---

## Deferred Phase Note

A **Phase LXII — Export & Billing Test Coverage** sprint is recommended to close P1 gaps (items 1–2 above), targeting:
- `routes/export_diagnostics.py` → 70%+
- `routes/export_testing.py` → 70%+
- `routes/billing.py` → 70%+
- `shared/entitlement_checks.py` → 80%+
