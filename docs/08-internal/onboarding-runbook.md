# New Employee Onboarding Runbook

**Document Classification:** Internal
**Version:** 1.0
**Created:** February 27, 2026
**Last Updated:** February 27, 2026
**Owner:** CTO
**Review Cycle:** Annual

---

## Overview

This runbook defines the mandatory steps for onboarding new Paciolus team members. It ensures consistent access provisioning, security training completion, and policy acknowledgment before any team member begins work on production systems.

**Timeline summary:**
- **Day 0 (before start):** IT/access prep
- **Day 1:** Accounts, policy acknowledgment, first security training modules
- **Week 1:** Remaining training, codebase orientation, first contribution
- **Day 30:** All training complete; access review scheduled

---

## Pre-Hire Checklist (Manager — Complete Before Day 1)

- [ ] Confirm role, start date, and system access requirements
- [ ] Request GitHub org invitation (admin approves)
- [ ] Request Render access at appropriate tier (view-only for non-engineers; deploy access for engineers)
- [ ] Request Vercel project access (viewer for non-engineers; developer for engineers)
- [ ] Request Sentry project membership
- [ ] **Do NOT provision:** Stripe dashboard, PostgreSQL direct access, SendGrid API keys — these require separate authorization per `ACCESS_CONTROL_POLICY.md §5`
- [ ] Schedule Day 1 orientation meeting (30–60 min) with manager
- [ ] Brief CISO of new hire (for access audit trail)

---

## Day 1 Checklist

### Account Setup
- [ ] Create Paciolus email account (`@paciolus.com`)
- [ ] Set up password manager (Bitwarden or equivalent) — never save passwords in browser
- [ ] Enable MFA on all provisioned accounts (GitHub, Render, Vercel, Sentry) — **MFA is mandatory**
- [ ] Receive and acknowledge provisioned credential list

### Policy Acknowledgment
- [ ] Read `docs/04-compliance/SECURITY_POLICY.md` (full document)
- [ ] Read `docs/04-compliance/ACCESS_CONTROL_POLICY.md` (full document)
- [ ] Read `docs/04-compliance/ZERO_STORAGE_ARCHITECTURE.md` (full document — critical for understanding what data must never be stored)
- [ ] Sign acknowledgment form (or send email to CISO confirming receipt and review)

### Security Training — Day 1 Modules
Complete the following modules from `docs/08-internal/security-training-curriculum-2026.md` on Day 1:
- [ ] **Module 3:** Incident Response Roles + Escalation (~30 min) — know your role before you have system access
- [ ] **Module 4:** Access Control + Least Privilege (~30 min) — understand credential hygiene before handling any secrets
- [ ] **Module 5:** Social Engineering + Phishing (~30 min)

Log Day 1 completions in `docs/08-internal/security-training-log-2026.md`.

---

## Week 1 Checklist

### Remaining Security Training
Complete by end of Week 1:
- [ ] **Module 1:** OWASP Top 10 (~1 hour)
- [ ] **Module 2:** Secure Coding — Python + TypeScript (~1 hour) — **engineers only**

Log completions in `docs/08-internal/security-training-log-2026.md`. Manager reviews attestation answers.

### Codebase Orientation (Engineers)
- [ ] Clone repository: `git clone https://github.com/[org]/paciolus`
- [ ] Read `CONTRIBUTING.md` (contribution workflow, pre-commit hooks, PR checklist)
- [ ] Read `CLAUDE.md` (project protocol, design mandate, architecture patterns)
- [ ] Set up local development environment per README
- [ ] Run `npm run build` + `pytest` to confirm environment is working
- [ ] Review the Zero-Storage architecture in code: `backend/shared/security_utils.py` + `scripts/accounting_invariants.py`
- [ ] Submit a small first PR (documentation or minor fix) to practice the PR process

### Architecture Overview (All Roles)
- [ ] Read `docs/02-technical/ARCHITECTURE.md`
- [ ] Read `docs/07-user-facing/USER_GUIDE.md` — understand the product from the customer's perspective
- [ ] Watch a demo of the 12-tool suite (or run one locally)

---

## Day 30 Checkpoint

Manager conducts 30-day check-in:

- [ ] All 5 training modules complete (4 for non-engineers)? Log confirmed in training log.
- [ ] All accounts have MFA enabled? Verify in GitHub/Render/Vercel.
- [ ] Any access needs to be adjusted (more or less than provisioned)?
- [ ] Any security questions or concerns raised during onboarding?
- [ ] Confirm CISO has recorded the new hire in the quarterly access review scope

---

## Access Provisioning Reference

### Standard Provisioning by Role

| System | Engineer | Non-Engineer |
|--------|----------|-------------|
| GitHub | Write access (team repos) | Read access |
| Render | Deploy access (non-prod); view-only (prod) | View-only |
| Vercel | Developer access | Viewer access |
| Sentry | Member (project-specific) | Member (project-specific) |
| PostgreSQL (direct) | Read-only staging only; production requires CTO approval | None |
| Stripe Dashboard | None by default; requires CTO approval | None by default |
| SendGrid | None by default; API key generated per-service, not personal | None |

### Elevated Access (Requires CTO + CISO Approval)
- Production database write access
- Stripe dashboard admin
- Render service admin
- GitHub organization admin

---

## Offboarding (For Reference)

When a team member departs:
- [ ] Revoke all system access within 24 hours of departure notice
- [ ] Rotate any secrets the team member had access to (if credentials were personal)
- [ ] Transfer or archive any documentation they owned
- [ ] Remove from `security-training-log-YYYY.md` compliance tracking
- [ ] Document in the next quarterly access review (`docs/08-internal/access-review-YYYY-QN.md`)

---

## Related Documents

| Document | Relationship |
|----------|-------------|
| [Security Policy](../../04-compliance/SECURITY_POLICY.md) | §10 — Security Training requirements |
| [Access Control Policy](../../04-compliance/ACCESS_CONTROL_POLICY.md) | Access provisioning rules and quarterly review process |
| [Security Training Curriculum](./security-training-curriculum-2026.md) | Full 5-module training content |
| [Security Training Log](./security-training-log-2026.md) | Completion tracking |
| [CONTRIBUTING.md](../../../CONTRIBUTING.md) | PR workflow, pre-commit hooks, security checklist |

---

## Document Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-27 | CTO | Initial publication |

---

*Paciolus — Zero-Storage Trial Balance Diagnostic Intelligence*
