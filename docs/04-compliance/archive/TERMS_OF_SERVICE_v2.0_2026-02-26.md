# Terms of Service

**Effective Date:** February 26, 2026
**Last Updated:** February 26, 2026
**Company:** Paciolus, Inc.
**Contact:** legal@paciolus.com

---

## Agreement to Terms

By accessing or using Paciolus (the "Service"), you agree to be bound by these Terms of Service ("Terms"). If you do not agree to these Terms, you may not use the Service.

**Important**: This is a legal agreement between you and Paciolus, Inc. Please read it carefully.

---

## Table of Contents

1. [Service Description](#1-service-description)
2. [Eligibility](#2-eligibility)
3. [Account Registration](#3-account-registration)
4. [Acceptable Use](#4-acceptable-use)
5. [Zero-Storage Model](#5-zero-storage-model)
6. [Intellectual Property](#6-intellectual-property)
7. [User Content](#7-user-content)
8. [Fees and Payment](#8-fees-and-payment)
9. [Disclaimer of Warranties](#9-disclaimer-of-warranties)
10. [Limitation of Liability](#10-limitation-of-liability)
11. [Indemnification](#11-indemnification)
12. [Termination](#12-termination)
13. [Dispute Resolution](#13-dispute-resolution)
14. [Modifications](#14-modifications)
15. [General Provisions](#15-general-provisions)
16. [Contact Information](#16-contact-information)

---

## 1. Service Description

### 1.1 What Paciolus Provides

Paciolus is a **trial balance diagnostic intelligence platform** designed for financial professionals. The Service provides:

- Trial balance upload and analysis (CSV, Excel, TSV, OFX, IIF, ODS, PDF, and other supported formats)
- Automated account classification and anomaly detection
- Materiality threshold configuration
- Diagnostic summary reports (PDF/Excel exports)
- Client metadata management (names, industries, fiscal year ends)
- Activity history tracking (aggregate summaries only)

**Key Feature:** Zero-Storage architecture—your trial balance data is processed in-memory and never persisted to our servers (see Section 5).

### 1.2 What Paciolus Does NOT Provide

The Service is **NOT**:
- ❌ An accounting software (we do not maintain your books)
- ❌ An audit engagement (we are not performing a financial statement audit)
- ❌ Assurance services (we do not provide opinions or certifications)
- ❌ Legal advice (we are not attorneys)
- ❌ Tax advice (we are not tax advisors)
- ❌ Investment advice (we are not financial advisors)

**No professional-client relationship:** Use of the Service does not create an accountant-client, attorney-client, or any other professional relationship.

---

## 2. Eligibility

### 2.1 Age Requirement

You must be at least **18 years old** to use Paciolus.

### 2.2 Capacity

By using the Service, you represent and warrant that:
- You have the legal capacity to enter into this agreement
- You are not prohibited by law from using the Service
- Your use of the Service complies with all applicable laws

### 2.3 Professional Use

Paciolus is intended for **professional use** by:
- Fractional CFOs
- Accountants
- Financial professionals
- Business owners

If you are using the Service on behalf of a company or organization:
- You represent that you have authority to bind that entity
- "You" and "your" refer to both you individually and the entity

---

## 3. Account Registration

### 3.1 Account Creation

To use Paciolus, you must create an account:
- **Required information:** Email address, password
- **Optional information:** Client metadata (if you manage clients)

**Password requirements:**
- Minimum 8 characters
- At least one uppercase letter, lowercase letter, number, and special character

### 3.2 Account Security

**You are responsible for:**
- ✅ Maintaining the confidentiality of your password
- ✅ All activities that occur under your account
- ✅ Notifying us immediately of unauthorized access (security@paciolus.com)

**We are NOT liable for** losses arising from unauthorized use of your account if you failed to secure your credentials.

### 3.3 Accurate Information

You agree to provide accurate, current information and update it as necessary. Providing false information may result in account termination.

---

## 4. Acceptable Use

### 4.1 Permitted Uses

You may use Paciolus **only** for:
- Analyzing trial balances for legitimate business purposes
- Managing client metadata (if you are a fractional CFO/accountant)
- Generating diagnostic reports for your own use or your clients

### 4.2 Prohibited Uses

You may **NOT** use Paciolus to:

| Prohibited Activity | Example |
|---------------------|---------|
| **Illegal activities** | Money laundering, fraud detection evasion, tax evasion |
| **Unauthorized access** | Hacking, bypassing security measures, brute force attacks |
| **Abusive behavior** | Uploading malware, excessive API requests (DOS attacks) |
| **Reverse engineering** | Decompiling, disassembling, or reverse-engineering the Service |
| **Reselling** | Offering Paciolus as a white-label service without permission |
| **Competitive intelligence** | Using the Service to build a competing product |
| **Violating rights** | Uploading trial balances you don't have permission to analyze |
| **Spam or scraping** | Automated data extraction, web scraping |

### 4.3 Rate Limits

**Fair use policy:**

| Tier | Diagnostic Limit | Client Limit |
|------|-------------------|--------------|
| **Free** | 10 per month | 3 |
| **Solo** | 20 per month | 10 |
| **Team** | Unlimited | Unlimited |
| **Organization** | Unlimited | Unlimited |

**Abuse prevention:** We may throttle or suspend accounts engaging in excessive use (e.g., >1,000 analyses per day without legitimate business justification).

---

## 5. Zero-Storage Model

**THIS SECTION IS CRITICAL. PLEASE READ CAREFULLY.**

### 5.1 No Financial Data Storage

Paciolus operates under a **Zero-Storage** model:

**What happens to your trial balance data:**
1. You upload a CSV/Excel file via your browser
2. The file is transmitted via HTTPS to our server
3. **The file is loaded into temporary memory (RAM)**
4. Analysis is performed (typically 3-5 seconds)
5. Results are sent back to your browser as a JSON response
6. **The memory buffer is immediately cleared (Python gc.collect())**
7. **The file does NOT touch our disk or database**

**Key implications:**
- ❌ We cannot "recover" your trial balance data later
- ❌ We cannot perform year-over-year comparisons (no historical storage)
- ❌ If you close your browser tab, the results are gone
- ✅ Your data cannot be leaked in a breach (it doesn't exist to leak)

### 5.2 What We DO Store

**Limited metadata** is stored for business functionality:

| Data Type | Storage | Example |
|-----------|---------|---------|
| **User credentials** | Stored | Email, bcrypt password hash |
| **Client metadata** | Stored | Client names, industries, fiscal year ends |
| **Activity logs (aggregates)** | Stored (365 days) | "Analyzed 500 rows, balanced, 3 anomalies" |
| **Trial balance data** | **Never stored** | "Cash: $50,000, A/R: $25,000" |

**For full details, see:** [ZERO_STORAGE_ARCHITECTURE.md](./ZERO_STORAGE_ARCHITECTURE.md)

### 5.3 Your Responsibilities

**Because we do not retain your trial balance data:**
- ✅ **You are responsible** for maintaining your own records
- ✅ **You must save** exported PDF/Excel reports if you need them later
- ✅ **You must re-upload** the trial balance if you want to re-analyze it

**We are not liable** for your inability to retrieve data we were never designed to store.

---

## 6. Intellectual Property

### 6.1 Paciolus's Intellectual Property

**We own:**
- The Paciolus brand, logo, and trademarks
- The software code (frontend, backend, algorithms)
- The design and user interface
- The "Oat & Obsidian" design system
- All documentation and marketing materials

**You receive a limited license** to use the Service for its intended purpose. You do NOT own the software and may not:
- Copy, modify, or distribute the software
- Remove copyright or proprietary notices
- Use our trademarks without permission

### 6.2 User's Intellectual Property

**You retain ownership** of:
- Your trial balance data (which is never stored on our servers)
- Your client metadata
- Any reports you generate using the Service

**License to us:** You grant us a limited license to:
- Process your uploaded files (ephemeral, in-memory only)
- Display your client metadata in your account
- Use aggregate, anonymized data for service improvement

**We do NOT claim ownership** of your financial data or reports.

---

## 7. User Content

### 7.1 Data You Upload

**You represent and warrant that:**
- You have the legal right to upload and analyze the trial balance data
- The data does not violate any third-party rights (e.g., confidentiality agreements)
- The data does not contain illegal content

**Client data:** If you are uploading trial balances on behalf of clients, you represent that you have their permission to do so.

### 7.2 Responsibility for Accuracy

**We rely on the data you provide.** If your trial balance is incorrect, our analysis will be incorrect. We are not responsible for errors in your source data.

---

## 8. Fees and Payment

### 8.1 Pricing Tiers

| Tier | Monthly | Annual | Included Seats |
|------|---------|--------|----------------|
| **Free** | $0 | $0 | 1 |
| **Solo** | $50/month | $500/year | 1 |
| **Team** | $130/month | $1,300/year | 3 |
| **Organization** | $400/month | $4,000/year | 3 |

Annual billing includes an approximate 17% discount compared to monthly billing.

**Current pricing:** See https://paciolus.com/pricing

**Note:** Public plan names displayed in the application or marketing materials may differ from internal identifiers used in API responses or system logs.

### 8.2 Seat-Based Pricing

Paid multi-user plans (Team, Organization) include a number of base seats at no additional cost (see Section 8.1). Additional seats beyond the base allocation are billed at the following rates:

| Seat Position | Monthly (per seat) | Annual (per seat) |
|---------------|--------------------|--------------------|
| Base seats (included in plan) | $0 | $0 |
| Seats 4–10 | $80/month | $800/year |
| Seats 11–25 | $70/month | $700/year |

Each additional seat is priced at the rate corresponding to its position in the tier schedule (i.e., rates are not blended across tiers).

**Seat enforcement:** We may enforce seat limits through logging-only monitoring or active access restrictions. We will provide reasonable notice before transitioning from monitoring to active enforcement for existing subscribers.

### 8.3 Custom Enterprise (26+ Seats)

Self-service seat purchases are available for up to 25 seats. Organizations requiring more than 25 seats must contact our sales team for a custom agreement. Custom enterprise subscriptions may include negotiated pricing, dedicated support, and tailored SLAs.

**Contact:** https://paciolus.com/contact

### 8.4 Trial Period

New subscribers to paid tiers may be eligible for a **7-day free trial**. Trial availability is subject to change and may not be offered on all plans or in all regions. At the end of the trial period, your subscription will automatically convert to a paid subscription unless canceled.

### 8.5 Promotions

From time to time, we may offer promotional discounts.

**Promotion rules:**
- Only one promotional discount may be applied per subscription at a time
- Promotions are non-stackable (you cannot combine multiple discount codes)
- Promotional terms (duration, eligible billing intervals) are specified at the time of the offer
- We reserve the right to modify or discontinue promotions at any time

### 8.6 Payment Terms

- **Billing cycle:** Monthly or annual
- **Payment method:** Credit card via Stripe (we do not store your card details)
- **Automatic renewal:** Subscriptions renew automatically unless canceled
- **Cancellation:** You may cancel anytime; access continues through the end of the current billing period. No refunds for partial billing periods.

### 8.7 Free Tier Limitations

The Free tier is intended for evaluation and light use. Free tier accounts are subject to the limits specified in Section 4.3. If you exceed these limits:
- Certain features may be restricted until the next billing cycle
- You may be prompted to upgrade to a paid tier

### 8.8 Price Changes

**We may change pricing** with 30 days' notice. Grandfathered pricing may apply to existing customers at our discretion.

### 8.9 Taxes

**Prices do not include taxes.** You are responsible for applicable sales tax, VAT, or other taxes.

---

## 9. Disclaimer of Warranties

**READ THIS SECTION CAREFULLY. IT LIMITS OUR LIABILITY.**

### 9.1 "As Is" Provision

**THE SERVICE IS PROVIDED "AS IS" WITHOUT WARRANTIES OF ANY KIND, EXPRESS OR IMPLIED.**

We disclaim all warranties, including but not limited to:
- ❌ Merchantability
- ❌ Fitness for a particular purpose
- ❌ Non-infringement
- ❌ Accuracy or completeness of results
- ❌ Uninterrupted or error-free operation

### 9.2 No Professional Advice

**PACIOLUS IS NOT AN AUDIT FIRM.** The Service:
- Does NOT provide audit opinions or assurance
- Does NOT constitute professional accounting services
- Does NOT replace the need for a CPA or auditor
- Is NOT a substitute for professional judgment

**You are responsible** for interpreting diagnostic results and making business decisions.

### 9.3 Diagnostic Tool Only

**The Service is a diagnostic tool**—it identifies potential issues but does not:
- Guarantee complete detection of all errors
- Replace manual review or professional skepticism
- Provide legal or tax advice
- Meet audit standards (GAAS, PCAOB, ISA)

**Example:** If Paciolus flags 3 anomalies, there may be additional issues not detected. Conversely, flagged items may be intentional or immaterial.

### 9.4 Third-Party Dependencies

**We rely on third-party services** (Vercel, Render, Stripe). We are not liable for their failures or security breaches.

### 9.5 No Guarantees

**We do not guarantee:**
- 100% uptime (target: 99.9% monthly)
- Zero data loss (Zero-Storage means no storage to lose)
- Compatibility with all browser versions
- Specific response times

---

## 10. Limitation of Liability

**THIS SECTION LIMITS DAMAGES YOU CAN RECOVER FROM US.**

### 10.1 Exclusion of Consequential Damages

**TO THE MAXIMUM EXTENT PERMITTED BY LAW, PACIOLUS SHALL NOT BE LIABLE FOR:**
- Indirect, incidental, or consequential damages
- Lost profits or revenue
- Lost data (note: Zero-Storage architecture)
- Business interruption
- Reputational harm

**EVEN IF WE WERE ADVISED** of the possibility of such damages.

### 10.2 Liability Cap

**OUR TOTAL LIABILITY TO YOU** for any claim arising from these Terms or the Service **SHALL NOT EXCEED** the greater of:
- $100 USD, or
- The amount you paid to Paciolus in the 12 months preceding the claim

**Example:** If you pay $50/month and have used the Service for 6 months ($300 total), our maximum liability is $300.

### 10.3 Exceptions

**This limitation does NOT apply to:**
- Our gross negligence or willful misconduct
- Violations of applicable law that cannot be waived
- Personal injury or death caused by our negligence (if applicable)

### 10.4 Jurisdictional Variations

**Some jurisdictions do not allow** exclusion of certain warranties or limitation of liability. If you are in such a jurisdiction, the above limitations may not apply to you.

---

## 11. Indemnification

### 11.1 Your Indemnification Obligation

**You agree to indemnify and hold harmless** Paciolus, its officers, directors, employees, and agents from any claims, damages, or expenses arising from:

- Your violation of these Terms
- Your violation of any law or regulation
- Your violation of third-party rights (e.g., uploading confidential data without permission)
- Your use of the Service in a negligent or unlawful manner

**Example:** If you upload a client's trial balance without their permission and they sue us, you agree to cover our legal costs and damages.

### 11.2 Our Rights

If we are subject to a claim due to your actions:
- We may assume control of the defense
- You must cooperate with our defense
- You may not settle the claim without our consent

---

## 12. Termination

### 12.1 Termination by You

**You may terminate your account at any time:**
- Settings → Delete Account (instant)
- Email legal@paciolus.com

**Upon termination:**
- Your subscription ends (no refunds for partial months)
- All data deleted (user account, client metadata, activity logs)
- Access to the Service immediately revoked

### 12.2 Termination by Us

**We may suspend or terminate your account if:**
- You violate these Terms
- You engage in prohibited activities (Section 4.2)
- Your account is inactive for >12 months
- Required by law or legal process

**Notice:** We will provide 30 days' notice for non-emergency terminations. For violations, termination may be immediate.

### 12.3 Effect of Termination

**Upon termination:**
- Your license to use the Service ends immediately
- You must cease all use of Paciolus
- You must delete any exported materials if required by us
- Sections 6, 9, 10, 11, and 13 survive termination

---

## 13. Dispute Resolution

### 13.1 Governing Law

**These Terms are governed by the laws of the State of [State], United States,** without regard to conflict of law principles.

### 13.2 Informal Resolution

**Before filing a lawsuit,** you agree to attempt informal resolution:
1. Email legal@paciolus.com with a description of the dispute
2. We will respond within 30 days
3. Both parties will negotiate in good faith

### 13.3 Arbitration (For U.S. Users)

**If informal resolution fails, disputes will be resolved by binding arbitration** under the American Arbitration Association (AAA) rules.

**Key terms:**
- **Location:** [City, State]
- **Costs:** Each party pays their own costs; arbitrator fees split equally
- **Discovery:** Limited to depositions and document requests
- **Appeal:** Arbitrator's decision is final and binding

**Class action waiver:** You agree to resolve disputes individually, not as part of a class action.

### 13.4 Exceptions to Arbitration

**The following may be brought in court:**
- Small claims court actions (\u003c$10,000)
- Injunctive relief (e.g., preventing unauthorized use of our IP)
- Disputes involving intellectual property

### 13.5 European Users

**If you are in the European Union,** you may bring disputes in your local courts under Brussels I Regulation.

---

## 14. Modifications

### 14.1 Changes to Terms

**We may modify these Terms** at any time.

**Notice:**
- **Material changes:** Email notification 30 days in advance
- **Minor changes:** Updated "Last Updated" date at the top
- **Continued use:** Constitutes acceptance of new Terms

**Your rights:**
- Review changes at https://paciolus.com/terms/history
- Delete your account if you disagree

### 14.2 Changes to the Service

**We may modify the Service**, including:
- Adding or removing features
- Changing pricing (with notice)
- Deprecating functionality

**We are not liable** for changes that affect your use of the Service, provided we give reasonable notice.

---

## 15. General Provisions

### 15.1 Entire Agreement

**These Terms, together with the Privacy Policy,** constitute the entire agreement between you and Paciolus.

### 15.2 Severability

If any provision of these Terms is found invalid, the remaining provisions remain in effect.

### 15.3 Waiver

**Failure to enforce** any provision does not waive our right to enforce it later.

### 15.4 Assignment

**You may not assign** these Terms without our consent. We may assign these Terms (e.g., in a merger or acquisition).

### 15.5 Force Majeure

**We are not liable for delays or failures** due to circumstances beyond our control (e.g., natural disasters, war, pandemic, government action).

### 15.6 No Third-Party Beneficiaries

**These Terms do not create** rights for third parties (except our affiliates and service providers).

### 15.7 Export Control

**You may not export** the Service to countries subject to U.S. export restrictions (e.g., embargoed countries).

### 15.8 Government Users

**If you are a U.S. government entity,** the Service is "Commercial Computer Software" under FAR 12.212 and DFARS 227.7202.

---

## 16. Contact Information

### Legal Inquiries

| Type | Contact | Response Time |
|------|---------|---------------|
| **General questions** | legal@paciolus.com | 5 business days |
| **Terms violations** | legal@paciolus.com | 2 business days |
| **DMCA notices** | dmca@paciolus.com | 48 hours |
| **Arbitration notices** | legal@paciolus.com | 5 business days |

**Mailing address:**  
Paciolus, Inc.  
[Address to be added]  
[City, State, ZIP]  
United States

**Registered agent (for legal service):**  
[To be appointed]

---

## Acknowledgment

**BY USING PACIOLUS, YOU ACKNOWLEDGE THAT:**
- ✅ You have read and understood these Terms
- ✅ You agree to be bound by these Terms
- ✅ You are authorized to accept these Terms (individually or on behalf of an entity)
- ✅ You understand that Paciolus is a diagnostic tool, not an audit or assurance service
- ✅ You understand the Zero-Storage model and your responsibility to maintain your own records

**If you do not agree, you may not use the Service.**

---

**Last updated:** February 26, 2026
**Version:** 2.0
**Version history:** https://paciolus.com/terms/history

---

*Paciolus — Zero-Storage Trial Balance Diagnostic Intelligence*  
*Professional tools for financial professionals.*
