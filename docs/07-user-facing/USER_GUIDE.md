# User Guide

**Document Classification:** Public (End User Documentation)  
**Version:** 1.0  
**Last Updated:** February 4, 2026  
**Product Version:** 0.16.0  
**Support:** help@paciolus.com

---

## Welcome to Paciolus

Paciolus is the fastest, most secure way to diagnose trial balance issues—without storing your financial data. This guide will help you get started and make the most of our platform.

**What makes Paciolus different:**
- ✅ **Zero-Storage:** Your trial balance data is processed in-memory and never stored on our servers
- ✅ **30-Second Diagnostics:** Upload, analyze, and export in under a minute
- ✅ **Professional Reports:** Client-ready PDF and Excel outputs

**Need help?** Email help@paciolus.com or visit our [Help Center](#)

---

## Table of Contents

1. [Getting Started](#1-getting-started)
2. [Uploading Your First Trial Balance](#2-uploading-your-first-trial-balance)
3. [Understanding Diagnostic Results](#3-understanding-diagnostic-results)
4. [Managing Clients](#4-managing-clients)
5. [Exporting Reports](#5-exporting-reports)
6. [Customizing Settings](#6-customizing-settings)
7. [Activity History](#7-activity-history)
8. [Troubleshooting](#8-troubleshooting)
9. [FAQ](#9-faq)

---

## 1. Getting Started

### 1.1 Creating Your Account

1. Go to [paciolus.com/register](https://paciolus.com/register)
2. Enter your email address
3. Create a strong password:
   - At least 8 characters
   - One uppercase, one lowercase, one number, one special character
4. Click "Create Account"
5. You'll receive a confirmation email (check spam folder)
6. Log in at [paciolus.com/login](https://paciolus.com/login)

**Already have an account?** [Sign in here](https://paciolus.com/login)

---

### 1.2 Understanding Your Workspace

**When you log in, you'll see:**

```
┌─────────────────────────────────────────────────────────┐
│ Workspace Header                                        │
│ • Welcome message                                       │
│ • Quick stats (assessments today, total clients)        │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Quick Actions                                           │
│ [View History] [Portfolio] [Settings]                   │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Diagnostic Intelligence Zone                            │
│ Drag & drop your trial balance here                    │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Recent History                                          │
│ Last 5 trial balances you've analyzed                  │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Uploading Your First Trial Balance

### 2.1 Supported File Formats

**Paciolus accepts:**
- ✅ CSV files (`.csv`)
- ✅ Excel files (`.xlsx`, `.xls`)
- ✅ Multi-sheet Excel workbooks

**File size limit:** 50 MB

---

### 2.2 Required Columns

Your trial balance file must include these columns (Paciolus will auto-detect):

| Column | Examples | Required |
|--------|----------|----------|
| **Account Name** | "Cash", "Accounts Receivable" | Yes |
| **Debit** | Dollar amounts (debits) | Yes* |
| **Credit** | Dollar amounts (credits) | Yes* |
| **Account Number** | "1000", "1200" | Optional |

*Note: You need *either* separate Debit/Credit columns OR a single Balance column with a type indicator.

**Common column name variations:**
- Account: "Account", "Account Name", "Description", "GL Account"
- Debit: "Debit", "DR", "Debit Amount", "Debit Balance"
- Credit: "Credit", "CR", "Credit Amount", "Credit Balance"

---

### 2.3 Quick Upload (3 Steps)

**Step 1: Drag & Drop**
- Drag your CSV or Excel file onto the upload zone
- Or click "Choose File" to browse

**Step 2: Review Detection**
- Paciolus automatically detects columns
- Green checkmark ✓ = detected correctly
- If columns aren't detected, click "Manual Mapping"

**Step 3: Analyze**
- Click "Analyze Trial Balance"
- Processing takes **5-30 seconds** (depending on file size)
- Results appear instantly

**That's it!** Your trial balance is now analyzed.

---

### 2.4 Manual Column Mapping (If Needed)

**If Paciolus doesn't auto-detect your columns:**

1. Click "Manual Mapping" when prompted
2. Match your file columns to Paciolus fields:
   - **Account Name:** Select your account description column
   - **Debit:** Select your debit balance column
   - **Credit:** Select your credit balance column
3. Click "Save Mapping"

**Example:**
```
Your File:          →   Paciolus Fields:
"GL Account"        →   Account Name
"DR Balance"        →   Debit
"CR Balance"        →   Credit
```

**Tip:** Paciolus remembers your mapping for next time!

---

### 2.5 Multi-Sheet Excel Workbooks

**If your file has multiple sheets:**

1. Upload the Excel file
2. Paciolus shows a "Workbook Inspector"
3. Select which sheets to analyze:
   - ☑ Consolidated (1,547 rows)
   - ☑ Entity A (823 rows)
   - ☐ Notes (skip)
4. Choose "Analyze Individually" or "Consolidate"
5. Click "Proceed"

**Consolidate:** Combines all selected sheets into one diagnostic (useful for multi-entity trial balances).

---

## 3. Understanding Diagnostic Results

### 3.1 Summary Card

```
┌─────────────────────────────────────┐
│ Trial Balance Summary                │
│                                      │
│ Total Records: 1,547                │
│ Total Debits: $25,000,000.00        │
│ Total Credits: $25,000,000.00       │
│                                      │
│ Status: ✓ BALANCED                  │
│ Variance: $0.00                     │
└─────────────────────────────────────┘
```

**What this means:**
- **Total Records:** Number of rows in your trial balance
- **Debits/Credits:** Sum of all debit/credit balances
- **Balanced:** ✓ if debits = credits, ⚠ if out of balance
- **Variance:** Difference between debits and credits (should be $0.00)

---

### 3.2 Classifications

```
┌─────────────────────────────────────┐
│ Account Classifications              │
│                                      │
│ Assets: 542 accounts                │
│ Liabilities: 234 accounts           │
│ Equity: 123 accounts                │
│ Revenue: 345 accounts               │
│ Expenses: 303 accounts              │
└─────────────────────────────────────┘
```

**How Paciolus classifies:**
- Uses 80+ keyword rules (e.g., "Accounts Receivable" → Asset)
- 95% accuracy rate
- You can override classifications if needed

---

### 3.3 Anomalies

**Anomalies are potential issues** Paciolus detected:

```
┌──────────────────────────────────────────────────┐
│ Accounts Receivable                              │
│ Account #1200                                    │
│                                                  │
│ ⚠ ABNORMAL CREDIT BALANCE                       │
│ Balance: -$15,000.00 CR                         │
│                                                  │
│ Why flagged: A/R normally has a debit balance   │
│ (customers owe you money). A credit balance may  │
│ indicate overpayment or misclassification.       │
│                                                  │
│ Severity: HIGH    Material: YES ($15K > $500)   │
└──────────────────────────────────────────────────┘
```

**Anomaly Types:**
1. **Abnormal Credit Balance** — Asset account with credit balance
2. **Abnormal Debit Balance** — Liability account with debit balance
3. **Large Balance** — Account balance exceeds materiality threshold

**Material vs. Immaterial:**
- **Material:** Exceeds your materiality threshold (default: $500)
- **Immaterial:** Below threshold (may still be worth investigating)

---

### 3.4 Sensitivity Toolbar (Tuning Results)

**Adjust thresholds in real-time:**

```
┌─────────────────────────────────────────┐
│ Materiality Threshold: [$500    ]      │
│ Display Mode: ○ Strict  ● Lenient       │
└─────────────────────────────────────────┘
```

**Materiality Threshold:**
- Increase to see fewer anomalies (e.g., $5,000 = big issues only)
- Decrease to see more anomalies (e.g., $100 = catch everything)

**Display Mode:**
- **Strict:** Material anomalies only
- **Lenient:** All anomalies (material + immaterial)

**Tip:** Start with Strict, then switch to Lenient for deep dive.

---

## 4. Managing Clients

### 4.1 Adding a Client

**If you're a fractional CFO or manage multiple clients:**

1. Click "Portfolio" in the navigation
2. Click "+ New Client" button
3. Fill in client details:
   - **Client Name:** "Acme Corp"
   - **Industry:** Technology
   - **Fiscal Year End:** 12-31
4. Click "Save Client"

**Why add clients?**
- Organize your work
- Track which diagnostics belong to which client
- Set client-specific settings (future: custom materiality formulas)

---

### 4.2 Client Portfolio View

```
┌─────────────────────────────────────────────────┐
│ Your Clients (15)                                │
├─────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────┐   │
│ │ Acme Corp                                 │   │
│ │ Technology | FYE: 12-31                   │   │
│ │ Last Assessment: 2 days ago               │   │
│ │ [View] [Edit] [Delete]                    │   │
│ └──────────────────────────────────────────┘   │
│                                                 │
│ ┌──────────────────────────────────────────┐   │
│ │ BizFlow LLC                               │   │
│ │ Professional Services | FYE: 06-30        │   │
│ │ Last Assessment: 1 week ago               │   │
│ │ [View] [Edit] [Delete]                    │   │
│ └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

---

## 5. Exporting Reports

### 5.1 PDF Diagnostic Report

**Professional, client-ready PDF:**

1. After analysis completes, click "Export Diagnostic Summary"
2. Choose "PDF Report"
3. File downloads automatically: `Acme_Corp_Diagnostic_20260204.pdf`

**What's included:**
- Executive summary (balanced status, totals)
- Account classifications breakdown
- Flagged anomalies with descriptions
- Legal disclaimer (not an audit, diagnostic only)
- Paciolus branding (Oat & Obsidian theme)

**File size:** ~200-500 KB (prints beautifully)

---

### 5.2 Excel Workpaper

**Detailed 4-tab Excel file:**

1. Click "Export Diagnostic Summary"
2. Choose "Excel Workpaper"
3. File downloads: `Acme_Corp_Diagnostic_20260204.xlsx`

**Tabs:**
1. **Summary** — High-level overview
2. **Standardized Trial Balance** — Cleaned, formatted trial balance
3. **Flagged Anomalies** — All detected issues with details
4. **Key Financial Ratios** — Current ratio, quick ratio, debt-to-equity, etc.

**Use case:** Attach to engagement letter, client review session

---

### 5.3 Zero-Storage Reminder

**Important:** Once you close the browser tab, your diagnostic results are gone forever (Zero-Storage architecture).

**Always export** if you need to keep results:
- ✅ Export to PDF (save locally)
- ✅ Export to Excel (save locally)
- ❌ Don't rely on Paciolus to "retrieve" results later

**We store only aggregate metadata:**
- You analyzed a file with 1,547 rows
- It was balanced with 10 anomalies
- **NOT** which accounts had issues or specific balances

---

## 6. Customizing Settings

### 6.1 Default Materiality Threshold

**Set your default threshold:**

1. Click "Settings" → "Preferences"
2. Update "Default Materiality Threshold": `$500`
3. Click "Save"

**This applies to all future diagnostics** (you can override per-analysis).

---

### 6.2 Materiality Formulas (Advanced)

**For power users:**

1. Settings → "Materiality Formulas"
2. Choose formula type:
   - **Fixed Amount:** $500 (simple)
   - **% of Revenue:** 1% of total revenue
   - **% of Assets:** 0.5% of total assets
   - **% of Equity:** 2% of total equity
3. Save formula

**Example:** If formula is "1% of revenue" and client has $1M revenue, threshold = $10,000 automatically.

---

## 7. Activity History

### 7.1 Viewing Past Diagnostics

**Access your audit trail:**

1. Click "History" in navigation
2. See chronological list of all diagnostics

```
┌─────────────────────────────────────────────────┐
│ Activity History                                │
├─────────────────────────────────────────────────┤
│ Feb 4, 2026, 10:30 AM                           │
│ ClientABC_Q4... (1,547 rows)                    │
│ ✓ Balanced | 10 anomalies                      │
└─────────────────────────────────────────────────┘
│ Feb 3, 2026, 3:15 PM                            │
│ XYZ_Trial_Ba... (892 rows)                      │
│ ⚠ Out of Balance | Variance: $250.00           │
└─────────────────────────────────────────────────┘
```

**What you see (metadata only):**
- Date/time
- First 12 characters of filename (privacy protection)
- Row count, balanced status, anomaly count

**What you DON'T see:**
- Account names or balances (Zero-Storage)
- Specific anomaly details

---

### 7.2 Clearing History (GDPR Right to Erasure)

**Delete all activity logs:**

1. Settings → "Privacy"
2. Click "Clear All Activity History"
3. Confirm deletion

**Warning:** This cannot be undone. All activity metadata is permanently deleted.

---

## 8. Troubleshooting

### 8.1 "Columns Not Detected"

**Problem:** Paciolus can't find Account/Debit/Credit columns

**Solutions:**
1. Check your file has headers in the first row
2. Use "Manual Mapping" to specify columns
3. Ensure columns have data (not empty)

**Example fix:**
```
Before (no headers):
Cash, 50000, 0
A/R, 25000, 0

After (with headers):
Account, Debit, Credit
Cash, 50000, 0
A/R, 25000, 0
```

---

### 8.2 "File Too Large"

**Problem:** File exceeds 50 MB limit

**Solutions:**
1. Split large files into smaller chunks
2. Remove unnecessary columns (notes, descriptions)
3. Export only active accounts (exclude zero-balance)

---

### 8.3 "Out of Balance" Warning

**Problem:** Debits ≠ Credits

**This is expected!** Paciolus is designed to **diagnose** trial balance issues.

**Next steps:**
1. Review flagged anomalies
2. Investigate misclassifications
3. Check source data for errors

---

## 9. FAQ

### Q: Is my data safe?

**A:** Yes. Paciolus uses **Zero-Storage architecture**—your trial balance is processed in-memory and never written to disk or database. See our [Security Policy](#) for details.

---

### Q: Can I recover a diagnostic I did last week?

**A:** No. Due to Zero-Storage, we don't retain your trial balance data or detailed diagnostic results. Always export to PDF/Excel before closing the browser tab.

---

### Q: What if Paciolus makes a mistake?

**A:** Paciolus is a diagnostic tool, not an audit. Always review flagged anomalies with professional judgment. Our classification accuracy is 95%, but edge cases exist. See our [Terms of Service](#) for full disclaimers.

---

### Q: Can I use Paciolus for audit engagements?

**A:** Paciolus is **NOT** an audit tool. It does not meet GAAS, PCAOB, or ISA audit standards. Use it for review engagements, compilations, and internal diagnostics only.

---

### Q: How do I cancel my subscription?

**A:** Settings → "Billing" → "Cancel Subscription". No fee, cancellation takes effect at end of billing period.

---

### Q: Do you offer team plans?

**A:** Yes! Team plans start at $249/month for 5 users. Contact sales@paciolus.com for details.

---

### Q: Can I white-label Paciolus for my CPA firm?

**A:** Enterprise customers can customize branding (logo, colors, domain). Contact sales@paciolus.com for a demo.

---

## Contact Support

**Need help?**
- **Email:** help@paciolus.com
- **Response time:** \u003c24 hours (business days)
- **Help Center:** [help.paciolus.com](#)
- **Video Tutorials:** [youtube.com/paciolus](#)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-04 | Initial user guide |

---

*Paciolus v0.16.0 — Surgical Precision for Trial Balance Diagnostics*
