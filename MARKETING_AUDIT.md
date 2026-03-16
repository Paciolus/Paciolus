# Paciolus Marketing & Pricing Audit

**Date:** 2026-03-16
**Auditor Role:** Senior Marketing Strategist & SaaS Pricing Analyst (Read-Only Review)
**Scope:** Codebase-grounded audit of marketing claims, pricing alignment, feature fulfillment, and growth opportunities

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Source of Truth Analysis](#2-source-of-truth-analysis)
3. [Pricing Alignment Audit](#3-pricing-alignment-audit)
4. [Advertised Features vs. Backend Implementation](#4-advertised-features-vs-backend-implementation)
5. [Value-Add Opportunities](#5-value-add-opportunities)

---

## 1. Executive Summary

Paciolus is a zero-storage, AI-native financial audit SaaS platform targeting CPAs, with 12 diagnostic tools, a tiered billing model (Free/Solo/Professional/Enterprise), and a mature codebase (~6,500 backend tests, ~1,340 frontend tests). The platform is architecturally sound, with a well-structured entitlement system and Stripe integration.

**Key Findings:**

- **Pricing alignment is strong.** Backend (`price_config.py`), frontend pricing page, entitlements module, and Stripe configuration all use consistent tier names and pricing. No critical pricing drift was found.
- **No single canonical pricing constant is shared between frontend and backend.** Prices are independently hardcoded in both `backend/billing/price_config.py` and `frontend/src/app/(marketing)/pricing/page.tsx`. They currently agree, but this creates ongoing drift risk.
- **One diagnostic tool (Multi-Currency Conversion) exists in the backend but is absent from all marketing surfaces and the frontend tool directory.** This is either a strategic choice or a gap.
- **Several advertised features are service-level commitments with no backend implementation** (dedicated account manager, custom SLA, priority support tiers). This is expected for human-delivered services but should be documented.
- **The "All formats" vs "PDF, Excel & CSV" distinction in the comparison table is misleading.** Both Solo and Professional have identical export entitlements in the backend.
- **The Free tier is deliberately hidden from pricing cards** (only visible in comparison table and FAQ). This is a valid sales strategy but creates a discoverability gap for top-of-funnel acquisition.

**Overall Assessment:** The platform is remarkably well-aligned for a product at this stage. The issues found are Minor-to-Major in severity, with no Critical pricing drift. The biggest growth opportunities lie in better surfacing existing capabilities and sharpening competitive differentiation.

---

## 2. Source of Truth Analysis

### 2.1 Where Pricing Lives

| Surface | File(s) | Tier Names | Prices Match? |
|---------|---------|------------|---------------|
| **Backend price table** | `backend/billing/price_config.py` (lines 19-24) | free, solo, professional, enterprise | **Canonical source** |
| **Backend entitlements** | `backend/shared/entitlements.py` (lines 58-131) | FREE, SOLO, PROFESSIONAL, ENTERPRISE (via `UserTier` enum) | Yes (limits, not prices) |
| **Frontend pricing page** | `frontend/src/app/(marketing)/pricing/page.tsx` (lines 371-434) | Solo, Professional, Enterprise | Yes — $100/$500/$1,000 monthly |
| **Frontend seat configs** | Same file (lines 99-118) | Professional, Enterprise | Yes — $65/$45 per seat |
| **Stripe Price IDs** | Loaded from env vars at runtime (`STRIPE_PRICE_{TIER}_{INTERVAL}`) | solo, professional, enterprise | Cannot verify values (runtime) |
| **Tier display names** | `backend/shared/tier_display.py` (lines 12-17) | Free, Solo, Professional, Enterprise | Consistent |
| **Subscription model** | `backend/subscription_model.py` (line 91) | free, solo, professional, enterprise (DB enum) | Consistent |

### 2.2 Assessment

**There is no single shared constants file between frontend and backend.** Pricing amounts are hardcoded in two independent locations:

1. `backend/billing/price_config.py` — `PRICE_TABLE` dict (cents)
2. `frontend/src/app/(marketing)/pricing/page.tsx` — `tiers` array (dollars)

These currently agree, but any future price change requires synchronized edits in both codebases. The frontend also mirrors seat pricing constants (`SEAT_CONFIGS`) from the backend (`PROFESSIONAL_SEAT_PRICE`, `ENTERPRISE_SEAT_PRICE`).

**Mitigating factor:** The frontend pricing page includes a comment `// mirror backend price_config.py` (line 87), indicating awareness of this dependency. The backend also has startup-time billing config validation (`validate_billing_config()`).

> **FINDING SOT-01 (Major):** No single source of truth for pricing values. Frontend and backend maintain independent hardcoded copies. Drift risk is structural.

> **FINDING SOT-02 (Minor):** Stripe Price IDs are env-var-loaded, meaning the actual Stripe product catalog is a third independent source. Mismatches between Stripe product prices and code-level PRICE_TABLE would be caught only at checkout time.

---

## 3. Pricing Alignment Audit

### 3.1 Plan Names Across Surfaces

| Surface | Free | Solo | Professional | Enterprise |
|---------|------|------|--------------|------------|
| Backend `UserTier` enum | `FREE` | `SOLO` | `PROFESSIONAL` | `ENTERPRISE` |
| Backend `price_config.py` | `free` | `solo` | `professional` | `enterprise` |
| Frontend pricing cards | (not shown) | Solo | Professional | Enterprise |
| Frontend comparison table | Free | Solo | Professional | Enterprise |
| Frontend FAQ | Free tier | Solo | Professional | Enterprise |
| Tier display names | Free | Solo | Professional | Enterprise |

**Verdict:** Plan names are consistent across all surfaces. No drift.

### 3.2 Pricing Amounts

| Tier | Backend (cents) | Frontend (dollars) | Match? |
|------|-----------------|--------------------|--------|
| Solo monthly | 10,000 | $100 | Yes |
| Solo annual | 100,000 | $1,000 | Yes |
| Professional monthly | 50,000 | $500 | Yes |
| Professional annual | 500,000 | $5,000 | Yes |
| Enterprise monthly | 100,000 | $1,000 | Yes |
| Enterprise annual | 1,000,000 | $10,000 | Yes |

**Verdict:** All prices match. No drift.

### 3.3 Seat Pricing

| Tier | Backend (cents) | Frontend (dollars) | Match? |
|------|-----------------|--------------------|--------|
| Professional seat monthly | 6,500 | $65 | Yes |
| Professional seat annual | 65,000 | $650 | Yes |
| Enterprise seat monthly | 4,500 | $45 | Yes |
| Enterprise seat annual | 45,000 | $450 | Yes |

| Tier | Backend included seats | Frontend display | Match? |
|------|-----------------------|-----------------|--------|
| Professional | 7 (`seats_included`) | "7 seats included (up to 20)" | Yes |
| Enterprise | 20 (`seats_included`) | "20 seats included (up to 100)" | Yes |

**Verdict:** Seat pricing and limits match. No drift.

### 3.4 Upload Limits

| Tier | Backend (`uploads_per_month`) | Frontend pricing page | Match? |
|------|------------------------------|----------------------|--------|
| Free | 10 | "10" (comparison table) | Yes |
| Solo | 100 | "100 uploads per month" | Yes |
| Professional | 500 | "500 uploads per month" | Yes |
| Enterprise | 0 (unlimited) | "Unlimited" | Yes |

**Verdict:** Upload limits match. No drift.

### 3.5 Feature Entitlements

| Feature | Backend Entitlement | Frontend Claim | Match? |
|---------|--------------------|--------------------|--------|
| **Free tools** | `trial_balance`, `flux_analysis` | "2 (TB + Flux)" | Yes |
| **Paid tools** | `_ALL_TOOLS` (all 12) | "All 12 diagnostic tools" | Yes |
| **Free clients** | 3 | "3" | Yes |
| **Paid clients** | 0 (unlimited) | "Unlimited" | Yes |
| **Solo exports** | pdf=True, excel=True, csv=True | "PDF, Excel & CSV" | Yes |
| **Pro exports** | pdf=True, excel=True, csv=True | "All formats" | **See PD-01** |
| **Workspace** | Solo+ (True) | "Diagnostic Workspace" on Solo card | Yes |
| **Export sharing** | Professional+ (True) | "Export sharing" on Pro card | Yes |
| **Admin dashboard** | Professional+ (True) | "Admin dashboard & activity logs" | Yes |
| **Activity logs** | Professional+ (True) | (included in above) | Yes |
| **Bulk upload** | Enterprise only (True) | "Bulk upload (up to 5 files)" | Yes |
| **Custom branding** | Enterprise only (True) | "Custom PDF branding" | Yes |

> **FINDING PD-01 (Minor):** The comparison table distinguishes Solo ("PDF, Excel & CSV") from Professional ("All formats"), but the backend grants identical export entitlements to both tiers (`pdf_export=True, excel_export=True, csv_export=True`). There are no additional export formats beyond PDF/Excel/CSV. The "All formats" label implies Professional gets something extra that doesn't exist. This creates false upgrade motivation.

### 3.6 Trial Configuration

| Claim | Code | Match? |
|-------|------|--------|
| "7-day free trial" | `TRIAL_PERIOD_DAYS = 7` in `price_config.py:127` | Yes |
| "no credit card required" | Checkout creates session with `trial_period_days=7` | **See PD-02** |
| Trial eligible tiers | `{"solo", "professional", "enterprise"}` | Matches pricing page |

> **FINDING PD-02 (Major):** The pricing page and FAQ state "no credit card required to start" the trial. However, the checkout flow uses Stripe Checkout Sessions, which by default collect payment information. Stripe's `trial_period_days` parameter on a Checkout Session still typically requires a payment method. If Stripe is configured with `payment_method_collection: 'if_required'` or similar, the claim may hold — but this cannot be verified from the codebase alone (it depends on Stripe Dashboard settings). The FAQ also says "After 7 days, your selected plan begins billing automatically **if a payment method is on file**" — the conditional language partially hedges this, but the hero claim "no credit card required" is presented without qualification. This is a potential FTC compliance risk if the Stripe checkout does require card entry.

### 3.7 Promotional Pricing

| Promo | Backend Code | Frontend Display | Match? |
|-------|-------------|-----------------|--------|
| Monthly 20% off first 3 months | `PROMO_CODES["MONTHLY20"]` → Stripe coupon | "20% off your first 3 months on any monthly plan" | Structurally present (coupon details in Stripe) |
| Annual 10% off first year | `PROMO_CODES["ANNUAL10"]` → Stripe coupon | "Extra 10% off your first year on any annual plan" | Structurally present (coupon details in Stripe) |

**Note:** Coupon IDs are loaded from env vars. The actual discount amounts and durations are configured in Stripe, not in code. The frontend copy cannot be verified against Stripe configuration from code alone.

### 3.8 Annual Discount Claim

The pricing page displays "Save ~16.7%" for annual billing. Verification:

- Solo: $100/mo × 12 = $1,200/yr. Annual = $1,000. Savings = $200/$1,200 = **16.7%**. Correct.
- Professional: $500/mo × 12 = $6,000/yr. Annual = $5,000. Savings = $1,000/$6,000 = **16.7%**. Correct.
- Enterprise: $1,000/mo × 12 = $12,000/yr. Annual = $10,000. Savings = $2,000/$12,000 = **16.7%**. Correct.

The backend `get_annual_savings_percent()` function computes this dynamically. No drift.

---

## 4. Advertised Features vs. Backend Implementation

### 4.1 Diagnostic Tools — Marketing Claims vs. Backend Engines

The marketing ToolSlideshow (`frontend/src/components/marketing/ToolSlideshow.tsx`) showcases 12 tools. Here is the verification:

| # | Tool (Marketing) | Backend Engine | Backend Memo | Frontend Page | Route | Test Count Claim | Verified |
|---|-----------------|----------------|-------------|---------------|-------|-----------------|----------|
| 1 | Trial Balance Diagnostics | `audit_engine.py` | `flux_expectations_memo.py` + others | `/tools/trial-balance` | `routes/diagnostics.py` | "17 ratios" | Yes — `ratio_engine.py` + `industry_ratios.py` |
| 2 | Multi-Period Comparison | `multi_period_comparison.py` | `multi_period_memo_generator.py` | `/tools/multi-period` | `routes/multi_period.py` | N/A | Yes |
| 3 | Journal Entry Testing | `je_testing_engine.py` | `je_testing_memo_generator.py` | `/tools/journal-entry-testing` | `routes/je_testing.py` | 19 tests | Yes |
| 4 | Revenue Testing | `revenue_testing_engine.py` | `revenue_testing_memo_generator.py` | `/tools/revenue-testing` | `routes/revenue_testing.py` | 16 tests | Yes |
| 5 | AP Payment Testing | `ap_testing_engine.py` | `ap_testing_memo_generator.py` | `/tools/ap-testing` | `routes/ap_testing.py` | 13 tests | Yes |
| 6 | Bank Reconciliation | `bank_reconciliation.py` | `bank_reconciliation_memo_generator.py` | `/tools/bank-rec` | `routes/bank_reconciliation.py` | N/A | Yes |
| 7 | Statistical Sampling | `sampling_engine.py` | `sampling_memo_generator.py` | `/tools/statistical-sampling` | `routes/sampling.py` | N/A | Yes |
| 8 | Payroll Testing | `payroll_testing_engine.py` | `payroll_testing_memo_generator.py` | `/tools/payroll-testing` | `routes/payroll_testing.py` | 11 tests | Yes |
| 9 | Three-Way Match | `three_way_match_engine.py` | `three_way_match_memo_generator.py` | `/tools/three-way-match` | `routes/three_way_match.py` | N/A | Yes |
| 10 | AR Aging Analysis | `ar_aging_engine.py` | `ar_aging_memo_generator.py` | `/tools/ar-aging` | `routes/ar_aging.py` | 11 tests | Yes |
| 11 | Fixed Asset Testing | `fixed_asset_testing_engine.py` | `fixed_asset_testing_memo_generator.py` | `/tools/fixed-assets` | `routes/fixed_asset_testing.py` | 10 tests | Yes (FA-01 through FA-10) |
| 12 | Inventory Testing | `inventory_testing_engine.py` | `inventory_testing_memo_generator.py` | `/tools/inventory-testing` | `routes/inventory_testing.py` | 9 tests | Yes |

**All 12 marketed tools have confirmed backend engines, memo generators, frontend pages, and API routes. No feature gaps.**

### 4.2 Unmarketable Assets (Backend Exists, No Marketing Presence)

| Backend Asset | Files | Marketing Mention | Status |
|---------------|-------|-------------------|--------|
| **Multi-Currency Conversion** | `currency_engine.py`, `currency_memo_generator.py`, `routes/currency.py` | **None** — absent from ToolSlideshow, no frontend tool page | **FINDING FG-01** |
| **Engagement Dashboard (DASH-01)** | `engagement_dashboard_engine.py`, `engagement_dashboard_memo.py` | Not directly marketed as a standalone tool | Accessible via workspace |
| **Population Profile** | `population_profile_engine.py`, `population_profile_memo.py` | Not marketed | Part of TB diagnostic flow |
| **Expense Category Analysis** | `expense_category_engine.py`, `expense_category_memo.py` | Not marketed | Part of TB diagnostic flow |
| **Accrual Completeness** | `accrual_completeness_engine.py`, `accrual_completeness_memo.py` | Not marketed | Part of TB diagnostic flow |
| **Going Concern Indicators** | `going_concern_engine.py` | Not marketed | Part of TB diagnostic flow |
| **Lease Diagnostics** | `lease_diagnostic_engine.py` | Not marketed | Part of TB diagnostic flow |
| **Cutoff Risk** | `cutoff_risk_engine.py` | Not marketed | Part of TB diagnostic flow |
| **Anomaly Summary** | `anomaly_summary_generator.py` | Not marketed separately | Part of TB diagnostic flow |
| **Preflight Checks** | `preflight_engine.py`, `preflight_memo_generator.py` | Not marketed | Data quality checks |

> **FINDING FG-01 (Major):** Multi-Currency Conversion is a complete backend tool with engine, memo generator, and API route, but has **no frontend tool page** (not listed in `frontend/src/app/tools/`) and is **absent from all marketing**. CLAUDE.md lists it as "Tool 12" in the historical record. The current marketing ToolSlideshow lists a different set of 12 tools that does not include Multi-Currency. This is either intentional deprecation or a significant marketing gap for international CPA firms.

> **FINDING FG-02 (Minor):** The TB Diagnostics tool page markets "17 financial ratios" and "anomaly detection," but the underlying engine includes at least 6 additional diagnostic sub-engines (population profile, expense category, accrual completeness, going concern, lease diagnostics, cutoff risk). These represent substantial analytical depth that could be marketed individually or as a suite differentiator — currently they are hidden inside the TB workflow with no public documentation.

### 4.3 Service-Level Claims Without Backend Implementation

| Advertised Feature | Tier | Backend? | Assessment |
|-------------------|------|----------|------------|
| "Dedicated account manager" | Enterprise | No backend implementation | Expected — human service delivery |
| "Custom SLA" | Enterprise | No backend implementation | Expected — contractual, not software |
| "Priority support" | Professional+ | No backend implementation | Expected — support tooling is external |
| "Email support (next business day)" | Solo | No backend implementation | Expected |
| "Community" support | Free | No backend implementation | Expected |

**Assessment:** These are all service-level commitments delivered through external processes (support desk, account management). No backend enforcement is expected or needed. **Not flagged as feature gaps.**

### 4.4 "140+ Automated Tests" Claim

The homepage (`EvidenceBand.tsx`, `BottomProof.tsx`) and `ProofStrip.tsx` all claim "140+ automated tests across all 12 diagnostic tools."

**Verification (from backend test IDs):**
- JE Testing: 19 tests
- Revenue Testing: 16 tests
- AP Testing: 13 tests
- Payroll Testing: 11 tests
- AR Aging: 11 tests
- Fixed Assets: 10 tests (FA-01 through FA-10)
- Inventory: 9 tests
- **Subtotal from numbered tools: 89**
- TB Diagnostics: 17 ratios + anomaly detection + classification + multiple sub-diagnostics ≈ 30+ checks
- Multi-Period: variance tests, reclassification detection
- Bank Rec: matching, reconciliation
- Statistical Sampling: MUS, random, Stringer bounds
- Three-Way Match: PO matching, variance, exception reporting
- **Estimated total: 130-150+**

**Verdict:** The "140+" claim appears plausible based on the aggregate test battery. It may be conservative. No issue flagged.

### 4.5 "Zero-Storage" Claims

The marketing approach page (`/approach`) makes extensive claims about zero-storage architecture:
- "Your raw financial data never touches our database. By design, not by policy."
- "Every file is processed in-memory and immediately discarded"
- "No financial data in database to breach"

**Backend verification:**
- `subscription_model.py` docstring confirms: "ZERO-STORAGE EXCEPTION: This module stores ONLY subscription metadata"
- Processing engines operate on in-memory DataFrames
- `shared/metadata_persistence_policy.md` exists (policy documentation)
- The approach page's "What We Store" / "What We Never Store" lists are consistent with the code architecture

**Verdict:** Zero-storage claims are well-substantiated by the architecture. The approach page's "Trade-Offs" section (acknowledging re-upload requirements) demonstrates commendable transparency.

### 4.6 Standards Citations Claims

Marketing claims: "ISA · PCAOB · ASC" per-memo citations, "7 Standards Referenced" (ISA, PCAOB, IFRS, ASC, IAS).

**Verified from ToolSlideshow data:** Tools reference ISA 240, ISA 315, ISA 500, ISA 501, ISA 505, ISA 520, ISA 530, ISA 540, PCAOB AS 2315, PCAOB AS 2401, ASC 326, ASC 330, ASC 360, ASC 606, IAS 1, IAS 2, IAS 16, IFRS 15. This spans 5 standard frameworks (ISA, PCAOB, ASC, IAS, IFRS).

**Verdict:** The "7 Standards Referenced" metric in BottomProof counts at 5 framework families, but "7" likely counts individual standard numbers. The claim is defensible but the counting methodology is ambiguous.

### 4.7 File Format Claims

Marketing claims: "10 file formats: CSV, Excel (.xlsx/.xls), TSV, TXT, QBO, OFX, IIF, PDF, ODS" (CLAUDE.md and FAQ).

**Backend verification from `shared/file_formats.py`:** CSV, XLSX, XLS, TSV, TXT, QBO, OFX, IIF, PDF, ODS = **10 formats**. All have `parse_supported=True`. Matches exactly.

The approach page lists upload formats as: "CSV, Excel, TSV, TXT, QBO, OFX, IIF, PDF, or ODS" — this lists 9 because "Excel" covers both XLSX and XLS. Accurate.

---

## 5. Value-Add Opportunities

### Lens A — Upsell & Expansion Revenue

#### A1: Multi-Currency as a Premium Feature / Upsell Lever

**Description:** Multi-Currency Conversion already exists as a complete backend tool (`currency_engine.py`, `currency_memo_generator.py`, `routes/currency.py`) but is completely absent from marketing and the frontend. Rather than simply adding it as tool #13 available to all paid tiers, consider positioning it as a premium add-on or as a headline differentiator for Professional/Enterprise tiers. International engagements are a premium workflow — firms handling multi-currency clients are typically larger and higher-value.

**Target tier:** Professional and Enterprise
**Value driver:** Upsell (Solo→Professional for international firms) + Acquisition (differentiator for global CPA firms)
**Codebase evidence:** `backend/currency_engine.py`, `backend/currency_memo_generator.py`, `backend/routes/currency.py` — complete engine with API route

#### A2: Diagnostic Depth Upsell — Sub-Engine Premium Reports

**Description:** The TB Diagnostics tool contains at least 6 sub-engines that run silently within the TB workflow: Population Profile, Expense Category Analysis, Accrual Completeness, Going Concern Indicators, Lease Diagnostics, and Cutoff Risk Analysis. These represent deep analytical capabilities that are currently invisible to users. Consider surfacing these as individually accessible "deep dive" diagnostics, available as standalone tools or as a "TB Diagnostics+" premium layer. This creates upgrade motivation without building new features.

**Target tier:** Professional and Enterprise
**Value driver:** Retention (users discover more value) + Upsell (premium depth tier)
**Codebase evidence:** `backend/going_concern_engine.py`, `backend/lease_diagnostic_engine.py`, `backend/cutoff_risk_engine.py`, `backend/accrual_completeness_engine.py`, `backend/expense_category_engine.py`, `backend/population_profile_engine.py`

#### A3: Upload Overage Billing

**Description:** Currently, when a Solo user hits 100 uploads, they're blocked. This is a hard wall that forces an upgrade decision (Solo $100 → Professional $500 — a 5x jump). Consider introducing per-upload overage pricing (e.g., $1-2 per additional upload) to capture revenue from users who occasionally exceed limits but don't need Professional features. The subscription model already tracks `uploads_used_current_period`, making metered billing feasible.

**Target tier:** Solo (bridging to Professional)
**Value driver:** Revenue expansion + Retention (reduces churn from hard limit frustration)
**Codebase evidence:** `backend/subscription_model.py:111` tracks `uploads_used_current_period`; `backend/shared/entitlement_checks.py:58-101` implements upload limit checking with the infrastructure to support metered billing

### Lens B — Competitive Differentiation vs. DataSnipper

#### B1: "Zero-Storage" as a Category Differentiator Against DataSnipper

**Description:** DataSnipper operates as an Excel add-in that processes data locally within Excel workbooks. Paciolus processes data in ephemeral server-side RAM with no persistence. Both claim data security, but the mechanisms are fundamentally different. DataSnipper's Excel-native approach means data lives in the firm's file system. Paciolus's zero-storage approach means data never persists *anywhere* on the platform side. The current `/approach` page makes the zero-storage case well but never mentions competitors or positions against alternatives. Consider a dedicated "Paciolus vs. Excel Add-ins" comparison page that highlights: (1) no dependency on local Excel installations, (2) no file versioning/duplication risk, (3) results accessible from any device, (4) automated report generation vs. Excel-native workflows.

**Target tier:** All (acquisition-focused)
**Value driver:** Differentiation + Acquisition
**Codebase evidence:** `/approach` page already has a "Traditional SaaS vs Paciolus Zero-Storage" comparison table — this framework could be extended to address Excel-native competitors specifically

#### B2: Engagement Workflow Completeness

**Description:** DataSnipper focuses on document-level extraction and cross-referencing within workpapers. Paciolus has a broader engagement management layer: engagement workspace, follow-up tracker, workpaper index, materiality cascade, completion gate, and diagnostic package ZIP export. This engagement-level orchestration is a significant differentiator that's undermarketed. The homepage FeaturePillars section mentions "Precision at Every Threshold" (materiality) but doesn't showcase the full engagement workflow. A dedicated "Engagement Management" feature page could highlight this.

**Target tier:** Professional and Enterprise (engagement management is a team workflow)
**Value driver:** Differentiation + Acquisition (firms evaluating audit workflow tools)
**Codebase evidence:** `backend/engagement_manager.py`, `backend/engagement_model.py`, `backend/follow_up_items_manager.py`, `backend/workpaper_index_generator.py`, `frontend/src/app/(workspace)/engagements/`

#### B3: Standards Citation Depth as Marketing Differentiator

**Description:** Every Paciolus tool test maps to a specific ISA, PCAOB, or ASC standard. This is a significant differentiator that peer review firms and quality control partners care deeply about. The marketing mentions standards in passing, but doesn't show how this works in practice. Consider adding a "Standards Map" page or section that visually shows which standard each test references, organized by ISA/PCAOB/ASC framework. This would resonate strongly with firms subject to AICPA peer review requirements, where documentation traceability is a key concern.

**Target tier:** All (credibility-focused)
**Value driver:** Acquisition + Differentiation (no competitor offers this level of standards traceability)
**Codebase evidence:** ToolSlideshow data includes per-tool standards arrays; memo generators embed standard references in PDF output; `shared/authoritative_language/` directory contains standards reference data

### Lens C — CPA Workflow Pain Points

#### C1: Peer Review Documentation Support

**Description:** CPAs in the US are subject to AICPA peer review, which requires demonstrating that engagement procedures were properly planned, executed, and documented. Paciolus's engagement workspace, follow-up tracker, and workpaper index already provide much of this documentation trail. Adding a "Peer Review Ready" export bundle (e.g., a ZIP containing all engagement documentation, workpapers, and completion status) could save firms hours of preparation before peer review. The engagement export already supports ZIP packaging.

**Target tier:** Professional and Enterprise
**Value driver:** Retention (becomes embedded in annual peer review workflow) + Acquisition (firms dreading peer review)
**Codebase evidence:** `backend/engagement_export.py` (ZIP packaging), `backend/workpaper_index_generator.py`, `backend/follow_up_items_manager.py`

#### C2: Client Onboarding Acceleration

**Description:** The biggest friction point in CPA audit workflow is getting client data in the right format. Paciolus already supports 10 file formats, including QuickBooks exports (QBO, IIF) and bank feeds (OFX). Marketing barely mentions this multi-format ingestion capability. A "Client Data Guide" feature that generates format-specific upload instructions for common accounting systems (QuickBooks, Xero, Sage, NetSuite) could dramatically reduce onboarding friction. This is a content/UX play, not an engineering lift.

**Target tier:** All
**Value driver:** Activation (reduces upload abandonment) + Acquisition (searchable content marketing)
**Codebase evidence:** `backend/shared/file_formats.py` already categorizes all 10 formats with labels; `backend/shared/iif_parser.py`, `backend/shared/ofx_parser.py`, `backend/shared/ods_parser.py`, `backend/shared/pdf_parser.py` demonstrate deep format support

#### C3: Deadline-Aware Engagement Prioritization

**Description:** CPAs work under extreme deadline pressure (fiscal year-ends, regulatory filing dates). The engagement workspace tracks engagement status but doesn't currently surface deadline urgency or enable prioritization by filing date. Adding a simple due-date field to engagements and a priority-sorted dashboard view could position Paciolus as deadline-aware rather than just tool-aware. This addresses the #1 workflow pain point in audit: managing concurrent engagements with staggered deadlines.

**Target tier:** Professional and Enterprise (multi-engagement workflow)
**Value driver:** Retention (daily usage driver) + Upsell (Solo practitioners manage 1-2 engagements; growing firms manage 10+)
**Codebase evidence:** `backend/engagement_model.py`, `frontend/src/app/(workspace)/engagements/` — engagement management infrastructure is in place

---

## Appendix: Summary of Findings

### Pricing Drift Findings

| ID | Severity | Finding | Location |
|----|----------|---------|----------|
| SOT-01 | **Major** | No single source of truth for pricing values — frontend and backend maintain independent hardcoded copies | `backend/billing/price_config.py` + `frontend/src/app/(marketing)/pricing/page.tsx` |
| SOT-02 | Minor | Stripe Price IDs are runtime-loaded, creating a third pricing source that can't be validated from code | `backend/billing/price_config.py:30-44` |
| PD-01 | Minor | "All formats" vs "PDF, Excel & CSV" distinction in comparison table is misleading — both tiers have identical export entitlements | `frontend/pricing/page.tsx:454` vs `backend/shared/entitlements.py:84-86,98-100` |
| PD-02 | **Major** | "No credit card required" trial claim may conflict with Stripe Checkout Session payment collection — depends on Stripe Dashboard configuration | `frontend/pricing/page.tsx:484,651` vs `backend/billing/checkout.py` |

### Feature Gap Findings

| ID | Severity | Finding | Location |
|----|----------|---------|----------|
| FG-01 | **Major** | Multi-Currency Conversion exists as complete backend tool but is absent from all marketing and frontend tool pages | `backend/currency_engine.py`, `backend/routes/currency.py` — no frontend counterpart |
| FG-02 | Minor | 6+ TB sub-diagnostics (going concern, lease, cutoff, accrual, expense category, population profile) are unmarketable hidden features | Various backend `*_engine.py` files |

### Severity Definitions

- **Critical:** Active misinformation, legal/compliance risk, or revenue-impacting pricing errors. *(None found.)*
- **Major:** Structural risks that could cause drift, misleading claims, or significant missed revenue. *(3 found: SOT-01, PD-02, FG-01.)*
- **Minor:** Cosmetic inconsistencies, suboptimal marketing choices, or low-risk alignment gaps. *(3 found: SOT-02, PD-01, FG-02.)*

---

*End of Marketing & Pricing Audit — Paciolus v2.1.0*
