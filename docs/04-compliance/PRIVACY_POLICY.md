# Privacy Policy

**Version:** 2.0
**Document Classification:** Public
**Effective Date:** February 26, 2026
**Last Updated:** February 26, 2026
**Owner:** privacy@paciolus.com
**Next Review:** August 26, 2026

---

## Your Privacy Matters

At Paciolus, we believe privacy is not just a legal requirement—it's a fundamental right. This Privacy Policy explains how we collect, use, and protect your information when you use our trial balance diagnostic platform.

**Our commitment to you:**
- ✅ We **never store** your financial data (trial balances, account details)
- ✅ We collect only what's necessary to provide our service
- ✅ We never sell your personal information
- ✅ You control your data and can delete it anytime

This policy applies to all users of Paciolus, accessible at https://paciolus.com and any related mobile applications.

---

## Table of Contents

1. [Information We Collect](#1-information-we-collect)
2. [How We Use Your Information](#2-how-we-use-your-information)
3. [Zero-Storage Architecture](#3-zero-storage-architecture)
4. [Data Retention Governance](#4-data-retention-governance)
5. [Information We Share](#5-information-we-share)
6. [Your Rights and Choices](#6-your-rights-and-choices)
7. [Data Security](#7-data-security)
8. [International Data Transfers](#8-international-data-transfers)
9. [Children's Privacy](#9-childrens-privacy)
10. [Changes to This Policy](#10-changes-to-this-policy)
11. [Contact Us](#11-contact-us)
12. [GDPR-Specific Information](#12-gdpr-specific-information)
13. [CCPA-Specific Information](#13-ccpa-specific-information)

---

## 1. Information We Collect

### 1.1 Information You Provide Directly

| Information Type | Purpose | Example |
|------------------|---------|---------|
| **Account Registration** | Create and manage your account | Email address, password |
| **Client Metadata** | Organize your work (for fractional CFOs) | Client company names, industries, fiscal year ends |
| **Support Requests** | Respond to your inquiries | Name, email, description of issue |
| **Payment Information** | Process subscriptions (via Stripe) | Credit card details (processed by Stripe, not stored by us) |

**What we DO NOT collect during account creation:**
- ❌ Social Security Number
- ❌ Address or phone number (unless you provide it for billing)
- ❌ Government-issued ID

### 1.2 Information We Collect Automatically

When you use Paciolus, we automatically collect:

| Category | What We Collect | Purpose |
|----------|-----------------|---------|
| **Usage Data** | Pages viewed, features used, time spent | Improve product, analytics |
| **Device Information** | Browser type, operating system, IP address | Security, fraud prevention |
| **Cookies** | Session cookies (ephemeral), analytics cookies | Maintain login session, analytics |
| **Log Data** | API requests, error messages, timestamps | Debugging, security monitoring |

**Note:** We use session storage (ephemeral) for authentication tokens. Data is deleted when you close your browser tab.

### 1.3 Information We DO NOT Collect

**Critical distinction:** Paciolus operates under a **Zero-Storage** model for financial data:

| Data Category | Collection Status | Why |
|---------------|------------------|-----|
| **Trial Balance Data** | ❌ Never collected or stored | Zero-Storage architecture (see Section 3) |
| **Account Balances** | ❌ Never stored | Processed in-memory, discarded after analysis |
| **Transaction Details** | ❌ Never stored | Ephemeral processing only |
| **Uploaded Files** | ❌ Never persisted | Exists in memory for \u003c5 seconds |
| **Specific Anomaly Details** | ❌ Never stored | Only aggregate counts stored |

**What this means:** If you upload a trial balance CSV with your client's financial data, that data is **never written to our databases or disks**. It exists only in temporary memory during the analysis (typically 3-5 seconds) and is immediately destroyed.

---

## 2. How We Use Your Information

### 2.1 Primary Uses

| Purpose | Information Used | Legal Basis (GDPR) |
|---------|------------------|--------------------|
| **Provide the Service** | Email, password, uploaded files (ephemeral) | Performance of contract |
| **Account Management** | Email, account preferences | Performance of contract |
| **Client Organization** | Client names, industries | Performance of contract |
| **Security** | IP address, login timestamps | Legitimate interest |
| **Analytics** | Usage patterns, feature adoption | Legitimate interest |
| **Support** | Email, support tickets | Performance of contract |
| **Legal Compliance** | Account data, activity logs | Legal obligation |

### 2.2 Aggregate Statistics (Privacy-Safe)

We store **aggregate activity statistics** that cannot identify individual accounts or transactions:

**Example of what we store:**
```json
{
  "user_id": "uuid-1234",
  "timestamp": "2026-02-04T10:00:00Z",
  "filename_hash": "abc123def456...",  // SHA-256 hash, irreversible
  "filename_display": "ClientQ4_202...",  // First 12 characters only
  "row_count": 1500,  // Count only, no details
  "total_debits": 2500000,  // Sum only, no breakdown
  "total_credits": 2500000,  // Sum only, no breakdown
  "balanced": true,  // Boolean status
  "anomaly_count": 3  // Count only, no specifics
}
```

**What we DO NOT store:**
- ❌ Which accounts had anomalies ("Accounts Receivable had abnormal balance")
- ❌ Specific account balances ("Cash: $50,000")
- ❌ Client names in activity logs (stored separately, not linked to trial balance data)

### 2.3 We Do NOT:
- ❌ **Sell your personal information** to third parties
- ❌ **Use your financial data for advertising** (we don't have it)
- ❌ **Share your data with data brokers**
- ❌ **Train AI models on your trial balance data** (Zero-Storage prevents this)

---

## 3. Zero-Storage Architecture

**This section is critical to understanding our privacy model.**

Paciolus is fundamentally different from traditional cloud accounting platforms like QuickBooks or Xero. While they **store your financial data** on their servers, we **do not**.

### 3.1 How It Works

```
┌──────────────────────────────────── ───────────┐
│ YOUR BROWSER                                   │
│ You upload "ClientABC_Q4_2024.xlsx" (500 rows) │
└────────────────────┬───────────────────────────┘
                     │ HTTPS Upload
                     ▼
┌─────────────────────────────────────────────────┐
│ PACIOLUS SERVER (Memory Only)                   │
│ ┌─────────────────────────────────────────────┐ │
│ │ 1. File loaded into RAM (BytesIO buffer)    │ │
│ │ 2. Analysis performed (3-5 seconds)         │ │
│ │ 3. Results sent back to your browser        │ │
│ │ 4. Buffer cleared (Python gc.collect())     │ │
│ └─────────────────────────────────────────────┘ │
│ ❌ No disk write     ❌ No database insert      │
└─────────────────────────────────────────────────┘
                     │ HTTPS Response (JSON summary)
                     ▼
┌─────────────────────────────────────────────────┐
│ YOUR BROWSER                                    │
│ Results displayed (React state, ephemeral)      │
│ You can download PDF/Excel (saved to YOUR PC)  │
└─────────────────────────────────────────────────┘
```

**Key points:**
- Your trial balance exists on our server for **less than 5 seconds**
- It's stored in **ephemeral memory**, not on disk or in a database
- When analysis completes, the data is **immediately destroyed**
- If you reload the page, the results are gone (no server-side storage)

**Why we built it this way:**
- **Security:** Can't leak data we don't have
- **Privacy:** No risk of long-term exposure
- **Compliance:** Simplified GDPR/CCPA requirements

**For full technical details, see:** [ZERO_STORAGE_ARCHITECTURE.md](./ZERO_STORAGE_ARCHITECTURE.md)

---

## 4. Data Retention Governance

Paciolus classifies all data into two categories based on retention behavior:

- **Ephemeral data** — Raw financial data (uploaded files, line-level account balances, transaction details) is processed entirely in-memory and destroyed immediately after analysis. Retention duration: **0 seconds**.
- **Bounded operational metadata** — Aggregate statistics, engagement records, and billing events are retained for a defined period, after which they are automatically archived.

### 4.1 Canonical Retention Schedule

| Data Class | Default Retention | Deletion Trigger | User-Request Deletion |
|------------|-------------------|------------------|-----------------------|
| **Raw trial balance data** | 0 seconds (ephemeral) | Immediate garbage collection after analysis | N/A (never stored) |
| **Uploaded files** | 0 seconds (ephemeral) | Immediate garbage collection after analysis | N/A (never stored) |
| **User credentials** | Until account deletion | User-initiated account deletion | Yes |
| **Client metadata** | Until deletion | User deletes client record or account | Yes |
| **User settings/preferences** | Until account deletion | User-initiated account deletion | Yes |
| **Activity logs** (aggregate summaries) | 365 days (1 year) | Automatic archival after retention window | Yes (immediate on request) |
| **Diagnostic summaries** (aggregate metadata) | 365 days (1 year) | Automatic archival after retention window | Yes (immediate on request) |
| **Engagement metadata** | Until account deletion | User deletes engagement or account | Yes |
| **Tool run records** (metadata only) | Until account deletion | User deletes engagement or account | Yes |
| **Follow-up items** (narratives only, no financial data) | Until account deletion | User deletes engagement or account | Yes |
| **Billing events** (append-only lifecycle log) | Until account deletion | User-initiated account deletion | Yes |
| **Subscription records** | Until account deletion | User-initiated account deletion | Yes |
| **Tool sessions** (ephemeral working state) | 1–2 hours | Automatic TTL expiration + server startup cleanup | N/A (auto-expired) |
| **Refresh tokens** | 7 days | Automatic expiration | Yes (logout/revocation) |
| **Email verification tokens** | 24 hours | Automatic expiration + periodic cleanup | N/A (auto-expired) |

### 4.2 Retention Configuration

The default retention window for aggregate operational metadata (activity logs, diagnostic summaries) is **365 days (1 year)**. This value is configurable at the deployment level. Records that exceed the retention window are automatically archived — not permanently deleted — preserving an immutable audit trail while removing them from active queries.

### 4.3 Policy Precedence

Where operational retention controls and legal minimum retention requirements differ, the stricter requirement applies. For example, if a legal hold or regulatory obligation requires retention beyond the configured window, the legal requirement takes precedence. Conversely, a user deletion request under GDPR Article 17 or CCPA §1798.105 will be honored unless a specific legal exception applies.

### 4.4 Archival vs. Deletion

Paciolus uses a **soft-delete archival model** for audit-sensitive records (activity logs, diagnostic summaries, tool runs, follow-up items). Archived records are excluded from active queries and user-facing displays but remain available for compliance or legal purposes. Permanent deletion of archived records occurs only when required by data subject request or when no legal retention obligation exists.

**For detailed audit logging event classes, tamper-resistance controls, and legal hold procedures, see [AUDIT_LOGGING_AND_EVIDENCE_RETENTION.md](./AUDIT_LOGGING_AND_EVIDENCE_RETENTION.md).**

---

## 5. Information We Share

### 5.1 Service Providers

We share limited data with third-party providers who help us operate our service:

| Provider | Purpose | Data Shared | DPA Signed |
|----------|---------|-------------|------------|
| **Vercel** | Frontend hosting (CDN) | None (static files only) | ✅ Yes |
| **Render** | Backend API hosting | User credentials (encrypted), client metadata | ✅ Yes |
| **PostgreSQL** | Database | User accounts, client metadata, activity logs (aggregates) | ✅ Yes |
| **Stripe** | Payment processing | Email, billing information | ✅ Yes |
| **Sentry** | Error tracking | Error messages, user IDs (anonymized) | ✅ Yes |

**Financial data shared:** ❌ **None** (Zero-Storage architecture)

### 5.2 Legal Requirements

We may disclose your information to comply with:
- **Legal process** (subpoena, court order)
- **Government requests** (law enforcement, regulators)
- **Protecting rights** (enforce our Terms of Service, detect fraud)

**What we can produce if compelled:**
- ✅ User account information (email, created date)
- ✅ Client metadata (client names, industries)
- ✅ Activity logs (aggregate summaries of analyses performed)
- ❌ **Trial balance data (does not exist to produce)**

### 5.3 Business Transfers

If Paciolus is acquired or merges with another company:
- You will be notified via email
- The acquiring company must honor this Privacy Policy
- You may delete your account if you disagree with the transfer

---

## 6. Your Rights and Choices

### 6.1 Access and Portability (GDPR Article 15, CCPA §1798.110)

**You have the right to access your personal data.**

**How to request:**
- Email privacy@paciolus.com with subject "Data Access Request"
- We will provide a JSON or CSV export within **30 days**

**What you'll receive:**
```json
{
  "account": {
    "email": "you@example.com",
    "created_at": "2026-01-01T00:00:00Z",
    "last_login": "2026-02-04T10:00:00Z"
  },
  "clients": [
    {"name": "Acme Corp", "industry": "technology", "fiscal_year_end": "12-31"}
  ],
  "activity_logs": [
    {"date": "2026-02-03", "balanced": true, "row_count": 500, "anomaly_count": 2}
  ]
}
```

**What you will NOT receive:**
- ❌ Trial balance data (Zero-Storage—never retained)

### 6.2 Correction (GDPR Article 16, CCPA §1798.106)

**You can update your account information anytime:**
- Email address: Settings → Account
- Password: Settings → Security
- Client metadata: Portfolio → Edit Client

**Or contact us:** privacy@paciolus.com

### 6.3 Deletion (GDPR Article 17, CCPA §1798.105)

**You have the right to delete your account.**

**How to delete:**
1. Settings → Account → Delete Account (instant)
2. Email privacy@paciolus.com with subject "Account Deletion Request"

**What gets deleted:**
- ✅ User account and credentials
- ✅ All client metadata
- ✅ All activity logs (aggregate summaries)
- ✅ All preferences and settings

**Timeline:** Immediate deletion (no 30-day grace period).

**Note:** We may retain minimal data for legal/accounting purposes (e.g., transaction records for tax compliance) for up to 7 years.

### 6.4 Objection and Restriction (GDPR Article 21)

**You can object to certain processing:**
- **Marketing emails:** Unsubscribe link in every email, or email privacy@paciolus.com
- **Analytics cookies:** Browser settings (clear cookies)

**You can request restriction:**
- Email privacy@paciolus.com to pause processing while we investigate a request

### 6.5 Withdraw Consent (GDPR Article 7)

**If processing is based on consent (rare for Paciolus), you can withdraw:**
- Email privacy@paciolus.com
- We will stop processing within 5 business days

### 6.6 Do Not Sell (CCPA §1798.120)

**Paciolus does not sell your personal information.**

We have not sold personal information in the past 12 months and have no plans to do so.

If this changes, we will:
1. Update this Privacy Policy
2. Provide a "Do Not Sell My Personal Information" link
3. Email you with the option to opt-out

---

## 7. Data Security

**See SECURITY_POLICY.md for comprehensive details.**

**Summary of protections:**
- ✅ **TLS 1.3 encryption** for all data in transit
- ✅ **bcrypt password hashing** (salted, work factor 12)
- ✅ **JWT authentication** (8-hour token expiration)
- ✅ **Multi-tenant isolation** (user-level database filtering)
- ✅ **Zero-Storage** (financial data never persisted)
- ✅ **24/7 security monitoring** (automated alerts)

**No system is 100% secure.** If a breach occurs:
- We will notify affected users within **72 hours** (GDPR requirement)
- We will notify regulators as required by law
- We will provide details on what data was accessed

**Financial data exposure risk:** ❌ **Zero** (Zero-Storage architecture)

---

## 8. International Data Transfers

### 8.1 Data Locations

| Data Type | Primary Storage Location | Backups |
|-----------|-------------------------|---------|
| User accounts | United States (AWS/Render) | United States |
| Client metadata | United States (PostgreSQL) | United States |
| **Trial balance data** | **None (Zero-Storage)** | **None** |

### 8.2 European Economic Area (EEA) Users

**GDPR compliance mechanisms:**
- **Standard Contractual Clauses (SCCs):** Signed with U.S.-based processors (Vercel, Render)
- **Data minimization:** Only essential data transferred
- **Encryption:** All data encrypted in transit and at rest

**Your rights remain unchanged** regardless of where data is processed.

---

## 9. Children's Privacy

Paciolus is not intended for children under 16 years old.

**We do not knowingly collect** personal information from children.

If you believe a child has provided us with personal information:
- Email privacy@paciolus.com
- We will delete the account within 48 hours

---

## 10. Changes to This Policy

We may update this Privacy Policy to reflect:
- Changes in our practices
- New legal requirements
- New features

**How you'll be notified:**
- **Material changes:** Email notification 30 days in advance
- **Minor changes:** Updated "Last Updated" date at the top

**Your options:**
- Continue using Paciolus (acceptance of new policy)
- Delete your account if you disagree (see Section 6.3)

**Version history:** Available at https://paciolus.com/privacy/history

---

## 11. Contact Us

### Privacy Inquiries

| Type | Contact | Response Time |
|------|---------|---------------|
| **General privacy questions** | privacy@paciolus.com | 5 business days |
| **Data access requests** | privacy@paciolus.com | 30 days (GDPR requirement) |
| **Data deletion requests** | privacy@paciolus.com | Immediate |
| **GDPR/CCPA compliance** | compliance@paciolus.com | 5 business days |
| **Data breach notifications** | security@paciolus.com | Immediate |

**Mailing address:**  
Paciolus, Inc.  
[Address to be added]  
[City, State, ZIP]  
United States

**EU Representative (GDPR Article 27):**  
[To be appointed if EEA users exceed threshold]

---

## 12. GDPR-Specific Information

### 12.1 Data Controller

**Paciolus, Inc.** is the data controller for your personal information.

**Contact:** privacy@paciolus.com

### 12.2 Lawful Basis for Processing

| Processing Activity | Lawful Basis |
|---------------------|--------------|
| Account management | Performance of contract (GDPR Article 6(1)(b)) |
| Security monitoring | Legitimate interest (GDPR Article 6(1)(f)) |
| Legal compliance | Legal obligation (GDPR Article 6(1)(c)) |
| Marketing (if you opt-in) | Consent (GDPR Article 6(1)(a)) |

### 12.3 Data Protection Officer (DPO)

**DPO:** [To be appointed]  
**Contact:** dpo@paciolus.com

### 12.4 Supervisory Authority

If you believe we have violated GDPR, you can lodge a complaint with your local supervisory authority.

**Example (UK):** Information Commissioner's Office (ICO)  
**Example (France):** Commission Nationale de l'Informatique et des Libertés (CNIL)

---

## 13. CCPA-Specific Information

### 13.1 Categories of Personal Information Collected

**In the past 12 months, we have collected:**

| Category | Examples | Collected |
|----------|----------|-----------|
| **Identifiers** | Email address | ✅ Yes |
| **Commercial information** | Client metadata, activity logs | ✅ Yes |
| **Internet activity** | Usage data, log files | ✅ Yes |
| **Financial information** | Trial balance data | ❌ No (Zero-Storage) |
| **Sensitive personal information** | Password (hashed) | ✅ Yes |

### 13.2 Sources

All personal information is collected **directly from you** (no third-party data brokers).

### 13.3 Business Purposes

We use personal information for:
- Providing the service
- Security and fraud prevention
- Analytics and product improvement
- Legal compliance

### 13.4 Sale of Personal Information

**We do not sell personal information.**

In the past 12 months:
- ❌ We have not sold personal information
- ❌ We have not sold sensitive personal information
- ❌ We have not sold personal information of minors under 16

### 13.5 Your California Rights

| Right | How to Exercise |
|-------|-----------------|
| **Right to Know** | Email privacy@paciolus.com |
| **Right to Delete** | Settings → Delete Account |
| **Right to Opt-Out of Sale** | Not applicable (we don't sell) |
| **Right to Non-Discrimination** | We will never discriminate for exercising rights |

**Response time:** 45 days (may extend to 90 days with notice).

---

## Summary Table: What We Collect vs. What We Store

| Data Category | Collection | Storage Duration | Purpose |
|---------------|------------|------------------|---------|
| **Email address** | ✅ At registration | Until account deletion | Authentication |
| **Password (hashed)** | ✅ At registration | Until account deletion | Authentication |
| **Client names** | ✅ When you create clients | Until you delete | Organization |
| **Industry, fiscal year** | ✅ When you create clients | Until you delete | Client metadata |
| **Activity logs (aggregates)** | ✅ After each analysis | 365 days (1 year) | Workflow tracking |
| **Trial balance data** | ⚠️ Ephemeral processing | **0 seconds** | Analysis only |
| **Account balances** | ⚠️ Ephemeral processing | **0 seconds** | Analysis only |
| **Uploaded files** | ⚠️ Ephemeral processing | **0 seconds** | Analysis only |

**Legend:**
- ✅ Collected and stored
- ⚠️ Processed in-memory, immediately destroyed (Zero-Storage)
- ❌ Never collected or stored

---

**Last updated:** February 26, 2026
**Version:** 2.0

---

*Paciolus — Zero-Storage Trial Balance Diagnostic Intelligence*  
*Your data stays yours.*
