# SOC 2 Evidence Index

> Maps each AICPA 2017 Trust Services Criteria to its evidence artifacts.
> **Updated:** 2026-03-01

---

## CC1 — Control Environment

| Criterion | Evidence | Location |
|-----------|----------|----------|
| CC1.1 | Organization chart, CISO role definition | `cc1/` |
| CC1.2 | Code of conduct, ethics policy | `cc1/` |
| CC1.3 | Board oversight / governance documentation | `cc1/` |
| CC1.4 | Competence commitment — job descriptions, training records | `cc1/`, `cc2/` |

## CC2 — Communication and Information

| Criterion | Evidence | Location |
|-----------|----------|----------|
| CC2.1 | Internal communication of policies (SECURITY_POLICY.md, CONTRIBUTING.md) | `cc2/` |
| CC2.2 | Security awareness training logs | `cc2/security-training-log-2026.md` |
| CC2.3 | External communication (Privacy Policy, Terms of Service) | `docs/04-compliance/` |

## CC3 — Risk Assessment

| Criterion | Evidence | Location |
|-----------|----------|----------|
| CC3.1 | Risk register (quarterly updated) | `cc4/risk-register-2026-Q*.md` |
| CC3.2 | Change risk assessment (PR template security checklist) | `cc5/` |
| CC3.3 | Fraud risk consideration | `cc4/` |
| CC3.4 | Change identification and assessment | `cc5/` |

## CC4 — Monitoring Activities

| Criterion | Evidence | Location |
|-----------|----------|----------|
| CC4.1 | Risk register — ongoing evaluation | `cc4/` |
| CC4.2 | Weekly security event reviews | `c1/security-review-YYYY-WNN.md` |
| CC4.3 | Penetration test reports (planned Q2 2026) | `pentest/` |

## CC5 — Control Activities

| Criterion | Evidence | Location |
|-----------|----------|----------|
| CC5.1 | CI/CD pipeline configuration (GitHub Actions) | `cc5/` |
| CC5.2 | Technology general controls — rate limiting, CSRF, CSP | `cc5/` |
| CC5.3 | Security policy deployment evidence | `cc5/` |

## CC6 — Logical and Physical Access Controls

| Criterion | Evidence | Location |
|-----------|----------|----------|
| CC6.1 | Quarterly access reviews | `cc6/access-review-YYYY-QN.md` |
| CC6.2 | User provisioning/deprovisioning records | `cc6/` |
| CC6.3 | Authentication controls — JWT, MFA, lockout | `cc6/` |
| CC6.6 | Encryption controls — TLS, at-rest verification | `cc7/` |
| CC6.7 | Access restriction to system components | `cc6/` |
| CC6.8 | Database audit logging (pgaudit — Sprint 460) | `cc6/` |

## CC7 — System Operations

| Criterion | Evidence | Location |
|-----------|----------|----------|
| CC7.1 | Infrastructure monitoring (Sentry, Prometheus) | `s3/` |
| CC7.2 | Encryption at-rest verification | `cc7/render-postgres-encryption-*.png` |
| CC7.3 | Key management / secrets rotation | `cc7/` |
| CC7.4 | Audit log chaining verification reports (Sprint 461) | `cc7/` |

## CC8 — Change Management

| Criterion | Evidence | Location |
|-----------|----------|----------|
| CC8.1 | Change management policy (SECURE_SDL_CHANGE_MANAGEMENT.md) | `cc8/` |
| CC8.4 | PR security checklist template | `cc8/` |
| CC8.6 | GPG commit signing evidence (Sprint 458) | `cc8/` |

## CC9 — Risk Mitigation

| Criterion | Evidence | Location |
|-----------|----------|----------|
| CC9.1 | Incident response plan + tabletop exercise | `cc9/`, `c1/` |
| CC9.2 | Business continuity / disaster recovery plan | `s3/` |

## S3 — Availability

| Criterion | Evidence | Location |
|-----------|----------|----------|
| S3.1 | BCP/DR documentation | `s3/` |
| S3.2 | Cross-region replication (Sprint 464 — pending CEO decision) | `s3/` |
| S3.3 | Monitoring dashboard configuration | `s3/sentry-config-*.json`, `s3/prometheus-config-*.yaml` |
| S3.5 | Backup restore test reports | `s3/dr-test-YYYY-QN.md` |

## C1 — Confidentiality

| Criterion | Evidence | Location |
|-----------|----------|----------|
| C1.1 | Data classification policy | `c1/` |
| C1.2 | Confidentiality commitments (DPA, NDA) | `pi1/` |
| C1.3 | Weekly security reviews (confidentiality monitoring) | `c1/security-review-YYYY-WNN.md` |

## PI — Privacy (Processing Integrity)

| Criterion | Evidence | Location |
|-----------|----------|----------|
| PI1.1 | Privacy Policy (public) | `docs/04-compliance/PRIVACY_POLICY.md` |
| PI1.3 | DPA acceptance register | `pi1/dpa-roster-YYYYQN.txt` |
| PI4.3 | Data deletion procedure + request log | `pi4/deletion-*.md` |

---

## Evidence Filing Guide

1. **Naming convention:** `{evidence-type}-{YYYYMM}.{ext}` or `{evidence-type}-{YYYY-QN}.{ext}`
2. **Retention:** 3 years minimum (per AUDIT_LOGGING_AND_EVIDENCE_RETENTION.md)
3. **Filing:** Copy completed evidence artifacts into the appropriate `soc2-evidence/{category}/` folder
4. **Index updates:** Update this file when new evidence categories are added

---

*Last updated: 2026-03-01 — Sprint 469*
