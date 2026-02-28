# SOC 2 Type II Evidence Index

**Version:** 1.0
**Date:** 2026-02-28
**Prepared by:** Engineering (Sprint 469)
**Purpose:** Maps each AICPA 2017 Trust Services Criterion to its evidence artifacts within this repository.

> **Convention:** Paths are relative to the repository root. Artifacts marked *(placeholder)* indicate the folder exists but requires CEO action or external data before it can be populated.

---

## CC1 — Control Environment

| Criterion | Description | Evidence Artifact(s) | Status |
|-----------|------------|----------------------|--------|
| CC1.1 | CISO / security responsibility | `docs/04-compliance/SECURITY_POLICY.md` §1 (roles & responsibilities) | Available |
| CC1.2 | Board / management oversight | `docs/04-compliance/SECURITY_POLICY.md` §1; `docs/08-internal/security-review-template.md` | Available |
| CC1.3 | Organizational structure | `docs/08-internal/onboarding-runbook.md` (role definitions); `docs/04-compliance/ACCESS_CONTROL_POLICY.md` §2 (role matrix) | Available |
| CC1.4 | Competence & accountability | `docs/08-internal/security-training-curriculum-2026.md`; `docs/08-internal/security-training-log-2026.md` | Available |
| CC1.5 | Accountability enforcement | `docs/04-compliance/ACCESS_CONTROL_POLICY.md` §5 (quarterly reviews); `docs/08-internal/access-review-2026-Q1.md` | Available |

**Evidence folder:** `soc2-evidence/cc1/`

---

## CC2 — Communication & Information

| Criterion | Description | Evidence Artifact(s) | Status |
|-----------|------------|----------------------|--------|
| CC2.1 | Internal communication of policies | `docs/04-compliance/README.md` (policy index); `docs/04-compliance/CHANGELOG.md` (version history) | Available |
| CC2.2 | External communication | `docs/04-compliance/PRIVACY_POLICY.md`; `docs/04-compliance/TERMS_OF_SERVICE.md`; `docs/04-compliance/VULNERABILITY_DISCLOSURE_POLICY.md` | Available |
| CC2.3 | Communication with external parties | `docs/04-compliance/SUBPROCESSOR_LIST.md`; `docs/04-compliance/DATA_PROCESSING_ADDENDUM.md` | Available |

**Evidence folder:** `soc2-evidence/cc2/`

---

## CC3 — Risk Assessment

| Criterion | Description | Evidence Artifact(s) | Status |
|-----------|------------|----------------------|--------|
| CC3.1 | Risk objectives | `docs/04-compliance/SECURITY_POLICY.md` §8 (threat model); `docs/08-internal/risk-register-2026-Q1.md` | Available |
| CC3.2 | Risk identification | `docs/08-internal/risk-register-2026-Q1.md` (risk register with scoring); `docs/08-internal/security-review-2026-W09.md` (weekly review) | Available |
| CC3.3 | Fraud risk consideration | `docs/04-compliance/SECURITY_POLICY.md` §8; `backend/guards/accounting_policy.toml` (5 AST-based invariant checkers) | Available |
| CC3.4 | Identification of significant changes | `docs/08-internal/security-review-template.md` (recurring review process); `docs/04-compliance/CHANGELOG.md` | Available |

**Evidence folder:** `soc2-evidence/cc3/`

---

## CC4 — Monitoring Activities

| Criterion | Description | Evidence Artifact(s) | Status |
|-----------|------------|----------------------|--------|
| CC4.1 | Ongoing monitoring | `docs/08-internal/security-review-2026-W09.md` (weekly cadence); `backend/guards/parser_alerts.toml` (TOML alert thresholds); Prometheus `/metrics` endpoint | Available |
| CC4.2 | Evaluation & communication of deficiencies | `docs/04-compliance/INCIDENT_RESPONSE_PLAN.md` (P0–P3 severity, post-mortem process); `docs/08-internal/security-review-template.md` (deficiency tracking) | Available |

**Evidence folder:** `soc2-evidence/cc4/` (populated via cc3/ risk register artifacts)

---

## CC5 — Control Activities

| Criterion | Description | Evidence Artifact(s) | Status |
|-----------|------------|----------------------|--------|
| CC5.1 | Selection of control activities | `docs/04-compliance/SECURE_SDL_CHANGE_MANAGEMENT.md` (10 CI checks, branch protection); `.github/workflows/ci.yml` (CI pipeline definition) | Available |
| CC5.2 | Technology controls | `.github/workflows/ci.yml` (pytest + build + lint + Bandit + pip-audit); `backend/guards/accounting_policy.toml` (5 accounting invariant checkers); `.github/workflows/backup-integrity-check.yml` | Available |
| CC5.3 | Policy deployment | `docs/04-compliance/SECURE_SDL_CHANGE_MANAGEMENT.md` §3 (release process); `.husky/` (pre-commit hooks — lint-staged) | Available |

**Evidence folder:** `soc2-evidence/cc5/`

---

## CC6 — Logical & Physical Access Controls

| Criterion | Description | Evidence Artifact(s) | Status |
|-----------|------------|----------------------|--------|
| CC6.1 | Logical access security | `docs/04-compliance/ACCESS_CONTROL_POLICY.md` §3 (MFA, provisioning SLAs); `docs/04-compliance/SECURITY_POLICY.md` §3–5 (JWT auth, CSRF, CORS) | Available |
| CC6.2 | Access provisioning | `docs/04-compliance/ACCESS_CONTROL_POLICY.md` §2–3 (role matrix, provisioning/deprovisioning); `docs/08-internal/onboarding-runbook.md` | Available |
| CC6.3 | Access modification & removal | `docs/04-compliance/ACCESS_CONTROL_POLICY.md` §4 (deprovisioning SLAs); `docs/08-internal/access-review-2026-Q1.md` (quarterly access review) | Available |
| CC6.6 | Threat management | `docs/04-compliance/SECURITY_POLICY.md` §6 (rate limiting tiers); `backend/shared/rate_limits.py` (implementation) | Available |
| CC6.7 | Access restrictions | `backend/shared/entitlement_checks.py` (tier-gated access); `backend/shared/entitlements.py` (entitlement definitions) | Available |
| CC6.8 | Access monitoring | `docs/04-compliance/AUDIT_LOGGING_AND_EVIDENCE_RETENTION.md` §3–4 (6 event classes, structured logging); `backend/shared/log_sanitizer.py` (PII scrubbing) | Available |

**Evidence folder:** `soc2-evidence/cc6/`

---

## CC7 — System Operations

| Criterion | Description | Evidence Artifact(s) | Status |
|-----------|------------|----------------------|--------|
| CC7.1 | Infrastructure monitoring | `docs/04-compliance/SECURITY_POLICY.md` §8.3–8.4 (Sentry + Prometheus alerting); `backend/shared/alert_checker.py`; `backend/shared/parser_metrics.py` | Available |
| CC7.2 | Incident management | `docs/04-compliance/INCIDENT_RESPONSE_PLAN.md` (4 playbooks, triage SLAs, post-mortem); `docs/04-compliance/VULNERABILITY_DISCLOSURE_POLICY.md` | Available |
| CC7.3 | Change management | `docs/04-compliance/SECURE_SDL_CHANGE_MANAGEMENT.md` (branch protection, <15-min rollback, hotfix workflow); `.github/workflows/ci.yml` | Available |
| CC7.4 | Tamper evidence | `backend/shared/audit_chain.py` (HMAC-SHA256 hash chaining — Sprint 461); `backend/shared/soft_delete.py` (SoftDeleteMixin — Sprint 345); `docs/04-compliance/AUDIT_LOGGING_AND_EVIDENCE_RETENTION.md` §5.4 | Available |
| CC7.5 | Data recovery | `docs/04-compliance/BUSINESS_CONTINUITY_DISASTER_RECOVERY.md` (RTO/RPO, backup strategy); `docs/08-internal/backup-integrity-procedure.md`; `.github/workflows/backup-integrity-check.yml` | Available |

**Evidence folder:** `soc2-evidence/cc7/`

---

## CC8 — Change Management

| Criterion | Description | Evidence Artifact(s) | Status |
|-----------|------------|----------------------|--------|
| CC8.1 | Change authorization | `docs/04-compliance/SECURE_SDL_CHANGE_MANAGEMENT.md` §2 (branch protection, PR review requirement); `.github/workflows/ci.yml` (10 CI gate checks) | Available |

**Evidence folder:** `soc2-evidence/cc8/`

---

## CC9 — Risk Mitigation

| Criterion | Description | Evidence Artifact(s) | Status |
|-----------|------------|----------------------|--------|
| CC9.1 | Risk mitigation activities | `docs/08-internal/risk-register-2026-Q1.md` (risk scoring, mitigation plans); `docs/04-compliance/BUSINESS_CONTINUITY_DISASTER_RECOVERY.md` (dependency map) | Available |
| CC9.2 | Vendor risk management | `docs/04-compliance/SUBPROCESSOR_LIST.md` (5 providers); `docs/04-compliance/DATA_PROCESSING_ADDENDUM.md` (GDPR Art. 28) | Available |

**Evidence folder:** `soc2-evidence/cc9/`

---

## S3 — Availability

| Criterion | Description | Evidence Artifact(s) | Status |
|-----------|------------|----------------------|--------|
| S3.1 | Availability objectives | `docs/04-compliance/BUSINESS_CONTINUITY_DISASTER_RECOVERY.md` §2 (RTO/RPO targets) | Available |
| S3.2 | Environmental safeguards | Render/Vercel PaaS (provider responsibility); `docs/04-compliance/SUBPROCESSOR_LIST.md` | Available |
| S3.3 | Availability monitoring | `docs/04-compliance/SECURITY_POLICY.md` §8.3 (Sentry APM); `backend/shared/alert_checker.py`; Prometheus `/metrics` | Available |
| S3.4 | Disaster recovery | `docs/08-internal/dr-test-2026-Q1.md` (DR test report); `docs/08-internal/backup-integrity-procedure.md` | Available |

**Evidence folder:** `soc2-evidence/s3/`

---

## C1 — Confidentiality

| Criterion | Description | Evidence Artifact(s) | Status |
|-----------|------------|----------------------|--------|
| C1.1 | Confidential information identification | `docs/04-compliance/ZERO_STORAGE_ARCHITECTURE.md` (Zero-Storage data classification); `docs/04-compliance/PRIVACY_POLICY.md` | Available |
| C1.2 | Confidential information disposal | `docs/04-compliance/ZERO_STORAGE_ARCHITECTURE.md` §2 (no persistent user data); `docs/08-internal/data-deletion-procedure.md` | Available |

**Evidence folder:** `soc2-evidence/c1/`

---

## PI — Privacy (Processing Integrity)

| Criterion | Description | Evidence Artifact(s) | Status |
|-----------|------------|----------------------|--------|
| PI1.1 | Privacy notice | `docs/04-compliance/PRIVACY_POLICY.md` v2.0 | Available |
| PI1.2 | Consent & choice | `docs/04-compliance/TERMS_OF_SERVICE.md` v2.0; `docs/04-compliance/DATA_PROCESSING_ADDENDUM.md` | Available |
| PI4.1 | Data subject access | `docs/08-internal/data-deletion-procedure.md`; `docs/08-internal/deletion-requests/` (request log) | Available |
| PI4.2 | DPA management | `docs/08-internal/dpa-acceptance-register.md`; `docs/08-internal/customer-dpa-archive/` | Available |

**Evidence folders:** `soc2-evidence/pi1/`, `soc2-evidence/pi4/`

---

## Pen Testing

| Criterion | Description | Evidence Artifact(s) | Status |
|-----------|------------|----------------------|--------|
| External penetration test | Third-party pen test report | *(placeholder — requires CEO engagement of pen test vendor)* | Gap |

**Evidence folder:** `soc2-evidence/pentest/`

---

## Cross-Cutting Technical Evidence

These code artifacts provide supplementary evidence across multiple criteria:

| Artifact | Path | Relevant Criteria |
|----------|------|-------------------|
| CI pipeline | `.github/workflows/ci.yml` | CC5.1, CC5.2, CC7.3, CC8.1 |
| Backup integrity CI | `.github/workflows/backup-integrity-check.yml` | CC7.5, S3.4 |
| Accounting policy guards | `backend/guards/accounting_policy.toml` | CC3.3, CC5.2 |
| Parser alert thresholds | `backend/guards/parser_alerts.toml` | CC4.1, CC7.1 |
| Soft-delete immutability | `backend/shared/soft_delete.py` | CC7.4 |
| Cryptographic audit chain | `backend/shared/audit_chain.py` | CC7.4 |
| Entitlement enforcement | `backend/shared/entitlement_checks.py` | CC6.7 |
| Log sanitizer (PII scrub) | `backend/shared/log_sanitizer.py` | CC6.8, C1.1 |
| Rate limiting | `backend/shared/rate_limits.py` | CC6.6 |
| GPG key registry | `docs/08-internal/gpg-key-registry.md` | CC7.4 |
| Encryption at-rest verification | `docs/08-internal/encryption-at-rest-verification-202602.md` | CC7.4, C1.1 |
