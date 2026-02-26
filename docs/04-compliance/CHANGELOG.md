# Compliance Documentation Changelog

All notable changes to Paciolus compliance documents are recorded here.

Format follows [Keep a Changelog](https://keepachangelog.com/). Each entry specifies the document, version, and effective date.

---

## [2026-02-26] Operational Governance Pack v1.0

**Type:** Major (6 New Documents)

### Added — Incident Response Plan v1.0
**Document:** INCIDENT_RESPONSE_PLAN.md
- 4 severity levels (P0–P3) with defined response SLAs (15 min to next business day)
- Incident Response Team roles (IC, Technical Lead, Communications Lead, Scribe)
- On-call rotation parameters and escalation paths
- 3 communication templates (Critical, Major, Resolution)
- GDPR Article 33/34 and CCPA notification procedures
- Post-mortem template with blameless review process
- 4 incident-specific playbooks (Zero-Storage violation, credential breach, service outage, payment failure)
- Semi-annual tabletop exercise requirement

### Added — Business Continuity and Disaster Recovery Plan v1.0
**Document:** BUSINESS_CONTINUITY_DISASTER_RECOVERY.md
- RTO/RPO targets for 7 service components (30 min to 24 hours)
- Infrastructure dependency map with provider SLA references
- Database backup strategy (daily snapshots + continuous WAL, 28-day retention)
- 5 disaster recovery procedures (database, backend, frontend, DNS/TLS, complete infrastructure loss)
- 5 degraded operation modes
- Semi-annual backup restore test procedure with success criteria
- Zero-Storage impact analysis on DR scope

### Added — Access Control Policy v1.0
**Document:** ACCESS_CONTROL_POLICY.md
- 8 internal role definitions with system access matrix
- Provisioning SLA (1 business day) and deprovisioning SLA (4 hours / 1 hour involuntary)
- Deprovisioning checklist (12 systems)
- MFA policy (mandatory, hardware key preferred, no SMS)
- Privileged access management (just-in-time, dual authorization, break-glass procedure)
- Application-level access control (multi-tenant isolation, tier-based entitlements)
- Quarterly privileged access review process
- Monthly orphaned account detection

### Added — Secure SDLC and Change Management Policy v1.0
**Document:** SECURE_SDL_CHANGE_MANAGEMENT.md
- 7-phase SDLC with security integration at each phase
- Branch protection rules (10 rules on main)
- Security review checklist (9 items) with dual-reviewer triggers
- 10 mandatory CI checks (pytest, build, lint, Bandit, pip-audit, npm audit, accounting invariants)
- Standard release process (7 steps) with deployment windows
- Rollback procedure (<15-minute target) with database migration rollback guidance
- Hotfix workflow with CI enforcement (no bypasses)
- Database migration management requirements

### Added — Vulnerability Disclosure Policy v1.0
**Document:** VULNERABILITY_DISCLOSURE_POLICY.md
- In-scope assets (web application, API, auth system, file upload, payment)
- Reporting channels (security@paciolus.com, security.txt)
- Safe-harbor provisions (CFAA, DMCA Section 1201 protections)
- Response SLAs (2-day acknowledgment, 5-day assessment, 90-day coordinated disclosure)
- CVSS-aligned severity classification with remediation SLAs
- Zero-Storage impact context for vulnerability assessment
- Coordinated disclosure timeline with researcher rights
- Testing boundaries (10 req/sec limit, own accounts only)

### Added — Audit Logging and Evidence Retention Policy v1.0
**Document:** AUDIT_LOGGING_AND_EVIDENCE_RETENTION.md
- 6 event classes (authentication, authorization, data access, administrative, security, operational)
- Minimum required events table (25+ specific events across 5 categories)
- Structured JSON log format with 11 required fields
- PII redaction rules (email masking, token fingerprinting, exception sanitization)
- Tamper resistance (soft-delete immutability, ORM deletion guard, append-only billing)
- Retention schedule aligned with Privacy Policy Section 4 (365-day operational, 90-day infra)
- Legal hold procedure with designated custodian and GDPR reconciliation
- Hold register template and quarterly review requirement
- 7 log-based monitoring alerts

---

## [2026-02-26] Data Processing Addendum v1.0

**Type:** Major (New Document)
**Document:** DATA_PROCESSING_ADDENDUM.md
**Previous Version:** N/A

### Added
- Complete DPA covering GDPR Article 28 requirements
- Sections: roles (controller/processor), processing purposes, data categories, security measures, subprocessor management, international transfers (SCCs/DPF), data subject rights, deletion/return, audit rights, breach notification
- Zero-Storage architecture acknowledgment with impact analysis on data subject rights and breach scope
- Cross-references to Security Policy, Zero-Storage Architecture, and Subprocessor List

---

## [2026-02-26] Subprocessor List v1.0

**Type:** Major (New Document)
**Document:** SUBPROCESSOR_LIST.md
**Previous Version:** N/A

### Added
- 5 active subprocessors: Render, Vercel, Stripe, Sentry, SendGrid (Twilio)
- Per-provider: service function, data categories, hosting region, transfer mechanism, certifications, DPA status
- Data categories reference table with retention periods
- Zero-Storage compliance notes per subprocessor
- Infrastructure-only services section (GitHub, Prometheus, Dependabot — not subprocessors)
- Notification and objection process (30-day notice period)
- Subprocessor change log

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
