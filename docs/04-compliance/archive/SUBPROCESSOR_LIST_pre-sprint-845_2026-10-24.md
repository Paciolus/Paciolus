# Subprocessor List

**Version:** 1.1
**Document Classification:** Public
**Effective Date:** February 26, 2026
**Last Updated:** October 23, 2026
**Owner:** privacy@paciolus.com
**Review Cycle:** Quarterly
**Next Review:** January 23, 2027

---

## Overview

This document lists all third-party subprocessors engaged by Paciolus, Inc. ("Paciolus") to process personal data on behalf of Customers, as referenced in the [Data Processing Addendum](DATA_PROCESSING_ADDENDUM.md) Section 6.

Paciolus will notify Customers at least **30 days** before adding or replacing a subprocessor. Customers may subscribe to change notifications by contacting privacy@paciolus.com.

---

## Active Subprocessors

| Provider | Service Function | Data Categories Processed | Hosting Region | Transfer Mechanism | Security Certifications | DPA Status | Date Added |
|----------|-----------------|--------------------------|----------------|-------------------|------------------------|------------|------------|
| **Render** | Backend API hosting, managed PostgreSQL database | User credentials (encrypted), client metadata, diagnostic metadata (aggregates), engagement metadata, activity logs | United States (Oregon) | EU-US DPF / SCCs | SOC 2 Type II | Signed | 2025-01-01 |
| **Vercel** | Frontend hosting, CDN, static asset delivery | None (static files only; no personal data processed) | United States / Global CDN | EU-US DPF / SCCs | SOC 2 Type II, ISO 27001 | Signed | 2025-01-01 |
| **Stripe** | Payment processing, subscription management, billing portal | Email address, billing information (card details handled by Stripe — never touch Paciolus servers) | United States | EU-US DPF / SCCs | PCI DSS Level 1, SOC 2 Type II | Signed | 2025-12-01 |
| **Sentry** | Error tracking, application performance monitoring (APM) | Anonymized user IDs, error messages (sanitized), performance traces (10% sampled). Request bodies, frame local variables, exception messages and log breadcrumbs stripped by the `before_send` hook (Sprint 840) | United States | EU-US DPF / SCCs | SOC 2 Type II | Signed | 2025-06-01 |
| **SendGrid** (Twilio) | Transactional email delivery | Email addresses, verification tokens (24-hour expiry), user display names | United States | EU-US DPF / SCCs | SOC 2 Type II, ISO 27001 | Signed | 2025-01-01 |
| **Cloudflare** (R2 object storage) | Storage of export-share file content — the `paciolus-exports` bucket, keyed `shares/<share_token_hash>` | **Customer financial export content** (PDF / Excel / CSV bytes of an export the Customer has chosen to share via a passcode-protected link). Object keys are SHA-256 hashes of the share token and carry no account or client identifiers | Eastern North America (ENAM) | EU-US DPF / SCCs | SOC 2 Type II, ISO 27001 | Signed | 2026-04-23 |

---

## Data Categories Reference

| Category | Description | Retention | Stored By |
|----------|-------------|-----------|-----------|
| **User credentials** | Email (plaintext), password (bcrypt hash), display name | Account lifetime | Render (PostgreSQL) |
| **Client metadata** | Client name, industry classification, fiscal year end | Account lifetime | Render (PostgreSQL) |
| **Diagnostic metadata** | Aggregate totals, financial ratios, row counts, anomaly counts | 365 days | Render (PostgreSQL) |
| **Engagement metadata** | Period, status, materiality threshold, follow-up narratives | 365 days | Render (PostgreSQL) |
| **Billing information** | Stripe customer ID, subscription tier, billing interval | Account lifetime | Render (PostgreSQL) + Stripe |
| **Email delivery data** | Recipient email, delivery status, verification tokens | 24 hours (tokens); per SendGrid policy (delivery logs) | SendGrid |
| **Error telemetry** | Anonymized user ID, error context, stack traces | 90 days | Sentry |
| **Export-share content** | Rendered export files (PDF / Excel / CSV) behind a Customer-created share link | Until the share expires or is revoked | Cloudflare R2 (`paciolus-exports`) |
| **Uploaded financial data** | Trial balances, ledgers, payment registers | **Not kept** (in memory for the request only) | None |

---

## Zero-Storage Compliance

All subprocessors operate in compliance with the Paciolus Zero-Storage architecture:

- **Render / PostgreSQL:** Stores only aggregate metadata (row counts, ratio values, category totals). No line-level account names, balances, or transaction details are ever written to the database.
- **Vercel:** Serves static frontend assets only. No personal data is transmitted to or stored by Vercel.
- **Stripe:** Receives only email addresses and billing information. No financial analysis data is shared with Stripe. Credit card details are handled entirely by Stripe's PCI-compliant infrastructure and never touch Paciolus servers.
- **Sentry:** A `before_send` hook strips all request body data before transmission. `send_default_pii=False` is enforced. No financial data reaches Sentry.
- **SendGrid:** Receives only email addresses and short-lived verification tokens. No financial data is included in transactional emails.
- **Cloudflare (R2):** The one subprocessor that does hold Customer financial content, and the exception that the Zero-Storage architecture document calls out explicitly. It stores only exports the Customer has *chosen* to share through a link, optionally passcode-protected. Objects are keyed by the SHA-256 hash of the share token, so the key reveals nothing about the client or engagement; a passcode, if set, is hashed with Argon2id and kept in the database, not with the object; and the object is deleted when the share is revoked or expires. Trial balances and ledgers as uploaded are not written to storage.

---

## Infrastructure-Only Services (Not Subprocessors)

The following services are used for infrastructure or operations but do **not** process personal data on behalf of Customers:

| Service | Purpose | Data Exposure |
|---------|---------|--------------|
| **GitHub** | Source code repository, CI/CD pipeline | No customer data (code and configuration only) |
| **Prometheus** | Self-hosted metrics collection | Aggregated counters only (no PII, no customer data) |
| **Dependabot** | Automated dependency security updates | No customer data |
| **Cloudflare** (DNS, CDN fallback) | Authoritative DNS for paciolus.com | No customer data. Distinct from the R2 object-storage role above, which **is** a processor and is listed as one |

---

## Subprocessor Change Log

| Date | Change Type | Provider | Description |
|------|------------|----------|-------------|
| 2026-02-26 | Initial publication | All | Subprocessor list created (v1.0) |
| 2026-10-23 | **Addition (retroactive disclosure)** | Cloudflare (R2) | Export-share file content has been written to the `paciolus-exports` R2 bucket since Sprint 611 (2026-04-23) and was not listed. Added with the original engagement date rather than today's, so the record is accurate rather than flattering. Found by the full-spectrum review of 2026-10-22 (finding C-1). |
| 2026-10-23 | **Removal by elimination** | Google LLC (Fonts) | `globals.css` loaded three font families from `fonts.googleapis.com`, transmitting every visitor's IP address and User-Agent to Google on every page load. Rather than disclose a processor we did not need, Sprint 807 self-hosts the fonts via `next/font`; the two Google hosts are gone from the CSP allowlist. |

---

## Notification and Objection

### Subscribing to Updates

Customers may subscribe to subprocessor change notifications by emailing privacy@paciolus.com with subject "Subprocessor Notification Subscription."

### Objection Process

Per the [Data Processing Addendum](DATA_PROCESSING_ADDENDUM.md) Section 6.3:

1. Paciolus publishes the proposed change at least **30 days** before it takes effect
2. The Customer may object in writing to privacy@paciolus.com within the 30-day notice period
3. Paciolus will work with the Customer to find a mutually acceptable resolution
4. If no resolution is reached, the Customer may terminate the Agreement in accordance with the Terms of Service

---

## Contact

- **Subprocessor inquiries:** privacy@paciolus.com
- **DPA requests:** legal@paciolus.com
- **Security assessments:** security@paciolus.com

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-26 | Initial subprocessor list |
| 1.1 | 2026-10-23 | Added Cloudflare (R2) as a processor of export-share file content, backdated to its actual engagement date. Recorded the elimination of Google Fonts. Added an export-share data category. Sprint 807, finding C-1. |

---

*Paciolus, Inc. — Professional Audit Intelligence Platform*
