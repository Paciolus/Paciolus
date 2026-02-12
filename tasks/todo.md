# Paciolus Development Roadmap

> **Protocol:** Every directive MUST begin with a Plan Update to this file and end with a Lesson Learned in `lessons.md`.

---

## Completed Phases

### Phase I (Sprints 1-24) — COMPLETE
> Core platform: Zero-Storage TB analysis, streaming, classification, brand, risk dashboard, multi-sheet Excel, PDF/Excel export, JWT auth, activity logging, client management, practice settings, deployment prep.

### Phase II (Sprints 25-40) — COMPLETE
> Test suite, 9 ratios (Current/Quick/D2E/Gross/Net/Operating/ROA/ROE/DSO), IFRS/GAAP docs, trend analysis + viz, industry ratios (6 industries), rolling windows, batch upload, benchmark RFC.

### Phase III (Sprints 41-47) — COMPLETE
> Anomaly detection (suspense, concentration, rounding, balance sheet), benchmark engine + API + UI + integration.

### Phase IV (Sprints 48-55) — COMPLETE
> User profile, security hardening, lead sheets (A-Z), prior period comparison, adjusting entries, DSO ratio, CSV export, frontend test foundation.

### Phase V (Sprints 56-60) — COMPLETE
> UX polish, email verification (backend + frontend), endpoint protection, homepage demo mode. **Tests: 625 backend + 26 frontend.**

### Phase VI (Sprints 61-70) — COMPLETE
> Multi-Period TB Comparison (Tool 2), Journal Entry Testing (Tool 3, 18-test battery + stratified sampling), platform rebrand to suite, diagnostic zone protection. Tests added: 268 JE + multi-period.

### Phase VII (Sprints 71-80) — COMPLETE
> Financial Statement Builder (Tool 1 enhancement), AP Payment Testing (Tool 4, 13-test battery), Bank Reconciliation (Tool 5). Tests added: 165 AP + 55 bank rec.

### Phase VIII (Sprints 81-89) — COMPLETE
> Cash Flow Statement (indirect method, ASC 230/IAS 7), Payroll & Employee Testing (Tool 6, 11-test battery), code quality sprints (81-82). Tests added: 139 payroll.

### Phase IX (Sprints 90-96) — COMPLETE
> Shared testing utilities extraction (enums/memo/round-amounts), Three-Way Match Validator (Tool 7), Classification Validator (TB Enhancement). Tests added: 114 three-way match + 52 classification.

### Phase X (Sprints 96.5-102) — COMPLETE
> The Engagement Layer: engagement model + materiality cascade, follow-up items tracker (narratives-only), workpaper index, anomaly summary report (PDF), diagnostic package export (ZIP with SHA-256), engagement workspace frontend. 8 AccountingExpertAuditor guardrails satisfied. Tests added: 158 engagement/follow-up/workpaper/export.

### Phase XI (Sprints 103-110) — COMPLETE
> Tool-Engagement Integration (frontend auto-link via EngagementProvider), Revenue Testing (Tool 8, 12-test battery, ISA 240), AR Aging Analysis (Tool 9, 11-test battery, dual-input TB + sub-ledger). Tests added: 110 revenue + 28 memo + 131 AR + 34 memo.

### Phase XII (Sprints 111-120) — COMPLETE
> Nav overflow infrastructure, FileDropZone extraction, Finding Comments + Assignments (collaboration), Fixed Asset Testing (Tool 10, 9-test battery, IAS 16), Inventory Testing (Tool 11, 9-test battery, IAS 2). Tests added: 41 comments + 15 assignments + 133 FA + 38 FA memo + 136 inventory + 38 inv memo.

### Phase XIII (Sprints 121-130) — COMPLETE
> Platform polish + dual-theme "The Vault Interior" architecture. Security hardening (26 rate-limited exports, upload validation, error sanitization). CSS custom property + Tailwind semantic token infrastructure. Light theme migration (all tool + authenticated pages). VaultTransition login animation. Export consolidation + Bank Rec/Multi-Period memos (11/11 tools with PDF memos). WCAG AAA accessibility + 60 frontend test backfill. **Version: 1.2.0. Tests: 2,593 backend + 128 frontend.**

### Phase XIV (Sprints 131-135) — COMPLETE
> Professional Threshold: 6 public marketing/legal pages (Privacy, Terms, Contact, About, Approach, Pricing, Trust). Shared MarketingNav/Footer. Contact backend with honeypot + rate limiting. All pages dark-themed (vault exterior).

### Phase XV (Sprints 136-141) — COMPLETE
> Code Deduplication: shared parsing helpers, shared types, 4 shared testing components (DataQualityBadge, ScoreCard, TestResultGrid, FlaggedTable), context consolidation. ~4,750 lines removed (81% deduplication), 100% backward compatible.

### Phase XVI (Sprints 142-150) — COMPLETE
> API Hygiene: semantic token migration, API call consolidation (15 direct fetch → apiClient), N+1 query fix, Docker hardening (.dockerignore, multi-stage fix, SQLite path).

### Phase XVII (Sprints 151-163) — COMPLETE
> Code Smell Refactoring: 7 backend shared modules (column_detector, data_quality, test_aggregator, benford, export_schemas, testing_route, memo_template), 8 frontend decompositions (TB page 1,219→215, export 1,497→32, practice 1,203→665, multi-period 897→470, FinancialStatements 772→333), hook factory, centralized constants. 15 new shared files, 9,298 added / 8,849 removed. **Tests: 2,716 backend + 128 frontend.**

**Test Coverage at Phase XVIII End:** 2,716 backend tests + 128 frontend tests | Version 1.2.0

> **Detailed checklists:** `tasks/archive/phases-vi-ix-details.md` | `tasks/archive/phases-x-xii-details.md` | `tasks/archive/phases-xiii-xvii-details.md`

---

## Post-Sprint Checklist

**MANDATORY:** Complete these steps after EVERY sprint before declaring it done.

### Verification
- [ ] Run `npm run build` in frontend directory (must pass)
- [ ] Run `pytest` in backend directory (if tests modified)
- [ ] Verify Zero-Storage compliance for new data handling

### Documentation
- [ ] Update sprint status to COMPLETE in todo.md
- [ ] Add Review section with Files Created/Modified
- [ ] Add lessons to lessons.md if corrections occurred

### Git Commit
- [ ] Stage relevant files: `git add <specific-files>`
- [ ] Commit with sprint reference: `git commit -m "Sprint X: Brief Description"`
- [ ] Verify commit: `git log -1`

---

### Phase XVIII (Sprints 164-170) — COMPLETE
> Async Architecture Remediation: `async def` → `def` for 82+ pure-DB/export endpoints, `asyncio.to_thread()` for CPU-bound Pandas work, `BackgroundTasks` for email/tool-run recording, `memory_cleanup()` context manager, rate limit gap closure. Zero behavioral regressions. **Tests: 2,716 backend + 128 frontend.**

> **Detailed checklists:** `tasks/archive/phase-xviii-details.md`

---

## Not Currently Pursuing

> **Reviewed:** Agent Council + Future State Consultant (2026-02-09)
> **Criteria:** Deprioritized due to low leverage, niche markets, regulatory burden, or off-brand positioning.

| Feature | Status | Reason |
|---------|--------|--------|
| Loan Amortization Generator | Not pursuing | Commodity calculator; off-brand |
| Depreciation Calculator | Not pursuing | MACRS table maintenance; better served by Excel |
| 1099 Preparation Helper | Not pursuing | US-only, seasonal, annual IRS rule changes |
| Book-to-Tax Adjustment Calculator | Not pursuing | Tax preparer persona; regulatory complexity |
| W-2/W-3 Reconciliation Tool | Not pursuing | Payroll niche; seasonal; different persona |
| Segregation of Duties Checker | Not pursuing | IT audit persona; different user base |
| Expense Allocation Testing | DROPPED | 2/5 market demand; niche applicability |
| Cross-Tool Composite Risk Scoring | REJECTED | ISA 315 violation — requires auditor risk inputs |
| Management Letter Generator | REJECTED | ISA 265 violation — deficiency classification is auditor judgment |
| Heat Map / Risk Visualization | REJECTED | Depends on composite scoring (rejected) |

### Deferred to Phase XIX+

| Feature | Reason | Earliest Phase |
|---------|--------|----------------|
| Budget Variance Deep-Dive | Multi-Period page tab refactor prerequisite | Phase XIX |
| Accrual Reasonableness Testing (Tool 12) | Dual-input fuzzy matching complexity | Phase XIX |
| Intercompany Transaction Testing (Tool 13) | Cycle-finding algorithm; narrow applicability | Phase XIX |
| Multi-Currency Conversion | Cross-cutting 11+ engine changes; needs dedicated RFC | Phase XIX |
| Engagement Templates | Premature until engagement workflow has real user feedback | Phase XIX |
| Lease Accounting (ASC 842) | 8/10 complexity; high value but needs research sprint | Phase XIX |
| Cash Flow Projector | Requires AR/AP aging + payment history | Phase XIX |
| Cash Flow — Direct Method | Requires AP/payroll detail integration | Phase XIX |
| Related Party Transaction Screening | Needs external data APIs; 8/10 complexity | Phase XIX+ |
| Finding Attachments | File storage contradicts Zero-Storage philosophy | Phase XIX+ |
| Real-Time Collaboration | WebSocket infrastructure; 9/10 complexity | Phase XIX+ |
| Custom Report Builder | Rich text editor + templating engine | Phase XIX+ |
| Historical Engagement Comparison | Requires persistent aggregated data | Phase XIX+ |
| User-toggleable dark/light mode | CEO vision is route-based, not preference | Phase XIX (if demand) |
| Homepage redesign | Homepage stays dark; separate initiative | Phase XIX |
| Mobile hamburger menu for ToolNav | Current overflow dropdown sufficient | Phase XIX |
| Print stylesheet | Out of scope for completed phases | Phase XIX |
| Component library / Storybook | Lower priority than shipping features | Phase XIX |
| Onboarding flow | UX research needed | Phase XIX |
| Batch export all memos | ZIP already bundles anomaly summary | Phase XIX |
| Async SQLAlchemy migration | Full AsyncSession + aiosqlite migration if threadpool proves insufficient | Phase XIX |
| Async email client | Replace sync SendGrid SDK with httpx async or aiosmtplib | Phase XIX |
