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

### Sprint 547 — Cross-Repository Cohesion Remediation

**Status:** COMPLETE
**Goal:** Resolve 6 architectural decisions from cohesion audit: 12-tool identity, layered retention, workspace-centric navigation, tier label retirement, API reference scaffold, moderate fixes.

#### Phase 1 — Product Identity (12-tool suite)
- [x] README hero: 12-tool AI-powered audit intelligence suite
- [x] Product Vision: 5-tool → 12-tool throughout + version history
- [x] ARCHITECTURE.md: 11-tool → 12-tool, version updated
- [x] Entitlements.py: canonical tool count comment block
- [x] FastAPI app description updated
- [x] EXECUTIVE_SUMMARY_NONTECH.md: 11-tool → 12-tool
- [x] GuestCTA.tsx: comment updated to 12 tools
- [x] Terms page: pricing/tier/tool count corrected

#### Phase 2 — Retention Language (layered)
- [x] User Guide §16: canonical headline + precision copy added
- [x] User Guide §16.3: ephemeral scope clarification
- [x] User Guide FAQ: recovery answer rewritten
- [x] EXECUTIVE_SUMMARY: purged → archived (matches soft-delete implementation)

#### Phase 3 — Navigation Identity (workspace-centric)
- [x] ARCHITECTURE.md: Navigation Model section added
- [x] User Guide: "Diagnostic Workspace" → "Workspace" (2 occurrences)
- [x] ToS draft: "Diagnostic Workspace" → "Workspace" (3 occurrences)

#### Phase 4 — Tier Label Retirement
- [x] User Guide §15: Team/Organization → Professional/Enterprise + pricing corrected
- [x] User Guide FAQ: Team/Organization → Professional/Enterprise
- [x] Access Control Policy: tier table corrected
- [x] rate_limits.py: LEGACY ALIAS comments added
- [x] Terms page: Team/Organization → Professional/Enterprise

#### Phase 5 — API Reference (hybrid)
- [x] Deprecation header added to old API_REFERENCE.md
- [x] Generated skeleton: API_REFERENCE_GENERATED.md from router registry
- [x] Docstrings added to undocumented route handlers

#### Phase 6 — Remaining Fixes
- [x] ARCHITECTURE.md: tech stack versions corrected (React 19, Tailwind 4, framer-motion 12, FastAPI 0.135)
- [x] User Guide: Free tier export entitlement corrected (no exports)
- [x] Historical artifact headers: FEATURE_ROADMAP.md, EXECUTIVE_SUMMARY_NONTECH.md

#### Phase 7 — Deliverable
- [x] COHESION_REMEDIATION.md created

#### Review
- Commit: (pending)

---

### Sprint 548 — Test Suite Remediation

**Status:** COMPLETE
**Goal:** 4-phase test efficiency overhaul: CI optimization, structural dedup, coverage gaps, E2E smoke layer.

#### Phase 1 — Quick Wins
- [x] Register `slow` pytest marker in `backend/pyproject.toml`
- [x] Add `-m "not slow"` to PR CI runs, nightly job for slow tests
- [x] Deduplicate `TestRateLimitTiers` from `test_rate_limit_coverage.py` (6 tests → covered by `test_rate_limit_tiered.py`)
- [x] Raise frontend coverage thresholds with per-directory minimums (`src/hooks/`, `src/app/`)

#### Phase 2 — Structural Improvements
- [x] Extract AP fixtures to `backend/tests/helpers/ap_fixtures.py` (3 files deduped)
- [x] Create `toolPageScenarios.tsx` shared harness for frontend tool page tests
- [x] Refactor 7 tool page tests (AP, AR, JE, Payroll, Revenue, FixedAsset, Inventory) to use harness

#### Phase 3 — Coverage Gaps
- [x] `test_billing_routes.py` — 91 tests (checkout, subscription, cancel, webhook, dedup, seats, portal, usage, analytics)
- [x] `test_entitlement_checks.py` — 52 tests (all 16 check functions, soft/hard mode, seat limits)
- [x] `test_export_routes.py` — 50 tests (PDF/Excel/CSV, auth, validation, financial statements)
- [x] `useStatementBuilder.test.ts` — 56 tests (balance sheet, income statement, cash flow, mapping trace)
- [x] `BillingPage.test.tsx` — 6 tests (plan details, upgrade CTA, usage, error, loading)
- [x] `WorkspaceContext.test.tsx` — 7 tests (providers, selection state, toggles, error boundary)

#### Phase 4 — E2E Smoke Layer
- [x] Install Playwright, configure `playwright.config.ts`
- [x] Create `e2e/smoke.spec.ts` (auth, upload, export flows)
- [x] Add `e2e-smoke` job to CI (depends on backend-tests + frontend-tests, main-only)

#### Review
- Commit: 966000e
- Backend: 6,714 passed (3 pre-existing failures in pagination tests), 5 deselected (slow)
- Frontend: 1,426 passed across 118 suites, coverage thresholds met
- Build: passes

---

### Sprint 550 — Nightly Report Bug Remediation (DEC 2026-03-18)

**Status:** COMPLETE
**Goal:** Fix bugs identified by 2026-03-18 nightly report and DEC council review: 3 broken pagination tests, procedure rotation, risk tier label normalization.

#### F-001 (P1) — PaginatedResponse Schema Drift
- [x] `test_activity_api.py`: `"activities"` → `"items"` (lines 137, 142, 151)
- [x] `test_clients_api.py`: `"clients"` → `"items"` (line 115)
- [x] Grep audit: no other pre-migration field names found in test suite

#### F-002 (P2) — Suggested Procedures Rotation (BUG-001)
- [x] `ap_testing_memo_generator.py`: hardcoded `rotation_index=1` → `enumerate(detail_tests)` with `detail_idx`
- [x] `je_testing_memo_generator.py`: hardcoded `rotation_index=1` → `enumerate(high_sev_tests)` with `finding_idx`
- [x] `multi_period_memo_generator.py`: 4 hardcoded calls → removed `rotation_index=1` (use default primary + contextual index)

#### F-003 (P2) — Risk Tier Label Normalization (BUG-002)
- [x] `shared/memo_base.py`: `str(...).lower()` normalization on `RISK_TIER_DISPLAY` lookup
- [x] `bank_reconciliation_memo_generator.py`: 2 lookup sites normalized
- [x] `engagement_dashboard_memo.py`: 2 lookup sites normalized
- [x] `multi_period_memo_generator.py`: 1 lookup site normalized
- [x] `three_way_match_memo_generator.py`: 2 lookup sites normalized
- [x] `pdf/sections/diagnostic.py`: 1 lookup site normalized

#### F-005/F-006 — BUG-006 (Data Quality) / BUG-007 (Drill-Down Stubs)
- [x] Investigated: `assess_data_quality()` is correct; scoring converges for well-formatted data (design, not bug)
- [x] Investigated: `build_drill_down_table()` has `if not rows: return` guard; all callers pre-filter with `if not flagged: continue`
- [ ] BUG-006: Requires scoring calibration review (deferred — design decision, not code fix)
- [ ] BUG-007: Cannot reproduce from code analysis; may require PDF output inspection

#### Review
- Commit: 9571187
- Backend: 6,665 passed, 0 failed, 5 deselected (slow)
- Frontend: build passes
- Memo generators: 281/281 pass

---

### Sprint 549 — Governance Remediation (Codex Review)

**Status:** COMPLETE
**Goal:** Resolve 8 governance documentation inconsistencies identified by control-plane audit.

#### Task 1 — Archival threshold normalization
- [x] CLAUDE.md: "4+" → "5+" to match commit-msg hook
- [x] todo.md post-sprint checklist: clarify hook enforcement language

#### Task 2 — PR checklist count mismatch
- [x] CONTRIBUTING.md: "eight" → "ten" to match PR template

#### Task 3 — CI check count in Secure SDL
- [x] SECURE_SDL: executive summary 8 → 14, §4.1 table expanded to 14 checks, ci.yml noted as authoritative

#### Task 4 — Stale sprint state in CLAUDE.md
- [x] Removed stale Phase/Test Coverage/Next Phase lines, replaced with pointer to tasks/todo.md

#### Task 5 — Document Authority Hierarchy
- [x] Added "Document Authority Hierarchy" section at top of CLAUDE.md with 4-tier precedence

#### Task 6 — Stale path references in retry-policy.md
- [x] Fixed 3 occurrences: `src/utils/apiClient.ts` → `frontend/src/utils/apiClient.ts`, `src/utils/constants.ts` → `frontend/src/utils/constants.ts`

#### Task 7 — Audit ecosystem ownership boundary
- [x] Created `.claude/agents/AUDIT_OWNERSHIP.md` — scope/exclusion table + conflict resolution

#### Task 8 — Design instruction tie-break
- [x] Added brand authority header to `.claude/agents/designer.md` and `.claude/skills/frontend-design/SKILL.md`

#### Review
- Commits: 467dc89, 6b4c81d, 8b628ab, 6ce4596, 04ac2b1, d16955f, 40f9b8b, 0f93e1f
- All 8 tasks completed as separate commits
- No test files, CI logic, or hook scripts modified — governance docs only

---
