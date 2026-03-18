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

- [2026-03-07] fb8a1fa: accuracy remediation — test count, storage claims, performance copy (16 frontend files)
- [2026-02-28] e3d6c88: Sprint 481 — undocumented (retroactive entry per DEC F-019)

---

## Deferred Items

| Item | Reason | Source |
|------|--------|--------|
| Composite Risk Scoring | Requires ISA 315 inputs — auditor-input workflow needed | Phase XI |
| Management Letter Generator | **REJECTED** — ISA 265 boundary, auditor judgment | Phase X |
| Expense Allocation Testing | 2/5 market demand | Phase XII |
| Templates system | Needs user feedback | Phase XII |
| Related Party detection | Needs external APIs | Phase XII |
| Marketing pages SSG | **Not feasible** — CSP nonce (`await headers()` in root layout) forces dynamic rendering; Vercel edge caching provides near-static perf | Phase XXVII |
| Test file mypy — full cleanup | 804 errors across 135 files (expanded from 68); `python_version` updated to 3.12 in Sprint 543 | Sprint 475/543 |

---

## Active Phase
> Sprints 478–497 archived to `tasks/archive/sprints-478-497-details.md`.
> Sprints 499–515 archived to `tasks/archive/sprints-499-515-details.md`.
> Sprints 516–526 archived to `tasks/archive/sprints-516-526-details.md`.
> Sprints 517–531 archived to `tasks/archive/sprints-517-531-details.md`.
> Sprints 532–536 archived to `tasks/archive/sprints-532-536-details.md`.
> Sprints 537–541 archived to `tasks/archive/sprints-537-541-details.md`.
> Sprints 542–546 archived to `tasks/archive/sprints-542-546-details.md`.
> Sprints 547–551 archived to `tasks/archive/sprints-547-551-details.md`.

### Sprint 553 — AUDIT-02 Authentication Lifecycle Remediation
**Status:** COMPLETE
**Scope:** 2 fixes from AUDIT-02 Authentication Lifecycle review

- [x] **FIX 1 (MEDIUM):** CSRF Logout Binding — bind logout CSRF validation to refresh-cookie owner via DB lookup, preventing cross-user CSRF token reuse on logout
- [x] **FIX 2 (LOW):** Session Inventory & Revocation — add session metadata columns (last_used_at, user_agent, ip_address) + 3 new API endpoints (GET/DELETE /auth/sessions)

**Review:**
- FIX 1: 3 new tests (cross-user rejected, same-user passes, no-cookie fallback) + 65 existing CSRF tests pass
- FIX 2: 12 new tests (list sessions, ownership enforcement, single/bulk revocation, route registration) + 26 existing auth route tests pass
- All 106 auth tests pass with zero regressions
- Files: `security_middleware.py`, `auth.py`, `models.py`, `routes/auth_routes.py`, migration `b6c7d8e9f0a1`

### Sprint 552 — AUDIT-01 Calculation Correctness Fixes
**Status:** COMPLETE
**Scope:** 5 confirmed defects from AUDIT-01 Financial Calculation Correctness review

- [x] **RPT-12 (CRITICAL):** Multi-Period duplicate normalized account overwrite — aggregate debits/credits instead of single-row overwrite
- [x] **RPT-07 (HIGH):** AR Aging `date.today()` fallback — add `as_of_date` config field, propagate through route → engine → `_compute_aging_days`
- [x] **RPT-10a (HIGH):** Bank Rec hardcoded $50k materiality — add `materiality`/`performance_materiality` to `BankRecConfig`, thread from route Form params
- [x] **RPT-10b (HIGH):** Bank Rec composite risk score missing from API — compute `composite_score` in `reconcile_bank_statement()`, serialize from `BankRecResult.to_dict()`, update `BankRecResponse` schema
- [x] **DASH-01 (HIGH):** Dashboard zero-score fallback — derive risk score from `rec_tests` when `composite_score` absent instead of hardcoding 0

**Review:**
- All 4 affected test suites pass (273 targeted + 278 broad = 551 tests verified)
- Files: `multi_period_comparison.py`, `ar_aging_engine.py`, `routes/ar_aging.py`, `bank_reconciliation.py`, `routes/bank_reconciliation.py`, `engagement_dashboard_engine.py`, `shared/testing_response_schemas.py`

