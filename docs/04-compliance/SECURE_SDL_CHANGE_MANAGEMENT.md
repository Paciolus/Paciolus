# Secure Software Development Lifecycle and Change Management Policy

**Version:** 1.0
**Document Classification:** Internal
**Effective Date:** February 26, 2026
**Last Updated:** February 26, 2026
**Owner:** Chief Technology Officer
**Review Cycle:** Quarterly
**Next Review:** May 26, 2026

---

## Executive Summary

This document defines Paciolus's secure software development lifecycle (SDLC), change management procedures, branch protection rules, required CI checks, release approval workflow, and rollback criteria. It ensures that all code changes are reviewed, tested, and deployed through a controlled process.

**Key Controls:**
- ✅ All production changes require pull request with at least one approval
- ✅ 8 mandatory CI checks must pass before merge (pytest, build, lint, security scans)
- ✅ 5 AST-based accounting invariant checks enforced in CI
- ✅ Pre-commit hooks (Husky + lint-staged) catch issues before push
- ✅ Documented rollback procedure with <15-minute execution target
- ✅ Zero-Storage compliance verified on every change touching data handling

**Target Audience:** Engineering team, auditors, enterprise customers

---

## Table of Contents

1. [Development Lifecycle](#1-development-lifecycle)
2. [Branch Strategy and Protection](#2-branch-strategy-and-protection)
3. [Code Review Requirements](#3-code-review-requirements)
4. [CI/CD Pipeline](#4-cicd-pipeline)
5. [Security Gates](#5-security-gates)
6. [Release Process](#6-release-process)
7. [Rollback Procedures](#7-rollback-procedures)
8. [Database Migration Management](#8-database-migration-management)
9. [Hotfix Process](#9-hotfix-process)
10. [Change Documentation](#10-change-documentation)
11. [Contact](#11-contact)

---

## 1. Development Lifecycle

### 1.1 SDLC Phases

| Phase | Activities | Security Integration | Deliverable |
|-------|-----------|---------------------|-------------|
| **Requirements** | Feature specification, threat assessment | Identify security requirements, data handling implications | Requirement document with security considerations |
| **Design** | Architecture, API design | Zero-Storage compliance review, threat modeling for new endpoints | Design document or RFC |
| **Implementation** | Coding, unit tests | Secure coding standards, pre-commit hooks (ruff, ESLint) | Feature branch with tests |
| **Code Review** | Pull request review | Security-focused review checklist (Section 3.2) | Approved PR |
| **Automated Testing** | CI pipeline execution | Security scans (Bandit, pip-audit, npm audit), accounting invariant checks | CI green |
| **Deployment** | Production release | Deployment checklist, rollback plan verified | Production release |
| **Monitoring** | Post-deployment observation | Error rate monitoring, anomaly detection | 24-hour stability confirmation |

### 1.2 Secure Coding Standards

All developers must adhere to:

| Standard | Enforcement |
|----------|-------------|
| No raw SQL (use SQLAlchemy ORM) | Code review + Bandit scan |
| Input validation on all user inputs (Pydantic schemas) | Code review + route integration tests |
| No hardcoded secrets | Code review + Bandit scan + .gitignore |
| Zero-Storage compliance (no financial data persistence) | Accounting Policy Guard (5 AST checks) |
| Error messages do not leak internals | `sanitize_error()` usage enforced in code review |
| Parameterized queries only | SQLAlchemy ORM enforcement |
| No `dangerouslySetInnerHTML` in React | ESLint rule |
| Content-Security-Policy headers | SecurityHeadersMiddleware |

See [SECURITY_POLICY.md](./SECURITY_POLICY.md) Section 3 for complete application security controls.

---

## 2. Branch Strategy and Protection

### 2.1 Branch Model

| Branch | Purpose | Lifetime | Deploys To |
|--------|---------|----------|------------|
| `main` | Production-ready code | Permanent | Production (on merge) |
| `feature/*` | New features | Temporary (until merged) | Staging (on push) |
| `fix/*` | Bug fixes | Temporary (until merged) | Staging (on push) |
| `hotfix/*` | Emergency production fixes | Temporary (hours) | Production (expedited) |

### 2.2 Branch Protection Rules (main)

| Rule | Setting | Rationale |
|------|---------|-----------|
| **Require pull request** | ✅ Enabled | All changes reviewed before merge |
| **Required approvals** | 1 minimum | At least one reviewer must approve |
| **Dismiss stale reviews** | ✅ Enabled | New commits invalidate prior approvals |
| **Require status checks** | ✅ Enabled | All CI checks must pass (Section 4) |
| **Require branches up to date** | ✅ Enabled | Branch must be rebased on latest main |
| **Require signed commits** | ❌ Not enforced (planned) | GPG signing planned for Q3 2026 |
| **Allow force push** | ❌ Disabled | Prevents history rewriting |
| **Allow deletions** | ❌ Disabled | Prevents accidental branch deletion |
| **Include administrators** | ✅ Enabled | Admins subject to same rules |

### 2.3 Pre-Commit Hooks

Husky + lint-staged enforce quality before push:

| Hook | Trigger | Checks |
|------|---------|--------|
| **pre-commit** | `git commit` | `lint-staged` runs ruff (backend .py) + ESLint + Prettier (frontend .ts/.tsx) |
| **Backend lint** | Staged `.py` files | `ruff check --fix` + `ruff format` |
| **Frontend lint** | Staged `.ts`/`.tsx` files | `eslint --fix` + `prettier --write` |

---

## 3. Code Review Requirements

### 3.1 Review Policy

| Requirement | Value |
|-------------|-------|
| Minimum reviewers | 1 (2 recommended for security-sensitive changes) |
| Self-approval | ❌ Not permitted |
| Review SLA | 1 business day for standard PRs; 4 hours for hotfixes |
| Stale review policy | Reviews dismissed when new commits are pushed |

### 3.2 Security Review Checklist

Reviewers must verify for every PR:

- [ ] **Input validation:** All new user inputs validated via Pydantic schemas
- [ ] **SQL safety:** No raw SQL; all queries via SQLAlchemy ORM
- [ ] **Secrets:** No hardcoded credentials, API keys, or tokens
- [ ] **Zero-Storage:** No new file persistence or database writes for financial data
- [ ] **Error handling:** Errors use `sanitize_error()`; no raw exception messages in responses
- [ ] **Authentication:** New endpoints use appropriate guard (`require_current_user` or `require_verified_user`)
- [ ] **Authorization:** Data queries filter by `user_id` (multi-tenant isolation)
- [ ] **Rate limiting:** New endpoints have rate limit decorators
- [ ] **Test coverage:** New functionality has corresponding tests

### 3.3 Additional Review Triggers

The following changes require **two** reviewers, one of whom must be a Senior Developer or above:

| Change Type | Rationale |
|-------------|-----------|
| Authentication or authorization logic | Security-critical |
| Database schema changes (Alembic migrations) | Data integrity |
| Billing or payment integration | Financial impact |
| Security middleware or CSRF logic | Security-critical |
| Dependency additions or major version bumps | Supply chain risk |
| Environment variable or secrets changes | Configuration integrity |

---

## 4. CI/CD Pipeline

### 4.1 Required CI Checks

All checks must pass before merge to `main`:

| Check | Tool | Blocking | Scope |
|-------|------|----------|-------|
| **Backend tests** | pytest | ✅ Yes | All backend tests (~4,650 tests) |
| **Frontend build** | `npm run build` | ✅ Yes | TypeScript compilation + Next.js build |
| **Frontend tests** | Jest + RTL | ✅ Yes | All frontend tests (~1,190 tests) |
| **Backend lint** | ruff | ✅ Yes | Python linting (0 errors baseline) |
| **Frontend lint** | ESLint | ✅ Yes | TypeScript/React linting (0 errors baseline) |
| **Python SAST** | Bandit | ✅ Yes | HIGH severity + HIGH/MEDIUM confidence |
| **Python SCA** | pip-audit | ✅ Yes | Any known vulnerability fails |
| **Node SCA** | npm audit | ✅ Yes | `--audit-level=high`, production deps |
| **Accounting invariants** | Accounting Policy Guard | ✅ Yes | 5 AST-based control checks |
| **Lint baseline gate** | Custom | ✅ Yes | No increase from baseline (0 errors) |

### 4.2 Accounting Policy Guard Invariants

Five AST-based checks enforced on every CI run:

| Invariant | What It Checks | Rationale |
|-----------|---------------|-----------|
| **Monetary float guard** | No `Float` column types for monetary fields | Numeric(19,2) precision required |
| **Hard delete guard** | No `db.delete()` on audit-protected models | Soft-delete immutability |
| **Contract field guard** | Revenue testing contract fields are optional | ASC 606 graceful degradation |
| **Adjustment gating guard** | Adjustment transitions use `validate_status_transition()` | Approval workflow integrity |
| **Framework metadata guard** | Framework fields (IFRS/GAAP) present on diagnostic models | Multi-framework support |

### 4.3 Pipeline Architecture

```
Push/PR to main
    │
    ├── pytest (backend tests)
    ├── npm run build (frontend)
    ├── npm test (frontend tests)
    ├── ruff check (backend lint)
    ├── eslint (frontend lint)
    ├── bandit (SAST)
    ├── pip-audit (SCA)
    ├── npm audit (SCA)
    ├── accounting-policy-guard
    └── lint-baseline-gate
    │
    ▼
All green? → Merge allowed
Any red? → Merge blocked
```

### 4.4 CI Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| Backend test suite | <5 minutes | ~3 minutes |
| Frontend build | <3 minutes | ~2 minutes |
| Frontend test suite | <3 minutes | ~2 minutes |
| Full pipeline (all checks) | <10 minutes | ~7 minutes |

---

## 5. Security Gates

### 5.1 Dependency Management

| Control | Implementation |
|---------|---------------|
| **Automated updates** | Dependabot PRs weekly (pip, npm, GitHub Actions) |
| **CVE scanning** | pip-audit + npm audit on every CI run |
| **Version pinning** | All dependencies pinned to specific versions in `requirements.txt` and `package-lock.json` |
| **License review** | New dependencies reviewed for license compatibility (no GPL in production) |

### 5.2 Vulnerability Remediation SLA

| Severity | Response Time | Fix Deployment |
|----------|--------------|----------------|
| **Critical** | 24 hours | 48 hours |
| **High** | 72 hours | 1 week |
| **Medium** | 1 week | 2 weeks |
| **Low** | 2 weeks | Next release |

See [SECURITY_POLICY.md](./SECURITY_POLICY.md) Section 7 for vulnerability management details.

### 5.3 Zero-Storage Compliance Verification

Every change that touches data handling is verified for Zero-Storage compliance:

| Check | Method |
|-------|--------|
| No new database columns for financial data | Code review + Accounting Policy Guard |
| No new file persistence for uploaded files | Code review |
| `memory_cleanup()` context manager used in analysis routes | Code review |
| Sentry `before_send` hook strips request bodies | Automated test |
| Tool session sanitization strips financial keys | Automated test |

---

## 6. Release Process

### 6.1 Standard Release

| Step | Action | Owner | Verification |
|------|--------|-------|-------------|
| 1 | All CI checks pass on PR | CI | Green status checks |
| 2 | Code review approved (Section 3) | Reviewer | PR approval |
| 3 | Branch up to date with main | Developer | GitHub merge check |
| 4 | Merge PR to main | Developer | Merge commit |
| 5 | Automated deployment triggers | CI/CD | Deployment log |
| 6 | Health check passes | Automated | `GET /api/health` returns 200 |
| 7 | Post-deployment monitoring (1 hour) | On-call | Error rate <1%, no new alerts |

### 6.2 Version Tagging

| Version Type | Format | Trigger |
|-------------|--------|---------|
| **Major** (X.0.0) | `vX.0.0` | Breaking changes, new major features |
| **Minor** (X.Y.0) | `vX.Y.0` | New features, non-breaking changes |
| **Patch** (X.Y.Z) | `vX.Y.Z` | Bug fixes, security patches |

Current version: **v2.1.0** (see CLAUDE.md for release history).

### 6.3 Deployment Windows

| Type | Window | Approval |
|------|--------|----------|
| Standard release | Business hours (09:00–17:00 UTC, Mon–Thu) | PR approval |
| Off-hours release | Requires CTO approval | CTO sign-off |
| Weekend release | Emergency only | CTO + IC approval |
| Hotfix | Any time | See Section 9 |

---

## 7. Rollback Procedures

### 7.1 Rollback Criteria

Initiate rollback if any of the following occur within 1 hour of deployment:

| Condition | Threshold |
|-----------|-----------|
| API error rate increase | >5% above baseline |
| Authentication failure rate | >1% of login attempts |
| Health endpoint failure | `GET /api/health` returns non-200 |
| Customer-reported critical bug | Confirmed by on-call engineer |
| Security vulnerability introduced | Any severity |

### 7.2 Rollback Procedure

| Step | Action | Owner | Target Time |
|------|--------|-------|-------------|
| 1 | Decision to rollback (IC or on-call) | IC | 0 minutes |
| 2 | Identify last known-good commit hash | On-call | 2 minutes |
| 3 | Deploy previous version via Render dashboard or `git revert` + push | On-call | 5–10 minutes |
| 4 | Verify health check passes | On-call | 2 minutes |
| 5 | Verify authentication flow functional | On-call | 3 minutes |
| 6 | Update status page if customer-facing impact occurred | Communications | 5 minutes |
| **Total rollback time** | | | **<15 minutes** |

### 7.3 Rollback for Database Migrations

If a deployment includes an Alembic migration and rollback is needed:

| Scenario | Action |
|----------|--------|
| Migration is reversible (has `downgrade()`) | Run `alembic downgrade -1` then deploy previous code |
| Migration is irreversible (no safe downgrade) | Deploy previous code with forward-compatible schema |
| Migration caused data corruption | Restore database from backup per [BCP/DR](./BUSINESS_CONTINUITY_DISASTER_RECOVERY.md) Section 5.1 |

### 7.4 Rollback Documentation

Every rollback must be documented:
- Deployment that was rolled back (commit hash, time)
- Reason for rollback
- Rollback duration (decision to full recovery)
- Impact assessment
- Follow-up actions (bug fix, process improvement)

---

## 8. Database Migration Management

### 8.1 Migration Requirements

| Requirement | Rationale |
|-------------|-----------|
| All schema changes via Alembic migrations | Reproducible, auditable changes |
| Migrations must include `upgrade()` and `downgrade()` | Enable rollback |
| New columns must have defaults or be nullable | Avoid breaking existing code during deploy |
| No data deletion in migrations (use soft-delete) | Audit immutability |
| Migration tested in staging before production | Prevent production schema issues |

### 8.2 Migration Review Checklist

- [ ] Migration has both `upgrade()` and `downgrade()` functions
- [ ] New columns have `server_default` or `nullable=True`
- [ ] No `DROP TABLE` or `DROP COLUMN` without CTO approval
- [ ] Monetary columns use `Numeric(19,2)`, not `Float`
- [ ] Foreign key constraints are correct
- [ ] Migration tested against a copy of production schema

### 8.3 Migration Deployment

| Step | Action | Owner |
|------|--------|-------|
| 1 | Review migration in PR (see checklist above) | Reviewer |
| 2 | Test `alembic upgrade head` in staging | Developer |
| 3 | Test `alembic downgrade -1` in staging | Developer |
| 4 | Deploy to production | CI/CD |
| 5 | Verify `alembic current` matches expected revision | On-call |

---

## 9. Hotfix Process

### 9.1 Hotfix Criteria

Hotfixes bypass the standard release window when:
- P0 or P1 security vulnerability in production
- P0 service outage caused by a code defect
- Data integrity issue (e.g., incorrect billing calculations)

### 9.2 Hotfix Workflow

| Step | Action | SLA | Approval |
|------|--------|-----|----------|
| 1 | Create `hotfix/*` branch from main | Immediately | IC |
| 2 | Implement minimal fix (smallest possible change) | ASAP | Developer |
| 3 | CI checks must pass (no exceptions) | <30 minutes | Automated |
| 4 | Code review (expedited: 1 reviewer, 4-hour SLA) | <4 hours | Senior Developer+ |
| 5 | Merge to main | After approval | Developer |
| 6 | Deploy to production | Automated | CI/CD |
| 7 | Verify fix in production | 15 minutes post-deploy | On-call |
| 8 | Post-mortem if hotfix resulted from process gap | 5 business days | IC |

### 9.3 Hotfix Restrictions

- Hotfixes must be **minimal** — fix only the reported issue.
- No feature additions, refactoring, or "while we're at it" changes.
- CI checks are **never bypassed**, even for hotfixes.
- If CI checks cannot pass due to pre-existing issues, those must be fixed first or the hotfix must be rethought.

---

## 10. Change Documentation

### 10.1 Required Documentation

| Change Type | Documentation Required |
|-------------|----------------------|
| New feature | PR description, design doc (if applicable), user guide update |
| Bug fix | PR description with root cause analysis |
| Security fix | PR description, advisory (if public), Security Policy update (if control changed) |
| Dependency update | PR description with changelog review, breaking change assessment |
| Database migration | PR description with schema change summary, rollback plan |
| Configuration change | PR description, runbook update (if applicable) |

### 10.2 Audit Trail

All changes are traceable through:

| Record | Location | Retention |
|--------|----------|-----------|
| Git commit history | GitHub | Permanent |
| Pull request discussions | GitHub | Permanent |
| CI/CD logs | GitHub Actions | 90 days |
| Deployment logs | Render dashboard | 90 days |
| Alembic migration history | `alembic_version` table | Permanent |

---

## 11. Contact

| Role | Contact | Purpose |
|------|---------|---------|
| CTO | cto@paciolus.com | Release approvals, migration review |
| CISO | security@paciolus.com | Security review escalation |
| On-call engineer | PagerDuty rotation | Deployment issues, rollback execution |

---

## Related Documents

| Document | Relationship |
|----------|-------------|
| [Security Policy](./SECURITY_POLICY.md) | Section 1.2 (security-first development), Section 7 (vulnerability management) |
| [Incident Response Plan](./INCIDENT_RESPONSE_PLAN.md) | Hotfix triggers, rollback escalation |
| [Business Continuity / Disaster Recovery](./BUSINESS_CONTINUITY_DISASTER_RECOVERY.md) | Database recovery for migration rollback failures |
| [Access Control Policy](./ACCESS_CONTROL_POLICY.md) | Deployment access permissions, privileged access for production |
| [Audit Logging and Evidence Retention](./AUDIT_LOGGING_AND_EVIDENCE_RETENTION.md) | Change audit trail requirements |

---

**Document Version History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-26 | CTO | Initial publication: SDLC phases, branch protection, 10 CI checks, security review checklist, release process, rollback procedure (<15 min target), hotfix workflow, migration management |

---

*Paciolus — Zero-Storage Trial Balance Diagnostic Intelligence*
