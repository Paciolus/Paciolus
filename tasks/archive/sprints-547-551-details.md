# Sprints 547–551 Details

> Archived from `tasks/todo.md` Active Phase on 2026-03-18.

---

### Sprint 551 — Multi-Audit Remediation (Pre-Launch)

**Status:** COMPLETE
**Goal:** Comprehensive remediation from 5 independent audits: 3 high-confidence bug fixes, governance alignment, CI hardening, architectural refactors.

#### Phase 1 — Critical Fixes
- [x] BUG-01: `accept_invite()` double-counts pending invite against seat cap — pass `exclude_invite_id`
- [x] BUG-02: `remove_member()` blindly wipes paid subscription tier — check personal `Subscription` first
- [x] BUG-03: `create_share()` accepts arbitrary client bytes — add magic-byte validation + logging
- [x] Tests: 19 new tests (6 org routes, 13 export sharing)
- [x] CONTRIBUTING.md CI section — align with actual ci.yml (14 jobs)
- [x] conftest.py: ExportShare model import for FK resolution

#### Phase 2–3 — Governance & Docs (prior sessions)
- [x] AGENTS.md, SESSION_STATE.md, features/status.json, init.sh, docs/README.md (Sprint 547–549)
- [x] Compliance version fixes, tier name retirement, React version fix (Sprint 547)
- [x] tasks/todo.md split (PROTOCOL.md, COMPLETED_ERAS.md, EXECUTIVE_BLOCKERS.md) (Sprint 548)
- [x] Archive stale docs (phase-iii, FEATURE_ROADMAP.md) (Sprint 547)

#### Phase 3b — Doc Archival
- [x] Archive legacy DEPLOYMENT.md (v0.16) to `docs/archive/`
- [x] Archive legacy API_REFERENCE.md (v0.70) to `docs/archive/`
- [x] Update docs index and AGENTS.md references

#### Phase 4 — Testing Infrastructure
- [x] Raise frontend coverage thresholds (26/25/33/32 → 27/29/37/36)
- [x] Harden Playwright smoke spec assertions (unconditional file input check)
- [x] Add PR-triggered E2E smoke job to CI (graceful secret skip)
- [x] Add concurrency tests for seat enforcement (BUG-04)

#### Phase 5 — Architectural Refactors
- [x] Split anomaly_rules.py by anomaly family (7 modules: balance, suspense, concentration, rounding, relationships, equity, merger)
- [x] Unify upload flow in useStatisticalSampling.ts (extracted `executeSamplingUpload` shared handler)
- [x] Prevent apiClient.ts god-module drift (governance contract comment added)
- [x] ~~Split billing.py~~ — already a clean facade, no action needed
- [x] ~~Migrate AuthContext facade~~ — facade is intentional design (78 lines), no action needed
- [ ] Decompose pipeline.py post-processing stages (deferred — already well-structured, 566 lines)
- [ ] Wire organization routes to existing service layer (deferred — service exists, wiring is low-risk)
- [ ] Move format serialization out of export_diagnostics.py (deferred — CSV is trivial, PDF/Excel already delegated)
- [ ] Extract pricing business rules from pricing page (deferred — 995 lines, high effort)

#### Review
- Commits: 551944b, 1a39f52, 431640d, f3bf1dd
- Backend: 4,596 passed, 1 flaky (pre-existing event loop issue), 5 deselected (slow)
- Frontend: 1,426 passed across 118 suites, build OK
- Coverage thresholds: raised and passing
- 4 deferred items tracked (pipeline decomposition, org service wiring, export extraction, pricing extraction)


---

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

