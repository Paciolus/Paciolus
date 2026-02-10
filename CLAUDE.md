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
**Phase:** Phase XIII — Platform Polish + The Vault Interior (Sprints 121–130, IN PROGRESS)
**Model:** Agent Council Sprint Delivery (6-agent consensus prioritization)
**Health:** PRODUCTION READY
**Version:** 1.1.0
**Test Coverage:** 2,549 backend tests + 76 frontend tests
**Next Sprint:** 124 — Theme: Shared Components

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
- PDF/Excel/CSV export with workpaper signoff + JE/AP/Payroll/TWM/Revenue/AR Aging/Fixed Asset/Inventory Testing Memos (PCAOB AS 1215/2401/2501, ISA 240/500/501/505/540)
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

### Phase XIII Overview (Sprints 121–130) — IN PROGRESS
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
| 124 | Theme: Shared Components | 4/10 | FrontendExecutor + FintechDesigner | PENDING |
| 125 | Theme: Tool Pages Batch 1 (6 tools) | 5/10 | FrontendExecutor | PENDING |
| 126 | Theme: Tool Pages Batch 2 + Authenticated Pages | 5/10 | FrontendExecutor | PENDING |
| 127 | Vault Transition + Visual Polish | 4/10 | FintechDesigner + FrontendExecutor | PENDING |
| 128 | Export Consolidation + Missing Memos | 5/10 | BackendCritic + AccountingExpertAuditor | PENDING |
| 129 | Accessibility + Frontend Test Backfill | 5/10 | QualityGuardian + FrontendExecutor | PENDING |
| 130 | Phase XIII Wrap — Regression + v1.2.0 | 2/10 | QualityGuardian | PENDING |

> **Detailed checklists for Phases X-XII:** `tasks/archive/phases-x-xii-details.md`

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
