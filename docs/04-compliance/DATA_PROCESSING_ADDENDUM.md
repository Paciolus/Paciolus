# Data Processing Addendum

**Version:** 1.0
**Document Classification:** Legal Agreement
**Effective Date:** February 26, 2026
**Last Updated:** February 26, 2026
**Owner:** legal@paciolus.com
**Review Cycle:** Semi-annual
**Next Review:** August 26, 2026

---

## Preamble

This Data Processing Addendum ("DPA") forms part of the Terms of Service ("Agreement") between the entity agreeing to these terms ("Customer") and Paciolus, Inc. ("Paciolus"), and governs the processing of personal data by Paciolus on behalf of Customer.

This DPA applies to the extent that Paciolus processes personal data that is subject to applicable data protection laws, including the EU General Data Protection Regulation ("GDPR"), the UK General Data Protection Regulation ("UK GDPR"), the California Consumer Privacy Act ("CCPA"), and any other applicable privacy legislation.

---

## Table of Contents

1. [Definitions](#1-definitions)
2. [Roles and Responsibilities](#2-roles-and-responsibilities)
3. [Processing Purpose and Scope](#3-processing-purpose-and-scope)
4. [Categories of Data Subjects and Personal Data](#4-categories-of-data-subjects-and-personal-data)
5. [Security Measures](#5-security-measures)
6. [Subprocessors](#6-subprocessors)
7. [International Data Transfers](#7-international-data-transfers)
8. [Data Subject Rights](#8-data-subject-rights)
9. [Data Deletion and Return](#9-data-deletion-and-return)
10. [Audit Rights](#10-audit-rights)
11. [Data Breach Notification](#11-data-breach-notification)
12. [Liability](#12-liability)
13. [Term and Termination](#13-term-and-termination)

---

## 1. Definitions

**"Controller"** means the entity that determines the purposes and means of the processing of personal data. In this DPA, the Customer is the Controller.

**"Processor"** means the entity that processes personal data on behalf of the Controller. In this DPA, Paciolus is the Processor.

**"Subprocessor"** means a third party engaged by Paciolus to process personal data on behalf of the Customer.

**"Personal Data"** means any information relating to an identified or identifiable natural person that Paciolus processes on behalf of Customer in connection with the Service.

**"Processing"** means any operation performed on personal data, including collection, recording, organization, structuring, storage, adaptation, retrieval, consultation, use, disclosure, erasure, or destruction.

**"Data Subject"** means the identified or identifiable natural person to whom personal data relates.

**"Applicable Data Protection Law"** means all laws and regulations applicable to the processing of personal data under this DPA, including GDPR, UK GDPR, CCPA, and any successor legislation.

---

## 2. Roles and Responsibilities

### 2.1 Customer as Controller

The Customer determines the purposes and means of processing personal data submitted to the Service. The Customer is responsible for:

- Ensuring a lawful basis for processing under applicable data protection law
- Providing required notices to data subjects regarding the use of Paciolus
- Obtaining any required consents from data subjects
- Ensuring the accuracy and relevance of personal data submitted to the Service

### 2.2 Paciolus as Processor

Paciolus processes personal data solely on behalf of and in accordance with the documented instructions of the Customer. Paciolus shall:

- Process personal data only on documented instructions from the Customer, unless required by applicable law
- Ensure that persons authorized to process personal data have committed themselves to confidentiality
- Implement appropriate technical and organizational security measures
- Assist the Customer in responding to data subject requests
- Make available all information necessary to demonstrate compliance with this DPA

### 2.3 Zero-Storage Architecture

Paciolus operates under a Zero-Storage security model for financial data. Uploaded files containing trial balances, general ledgers, payment registers, and other financial data are:

- Processed entirely in-memory
- Never written to disk or database
- Discarded immediately after analysis completes

Only aggregate metadata (category totals, financial ratios, row counts) and user account data are persisted. Line-level account names, balances, and individual transaction details are never stored. See the [Zero-Storage Architecture](ZERO_STORAGE_ARCHITECTURE.md) document for the full technical specification.

---

## 3. Processing Purpose and Scope

### 3.1 Purpose

Paciolus processes personal data solely for the purpose of providing the Service as described in the Agreement, including:

- User account creation and authentication
- Client portfolio organization
- Diagnostic tool execution and result delivery
- Engagement workspace management
- Export and report generation
- Billing and subscription management
- Transactional email delivery (verification, notifications)
- Error monitoring and service reliability

### 3.2 Duration

Processing continues for the duration of the Agreement. Upon termination, Section 9 (Data Deletion and Return) applies.

### 3.3 Nature of Processing

| Processing Activity | Data Involved | Storage Duration |
|---------------------|---------------|-----------------|
| Account authentication | Email, hashed password, name | Account lifetime |
| Client management | Client name, industry, fiscal year | Account lifetime |
| Financial data analysis | Uploaded file contents | Ephemeral (in-memory only) |
| Diagnostic history | Aggregate metadata (row counts, ratios) | 365 days |
| Engagement tracking | Engagement metadata, follow-up narratives | 365 days |
| Billing | Email, Stripe customer ID, plan tier | Account lifetime |
| Email delivery | Email address, verification tokens | 24 hours (tokens), permanent (delivery records via SendGrid) |
| Error monitoring | Anonymized user ID, error context | 90 days (via Sentry) |

---

## 4. Categories of Data Subjects and Personal Data

### 4.1 Data Subjects

- **Authorized Users** — Individuals with accounts on the Customer's Paciolus subscription
- **End Users** — Individuals whose data may appear in files uploaded by Authorized Users (e.g., employee names in payroll registers, vendor contacts in AP data)

### 4.2 Categories of Personal Data

| Category | Examples | Storage |
|----------|----------|---------|
| **Account identifiers** | Email address, display name | Persistent |
| **Authentication credentials** | Hashed password (bcrypt) | Persistent |
| **Billing information** | Stripe customer ID, plan tier, billing interval | Persistent |
| **Client metadata** | Client name, industry, fiscal year end | Persistent |
| **Diagnostic metadata** | Aggregate totals, financial ratios, row counts | 365-day retention |
| **Engagement metadata** | Period, status, materiality threshold | 365-day retention |
| **Follow-up narratives** | Free-text notes (no amounts, no account numbers) | 365-day retention |
| **Uploaded financial data** | Trial balances, ledgers, payment registers | **Never stored** (ephemeral) |

### 4.3 Special Categories

Paciolus does not intentionally process special categories of personal data (Article 9 GDPR). The Customer must not upload files containing health data, biometric data, or other special category data to the Service.

---

## 5. Security Measures

Paciolus implements the following technical and organizational measures to protect personal data. For the complete specification, see the [Security Policy](SECURITY_POLICY.md).

### 5.1 Access Controls

- JWT authentication with 30-minute access tokens and 7-day refresh token rotation
- Refresh token reuse detection (automatic revocation on suspected compromise)
- DB-backed account lockout (5 failed attempts, 15-minute lockout period)
- Role-based access with tier-gated entitlements
- Email verification required for diagnostic tool access

### 5.2 Encryption

- **In transit:** TLS 1.2+ on all connections (HSTS enforced)
- **At rest:** Passwords hashed with bcrypt (explicit rounds). Database encryption managed by hosting provider (Render)
- **Tokens:** Cryptographically random (32-byte hex), time-limited

### 5.3 Application Security

- Stateless HMAC-SHA256 CSRF protection with 60-minute expiry
- Content Security Policy (CSP) with restrictive directives
- Formula injection sanitization on CSV/Excel uploads
- Global body size middleware (110 MB limit)
- Rate limiting across 6 tiers and 5 endpoint categories

### 5.4 Data Minimization

- Zero-Storage architecture for financial data (processed in-memory, never persisted)
- Sentry request body stripping (`before_send` hook removes `event["request"]["data"]`)
- Log redaction: PII masking for email, token, and exception fields in structured logs
- `send_default_pii=False` for all observability integrations

### 5.5 Infrastructure Security

- Production containers: Python 3.12-slim-bookworm, Node 22-alpine
- Automated scanning: Bandit (SAST), pip-audit, npm audit, Dependabot
- Accounting Policy Guard: 5 AST-based invariant checkers in CI pipeline
- PostgreSQL connection pooling with recycle timeouts

### 5.6 Organizational Measures

- Confidentiality commitments for all personnel with access to personal data
- Principle of least privilege for infrastructure access
- Incident response procedures documented in the [Security Policy](SECURITY_POLICY.md)

---

## 6. Subprocessors

### 6.1 Authorization

The Customer provides general written authorization for Paciolus to engage subprocessors as listed in the [Subprocessor List](SUBPROCESSOR_LIST.md).

### 6.2 Obligations

Paciolus shall:

- Maintain an up-to-date list of subprocessors at [SUBPROCESSOR_LIST.md](SUBPROCESSOR_LIST.md)
- Impose data protection obligations on each subprocessor that are no less protective than those in this DPA
- Conduct a security assessment of each subprocessor before engagement (vendor risk assessment documented in [Security Policy](SECURITY_POLICY.md) Section 9)
- Remain liable to the Customer for the acts and omissions of its subprocessors

### 6.3 Notification of Changes

Paciolus shall notify the Customer at least **30 days** before adding or replacing a subprocessor by updating the [Subprocessor List](SUBPROCESSOR_LIST.md). The Customer may object to a new subprocessor within the 30-day notice period by contacting privacy@paciolus.com. If the objection cannot be resolved, the Customer may terminate the Agreement.

---

## 7. International Data Transfers

### 7.1 Data Location

All personal data is processed and stored in the **United States**.

| Data Type | Location | Provider |
|-----------|----------|----------|
| User accounts and client metadata | US (Oregon) | Render |
| Financial data (ephemeral) | US (Oregon) | Render (in-memory only) |
| Payment information | US | Stripe |
| Error telemetry | US | Sentry |
| Email delivery metadata | US | SendGrid |
| Static assets (frontend) | US/Global CDN | Vercel |

### 7.2 Transfer Mechanisms

For transfers of personal data from the EEA, UK, or Switzerland to the United States, Paciolus relies on the following mechanisms:

- **EU-US Data Privacy Framework** — Paciolus and its subprocessors participate in or benefit from adequacy decisions covering the EU-US Data Privacy Framework where applicable
- **Standard Contractual Clauses (SCCs)** — Where the Data Privacy Framework does not apply, Paciolus offers the European Commission's Standard Contractual Clauses (Module 2: Controller to Processor) as a transfer mechanism. The Customer may request execution of SCCs by contacting legal@paciolus.com
- **UK International Data Transfer Agreement** — For UK transfers, supplementary clauses are available upon request

### 7.3 Subprocessor Transfer Mechanisms

Paciolus ensures each subprocessor maintains an appropriate transfer mechanism. See the [Subprocessor List](SUBPROCESSOR_LIST.md) for per-provider details.

---

## 8. Data Subject Rights

### 8.1 Assistance

Paciolus shall assist the Customer in responding to data subject requests to exercise their rights under applicable data protection law, including rights of access, rectification, erasure, restriction, portability, and objection.

### 8.2 Scope

Given the Zero-Storage architecture, data subject requests concerning uploaded financial data generally do not apply — such data is not persisted and cannot be retrieved after analysis.

For persistent data (user accounts, client metadata, diagnostic history), Paciolus provides:

- **Access:** Users can view their profile data via the Settings page
- **Rectification:** Users can update their name and email via the Settings page
- **Erasure:** Users can clear activity history (Settings > Privacy). Full account deletion available upon request to privacy@paciolus.com
- **Portability:** Diagnostic results are exportable as PDF/Excel/CSV during the active session

### 8.3 Response Timeline

Paciolus shall respond to Customer requests for assistance within **10 business days**.

---

## 9. Data Deletion and Return

### 9.1 During the Agreement

- **Financial data:** Automatically deleted from memory upon analysis completion (Zero-Storage)
- **Diagnostic metadata:** Subject to 365-day retention, then automatically purged by the retention cleanup job
- **User-initiated deletion:** Activity history can be cleared at any time via Settings > Privacy

### 9.2 Upon Termination

Upon termination of the Agreement, Paciolus shall:

1. **Immediately cease processing** personal data on behalf of the Customer
2. **Provide data export** — The Customer may export all available data (diagnostic results, client metadata) prior to account deactivation
3. **Delete personal data** within **30 days** of termination, including:
   - User account records
   - Client metadata
   - Diagnostic history and engagement metadata
   - Billing records (except where retention is required by applicable law)
4. **Certify deletion** upon written request from the Customer

### 9.3 Exceptions

Paciolus may retain personal data beyond termination where required by applicable law (e.g., tax records for billing transactions). Such data shall be isolated and protected, and deleted when the legal obligation expires.

---

## 10. Audit Rights

### 10.1 Information Requests

Paciolus shall make available to the Customer all information reasonably necessary to demonstrate compliance with this DPA. This includes:

- Current [Security Policy](SECURITY_POLICY.md) and [Zero-Storage Architecture](ZERO_STORAGE_ARCHITECTURE.md) documentation
- Current [Subprocessor List](SUBPROCESSOR_LIST.md)
- SOC 2 Type II reports or equivalent certifications from subprocessors (upon request)
- Summary of security incidents affecting the Customer's data (if any)

### 10.2 On-Site Audits

The Customer may conduct or commission an audit of Paciolus's processing activities under this DPA, subject to the following conditions:

- The Customer shall provide at least **30 days** written notice
- Audits shall be conducted during normal business hours
- Audits shall not unreasonably interfere with Paciolus's operations
- The auditor must execute a confidentiality agreement before accessing Paciolus premises or systems
- The Customer bears the cost of the audit unless the audit reveals a material breach of this DPA

### 10.3 Frequency

The Customer may exercise audit rights no more than **once per calendar year**, unless required by a supervisory authority or following a confirmed data breach.

---

## 11. Data Breach Notification

### 11.1 Notification Obligation

Paciolus shall notify the Customer **without undue delay** (and in any event within **72 hours**) after becoming aware of a personal data breach affecting the Customer's data.

### 11.2 Notification Contents

The notification shall include, to the extent reasonably available:

- The nature of the breach, including categories and approximate number of data subjects and records affected
- The name and contact details of Paciolus's designated point of contact
- The likely consequences of the breach
- The measures taken or proposed to address the breach and mitigate its effects

### 11.3 Zero-Storage Impact

Due to the Zero-Storage architecture, a breach of the application server would not expose historical financial data, as such data is never persisted. The potential impact of a breach is limited to:

- User account credentials (hashed passwords)
- Client metadata (names, industry classifications)
- Aggregate diagnostic metadata (ratios, row counts)
- Billing records (Stripe customer IDs, plan tiers)

### 11.4 Cooperation

Paciolus shall cooperate with the Customer and take reasonable steps to assist in the investigation, mitigation, and remediation of any data breach. Paciolus shall not inform any third party of a breach without the Customer's prior consent, unless required by law.

---

## 12. Liability

Liability for breaches of this DPA shall be subject to the limitations set forth in the Agreement (Terms of Service, Section 10). Nothing in this DPA limits either party's liability for breaches of applicable data protection law to the extent such limitation is prohibited by that law.

---

## 13. Term and Termination

### 13.1 Term

This DPA takes effect on the date the Customer accepts the Agreement and continues for the duration of Paciolus's processing of personal data on behalf of the Customer.

### 13.2 Survival

Sections 9 (Data Deletion and Return), 10 (Audit Rights), 11 (Data Breach Notification), and 12 (Liability) survive termination of this DPA.

---

## Contact

For questions regarding this DPA, contact:

- **Privacy inquiries:** privacy@paciolus.com
- **Legal inquiries:** legal@paciolus.com
- **Security inquiries:** security@paciolus.com

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-26 | Initial Data Processing Addendum |

---

*Paciolus, Inc. — Professional Audit Intelligence Platform*
