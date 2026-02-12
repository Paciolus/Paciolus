# Backlog & Decisions

> **Archived:** 2026-02-12 — Moved from todo.md to reduce context bloat.
> **Review cycle:** Revisit at Phase XIX planning.

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

---

## Deferred to Phase XIX+

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
