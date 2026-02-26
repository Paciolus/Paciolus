# Compliance Documentation Changelog

All notable changes to Paciolus compliance documents are recorded here.

Format follows [Keep a Changelog](https://keepachangelog.com/). Each entry specifies the document, version, and effective date.

---

## [2026-02-26] Security Policy v2.1

**Type:** Minor
**Document:** SECURITY_POLICY.md
**Previous Version:** 2.0

### Added
- Section 3.4: Request Integrity Controls (HMAC CSRF, constant-time comparison)
- Section 3.5: Rate Limit Tiers (6-tier table with per-endpoint, per-user, per-tier policies)
- Section 8.2: Log Redaction (PII masking for email, token, exception fields)

### Changed
- Restructured Sections 3.3–3.5 into dedicated subsections for clarity

---

## [2026-02-26] Zero-Storage Architecture v2.1

**Type:** Minor
**Document:** ZERO_STORAGE_ARCHITECTURE.md
**Previous Version:** 2.0

### Added
- Section 1.3: Terminology Clarity — defines "zero-storage" scope (raw financial data, not all metadata)
- Section 5 preamble: Scope Boundaries — explicit boundary between zero-storage and metadata retention
- Section 10.2: Control Verification — 6 automated safeguards table (retention cleanup, ORM guard, memory_cleanup, Sentry stripping, Accounting Policy Guard, tool session sanitization)

---

## [2026-02-26] Terms of Service v2.0

**Type:** Major
**Document:** TERMS_OF_SERVICE.md
**Previous Version:** 1.0

### Changed
- Section 1.1: File format support updated from "CSV/Excel" to 10 supported formats
- Section 4.3: Rate limits aligned to tier entitlements (Free 10/mo, Solo 20/mo, Team/Org unlimited)
- Section 5.2: Retention period corrected from "2 years" to "365 days"
- Section 8.1: Pricing table replaced with Free/Solo/Team/Organization values
- Section 10.2: Liability example updated ($29 to $50)

### Added
- Section 8.2: Seat-based pricing (base seats, add-on tiers, enforcement)
- Section 8.3: Custom Enterprise (26+ seats, contact sales)
- Section 8.4: Trial Period (7-day)
- Section 8.5: Promotions (non-stackable, one discount at a time)
- Section 8.6: Payment Terms (annual ~17% discount, cancel at period end)
- Section 8.7: Free tier limitations matching entitlements
- Clause: "Public plan names may differ from internal identifiers"

### Removed
- References to purchasable "Professional" and "Starter" tiers

---

## [2026-02-26] Privacy Policy v2.0

**Type:** Major
**Document:** PRIVACY_POLICY.md
**Previous Version:** 1.0

### Changed
- Retention periods corrected from "2 years" to "365 days (1 year)" for activity logs and diagnostic summaries
- Section numbering updated (Sections 4-13 renumbered after new Section 4 insertion)

### Added
- Section 4: Data Retention Governance (canonical table with 15 data classes)
- Section 4.1: Retention schedule with ephemeral vs. bounded distinction
- Section 4.2: Configurable retention governance
- Section 4.3: Policy precedence rules
- Section 4.4: Archival vs. deletion explanation (soft-delete model)
- Data classes: engagement metadata, billing events, follow-up items, subscriptions, tool runs, refresh tokens, verification tokens

---

## [2026-02-26] Security Policy v2.0

**Type:** Major
**Document:** SECURITY_POLICY.md
**Previous Version:** 1.0

### Changed
- JWT: "8 hour" expiration to "30-minute access + 7-day refresh rotation"
- Account lockout: "Not implemented" to DB-backed (5 attempts, 15-min lockout)
- CSRF: SameSite cookies to stateless HMAC-SHA256
- Docker: python:3.11 to 3.12-slim-bookworm, node:20 to 22-alpine
- Scanning tools: removed Snyk, added Bandit + pip-audit + npm audit
- Retention: "2 years" to "365 days"

### Added
- CORS configuration details (env-var, wildcard blocked, credentials)
- Input validation for 10 file formats (110MB limit, formula injection sanitization)
- CSP full production policy
- Security headers table (6 headers)
- Rate limiting table (6 tiers x 5 categories)
- Prometheus metrics + Sentry APM
- Stripe as vendor (PCI DSS Level 1)

---

## [2026-02-26] Zero-Storage Architecture v2.0

**Type:** Major
**Document:** ZERO_STORAGE_ARCHITECTURE.md
**Previous Version:** 1.0

### Changed
- Section 1.3: File format support from "CSV/Excel" to 10 supported formats
- Section 2.2: ActivityLog fields updated (Numeric(19,2), material_count, sheet_count)
- Section 2.2: DiagnosticSummary fields updated (8 ratios, period metadata, Numeric types)
- Section 3.1: Architecture diagram updated for multi-format parsing
- Section 3.3: Memory cleanup updated to context manager pattern
- Retention: "2 years" to "365 days" (3 locations)

### Added
- Section 2.2: Engagement, ToolRun, FollowUpItem, Subscription, BillingEvent table descriptions
- Section 2.3: Soft-delete archival model documentation
- Section 2.4: Engagement, billing, follow-up rows in duration table

---

## Pre-v2.0 (v1.0)

Initial versions of all four compliance documents. Created during Phase XIV (Sprints 131-135) as part of the Professional Threshold milestone. No formal changelog was maintained prior to this point.
