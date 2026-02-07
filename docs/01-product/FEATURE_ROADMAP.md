# Feature Roadmap

**Document Classification:** Internal (Product, Engineering)
**Version:** 2.0
**Last Updated:** February 6, 2026
**Owner:** Product Manager
**Review Cycle:** Monthly

---

## Overview

This roadmap outlines Paciolus's feature development history and future plans. Features are prioritized using the RICE framework (Reach, Impact, Confidence, Effort) and aligned with our product vision.

**Current Version:** 0.70.0 (February 2026)
**Current Phase:** Phase VII Complete (80 sprints delivered)
**Next Milestone:** Phase VIII Planning

---

## Completed: Phase I-V (Sprints 1-60) — Foundation & Core Platform

**Theme:** Zero-Storage diagnostics, authentication, portfolio, exports, anomaly detection, ratios, benchmarks

**Delivered:**
- Zero-Storage trial balance processing with streaming for large files
- Automated account classification (80+ keywords, weighted heuristic scoring)
- Anomaly detection: abnormal balances, suspense accounts, concentration risk, rounding
- 9 core financial ratios + 8 industry-specific ratios across 6 benchmark industries
- Multi-sheet Excel support with workbook inspection and consolidation
- PDF export (Renaissance Ledger aesthetic) + Excel workpaper (4-tab structure)
- JWT authentication with email verification, CSRF protection, account lockout
- Client portfolio management with industry classification
- Activity history (GDPR-compliant metadata only)
- Practice settings with materiality formulas (fixed, % of revenue/assets/equity)
- Real-time sensitivity tuning toolbar
- A-Z lead sheet mapping
- Prior period comparison with movement classification
- Adjusting entries with multi-line journal entry validation
- CSV export for flagged items
- User profile with Free/Professional/Enterprise tiers
- Platform homepage with demo mode
- 26 frontend tests + comprehensive backend test suite

---

## Completed: Phase VI (Sprints 61-70) — Multi-Period + JE Testing

**Theme:** Multi-Period TB Comparison (Tool 2) + Journal Entry Testing (Tool 3) + Platform Rebrand

**Delivered:**

### Tool 2: Multi-Period TB Comparison
- Two-way comparison with 6 movement types (NEW, CLOSED, SIGN_CHANGE, INCREASE, DECREASE, UNCHANGED)
- Three-way comparison with budget variance analysis
- Account name normalization for fuzzy matching
- Significance tiers (MATERIAL, SIGNIFICANT, MINOR)
- Lead sheet grouping for movement results
- Dual-file upload UI with period labeling

### Tool 3: Journal Entry Testing
- 18 automated tests across 3 tiers:
  - **Tier 1 (Structural):** Unbalanced entries, missing fields, duplicate entries, backdated entries, unusual amounts
  - **Tier 2 (Statistical):** Benford's Law analysis, round amount concentration, weekend/holiday posting, unusual users, description anomalies
  - **Tier 3 (Advanced):** Split transaction patterns, sequential anomalies, cross-period entries, related party indicators, fraud keyword detection
- Benford's Law with multi-order-of-magnitude prechecks
- Stratified sampling engine with CSPRNG (PCAOB AS 2315 compliant)
- JE Testing Memo PDF export (PCAOB AS 1215 / ISA 530 references)
- Composite risk scoring with configurable thresholds
- Threshold configuration UI with Conservative/Standard/Permissive presets

### Platform Rebrand
- Standalone tool routes (`/tools/trial-balance`, `/tools/multi-period`, `/tools/journal-entry-testing`)
- Platform homepage with tool showcase cards
- Diagnostic zone protection (3-state: guest, unverified, verified)

---

## Completed: Phase VII (Sprints 71-80) — Financial Statements + AP Testing + Bank Rec

**Theme:** Financial Statements (Tool 1 enhancement) + AP Payment Testing (Tool 4) + Bank Reconciliation (Tool 5)

**Delivered:**

### Financial Statements (Tool 1 Enhancement)
- Balance Sheet + Income Statement generated from lead sheet groupings (A-Z categories)
- Sign conventions for assets, liabilities, equity, revenue, COGS, operating expenses
- Balance verification seal (BALANCED / OUT OF BALANCE)
- PDF export with leader dots, subtotals, double-rule totals
- Excel export with dual worksheets and lead sheet references

### Tool 4: AP Payment Testing
- 13 automated tests across 3 tiers:
  - **Tier 1 (Structural):** Exact duplicate payments, missing critical fields, check number gaps, round dollar amounts, payment before invoice
  - **Tier 2 (Statistical):** Fuzzy duplicate payments, invoice number reuse, unusual payment amounts (z-score), weekend payments, high-frequency vendors
  - **Tier 3 (Fraud Indicators):** Vendor name variations (SequenceMatcher), just-below-threshold amounts, suspicious descriptions (16 AP-specific keywords)
- AP column detection with weighted regex patterns (11 column types)
- Composite scoring with configurable thresholds
- AP Testing Memo PDF export (ISA 240 / ISA 500 / PCAOB AS 2401)
- CSV export for flagged payments
- Threshold configuration with Conservative/Standard/Permissive/Custom presets

### Tool 5: Bank Statement Reconciliation
- Dual-file upload: bank statement + GL cash detail
- Automated column detection for bank transactions
- V1 exact matching engine (greedy, largest-first)
- Amount tolerance and date tolerance support
- Auto-categorization: Outstanding Check/Deposit, Deposit in Transit, Unrecorded Check
- Reconciliation bridge (standard bank rec workpaper format)
- CSV export with 4 sections (matched, bank-only, ledger-only, summary)
- Match rate percentage and reconciling difference surfacing

### Navigation Standardization (Sprint 80)
- 5-tool cross-navigation on all tool pages
- Consistent active/inactive link styling
- Homepage updated to showcase all 5 tools
- Version bumped to 0.70.0

**Phase VII Metrics:**
- ~248 new backend tests (1,022 → 1,270 total)
- 22 frontend routes, 0 build errors
- API router decomposition: main.py 4,690 → 63 lines across 17 router modules

---

## Planned: Phase VIII — Evaluation Stage

**Theme:** Expand tool suite based on user adoption data

**Shortlisted Candidates (Agent Council evaluation):**

| Feature | Reuse Factor | Complexity | Council Interest |
|---------|:---:|:---:|:---:|
| Ghost Employee Detector | 70% (JE Testing clone) | 4/10 | High |
| Expense Classification Validator | 60% (classification engine) | 5/10 | Medium |
| Cash Flow Statement (Indirect) | Extends Financial Statements | 6/10 | Medium |
| Three-Way Match Validator | New paradigm (3 parsers) | 7/10 | Medium |
| Intercompany Elimination Checker | New paradigm (N-file) | 7/10 | Low |

**Selection Criteria:** Value x Leverage — prioritize features that reuse existing engines.

---

## Future Roadmap (High-Level)

### Q2-Q3 2026: Production Launch & Growth
- SOC 2 Type II certification
- Mobile optimization / PWA support
- Team collaboration (Enterprise tier)
- QuickBooks Online integration (OAuth, direct import)
- AI anomaly explanations (OpenAI integration, Zero-Storage compliant)

### Q4 2026: Scale & Polish
- Native mobile apps (React Native)
- White-label branding (Enterprise)
- Advanced materiality formulas
- Workflow automation (Zapier/Make.com)

### 2027: International Expansion
- Multi-language support (Spanish, French, German)
- Multi-currency conversion
- IFRS account classification enhancements
- European data residency (GDPR)
- Open-source core engine

---

## Will Not Build

| Feature | Reason |
|---------|--------|
| Full accounting suite | Out of scope — we're diagnostic-only |
| Tax preparation | Not our expertise |
| Payroll integration | Too far from core value prop |
| Revenue Recognition (ASC 606) | Extreme complexity (9/10), contract-specific |
| Segregation of Duties Checker | IT audit persona, different user base |

---

## Feature Prioritization Framework (RICE)

| Feature | Reach | Impact | Confidence | Effort | RICE Score |
|---------|-------|--------|------------|--------|------------|
| **Ghost Employee Detector** | 5000 | 3 | 80% | 4 | 3000 |
| **AI explanations** | 5000 | 2 | 60% | 3 | 2000 |
| **Mobile apps** | 5000 | 3 | 80% | 8 | 1500 |
| **QB integration** | 2000 | 3 | 70% | 4 | 1050 |
| **Team collaboration** | 500 | 3 | 90% | 4 | 338 |

**RICE = (Reach x Impact x Confidence) / Effort**

---

## Changelog

**Version 2.0 (Feb 2026):** Updated to reflect Phase VII completion (v0.70.0), 5-tool suite
**Version 1.0 (Feb 2026):** Initial roadmap through Q4 2027

---

**Document Version History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 2.0 | 2026-02-06 | Product | Phase VII completion, 5-tool suite, updated roadmap |
| 1.0 | 2026-02-04 | Product | Initial publication |

---

*Paciolus v0.70.0 — Professional Audit Intelligence Suite*
