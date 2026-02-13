# Project Protocol: The Council

## Role: IntegratorLead
You are the synthesis lead. You do not originate large ideas; you resolve deadlocks between sub-agents and the CEO (User).

## Interaction Protocol: The Conflict Loop
When a task is initiated:
1. **Call Specialists:** Use `/agents run` to consult `critic`, `scout`, `executor`, and `guardian`.
2. **Audit for "Hive-Mind":** If agents agree too quickly, you must play devil's advocate.
3. **Identify Tensions:** Explicitly state: "[Agent A] wants X, but [Agent B] insists on Y."
4. **The Tradeoff Map:** Present the CEO with a choice between specific technical/market sacrifices.

## Global Rules
- **No "I Agree":** Forbid agents from simply echoing.
- **Steel Man:** Every critique must acknowledge the merit of the original idea before dismantling it.
- **Decision Rule:** No path is final until an implementation plan exists and a "Complexity Score" is assigned.

---

## MANDATORY: Directive Protocol

**STRICT REQUIREMENT:** Every new directive MUST follow this protocol:

### 1. Plan Update (START of directive)
Before ANY implementation begins:
- [ ] Read `tasks/todo.md`
- [ ] Add/update checklist items for the current directive
- [ ] Mark the directive as "In Progress"
- [ ] Identify which agents are involved

### 2. Implementation
- Follow the Conflict Loop
- Track progress by checking off items in `tasks/todo.md`
- Document blockers in the Review section

### 3. Verification (BEFORE marking complete)
Before declaring a directive complete:
- [ ] Run `npm run build` in frontend (must pass with no errors)
- [ ] Run `pytest` in backend if tests were modified
- [ ] Verify Zero-Storage compliance for any new data handling

### 4. Lesson Learned (END of directive)
After directive completion:
- [ ] Add entry to `tasks/lessons.md` if ANY of these occurred:
  - CEO provided a correction
  - A better pattern was discovered
  - A mistake was made and fixed
  - An assumption proved wrong
- [ ] Update `tasks/todo.md` Review section with completion notes
- [ ] Mark all directive items as complete

### 5. Git Commit (FINAL step)
After ALL directive work is complete:
- [ ] Stage relevant files (avoid `git add -A` to prevent accidental inclusions)
- [ ] Create atomic commit with descriptive message: `Sprint X: [Brief Description]`
- [ ] Commit message should reference the sprint number and key changes

**FAILURE TO FOLLOW THIS PROTOCOL WILL RESULT IN AUDIT SCORE PENALTIES.**

---

## Current Project State

**Project:** Paciolus — Professional Audit Intelligence Platform for Financial Professionals
**Phase:** Phase XXII — Pydantic Model Hardening (Sprints 184–190, COMPLETE)
**Model:** Agent Council Sprint Delivery (6-agent consensus prioritization)
**Health:** PRODUCTION READY
**Version:** 1.2.0
**Test Coverage:** 2,716 backend tests + 128 frontend tests
**Next Phase:** Phase XXIII (TBD)

### Completed Phases (details in `tasks/todo.md`)
- **Phase I (Sprints 1-24):** Core platform — Zero-Storage TB analysis, streaming, auth, PDF/Excel export, client management, practice settings, deployment
- **Phase II (Sprints 25-40):** Test suite, 9 ratios, IFRS/GAAP, trend analysis, industry ratios, rolling windows, batch upload, benchmark RFC
- **Phase III (Sprints 41-47):** Anomaly detection (suspense, concentration, rounding, balance sheet), benchmark engine + API + UI
- **Phase IV (Sprints 48-55):** User profile, security hardening, lead sheets, prior period comparison, adjusting entries, DSO, CSV export, frontend tests
- **Phase V (Sprints 56-60):** UX polish, email verification (backend + frontend), endpoint protection, homepage demo mode
- **Phase VI (Sprints 61-70):** Multi-Period TB Comparison, Journal Entry Testing (18-test battery + stratified sampling), platform rebrand, diagnostic zone protection
- **Phase VII (Sprints 71-80):** Financial Statements, AP Payment Testing (13-test battery), Bank Reconciliation, 5-tool navigation standardization
- **Phase VIII (Sprints 83-89):** Cash Flow Statement (indirect method), Payroll & Employee Testing (11-test battery), 6-tool navigation, code quality sprints (81-82)
- **Phase IX (Sprints 90-96):** Code quality extraction (shared enums/memo/round-amounts), Three-Way Match Validator (Tool 7), Classification Validator (TB Enhancement), 7-tool navigation
- **Phase X (Sprints 96.5-102):** Engagement Layer — engagement model + materiality cascade, follow-up items tracker, workpaper index, anomaly summary report, diagnostic package export, engagement workspace (frontend)
- **Phase XI (Sprints 103-110):** Tool-Engagement Integration, Revenue Testing (Tool 8), AR Aging (Tool 9), 9-tool nav, v1.0.0
- **Phase XII (Sprints 111-120):** Nav overflow, Finding Comments + Assignments, Fixed Asset Testing (Tool 10), Inventory Testing (Tool 11), 11-tool nav, v1.1.0
- **Phase XIII (Sprints 121-130):** Platform polish, dual-theme "The Vault" architecture, security hardening, WCAG AAA accessibility, 11 PDF memos, 24 rate-limited export endpoints, v1.2.0
- **Phase XIV (Sprints 131-135):** Professional Threshold — 6 public marketing/legal pages (Privacy, Terms, Contact, About, Approach, Pricing, Trust), shared MarketingNav/Footer, contact backend
- **Phase XV (Sprints 136-141):** Code Deduplication — shared parsing helpers, shared types, 4 shared testing components (DataQualityBadge, ScoreCard, TestResultGrid, FlaggedTable), context consolidation, ~4,750 lines removed
- **Phase XVI (Sprints 142-147):** API Hygiene — semantic token migration, API call consolidation (15 direct fetch → apiClient)
- **Phase XVII (Sprints 151-163):** Code Smell Refactoring — 7 backend shared modules (column detector, data quality, test aggregator, Benford, export schemas, testing route factory, memo template), 8 frontend decompositions, 15 new shared files, 8,849 lines refactored
- **Phase XVIII (Sprints 164-170):** Async Architecture Remediation — `async def` → `def` for pure-DB routes, `asyncio.to_thread()` for CPU-bound Pandas work, `BackgroundTasks` for email/tool-run recording, `memory_cleanup()` context manager, rate limit gaps closed
- **Phase XIX (Sprints 171-177):** API Contract Hardening — 100% `response_model` coverage, DELETE→204/POST→201 status codes, trends.py error-in-body→HTTPException(422), `/diagnostics/flux`→`/audit/flux` path fix, shared response schemas
- **Phase XX (Sprint 178):** Rate Limit Gap Closure — missing limits on verify-email, password-change, waitlist, inspect-workbook; global 60/min default
- **Phase XXI (Sprints 180-183):** Migration Hygiene — Alembic env.py model imports, baseline regeneration (e2f21cb79a61), manual script archival, datetime deprecation fix
- **Phase XXII (Sprints 184-190):** Pydantic Model Hardening — Field constraints (min_length/max_length/ge/le), str→Enum/Literal migration, manual validation removal (~30 lines try/except), model decomposition (WorkpaperMetadata base, DiagnosticSummaryCreate sub-models), v2 syntax (ConfigDict), password field_validators

### Key Capabilities
- 9 core ratios + 8 industry ratios across 6 benchmark industries
- A-Z lead sheet mapping, prior period comparison, adjusting entries
- Multi-Period TB Comparison (2-way + 3-way with budget variance)
- Journal Entry Testing: 18 automated tests (structural + statistical + advanced), Benford's Law, stratified sampling
- AP Payment Testing: 13 automated tests (structural + statistical + fraud indicators), duplicate detection
- Bank Statement Reconciliation: exact matching, auto-categorization, reconciliation bridge
- Financial Statements: Balance Sheet + Income Statement + Cash Flow Statement (indirect method, ASC 230/IAS 7)
- Payroll & Employee Testing: 11 automated tests (structural + statistical + fraud indicators), ghost employee detection
- Three-Way Match Validator: PO→Invoice→Receipt matching with exact PO# linkage + fuzzy fallback, variance analysis
- Revenue Testing: 12 automated tests (5 structural + 4 statistical + 3 advanced), ISA 240 fraud risk in revenue recognition
- AR Aging Analysis: 11 automated tests (4 structural + 5 statistical + 2 advanced), ISA 500/540 receivables valuation, dual-input (TB + optional sub-ledger)
- Fixed Asset Testing: 9 automated tests (4 structural + 3 statistical + 2 advanced), IAS 16/ASC 360 PP&E assertions, depreciation/useful life analysis
- Inventory Testing: 9 automated tests (3 structural + 4 statistical + 2 advanced), IAS 2/ASC 330 inventory assertions, slow-moving/obsolescence indicators
- Classification Validator: 6 structural COA checks (duplicates, orphans, unclassified, gaps, naming, sign anomalies) integrated into TB Diagnostics
- PDF/Excel/CSV export with workpaper signoff + JE/AP/Payroll/TWM/Revenue/AR Aging/Fixed Asset/Inventory/Bank Rec/Multi-Period Memos (PCAOB AS 1215/2401/2501, ISA 240/500/501/505/520/540)
- JWT auth, email verification, CSRF, account lockout, diagnostic zone protection
- Free/Professional/Enterprise user tiers
- Engagement Layer: Diagnostic Workspace with materiality cascade, follow-up items tracker, workpaper index, anomaly summary report, diagnostic package ZIP export
- Platform homepage with 11-tool suite + workspace marketing

### Unresolved Tensions
| Tension | Resolution | Status |
|---------|------------|--------|
| Multi-Currency Conversion | Detection shipped (Sprint 64); conversion logic deferred | Beyond Phase VII |
| Composite Risk Scoring | Rejected by AccountingExpertAuditor (requires ISA 315 inputs) | Deferred to Phase XI with auditor-input workflow |
| Management Letter Generator | Rejected permanently (ISA 265 boundary — deficiency classification is auditor judgment) | REJECTED |

### Phase XIII Overview (Sprints 121–130) — COMPLETE
> **Focus:** Platform polish + dual-theme architecture ("The Vault Interior")
> **Source:** Comprehensive Product Review (4 agents) + FintechDesigner spec — 2026-02-09
> **Strategy:** Hygiene first (broken tokens, versions, security), then theme infrastructure, then full light-theme migration
> **Design:** Dark homepage (vault exterior) → Light tool pages (vault interior). Route-based, not user-toggleable.
> **Target Version:** 1.2.0

| Sprint | Feature | Complexity | Agent Lead | Status |
|--------|---------|:---:|:---|:---:|
| 121 | Tailwind Config + Version Hygiene + Design Fixes | 3/10 | QualityGuardian + FintechDesigner | COMPLETE |
| 122 | Security Hardening + Error Handling | 4/10 | BackendCritic + QualityGuardian | COMPLETE |
| 123 | Theme Infrastructure — "The Vault" | 5/10 | FintechDesigner + FrontendExecutor | COMPLETE |
| 124 | Theme: Shared Components | 4/10 | FrontendExecutor + FintechDesigner | COMPLETE |
| 125 | Theme: Tool Pages Batch 1 (6 tools) | 5/10 | FrontendExecutor | COMPLETE |
| 126 | Theme: Tool Pages Batch 2 + Authenticated Pages | 5/10 | FrontendExecutor | COMPLETE |
| 127 | Vault Transition + Visual Polish | 4/10 | FintechDesigner + FrontendExecutor | COMPLETE |
| 128 | Export Consolidation + Missing Memos | 5/10 | BackendCritic + AccountingExpertAuditor | COMPLETE |
| 129 | Accessibility + Frontend Test Backfill | 5/10 | QualityGuardian + FrontendExecutor | COMPLETE |
| 130 | Phase XIII Wrap — Regression + v1.2.0 | 2/10 | QualityGuardian | COMPLETE |

> **Detailed checklists for Phases X-XII:** `tasks/archive/phases-x-xii-details.md`

### Phase XIV Overview (Sprints 131–135) — COMPLETE
> **Focus:** Professional Threshold — 6 public marketing/legal pages + contact backend
> **Source:** Competitive analysis (6 competitors) + Agent Council consensus (Option B)
> **Strategy:** Shared MarketingNav/Footer, hardcoded legal content in TSX, honest compliance disclosure
> **Design:** All new pages are DARK themed (vault exterior). No dollar amounts on paid tiers.

| Sprint | Feature | Complexity | Agent Lead | Status |
|--------|---------|:---:|:---|:---:|
| 131 | Shared MarketingNav + MarketingFooter + Legal Pages (Privacy, Terms) | 4/10 | FrontendExecutor + FintechDesigner | COMPLETE |
| 132 | Contact Us (Frontend + Backend — honeypot, rate limit, SendGrid) | 4/10 | BackendCritic + FrontendExecutor | COMPLETE |
| 133 | About + Approach Pages (Zero-Storage deep dive) | 4/10 | FintechDesigner | COMPLETE |
| 134 | Pricing + Trust & Security Pages | 4/10 | FintechDesigner | COMPLETE |
| 135 | Polish + Cross-Link Verification + Documentation | 2/10 | QualityGuardian | COMPLETE |

### Phase XV Overview (Sprints 136–141) — COMPLETE
> **Focus:** Code Deduplication — extract shared utilities from 11-tool testing suite
> **Source:** Comprehensive codebase review (~5,800 lines duplicated)
> **Strategy:** Backend helpers → shared types → 4 shared components → structural cleanup
> **Impact:** ~4,750 lines removed (81% deduplication), 5 new shared modules, 100% backward compatible

| Sprint | Feature | Complexity | Status |
|--------|---------|:---:|:---:|
| 136 | Backend Parsing Helpers (`shared/parsing_helpers.py`) | 3/10 | COMPLETE |
| 137 | Frontend Shared Types (`types/testingShared.ts`) | 3/10 | COMPLETE |
| 138 | Shared DataQualityBadge | 3/10 | COMPLETE |
| 139 | Shared TestingScoreCard + TestResultGrid | 5/10 | COMPLETE |
| 140 | Shared FlaggedEntriesTable | 5/10 | COMPLETE |
| 141 | Structural Cleanup | 2/10 | COMPLETE |

### Phase XVI Overview (Sprints 142–147) — COMPLETE
> **Focus:** API Hygiene — semantic token migration + API call consolidation
> **Impact:** 15 direct fetch() calls migrated to apiClient, semantic tokens in 15 files

### Phase XVII Overview (Sprints 151–163) — COMPLETE
> **Focus:** Code Smell Refactoring — 200+ smells, 73 unique patterns identified
> **Source:** Comprehensive code smell audit (~7,500 duplicated lines identified)
> **Strategy:** Backend shared abstractions (P0) → decomposition → frontend decomposition
> **Impact:** 7 backend shared modules + 8 frontend decompositions, 15 new shared files, 2,716 backend tests

| Sprint | Feature | Complexity | Status |
|--------|---------|:---:|:---:|
| 151 | Shared Column Detector (9 engine migrations) | 6/10 | COMPLETE |
| 152 | Shared Data Quality + Test Aggregator (7 migrations) | 5/10 | COMPLETE |
| 153 | Shared Benford Analysis + Z-Score Severity | 4/10 | COMPLETE |
| 154 | audit_engine.py + financial_statement_builder Decomposition | 5/10 | COMPLETE |
| 155 | routes/export.py Decomposition (1,497→32 lines) | 5/10 | COMPLETE |
| 156 | Testing Route Factory (6 route migrations) | 4/10 | COMPLETE |
| 157 | Memo Generator Simplification (7 config-driven) | 4/10 | COMPLETE |
| 158 | Backend Magic Numbers + Naming + Email Template | 3/10 | COMPLETE |
| 159 | trial-balance/page.tsx Decomposition (1,219→215) | 5/10 | COMPLETE |
| 160 | practice/page.tsx + multi-period/page.tsx Decomposition | 5/10 | COMPLETE |
| 161 | Frontend Testing Hook Factory + Centralized Constants | 4/10 | COMPLETE |
| 162 | FinancialStatementsPreview + Shared Badge + Cleanup | 4/10 | COMPLETE |
| 163 | Phase XVII Wrap — Regression + Documentation | 2/10 | COMPLETE |

> **Detailed checklists:** `tasks/todo.md` (Phase XVII section)

### Phase XVIII Overview (Sprints 164–170) — COMPLETE
> **Focus:** Async Architecture Remediation — fix systemic async anti-patterns across all backend routes
> **Source:** Comprehensive 5-agent async audit (2026-02-12)
> **Strategy:** Mechanical `async def` → `def` first (zero-risk), then `asyncio.to_thread()`, then BackgroundTasks, then cleanup
> **Impact:** Event loop unblocked under concurrent load; 100–500ms faster registration/contact; memory leak prevention

| Sprint | Feature | Complexity | Status |
|--------|---------|:---:|:---:|
| 164 | Convert pure-DB routes from `async def` to `def` (58 endpoints) | 3/10 | COMPLETE |
| 165 | Wrap Pandas/engine CPU-bound work in `asyncio.to_thread()` | 5/10 | COMPLETE |
| 166 | Convert 24 export endpoints from `async def` to `def` | 3/10 | COMPLETE |
| 167 | Defer email sending + tool run recording to `BackgroundTasks` | 4/10 | COMPLETE |
| 168 | Replace manual `clear_memory()` with `memory_cleanup()` context manager | 3/10 | COMPLETE |
| 169 | Rate limiting gaps + DI consistency cleanup | 2/10 | COMPLETE |
| 170 | Phase XVIII Wrap — regression + documentation | 2/10 | COMPLETE |

> **Detailed checklists:** `tasks/archive/phase-xviii-details.md`

### Phase XIX Overview (Sprints 171–177) — COMPLETE
> **Focus:** API Contract Hardening — response_model coverage, correct HTTP status codes, consistent error handling
> **Source:** 3-agent audit of 21 route files (~115 endpoints)
> **Strategy:** Shared models first → status codes → per-file response_model → trends fix → path fixes → regression
> **Impact:** 25 endpoints gain response_model, 16 status codes corrected, 3 router issues fixed, trends.py error-in-body eliminated

| Sprint | Feature | Complexity | Status |
|--------|---------|:---:|:---:|
| 171 | Shared Response Models (`shared/response_schemas.py`) + follow_up_items tag fix | 3/10 | COMPLETE |
| 172 | DELETE 204 No Content (7 endpoints) + POST 201 Created (9 endpoints) | 4/10 | COMPLETE |
| 173 | response_model: adjustments.py (9 endpoints) + auth_routes.py (4 endpoints) | 5/10 | COMPLETE |
| 174 | response_model: 10-file batch (settings, diagnostics, users, engagements, bank_rec, twm, je, multi_period, prior_period) | 4/10 | COMPLETE |
| 175 | trends.py architecture fix: error-in-body → HTTPException(422) + response_model | 6/10 | COMPLETE |
| 176 | Router path fixes: `/diagnostics/flux` → `/audit/flux`, lead-sheets tag fix | 5/10 | COMPLETE |
| 177 | audit.py response_model + Phase XIX regression + documentation | 4/10 | COMPLETE |

> **Detailed checklists:** `tasks/todo.md` (Phase XIX section)

### Phase XX Overview (Sprint 178) — COMPLETE
> **Focus:** Rate Limit Gap Closure — missing limits on sensitive endpoints, no global default
> **Impact:** 4 endpoints secured, global 60/min default added

| Sprint | Feature | Complexity | Status |
|--------|---------|:---:|:---:|
| 178 | Rate limit gap closure + global default | 3/10 | COMPLETE |

### Phase XXI Overview (Sprints 180–183) — COMPLETE
> **Focus:** Migration Hygiene — fix broken Alembic migration chain, establish working baseline
> **Impact:** Alembic fully operational for fresh deployments, legacy scripts archived, zero datetime deprecations in project code

| Sprint | Feature | Complexity | Status |
|--------|---------|:---:|:---:|
| 180 | Fix env.py missing models + sync alembic.ini DB URL | 2/10 | COMPLETE |
| 181 | Regenerate Alembic baseline from current schema | 4/10 | COMPLETE |
| 182 | Archive manual migration scripts + update README | 2/10 | COMPLETE |
| 183 | Fix deprecated `datetime.utcnow()` + Phase XXI wrap | 1/10 | COMPLETE |

> **Detailed checklists:** `tasks/todo.md` (Phase XXI section)

### Phase XXII Overview (Sprints 184–190) — COMPLETE
> **Focus:** Pydantic Model Hardening — Field constraints, Enum/Literal migrations, manual validation removal, model decomposition, v2 syntax
> **Source:** Comprehensive Pydantic audit of 21 route files + auth.py
> **Strategy:** Security constraints first (P0) → Enum migration → Field bounds → model decomposition → v2 syntax → field_validators → wrap
> **Impact:** ~100 lines manual validation removed, 13 str→Enum/Literal migrations, 25+ Field constraints added, WorkpaperMetadata base class (10 models), password validation centralized in Pydantic

| Sprint | Feature | Complexity | Status |
|--------|---------|:---:|:---:|
| 184 | P0 Security Constraints — min_length/max_length on 11 auth/client/follow-up fields | 2/10 | COMPLETE |
| 185 | Enum/Literal Migration — 13 fields across 6 files, ~30 lines try/except removed | 4/10 | COMPLETE |
| 186 | Field Constraints — 11 string + 13 numeric + 2 list bounds across 7 files | 3/10 | COMPLETE |
| 187 | Model Decomposition — WorkpaperMetadata base (10 models), DiagnosticSummaryCreate sub-models | 4/10 | COMPLETE |
| 188 | V2 Syntax Migration — 4 ConfigDict conversions + 3 model renames | 2/10 | COMPLETE |
| 189 | Password field_validator + sample_rate ge/le + prior_period date migration | 3/10 | COMPLETE |
| 190 | Phase XXII Wrap — regression, adjustments.py bugfix, documentation | 2/10 | COMPLETE |

> **Detailed checklists:** `tasks/todo.md` (Phase XXII section)

---

## Design Mandate: Oat & Obsidian

**STRICT REQUIREMENT:** All UI development MUST adhere to the Oat & Obsidian brand identity.

### Reference
See `skills/theme-factory/themes/oat-and-obsidian.md` for the complete specification.

### Core Colors (Tailwind Tokens)
| Token | Hex | Usage |
|-------|-----|-------|
| `obsidian` | #212121 | Primary dark, headers, backgrounds |
| `oatmeal` | #EBE9E4 | Light backgrounds, secondary text |
| `clay` | #BC4749 | Expenses, errors, alerts, abnormal balances |
| `sage` | #4A7C59 | Income, success, positive states |

### Typography
| Element | Font |
|---------|------|
| Headers | `font-serif` (Merriweather) |
| Body | `font-sans` (Lato) |
| Financial Data | `font-mono` (JetBrains Mono) |

### Enforcement Rules
1. **NO** generic Tailwind colors (`slate-*`, `blue-*`, `green-*`, `red-*`)
2. **USE** theme tokens: `obsidian-*`, `oatmeal-*`, `clay-*`, `sage-*`
3. **SUCCESS** states use `sage-*` (not green-*)
4. **ERROR/EXPENSE** states use `clay-*` (not red-*)
5. **Headers** must use `font-serif` class
6. **Financial numbers** must use `font-mono` class

### Audit Penalty
UI changes that deviate from this palette without CEO approval will result in audit score deductions.
