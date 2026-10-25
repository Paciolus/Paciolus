# Zero-Storage Architecture

**Version:** 2.2
**Document Classification:** Public
**Effective Date:** February 26, 2026
**Last Updated:** February 27, 2026
**Owner:** Chief Technology Officer
**Review Cycle:** Quarterly
**Next Review:** May 26, 2026

---

## Executive Summary

**Uploaded files are processed in memory and not kept after analysis.** Paciolus does save user accounts, client metadata, a summary of each analysis, the names of accounts a tool flagged, practitioner-entered engagement content and — for up to 48 hours — reports a customer shares by link. (Sprint 841, 2026-10-24: this document no longer describes the model as "Zero-Storage"; that word read as a promise about all data. The filename is kept so links do not break.)

**Key Points:**
- ✅ **What Is Stored:** User credentials, client metadata, aggregate diagnostic metadata (category totals, ratios, row counts), and workpaper conclusions the practitioner types in themselves (see §2.2)
- ❌ **What Is Not Kept:** Raw uploaded files, and the line-level balances and transaction details **parsed from an upload**. Account names parsed from an upload are kept only when a tool flags the account (name only, no amount)
- 🔒 **Security Benefit:** A breach exposes no uploaded trial balance rows — they are not written to disk or the database; summaries and engagement entries are in scope
- ⚖️ **Compliance Impact:** Simplified GDPR, CCPA, SOC 2 requirements
- 💼 **Business Value:** Competitive differentiator for privacy-conscious financial professionals

This document explains the technical implementation, security advantages, and compliance implications of Paciolus's Zero-Storage architecture.

---

## Table of Contents

1. [Core Principle](#1-core-principle)
2. [What Is Stored vs. What Is Not](#2-what-is-stored-vs-what-is-not)
3. [Technical Implementation](#3-technical-implementation)
4. [Security Advantages](#4-security-advantages)
5. [Compliance Implications](#5-compliance-implications)
6. [Competitive Differentiation](#6-competitive-differentiation)
7. [User Experience](#7-user-experience)
8. [Audit Trail](#8-audit-trail)
9. [Limitations and Trade-offs](#9-limitations-and-trade-offs)
10. [Verification and Assurance](#10-verification-and-assurance)

---

## 1. Core Principle

### 1.1 Definition

**Zero-Storage** means that Paciolus **never persists the uploaded file, nor the trial balance itself** — no complete row set, and no line-level balance-by-account ledger — to any disk, database, or cloud storage system. Parsing happens in ephemeral memory and the parsed data is destroyed when analysis completes.

What the term guarantees, stated plainly: **your client's ledger is never warehoused.** A breach of our database exposes diagnostic metadata and the practitioner's own conclusions — not the underlying trial balance.

What the term does **not** guarantee is that no account name or figure ever reaches the database. Four narrow classes are deliberately retained, and §2.1 and §2.2 below enumerate them exhaustively:

| Retained class | Example | Where |
|---|---|---|
| **Aggregate metadata** | category totals, financial ratios, row counts | `diagnostic_summaries`, `activity_logs` |
| **Flagged account identifiers** | the account *names* a tool flagged — identifiers only, never their balances | `tool_runs.flagged_accounts` |
| **Single computed figures** | one ISA 520 comparison actual and its variance, not the population behind it | `analytical_expectations` |
| **Practitioner-entered workpaper entries** | an ISA 450 misstatement line the auditor typed themselves | `uncorrected_misstatements` |

The fourth class exists because ISA 450 and ISA 520 workpapers *are* the auditor's own record of decisions rather than a derivative of tool output; where such an entry contains an account name and an amount, the practitioner typed those characters.

The second and third classes are upload-derived and are the reason this section is worded as a positive enumeration rather than an absolute exclusion. Earlier revisions of this document claimed that no account name parsed from an upload was ever stored. That was not true once tool-run flagging and ISA 520 actual-capture shipped, and the surrounding sections contradicted it. Stating what is retained — rather than asserting what never is — is the only version of this claim that stays true as features ship.

### 1.2 Philosophy

Traditional accounting platforms operate on a "store first, process later" model. Paciolus inverts this:

| Traditional SaaS | Paciolus Zero-Storage |
|------------------|----------------------|
| Upload → Store → Process → Display | Upload → Process → Display → Discard |
| Data persists indefinitely | Raw data exists only during analysis; aggregate metadata retained |
| Server-side financial data | Client-side data ownership |
| Breach exposes all historical data | Breach exposes no line-level financial data |

### 1.3 Terminology Clarity

> **"Zero-storage" does not mean "no storage for all data."**

| Term | Meaning |
|------|---------|
| **Uploads not kept** | Raw uploaded files, and the individual balances and transaction details parsed from them, are not written to disk or the database. Exceptions: flagged account names (no amounts) are saved with the analysis summary; a previewed file is held in memory for up to 10 minutes; shared report files are held in Cloudflare R2 for up to 48 hours |

| **Practitioner-entered workpaper entry** | A conclusion the auditor types themselves (ISA 450 misstatement, ISA 520 expectation). Persisted for the engagement lifecycle, soft-deletable, and outside the Zero-Storage exclusion because it is the auditor's own record rather than extracted client data |
| **Aggregate metadata retention** | Separate and controlled persistence of computed summaries (category totals, ratios, row counts) subject to configurable retention windows (see Section 2.4) |

Paciolus maintains a minimal metadata database for authentication, client organization, diagnostic history (aggregates only), engagement workflow, and billing. These operational data classes are governed by the retention schedule in Section 2.4 and the canonical retention table in the Privacy Policy (Section 4.1).

### 1.4 Scope

Zero-Storage applies to:
- ✅ Raw uploaded files in all 10 supported formats (CSV, XLSX, XLS, TSV, TXT, OFX, QBO, IIF, PDF, ODS — not written to disk; uploads below the 110 MB request cap stay in memory since Sprint 840)
- ✅ Line-level account names and balances (not persisted)
- ✅ Individual transaction details (not persisted)
- ✅ Ledger entries (not persisted)
- ✅ Financial reports (except user-downloaded PDFs/Excel)

Zero-Storage does **not** apply to:
- User authentication credentials (hashed passwords)
- Client metadata (name, industry, fiscal year end)
- Aggregate diagnostic metadata (category totals, financial ratios, row counts)
- Engagement metadata and tool run records (narrative-only, no financial data)
- Ephemeral tool working state (adjustments, currency rates — DB-backed with TTL expiration and financial key stripping)
- Subscription and billing lifecycle events (Stripe references only, no payment card data)
- User preferences and settings

---

## 2. What Is Stored vs. What Is Not

### 2.1 Data Classification Matrix

| Data Type | Storage Status | Retention | Example |
|-----------|----------------|-----------|---------|
| **Raw Trial Balance Rows** | ❌ Not Kept | The request only | "Cash: $50,000 DR" |
| **Account Names Parsed From an Upload** | ⚠️ Only if flagged | Name only, with the analysis summary (`tool_runs.flagged_accounts`) | "Accounts Receivable", flagged by a test |
| **Raw Uploaded Files** | ❌ Not Kept | The request only (preview: up to 10 minutes in memory) | "ClientXYZ_Q4_2024.xlsx" |
| **Shared Report Files** | ✅ Stored (Cloudflare R2) | Up to 48 hours, then deleted | A memo PDF shared by link |
| **Account Names Typed by the Practitioner** | ✅ Stored | Engagement lifecycle (soft-delete) | An ISA 450 misstatement line naming "Accrued Payroll, CR 12,400" |
| **User Credentials** | ✅ Stored | Until account deletion | "user@example.com, bcrypt hash" |
| **Client Metadata** | ✅ Stored | Until deletion | "Acme Corp, Technology, 12-31 FYE" |
| **Diagnostic Summaries** | ✅ Stored (aggregates) | 365 days (1 year) | "47 rows, balanced, 3 anomalies, total_assets: $1.2M" |
| **Engagement Metadata** | ✅ Stored (metadata only) | Until account deletion | "Period: Q4 2025, materiality: $50K, status: active" |
| **Tool Run Records** | ✅ Stored (metadata + flagged account names) | Until account deletion | "Revenue Testing, score: 85, flagged: ['Accrued Payroll', 'Deferred Revenue']" — identifiers only, no balances |
| **Uncorrected Misstatements (ISA 450)** | ✅ Stored (practitioner-entered) | Engagement lifecycle — **archived, not erased**, on delete (§2.3) | "Accrued Payroll CR 12,400; judgmental; net income impact (12,400)" |
| **Analytical Expectations (ISA 520)** | ✅ Stored (expectation + single actual) | Engagement lifecycle — **archived, not erased**, on delete (§2.3) | "Expected revenue 4.2M ±5%; actual 4.47M; variance 270K" |
| **Admin Audit Log Details** | ✅ Stored | Append-only | "credit issued, amount_cents: 5000" — our billing actions, never client data |
| **Activity Feed Summaries** | ✅ Stored (caller-supplied) | Until account deletion | Free-form blob, capped at 2,000 characters |
| **Follow-Up Items** | ✅ Stored (narratives only) | Until account deletion | "Investigate revenue timing — no amounts or account numbers" |
| **Subscription Records** | ✅ Stored | Until account deletion | "Tier: professional, Stripe ref: sub_xxx" |
| **Billing Events** | ✅ Stored (append-only) | Until account deletion | "subscription_created, tier: professional" |
| **User Settings** | ✅ Stored | Until account deletion | "Materiality: $500, Theme: Dark" |

### 2.2 Controlled Storage Exceptions

Paciolus maintains a **minimal metadata database** for essential business functions:

#### Users Table
**Purpose:** Authentication and authorization  
**Fields Stored:**
- User ID (UUID)
- Email address (for login)
- Password hash (bcrypt, salted)
- Account creation date
- Last login timestamp
- User preferences (JSON: materiality defaults, UI settings)

**What Is NOT Stored:**
- Financial data of any kind
- Client financial information
- Trial balance results

#### Clients Table
**Purpose:** Organizational metadata for fractional CFOs managing multiple entities  
**Fields Stored:**
- Client ID (UUID)
- User ID (foreign key, multi-tenant isolation)
- Client company name
- Industry classification (12 standard categories)
- Fiscal year end (MM-DD format)
- Created/updated timestamps
- Client-specific settings (JSON: materiality formulas)

**What Is NOT Stored:**
- Trial balance data for the client
- Account balances or transactions
- Audit results or anomaly details

#### Activity Logs Table
**Purpose:** User activity history for workflow tracking (GDPR/CCPA compliant)
**Archival:** Soft-delete (see Section 2.3)
**Fields Stored:**
- Activity ID (integer, primary key)
- User ID (foreign key)
- **Filename hash** (SHA-256, irreversible)
- Filename display (first 8 characters + ellipsis)
- Timestamp
- **Aggregate statistics only (Numeric(19,2) precision):**
  - Row count (integer)
  - Total debits (Numeric sum only, no line-level detail)
  - Total credits (Numeric sum only, no line-level detail)
  - Materiality threshold used (Numeric)
  - Balanced status (boolean)
  - Anomaly count (integer only, no specifics)
  - Material anomaly count (integer)
  - Immaterial anomaly count (integer)
  - Sheet count (integer, for multi-sheet workbooks)

**What Is NOT Stored:**
- Original filename (hashed for privacy)
- File contents or raw data
- Specific account names or balances
- Individual transaction details
- Anomaly descriptions (which accounts had issues)

#### Diagnostic Summaries Table
**Purpose:** Aggregate diagnostic metadata for historical comparison and trend analysis
**Archival:** Soft-delete (see Section 2.3)
**Fields Stored:**
- Summary ID (integer, primary key)
- User ID (foreign key)
- Client ID (foreign key, optional)
- **Aggregate category totals (Numeric(19,2) precision, no line-level detail):**
  - Total assets, current assets, inventory
  - Total liabilities, current liabilities, total equity
  - Total revenue, cost of goods sold, total expenses, operating expenses
  - Total debits, total credits, materiality threshold
- **Financial ratios (Float, calculated):**
  - Current ratio, quick ratio, debt-to-equity, gross margin
  - Net profit margin, operating margin, return on assets, return on equity
- **Diagnostic metadata:**
  - Row count (integer), balanced status (boolean), anomaly count (integer)
  - Period date, period type (monthly/quarterly/annual), period label
  - Filename hash (SHA-256), filename display (first 8 chars)
- Timestamp

**What Is NOT Stored:**
- Individual account names or balances
- Line-level trial balance rows
- Specific transaction details
- Raw file contents

#### Tool Sessions Table
**Purpose:** Ephemeral working state for multi-step tool workflows (e.g., adjusting entries, currency rates)
**Archival:** Physical deletion (not soft-deleted — ephemeral by design)
**Fields Stored:**
- User ID (foreign key)
- Tool name (string)
- Session data (JSON working state — financial keys stripped before persistence)
- Created/updated timestamps (TTL computed from updated_at)

**TTL Policy:**
- Adjustments: 1 hour
- Currency rates: 2 hours
- Default: 1 hour

**Zero-Storage enforcement for tool sessions:**
- **Financial key stripping:** Before writing to the database, an allowlist filter removes all financial amounts, debit/credit lines, and monetary totals. Only structural metadata (entry IDs, descriptions, status, preparer names) survives persistence.
- **Startup sanitization:** On server start, all existing sessions are re-scanned and any legacy financial keys are stripped.
- **Lazy TTL:** Expired sessions are deleted on next read attempt.
- **Startup cleanup:** Bulk deletion of all sessions exceeding their TTL.

**Important:** Tool sessions are ephemeral by design — they expire automatically via TTL and are cleaned up at server startup. They are **not** permanent storage.

#### Engagements Table
**Purpose:** Diagnostic workspace metadata for organizing multi-tool analysis workflows
**Fields Stored:**
- Engagement ID (integer, primary key)
- Client ID (foreign key)
- Period start/end (date range)
- Status (active/completed/archived)
- Materiality configuration (basis, percentage, amount, performance factor, trivial threshold)
- Created by / completed by (user foreign keys)
- Timestamps

**What Is NOT Stored:**
- Financial data of any kind
- Trial balance results or account balances
- Anomaly details or line-level findings

#### Tool Runs Table
**Purpose:** Record of individual tool executions within an engagement
**Archival:** Soft-delete (see Section 2.3)
**Fields Stored:**
- Tool run ID (integer, primary key)
- Engagement ID (foreign key)
- Tool name (enum — 13 tools)
- Run number, status (completed/failed)
- Composite score (float, 0-100)
- Flagged accounts (JSON list of account name strings only — no amounts)
- Run timestamp

**What Is NOT Stored:**
- Financial amounts or balances
- Line-level test results
- Raw uploaded data

#### Follow-Up Items Table
**Purpose:** Narrative-only anomaly tracker tied to an engagement
**Archival:** Soft-delete (see Section 2.3)
**Fields Stored:**
- Item ID (integer, primary key)
- Engagement ID (foreign key)
- Description (narrative text only)
- Tool source (which tool generated the finding)
- Disposition (open/resolved/deferred)
- Auditor notes (free text)

**What Is NOT Stored:**
- Account numbers, financial amounts, PII
- Specific account balances or transaction details

#### Subscriptions Table
**Purpose:** Links a user to their billing state
**Fields Stored:**
- User ID (foreign key)
- Tier (free/solo/team/enterprise), status, billing interval
- Stripe customer ID, Stripe subscription ID (references only)
- Seat count, additional seats
- Period start/end, cancel-at-period-end flag
- Timestamps

**What Is NOT Stored:**
- Payment card details (handled entirely by Stripe)
- Financial amounts beyond subscription pricing metadata

#### Billing Events Table
**Purpose:** Append-only billing lifecycle log
**Fields Stored:**
- User ID (nullable foreign key)
- Event type (10 lifecycle types: trial_started, subscription_created, etc.)
- Tier, interval, seat count at time of event
- Metadata JSON (e.g., cancellation reason, promo code)
- Created timestamp

**What Is NOT Stored:**
- Payment amounts, card details, invoice line items (Stripe handles all of these)

#### Uncorrected Misstatements Table
**Purpose:** The practitioner's Summary of Uncorrected Misstatements workpaper (ISA 450 / AU-C 450)
**Fields Stored:**
- Engagement ID (foreign key), source type and narrative source reference
- Description of the misstatement (practitioner-authored)
- Accounts affected — JSON list of `{account, debit_credit, amount}` **as typed by the practitioner**
- ISA 450 §A6 classification (factual / judgmental / projected) and §A12–A15 disposition
- Signed financial-statement impact on net income and net assets
- Created/updated timestamps, soft-delete marker

**Why this is outside the Zero-Storage exclusion:** every value is the auditor's own documented conclusion, entered by hand. Nothing here is parsed from an uploaded file. Adjusting entries (`backend/adjusting_entries.py`) and sample projections remain in-memory and are never persisted. Architectural decision and ISA mapping: [`isa-450-coverage.md`](isa-450-coverage.md).

**What Is NOT Stored:**
- The trial balance the misstatement was identified from
- Any automatic aggregation of tool output into this table

#### Analytical Expectations Table
**Purpose:** The practitioner's independent expectation and its comparison result (ISA 520 / AS 2305)
**Fields Stored:**
- Engagement ID (foreign key), procedure target type and identifier
- Expected value **or** expected range, precision threshold (amount or percent)
- Corroboration basis text and tags (ISA 520 §A12–A13)
- Practitioner notes
- Comparison result: actual value, variance amount, within-threshold indicator
- Created/updated timestamps, soft-delete marker

**Why this is outside the Zero-Storage exclusion:** the expectation is the auditor's own judgement, and the stored result is a single comparison figure, not the population it was computed over. Underlying flux line items and ratio inputs remain ephemeral. ISA mapping: [`isa-520-coverage.md`](isa-520-coverage.md).

**What Is NOT Stored:**
- The flux line items, ratio inputs, or trial balance rows the actual was derived from

#### Admin Audit Logs Table
**Purpose:** Append-only record of internal administrative actions (impersonation, tier changes, credits, refunds)
**Fields Stored:**
- Admin user ID, action type, target org / target user IDs
- Timestamp, IP address
- `details_json` — action-specific payload. **For billing actions this includes monetary amounts** (e.g. `{"amount_cents": 5000, "reason": "..."}` for a credit or refund).

**Why this is outside the Zero-Storage exclusion:** the amounts describe *our own* billing actions against a customer's subscription, not the customer's client data. No trial balance figure reaches this table.

**What Is NOT Stored:**
- Card details or any payment instrument (Stripe holds these)
- Any client financial data from an upload

#### Tool Activities Table
**Purpose:** Unified activity feed for the workspace timeline
**Fields Stored:**
- User ID, tool name, engagement ID, record count
- Display-truncated filename (not the file)
- `summary_json` — a caller-supplied summary blob, capped at 2,000 characters

**Why this is called out:** `summary_json` is free-form and supplied by the client application rather than fixed by a schema, so its contents are bounded by length but not by type. It is listed here so the exception is disclosed rather than implied.

**What Is NOT Stored:**
- The uploaded file or any row set from it

### 2.3 Soft-Delete Archival Model

Paciolus uses a **soft-delete archival model** for audit-sensitive records. Five tables are protected:

1. **Activity Logs** — aggregate summaries of analyses
2. **Diagnostic Summaries** — aggregate metadata
3. **Tool Runs** — tool execution records
4. **Follow-Up Items** — narrative anomaly trackers
5. **Follow-Up Item Comments** — threaded discussion on follow-up items

**How it works:**
- Each protected table has `archived_at`, `archived_by`, and `archive_reason` columns
- An ORM-level `before_flush` guard raises `AuditImmutabilityError` on any `db.delete()` call for protected models
- All read paths filter `archived_at IS NULL` to exclude archived records from active queries
- Retention cleanup (365-day window) sets `archived_at` rather than physically deleting rows
- Archived records remain available for compliance or legal purposes

**Purpose:** Ensures an immutable audit trail while supporting configurable retention windows.

### 2.4 Storage Duration

| Category | Retention Period | Deletion Trigger |
|----------|------------------|------------------|
| **Raw trial balance data** | **0 seconds** | **Immediate garbage collection** |
| **Uploaded files** | **0 seconds** | **Immediate garbage collection** |
| Tool sessions | 1–2 hours | TTL expiration + startup cleanup |
| User credentials | Indefinite | User account deletion request |
| Client metadata | Indefinite | User deletes client record |
| User settings | Indefinite | User account deletion request |
| Activity logs | 365 days (1 year) | Automatic archival or user deletion request |
| Diagnostic summaries | 365 days (1 year) | Automatic archival or user deletion request |
| Engagement metadata | Indefinite | User deletes engagement or account |
| Tool run records | Indefinite | User deletes engagement or account |
| Follow-up items | Indefinite | User deletes engagement or account |
| Subscription records | Indefinite | User account deletion request |
| Billing events | Indefinite | User account deletion request |

---

## 3. Technical Implementation

### 3.1 In-Memory Processing Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    USER'S BROWSER                            │
│                                                              │
│  1. User uploads file (CSV/Excel/TSV/OFX/ODS/PDF/IIF/etc.)  │
│  2. File sent via HTTPS to Paciolus API                     │
│                                                              │
└──────────────────────┬───────────────────────────────────────┘
                       │ HTTPS POST /audit/trial-balance
                       │ (multipart/form-data)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    PACIOLUS API SERVER                       │
│                                                              │
│  3. FastAPI receives file in BytesIO buffer (memory)         │
│  4. Format-specific parser loads into DataFrame (memory)     │
│  5. Audit engine processes data:                            │
│     - Classify accounts (heuristics)                         │
│     - Detect anomalies (debit/credit violations)             │
│     - Calculate materiality (user threshold)                 │
│  6. Generate summary statistics (aggregates only)            │
│  7. Return JSON response to client                           │
│  8. BytesIO buffer cleared (Python gc.collect())             │
│  9. DataFrame destroyed (memory freed)                       │
│                                                              │
└──────────────────────┬───────────────────────────────────────┘
                       │ HTTPS Response (JSON)
                       │ { "balanced": true, "anomalies": 3, ... }
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    USER'S BROWSER                            │
│                                                              │
│  10. React renders results in UI (ephemeral state)           │
│  11. User can download PDF/Excel (server-generated, streamed)│
│  12. Session ends → All data cleared from browser memory     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Key Observations:**
- No raw file data written to disk; aggregate metadata persisted to database
- File exists in server memory for <5 seconds (typical analysis time)
- Results exist only in React component state (browser RAM)
- Access tokens held in React `useRef` (in-memory only); refresh tokens in HttpOnly `paciolus_refresh` cookie; CSRF tokens are stateless HMAC credentials derived from auth responses — none written to session storage or local storage

### 3.2 Streaming Processing for Large Files

For trial balances with 50,000+ rows, Paciolus uses **chunked streaming** to avoid memory overload:

```python
# audit_engine.py
def audit_trial_balance_streaming(file_buffer, chunk_size=10000):
    """
    Process large trial balances in memory-efficient chunks.
    Each chunk is processed and discarded before the next loads.
    """
    for chunk in pd.read_csv(file_buffer, chunksize=chunk_size):
        # Process chunk
        anomalies = detect_anomalies(chunk)
        # Aggregate results
        aggregate_stats(anomalies)
        # Explicitly clear chunk
        del chunk
        gc.collect()  # Force garbage collection
    
    return aggregated_results  # Summary only, no raw data
```

**Memory footprint**: Maximum 10,000 rows loaded at any time, regardless of file size.

### 3.3 Memory Cleanup

Raw financial data is purged from RAM immediately after processing via the `memory_cleanup()` context manager:

```python
from shared.helpers import memory_cleanup

# Every upload route wraps processing in this context manager
with memory_cleanup():
    df = parse_file(buffer)       # Load into memory
    results = analyze(df)         # Process
    # ... return results to client
# On exit (normal or exception): gc.collect() is called automatically
```

The `memory_cleanup()` context manager guarantees `gc.collect()` runs in a `finally` block, ensuring cleanup even if an exception occurs during processing. This pattern is applied to all file upload routes (TB analysis, journal entry testing, bank reconciliation, sampling, three-way match, AR aging, currency conversion, and all testing tool routes).

### 3.4 Export Mechanism (PDF/Excel)

When users export diagnostic reports:

1. **Backend generates PDF/Excel in BytesIO buffer** (memory, not disk)
2. **Streams to user via HTTP chunked transfer** (8KB chunks)
3. **Buffer cleared immediately after streaming completes**
4. **User's browser saves file locally** (user's device, not Paciolus servers)

**Key Point:** A downloaded export is not saved by Paciolus. **Exception — share links:** when a customer shares a report by link, the generated file is stored, encrypted at rest by the provider, in Cloudflare R2 (`paciolus-exports`), keyed by a hash of the share token, for 24 hours (Professional) or 48 hours (Enterprise), and deleted when the share expires or is revoked (the cleanup removes the database row only after R2 confirms deletion — Sprint 840).

---

## 4. Security Advantages

### 4.1 Breach Impact Analysis

| Scenario | Traditional SaaS | Paciolus Zero-Storage |
|----------|------------------|----------------------|
| **Database breach** | All historical financial data exposed | Only user credentials and aggregate metadata exposed (no line-level financial data) |
| **Server compromise** | Attacker gains access to stored files | No raw files exist on server to access |
| **Backup theft** | Years of client data in backups | Backups contain only aggregate metadata, no line-level data |
| **Insider threat** | Employee can export customer data | No line-level financial data exists to export |
| **Subpoena** | Must produce stored financial records | Can only produce aggregate metadata — no raw files or line-level data |

### 4.2 Attack Surface Reduction

**Eliminated Attack Vectors:**
- ❌ SQL injection targeting line-level financial data (no line-level data in database)
- ❌ Ransomware encrypting client files (no raw files stored)
- ❌ Data exfiltration of raw financial records via backup systems (backups contain aggregate metadata only)
- ❌ Long-term exposure of raw financial data (raw data expires in seconds)

**Remaining Attack Vectors:**
- ⚠️ Man-in-the-middle attacks (mitigated by TLS 1.3)
- ⚠️ Credential theft (mitigated by bcrypt hashing, JWT expiration)
- ⚠️ Client-side attacks (user's browser, outside Paciolus control)

### 4.3 Data Breach Notification Thresholds

Under GDPR and CCPA, companies must notify users of breaches involving **personal data**. Paciolus's exposure:

| Data Type | Breach Severity | Notification Required |
|-----------|-----------------|----------------------|
| Raw trial balance data | N/A (not stored) | ❌ No |
| Individual account balances | N/A (not stored) | ❌ No |
| User email addresses | Low | ✅ Yes (standard) |
| Password hashes | Low (bcrypt) | ✅ Yes (standard) |
| Client names | Low (metadata) | ✅ Yes (metadata only) |
| Aggregate diagnostic metadata | Low (category totals only) | ✅ Yes (metadata only) |
| **Raw financial transactions** | **N/A (not stored)** | **❌ No** |

**Liability reduction:** The most damaging breach scenario (line-level financial data exposure) is architecturally prevented. Only aggregate metadata is at risk.

---

## 5. Compliance Implications

### Scope Boundaries

Zero-Storage applies specifically to **raw financial data** — uploaded files, line-level account balances, and individual transaction details. It does **not** imply that Paciolus stores no data at all.

Operational metadata — user credentials, client metadata, aggregate diagnostic summaries, engagement records, and billing events — is stored and governed by the retention schedule in Section 2.4. Compliance obligations apply differently to each data category:

| Data Category | Regulatory Exposure | Rationale |
|---------------|---------------------|-----------|
| **Raw financial data** | None (never persisted) | Zero-Storage architecture eliminates storage-related obligations |
| **User credentials** | Standard data protection (GDPR Art. 5, CCPA §1798.100) | Encrypted at rest (bcrypt), deletable on request |
| **Aggregate diagnostic metadata** | Standard data protection | Contains no line-level detail; 365-day retention window |
| **Engagement & billing metadata** | Standard data protection | Narrative-only / Stripe references only; deletable on request |

### 5.1 GDPR (General Data Protection Regulation)

#### Article 25: Data Protection by Design and by Default

Paciolus demonstrates **privacy by design** through Zero-Storage:

> "The controller shall implement appropriate technical and organisational measures designed to implement data-protection principles, such as data minimisation."

**How Paciolus Complies:**
- **Data Minimization (Article 5(1)(c)):** Raw trial balance data and line-level financial records are not persisted; only aggregate metadata is retained
- **Storage Limitation (Article 5(1)(e)):** Raw financial data storage duration = 0 seconds; aggregate metadata retained for 365 days (1 year) by default
- **Purpose Limitation (Article 5(1)(b)):** Aggregate metadata stored only for specified purposes (diagnostic history, trend analysis)

#### Right to Erasure (Article 17)

`/activity/clear` archives (soft-deletes) activity history; it does not erase it. Erasure requests go to privacy@paciolus.com. Uploaded files are not kept, so erasure covers account data, client metadata, analysis summaries, flagged account names and engagement entries.

#### Data Processing Agreement (DPA)

For enterprise customers, Paciolus's DPA is simplified:

| Data Category | Processor Role | Processing Activity |
|---------------|---------------|---------------------|
| Raw trial balances | ❌ Not a processor | Not stored, only processed in-memory (aggregate metadata retained) |
| User credentials | ✅ Processor | Stores for authentication |
| Client metadata | ✅ Processor | Stores for organizational purposes |

**Key Advantage:** Paciolus is **not a data processor** for financial data, reducing regulatory burden.

### 5.2 CCPA (California Consumer Privacy Act)

#### "Sale" of Personal Information

CCPA defines "sale" broadly. Paciolus's position:

- **Raw trial balance data:** Not collected, therefore cannot be sold ✅
- **User email:** Collected, not sold ✅
- **Client metadata:** Collected, not sold ✅

**Simplified disclosure:** "Paciolus does not sell your personal information and does not store raw financial data. Only aggregate diagnostic metadata is retained."

#### Right to Deletion (§1798.105)

Users can request deletion of:
- ✅ User account and credentials
- ✅ Client metadata
- ✅ Activity logs (aggregate summaries)
- ❌ Trial balance data (already deleted automatically)

### 5.3 SOC 2 Type II (Security, Availability, Confidentiality)

#### Simplified Control Scope

Traditional SaaS SOC 2 controls:
- ✅ Access control to production databases
- ✅ Encryption at rest for stored data
- ✅ Data backup and recovery procedures
- ✅ Logical access to financial data
- ✅ Change management for data schemas

**Paciolus's reduced scope:**
- ✅ Access control to production databases (metadata only)
- ✅ Encryption at rest (aggregate metadata only, no line-level financial data)
- ✅ Data backup (aggregate metadata only, no line-level financial data)
- ❌ **Logical access to line-level financial data (N/A - not stored)**
- ❌ **Change management for line-level financial data schemas (N/A - not stored)**

**Audit advantage:** Fewer controls required, simpler evidence collection.

### 5.4 Industry-Specific Regulations

#### SOX (Sarbanes-Oxley Section 404)

Paciolus is **not subject to SOX** as it does not store financial records. Clients remain responsible for their own SOX compliance using data they download from Paciolus.

#### PCI DSS (Payment Card Industry Data Security Standard)

Paciolus does not process, store, or transmit payment card data. **Not applicable.**

---

## 6. Competitive Differentiation

### 6.1 Market Positioning

| Competitor | Data Storage Model | Paciolus Zero-Storage Advantage |
|------------|-------------------|----------------------------------|
| **QuickBooks Online** | Stores all transactions, invoices, reports | ✅ No long-term liability for client data breaches |
| **Xero** | Stores full accounting ledger in cloud | ✅ Cannot be compelled to produce client data |
| **Sage Intacct** | Stores financial data with backups | ✅ Simpler compliance (GDPR, SOC 2) |
| **NetSuite** | Full ERP storage | ✅ Faster onboarding (no data migration needed) |
| **FreshBooks** | Stores invoices, expenses, time tracking | ✅ Privacy-first positioning for sensitive clients |

### 6.2 Value Proposition for Fractional CFOs

**Target Persona:** Fractional CFO managing confidential data for 5-15 clients across industries (healthcare, legal, startups).

**Pain Point:** "I'm terrified of a data breach exposing my clients' financials."

**Paciolus Solution:**
> "Your clients' raw trial balance files are never persisted to our database. We process the data in ephemeral server memory and send you the diagnostic report. Only aggregate metadata (category totals, ratios) is retained — no line-level financial data."

**Competitive Moat:**
- Competitors cannot easily replicate Zero-Storage without re-architecting their platforms
- Zero-Storage is a **credible signal** of privacy commitment (not just marketing)
- Professional liability insurance costs may be lower (reduced exposure)

### 6.3 Trust Signals

**For Privacy-Conscious Industries:**
- Healthcare practices (HIPAA-adjacent financial data)
- Law firms (client trust account audits)
- Nonprofit organizations (donor privacy concerns)
- Venture-backed startups (pre-IPO confidentiality)

**Marketing Message:**
> "We can't leak what we don't store. Your raw financial data is processed in ephemeral server memory for the few seconds it takes to analyze, then discarded. Only aggregate metadata is retained."

---

## 7. User Experience

### 7.1 Session-Based Workflow

1. **Upload:** User uploads trial balance (CSV, Excel, TSV, OFX, ODS, PDF, IIF, or other supported format)
2. **Process:** Analysis happens in <5 seconds (in-memory)
3. **Review:** Results displayed in browser (React state)
4. **Export:** User downloads PDF/Excel report (local save)
5. **Close Tab:** All data cleared from browser memory

**Key UX Point:** Users understand that closing the tab = data gone forever (ephemeral session).

### 7.2 No "Recall Previous Analysis" Feature

**By design**, Paciolus cannot offer:
- ❌ "View last month's trial balance"
- ❌ "Compare Q3 2024 vs Q4 2024"
- ❌ "Retrieve analysis from October"

**Why:** The data doesn't exist to retrieve.

**Workaround for users:**
- Save exported PDF/Excel files locally
- Maintain their own archive of diagnostic reports
- Re-upload the same trial balance if re-analysis needed

### 7.3 Activity History (Metadata Only)

Users can view their audit **history** via the Heritage Timeline:

**What's shown:**
- ✅ Date/time of each analysis
- ✅ Filename (first 12 characters, hashed)
- ✅ Balanced status (yes/no)
- ✅ Anomaly count (integer)
- ✅ Row count

**What's NOT shown:**
- ❌ Which accounts had anomalies
- ❌ Account balances
- ❌ Original file contents

**User understanding:** "I can see that I analyzed 'ClientQ4_202...' on Jan 15 and it had 3 anomalies, but I can't see which accounts. I need to refer to my downloaded PDF for details."

---

## 8. Audit Trail

### 8.1 For Internal Audits

**Auditor question:** "Can you show me the trial balance processed on January 10, 2026?"

**Paciolus answer:** "No. The raw trial balance data was destroyed immediately after processing. We can show you:
- The activity log entry (metadata: date, filename hash, row count, balanced status)
- The user who performed the analysis
- The PDF report if the user downloaded it and archived it locally"

**Implication:** Paciolus shifts **data retention responsibility to the user**.

### 8.2 For Regulatory Audits

**Regulator:** "Produce all financial records for User ID 12345."

**Paciolus response:** "We do not store raw financial records. We can produce:
- User account information (email, created date)
- Client metadata (client names, industries)
- Activity logs (aggregate summaries, no detailed financial data)
- No trial balance data is available (Zero-Storage architecture)"

**Legal advantage:** Paciolus cannot be compelled to produce data it doesn't possess.

---

## 9. Limitations and Trade-offs

### 9.1 Feature Limitations

**Cannot offer:**
- ❌ Longitudinal trend analysis (requires historical data storage)
- ❌ Year-over-year comparisons (no prior year data stored)
- ❌ Automated anomaly detection across time (no time series data)
- ❌ "Undo" or "Restore previous analysis" (no snapshots stored)

**Workarounds:**
- Users maintain their own historical diagnostic reports (PDFs/Excel)
- Comparative analysis done manually by users via exported files

### 9.2 Performance Trade-offs

**Advantages:**
- ✅ Faster initial load (no data migration required)
- ✅ Instant account deletion (no data to purge)
- ✅ Scalable (no growing database of raw financial data)

**Disadvantages:**
- ⚠️ Slight latency for large files (streaming processing in real-time)
- ⚠️ Re-upload required for re-analysis (cannot pull from cache)

### 9.3 Business Trade-offs

**Revenue implications:**
- ✅ Lower infrastructure costs (minimal database storage)
- ✅ Lower insurance premiums (reduced liability exposure)
- ❌ Cannot upsell "data analytics" features that require historical data
- ❌ Cannot offer "AI-powered insights" based on cross-customer trends

**Strategic decision:** Paciolus prioritizes **privacy and security** over advanced analytics features.

---

## 10. Verification and Assurance

### 10.1 How Users Can Verify Zero-Storage

**Transparency mechanisms:**

1. **Open-Source Codebase (Future):**
   - Backend audit engine code published on GitHub
   - Independent security researchers can audit the code

2. **SOC 2 Type II Report:**
   - Control: "Raw financial data is not persisted to disk or database; only aggregate metadata is retained"
   - Testing procedure: Auditor inspects database schema and confirms no line-level financial data fields
   - Evidence: Database dump analysis showing only aggregate metadata and user/client tables

3. **Penetration Testing:**
   - Engage third-party security firm to attempt data extraction
   - Publish summary findings confirming zero raw financial data storage

4. **User-Facing Transparency:**
   - Real-time memory usage indicator in UI (shows spike during processing, immediate drop after)
   - "Your data has been discarded" confirmation message after analysis

### 10.2 Control Verification: Automated Safeguards

Paciolus enforces Zero-Storage and retention compliance through automated controls that run without manual intervention:

| Control | Mechanism | Frequency |
|---------|-----------|-----------|
| **Retention cleanup** | Soft-archives activity logs and diagnostic summaries exceeding the 365-day retention window via `archived_at` timestamp | Periodic (configurable interval) |
| **Tool session sanitization** | Financial key stripping (allowlist filter) before every DB write; bulk TTL cleanup of expired sessions on server startup | Every session write + every server start |
| **Memory cleanup** | `memory_cleanup()` context manager calls `gc.collect()` in a `finally` block on all file upload routes | Every file upload request |
| **ORM deletion guard** | `before_flush` event listener raises `AuditImmutabilityError` on hard-delete of 5 audit-sensitive tables | Every database transaction |
| **Sentry body stripping** | `before_send` hook removes `event["request"]["data"]` from all error reports sent to Sentry | Every Sentry event |
| **Accounting Policy Guard** | 5 AST-based invariant checkers enforce monetary precision, deletion prevention, contract fields, adjustment gating, and framework metadata in CI | Every CI pipeline run |

These controls are independently verifiable by inspecting the codebase (`backend/shared/soft_delete.py`, `backend/shared/helpers.py`, `backend/main.py` lifespan, `.github/workflows/`).

### 10.3 Third-Party Validation

**Recommended certifications:**
- ✅ SOC 2 Type II (with specific Zero-Storage controls)
- ✅ ISO 27001 (information security management)
- ✅ GDPR Article 42 certification (data protection certification)

**Audit evidence:**
- Database schema documentation (shows only user, client, aggregate metadata, and workflow tables)
- Code review of audit engine (confirms no persistence logic)
- Infrastructure audit (confirms no file storage configured)

---

## Conclusion

Paciolus's Zero-Storage architecture is a **fundamental technical design choice** with measurable security, compliance, and competitive benefits. No raw uploaded files or line-level financial data are persisted; only aggregate diagnostic metadata (category totals, ratios, row counts) is retained.

**For Enterprise Customers:**
- Reduced breach liability
- Simplified compliance (GDPR, CCPA, SOC 2)
- Privacy-first positioning for sensitive industries

**For Paciolus:**
- Competitive differentiation in a crowded market
- Lower infrastructure and insurance costs
- Credible trust signal to privacy-conscious buyers

**For Regulators:**
- Architecturally enforced data minimization (GDPR Article 25)
- Transparent, auditable data handling
- Clear boundaries of data retention

Zero-Storage is Paciolus's **strategic moat**. Competitors who store data cannot easily migrate to this model without rebuilding their entire platform.

---

## Appendices

### Appendix A: Glossary

| Term | Definition |
|------|------------|
| **Zero-Storage** | Architectural principle where raw financial data is processed in ephemeral memory and never persisted to disk or database; aggregate metadata may be retained |
| **In-Memory Processing** | Data processing that occurs entirely in RAM without writing to permanent storage |
| **BytesIO Buffer** | Python object that stores file data in memory (not disk) |
| **Ephemeral** | Existing only temporarily; destroyed when no longer needed |
| **Aggregate Statistics** | Summary metrics (counts, totals) without detailed data |
| **SHA-256 Hash** | One-way cryptographic hash function (cannot reverse to original value) |

### Appendix B: References

- GDPR (General Data Protection Regulation): https://gdpr-info.eu/
- CCPA (California Consumer Privacy Act): https://oag.ca.gov/privacy/ccpa
- SOC 2 Framework: AICPA Trust Services Criteria
- FastAPI Documentation: https://fastapi.tiangolo.com/
- pandas Documentation: https://pandas.pydata.org/

### Appendix C: Contact

For questions about Paciolus's Zero-Storage architecture:
- **Technical inquiries:** engineering@paciolus.com
- **Compliance inquiries:** compliance@paciolus.com
- **Security inquiries:** security@paciolus.com

---

**Document Version History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 2.2 | 2026-02-27 | CTO | CSRF upgrade: Section 3.1 corrected — access tokens are React `useRef` in-memory only, refresh tokens are HttpOnly `paciolus_refresh` cookie, CSRF tokens are stateless HMAC credentials derived from auth responses and never written to session or local storage |
| 2.1 | 2026-02-26 | CTO | Consistency pass: Terminology Clarity box (Section 1.3), Scope Boundaries preamble (Section 5), Control Verification automated safeguards table (Section 10.2), cross-doc retention alignment verified |
| 2.0 | 2026-02-26 | CTO | Align with implementation: 10 file formats, add Engagement/ToolRun/FollowUp/Subscription/BillingEvent tables, Numeric(19,2) field types, soft-delete archival model (Section 2.4), memory_cleanup() context manager, DB-backed tool sessions with financial key stripping, expanded DiagnosticSummary fields (8 ratios + period metadata), retention 365 days |
| 1.1 | 2026-02-16 | CTO | Truthful language baseline: qualify absolute claims, add diagnostic_summaries + tool_sessions tables, fix server vs browser processing |
| 1.0 | 2026-02-04 | CTO | Initial publication |

---

*Paciolus — Zero-Storage Trial Balance Diagnostic Intelligence*
