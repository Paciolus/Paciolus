# Quarterly Access Review — 2026 Q1

**Document Classification:** Internal — SOC 2 Evidence Artifact
**Control Reference:** CC6.1 / CC3.1 — Privileged access reviews
**Review Period:** 2026 Q1 (January 1 – March 31, 2026)
**Due Date:** March 31, 2026
**Template source:** `docs/08-internal/access-review-template.md`

> **CEO ACTION:** Complete this review by March 31, 2026. For each system, log in to the provider dashboard and fill in every table row. Use the action codes: ✅ RETAIN / ✏️ MODIFY / ❌ REMOVE / ⚠️ EXCEPTION. When done, copy this file to `docs/08-internal/soc2-evidence/cc6/access-review-2026-Q1.md`.

---

## 1. Review Metadata

| Field | Value |
|-------|-------|
| **Review period** | 2026 Q1 (January 1 – March 31, 2026) |
| **Review date** | _[CEO ACTION: date review was completed]_ |
| **Reviewer name** | _[CEO ACTION: name]_ |
| **Reviewer role** | _[CEO ACTION: e.g., CISO / CTO]_ |
| **Scope** | All system access — GitHub, Render, Vercel, PostgreSQL, Sentry, SendGrid, Stripe |
| **Next review due** | 2026-06-30 (Q2) |
| **Report status** | _[CEO ACTION: DRAFT → FINAL when signed]_ |

---

## 2. Review Scope

This Q1 2026 review is the **first access review conducted** for Paciolus. It establishes the baseline access inventory that subsequent quarterly reviews will track for changes.

**Action codes:**

| Code | Meaning |
|------|---------|
| ✅ RETAIN | Access confirmed appropriate; no change |
| ✏️ MODIFY | Access level changed (document new level in Notes) |
| ❌ REMOVE | Access revoked (document date removed in Notes) |
| ⚠️ EXCEPTION | Access retained despite policy concern (requires documented justification) |

---

## 3. System-by-System Review

### 3.1 GitHub — Repository Access

**How to review:** GitHub.com → [Your Organization] → People tab

**Check for:** Anyone who no longer works at Paciolus; outside collaborators who no longer need access; anyone with Owner/Admin who doesn't need it; MFA disabled (GitHub org can enforce MFA — verify setting is enabled).

**Team members:**

| Account / User | Role | MFA Enabled? | Action | Notes |
|---------------|------|-------------|--------|-------|
| _[CEO ACTION: list all GitHub org members]_ | | | | |

**Outside collaborators (if any):**

| Account | Repo(s) | Purpose / Expiry | Action | Notes |
|---------|---------|-----------------|--------|-------|
| _[CEO ACTION: list all, or write "None"]_ | | | | |

**Service accounts / automations:**

| Account | Purpose | Permissions | Action | Notes |
|---------|---------|-------------|--------|-------|
| GitHub Actions `GITHUB_TOKEN` | CI/CD pipeline | Repo write (scoped per workflow) | ✅ RETAIN | Verify `permissions:` block is set in each workflow file |
| Dependabot | Dependency PRs | PR create | ✅ RETAIN | |
| _[CEO ACTION: any deploy keys or other bots]_ | | | | |

**GitHub org settings to verify:**
- [ ] Org-level MFA enforcement enabled? _[CEO ACTION: Yes / No — if No, enable it]_
- [ ] No public repositories that should be private? _[CEO ACTION: verify]_

**Section summary:**
- Members reviewed: _[N]_ | Removed: _[N]_ | Modified: _[N]_ | Exceptions: _[N]_

---

### 3.2 Render — Backend Hosting + Database Access

**How to review:** render.com → Dashboard → Team (top-right menu)

**Check for:** Anyone who has left or changed roles; anyone with Admin who only needs Member-level; verify all services accessible match current team needs.

**Team members:**

| Account / User | Role | Services Accessible | MFA Enabled? | Action | Notes |
|---------------|------|--------------------|-----------  |--------|-------|
| _[CEO ACTION: list all Render team members]_ | | | | | |

**Database access (PostgreSQL connection):**

| Access Method | Used By | Authorized? | Action | Notes |
|--------------|---------|------------|--------|-------|
| Connection string in Render env var | Backend application (`DATABASE_URL`) | Yes — application only | ✅ RETAIN | Verify `sslmode=require` in connection string |
| External DB connection (IP allowlist) | _[CEO ACTION: anyone with direct external access?]_ | _[CEO ACTION]_ | _[CEO ACTION]_ | _[CEO ACTION: if no external access, write "None — internal only"]_ |

**Section summary:**
- Members reviewed: _[N]_ | Removed: _[N]_ | Modified: _[N]_

---

### 3.3 Vercel — Frontend Hosting

**How to review:** vercel.com → Team → Settings → Members

**Check for:** Anyone who has left; anyone with unnecessary admin access; unrecognized accounts.

| Account / User | Role | MFA Enabled? | Action | Notes |
|---------------|------|-------------|--------|-------|
| _[CEO ACTION: list all Vercel team members]_ | | | | |

**Section summary:**
- Members reviewed: _[N]_ | Removed: _[N]_ | Modified: _[N]_

---

### 3.4 PostgreSQL — Direct Database Roles

**How to review:** Render DB → Connect tab (shows connection methods); run `\du` in psql to list database roles if you have CLI access.

**Note:** The principle of least privilege requires that no human has persistent read-write access to the production database outside of a declared incident. This section documents what exists and establishes the authorized baseline.

| Role / Account | Type | Access Level | Authorized? | Action | Notes |
|---------------|------|-------------|------------|--------|-------|
| Application service user (connection string) | Service account | Read + Write (application tables) | Yes | ✅ RETAIN | Only account that should have write access |
| `postgres` superuser | System | Superuser | Yes — Render managed | ✅ RETAIN | Render controls this; no direct human access |
| _[CEO ACTION: any additional roles from `\du` output?]_ | | | | | |

**`\du` output (optional but recommended):**
```
-- Paste output of: psql $DATABASE_URL -c "\du" here
_[CEO ACTION]_
```

**Section summary:**
- Roles reviewed: _[N]_ | Removed: _[N]_ | Modified: _[N]_

---

### 3.5 Sentry — Error Tracking

**How to review:** sentry.io → Organization Settings → Members

**Check for:** Anyone who has left; contractors with expired need; anyone with Manager/Owner who only needs Member.

| Account / User | Role | Projects | MFA Enabled? | Action | Notes |
|---------------|------|---------|-------------|--------|-------|
| _[CEO ACTION: list all Sentry org members]_ | | | | | |

**Section summary:**
- Members reviewed: _[N]_ | Removed: _[N]_ | Modified: _[N]_

---

### 3.6 SendGrid — Transactional Email

**How to review:**
- Team members: app.sendgrid.com → Settings → Teammates
- API keys: app.sendgrid.com → Settings → API Keys

**Critical:** Review all API keys. Any key not actively used by a named service should be revoked immediately.

**Team members:**

| Account / User | Role | MFA Enabled? | Action | Notes |
|---------------|------|-------------|--------|-------|
| _[CEO ACTION: list all SendGrid teammates, or write "No teammates — single owner account"]_ | | | | |

**API keys:**

| Key Name | Permissions | Service | Created | Last Used | Action | Notes |
|----------|------------|---------|---------|----------|--------|-------|
| _[CEO ACTION: list every API key shown in the dashboard]_ | | | | | | |

> For each key: if you cannot identify which service uses it or when it was last used, **revoke it**. The application will surface an error immediately if a key in active use was revoked — you can then restore it with a new key.

**Keys revoked during this review:** _[CEO ACTION: list any revoked keys with revocation date, or "None"]_

**Section summary:**
- Team members reviewed: _[N]_ | API keys reviewed: _[N]_ | Keys revoked: _[N]_

---

### 3.7 Stripe — Payment Processing

**How to review:** dashboard.stripe.com → Settings → Team

**Critical:** Live-mode secret keys (`sk_live_`) grant full access to charge customers. Only personnel with an active business need should have Stripe dashboard access.

**Team members:**

| Account / User | Role | Live Mode Access? | MFA Enabled? | Action | Notes |
|---------------|------|-----------------|-------------|--------|-------|
| _[CEO ACTION: list all Stripe team members]_ | | | | | |

**API keys audit:**

| Key | Environment | Location | Action | Notes |
|-----|------------|---------|--------|-------|
| `sk_live_...` (secret) | Production | Render env var (`STRIPE_SECRET_KEY`) | ✅ RETAIN | Verify not in git, not in logs |
| `sk_test_...` (secret) | Test/CI | CI secret + local `.env` | ✅ RETAIN | Verify `.env` is in `.gitignore` |
| `whsec_...` (webhook) | Production | Render env var (`STRIPE_WEBHOOK_SECRET`) | ✅ RETAIN | |
| `whsec_...` (webhook) | Test | CI secret | ✅ RETAIN | |
| _[any other keys or restricted keys?]_ | | | | |

**Restricted API keys (if any):**
_[CEO ACTION: list any restricted keys created for specific purposes, or write "None — using standard secret key only"]_

**Section summary:**
- Members reviewed: _[N]_ | Removed: _[N]_ | Modified: _[N]_

---

## 4. Exceptions

> Access that was retained despite a policy concern requires documented justification.

| System | Account | Policy Concern | Business Justification | Compensating Control | Approver | Exception Expiry |
|--------|---------|---------------|----------------------|---------------------|----------|-----------------|
| _[CEO ACTION: list exceptions, or write "None"]_ | | | | | | |

---

## 5. Actions Taken

> Complete this section after finishing all system reviews above.

| Date | System | Account | Action Taken | Performed By |
|------|--------|---------|-------------|-------------|
| _[CEO ACTION: list every change made — removed account, modified role, revoked key — or write "No changes: all access confirmed appropriate"]_ | | | | |

---

## 6. Sign-Off

| Role | Name | Date | Initials |
|------|------|------|---------|
| **Reviewer (CISO / CTO)** | _[CEO ACTION]_ | _[CEO ACTION]_ | _[CEO ACTION]_ |

By signing, the reviewer attests that:
1. All system access was verified against the actual provider dashboard during this review
2. Access not justified by current role has been removed or documented as an exception above
3. All personnel with production access have MFA enabled (or exceptions are documented)
4. This report accurately reflects the access state as of the review date

---

## 7. Next Review

| Field | Value |
|-------|-------|
| **Next review due** | 2026-06-30 (Q2) |
| **Calendar reminder set?** | _[CEO ACTION: Yes / No]_ |
| **Reminder owner** | _[CEO ACTION: name]_ |

**Subsequent reviews:** Q3 due 2026-09-30, Q4 due 2026-12-31

---

## Related Documents

| Document | Relationship |
|----------|-------------|
| [Access Control Policy §8](../../04-compliance/ACCESS_CONTROL_POLICY.md) | Defines review cadence, scope, and output requirements |
| [Access Review Template](./access-review-template.md) | Reusable template this document was generated from |
| [Onboarding Runbook](./onboarding-runbook.md) | Provisioning standards new hire access should conform to |

---

*Paciolus — Zero-Storage Trial Balance Diagnostic Intelligence*
*SOC 2 Type II evidence artifact — CC6.1 / CC3.1*
*Q1 2026 | Due: 2026-03-31*
