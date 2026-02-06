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

**Project:** Paciolus — Trial Balance Diagnostic Intelligence Platform for Financial Professionals
**Phase:** Phase VI Starting — Sprint 61 Next
**Model:** Agent Council Sprint Delivery (6-agent consensus prioritization)
**Health:** PRODUCTION READY
**Version:** 0.47.0
**Test Coverage:** 1022 backend tests + 26 frontend tests (268 JE testing)
**Next Priority:** Sprint 70 (Diagnostic Zone Protection + Phase VI Wrap)

### Completed Phases (details in `tasks/todo.md`)
- **Phase I (Sprints 1-24):** Core platform — Zero-Storage TB analysis, streaming, auth, PDF/Excel export, client management, practice settings, deployment
- **Phase II (Sprints 25-40):** Test suite, 9 ratios, IFRS/GAAP, trend analysis, industry ratios, rolling windows, batch upload, benchmark RFC
- **Phase III (Sprints 41-47):** Anomaly detection (suspense, concentration, rounding, balance sheet), benchmark engine + API + UI
- **Phase IV (Sprints 48-55):** User profile, security hardening, lead sheets, prior period comparison, adjusting entries, DSO, CSV export, frontend tests
- **Phase V (Sprints 56-60):** UX polish, email verification (backend + frontend), endpoint protection, homepage demo mode

### Key Capabilities
- 9 core ratios + 8 industry ratios across 6 benchmark industries
- A-Z lead sheet mapping, prior period comparison, adjusting entries
- PDF/Excel/CSV export with workpaper signoff
- JWT auth, email verification, CSRF, account lockout
- Free/Professional/Enterprise user tiers

### Phase VI Overview (Sprints 61-70) — CURRENT
> **Focus:** Multi-Period TB Comparison (Tool 2) + Journal Entry Testing (Tool 3) + Platform Rebrand
> **CEO Directive:** Three separate tools, platform-level homepage marketing
> **Reviewed by:** Accounting Expert Auditor + Agent Council (2026-02-06) — resequenced per professional adoption priorities

| Sprint | Feature | Complexity | Agent Lead | Status |
|--------|---------|:---:|:---|:---:|
| 61 | Housekeeping + Multi-Period Foundation | 3/10 | BackendCritic | COMPLETE |
| 62 | Route Scaffolding + Multi-Period API/Frontend | 6/10 | FrontendExecutor + BackendCritic | ✅ |
| 63 | Multi-Period Polish + Three-Way Comparison | 4/10 | BackendCritic + FrontendExecutor | ✅ |
| 64 | JE Testing — Backend Foundation + Config + Dual-Date | 5/10 | BackendCritic | ✅ |
| 65 | JE Testing — Statistical Tests + Benford Pre-Checks | 7/10 | BackendCritic + QualityGuardian | ✅ |
| 66 | JE Testing — Frontend MVP + Platform Rebrand | 7/10 | FrontendExecutor + FintechDesigner | ✅ |
| 67 | JE Testing — Results Table + Export + Testing Memo | 5/10 | FrontendExecutor + BackendCritic | ✅ |
| 68 | JE Testing — Tier 2 Tests + Threshold Config UI | 6/10 | BackendCritic + FrontendExecutor | ✅ |
| 69 | JE Testing — Tier 3 + Sampling + Fraud Indicators | 7/10 | BackendCritic + QualityGuardian | ✅ |
| 70 | Diagnostic Zone Protection + Wrap | 2/10 | QualityGuardian | PLANNED |

### Unresolved Tensions
| Tension | Resolution | Status |
|---------|------------|--------|
| Diagnostic zone protection disabled | Sprint 70 | Planned |
| Contra-Account Validator | Deferred | Requires industry-specific rules |

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
