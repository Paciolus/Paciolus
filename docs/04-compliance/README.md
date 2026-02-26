# Compliance Documentation Index

**Last Updated:** February 26, 2026
**Maintainer:** IntegratorLead (Agent Council)

---

## Document Inventory

| Document | Version | Effective Date | Owner | Classification | Next Review |
|----------|---------|----------------|-------|----------------|-------------|
| [Terms of Service](TERMS_OF_SERVICE.md) | 2.0 | 2026-02-26 | legal@paciolus.com | Legal Agreement | 2026-08-26 |
| [Privacy Policy](PRIVACY_POLICY.md) | 2.0 | 2026-02-26 | privacy@paciolus.com | Public | 2026-08-26 |
| [Security Policy](SECURITY_POLICY.md) | 2.1 | 2026-02-26 | Chief Information Security Officer | Public | 2026-05-26 |
| [Zero-Storage Architecture](ZERO_STORAGE_ARCHITECTURE.md) | 2.1 | 2026-02-26 | Chief Technology Officer | Public | 2026-05-26 |

Each `.md` document has a corresponding `.docx` generated via `pandoc`.

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

---

## Cross-Document Consistency Checklist

Use this checklist before any compliance document release:

- [ ] **Retention values** match across all 4 documents (currently: 365 days for activity logs/diagnostic summaries)
- [ ] **Tier names** match current billing model (Free / Solo / Team / Organization)
- [ ] **File format count** matches implementation (currently: 10 supported formats)
- [ ] **Security controls** described in ToS/Privacy align with Security Policy specifics
- [ ] **Zero-storage claims** in ToS/Privacy align with Zero-Storage Architecture definitions
- [ ] **Version numbers** in document headers match this index
- [ ] **Effective dates** are consistent where documents were updated together
- [ ] **Owner/contact** information is current
- [ ] `.docx` files regenerated for all modified documents
- [ ] Archive snapshots created for any documents with effective date or major version changes

---

## Regenerating .docx Files

```bash
cd docs/04-compliance
pandoc TERMS_OF_SERVICE.md -o TERMS_OF_SERVICE.docx
pandoc PRIVACY_POLICY.md -o PRIVACY_POLICY.docx
pandoc SECURITY_POLICY.md -o SECURITY_POLICY.docx
pandoc ZERO_STORAGE_ARCHITECTURE.md -o ZERO_STORAGE_ARCHITECTURE.docx
```
