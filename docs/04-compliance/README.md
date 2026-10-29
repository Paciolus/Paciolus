# Compliance Documentation Index

**Last Updated:** 2026-10-24 (Sprint 845) · **Owner:** security@paciolus.com

The repository is public, so every document here is a published claim. In Sprint 845 they were
rewritten as short, accurate documents for a solo-operated service: no SOC 2, pen test or bug bounty
claims, no officer titles that do not exist, no uptime or recovery commitments the operator cannot keep.
Superseded versions are kept, labelled, in [`archive/`](archive/). The website Terms and Privacy Policy
are authoritative; the files here point to them.

## Document Inventory

| Document | Version | Effective | Classification |
|----------|---------|-----------|----------------|
| [Terms of Service](TERMS_OF_SERVICE.md) — pointer to paciolus.com/terms | — | 2026-10-24 | Legal |
| [Privacy Policy](PRIVACY_POLICY.md) — pointer to paciolus.com/privacy | — | 2026-10-24 | Public |
| [Security Policy](SECURITY_POLICY.md) | 3.0 | 2026-10-24 | Public |
| [Data Handling Architecture](ZERO_STORAGE_ARCHITECTURE.md) | 3.0 | 2026-10-24 | Public |
| [Data Processing Addendum](DATA_PROCESSING_ADDENDUM.md) | 2.0-draft | not yet offered | Draft |
| [Subprocessor List](SUBPROCESSOR_LIST.md) | 2.0 | 2026-10-24 | Public |
| [Incident Response Plan](INCIDENT_RESPONSE_PLAN.md) | 2.0 | 2026-10-24 | Public |
| [Business Continuity / Disaster Recovery](BUSINESS_CONTINUITY_DISASTER_RECOVERY.md) | 2.0 | 2026-10-24 | Public |
| [Access Control Policy](ACCESS_CONTROL_POLICY.md) | 2.0 | 2026-10-24 | Public |
| [Secure Development / Change Management](SECURE_SDL_CHANGE_MANAGEMENT.md) | 2.0 | 2026-10-24 | Public |
| [Vulnerability Disclosure Policy](VULNERABILITY_DISCLOSURE_POLICY.md) | 2.0 | 2026-10-24 | Public |
| [Audit Logging and Evidence Retention](AUDIT_LOGGING_AND_EVIDENCE_RETENTION.md) | 2.0 | 2026-10-24 | Public |

The `.docx` exports were removed in Sprint 845 (they were copies of the superseded text). Generate them
with `pandoc` when a customer asks for Word copies.

---

## Versioning Rules

All compliance documents follow [Semantic Versioning](https://semver.org/) adapted for policy documents:

| Change Type | Version Bump | Examples |
|-------------|-------------|----------|
| **Patch** (X.Y.**Z**) | Typo corrections, formatting fixes, non-substantive rewording | Fix broken link, correct grammar, adjust whitespace |
| **Minor** (X.**Y**.0) | Clarifications, added detail, new subsections that do not change commitments | Add explanatory table, expand existing section, add cross-reference |
| **Major** (**X**.0.0) | Changes to legal, commercial, or security commitments | Modify data retention periods, change pricing terms, alter security guarantees, add/remove user rights |

### Rules

1. **Every version change** must be recorded in [CHANGELOG.md](CHANGELOG.md).
2. **Major versions** require legal owner sign-off before the new effective date.
3. **Minor/patch versions** may be applied by the engineering team with post-hoc review.
4. The `.docx` file must be regenerated whenever the `.md` source changes.

---

## Archive Policy

### Triggers

An archived snapshot **must** be created when:

1. **Effective date changes** on Terms of Service or Privacy Policy.
2. **Major version bump** on any document.
3. **Legal/regulatory requirement** mandates preservation of a prior version.

### Archive Format

Archived files are stored in [`archive/`](archive/) with immutable filenames:

```
archive/<DOCUMENT_NAME>_v<VERSION>_<EFFECTIVE_DATE>.md
```

Examples:
- `archive/TERMS_OF_SERVICE_v2.0_2026-02-26.md`
- `archive/SECURITY_POLICY_v2.1_2026-02-26.md`

**Immutability rule:** Once placed in `archive/`, files must never be modified. If an error is discovered in an archived version, document the correction in CHANGELOG.md and reference the corrected live version.

---

## Review Schedule

| Document | Review Cycle | Next Review |
|----------|-------------|-------------|
| Terms of Service | Semi-annual | 2026-08-26 |
| Privacy Policy | Semi-annual | 2026-08-26 |
| Security Policy | Quarterly | 2026-05-26 |
| Zero-Storage Architecture | Quarterly | 2026-05-26 |
| Data Processing Addendum | Semi-annual | 2026-08-26 |
| Subprocessor List | Quarterly | 2026-05-26 |
| Incident Response Plan | Quarterly | 2026-05-26 |
| Business Continuity / Disaster Recovery | Semi-annual | 2026-08-26 |
| Access Control Policy | Quarterly | 2026-05-26 |
| Secure SDLC / Change Management | Quarterly | 2026-05-26 |
| Vulnerability Disclosure Policy | Semi-annual | 2026-08-26 |
| Audit Logging and Evidence Retention | Quarterly | 2026-05-26 |

---

## Cross-Document Consistency Checklist

Use this checklist before any compliance document release:

- [ ] **Retention values** match across all 4 documents (currently: 365 days for activity logs/diagnostic summaries)
- [ ] **Tier names** match current billing model (Free / Solo / Professional / Enterprise)
- [ ] **File format count** matches implementation (currently: 10 supported formats)
- [ ] **Security controls** described in ToS/Privacy align with Security Policy specifics
- [ ] **Storage claims** in ToS/Privacy align with the Data Handling Architecture (guarded by `backend/tests/test_storage_claims.py`)
- [ ] **Version numbers** in document headers match this index
- [ ] **Effective dates** are consistent where documents were updated together
- [ ] **Owner/contact** information is current
- [ ] Archive snapshots created for any documents with effective date or major version changes

---

