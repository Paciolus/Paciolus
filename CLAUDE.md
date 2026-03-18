> **New sessions:** Start with `AGENTS.md`, not this file. This file contains the full operator protocol and is reference material, not startup orientation.

# Project Protocol: The Council

## Document Authority Hierarchy

When any two sources conflict, the higher-ranked source wins. Prose docs must be updated to match enforcement, not the reverse.

1. **Executable enforcement** — `ci.yml`, Husky hooks (`frontend/.husky/`). These are mechanically enforced and final.
2. **`tasks/todo.md`** — Live sprint state, lifecycle, archival thresholds.
3. **`CLAUDE.md`** — Operator conventions, process defaults, design mandate.
4. **Supporting docs** — `sprint-close-checklist.md`, `CONTRIBUTING.md`, `SECURE_SDL_CHANGE_MANAGEMENT.md`, runbooks. Informational; must not contradict items 1–3.

---

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
- [ ] If `## Active Phase` has 5+ completed sprints, archive them before starting new work
- [ ] Add/update checklist items for the current directive
- [ ] Mark the directive as "In Progress"
- [ ] Identify which agents are involved

### 1b. Sprint vs. Hotfix Classification
- **Sprint:** New features, architectural changes, report enrichments, bug fix batches, test additions
- **Hotfix:** Copy corrections, test count updates, typo fixes, dependency bumps with no code changes
- Hotfixes: add one-line entry to `## Hotfixes` in `tasks/todo.md`, commit with `fix:` prefix. No sprint number needed.

### 2. Implementation
- Follow the Conflict Loop
- Track progress by checking off items in `tasks/todo.md`
- Document blockers in the Review section

### 3. Verification (BEFORE marking complete)
Before declaring a directive complete:
- [ ] Run `npm run build` in frontend (must pass with no errors)
- [ ] Run `npm test` in frontend (must pass with no errors)
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
- [ ] Update sprint status to COMPLETE in `tasks/todo.md`
- [ ] Record commit SHA in sprint Review section
- [ ] Stage relevant files (avoid `git add -A` to prevent accidental inclusions)
- [ ] **Stage `tasks/todo.md`** — the commit-msg hook will reject `Sprint N:` commits without it
- [ ] Create atomic commit with descriptive message: `Sprint X: [Brief Description]`
- [ ] Commit message should reference the sprint number and key changes

**ENFORCEMENT:** A `commit-msg` hook (`frontend/.husky/commit-msg`) enforces two gates on `Sprint N:` commits:
1. **Todo gate:** Rejects unless `tasks/todo.md` is staged.
2. **Archival gate:** Rejects if Active Phase has 5+ completed sprints. Run `sh scripts/archive_sprints.sh` to clear.

Both are mechanically enforced — not discipline-dependent. Hotfix commits (`fix:` prefix) are exempt.

**FAILURE TO FOLLOW THIS PROTOCOL WILL RESULT IN AUDIT SCORE PENALTIES.**

---

## Current Project State

**Project:** Paciolus — Professional Audit Intelligence Platform for Financial Professionals
**Model:** Agent Council Sprint Delivery (6-agent consensus prioritization)
**Health:** PRODUCTION READY
**Version:** 2.1.0
**Live Sprint State:** See `tasks/todo.md` `## Active Phase` (authoritative — do not hardcode sprint numbers here)

### Completed Phases

> **Full details:** `tasks/archive/` (per-phase files) and `tasks/todo.md` (active phase)

| Sprints | Era | Highlights |
|---------|-----|------------|
| 1–55 (I–IV) | Core Platform | Zero-Storage TB analysis, streaming, auth, PDF/Excel export, 9 ratios, anomaly detection, lead sheets, adjusting entries |
| 56–96 (V–IX) | Tool Expansion | Email verification, Multi-Period TB, Journal Entry Testing (19 tests), Financial Statements, AP Testing (13 tests), Cash Flow, Payroll Testing (11 tests), Three-Way Match, Classification Validator — **7 tools** |
| 96.5–130 (X–XII) | Engagement & Growth | Engagement layer + materiality cascade, Revenue Testing (16 tests), AR Aging (11 tests), Fixed Assets (9 tests), Inventory (9 tests) — **11 tools, v1.1.0** |
| 121–147 (XIII–XVI) | Polish & Hardening | Dual-theme "The Vault", WCAG AAA, 11 PDF memos, 24 export endpoints, marketing/legal pages, code dedup (~4,750 lines removed), API hygiene — **v1.2.0** |
| 151–209 (XVII–XXVII) | Architecture & Security | 7 backend shared modules, async remediation, API contract hardening, rate limits, Pydantic hardening, Pandas precision, upload/export security, JWT hardening, email verification hardening, Next.js App Router |
| 210–254 (XXVIII–XXXIII) | Production Readiness | CI pipeline, structured logging, type safety, frontend test expansion (389→520 tests), backend test hardening (3,050 tests), error handling, Docker tuning |
| 255–278 (XXXIV–XXXVII) | v1.3–v1.5 | Multi-Currency Conversion, in-memory state fix, Statistical Sampling (Tool 12, ISA 530), deployment hardening, Sentry APM — **12 tools, v1.5.0** |
| 279–312 (XXXVIII–XLI) | Diagnostic Intelligence | Security/accessibility hardening, TB Population Profile, Convergence Index, Expense Category, Accrual Completeness, Cash Conversion Cycle, cross-tool workflow integration — **v1.8.0** |
| 313–398 (XLII–LV) | Design & UX | Oat & Obsidian token migration, homepage "Ferrari" transformation, tool pages refinement, IntelligenceCanvas, Workspace Shell "Audit OS", Proof Architecture, typography system, command palette — **v1.9.0–v1.9.5** |
| 340–361 (XLV–XLIX) | Data Integrity | Monetary precision (Float→Numeric), soft-delete immutability, ASC 606/IFRS 15 contract testing, adjustment approval gating, diagnostic feature expansion (lease/cutoff/going concern) — **v2.0.0** |
| 362–381 (L–LI) | Billing & Compliance | Stripe integration, tiered billing (Solo/Team/Org), entitlement enforcement, accounting-control policy gate (5 AST invariant checkers) — **v2.1.0** |
| 382–420 | Refinement | IntelligenceCanvas, state-linked motion, premium moments, lint remediation (687→0 issues), accessibility (51→0 errors), Husky pre-commit hooks |
| 421–438 (LVIII) | File Formats | TSV/TXT/OFX/QBO/IIF/PDF/ODS parsers (10 supported types), Prometheus metrics, tier-gated format access |
| 439–448 (LIX–LXIII) | Pricing & Coverage | Hybrid pricing overhaul, billing analytics, React 19, Python 3.12, pandas 3.0 eval, entitlement wiring, export test coverage (17%→90%) |
| 449–476 (LXIV–LXIX) | Security, SOC 2, Pricing v3 | HttpOnly cookies, CSP nonce, CSRF upgrade, SOC 2 readiness (42 criteria), mypy annotations, Pricing Restructure v3 (Free/Solo/Professional/Enterprise — all paid = all tools), org entities, export sharing, admin dashboard, bulk upload, comprehensive security audit (14 fixes) |
| 477–487 | Report Engine & UX Polish | Copy consistency, Digital Excellence Council audits, pricing page redesign, report engine content audit, TB Diagnostic enrichment |
| 478, 488–502 | Security Hardening & Quality | Deprecated alias migration, report fixes, security audit quadrilogy (35 fixes), 61 injection tests, CI hardening, formula consistency, Digital Excellence Council remediation (42 findings), payroll report enrichment, toolbar refactor, revenue report enrichment (3 bug fixes, 4 improvements), fixed asset report enrichment (4 bug fixes, 4 improvements, FA-10 lease indicator) — **Tests: 5,808 + 1,345** |
| 499–515 | Report Enrichment | Toolbar three-zone refactor, 16 report enrichments (Payroll through Anomaly Summary: bug fixes, new sections, risk scoring, suggested procedures, authoritative reference corrections), test suite fixes — **Tests: 6,188 + 1,345** |

### Compliance Documentation
Located in `docs/04-compliance/`:
- Security Policy v2.6, Privacy Policy v2.1, Terms of Service v2.0
- Zero-Storage Architecture v2.1, DPA v1.0, Subprocessor List v1.0
- IRP v1.0, BCP/DR v1.2, Access Control v1.2, Secure SDL v1.1
- VDP v1.1, Audit Logging v1.1

### Key Capabilities
- 17 core ratios + 8 industry ratios across 6 benchmark industries + DuPont decomposition
- 12 testing tools: JE (19 tests), AP (13), Payroll (11), Revenue (16, ASC 606/IFRS 15), AR Aging (11), Fixed Assets (9), Inventory (9), Bank Rec, Three-Way Match, Multi-Period TB, Statistical Sampling (ISA 530), Multi-Currency
- TB Diagnostics: classification validator, lead sheets (A-Z), adjusting entries (approval-gated), lease/cutoff/going concern indicators
- Financial Statements: Balance Sheet + Income Statement + Cash Flow (indirect, ASC 230/IAS 7)
- 21 PDF memos (PCAOB AS 1215/2401/2501, ISA 240/500/501/505/520/530/540) + Excel/CSV export
- JWT auth (HttpOnly cookie refresh, in-memory access tokens), CSRF, account lockout
- Free/Solo/Professional/Enterprise tiers: all paid tiers get all 12 tools. Solo ($100/$1,000), Professional ($500/$5,000, org features), Enterprise ($1,000/$10,000, PDF branding, bulk upload)
- Engagement Layer: materiality cascade, follow-up tracker, workpaper index, diagnostic package ZIP, completion gate
- Universal command palette (Cmd+K), Workspace Shell ("Audit OS"), Proof Architecture
- 10 file formats: XLSX, XLS, CSV, TSV, TXT, OFX, QBO, IIF, PDF, ODS

### Unresolved Tensions
| Tension | Resolution | Status |
|---------|------------|--------|
| Composite Risk Scoring | Rejected by AccountingExpertAuditor (requires ISA 315 inputs) | DEFERRED |
| Management Letter Generator | Rejected permanently (ISA 265 boundary — deficiency classification is auditor judgment) | REJECTED |

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
