# Business Continuity and Disaster Recovery Plan

**Version:** 1.0
**Document Classification:** Internal
**Effective Date:** February 26, 2026
**Last Updated:** February 26, 2026
**Owner:** Chief Technology Officer
**Review Cycle:** Semi-annual
**Next Review:** August 26, 2026

---

## Executive Summary

This document defines Paciolus's business continuity and disaster recovery (BCP/DR) objectives, procedures, and testing requirements. Paciolus's Zero-Storage architecture significantly reduces recovery complexity — financial data is never persisted, so there is no financial data to recover.

**Key Controls:**
- ✅ Defined RTO/RPO targets for all service tiers
- ✅ Automated database backups with tested restore procedures
- ✅ Infrastructure dependency map with provider SLA references
- ✅ Semi-annual backup restore testing with documented results
- ✅ Zero-Storage architecture eliminates financial data recovery requirements

**Target Audience:** Engineering team, leadership, auditors, enterprise customers

---

## Table of Contents

1. [Scope and Objectives](#1-scope-and-objectives)
2. [Recovery Objectives](#2-recovery-objectives)
3. [Infrastructure Dependency Map](#3-infrastructure-dependency-map)
4. [Backup Strategy](#4-backup-strategy)
5. [Disaster Recovery Procedures](#5-disaster-recovery-procedures)
6. [Business Continuity Procedures](#6-business-continuity-procedures)
7. [Testing and Validation](#7-testing-and-validation)
8. [Roles and Responsibilities](#8-roles-and-responsibilities)
9. [Contact](#9-contact)

---

## 1. Scope and Objectives

### 1.1 Scope

This plan covers continuity and recovery for:
- Paciolus backend API services (Render)
- Paciolus frontend application (Vercel)
- PostgreSQL database (managed, Render/AWS)
- Third-party integrations (Stripe, Sentry, SendGrid)
- DNS and TLS certificate infrastructure

### 1.2 Objectives

| Objective | Target |
|-----------|--------|
| Ensure service availability meets customer commitments | 99.9% uptime (measured monthly) |
| Recover from infrastructure failure within defined RTO | See Section 2 |
| Limit data loss to within defined RPO | See Section 2 |
| Validate recovery capability through regular testing | Semi-annual restore tests |

### 1.3 Zero-Storage Impact on DR

Paciolus's [Zero-Storage Architecture](./ZERO_STORAGE_ARCHITECTURE.md) fundamentally simplifies disaster recovery:

| Traditional SaaS | Paciolus |
|-------------------|----------|
| Must recover customer financial data from backups | No financial data to recover |
| Data loss window = time since last backup | Financial data loss window = 0 (never stored) |
| Recovery includes data integrity verification | Recovery limited to credentials, metadata, billing |
| Breach during DR may expose financial records | Financial records cannot be exposed (do not exist) |

**What DR covers for Paciolus:** User accounts, client metadata, engagement records, billing state, activity logs (aggregate summaries), and application configuration.

---

## 2. Recovery Objectives

### 2.1 RTO/RPO by Service Tier

| Service Component | RTO (Recovery Time Objective) | RPO (Recovery Point Objective) | Priority |
|-------------------|-------------------------------|--------------------------------|----------|
| **Authentication & API** | 1 hour | 1 hour | Critical |
| **Frontend application** | 30 minutes | 0 (static assets, CDN-cached) | Critical |
| **PostgreSQL database** | 2 hours | 1 hour (point-in-time recovery) | Critical |
| **Billing (Stripe integration)** | 4 hours | 0 (Stripe is source of truth) | High |
| **Email (SendGrid)** | 8 hours | N/A (transactional, not queued) | Medium |
| **Error tracking (Sentry)** | 24 hours | N/A (diagnostic, not operational) | Low |
| **Prometheus metrics** | 24 hours | N/A (can be rebuilt from logs) | Low |

### 2.2 RTO/RPO Definitions

- **RTO:** Maximum acceptable time from incident declaration to service restoration.
- **RPO:** Maximum acceptable data loss measured in time. An RPO of 1 hour means we accept losing up to 1 hour of data changes.

### 2.3 Availability Target

| Metric | Target | Measurement |
|--------|--------|-------------|
| Monthly uptime | 99.9% | (total minutes - downtime minutes) / total minutes |
| Maximum planned downtime | 30 minutes/month | Maintenance windows (with 48-hour notice) |
| Maximum unplanned downtime | 43 minutes/month | Based on 99.9% SLA |

---

## 3. Infrastructure Dependency Map

### 3.1 Service Dependencies

```
┌─────────────────────────────────────────────────────┐
│ USERS (Browser)                                     │
└───────────┬─────────────────────────────┬───────────┘
            │ HTTPS                       │ HTTPS
            ▼                             ▼
┌───────────────────┐         ┌───────────────────────┐
│ Vercel (Frontend)  │         │ Render (Backend API)   │
│ CDN + Edge Network │         │ Docker container       │
│ SLA: 99.99%        │         │ SLA: 99.95%            │
└───────────────────┘         └──────────┬────────────┘
                                         │
                    ┌────────────────────┬┴───────────────────┐
                    │                    │                     │
                    ▼                    ▼                     ▼
          ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
          │ PostgreSQL (DB)  │  │ Stripe           │  │ SendGrid         │
          │ Managed instance │  │ Payments         │  │ Transactional    │
          │ SLA: 99.95%      │  │ SLA: 99.99%      │  │ email            │
          └─────────────────┘  └─────────────────┘  └─────────────────┘
                                         │
                                         ▼
                               ┌─────────────────┐
                               │ Sentry           │
                               │ Error tracking   │
                               │ SLA: 99.9%       │
                               └─────────────────┘
```

### 3.2 Dependency Classification

| Dependency | Criticality | Failure Impact | Fallback |
|------------|-------------|----------------|----------|
| **Render (API hosting)** | Critical | Complete API unavailability | Redeploy to secondary provider |
| **PostgreSQL (database)** | Critical | No auth, no client data, no billing records | Restore from backup to new instance |
| **Vercel (frontend hosting)** | Critical | No UI access (API still functional via direct calls) | Deploy to secondary CDN |
| **Stripe** | High | No new subscriptions or billing changes; existing access unaffected | Graceful degradation (disable billing UI) |
| **SendGrid** | Medium | No email verification, no notifications; core analysis unaffected | Queue emails for retry; manual verification |
| **Sentry** | Low | No error tracking; service fully operational | Rely on application logs |
| **DNS (Cloudflare/registrar)** | Critical | Domain unreachable | Secondary DNS provider |
| **TLS certificates** | Critical | Browser security warnings | Auto-renewal monitoring, manual renewal fallback |

### 3.3 Single Points of Failure

| Component | SPOF Risk | Mitigation |
|-----------|-----------|------------|
| PostgreSQL instance | Database is single instance | Managed provider handles replication; point-in-time recovery enabled |
| Render deployment | Single container | Auto-restart on crash; manual redeploy from Git |
| JWT secret key | Loss prevents all authentication | Documented in secrets management; rotation procedure defined |
| DNS | Registrar failure | Monitor expiry; auto-renew enabled |

---

## 4. Backup Strategy

### 4.1 Database Backups

| Parameter | Value |
|-----------|-------|
| Database | PostgreSQL (managed) |
| Backup type | Automated daily snapshots + continuous WAL archiving |
| Backup frequency | Daily full backup + continuous WAL (point-in-time recovery) |
| Retention | 7 daily snapshots + 4 weekly snapshots (28-day window) |
| Encryption | AES-256 at rest (managed provider) |
| Storage location | Provider-managed, same region (US) |
| Cross-region replication | Planned (see Section 4.4) |

### 4.2 What Is Backed Up

| Data Category | Backed Up | Rationale |
|---------------|-----------|-----------|
| User accounts and credentials (hashed) | ✅ Yes | Required for authentication |
| Client metadata | ✅ Yes | Required for client organization |
| Activity logs (aggregate summaries) | ✅ Yes | Workflow tracking |
| Diagnostic summaries (aggregate metadata) | ✅ Yes | Engagement history |
| Engagement records | ✅ Yes | Workspace state |
| Billing events and subscriptions | ✅ Yes | Financial records |
| Follow-up items | ✅ Yes | Engagement narratives |
| Application configuration | ✅ Yes | Settings and preferences |
| **Trial balance data** | ❌ No | Zero-Storage (never persisted) |
| **Uploaded files** | ❌ No | Zero-Storage (never persisted) |

### 4.3 Application Code and Configuration

| Asset | Backup Method | Location |
|-------|---------------|----------|
| Application source code | Git (GitHub) | GitHub cloud + local clones |
| Infrastructure configuration | Git (documented in repo) | GitHub |
| Environment variables / secrets | Platform secret managers (Render, Vercel) | Provider-managed |
| Alembic migrations | Git (versioned) | GitHub |

### 4.4 Planned Improvements

| Improvement | Target Date | Status |
|-------------|-------------|--------|
| Cross-region database replication | Q3 2026 | Planned |
| Automated backup restore testing in CI | Q3 2026 | Planned |
| Secrets backup to secondary vault | Q4 2026 | Planned |

---

## 5. Disaster Recovery Procedures

### 5.1 Database Recovery

**Scenario:** PostgreSQL database is corrupted or unavailable.

| Step | Action | Owner | Estimated Time |
|------|--------|-------|----------------|
| 1 | Declare incident per [Incident Response Plan](./INCIDENT_RESPONSE_PLAN.md) | IC | 5 minutes |
| 2 | Assess database status via provider dashboard | Technical Lead | 15 minutes |
| 3 | If provider issue: contact provider support, monitor status | IC | Ongoing |
| 4 | If data corruption: initiate point-in-time recovery to pre-corruption timestamp | Technical Lead | 30–60 minutes |
| 5 | If full instance loss: restore from latest daily snapshot | Technical Lead | 60–120 minutes |
| 6 | Verify data integrity (user count, client count, engagement count) | Technical Lead | 30 minutes |
| 7 | Update application connection string if instance changed | Technical Lead | 15 minutes |
| 8 | Verify application health | IC | 15 minutes |
| 9 | Run `alembic upgrade head` if schema version mismatch | Technical Lead | 10 minutes |

### 5.2 Backend API Recovery

**Scenario:** Render backend service is unavailable.

| Step | Action | Owner | Estimated Time |
|------|--------|-------|----------------|
| 1 | Check Render status page for platform-wide issues | Technical Lead | 5 minutes |
| 2 | Attempt manual redeploy from latest Git commit | Technical Lead | 10 minutes |
| 3 | If Render platform issue: wait for provider resolution | IC | Provider-dependent |
| 4 | If prolonged outage (>2 hours): prepare deployment to backup provider | Technical Lead | 2–4 hours |
| 5 | Update DNS to point to backup deployment | Technical Lead | 15 minutes + propagation |
| 6 | Verify service health and authentication flow | IC | 30 minutes |

### 5.3 Frontend Recovery

**Scenario:** Vercel frontend is unavailable.

| Step | Action | Owner | Estimated Time |
|------|--------|-------|----------------|
| 1 | Check Vercel status page | Technical Lead | 5 minutes |
| 2 | Trigger manual redeployment | Technical Lead | 5 minutes |
| 3 | If Vercel outage: deploy to secondary CDN (e.g., Cloudflare Pages) | Technical Lead | 30–60 minutes |
| 4 | Update DNS if needed | Technical Lead | 15 minutes + propagation |

### 5.4 DNS/TLS Recovery

**Scenario:** Domain unreachable or TLS certificate expired.

| Step | Action | Owner | Estimated Time |
|------|--------|-------|----------------|
| 1 | Verify DNS resolution (`dig paciolus.com`) | Technical Lead | 5 minutes |
| 2 | If DNS registrar issue: contact registrar, use secondary DNS if available | IC | Provider-dependent |
| 3 | If TLS expired: trigger manual renewal via provider (Vercel/Render auto-renew) | Technical Lead | 15 minutes |
| 4 | If Let's Encrypt outage: obtain certificate from alternative CA | Technical Lead | 1–2 hours |

### 5.5 Complete Infrastructure Loss

**Scenario:** Catastrophic failure of primary hosting region.

| Step | Action | Owner | Estimated Time |
|------|--------|-------|----------------|
| 1 | Declare P0 incident | IC | Immediately |
| 2 | Spin up new PostgreSQL instance in secondary region | Technical Lead | 30 minutes |
| 3 | Restore database from most recent backup | Technical Lead | 60–120 minutes |
| 4 | Deploy backend to secondary provider | Technical Lead | 60 minutes |
| 5 | Deploy frontend to secondary CDN | Technical Lead | 30 minutes |
| 6 | Update DNS records | Technical Lead | 15 minutes + propagation |
| 7 | Verify all services operational | IC | 30 minutes |
| **Total estimated recovery time** | | | **4–6 hours** |

---

## 6. Business Continuity Procedures

### 6.1 Degraded Operation Modes

| Mode | Trigger | Available Features | Disabled Features |
|------|---------|--------------------|--------------------|
| **Full operation** | Normal | All features | None |
| **Billing degraded** | Stripe outage | Analysis, exports, client management | New subscriptions, billing changes |
| **Email degraded** | SendGrid outage | All except email-dependent flows | Email verification, password reset |
| **Read-only mode** | Database write failure | View existing data, run analyses | Create/update clients, engagements, settings |
| **Static mode** | API completely down | Frontend loads (cached), marketing pages | All authenticated features |

### 6.2 Customer Communication During Outage

| Duration | Action |
|----------|--------|
| <15 minutes | Status page update only |
| 15–60 minutes | Status page + in-app banner (if frontend available) |
| >1 hour | Status page + email notification to active users |
| >4 hours | Status page + email + social media update |

### 6.3 Data Integrity Verification After Recovery

After any recovery operation, verify:

- [ ] User authentication functional (login, token refresh)
- [ ] Client count matches pre-incident records
- [ ] Engagement records intact
- [ ] Billing subscription states match Stripe (source of truth)
- [ ] Activity logs not truncated beyond RPO window
- [ ] Alembic migration version correct
- [ ] No Zero-Storage violation (no financial data in backups or restored data)

---

## 7. Testing and Validation

### 7.1 Test Schedule

| Test Type | Frequency | Scope | Documentation |
|-----------|-----------|-------|---------------|
| **Backup restore test** | Semi-annual | Full database restore to isolated instance | Test report with duration, data integrity check |
| **Failover simulation** | Annual | Backend redeploy to secondary provider | Failover report with RTO measurement |
| **Tabletop exercise** | Semi-annual | Walk through complete infrastructure loss scenario | Exercise report with identified gaps |
| **DNS recovery test** | Annual | Verify secondary DNS activation procedure | Test report |
| **Backup integrity check** | Monthly | Verify backup exists and is not corrupted (checksums) | Automated check with alert on failure |

### 7.2 Backup Restore Test Procedure

| Step | Action | Success Criteria |
|------|--------|-----------------|
| 1 | Provision isolated PostgreSQL instance (not production) | Instance running |
| 2 | Restore latest backup to isolated instance | Restore completes without errors |
| 3 | Run `alembic upgrade head` | No migration errors |
| 4 | Verify table counts (users, clients, engagements, activity_logs) | Counts match production (±backup window) |
| 5 | Verify sample data integrity (spot-check 10 user records) | Data matches expectations |
| 6 | Measure restore duration | Within RTO target (2 hours) |
| 7 | Document results in test report | Report filed |
| 8 | Tear down isolated instance | Instance removed |

### 7.3 Test Reporting

Each test must produce a report containing:
- Test date and participants
- Procedure followed
- Duration measured vs. target
- Data integrity verification results
- Issues discovered
- Remediation actions (if any)
- Sign-off by CTO

Reports stored in `docs/08-internal/dr-test-YYYYMMDD.md`.

---

## 8. Roles and Responsibilities

| Role | Responsibilities |
|------|-----------------|
| **CTO** | Plan owner; approves RTO/RPO targets; reviews test results |
| **CISO** | Ensures DR procedures align with security policy; coordinates breach-related DR |
| **Senior Engineer (on-call)** | Executes recovery procedures; performs backup restore tests |
| **DevOps/SRE** | Maintains backup configuration; monitors backup integrity; manages infrastructure |
| **Product Lead** | Coordinates customer communication during extended outages |

---

## 9. Contact

| Role | Contact | Availability |
|------|---------|-------------|
| CTO | cto@paciolus.com | Business hours + P0 escalation |
| CISO | security@paciolus.com | Business hours + P0 escalation |
| On-call engineer | PagerDuty rotation | 24/7 |
| Render support | Render dashboard | 24/7 |
| Stripe support | Stripe dashboard | 24/7 |

---

## Related Documents

| Document | Relationship |
|----------|-------------|
| [Incident Response Plan](./INCIDENT_RESPONSE_PLAN.md) | Incident declaration and escalation procedures |
| [Security Policy](./SECURITY_POLICY.md) | Section 4 (infrastructure security), Section 6 (incident response) |
| [Zero-Storage Architecture](./ZERO_STORAGE_ARCHITECTURE.md) | Data classification and retention (informs backup scope) |
| [Audit Logging and Evidence Retention](./AUDIT_LOGGING_AND_EVIDENCE_RETENTION.md) | Log retention during and after recovery |

---

**Document Version History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-26 | CTO | Initial publication: RTO/RPO targets, dependency map, backup strategy, 5 recovery procedures, degraded operation modes, testing schedule |

---

*Paciolus — Zero-Storage Trial Balance Diagnostic Intelligence*
