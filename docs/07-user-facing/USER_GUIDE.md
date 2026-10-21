# User Guide

**Document Classification:** Public (End User Documentation)
**Version:** 3.0
**Last Updated:** February 26, 2026
**Product Version:** 2.1.0
**Support:** help@paciolus.com

---

## Welcome to Paciolus

Paciolus is a diagnostic intelligence platform for financial professionals. Eighteen specialized tools. Ten supported file formats. Zero data retention. Upload your financial data, receive structured diagnostics and report-ready exports — your client's files are processed in-memory and never written to disk.

**What makes Paciolus different:**
- **Zero-Storage Architecture:** Client data is processed in-memory and immediately discarded. Nothing written to disk. Nothing retained between sessions.
- **18 Audit Tools:** Trial Balance Diagnostics, Multi-Period Comparison, Bank Reconciliation, Three-Way Match, Journal Entry Testing, AP Payment Testing, Revenue Testing, AR Aging, Payroll Testing, Fixed Assets, Inventory Testing, Statistical Sampling, Segregation of Duties, Intercompany Elimination, W-2 / W-3 Reconciliation, Form 1099 Preparation, Book-to-Tax Reconciliation, and the Cash Flow Projector. Multi-Currency Conversion runs alongside them as a validation layer rather than a tool of its own.
  - Sections 3–20 below walk through all eighteen in detail, one chapter each.
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
15. [Tool 13: Segregation of Duties](#15-tool-13-segregation-of-duties)
16. [Tool 14: Intercompany Elimination](#16-tool-14-intercompany-elimination)
17. [Tool 15: W-2 / W-3 Reconciliation](#17-tool-15-w-2--w-3-reconciliation)
18. [Tool 16: Form 1099 Preparation](#18-tool-16-form-1099-preparation)
19. [Tool 17: Book-to-Tax Reconciliation](#19-tool-17-book-to-tax-reconciliation)
20. [Tool 18: Cash Flow Projector](#20-tool-18-cash-flow-projector)
21. [Billing & Plans](#21-billing--plans)
22. [Data Handling Guarantees](#22-data-handling-guarantees)
23. [Engagement Workspaces](#23-engagement-workspaces)
24. [Managing Clients](#24-managing-clients)
25. [Exports & Reports](#25-exports--reports)
26. [Customizing Settings](#26-customizing-settings)
27. [Command Palette](#27-command-palette)
28. [Activity History](#28-activity-history)
29. [Troubleshooting](#29-troubleshooting)
30. [FAQ](#30-faq)

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

The tool navigation bar appears at the top of every tool page. Six tools are shown inline and the rest sit under the "More" dropdown. The navigation bar carries the twelve core diagnostic and testing tools; the full catalogue of eighteen — including Segregation of Duties, Intercompany Elimination, W-2 / W-3 Reconciliation, Form 1099 Preparation, Book-to-Tax Reconciliation and the Cash Flow Projector — is on the Tools index page and in the command palette (Cmd+K).

```
[Logo] | TB Diagnostics | Multi-Period | JE Testing | AP Testing | Bank Rec | Payroll | More ▾ | [Cmd+K] | [Profile]
```

The "More" dropdown contains: Three-Way Match, Revenue, AR Aging, Fixed Assets, Inventory, and Sampling.

Tools that require a higher plan tier show an upgrade prompt when accessed.

### 1.4 Keyboard Shortcuts

Press **Cmd+K** (Mac) or **Ctrl+K** (Windows) anywhere to open the command palette. Type a tool name, page, or action to navigate instantly.

Additional shortcuts:
- **Cmd+1** — Client Portfolio
- **Cmd+2** — Workspace
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

- **JE Testing Memo (PDF)** — Professional testing memorandum (PCAOB AS 2401 + ISA 240 procedure references)
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

### 6.2 Test Battery (14 Tests)

**Tier 1 — Structural (6 tests):**
- **AP-T1:** Exact duplicate payments (same vendor + invoice + amount + date)
- **AP-T2:** Missing critical fields (blank vendor, zero amount)
- **AP-T3:** Check number gaps (sequential gap detection)
- **AP-T4:** Round dollar amounts ($10K+ thresholds)
- **AP-T5:** Payment before invoice date
- **AP-T14:** Invoice without PO — payments above materiality with a blank purchase-order
  reference. Per the ACFE 2024 *Report to the Nations*, billing schemes account for roughly
  19% of occupational fraud cases, and missing PO linkage is the canonical indicator.
  Requires a PO-number column; skipped with a reason when absent.

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

### 8.2 Test Battery (13 Tests)

**Tier 1 — Structural (7 tests):**
- **PR-T1:** Duplicate employee IDs (same ID, different names)
- **PR-T2:** Missing critical fields (blank name, zero pay, blank date)
- **PR-T3:** Round salary amounts ($100K / $50K / $25K / $10K patterns)
- **PR-T4:** Pay after termination date — *requires a termination-date column*
- **PR-T5:** Check number gaps — *requires a check-number column*
- **PR-T12:** Duplicate employee names (same name, different IDs). Paired with PR-T1 this
  completes the employee-identity check: same ID with different names points at ID reuse,
  same name with different IDs is the classic ghost-employee pattern.
- **PR-T13:** Gross-to-net reconciliation — flags rows where gross pay − deductions ≠ net pay.
  Named in the AICPA *Employee Benefit Plan Audit Guide* Ch. 5 as a first-line integrity check:
  if the three columns do not reconcile, at least one of them is wrong.

**Tier 2 — Statistical (3 tests):**
- **PR-T6:** Unusual pay amounts (per-department z-score outliers)
- **PR-T7:** Pay frequency anomalies (irregular pay spacing per employee)
- **PR-T8:** Benford's Law on gross pay (first-digit distribution)

**Tier 3 — Fraud Indicators (3 tests):**
- **PR-T9:** Ghost employee indicators (employees matching multiple fraud signals)
- **PR-T10:** Duplicate bank accounts or addresses — *requires a bank-account or address column*
- **PR-T11:** Duplicate tax IDs — *requires a tax-ID column*

Tests marked *requires* emit a skipped result with a reason when the column is absent, rather
than failing the run.

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

### 10.2 Test Battery (18 Tests)

**Tier 1 — Structural (5 tests):**
- **RT-01:** Large manual entries
- **RT-02:** Year-end concentration
- **RT-03:** Round revenue amounts
- **RT-04:** Sign anomalies (credit-balance revenue accounts)
- **RT-05:** Unclassified entries

**Tier 2 — Statistical (5 tests):**
- **RT-06:** Amount z-score outliers
- **RT-07:** Revenue trend variance
- **RT-08:** Customer concentration risk
- **RT-09:** Period-end cut-off risk (early-recognition exposure)
- **RT-09b:** Prior-period timing — entries dated near the *period start*. Split from RT-09,
  because an entry just after the opening is a different assertion from one just before the
  close: the first suggests revenue held back from the prior period, the second suggests
  revenue pulled forward into this one.

**Tier 3 — Advanced (4 tests):**
- **RT-10:** Benford's Law first-digit analysis
- **RT-11:** Duplicate entries
- **RT-12:** Contra-revenue anomalies
- **RT-17:** Contract validity (ASC 606 Step 1). Flags three combinations, any of which means
  revenue is recognised without the contract structure ASC 606 requires:
  a `contract_id` with no `performance_obligation_id` (Step 2 requires identified obligations);
  a `recognition_method` with no `contract_id` (no underlying contract to support recognition);
  and point-in-time recognition with no `obligation_satisfaction_date` (ASC 606-10-25-30 requires
  the transfer-of-control moment to be identified). Two or more issues on one entry raise it to
  high severity. Skipped entirely when no contract-aware columns are detected.

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

### 11.2 Test Battery (12 Tests)

**Tier 1 — Structural (5 tests):**
- **AR-01:** AR sign anomalies — a credit balance on the trial-balance AR account
- **AR-01b:** Sub-ledger negative invoices. A different assertion from AR-01: the trial
  balance can still net to a debit while an individual invoice is a credit memo, a reversal
  or a data-entry error that the account-level check cannot see.
- **AR-02:** Missing allowance for doubtful accounts
- **AR-03:** Negative aging buckets
- **AR-04:** Unreconciled sub-ledger detail against the trial-balance account

**Tier 2 — Statistical (5 tests):**
- **AR-05:** Aging bucket concentration
- **AR-06:** Past-due concentration
- **AR-07:** Allowance adequacy against the aging profile
- **AR-08:** Customer concentration
- **AR-09:** DSO trend deviation

**Tier 3 — Advanced (2 tests):**
- **AR-10:** AR rollforward reconciliation
- **AR-11:** Credit limit breaches

AR-01b, AR-03, AR-04, AR-05, AR-06, AR-08, AR-10 and AR-11 need the sub-ledger file. Without
it each emits a skipped result with a reason, so the test-slot count stays stable.

### 11.3 Exporting

- **AR Aging Memo (PDF)** — ISA 500/540 receivables valuation workpaper memo
- **Flagged Accounts (CSV)** — All flagged items with severity and test details

---

## 12. Tool 10: Fixed Asset Testing

**Route:** `/tools/fixed-assets`
**Purpose:** PP&E testing with 9 automated tests covering structural, statistical, and advanced assessments (IAS 16/ASC 360).

### 12.1 Upload

Upload a fixed asset register. Key columns: Asset Description, Cost, Accumulated Depreciation, Useful Life, Date Placed in Service.

### 12.2 Test Battery (11 Tests)

**Tier 1 — Structural (4 tests):**
- **FA-01:** Fully depreciated assets still on the register
- **FA-02:** Missing required fields
- **FA-03:** Negative cost or accumulated depreciation
- **FA-04:** Accumulated depreciation exceeding cost

**Tier 2 — Statistical (4 tests):**
- **FA-05:** Useful life outliers
- **FA-06:** Cost z-score outliers
- **FA-07:** Asset age concentration
- **FA-T11:** Depreciation recalculation (IAS 16 / ASC 360) — where cost, residual value,
  useful life and method are all present, recomputes expected annual depreciation and flags
  material deviation from the reported accumulated figure. Supports straight-line and
  double-declining balance.

**Tier 3 — Advanced (3 tests):**
- **FA-08:** Duplicate asset detection
- **FA-09:** Residual value anomalies
- **FA-10:** Lease asset indicators — scans descriptions for lease language and flags for
  confirmation of ASC 842 treatment (right-of-use recognition, classification, amortization).

### 12.3 Exporting

- **Fixed Asset Memo (PDF)** — IAS 16/ASC 360 PP&E workpaper memo
- **Flagged Assets (CSV)** — All flagged items with severity and test details

---

## 13. Tool 11: Inventory Testing

**Route:** `/tools/inventory-testing`
**Purpose:** Inventory analysis with 9 automated tests covering structural, statistical, and advanced assessments (IAS 2/ASC 330).

### 13.1 Upload

Upload an inventory listing. Key columns: Item Description, Quantity, Unit Cost. Optional: Category, Last Movement Date, Location.

### 13.2 Test Battery (10 Tests)

**Tier 1 — Structural (3 tests):**
- **IN-01:** Missing required fields
- **IN-02:** Negative quantities or costs
- **IN-03:** Extended value mismatch (quantity × unit cost ≠ reported extended value)

**Tier 2 — Statistical (4 tests):**
- **IN-04:** Unit cost outliers (z-score)
- **IN-05:** Quantity outliers (z-score)
- **IN-06:** Slow-moving inventory (default 180-day threshold against last movement date)
- **IN-07:** Category concentration

**Tier 3 — Advanced (3 tests):**
- **IN-08:** Duplicate item detection
- **IN-09:** Zero-value items carrying quantity
- **IN-T10:** Lower-of-cost-or-market / NRV indicator. IAS 2 ¶9 and ASC 330-10 cap inventory
  at the lower of cost and net realizable value; where a selling-price column is present,
  flags items whose unit cost exceeds selling price after an expected margin floor. Runs only
  when selling price is populated on at least one row.

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

## 15. Tool 13: Segregation of Duties

**Purpose:** Detect incompatible access combinations — one person who can both create a vendor and approve its invoice, or post a journal entry and close the period. Built for SOC 1 and internal-audit engagements.

**Standards:** SOC 1, COSO 2013 Principle 10 (selects and develops control activities), AICPA segregation-of-incompatible-duties guidance.

**Availability:** every paid plan.

### 15.1 Input

Two matrices, uploaded as CSV and parsed in your browser:

| Matrix | Columns |
|--------|---------|
| User-to-role | User ID, User Name, Role Codes (one role per row, or a delimited list) |
| Role-to-permission | Role Code, Permissions (one per row, or a delimited list) |

Permission names are normalised before matching — case, surrounding whitespace and spaces-versus-underscores are all treated the same, so `JE Create`, `je_create` and `JE_CREATE` are one permission.

Custom rules can be supplied with the request. They are **additive** to the built-in library, not a replacement.

### 15.2 Rule Library (11 Rules)

| Code | Conflict |
|------|----------|
| **AP-01** | Vendor master maintenance + invoice creation |
| **AP-02** | Invoice creation + payment release |
| **AP-03** | Payment execution + bank reconciliation |
| **JE-01** | Journal entry creation + posting |
| **JE-02** | Journal entry posting + period close |
| **PR-01** | Payroll master maintenance + payment |
| **PR-02** | Pay rate change + payment |
| **REV-01** | Customer creation + credit memo issuance |
| **REV-02** | Invoicing + cash receipt application |
| **INV-01** | Physical inventory custody + accounting records |
| **ADM-01** | User administration + transactional access |

Each rule carries a severity (high / medium / low), a mitigation suggestion and a rationale, all returned with the result so they can be pasted into a workpaper.

### 15.3 Reading the Output

- **Conflict matrix** — one row per (user, rule) hit, with the permissions that triggered it.
- **Per-user risk ranking** — score = `3 × high + 2 × medium + 1 × low`. Tiers: **high** at ≥ 6, **moderate** at ≥ 3, otherwise **low**.
- **Counts** — rules evaluated, users evaluated, users with at least one conflict, high-risk users.

A detected conflict is a **candidate for review**, not a deficiency. Whether a compensating control is adequate, and whether any gap rises to a significant deficiency or material weakness, is auditor judgment under ISA 265 / AU-C 265 and is deliberately not automated.

### 15.4 Exporting

- **SoD Analysis (CSV)** — conflict matrix plus the per-user ranking.

**Scope limits:** one matrix set per run. Bridging roles across multiple systems is out of scope, and the rule library covers common AICPA / SOX 404 patterns rather than every entity-specific conflict.

---

## 16. Tool 14: Intercompany Elimination

**Purpose:** Match reciprocal intercompany balances across entity trial balances, propose the elimination entries that zero them, and show the consolidation worksheet before and after.

**Standards:** ASC 810, IFRS 10, ISA 600.

**Availability:** every paid plan.

### 16.1 Input

Two or more entity trial balances in one request (maximum 50 entities, 5,000 accounts each):

| Field | Notes |
|-------|-------|
| Entity ID, Entity Name | Entity ID must be unique across the request |
| Account | Account name or number |
| Debit, Credit | Decimal strings |
| Counterparty Entity | **The field that makes matching possible** — which entity the balance is due from or to |
| Tolerance | Reconciliation tolerance, default `1.00` |

Without a counterparty entity on at least one side, a balance cannot be paired and appears as an unmatched intercompany line.

### 16.2 Reading the Output

- **Intercompany lines** — every account identified as intercompany.
- **Matched pairs** — reciprocal balances found, each marked reconciling or mismatched against the tolerance.
- **Mismatches** — pairs that do not agree. These are the ones that matter: a mismatch is the signature of a timing difference, a currency difference or a booking error, and it has to be reconciled manually before consolidation can complete.
- **Elimination journal entries** — proposed entries to zero out the reconciling pairs.
- **Consolidation worksheet** — pre-elimination totals by entity, the eliminations, and post-elimination consolidated totals.

**The engine does not assert that elimination is complete.** It shows the gaps so you can close them. A clean mismatch report is evidence; an empty one on incomplete data is not.

### 16.3 Exporting

- **Consolidation Worksheet (CSV)** — the full worksheet including proposed eliminations.

---

## 17. Tool 15: W-2 / W-3 Reconciliation

**Purpose:** Reconcile payroll system year-to-date totals against draft W-2s and the four quarterly Forms 941 — before filing, rather than after an IRS notice.

**Standards:** IRC §6051, Form W-2, Form W-3, Form 941.

**Availability:** every paid plan.

### 17.1 Input

| Input | Required | Columns |
|-------|----------|---------|
| Payroll YTD | Yes | Employee ID, Employee Name, Federal Wages, Federal Withholding, SS Wages, SS Tax Withheld, Medicare Wages, Medicare Tax Withheld |
| Draft W-2 list | Optional | Same per-employee amounts as drafted for filing |
| Form 941 quarters | Optional — but see below | Up to four quarters: total wages, federal withholding, SS wages, Medicare wages |

Also supply the tax year and a tolerance (default `1.00`). Supplying only payroll YTD still produces internal-consistency checks; adding the W-2 drafts and 941s is what enables the cross-form reconciliation.

### 17.2 What It Catches

- Mismatched Social Security and Medicare wages between payroll and the draft W-2
- Mis-applied Social Security wage base caps
- Over-contributions to HSAs and retirement plans
- Quarterly 941 totals that do not sum to the W-3 summary

> **Check the statutory limits before relying on the cap and over-limit findings.** The engine
> holds **one fixed set** of limits — Social Security wage base, HSA self-only and family,
> 401(k) and SIMPLE elective deferrals — and applies them to whatever `tax_year` you supply,
> anywhere from 2000 to 2099. It does not select limits by year, and the API exposes no way to
> override them. Treat every wage-base and over-limit finding as "check this against the figures
> for your tax year" rather than as a conclusion. Tracked as **Sprint 793**; the wage
> comparisons and the 941 reconciliation are unaffected, since those compare your own numbers to
> each other.

### 17.3 Reading the Output

- **Employee discrepancies** — per-employee differences between payroll and the draft W-2.
- **Form 941 mismatches** — an **annual aggregate** comparison. The engine sums every quarter
  you supply and compares that sum against the full-year payroll totals; it does not compute
  per-quarter differences, and each finding is reported without a quarter attached.

  > **Supply all four quarters or none.** Because the comparison is against *annual* payroll,
  > supplying only Q1 compares one quarter's totals to the whole year and reports a large
  > mismatch that means nothing. This is a limitation of the current implementation, not a
  > finding about your data.
- **W-3 totals** — the computed summary the four 941s should agree to.

**The engine flags discrepancies; it does not decide which number is right.** When payroll and the draft W-2 disagree, determining the correct figure is a practitioner judgment about the underlying facts.

### 17.4 Exporting

- **Reconciliation (CSV)** — employee discrepancies and 941 mismatches.

A PDF memo for this tool is not yet available.

---

## 18. Tool 16: Form 1099 Preparation

**Purpose:** Aggregate vendor payments across a tax year, apply the common 1099 reporting thresholds, and produce a candidate filing list with a data-quality report.

**Standards:** IRC §6041, IRC §6041A, IRS Publication 1220.

**Availability:** every paid plan.

### 18.1 Input

| Input | Columns |
|-------|---------|
| Vendors (max 5,000) | Vendor ID, Vendor Name, TIN (EIN or SSN, formatted or not), Entity Type, Address, City, State, Postal Code |
| Payments (max 50,000) | Vendor ID, Amount, Payment Category, Payment Method |

Plus the tax year. Entity type drives the corporate safe harbour, and payment method drives the processor exemption, so both affect whether a vendor becomes a candidate.

### 18.2 Thresholds

| Form | Threshold the engine applies (aggregate per vendor) |
|------|------------------------------------------------------|
| 1099-NEC — nonemployee compensation | $600 |
| 1099-MISC — rents, royalties, medical, legal | $600 |
| 1099-INT — interest | $10 |

> **These are fixed, and the reporting thresholds are not.** The engine applies the table above
> to whatever `tax_year` you supply and does not vary by year or sub-category — so for a year in
> which a threshold has moved, the candidate list will be wrong in both directions: vendors below
> the current threshold included, and vendors above a *lowered* one omitted. Confirm the
> thresholds for your filing year before treating the candidate list as complete. Tracked as
> **Sprint 793**. The vendor aggregation, the corporate safe harbour, the processor exemption and
> the data-quality report are unaffected.

### 18.3 Reading the Output

- **Candidates** — vendors meeting a threshold, with per-box amounts.
- **Data quality** — vendors missing a TIN or address, or with inconsistent records. Fix these before filing; a missing TIN is the most common cause of a rejected submission.
- **W-9 collection list** — vendors you need a W-9 from, derived from the data-quality findings.

**The engine is deliberately conservative: it identifies candidates for review rather than asserting a filing obligation.** 1099 rules are IRS-defined and sit outside platform judgment — corporate status, payment categorisation and exemptions all require the practitioner's read of the facts.

### 18.4 Exporting

- **1099 Candidates (CSV)** — the candidate listing only: form type, vendor, total reportable,
  per-box categories, payment count, excluded amount, and the per-candidate review flag with its
  reasons.

  The **data-quality report and the W-9 collection list are not in the CSV** — they are returned
  by the API and shown on screen, but the export does not carry them. Work through those on
  screen before exporting, or capture them separately.

A PDF memo for this tool is not yet available.

---

## 19. Tool 17: Book-to-Tax Reconciliation

**Purpose:** Bridge book pretax income to taxable income, lay the adjustments out as Schedule M-1 or M-3, and roll the timing differences into a deferred tax summary.

**Standards:** Form 1120 Schedule M-1, Form 1120 Schedule M-3, ASC 740.

**Availability:** every paid plan.

### 19.1 Input

| Field | Notes |
|-------|-------|
| Tax year | |
| Book pretax income | Per GAAP |
| Total assets | **Drives the M-1 vs M-3 output** |
| Federal tax rate, state tax rate | Decimal strings, e.g. `0.21` |
| Adjustments (max 500) | Label, Amount, Difference Type (`permanent` / `temporary`), Direction (`add` / `subtract`) |
| Rollforward | Beginning deferred tax asset and liability |

### 19.2 M-1 or M-3

The entity-size heuristic follows the IRS Schedule M-3 threshold for corporations:

| Total assets | Output |
|--------------|--------|
| Under $10M | Schedule M-1 |
| $10M and above | Schedule M-3 |

Both layouts are computed and returned; the `entity_size` field tells you which one applies.

### 19.3 Reading the Output

- **Schedule M-1 / M-3** — the reconciliation from book income to taxable income, adjustments classified permanent or temporary.
- **Deferred tax rollforward** — beginning balances, the movement from this year's temporary differences, and ending deferred tax asset / liability.
- **Tax provision** — current and deferred components at the supplied rates.

**The engine is a calculator, not a tax opinion.** Whether a given adjustment is permanent or temporary for the entity's facts is the practitioner's determination, and the classification you supply is the classification it uses.

### 19.4 Exporting

- **Book-to-Tax (CSV)** — the reconciliation, deferred rollforward and provision summary.

A PDF memo for this tool is not yet available.

---

## 20. Tool 18: Cash Flow Projector

**Purpose:** Project the forward 30 / 60 / 90-day cash position from AR aging, AP aging, opening cash and recurring flows, across three scenarios, and flag where the balance breaches a minimum safe level.

**Standards:** ASC 230.

**Availability:** every paid plan.

**Not the same thing as the Cash Flow Statement.** Trial Balance Diagnostics produces an indirect-method cash flow *statement* from historical trial balance data (§3). This tool is its forward-looking counterpart, aimed at operational finance rather than financial reporting.

### 20.1 Input

| Field | Notes |
|-------|-------|
| Opening balance | Cash on hand at the start date |
| Start date | The projection origin |
| AR aging | Current, 1–30, 31–60, 61–90, over 90 |
| AP aging | Same five buckets |
| Recurring flows (max 100) | Label, Amount (negative for outflow), Frequency, First Date |
| Minimum safe cash | Optional — the threshold whose breach gets flagged |

### 20.2 Scenarios

Three scenarios apply different collection and payment assumptions to the same deterministic weekly grid. AR collection rates by bucket:

| Bucket | Stress | Base | Best |
|--------|--------|------|------|
| Current | 80% | 95% | 100% |
| 1–30 | 65% | 85% | 95% |
| 31–60 | 50% | 70% | 85% |
| 61–90 | 30% | 50% | 70% |
| Over 90 | 10% | 20% | 40% |

The AP side moves with it, and that is what makes stress bite. Under **base**, payables aged past 30 days are partly deferred (95% / 90% / 80% paid). Under **stress** every bucket pays at 100% — receipts slow while payables go out on time, which is the combination that actually causes a squeeze. Under **best**, AP defers across the board (90% down to 70%) while collections improve.

Run stress first. It is the scenario that tells you whether you have a problem; base tells you what you expect, and best tells you very little.

### 20.3 Reading the Output

Per scenario, at each of the 30 / 60 / 90-day horizons:

- **Cumulative inflow and outflow**
- **Ending balance**
- **Lowest balance and the day it occurs** — the number that matters most. A healthy 90-day ending balance can sit on top of a mid-period trough that breaches your minimum.
- **Liquidity breach flags** where the minimum safe cash level is crossed

AR buckets are also ranked by their expected contribution to collections under the base scenario, which is the practical collections priority list.

### 20.4 Exporting

- **Projection (CSV)** — a **daily** row per scenario: day index, date, AR inflow, AP outflow,
  recurring net, net change and ending balance, for all 90 days of each of the three scenarios.

  The **30 / 60 / 90-day horizon summaries are not in the CSV** — including the lowest balance
  and the day it occurs. Those are returned by the API and shown on screen. If you need them in
  a workpaper, read them off the screen or derive them from the daily rows.

PDF and Excel exports for this tool are not yet available.

---

## 21. Billing & Plans

### 21.1 Plan Overview

Paciolus offers three purchasable plans plus a Free tier for evaluation.

| Feature | Free | Solo | Professional | Enterprise |
|---------|------|------|-------------|------------|
| **Price (monthly)** | $0 | $100/mo | $500/mo | $1,000/mo |
| **Price (annual)** | $0 | $1,000/yr | $5,000/yr | $10,000/yr |
| **Seats** | 1 | 1 | 7 included (up to 20) | 20 included (up to 100) |
| **Uploads/month** | 10 | 100 | 500 | Unlimited |
| **Clients** | 3 | Unlimited | Unlimited | Unlimited |
| **Tools** | 2 (TB + Flux) | All 18 | All 18 | All 18 |
| **File formats** | 5 basic | All 10 | All 10 | All 10 |
| **PDF export** | — | Yes | Yes | Yes |
| **Excel export** | — | Yes | Yes | Yes |
| **CSV export** | — | Yes | Yes | Yes |
| **Engagement Workspace** | — | Yes | Yes | Yes |
| **Export sharing** | — | — | Yes | Yes |
| **Admin dashboard** | — | — | Yes | Yes |
| **Custom PDF branding** | — | — | — | Yes |
| **Bulk upload** | — | — | — | Yes |
| **Priority support** | — | — | Yes | Yes |

### 21.2 Tool Access by Plan

All paid tiers (Solo, Professional, Enterprise) have access to all 18 tools.

| Tool | Free | Solo | Professional | Enterprise |
|------|------|------|-------------|------------|
| TB Diagnostics | Yes | Yes | Yes | Yes |
| Multi-Period Comparison | — | Yes | Yes | Yes |
| Journal Entry Testing | — | Yes | Yes | Yes |
| AP Payment Testing | — | Yes | Yes | Yes |
| Bank Reconciliation | — | Yes | Yes | Yes |
| Revenue Testing | — | Yes | Yes | Yes |
| Payroll Testing | — | Yes | Yes | Yes |
| Three-Way Match | — | Yes | Yes | Yes |
| AR Aging Analysis | — | Yes | Yes | Yes |
| Fixed Asset Testing | — | Yes | Yes | Yes |
| Inventory Testing | — | Yes | Yes | Yes |
| Statistical Sampling | — | Yes | Yes | Yes |
| Segregation of Duties | — | Yes | Yes | Yes |
| Intercompany Elimination | — | Yes | Yes | Yes |
| W-2 / W-3 Reconciliation | — | Yes | Yes | Yes |
| Form 1099 Preparation | — | Yes | Yes | Yes |
| Book-to-Tax Reconciliation | — | Yes | Yes | Yes |
| Cash Flow Projector | — | Yes | Yes | Yes |

Free tier is limited to TB Diagnostics and Flux Analysis.

### 21.3 Seat-Based Pricing

Professional and Enterprise plans include a base number of seats. Additional seats can be added:

- **Seats 8–22:** $80/month ($800/year) per seat (graduated: Tier 1 qty 1–7 = $80, Tier 2 qty 8–22 = $70)
- **23+ seats:** Contact sales for a custom quote

Manage seats from **Settings > Billing > Manage Seats**.

### 21.4 Upgrading and Managing Your Plan

1. Go to **Settings > Billing** or use the command palette (Cmd+K > "Billing")
2. Click "Upgrade" on the desired plan
3. Complete checkout via Stripe (secure payment processing)
4. Your plan activates immediately

To manage payment methods, view invoices, or cancel, click **"Manage Billing"** to open the Stripe Customer Portal.

**Cancellation:** Plans cancel at the end of the current billing period. You retain access until then. You can reactivate before the period ends.

---

## 22. Data Handling Guarantees

### 22.1 Zero-Storage Architecture

Your uploaded financial data is never stored.

Raw uploaded financial data is never persisted to disk or retained between sessions. Paciolus retains only aggregate, non-attributable usage metadata in accordance with our retention policy. No line-level financial data is ever written to storage.

Paciolus operates under a Zero-Storage security model:

- **Your uploaded files are never stored.** Files are processed entirely in-memory and discarded immediately after analysis
- **No line-level data is persisted.** Individual account names, balances, and transaction details are never written to disk or database
- **Only aggregate metadata is retained.** Category totals, financial ratios, row counts, and diagnostic metadata are stored for your activity history and workspace continuity
- **Server breach exposure is minimal.** Even in the event of a server compromise, no client financial data exists to be stolen

### 22.2 What Is Stored vs. What Is Not

| Stored (Aggregate Metadata) | Never Stored (Financial Data) |
|-----------------------------|-------------------------------|
| Your user credentials (hashed) | Raw uploaded files |
| Client names and industry settings | Individual account balances |
| Diagnostic summary (ratio values, row counts) | Line-level transaction details |
| Engagement metadata and status | Ledger entries or journal lines |
| Billing and subscription records | Bank statement line items |
| Activity log (filename prefix, timestamp) | Vendor names or employee names |

### 22.3 Implications for You

"Ephemeral" refers specifically to your uploaded financial data. Workspace metadata — including analysis results, findings summaries, and report history — is retained so you can return to your work.

- **Always export detailed results before closing.** Line-level analysis detail (flagged entries, individual transactions) exists only during your session. Download PDF/Excel/CSV reports before navigating away. Aggregate summaries and workspace metadata persist across sessions.
- **No raw data retrieval.** Paciolus cannot recover your uploaded financial files or line-level detail from a prior session. Your activity history shows aggregate metadata only (dates, row counts, ratios)
- **Simplified compliance.** Because Paciolus never stores client financial data, the platform has a minimal data footprint under GDPR, CCPA, and SOC 2 frameworks

For the complete technical specification, see the [Zero-Storage Architecture](https://paciolus.com/trust) document on our Trust page.

---

## 23. Engagement Workspaces

**Available on Solo, Professional, and Enterprise plans.**

Engagement Workspaces let you organize diagnostic work by client engagement, track follow-up items, and export a complete diagnostic package.

### 23.1 Creating a Workspace

1. Go to **Workspace** (Cmd+K > "Workspace" or navigate via sidebar)
2. Click "New Workspace"
3. Select a client and reporting period
4. Set the materiality threshold (or inherit from client/practice defaults)

### 23.2 Working in a Workspace

When a workspace is active, tool runs are automatically linked to the engagement:
- Tool results appear in the **Workpaper Index**
- The **Materiality Cascade** flows from engagement → client → practice → system default
- **Follow-Up Items** can be created for flagged issues (narratives only — no financial data stored)
- The **Cross-Tool Convergence Index** shows which accounts were flagged across multiple tools

### 23.3 Engagement Lifecycle

Workspaces follow a three-state workflow:
- **Active** → Running diagnostics, adding follow-up items
- **Completed** → All follow-up items must be resolved before completion
- **Archived** → Terminal state, read-only

### 23.4 Exporting

- **Anomaly Summary Report** — Aggregated diagnostic results with disclaimer
- **Diagnostic Package (ZIP)** — Contains anomaly summary + all tool memos generated during the engagement
- **Convergence CSV** — Cross-tool flagged account analysis

**Important:** All engagement exports include a non-dismissible disclaimer banner. Paciolus is a diagnostic tool, not an audit opinion.

---

## 24. Managing Clients

### 24.1 Adding a Client

1. Click "Portfolio" in navigation (or Cmd+K > "Portfolio")
2. Click "+ New Client"
3. Enter: Client Name, Industry, Fiscal Year End
4. Click "Save Client"

### 24.2 Client Settings

Each client can have custom settings:
- Materiality threshold override
- Industry classification for benchmark comparison (12 supported industries)
- Reporting framework (IFRS or GAAP)
- Practice-level thresholds cascade to client level

---

## 25. Exports & Reports

### 25.1 Export Formats

| Format | Description | Availability |
|--------|-------------|--------------|
| **PDF Memos** | Professional workpaper memoranda with ISA/PCAOB/IFRS/GAAP references, signoff fields, and legal disclaimers | Solo and above |
| **Excel Workpapers** | Multi-tab spreadsheets with structured data, summaries, and analysis tabs | Solo and above |
| **CSV** | Raw data exports (flagged entries, sample selections, anomalies) | Solo and above |
| **Lead Sheets (Excel)** | A–Z categorized workpaper | Solo and above |
| **Financial Statements** | Balance Sheet + Income Statement + Cash Flow Statement | Solo and above |
| **Diagnostic Package (ZIP)** | Complete engagement export with all memos | Professional and above |

### 25.2 Available PDF Memos

Each testing tool generates a professional memorandum:

| Tool | Memo | Standards Referenced |
|------|------|---------------------|
| TB Diagnostics | Diagnostic Report | — |
| Multi-Period | Trend Analysis Memo | — |
| JE Testing | JE Testing Memo | PCAOB AS 2401, ISA 240 |
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

### 25.3 Proof Summary

Each testing tool page includes a **Proof Summary Bar** showing evidence quality across three dimensions: population coverage, test completeness, and data quality. These metrics also appear in the Engagement Workspace's **Proof Readiness** meter.

---

## 26. Customizing Settings

### 26.1 Practice Settings

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

### 26.2 User Profile

**Settings > Profile:** Update display name, email, password.

Email changes require re-verification. A security notification is sent to your previous email address.

### 26.3 Billing Settings

**Settings > Billing:** View current plan, usage metrics, upgrade/downgrade, manage seats, access Stripe portal.

---

## 27. Command Palette

Press **Cmd+K** (Mac) or **Ctrl+K** (Windows) to open the command palette from anywhere in the platform.

### 27.1 What You Can Do

- **Navigate** — Jump to any page (Home, Portfolio, Workspace, Settings, Billing, Practice Settings)
- **Open Tools** — Type a tool name to go directly to it
- **Create** — Start a new workspace
- **Search** — Fuzzy search across all commands with keyword matching

### 27.2 Tier Gating

Commands for tools outside your current plan are visible but will show an upgrade prompt when selected.

### 27.3 Recency

Recently used commands appear higher in results. Recency data is stored in your browser session (Zero-Storage compliant — nothing sent to the server).

---

## 28. Activity History

**Route:** `/history`

Shows a chronological list of all diagnostics run:
- Date/time, truncated filename (first 12 characters), row count
- Balanced status, anomaly count
- **No account names or balances stored** (Zero-Storage compliant)

**Clear History:** Settings > Privacy > "Clear All Activity History" (GDPR Right to Erasure)

---

## 29. Troubleshooting

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

Free plans allow 10 uploads per month; Solo allows 100. Professional and Enterprise plans have unlimited uploads.

---

## 30. FAQ

**Q: Is my data safe?**
A: Yes. Zero-Storage architecture means your financial data is processed in-memory and never stored. See Section 16 and our [Trust page](https://paciolus.com/trust) for details.

**Q: Can I recover results from last week?**
A: "Ephemeral" refers specifically to your uploaded financial data. Workspace metadata — including analysis results, findings summaries, and report history — is retained so you can return to your work. However, line-level detail (individual flagged entries, transaction lists) exists only during your active session. Always export detailed reports to PDF/Excel/CSV before closing the browser.

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
A: Professional and Enterprise plans support multiple seats. Go to Settings > Billing > Manage Seats to add users.

**Q: Can I change my plan?**
A: Yes. Upgrade or downgrade at any time from Settings > Billing. Plan changes take effect immediately for upgrades and at the end of the billing period for downgrades/cancellations.

---

## Contact Support

- **Email:** help@paciolus.com
- **Response time:** 1–2 business days
- **Priority support:** Available on Team and Organization plans
- **Help Center:** [help.paciolus.com](#)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 3.0 | 2026-02-26 | Complete rewrite: 18 tools, 10 file formats, billing plans, engagement workspaces, command palette, data handling guarantees, v2.1.0 |
| 2.0 | 2026-02-06 | Added Tools 2–5 guides, updated navigation, v0.70.0 |
| 1.0 | 2026-02-04 | Initial user guide (Tool 1 only) |

---

*Paciolus v2.1.0 — Professional Audit Intelligence Platform*
