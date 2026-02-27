# Quarterly Access Review — Template

**Document Classification:** Internal — SOC 2 Evidence Artifact
**Control Reference:** CC6.1 / CC3.1 — Privileged access reviews
**Template Version:** 1.0
**Source policy:** `docs/04-compliance/ACCESS_CONTROL_POLICY.md` §8

> **Usage:** Copy this file to `docs/08-internal/access-review-YYYY-QN.md`, replace all `[PLACEHOLDER]` values, and complete each system table by reviewing the actual provider dashboards. File the completed review in `docs/08-internal/soc2-evidence/cc6/`.

---

## 1. Review Metadata

| Field | Value |
|-------|-------|
| **Review period** | [YYYY] Q[N] (e.g., 2026 Q1) |
| **Review date** | [YYYY-MM-DD] |
| **Reviewer name** | [Name] |
| **Reviewer role** | [e.g., CISO / CTO] |
| **Scope** | All system access — GitHub, Render, Vercel, PostgreSQL, Sentry, SendGrid, Stripe |
| **Next review due** | [YYYY-MM-DD] (approximately 90 days) |
| **Report status** | DRAFT / FINAL |

---

## 2. Review Scope

This review covers all personnel and service account access across the 7 systems that host or support the Paciolus production environment. For each account, the reviewer assesses:

1. Does this person/service still require this access?
2. Is the access level appropriate (not overly permissive)?
3. Is MFA enabled where required?
4. Should any access be modified or removed?

**Action codes used in tables:**

| Code | Meaning |
|------|---------|
| ✅ RETAIN | Access confirmed appropriate; no change |
| ✏️ MODIFY | Access level changed (document new level in Notes) |
| ❌ REMOVE | Access revoked (document date removed in Notes) |
| ⚠️ EXCEPTION | Access retained despite policy concern (requires documented justification) |

---

## 3. System-by-System Review

### 3.1 GitHub — Repository Access

**Review source:** GitHub → Organization → People → [org-name]

**Roles to check:** Owner, Member, Outside Collaborator; per-repo access levels (Admin / Write / Read)

| Account / User | Role / Access Level | Business Justification | MFA Enabled? | Action | Notes |
|---------------|--------------------|-----------------------|-------------|--------|-------|
| [name] | [Owner / Member / Collaborator] | [justification] | [Yes / No] | [✅/✏️/❌/⚠️] | |
| _Add rows for all org members and collaborators_ | | | | | |

**Service accounts / bots:**

| Account | Purpose | Permissions | Last Used | Action | Notes |
|---------|---------|-------------|----------|--------|-------|
| GitHub Actions (`GITHUB_TOKEN`) | CI/CD pipeline | Repo write (scoped) | Automated | ✅ RETAIN | Review workflow permissions |
| Dependabot | Dependency PRs | PR write | Automated | ✅ RETAIN | |
| [any deploy keys] | | | | | |

**Summary:**
- Accounts reviewed: [N]
- Accounts removed: [N]
- Accounts modified: [N]
- Exceptions: [N]

---

### 3.2 Render — Backend Hosting + Database Access

**Review source:** Render Dashboard → Team → Members

**Roles:** Owner, Admin, Member (deploy), Billing

| Account / User | Role | Services Accessible | MFA Enabled? | Action | Notes |
|---------------|------|--------------------|-----------  |--------|-------|
| [name] | [Owner / Admin / Member] | [list services] | [Yes / No] | [✅/✏️/❌/⚠️] | |
| _Add rows for all Render team members_ | | | | | |

**Database access (PostgreSQL):**

| Account / User | DB Access Method | Access Level | Business Justification | Action | Notes |
|---------------|-----------------|-------------|----------------------|--------|-------|
| [name] | [Render DB console / external connection] | [Read / Read-Write / Admin] | [justification] | [✅/✏️/❌/⚠️] | |

**Summary:**
- Accounts reviewed: [N]
- Accounts removed: [N]
- Accounts modified: [N]

---

### 3.3 Vercel — Frontend Hosting

**Review source:** Vercel Dashboard → Team → Members

**Roles:** Owner, Member, Viewer

| Account / User | Role | MFA Enabled? | Action | Notes |
|---------------|------|-------------|--------|-------|
| [name] | [Owner / Member / Viewer] | [Yes / No] | [✅/✏️/❌/⚠️] | |
| _Add rows for all Vercel team members_ | | | | |

**Summary:**
- Accounts reviewed: [N]
- Accounts removed: [N]
- Accounts modified: [N]

---

### 3.4 PostgreSQL — Direct Database Access

**Review source:** Render DB settings → Connection details; check if any external IP allowlist entries exist

**Note:** Direct database access should be restricted to production emergencies only. Staging read-only access is permitted for engineers.

| Account / Role | Access Type | Allowed IPs / Methods | Business Justification | Action | Notes |
|---------------|------------|----------------------|----------------------|--------|-------|
| Application service account | Read/Write (connection string) | Render internal | Production application | ✅ RETAIN | Verify connection uses `sslmode=require` |
| [engineer name] | Read-only staging | [IP or method] | [justification] | [✅/✏️/❌/⚠️] | |
| [any other accounts] | | | | | |

**Summary:**
- DB accounts reviewed: [N]
- Accounts removed: [N]
- Accounts modified: [N]

---

### 3.5 Sentry — Error Tracking

**Review source:** Sentry Dashboard → Organization → Members

**Roles:** Owner, Manager, Member, Billing

| Account / User | Role | Projects Accessible | MFA Enabled? | Action | Notes |
|---------------|------|--------------------|-----------  |--------|-------|
| [name] | [Owner / Manager / Member] | [project names] | [Yes / No] | [✅/✏️/❌/⚠️] | |
| _Add rows for all Sentry members_ | | | | | |

**Summary:**
- Accounts reviewed: [N]
- Accounts removed: [N]
- Accounts modified: [N]

---

### 3.6 SendGrid — Transactional Email

**Review source:** SendGrid Dashboard → Settings → API Keys; Settings → Teammates

**Important:** Review both (a) team member dashboard access and (b) API keys in use. Revoke any keys not actively used by a service.

**Team members:**

| Account / User | Role | MFA Enabled? | Action | Notes |
|---------------|------|-------------|--------|-------|
| [name] | [Owner / Administrator / Developer / Restricted] | [Yes / No] | [✅/✏️/❌/⚠️] | |

**API Keys:**

| Key Name | Permissions | Service Using It | Last Used | Action | Notes |
|----------|------------|-----------------|----------|--------|-------|
| `paciolus-production` | Mail Send | Backend (Render env var) | [date or "active"] | ✅ RETAIN | Confirm still in use |
| [any other keys] | | | | | |

**Action for unused keys:** Revoke immediately. Document key name and revocation date in Notes.

**Summary:**
- Team members reviewed: [N]
- API keys reviewed: [N]
- Keys revoked: [N] (list names)

---

### 3.7 Stripe — Payment Processing

**Review source:** Stripe Dashboard → Settings → Team

**Roles:** Administrator, Developer, View only, Support specialist, Refund analyst

**Note:** Stripe dashboard access to live keys is highly sensitive. Only personnel who actively manage billing or investigate payment issues should have access.

| Account / User | Role | Restricted to Test Mode? | Business Justification | Action | Notes |
|---------------|------|------------------------|----------------------|--------|-------|
| [name] | [Administrator / Developer / View only] | [Yes / No] | [justification] | [✅/✏️/❌/⚠️] | |
| _Add rows for all Stripe team members_ | | | | | |

**API Keys in use:**

| Key Type | Environment | Stored In | Action | Notes |
|----------|------------|----------|--------|-------|
| Secret key (`sk_live_...`) | Production | Render env var | ✅ RETAIN | Verify not in code or logs |
| Secret key (`sk_test_...`) | Test | Local `.env` / CI secret | ✅ RETAIN | Verify not committed to git |
| Webhook signing secret | Production | Render env var | ✅ RETAIN | |

**Summary:**
- Accounts reviewed: [N]
- Accounts removed: [N]
- Accounts modified: [N]

---

## 4. Exceptions

> List any access that was retained despite not fully meeting policy requirements. Each exception requires a documented business justification and CISO approval.

| System | Account | Policy Concern | Business Justification | Compensating Control | Approver | Exception Expiry |
|--------|---------|---------------|----------------------|---------------------|----------|-----------------|
| [system] | [account] | [what policy is not met] | [why access is retained] | [what mitigates the risk] | [CISO name] | [date] |

_If no exceptions: write "None"_

---

## 5. Actions Taken

> Summary of all access changes made during this review cycle.

| Date | System | Account | Action | Performed By |
|------|--------|---------|--------|-------------|
| [YYYY-MM-DD] | [system] | [account] | [Removed / Modified to [new level]] | [name] |

_If no changes: write "No changes required — all access confirmed appropriate"_

---

## 6. Sign-Off

| Role | Name | Date | Signature / Initials |
|------|------|------|---------------------|
| **Reviewer (CISO / CTO)** | [name] | [YYYY-MM-DD] | [initials] |
| **Secondary reviewer (optional)** | [name] | [YYYY-MM-DD] | [initials] |

By signing, the reviewer attests that:
1. All system access listed above was verified against the actual provider dashboard
2. Access not justified by current role has been removed or is documented as an exception
3. All personnel with production access have MFA enabled (or exceptions are documented)
4. This report accurately reflects the access state as of the review date

---

## 7. Next Review

| Field | Value |
|-------|-------|
| **Next review due** | [YYYY-MM-DD] |
| **Calendar reminder set?** | [Yes / No] |
| **Reminder owner** | [name] |

---

*Paciolus — Zero-Storage Trial Balance Diagnostic Intelligence*
*SOC 2 Type II evidence template — CC6.1 / CC3.1*
