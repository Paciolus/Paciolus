# User Guide

**Document Classification:** Public (End User Documentation)
**Version:** 3.0
**Last Updated:** February 26, 2026
**Product Version:** 2.1.0
**Support:** help@paciolus.com

---

## Welcome to Paciolus

Paciolus is a diagnostic intelligence platform for financial professionals. Twelve specialized tools. Ten supported file formats. Zero data retention. Upload your financial data, receive structured diagnostics and report-ready exports — your client's files are processed in-memory and never written to disk.

**What makes Paciolus different:**
- **Zero-Storage Architecture:** Client data is processed in-memory and immediately discarded. Nothing written to disk. Nothing retained between sessions.
- **12 Diagnostic Tools:** Trial Balance Diagnostics, Multi-Period Comparison, Journal Entry Testing, AP Payment Testing, Bank Reconciliation, Payroll Testing, Three-Way Match, Revenue Testing, AR Aging, Fixed Asset Testing, Inventory Testing, and Statistical Sampling
- **10 File Formats:** CSV, Excel (.xlsx/.xls), TSV, TXT, OFX, QBO, IIF, PDF, and ODS
- **Professional Reports:** Client-ready PDF memos, Excel workpapers, and CSV exports with workpaper signoff

**Need help?** Email help@paciolus.com or visit our [Help Center](#)

---

## Table of Contents

1. [Getting Started](#1-getting-started)
2. [Data Upload Standards](#2-data-upload-standards)
3. [Tool 1: Trial Balance Diagnostics](#3-tool-1-trial-balance-diagnostics)
4. [Tool 2: Multi-Period Comparison](#4-tool-2-multi-period-comparison)
5. [Tool 3: Journal Entry Testing](#5-tool-3-journal-entry-testing)
6. [Tool 4: AP Payment Testing](#6-tool-4-ap-payment-testing)
7. [Tool 5: Bank Reconciliation](#7-tool-5-bank-reconciliation)
8. [Tool 6: Payroll Testing](#8-tool-6-payroll-testing)
9. [Tool 7: Three-Way Match](#9-tool-7-three-way-match)
10. [Tool 8: Revenue Testing](#10-tool-8-revenue-testing)
11. [Tool 9: AR Aging Analysis](#11-tool-9-ar-aging-analysis)
12. [Tool 10: Fixed Asset Testing](#12-tool-10-fixed-asset-testing)
13. [Tool 11: Inventory Testing](#13-tool-11-inventory-testing)
14. [Tool 12: Statistical Sampling](#14-tool-12-statistical-sampling)
15. [Billing & Plans](#15-billing--plans)
16. [Data Handling Guarantees](#16-data-handling-guarantees)
17. [Engagement Workspaces](#17-engagement-workspaces)
18. [Managing Clients](#18-managing-clients)
19. [Exports & Reports](#19-exports--reports)
20. [Customizing Settings](#20-customizing-settings)
21. [Command Palette](#21-command-palette)
22. [Activity History](#22-activity-history)
23. [Troubleshooting](#23-troubleshooting)
24. [FAQ](#24-faq)

---

## 1. Getting Started

### 1.1 Creating Your Account

1. Go to [paciolus.com/register](https://paciolus.com/register)
2. Enter your email address
3. Create a strong password (8+ characters, uppercase, lowercase, number, special character)
4. Click "Create Account"
5. **Verify your email** — check for a verification link (required to access tools)
6. Log in at [paciolus.com/login](https://paciolus.com/login)

All new accounts start on the **Free** plan. You can upgrade at any time from the Billing page.

### 1.2 Email Verification

All diagnostic tools require a verified email address. Without verification, you'll see a "Verify Your Email" banner instead of the tool interface.

**To verify:** Check your inbox for the verification email and click the link. If you don't see it, use the "Resend Verification" button.

### 1.3 Navigating the Platform

The tool navigation bar appears at the top of every tool page. The first six tools are shown inline; the remaining six are accessible from the "More" dropdown menu.

```
[Logo] | TB Diagnostics | Multi-Period | JE Testing | AP Testing | Bank Rec | Payroll | More ▾ | [Cmd+K] | [Profile]
```

The "More" dropdown contains: Three-Way Match, Revenue, AR Aging, Fixed Assets, Inventory, and Sampling.

Tools that require a higher plan tier show an upgrade prompt when accessed.

### 1.4 Keyboard Shortcuts

Press **Cmd+K** (Mac) or **Ctrl+K** (Windows) anywhere to open the command palette. Type a tool name, page, or action to navigate instantly.

Additional shortcuts:
- **Cmd+1** — Client Portfolio
- **Cmd+2** — Diagnostic Workspace
- **Cmd+[** / **Cmd+]** — Collapse/expand sidebars (workspace view)
- **Escape** — Close modals and menus

---

## 2. Data Upload Standards

### 2.1 Supported File Formats

Paciolus accepts the following file formats for upload. Format availability depends on your plan tier.

| Format | Extensions | Description | Tier |
|--------|-----------|-------------|------|
| CSV | `.csv` | Comma-separated values | All plans |
| Excel (modern) | `.xlsx` | Excel 2007+ (OOXML) | All plans |
| Excel (legacy) | `.xls` | Excel 97–2003 (BIFF) | All plans |
| TSV | `.tsv` | Tab-separated values | All plans |
| Text | `.txt` | Plain text with delimiter detection | All plans |
| QBO | `.qbo` | Quicken/QuickBooks Online interchange | Solo and above |
| OFX | `.ofx` | Open Financial Exchange (SGML v1 / XML v2) | Solo and above |
| IIF | `.iif` | QuickBooks Interchange Format | Solo and above |
| PDF | `.pdf` | Table extraction from PDF documents | Solo and above |
| ODS | `.ods` | OpenDocument Spreadsheet (LibreOffice/Calc) | Team and above |

### 2.2 File Requirements

- **Maximum file size:** 50 MB per upload
- **Headers:** Place column headers in the first row
- **Column detection:** Paciolus auto-detects columns using weighted pattern matching. If detection fails, use "Manual Mapping" to assign columns
- **Encoding:** UTF-8 recommended for CSV/TSV/TXT files

### 2.3 Column Detection

Each tool expects specific columns. Paciolus uses pattern matching to identify them automatically:

- A green checkmark means the column was confidently detected
- A yellow warning means low-confidence detection — review before proceeding
- If columns are not detected, click "Manual Mapping" to assign them yourself

---

## 3. Tool 1: Trial Balance Diagnostics

**Route:** `/tools/trial-balance`
**Purpose:** Upload a trial balance for instant anomaly detection, ratio analysis, lead sheet mapping, financial statement generation, and diagnostic analytics.

### 3.1 Uploading Your Trial Balance

**Required columns:** Account Name + Debit/Credit (auto-detected). Optional: Account Number, Sub-Account, Notes.

**Steps:**
1. Drag-and-drop your file onto the upload zone (or click to browse)
2. Paciolus auto-detects columns (green checkmark = detected)
3. If not detected, click "Manual Mapping" to assign columns
4. Processing takes 5–30 seconds depending on file size

### 3.2 Understanding Results

**Summary Card:** Total records, debits, credits, balanced status, variance.

**Classifications:** Accounts grouped into Assets, Liabilities, Equity, Revenue, and Expenses using 80+ keyword classification rules.

**Anomalies:** Flagged items include:
- Abnormal balances (credit balance on asset, debit balance on liability)
- Suspense account detection
- Concentration risk (single account holding disproportionate balance)
- Rounding anomalies
- Balance sheet imbalance detection

**Financial Ratios:** 17 core ratios across five categories — liquidity (Current, Quick), solvency (Debt-to-Equity, Equity Ratio, Long-Term Debt Ratio), profitability (Gross/Net/Operating margin, ROA, ROE), efficiency (Asset Turnover, Inventory Turnover, Receivables Turnover), and cash cycle (DSO, DPO, DIO, Cash Conversion Cycle) — plus industry-specific ratios when the client's industry is set. A DuPont decomposition (Net Profit Margin × Asset Turnover × Equity Multiplier = ROE) is available when all components are calculable.

**Lead Sheets:** Accounts mapped to A–Z workpaper categories for professional organization.

**Financial Statements:** Balance Sheet, Income Statement, and Cash Flow Statement (indirect method, ASC 230/IAS 7) generated from lead sheet groupings.

**Diagnostic Analytics:**
- **Data Quality Pre-Flight** — Format issues, outliers, and completeness checks run before full analysis
- **Population Profile** — Gini coefficient, magnitude distribution, top-N accounts by balance
- **Expense Category Analytics** — ISA 520 five-category decomposition
- **Accrual Completeness** — Run-rate ratios and completeness estimation
- **Classification Validator** — 6 structural COA checks (duplicates, orphans, unclassified, gaps, naming, sign anomalies)
- **Account-to-Statement Mapping Trace** — Raw aggregate and sign correction for each financial statement line
- **Lease Account Diagnostic** — IFRS 16/ASC 842 consistency tests
- **Cutoff Risk Indicator** — ISA 501 cutoff risk tests
- **Going Concern Indicator Profile** — ISA 570 six-indicator assessment (mandatory disclaimer)

### 3.3 Multi-Currency Support

If your trial balance contains amounts in multiple currencies:
1. Upload or manually enter currency exchange rates (closing rates)
2. Paciolus converts all amounts to a single reporting currency
3. Unconverted items are flagged for review
4. A Currency Conversion Memo (PDF) documents the methodology

### 3.4 Exporting

- **PDF Report** — Professional diagnostic report with legal disclaimers
- **Excel Workpaper** — Multi-tab structure (Summary, Standardized TB, Anomalies, Ratios)
- **CSV** — Standardized trial balance or anomalies list
- **Lead Sheets** — A–Z workbook (Excel)
- **Financial Statements** — Balance Sheet + Income Statement + Cash Flow (PDF or Excel)
- **Pre-Flight Memo** — Data quality assessment (PDF)
- **Population Profile Memo** — Account population analysis (PDF)

### 3.5 Sensitivity Tuning

Adjust the materiality threshold in real-time to see more or fewer flagged items. The materiality cascade flows from engagement-level settings down through practice and client defaults.

---

## 4. Tool 2: Multi-Period Comparison

**Route:** `/tools/multi-period`
**Purpose:** Compare up to three trial balance periods side-by-side with variance and flux analysis.

### 4.1 How It Works

1. Upload two files: **Prior Period** and **Current Period**
2. Label each period (e.g., "FY2024", "FY2025")
3. Both files are analyzed independently, then compared
4. For three-way comparison, add a budget period

### 4.2 Movement Types

Each account is classified into one of six movement types:

| Type | Meaning |
|------|---------|
| **NEW** | Account exists in current but not prior |
| **CLOSED** | Account exists in prior but not current |
| **SIGN_CHANGE** | Balance changed from debit to credit (or vice versa) |
| **INCREASE** | Balance increased |
| **DECREASE** | Balance decreased |
| **UNCHANGED** | No change |

### 4.3 Significance Tiers

- **MATERIAL** — Exceeds materiality threshold
- **SIGNIFICANT** — >10% change or >$10K
- **MINOR** — Small changes (<10% and <$10K)

### 4.4 Budget Variance (Three-Way)

When a budget period is included, each account shows:
- Budget amount, actual amount, variance amount
- Variance percentage and significance tier

### 4.5 Interperiod Reclassification Detection

Paciolus flags accounts that appear to have been reclassified between periods — for example, an account that moves from one financial statement category to another.

### 4.6 Exporting

- **Multi-Period Memo (PDF)** — Trend analysis and variance workpaper memo
- **CSV** — Comparison data with movement types and variances

---

## 5. Tool 3: Journal Entry Testing

**Route:** `/tools/journal-entry-testing`
**Purpose:** Automated general ledger analysis with 19 tests, Benford's Law, and stratified sampling.

### 5.1 Upload

Upload a General Ledger export. Required columns: Entry Number, Date, Account, Debit, Credit. Optional: Description, User, Reference.

### 5.2 Test Battery (19 Tests)

**Tier 1 — Structural (5 tests):**
- Unbalanced journal entries
- Missing required fields
- Duplicate entries
- Backdated entries
- Unusual amounts (z-score outliers)

**Tier 2 — Statistical (5 tests):**
- Benford's Law first-digit analysis
- Round amount concentration
- Weekend/holiday posting detection
- Unusual user activity
- Description anomaly detection

**Tier 3 — Advanced (9 tests):**
- Split transaction patterns
- Sequential anomalies
- Cross-period entries
- Related party indicators
- Fraud keyword detection
- Holiday posting detection (ISA 240.A40, JT-19)
- And additional pattern-based tests

### 5.3 Results

- **Composite Score** — Overall risk tier (LOW, MODERATE, ELEVATED, HIGH)
- **Test Result Grid** — Pass/fail status per test with flagged count and flag rate
- **Flagged Entry Table** — Sortable, filterable, paginated (25 per page)

### 5.4 Stratified Sampling

1. Configure sample parameters (confidence level, expected error rate)
2. Preview stratification (strata breakdown by amount range)
3. Execute CSPRNG-based sample selection (PCAOB AS 2315 compliant)

### 5.5 Exporting

- **JE Testing Memo (PDF)** — Professional testing memorandum (PCAOB AS 1215 / ISA 530 references)
- **Flagged Entries (CSV)** — All flagged entries with test key, severity, and confidence

### 5.6 Threshold Configuration

Go to Settings > Practice to configure test thresholds:
- **Presets:** Conservative, Standard, Permissive
- **Custom:** Adjust individual thresholds per test

---

## 6. Tool 4: AP Payment Testing

**Route:** `/tools/ap-testing`
**Purpose:** Detect duplicate payments, vendor anomalies, and fraud indicators in accounts payable data.

### 6.1 Upload

Upload an AP payment register. Key columns: Vendor, Invoice Number, Amount, Payment Date. Optional: Check Number, Description, Payment Method.

### 6.2 Test Battery (13 Tests)

**Tier 1 — Structural (5 tests):**
- **AP-T1:** Exact duplicate payments (same vendor + invoice + amount + date)
- **AP-T2:** Missing critical fields (blank vendor, zero amount)
- **AP-T3:** Check number gaps (sequential gap detection)
- **AP-T4:** Round dollar amounts ($10K+ thresholds)
- **AP-T5:** Payment before invoice date

**Tier 2 — Statistical (5 tests):**
- **AP-T6:** Fuzzy duplicate payments (same vendor, similar amount, different dates)
- **AP-T7:** Invoice number reuse across vendors
- **AP-T8:** Unusual payment amounts (per-vendor z-score outliers)
- **AP-T9:** Weekend payments
- **AP-T10:** High-frequency vendors (5+ payments on one day)

**Tier 3 — Fraud Indicators (3 tests):**
- **AP-T11:** Vendor name variations (similar names that might be the same vendor)
- **AP-T12:** Just-below-threshold amounts (within 5% of approval limits)
- **AP-T13:** Suspicious descriptions (16 AP-specific keywords)

### 6.3 Results

- **Composite Score Ring** — Visual risk tier indicator
- **Test Result Grid** — Cards organized by tier
- **Flagged Payment Table** — Sortable by test, vendor, amount, date, severity
- **Data Quality Badge** — Field completeness score

### 6.4 Exporting

- **AP Testing Memo (PDF)** — Professional memorandum (ISA 240 / ISA 500 / PCAOB AS 2401)
- **Flagged Payments (CSV)** — All flagged items with test details, severity, confidence

### 6.5 Threshold Configuration

Settings > Practice > AP Testing section:
- **Presets:** Conservative, Standard, Permissive, Custom
- **Key thresholds:** Round Amount ($), Duplicate Date Window (days), Unusual Amount Sensitivity (sigma), Keyword Sensitivity (%)
- **Toggle tests:** Enable/disable individual tests

---

## 7. Tool 5: Bank Reconciliation

**Route:** `/tools/bank-rec`
**Purpose:** Reconcile bank statement transactions against general ledger cash detail.

### 7.1 Upload

Upload two files side-by-side:
- **Left:** Bank Statement
- **Right:** GL Cash Detail

Column detection is automatic. If columns aren't detected confidently, a warning appears.

### 7.2 How Matching Works

Paciolus uses exact matching:
- Matches by amount (with configurable tolerance, default $0.01)
- Greedy algorithm processes largest amounts first
- Each transaction can only match once (one-to-one)
- Date tolerance also configurable

### 7.3 Results

**Match Summary Cards:**
- Matched count and amount
- Bank-only items (outstanding deposits/checks)
- Ledger-only items (unrecorded transactions)
- Reconciling difference

**Match Table:** Color-coded rows:
- Matched transactions (paired)
- Bank-only items (auto-categorized as Outstanding Check/Deposit, Deposit in Transit)
- Ledger-only items (auto-categorized as Unrecorded Check)

**Reconciliation Bridge:** Standard bank rec workpaper format showing:
- Bank balance → Adjusted bank balance
- GL balance → Adjusted GL balance
- Reconciling items breakdown

### 7.4 Exporting

- **Bank Rec Memo (PDF)** — Reconciliation verification workpaper memo
- **CSV Report** — 4 sections: Matched, Bank-Only, Ledger-Only, Summary

---

## 8. Tool 6: Payroll Testing

**Route:** `/tools/payroll-testing`
**Purpose:** Automated payroll register analysis with 11 tests covering structural, statistical, and fraud indicators.

### 8.1 Upload

Upload a payroll register. Key columns: Employee Name/ID, Gross Pay, Pay Date. Optional: Department, Hours, Rate, Net Pay, Deductions.

### 8.2 Test Battery (11 Tests)

**Structural tests:** Missing fields, duplicate records, pay frequency anomalies, termination-date checks.

**Statistical tests:** Gross pay outliers, overtime concentration, departmental variance.

**Fraud indicators:** Ghost employee detection (terminated employees still receiving pay), split-payroll patterns, round-amount concentration.

### 8.3 Results

- **Composite Score** — Risk tier assessment
- **Test Result Grid** — Pass/fail by test
- **Flagged Employee Table** — Sortable by test, employee, amount, severity

### 8.4 Exporting

- **Payroll Testing Memo (PDF)** — ISA 500 workpaper memo
- **Flagged Entries (CSV)** — All flagged items with test details

---

## 9. Tool 7: Three-Way Match

**Route:** `/tools/three-way-match`
**Purpose:** Match Purchase Orders to Invoices to Receipts with variance analysis.

### 9.1 Upload

Upload up to three data files:
- **Purchase Orders** — PO Number, Vendor, Amount, Date
- **Invoices** — Invoice Number, Vendor, Amount, Date, PO Reference
- **Receipts** — Receipt ID, PO Reference, Quantity/Amount Received

### 9.2 Matching Logic

Paciolus performs exact PO# linkage first, then falls back to fuzzy matching (vendor + amount similarity). Variances between PO, Invoice, and Receipt amounts are flagged.

### 9.3 Results

- Match status per document set (Fully Matched, Partial Match, Unmatched)
- Variance analysis (PO vs. Invoice, Invoice vs. Receipt)
- Flagged mismatches with severity assessment

### 9.4 Exporting

- **Three-Way Match Memo (PDF)** — Reconciliation workpaper memo
- **Flagged Items (CSV)** — All flagged matches with variance details

---

## 10. Tool 8: Revenue Testing

**Route:** `/tools/revenue-testing`
**Purpose:** Automated revenue transaction analysis with 16 tests covering structural, statistical, advanced, and contract-aware assessments (ISA 240, ASC 606/IFRS 15).

### 10.1 Upload

Upload a revenue register or sales journal. Key columns: Transaction ID, Date, Amount, Customer/Account. Optional: Contract ID, Obligation ID, Product/Service.

### 10.2 Test Battery (16 Tests)

**Tier 1 — Structural (5 tests):**
- Missing fields, duplicate transactions, negative revenue, date gaps, unusual customers

**Tier 2 — Statistical (4 tests):**
- Amount outliers, concentration risk, Benford's analysis, seasonality deviation

**Tier 3 — Advanced (3 tests):**
- Revenue recognition timing, period-end spikes, reversal patterns

**Tier 4 — Contract-Aware (4 tests, optional):**
- **RT-13:** Recognition timing (ASC 606 Step 5)
- **RT-14:** Obligation linkage (ASC 606 Step 2)
- **RT-15:** Modification treatment (ASC 606-10-25-12)
- **RT-16:** SSP allocation (ASC 606 Step 4)

Contract-aware tests activate when contract columns are detected. If columns are absent, tests are skipped with a reason — no errors are raised.

### 10.3 Exporting

- **Revenue Testing Memo (PDF)** — ASC 606/IFRS 15 workpaper memo
- **Flagged Transactions (CSV)** — All flagged items with test details

---

## 11. Tool 9: AR Aging Analysis

**Route:** `/tools/ar-aging`
**Purpose:** Accounts receivable aging analysis with 11 automated tests covering structural, statistical, and advanced assessments (ISA 500/540).

### 11.1 Upload

**Dual-input:**
- **Required:** Trial Balance with AR accounts
- **Optional:** AR Sub-Ledger detail for deeper analysis

### 11.2 Test Battery (11 Tests)

**Structural (4 tests):** Missing data, duplicate accounts, negative balances, aging bucket validation.

**Statistical (5 tests):** Concentration risk, aging distribution outliers, DSO calculation, allowance adequacy, trend deviation.

**Advanced (2 tests):** Subsequent collection analysis, credit limit assessment.

### 11.3 Exporting

- **AR Aging Memo (PDF)** — ISA 500/540 receivables valuation workpaper memo
- **Flagged Accounts (CSV)** — All flagged items with severity and test details

---

## 12. Tool 10: Fixed Asset Testing

**Route:** `/tools/fixed-assets`
**Purpose:** PP&E testing with 9 automated tests covering structural, statistical, and advanced assessments (IAS 16/ASC 360).

### 12.1 Upload

Upload a fixed asset register. Key columns: Asset Description, Cost, Accumulated Depreciation, Useful Life, Date Placed in Service.

### 12.2 Test Battery (9 Tests)

**Structural (4 tests):** Missing data, duplicate assets, negative values, classification anomalies.

**Statistical (3 tests):** Depreciation outliers, useful life deviation, capitalization threshold analysis.

**Advanced (2 tests):** Impairment indicators, disposal pattern analysis.

### 12.3 Exporting

- **Fixed Asset Memo (PDF)** — IAS 16/ASC 360 PP&E workpaper memo
- **Flagged Assets (CSV)** — All flagged items with severity and test details

---

## 13. Tool 11: Inventory Testing

**Route:** `/tools/inventory-testing`
**Purpose:** Inventory analysis with 9 automated tests covering structural, statistical, and advanced assessments (IAS 2/ASC 330).

### 13.1 Upload

Upload an inventory listing. Key columns: Item Description, Quantity, Unit Cost. Optional: Category, Last Movement Date, Location.

### 13.2 Test Battery (9 Tests)

**Structural (3 tests):** Missing data, duplicate items, negative quantities.

**Statistical (4 tests):** Cost outliers, slow-moving inventory, concentration by category, valuation anomalies.

**Advanced (2 tests):** Obsolescence indicators, NRV (net realizable value) assessment.

### 13.3 Exporting

- **Inventory Memo (PDF)** — IAS 2/ASC 330 inventory workpaper memo
- **Flagged Items (CSV)** — All flagged items with severity and slow-moving flags

---

## 14. Tool 12: Statistical Sampling

**Route:** `/tools/statistical-sampling`
**Purpose:** ISA 530 / PCAOB AS 2315 compliant sampling design, selection, and evaluation.

### 14.1 Two-Phase Workflow

**Phase 1 — Design & Select:**
1. Upload a population (any financial dataset)
2. Choose sampling method: **Monetary Unit Sampling (MUS)** or **Random Sampling**
3. Configure parameters: confidence level, expected error rate, tolerable misstatement
4. Preview 2-tier stratification (strata breakdown by amount range)
5. Execute CSPRNG-based sample selection
6. Export the selected sample for testing

**Phase 2 — Evaluate:**
1. Upload tested results (sample items with found errors)
2. Paciolus evaluates using Stringer bound calculation
3. Results: Pass or Fail with projected misstatement and upper error limit
4. Export evaluation memo

### 14.2 Exporting

- **Sampling Design Memo (PDF)** — ISA 530 / PCAOB AS 2315 methodology documentation
- **Sampling Evaluation Memo (PDF)** — Stringer bound evaluation results
- **Sample Selection (CSV)** — Selected items with stratum assignment

---

## 15. Billing & Plans

### 15.1 Plan Overview

Paciolus offers three purchasable plans plus a Free tier for evaluation.

| Feature | Free | Solo | Team | Organization |
|---------|------|------|------|-------------|
| **Price (monthly)** | $0 | $50/mo | $130/mo | $400/mo |
| **Price (annual)** | $0 | $500/yr | $1,300/yr | $4,000/yr |
| **Seats** | 1 | 1 | 3 included | 3 included |
| **Diagnostics/month** | 10 | 20 | Unlimited | Unlimited |
| **Clients** | 3 | 10 | Unlimited | Unlimited |
| **Tools** | 2 | 9 | All 12 | All 12 |
| **File formats** | 5 basic | 9 formats | All 10 | All 10 |
| **PDF export** | Yes | Yes | Yes | Yes |
| **Excel export** | — | Yes | Yes | Yes |
| **CSV export** | — | Yes | Yes | Yes |
| **Engagement Workspace** | — | — | Yes | Yes |
| **Priority support** | — | — | Yes | Yes |

### 15.2 Tool Access by Plan

| Tool | Free | Solo | Team | Organization |
|------|------|------|------|-------------|
| TB Diagnostics | Yes | Yes | Yes | Yes |
| Multi-Period Comparison | — | Yes | Yes | Yes |
| Journal Entry Testing | — | Yes | Yes | Yes |
| AP Payment Testing | — | Yes | Yes | Yes |
| Bank Reconciliation | — | Yes | Yes | Yes |
| Revenue Testing | — | Yes | Yes | Yes |
| Payroll Testing | — | — | Yes | Yes |
| Three-Way Match | — | — | Yes | Yes |
| AR Aging Analysis | — | — | Yes | Yes |
| Fixed Asset Testing | — | — | Yes | Yes |
| Inventory Testing | — | — | Yes | Yes |
| Statistical Sampling | — | — | Yes | Yes |

### 15.3 Seat-Based Pricing

Team and Organization plans include a base number of seats. Additional seats can be added:

- **Seats 4–10:** $80/month ($800/year) per seat
- **Seats 11–25:** $70/month ($700/year) per seat
- **26+ seats:** Contact sales for a custom quote

Manage seats from **Settings > Billing > Manage Seats**.

### 15.4 Upgrading and Managing Your Plan

1. Go to **Settings > Billing** or use the command palette (Cmd+K > "Billing")
2. Click "Upgrade" on the desired plan
3. Complete checkout via Stripe (secure payment processing)
4. Your plan activates immediately

To manage payment methods, view invoices, or cancel, click **"Manage Billing"** to open the Stripe Customer Portal.

**Cancellation:** Plans cancel at the end of the current billing period. You retain access until then. You can reactivate before the period ends.

---

## 16. Data Handling Guarantees

### 16.1 Zero-Storage Architecture

Paciolus operates under a Zero-Storage security model:

- **Your uploaded files are never stored.** Files are processed entirely in-memory and discarded immediately after analysis
- **No line-level data is persisted.** Individual account names, balances, and transaction details are never written to disk or database
- **Only aggregate metadata is retained.** Category totals, financial ratios, row counts, and diagnostic metadata are stored for your activity history
- **Server breach exposure is minimal.** Even in the event of a server compromise, no client financial data exists to be stolen

### 16.2 What Is Stored vs. What Is Not

| Stored (Aggregate Metadata) | Never Stored (Financial Data) |
|-----------------------------|-------------------------------|
| Your user credentials (hashed) | Raw uploaded files |
| Client names and industry settings | Individual account balances |
| Diagnostic summary (ratio values, row counts) | Line-level transaction details |
| Engagement metadata and status | Ledger entries or journal lines |
| Billing and subscription records | Bank statement line items |
| Activity log (filename prefix, timestamp) | Vendor names or employee names |

### 16.3 Implications for You

- **Always export before closing.** Results exist only during your session. Download PDF/Excel/CSV reports before navigating away
- **No historical data retrieval.** Paciolus cannot recover analysis results from a prior session. Your activity history shows metadata only (dates, row counts, ratios)
- **Simplified compliance.** Because Paciolus never stores client financial data, the platform has a minimal data footprint under GDPR, CCPA, and SOC 2 frameworks

For the complete technical specification, see the [Zero-Storage Architecture](https://paciolus.com/trust) document on our Trust page.

---

## 17. Engagement Workspaces

**Available on Team and Organization plans.**

Engagement Workspaces let you organize diagnostic work by client engagement, track follow-up items, and export a complete diagnostic package.

### 17.1 Creating a Workspace

1. Go to **Diagnostic Workspace** (Cmd+K > "Workspace" or navigate via sidebar)
2. Click "New Workspace"
3. Select a client and reporting period
4. Set the materiality threshold (or inherit from client/practice defaults)

### 17.2 Working in a Workspace

When a workspace is active, tool runs are automatically linked to the engagement:
- Tool results appear in the **Workpaper Index**
- The **Materiality Cascade** flows from engagement → client → practice → system default
- **Follow-Up Items** can be created for flagged issues (narratives only — no financial data stored)
- The **Cross-Tool Convergence Index** shows which accounts were flagged across multiple tools

### 17.3 Engagement Lifecycle

Workspaces follow a three-state workflow:
- **Active** → Running diagnostics, adding follow-up items
- **Completed** → All follow-up items must be resolved before completion
- **Archived** → Terminal state, read-only

### 17.4 Exporting

- **Anomaly Summary Report** — Aggregated diagnostic results with disclaimer
- **Diagnostic Package (ZIP)** — Contains anomaly summary + all tool memos generated during the engagement
- **Convergence CSV** — Cross-tool flagged account analysis

**Important:** All engagement exports include a non-dismissible disclaimer banner. Paciolus is a diagnostic tool, not an audit opinion.

---

## 18. Managing Clients

### 18.1 Adding a Client

1. Click "Portfolio" in navigation (or Cmd+K > "Portfolio")
2. Click "+ New Client"
3. Enter: Client Name, Industry, Fiscal Year End
4. Click "Save Client"

### 18.2 Client Settings

Each client can have custom settings:
- Materiality threshold override
- Industry classification for benchmark comparison (12 supported industries)
- Reporting framework (IFRS or GAAP)
- Practice-level thresholds cascade to client level

---

## 19. Exports & Reports

### 19.1 Export Formats

| Format | Description | Availability |
|--------|-------------|--------------|
| **PDF Memos** | Professional workpaper memoranda with ISA/PCAOB/IFRS/GAAP references, signoff fields, and legal disclaimers | All plans |
| **Excel Workpapers** | Multi-tab spreadsheets with structured data, summaries, and analysis tabs | Solo and above |
| **CSV** | Raw data exports (flagged entries, sample selections, anomalies) | Solo and above |
| **Lead Sheets (Excel)** | A–Z categorized workpaper | Solo and above |
| **Financial Statements** | Balance Sheet + Income Statement + Cash Flow Statement | Solo and above |
| **Diagnostic Package (ZIP)** | Complete engagement export with all memos | Team and above |

### 19.2 Available PDF Memos

Each testing tool generates a professional memorandum:

| Tool | Memo | Standards Referenced |
|------|------|---------------------|
| TB Diagnostics | Diagnostic Report | — |
| Multi-Period | Trend Analysis Memo | — |
| JE Testing | JE Testing Memo | PCAOB AS 1215, ISA 530 |
| AP Testing | AP Testing Memo | ISA 240, ISA 500, PCAOB AS 2401 |
| Bank Rec | Bank Rec Memo | — |
| Payroll Testing | Payroll Testing Memo | ISA 500 |
| Three-Way Match | Three-Way Match Memo | — |
| Revenue Testing | Revenue Testing Memo | ASC 606, IFRS 15 |
| AR Aging | AR Aging Memo | ISA 500, ISA 540 |
| Fixed Assets | Fixed Asset Memo | IAS 16, ASC 360 |
| Inventory | Inventory Memo | IAS 2, ASC 330 |
| Statistical Sampling | Design Memo + Evaluation Memo | ISA 530, PCAOB AS 2315 |

Additional memos: Currency Conversion Memo, Pre-Flight Memo, Population Profile Memo.

### 19.3 Proof Summary

Each testing tool page includes a **Proof Summary Bar** showing evidence quality across three dimensions: population coverage, test completeness, and data quality. These metrics also appear in the Engagement Workspace's **Proof Readiness** meter.

---

## 20. Customizing Settings

### 20.1 Practice Settings

**Settings > Practice** provides firm-wide defaults:

**Materiality:**
- Fixed amount, % of Revenue, % of Assets, % of Equity
- Priority chain: engagement override > client > practice > system default

**JE Testing Thresholds:**
- Conservative / Standard / Permissive presets
- Custom per-test thresholds

**AP Testing Thresholds:**
- Same preset system with configurable fields
- Toggle individual tests on/off

### 20.2 User Profile

**Settings > Profile:** Update display name, email, password.

Email changes require re-verification. A security notification is sent to your previous email address.

### 20.3 Billing Settings

**Settings > Billing:** View current plan, usage metrics, upgrade/downgrade, manage seats, access Stripe portal.

---

## 21. Command Palette

Press **Cmd+K** (Mac) or **Ctrl+K** (Windows) to open the command palette from anywhere in the platform.

### 21.1 What You Can Do

- **Navigate** — Jump to any page (Home, Portfolio, Workspace, Settings, Billing, Practice Settings)
- **Open Tools** — Type a tool name to go directly to it
- **Create** — Start a new workspace
- **Search** — Fuzzy search across all commands with keyword matching

### 21.2 Tier Gating

Commands for tools outside your current plan are visible but will show an upgrade prompt when selected.

### 21.3 Recency

Recently used commands appear higher in results. Recency data is stored in your browser session (Zero-Storage compliant — nothing sent to the server).

---

## 22. Activity History

**Route:** `/history`

Shows a chronological list of all diagnostics run:
- Date/time, truncated filename (first 12 characters), row count
- Balanced status, anomaly count
- **No account names or balances stored** (Zero-Storage compliant)

**Clear History:** Settings > Privacy > "Clear All Activity History" (GDPR Right to Erasure)

---

## 23. Troubleshooting

### "Columns Not Detected"

Ensure your file has headers in the first row. Try the following:
- Use "Manual Mapping" if auto-detection fails
- Check that column names match expected patterns (e.g., "Debit", "Credit", "Amount")
- For TSV/TXT files, verify the delimiter is consistent

### "File Too Large"

Maximum file size is 50 MB. Remove unnecessary columns or split into smaller files.

### "Unsupported Format"

Verify your file extension matches one of the 10 supported formats. Some formats (QBO, OFX, IIF, PDF, ODS) require a Solo plan or higher.

### "Verify Your Email"

All tools require email verification. Check your inbox for the verification link, or use "Resend Verification."

### "Out of Balance" Warning

This is informational — Paciolus is designed to diagnose trial balance issues. Review the flagged anomalies for investigation.

### "Upgrade Required"

You've attempted to access a tool or feature outside your current plan. Visit Settings > Billing to upgrade.

### "Diagnostic Limit Reached"

Free plans allow 10 diagnostics per month; Solo allows 20. Team and Organization plans have unlimited diagnostics.

---

## 24. FAQ

**Q: Is my data safe?**
A: Yes. Zero-Storage architecture means your financial data is processed in-memory and never stored. See Section 16 and our [Trust page](https://paciolus.com/trust) for details.

**Q: Can I recover results from last week?**
A: No. Zero-Storage means results are ephemeral. Always export to PDF/Excel/CSV before closing the browser.

**Q: Which tool should I use?**

| Scenario | Tool |
|----------|------|
| Analyze a single trial balance | TB Diagnostics |
| Compare this year vs. last year | Multi-Period Comparison |
| Test journal entries for fraud/errors | Journal Entry Testing |
| Check for duplicate vendor payments | AP Payment Testing |
| Reconcile bank statement to GL | Bank Reconciliation |
| Verify payroll register integrity | Payroll Testing |
| Match PO → Invoice → Receipt | Three-Way Match |
| Test revenue recognition (ASC 606) | Revenue Testing |
| Analyze accounts receivable aging | AR Aging Analysis |
| Assess fixed asset depreciation | Fixed Asset Testing |
| Evaluate inventory valuation | Inventory Testing |
| Design a statistical audit sample | Statistical Sampling |

**Q: Can I use Paciolus for audit engagements?**
A: Paciolus is a diagnostic intelligence tool, not an audit. It provides data-driven analysis to support your professional judgment. Use it for review engagements, compilations, internal diagnostics, and audit planning. See our [Terms of Service](https://paciolus.com/terms).

**Q: What file formats are supported?**
A: Ten formats: CSV, Excel (.xlsx/.xls), TSV, TXT, OFX, QBO, IIF, PDF, and ODS. Some formats require a Solo plan or higher. See Section 2 for details.

**Q: What is the maximum file size?**
A: 50 MB per upload across all formats.

**Q: How do I add team members?**
A: Team and Organization plans support multiple seats. Go to Settings > Billing > Manage Seats to add users.

**Q: Can I change my plan?**
A: Yes. Upgrade or downgrade at any time from Settings > Billing. Plan changes take effect immediately for upgrades and at the end of the billing period for downgrades/cancellations.

---

## Contact Support

- **Email:** help@paciolus.com
- **Response time:** <24 hours (business days)
- **Priority support:** Available on Team and Organization plans
- **Help Center:** [help.paciolus.com](#)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 3.0 | 2026-02-26 | Complete rewrite: 12 tools, 10 file formats, billing plans, engagement workspaces, command palette, data handling guarantees, v2.1.0 |
| 2.0 | 2026-02-06 | Added Tools 2–5 guides, updated navigation, v0.70.0 |
| 1.0 | 2026-02-04 | Initial user guide (Tool 1 only) |

---

*Paciolus v2.1.0 — Professional Audit Intelligence Platform*
