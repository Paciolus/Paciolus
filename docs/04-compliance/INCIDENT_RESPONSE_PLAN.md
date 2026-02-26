# Incident Response Plan

**Version:** 1.0
**Document Classification:** Internal
**Effective Date:** February 26, 2026
**Last Updated:** February 26, 2026
**Owner:** Chief Information Security Officer
**Review Cycle:** Quarterly
**Next Review:** May 26, 2026

---

## Executive Summary

This document defines Paciolus's incident response procedures, severity classification, escalation paths, communication requirements, and post-incident review process. It operationalizes the incident response framework outlined in [SECURITY_POLICY.md](./SECURITY_POLICY.md) Section 6 into a repeatable, auditable playbook.

**Key Controls:**
- ✅ Four severity levels (P0–P3) with defined response SLAs
- ✅ Designated Incident Commander role with rotation schedule
- ✅ Structured communication templates for stakeholders, regulators, and affected users
- ✅ Mandatory blameless post-mortem within 5 business days of resolution
- ✅ Zero-Storage architecture limits breach scope to credentials and metadata only

**Target Audience:** Engineering team, on-call engineers, leadership, compliance officers

---

## Table of Contents

1. [Scope and Definitions](#1-scope-and-definitions)
2. [Severity Classification](#2-severity-classification)
3. [Incident Response Team](#3-incident-response-team)
4. [Detection and Reporting](#4-detection-and-reporting)
5. [Triage and Assessment](#5-triage-and-assessment)
6. [Containment](#6-containment)
7. [Eradication and Recovery](#7-eradication-and-recovery)
8. [Communication](#8-communication)
9. [Post-Incident Review](#9-post-incident-review)
10. [Incident-Specific Playbooks](#10-incident-specific-playbooks)
11. [Training and Exercises](#11-training-and-exercises)
12. [Contact](#12-contact)

---

## 1. Scope and Definitions

### 1.1 Scope

This plan covers all incidents affecting:
- Paciolus production infrastructure (Render, Vercel, PostgreSQL)
- Application-layer security events (authentication bypass, authorization failure)
- Data-related events (credential exposure, Zero-Storage policy violation)
- Availability events (service outage, performance degradation)
- Third-party service failures affecting Paciolus (Stripe, Sentry, SendGrid)

### 1.2 Definitions

| Term | Definition |
|------|------------|
| **Incident** | Any unplanned event that disrupts or threatens Paciolus service, security, or data integrity |
| **Security Incident** | An incident involving unauthorized access, data exposure, or policy violation |
| **Zero-Storage Violation** | Trial balance or financial data persisted to disk, database, or third-party service |
| **Incident Commander (IC)** | The engineer designated to coordinate response activities for a specific incident |
| **Responder** | Any team member actively working on incident resolution |
| **Post-Mortem** | A structured review conducted after incident resolution to identify root causes and preventive measures |

---

## 2. Severity Classification

### 2.1 Severity Levels

| Level | Name | Definition | Response SLA | Resolution Target | Escalation |
|-------|------|------------|--------------|-------------------|------------|
| **P0** | Critical | Complete service outage, active data breach, or Zero-Storage violation | 15 minutes | 4 hours | CTO + CISO immediately |
| **P1** | High | Major functionality degraded (>25% error rate), authentication system down, payment processing failure | 1 hour | 8 hours | CTO within 2 hours |
| **P2** | Medium | Minor functionality degraded, single-tool failure, non-critical export errors, elevated error rates (<25%) | 4 hours | 24 hours | Team lead within 4 hours |
| **P3** | Low | Cosmetic issues, low-impact bugs, non-customer-facing errors | Next business day | 5 business days | None required |

### 2.2 Automatic P0 Triggers

The following conditions automatically classify as P0 regardless of other assessment:

| Trigger | Rationale |
|---------|-----------|
| Zero-Storage violation (financial data persisted) | Core security promise violated |
| Credential database exfiltrated or exposed | User passwords at risk |
| JWT secret key compromised | All active sessions at risk |
| Complete API unavailability (>5 minutes) | Total service outage |
| Ransomware or unauthorized code execution on production | Infrastructure compromise |

### 2.3 Severity Escalation

An incident's severity may be escalated if:
- Impact grows beyond initial assessment
- Resolution target is missed
- Customer-reported impact exceeds initial detection scope
- Regulatory notification thresholds may be triggered

Severity may only be **downgraded** by the Incident Commander after documented justification.

---

## 3. Incident Response Team

### 3.1 Roles

| Role | Responsibilities | Assignment |
|------|-----------------|------------|
| **Incident Commander** | Coordinates all response activities, makes severity decisions, authorizes communications | On-call engineer (rotates weekly) |
| **Technical Lead** | Performs root cause analysis, implements fixes, validates resolution | Senior engineer with domain expertise |
| **Communications Lead** | Drafts status page updates, customer notifications, regulatory notices | Product/support lead |
| **Scribe** | Maintains real-time incident timeline, collects evidence for post-mortem | Any available team member |

### 3.2 On-Call Rotation

| Parameter | Value |
|-----------|-------|
| Rotation cadence | Weekly (Monday 09:00 UTC to following Monday 09:00 UTC) |
| Primary on-call | 1 engineer (all P0–P2 incidents) |
| Secondary on-call | 1 engineer (P0–P1 escalation backup) |
| Notification method | PagerDuty (phone + push) for P0–P1; Slack for P2–P3 |
| Acknowledgment SLA | P0: 5 minutes; P1: 15 minutes; P2: 30 minutes |

### 3.3 Escalation Path

```
P3 → On-call engineer
P2 → On-call engineer → Team lead (if unresolved after 4 hours)
P1 → On-call engineer → CTO (if unresolved after 2 hours)
P0 → On-call engineer + CTO + CISO (immediate parallel notification)
```

---

## 4. Detection and Reporting

### 4.1 Automated Detection

| Source | Monitors | Alert Channel |
|--------|----------|---------------|
| **Sentry** | Application exceptions, error rate spikes | PagerDuty (P0–P1), Slack (P2–P3) |
| **Prometheus** | Parse failures, billing events, metric anomalies | Alertmanager → PagerDuty/Slack |
| **Render** | Infrastructure health, deployment failures | Email + Slack |
| **Stripe** | Webhook delivery failures, payment declines | Stripe Dashboard alerts |
| **Application Logs** | Failed login rate >100/min, Zero-Storage violation markers | Structured log queries → alert |

See [SECURITY_POLICY.md](./SECURITY_POLICY.md) Section 8 for monitoring configuration details.

### 4.2 Manual Reporting

Any team member or external party may report an incident:

| Channel | Address | Response SLA |
|---------|---------|-------------|
| Security email | security@paciolus.com | 2 business days |
| Engineering Slack | #incidents channel | 30 minutes (business hours) |
| Customer support | support@paciolus.com | 4 business hours |
| Vulnerability disclosure | See [VULNERABILITY_DISCLOSURE_POLICY.md](./VULNERABILITY_DISCLOSURE_POLICY.md) | 2 business days |

### 4.3 Incident Declaration

An incident is formally declared when:
1. An automated alert fires at P0 or P1 severity, OR
2. An engineer or team lead manually declares an incident after assessment

**Declaration action:** Create an entry in the incident tracker with timestamp, initial severity, and assigned Incident Commander.

---

## 5. Triage and Assessment

### 5.1 Initial Assessment Checklist

The Incident Commander must complete within the response SLA:

- [ ] **Impact scope:** How many users/features are affected?
- [ ] **Data impact:** Is any stored data (credentials, metadata) at risk?
- [ ] **Zero-Storage check:** Could financial data have been persisted? (If yes → automatic P0)
- [ ] **Service status:** Which endpoints/features are degraded or offline?
- [ ] **Root cause hypothesis:** What is the most likely cause based on initial evidence?
- [ ] **Severity assignment:** Assign P0–P3 based on Section 2 criteria

### 5.2 Evidence Collection

During triage, the Scribe must capture:

| Evidence Type | Collection Method | Retention |
|---------------|-------------------|-----------|
| Application logs (relevant timeframe) | Export from log aggregator with request IDs | Attached to incident record |
| Prometheus metrics (relevant timeframe) | Screenshot or Grafana dashboard export | Attached to incident record |
| Error traces (Sentry) | Link to Sentry issue(s) | Linked in incident record |
| Git history (recent deploys) | `git log --oneline --since="24 hours ago"` | Noted in timeline |
| Database state (if relevant) | Query results (metadata only — no financial data per Zero-Storage) | Sanitized and attached |

---

## 6. Containment

### 6.1 Immediate Containment Actions

| Incident Type | Containment Action | Authorization Required |
|---------------|-------------------|----------------------|
| **Service outage** | Rollback to last known-good deployment | IC approval |
| **Active exploitation** | Block attacking IPs via WAF/rate limiting | IC approval |
| **Credential compromise** | Rotate JWT secret, force-logout all users | IC + CISO approval |
| **Zero-Storage violation** | Immediate data deletion + service halt | IC + CTO approval |
| **Dependency compromise** | Pin affected dependency, deploy patched version | IC approval |
| **Payment system failure** | Enable Stripe maintenance mode, pause checkout | IC + product lead approval |

### 6.2 Containment Principles

1. **Minimize blast radius** — Isolate affected components before attempting fixes.
2. **Preserve evidence** — Capture logs and state before making changes.
3. **Communicate early** — Update status page within 15 minutes of P0/P1 containment.
4. **Rollback first, fix later** — Prefer rollback to previous deployment over hotfix under time pressure.

---

## 7. Eradication and Recovery

### 7.1 Eradication

After containment, the Technical Lead must:

1. **Identify root cause** — Use logs, metrics, and code review to confirm the exact failure.
2. **Develop fix** — Create a targeted patch addressing the root cause.
3. **Test fix** — Validate in staging environment (if time-critical) or full CI pipeline.
4. **Deploy fix** — Standard deployment process (see [SECURE_SDL_CHANGE_MANAGEMENT.md](./SECURE_SDL_CHANGE_MANAGEMENT.md)).

### 7.2 Recovery

| Step | Action | Verification |
|------|--------|-------------|
| 1 | Deploy fix to production | CI pipeline passes, deployment succeeds |
| 2 | Verify service health | Health endpoint returns 200, key workflows functional |
| 3 | Monitor for recurrence | 24-hour elevated monitoring window |
| 4 | Restore normal operations | Remove emergency rate limits, re-enable features |
| 5 | Update status page | Mark incident as "Resolved" with brief summary |

### 7.3 Recovery Verification Checklist

- [ ] All API endpoints returning expected status codes
- [ ] Authentication flow functional (login, refresh, logout)
- [ ] File upload and analysis completing successfully
- [ ] Error rate returned to baseline (<1%)
- [ ] No new alerts firing related to the incident

---

## 8. Communication

### 8.1 Internal Communication

| Audience | Channel | Timing | Content |
|----------|---------|--------|---------|
| On-call team | Slack #incidents | Immediately on detection | Incident declared, severity, IC assigned |
| Engineering team | Slack #engineering | Within 15 minutes (P0–P1) | Impact summary, containment status |
| Leadership (CTO, CEO) | Direct message + email | Within 30 minutes (P0), 2 hours (P1) | Impact, ETA, customer-facing risk |
| All staff | Email | After resolution | Summary and next steps |

### 8.2 External Communication

#### Status Page Updates

| Severity | First Update | Update Cadence | Template |
|----------|-------------|----------------|----------|
| P0 | Within 15 minutes | Every 30 minutes | Template A (Critical) |
| P1 | Within 1 hour | Every 2 hours | Template B (Major) |
| P2 | Within 4 hours | At resolution | Template C (Minor) |
| P3 | Not published | N/A | N/A |

#### Communication Templates

**Template A — Critical Incident (P0):**
```
Subject: [Investigating] Service Disruption

We are currently investigating reports of [brief description].
Our engineering team is actively working on the issue.

Impact: [description of affected functionality]
Status: Investigating
Next update: [time, within 30 minutes]

We apologize for the inconvenience.
```

**Template B — Major Incident (P1):**
```
Subject: [Identified] Degraded Performance on [Component]

We have identified an issue affecting [component/feature].
A fix is being implemented and we expect resolution within [ETA].

Impact: [description]
Status: Identified / Fix in Progress
Next update: [time, within 2 hours]
```

**Template C — Resolution:**
```
Subject: [Resolved] [Original Subject]

The issue reported on [date/time] has been resolved.

Root cause: [brief description]
Resolution: [brief description]
Duration: [start time] to [end time]

We apologize for any disruption. A detailed post-mortem will follow
within 5 business days.
```

### 8.3 Regulatory Notification

**GDPR (Article 33/34):**
- Supervisory authority notification: Within **72 hours** of becoming aware of a personal data breach
- Data subject notification: "Without undue delay" when breach is likely to result in high risk
- Applies to: Credential exposure, metadata leakage, email address exposure
- Does NOT apply to: Zero-Storage financial data (never persisted, cannot be breached)

**CCPA (§1798.82):**
- Notification to affected California residents if unencrypted personal information is exposed
- Notification to California Attorney General if >500 California residents affected

See [PRIVACY_POLICY.md](./PRIVACY_POLICY.md) Section 7 for data breach notification commitments.

### 8.4 Customer Notification Template (Data Breach)

```
Subject: Important Security Notice from Paciolus

Dear [Customer],

We are writing to inform you of a security incident that may have
affected your account.

What happened: [description]
When: [date/time range]
What information was involved: [specific data types]
What was NOT involved: Your financial data (trial balances, account
balances) was not affected. Under our Zero-Storage architecture,
financial data is never retained on our servers.

What we are doing: [remediation steps]
What you should do: [recommended actions — e.g., change password]

If you have questions, contact security@paciolus.com.

Sincerely,
Paciolus Security Team
```

---

## 9. Post-Incident Review

### 9.1 Post-Mortem Requirements

| Parameter | Requirement |
|-----------|-------------|
| Trigger | All P0 and P1 incidents; P2 at IC discretion |
| Deadline | Within **5 business days** of resolution |
| Format | Written document using template below |
| Attendees | IC, Technical Lead, Scribe, affected team members |
| Distribution | All engineering staff + leadership |
| Storage | `docs/08-internal/incident-YYYYMMDD-short-description.md` |

### 9.2 Post-Mortem Template

```markdown
# Post-Mortem: [Incident Title]

**Date:** [YYYY-MM-DD]
**Severity:** [P0/P1/P2]
**Duration:** [start time] to [end time] ([total duration])
**Incident Commander:** [name]
**Author:** [name]

## Summary
[1-2 sentence description of the incident and its impact]

## Timeline
| Time (UTC) | Event |
|------------|-------|
| HH:MM | [Detection / first alert] |
| HH:MM | [IC assigned, triage begins] |
| HH:MM | [Root cause identified] |
| HH:MM | [Fix deployed] |
| HH:MM | [Service restored, monitoring initiated] |

## Root Cause
[Detailed technical explanation. 5 Whys analysis if applicable.]

## Impact
- Users affected: [count or percentage]
- Features affected: [list]
- Data impact: [None / credential exposure / metadata leakage]
- Financial data impact: None (Zero-Storage architecture)
- Duration of impact: [time range]

## Detection
How was the incident detected? [Automated alert / customer report / manual observation]
Was detection timely? [Yes / No — if No, what would improve detection?]

## Response Assessment
- Response SLA met? [Yes / No]
- Resolution target met? [Yes / No]
- Communication timely and accurate? [Yes / No]

## Action Items
| Action | Owner | Priority | Deadline |
|--------|-------|----------|----------|
| [Preventive measure 1] | [name] | [P0-P3] | [date] |
| [Monitoring improvement] | [name] | [P0-P3] | [date] |
| [Process improvement] | [name] | [P0-P3] | [date] |

## Lessons Learned
[Blameless observations about what went well and what to improve]
```

### 9.3 Post-Mortem Principles

1. **Blameless** — Focus on systems and processes, not individuals.
2. **Thorough** — 5 Whys analysis for all P0/P1 incidents.
3. **Actionable** — Every post-mortem produces at least one tracked action item.
4. **Shared** — Distributed to all engineering staff for organizational learning.

### 9.4 Action Item Tracking

Post-mortem action items are tracked in the engineering issue tracker with:
- `incident-followup` label
- Link back to the post-mortem document
- Assigned owner and deadline
- Reviewed in weekly engineering standup until closed

---

## 10. Incident-Specific Playbooks

### 10.1 Zero-Storage Violation

**Trigger:** Financial data (trial balance rows, account balances, transaction details) persisted to disk, database, or third-party service.

| Step | Action | Owner | SLA |
|------|--------|-------|-----|
| 1 | Declare P0 incident | IC | Immediately |
| 2 | Identify persisted data location and scope | Technical Lead | 30 minutes |
| 3 | Delete persisted data from all locations | Technical Lead | 1 hour |
| 4 | Verify deletion (confirm no backups contain data) | IC + CTO | 2 hours |
| 5 | Identify code change that caused persistence | Technical Lead | 4 hours |
| 6 | Rollback or deploy fix | Technical Lead | 4 hours |
| 7 | Commission external security audit for deletion verification | CISO | 5 business days |
| 8 | Public disclosure on status page / blog | Communications Lead | 5 business days |

See [ZERO_STORAGE_ARCHITECTURE.md](./ZERO_STORAGE_ARCHITECTURE.md) Section 10.2 for automated safeguards.

### 10.2 Credential Breach

**Trigger:** Evidence that user credentials (password hashes, email addresses) have been accessed by unauthorized parties.

| Step | Action | Owner | SLA |
|------|--------|-------|-----|
| 1 | Declare P0 incident | IC | Immediately |
| 2 | Rotate JWT secret key (force-logout all users) | Technical Lead | 30 minutes |
| 3 | Revoke all refresh tokens | Technical Lead | 30 minutes |
| 4 | Assess scope (which users, what data) | Technical Lead | 2 hours |
| 5 | Force password reset for affected users | Technical Lead | 4 hours |
| 6 | Notify affected users via email (Template in Section 8.4) | Communications Lead | 72 hours |
| 7 | Notify supervisory authority (GDPR Article 33) | CISO | 72 hours |
| 8 | Conduct post-mortem | IC | 5 business days |

### 10.3 Complete Service Outage

**Trigger:** All API endpoints returning errors or timing out for >5 minutes.

| Step | Action | Owner | SLA |
|------|--------|-------|-----|
| 1 | Declare P0 incident | IC | Immediately |
| 2 | Check infrastructure status (Render, PostgreSQL, Vercel) | Technical Lead | 15 minutes |
| 3 | If deployment-related: rollback to previous version | Technical Lead | 30 minutes |
| 4 | If infrastructure-related: contact provider support | IC | 30 minutes |
| 5 | Update status page | Communications Lead | 15 minutes |
| 6 | Verify service restoration | Technical Lead | Post-fix |
| 7 | 24-hour elevated monitoring | On-call | 24 hours |

### 10.4 Payment System Failure

**Trigger:** Stripe integration errors preventing checkout, subscription management, or webhook processing.

| Step | Action | Owner | SLA |
|------|--------|-------|-----|
| 1 | Assess severity (P1 if checkout only, P0 if webhook processing down >1 hour) | IC | 30 minutes |
| 2 | Check Stripe status page | Technical Lead | 15 minutes |
| 3 | If Paciolus code issue: deploy fix | Technical Lead | 2 hours |
| 4 | If Stripe outage: monitor and communicate | IC | Ongoing |
| 5 | Reconcile any missed webhook events after restoration | Technical Lead | 24 hours |

---

## 11. Training and Exercises

### 11.1 Training Schedule

| Training | Frequency | Audience | Format |
|----------|-----------|----------|--------|
| IRP overview and role assignments | Onboarding (Day 1) | All engineering | Walkthrough |
| Tabletop exercise (P0 scenario) | Semi-annual | All engineering | Facilitated simulation |
| On-call handoff review | Weekly | Incoming/outgoing on-call | 15-minute briefing |
| Communication template review | Annual | Communications leads | Workshop |

### 11.2 Tabletop Exercise Scenarios

Conduct at least two of the following per year:

1. **Zero-Storage violation** — A code change persists trial balance data to the database.
2. **Credential breach** — An attacker gains read access to the users table.
3. **Infrastructure failure** — Render experiences a 2-hour outage during business hours.
4. **Supply chain attack** — A Python dependency is found to contain malicious code.

### 11.3 Exercise Evaluation

After each exercise, evaluate:
- Were roles clearly understood?
- Were SLAs met in the simulated timeline?
- Were communication templates effective?
- What improvements are needed?

Document findings and update this plan accordingly.

---

## 12. Contact

| Role | Contact | Availability |
|------|---------|-------------|
| On-call engineer | PagerDuty rotation | 24/7 |
| CISO | security@paciolus.com | Business hours + P0 escalation |
| CTO | Direct contact | Business hours + P0 escalation |
| Legal | legal@paciolus.com | Business hours |
| Communications | support@paciolus.com | Business hours |

---

## Related Documents

| Document | Relationship |
|----------|-------------|
| [Security Policy](./SECURITY_POLICY.md) | Section 6 (incident response overview), Section 8 (monitoring) |
| [Privacy Policy](./PRIVACY_POLICY.md) | Section 7 (breach notification commitments) |
| [Zero-Storage Architecture](./ZERO_STORAGE_ARCHITECTURE.md) | Section 10.2 (automated safeguards) |
| [Vulnerability Disclosure Policy](./VULNERABILITY_DISCLOSURE_POLICY.md) | External vulnerability reporting procedures |
| [Business Continuity / Disaster Recovery](./BUSINESS_CONTINUITY_DISASTER_RECOVERY.md) | Recovery procedures for infrastructure failures |
| [Audit Logging and Evidence Retention](./AUDIT_LOGGING_AND_EVIDENCE_RETENTION.md) | Evidence collection and preservation |

---

**Document Version History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-26 | CISO | Initial publication: severity classification, triage SLAs, communication templates, 4 incident playbooks, post-mortem template, training schedule |

---

*Paciolus — Zero-Storage Trial Balance Diagnostic Intelligence*
