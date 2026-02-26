# Zero-Storage Architecture

**Document Classification:** Public  
**Version:** 1.1
**Last Updated:** February 16, 2026  
**Owner:** Chief Technology Officer

---

## Executive Summary

Paciolus operates under a **Zero-Storage security model** that fundamentally differentiates it from traditional cloud accounting platforms. While competitors store client financial data on their servers, Paciolus processes trial balance data entirely in-memory and immediately discards it after analysis.

**Key Points:**
- ✅ **What Is Stored:** User credentials, client metadata, aggregate diagnostic metadata (category totals, ratios, row counts)
- ❌ **What Is Never Stored:** Raw uploaded files, line-level account balances, individual transaction details
- 🔒 **Security Benefit:** Zero exposure of line-level financial data in the event of a breach
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

**Zero-Storage** means that Paciolus **never persists raw uploaded files or line-level financial transaction data** to any disk, database, or cloud storage system. All trial balance processing occurs in ephemeral memory and is destroyed immediately after analysis completes. Aggregate metadata (category totals, financial ratios, row counts) may be retained for diagnostic history.

### 1.2 Philosophy

Traditional accounting platforms operate on a "store first, process later" model. Paciolus inverts this:

| Traditional SaaS | Paciolus Zero-Storage |
|------------------|----------------------|
| Upload → Store → Process → Display | Upload → Process → Display → Discard |
| Data persists indefinitely | Raw data exists only during analysis; aggregate metadata retained |
| Server-side financial data | Client-side data ownership |
| Breach exposes all historical data | Breach exposes no line-level financial data |

### 1.3 Scope

Zero-Storage applies to:
- ✅ Raw uploaded CSV/Excel files (never written to disk)
- ✅ Line-level account names and balances (not persisted)
- ✅ Individual transaction details (not persisted)
- ✅ Ledger entries (not persisted)
- ✅ Financial reports (except user-downloaded PDFs/Excel)

Zero-Storage does **not** apply to:
- User authentication credentials (hashed passwords)
- Client metadata (name, industry, fiscal year end)
- Aggregate diagnostic metadata (category totals, financial ratios, row counts)
- Ephemeral tool working state (adjustments, currency rates — TTL-expired)
- User preferences and settings

---

## 2. What Is Stored vs. What Is Not

### 2.1 Data Classification Matrix

| Data Type | Storage Status | Retention | Example |
|-----------|----------------|-----------|---------|
| **Raw Trial Balance Rows** | ❌ Never Stored | Ephemeral (seconds) | "Cash: $50,000 DR" |
| **Individual Account Names** | ❌ Never Stored | Ephemeral | "Accounts Receivable" |
| **Raw Uploaded Files** | ❌ Never Stored | Ephemeral | "ClientXYZ_Q4_2024.xlsx" |
| **User Credentials** | ✅ Stored | Until account deletion | "user@example.com, bcrypt hash" |
| **Client Metadata** | ✅ Stored | Until deletion | "Acme Corp, Technology, 12-31 FYE" |
| **Diagnostic Summaries** | ✅ Stored (aggregates) | 365 days (1 year) | "47 rows, balanced, 3 anomalies, total_assets: $1.2M" |
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
**Fields Stored:**
- Activity ID (UUID)
- User ID (foreign key)
- **Filename hash** (SHA-256, irreversible)
- Filename display (first 12 characters only)
- Timestamp
- **Aggregate statistics only:**
  - Row count (integer)
  - Total debits (sum only, no details)
  - Total credits (sum only, no details)
  - Balanced status (boolean)
  - Anomaly count (integer only, no specifics)
  - Materiality threshold used

**What Is NOT Stored:**
- Original filename (hashed for privacy)
- File contents or raw data
- Specific account names or balances
- Individual transaction details
- Anomaly descriptions (which accounts had issues)

#### Diagnostic Summaries Table
**Purpose:** Aggregate diagnostic metadata for historical comparison and trend analysis
**Fields Stored:**
- Summary ID (UUID)
- User ID (foreign key)
- Client ID (foreign key, optional)
- **Aggregate category totals only:**
  - Total assets, liabilities, equity, revenue, expenses (sums, no line-level detail)
  - Financial ratios (current ratio, quick ratio, debt-to-equity, gross margin)
  - Row count (integer)
- Timestamp

**What Is NOT Stored:**
- Individual account names or balances
- Line-level trial balance rows
- Specific transaction details
- Raw file contents

#### Tool Sessions Table
**Purpose:** Ephemeral working state for multi-step tool workflows (e.g., adjusting entries, currency rates)
**Fields Stored:**
- User ID (foreign key)
- Tool name (string)
- Session data (JSON working state)
- TTL-based expiration (1–2 hours)

**Important:** Tool sessions are ephemeral by design — they expire automatically via TTL and are cleaned up at server startup. They are **not** permanent storage.

### 2.3 Storage Duration

| Category | Retention Period | Deletion Trigger |
|----------|------------------|------------------|
| User credentials | Indefinite | User account deletion request |
| Client metadata | Indefinite | User deletes client record |
| Activity logs | 365 days (1 year) | Automatic archival or user deletion request |
| Diagnostic summaries | 365 days (1 year) | Automatic archival |
| Tool sessions | 1–2 hours | TTL expiration + startup cleanup |
| User settings | Indefinite | User account deletion request |
| **Raw trial balance data** | **0 seconds** | **Immediate garbage collection** |

---

## 3. Technical Implementation

### 3.1 In-Memory Processing Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    USER'S BROWSER                            │
│                                                              │
│  1. User uploads CSV/Excel file                             │
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
│  4. pandas.read_csv() loads into DataFrame (memory)          │
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
- Session storage used only for JWT token (not financial data)

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

### 3.3 Garbage Collection

Python's garbage collector is explicitly invoked after processing:

```python
import gc

# After processing
del dataframe
del buffer
gc.collect()  # Force immediate memory reclamation
```

This ensures raw financial data is purged from RAM immediately, not left for eventual cleanup.

### 3.4 Export Mechanism (PDF/Excel)

When users export diagnostic reports:

1. **Backend generates PDF/Excel in BytesIO buffer** (memory, not disk)
2. **Streams to user via HTTP chunked transfer** (8KB chunks)
3. **Buffer cleared immediately after streaming completes**
4. **User's browser saves file locally** (user's device, not Paciolus servers)

**Key Point:** The exported file never touches Paciolus's persistent storage.

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

### 5.1 GDPR (General Data Protection Regulation)

#### Article 25: Data Protection by Design and by Default

Paciolus demonstrates **privacy by design** through Zero-Storage:

> "The controller shall implement appropriate technical and organisational measures designed to implement data-protection principles, such as data minimisation."

**How Paciolus Complies:**
- **Data Minimization (Article 5(1)(c)):** Raw trial balance data and line-level financial records are not persisted; only aggregate metadata is retained
- **Storage Limitation (Article 5(1)(e)):** Raw financial data storage duration = 0 seconds; aggregate metadata retained for 365 days (1 year) by default
- **Purpose Limitation (Article 5(1)(b)):** Aggregate metadata stored only for specified purposes (diagnostic history, trend analysis)

#### Right to Erasure (Article 17)

Users can delete their data via `/activity/clear` endpoint. Since raw financial data is never stored, there is nothing to erase beyond aggregate metadata.

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

1. **Upload:** User uploads trial balance CSV/Excel
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

### 10.2 Third-Party Validation

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
| 1.1 | 2026-02-16 | CTO | Truthful language baseline: qualify absolute claims, add diagnostic_summaries + tool_sessions tables, fix server vs browser processing |
| 1.0 | 2026-02-04 | CTO | Initial publication |

---

*Paciolus — Zero-Storage Trial Balance Diagnostic Intelligence*
