# User Guide

**Document Classification:** Public (End User Documentation)
**Version:** 2.0
**Last Updated:** February 6, 2026
**Product Version:** 0.70.0
**Support:** help@paciolus.com

---

## Welcome to Paciolus

Paciolus is the fastest, most secure audit intelligence platform for financial professionals — five integrated tools, zero data storage. This guide will help you get started and make the most of our suite.

**What makes Paciolus different:**
- **Zero-Storage:** Your data is processed in-memory and never stored on our servers
- **5 Integrated Tools:** TB Diagnostics, Multi-Period Comparison, JE Testing, AP Payment Testing, Bank Reconciliation
- **Professional Reports:** Client-ready PDF, Excel, and CSV outputs with workpaper signoff

**Need help?** Email help@paciolus.com or visit our [Help Center](#)

---

## Table of Contents

1. [Getting Started](#1-getting-started)
2. [Tool 1: Trial Balance Diagnostics](#2-tool-1-trial-balance-diagnostics)
3. [Tool 2: Multi-Period Comparison](#3-tool-2-multi-period-comparison)
4. [Tool 3: Journal Entry Testing](#4-tool-3-journal-entry-testing)
5. [Tool 4: AP Payment Testing](#5-tool-4-ap-payment-testing)
6. [Tool 5: Bank Reconciliation](#6-tool-5-bank-reconciliation)
7. [Managing Clients](#7-managing-clients)
8. [Customizing Settings](#8-customizing-settings)
9. [Activity History](#9-activity-history)
10. [Troubleshooting](#10-troubleshooting)
11. [FAQ](#11-faq)

---

## 1. Getting Started

### 1.1 Creating Your Account

1. Go to [paciolus.com/register](https://paciolus.com/register)
2. Enter your email address
3. Create a strong password (8+ chars, uppercase, lowercase, number, special character)
4. Click "Create Account"
5. **Verify your email** — check for a verification link (required to access tools)
6. Log in at [paciolus.com/login](https://paciolus.com/login)

### 1.2 Email Verification

All diagnostic tools require a verified email address. Without verification, you'll see a "Verify Your Email" banner instead of the tool interface.

**To verify:** Check your inbox for the verification email and click the link. If you don't see it, use the "Resend Verification" button.

### 1.3 Navigating the Platform

The homepage showcases all five tools. Each tool page has a consistent navigation bar:

```
[Logo] | TB Diagnostics | Multi-Period | JE Testing | AP Testing | Bank Rec | [Profile/Sign In]
```

The active tool is highlighted in sage green. Click any tool name to switch.

---

## 2. Tool 1: Trial Balance Diagnostics

**Route:** `/tools/trial-balance`
**Purpose:** Upload a trial balance for instant anomaly detection, ratio analysis, lead sheet mapping, and financial statement generation.

### 2.1 Uploading Your Trial Balance

**Supported formats:** CSV (.csv), Excel (.xlsx, .xls). Max 50 MB.

**Required columns:** Account Name + Debit/Credit (auto-detected).

**Steps:**
1. Drag-and-drop your file onto the upload zone (or click to browse)
2. Paciolus auto-detects columns (green checkmark = detected)
3. If not detected, click "Manual Mapping" to assign columns
4. Processing takes 5-30 seconds depending on file size

### 2.2 Understanding Results

**Summary Card:** Total records, debits, credits, balanced status, variance.

**Classifications:** Accounts grouped into Assets, Liabilities, Equity, Revenue, Expenses using 80+ keyword rules.

**Anomalies:** Flagged items include:
- Abnormal balances (credit balance on asset, debit balance on liability)
- Suspense account detection
- Concentration risk
- Rounding anomalies

**Financial Ratios:** 9 core ratios (Current, Quick, D2E, Gross/Net/Operating margin, ROA, ROE, DSO) plus industry-specific ratios if client industry is set.

**Lead Sheets:** Accounts mapped to A-Z categories for workpaper organization.

**Financial Statements:** Balance Sheet and Income Statement generated from lead sheet groupings with proper sign conventions.

### 2.3 Exporting

- **PDF Report** — Professional "Renaissance Ledger" aesthetic with legal disclaimers
- **Excel Workpaper** — 4-tab structure (Summary, Standardized TB, Anomalies, Ratios)
- **CSV** — Standardized trial balance or anomalies list
- **Lead Sheets** — A-Z workbook
- **Financial Statements** — Balance Sheet + Income Statement (PDF or Excel)

### 2.4 Sensitivity Tuning

Adjust the materiality threshold in real-time to see more or fewer flagged items. Strict mode shows material items only; Lenient shows all.

---

## 3. Tool 2: Multi-Period Comparison

**Route:** `/tools/multi-period`
**Purpose:** Compare up to three trial balance periods side-by-side with variance analysis.

### 3.1 How It Works

1. Upload two files: **Prior Period** and **Current Period**
2. Label each period (e.g., "FY2024", "FY2025")
3. Both files are analyzed independently, then compared
4. For three-way comparison, add a budget period

### 3.2 Movement Types

Each account is classified into one of six movement types:

| Type | Meaning |
|------|---------|
| **NEW** | Account exists in current but not prior |
| **CLOSED** | Account exists in prior but not current |
| **SIGN_CHANGE** | Balance changed from debit to credit (or vice versa) |
| **INCREASE** | Balance increased |
| **DECREASE** | Balance decreased |
| **UNCHANGED** | No change |

### 3.3 Significance Tiers

- **MATERIAL** — Exceeds materiality threshold
- **SIGNIFICANT** — >10% change or >$10K
- **MINOR** — Small changes (<10% and <$10K)

### 3.4 Budget Variance (Three-Way)

When a budget period is included, each account shows:
- Budget amount, actual amount, variance amount
- Variance percentage and significance tier

---

## 4. Tool 3: Journal Entry Testing

**Route:** `/tools/journal-entry-testing`
**Purpose:** Automated GL analysis with 18 tests, Benford's Law, and stratified sampling.

### 4.1 Upload

Upload a General Ledger export (CSV or Excel). Required columns: Entry Number, Date, Account, Debit, Credit. Optional: Description, User, Reference.

### 4.2 Test Battery (18 Tests)

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

**Tier 3 — Advanced (5+ tests):**
- Split transaction patterns
- Sequential anomalies
- Cross-period entries
- Related party indicators
- Fraud keyword detection

### 4.3 Results

- **Composite Score** — Overall risk tier (LOW, MODERATE, ELEVATED, HIGH)
- **Test Result Grid** — Pass/fail status per test with flagged count and flag rate
- **Flagged Entry Table** — Sortable, filterable, paginated (25 per page)

### 4.4 Stratified Sampling

1. Configure sample parameters (confidence level, expected error rate)
2. Preview stratification (strata breakdown by amount range)
3. Execute CSPRNG-based sample selection (PCAOB AS 2315 compliant)

### 4.5 Exporting

- **JE Testing Memo (PDF)** — Professional testing memorandum (PCAOB AS 1215 / ISA 530 references)
- **Flagged Entries (CSV)** — All flagged entries with test details

### 4.6 Threshold Configuration

Go to Settings > Practice to configure test thresholds:
- **Presets:** Conservative, Standard, Permissive
- **Custom:** Adjust individual thresholds per test

---

## 5. Tool 4: AP Payment Testing

**Route:** `/tools/ap-testing`
**Purpose:** Detect duplicate payments, vendor anomalies, and fraud indicators in accounts payable data.

### 5.1 Upload

Upload an AP payment register (CSV or Excel). Key columns: Vendor, Invoice Number, Amount, Payment Date. Optional: Check Number, Description, Payment Method.

Paciolus auto-detects columns using weighted regex patterns (11 column types supported).

### 5.2 Test Battery (13 Tests)

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

### 5.3 Results

- **Composite Score Ring** — Visual risk tier indicator
- **Test Result Grid** — Cards organized by tier
- **Flagged Payment Table** — Sortable by test, vendor, amount, date, severity
- **Data Quality Badge** — Field completeness score

### 5.4 Exporting

- **AP Testing Memo (PDF)** — Professional memorandum (ISA 240 / ISA 500 / PCAOB AS 2401)
- **Flagged Payments (CSV)** — All flagged items with test details, severity, confidence

### 5.5 Threshold Configuration

Settings > Practice > AP Testing section:
- **Presets:** Conservative, Standard, Permissive, Custom
- **Key thresholds:** Round Amount ($), Duplicate Date Window (days), Unusual Amount Sensitivity (sigma), Keyword Sensitivity (%)
- **Toggle tests:** Enable/disable individual tests (Check Gaps, Weekend Payments, etc.)

---

## 6. Tool 5: Bank Reconciliation

**Route:** `/tools/bank-rec`
**Purpose:** Reconcile bank statement transactions against general ledger cash detail.

### 6.1 Upload

Upload two files side-by-side:
- **Left:** Bank Statement (CSV or Excel)
- **Right:** GL Cash Detail (CSV or Excel)

Column detection is automatic. If columns aren't detected confidently, a warning appears.

### 6.2 How Matching Works

Paciolus uses V1 exact matching:
- Matches by amount (with configurable tolerance, default $0.01)
- Greedy algorithm processes largest amounts first
- Each transaction can only match once (one-to-one)
- Date tolerance also configurable

### 6.3 Results

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

### 6.4 Exporting

- **CSV Report** — 4 sections: Matched, Bank-Only, Ledger-Only, Summary

---

## 7. Managing Clients

### 7.1 Adding a Client

1. Click "Portfolio" in navigation
2. Click "+ New Client"
3. Enter: Client Name, Industry, Fiscal Year End
4. Click "Save Client"

### 7.2 Client Settings

Each client can have custom settings:
- Materiality threshold override
- Industry for benchmark comparison
- Practice-level thresholds cascade to client level

---

## 8. Customizing Settings

### 8.1 Practice Settings

**Settings > Practice** provides firm-wide defaults:

**Materiality:**
- Fixed amount, % of Revenue, % of Assets, % of Equity
- Priority chain: session override > client > practice > system default

**JE Testing Thresholds:**
- Conservative / Standard / Permissive presets
- Custom per-test thresholds

**AP Testing Thresholds:**
- Same preset system with 14 configurable fields
- Toggle individual tests on/off

### 8.2 User Profile

**Settings > Profile:** Update display name, email, password.

---

## 9. Activity History

**Route:** `/history`

Shows chronological list of all diagnostics run:
- Date/time, truncated filename (first 12 chars), row count
- Balanced status, anomaly count
- **No account names or balances stored** (Zero-Storage)

**Clear History:** Settings > Privacy > "Clear All Activity History" (GDPR Right to Erasure)

---

## 10. Troubleshooting

### "Columns Not Detected"

Ensure your file has headers in the first row. Use "Manual Mapping" if auto-detection fails.

### "File Too Large"

Max 50 MB. Remove unnecessary columns or split into smaller files.

### "Verify Your Email"

All tools require email verification. Check inbox for verification link, or use "Resend Verification."

### "Out of Balance" Warning

This is expected — Paciolus is designed to diagnose trial balance issues. Review flagged anomalies.

---

## 11. FAQ

**Q: Is my data safe?**
A: Yes. Zero-Storage architecture means your data is processed in-memory and never written to disk. See our [Security Policy](#) for details.

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

**Q: Can I use Paciolus for audit engagements?**
A: Paciolus is a diagnostic tool, not an audit. Use it for review engagements, compilations, and internal diagnostics. See our [Terms of Service](#).

**Q: What file formats are supported?**
A: CSV (.csv) and Excel (.xlsx, .xls) for all tools. Max 50 MB per file.

---

## Contact Support

- **Email:** help@paciolus.com
- **Response time:** <24 hours (business days)
- **Help Center:** [help.paciolus.com](#)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | 2026-02-06 | Added Tools 2-5 guides, updated navigation, v0.70.0 |
| 1.0 | 2026-02-04 | Initial user guide (Tool 1 only) |

---

*Paciolus v0.70.0 — Professional Audit Intelligence Suite*
