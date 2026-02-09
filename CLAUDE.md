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
**Phase:** Phase XI — Tool-Engagement Integration + Revenue Testing + AR Aging (Sprints 103–110, IN PROGRESS)
**Model:** Agent Council Sprint Delivery (6-agent consensus prioritization)
**Health:** PRODUCTION READY
**Version:** 0.95.0
**Test Coverage:** 1,949 backend tests + 76 frontend tests (268 JE testing, 165 AP testing, 55 bank rec, 139 payroll testing, 114 three-way match, 52 classification validator, 23 DB fixtures, 16 export helpers, 54 engagement, 59 follow-up items, 17 workpaper index, 28 anomaly summary/export, 110 revenue testing, 28 revenue testing memo)
**Next Sprint:** 106 — Revenue Testing Frontend + 8-Tool Nav

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
- Classification Validator: 6 structural COA checks (duplicates, orphans, unclassified, gaps, naming, sign anomalies) integrated into TB Diagnostics
- PDF/Excel/CSV export with workpaper signoff + JE/AP/Payroll/TWM/Revenue Testing Memos (PCAOB AS 1215/2401, ISA 240/505/500)
- JWT auth, email verification, CSRF, account lockout, diagnostic zone protection
- Free/Professional/Enterprise user tiers
- Engagement Layer: Diagnostic Workspace with materiality cascade, follow-up items tracker, workpaper index, anomaly summary report, diagnostic package ZIP export
- Platform homepage with 7-tool suite + workspace marketing

### Unresolved Tensions
| Tension | Resolution | Status |
|---------|------------|--------|
| Multi-Currency Conversion | Detection shipped (Sprint 64); conversion logic deferred | Beyond Phase VII |
| Composite Risk Scoring | Rejected by AccountingExpertAuditor (requires ISA 315 inputs) | Deferred to Phase XI with auditor-input workflow |
| Management Letter Generator | Rejected permanently (ISA 265 boundary — deficiency classification is auditor judgment) | REJECTED |

### Phase X Overview (Sprints 96.5–102) — COMPLETE
> **Focus:** The Engagement Layer — Test Infrastructure + Engagement Model + Materiality Cascade + Follow-Up Items + Workpaper Index + Anomaly Summary Report
> **Source:** Agent Council unanimous consensus on Path C (Hybrid) — 2026-02-08
> **Strategy:** Engagement workflow WITHOUT engagement assurance — "engagement spine without a judgment brain"
> **Guardrails:** 8 non-negotiable conditions from AccountingExpertAuditor (terminology, schema, disclaimers, review gates)

| Sprint | Feature | Complexity | Agent Lead | Status |
|--------|---------|:---:|:---|:---:|
| 96.5 | Test Infrastructure — DB Fixtures + Migration + Frontend Backfill | 2/10 | QualityGuardian | COMPLETE |
| 97 | Engagement Model + Materiality Cascade | 6/10 | BackendCritic + AccountingExpertAuditor | COMPLETE |
| 98 | Engagement Workspace (Frontend) | 5/10 | FrontendExecutor + FintechDesigner | COMPLETE |
| 99 | Follow-Up Items Tracker (Backend) | 5/10 | BackendCritic + QualityGuardian | COMPLETE |
| 100 | Follow-Up Items UI + Workpaper Index | 6/10 | FrontendExecutor + BackendCritic | COMPLETE |
| 101 | Engagement ZIP Export + Anomaly Summary Report | 5/10 | BackendCritic + AccountingExpertAuditor | COMPLETE |
| 102 | Phase X Wrap — Regression + TOS + CI Checks | 2/10 | QualityGuardian + FintechDesigner | COMPLETE |

### Phase XI Overview (Sprints 103–110) — IN PROGRESS
> **Focus:** Complete engagement workflow loop + expand to 9-tool suite (Revenue Testing + AR Aging)
> **Source:** Agent Council Path B deliberation — 2026-02-08
> **Strategy:** Integration first (make workspace functional), then new tools that auto-link from day one
> **Target Version:** 1.0.0

| Sprint | Feature | Complexity | Agent Lead | Status |
|--------|---------|:---:|:---|:---:|
| 103 | Tool-Engagement Integration (Frontend) | 3/10 | FrontendExecutor | COMPLETE |
| 104 | Revenue Testing — Engine + Routes | 5/10 | BackendCritic | COMPLETE |
| 105 | Revenue Testing — Memo + Export | 3/10 | BackendCritic + AccountingExpertAuditor | COMPLETE |
| 106 | Revenue Testing — Frontend + 8-Tool Nav | 5/10 | FrontendExecutor + FintechDesigner | PENDING |
| 107 | AR Aging — Engine + Routes | 5/10 | BackendCritic | PENDING |
| 108 | AR Aging — Memo + Export | 3/10 | BackendCritic + AccountingExpertAuditor | PENDING |
| 109 | AR Aging — Frontend + 9-Tool Nav | 5/10 | FrontendExecutor + FintechDesigner | PENDING |
| 110 | Phase XI Wrap — Regression + v1.0.0 | 2/10 | QualityGuardian | PENDING |

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
