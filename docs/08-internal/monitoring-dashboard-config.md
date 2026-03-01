# Monitoring Dashboard Configuration

> **Sprint:** 462 | **Controls:** S3.3 / CC4.2 | **Date:** 2026-03-01

## Overview

This document records the configuration of all monitoring and alerting systems. Evidence artifacts (screenshots, config exports) should be filed quarterly to `docs/08-internal/soc2-evidence/s3/`.

---

## 1. Sentry APM

| Setting | Value |
|---------|-------|
| **Project** | Paciolus |
| **DSN** | `[REDACTED — stored in SENTRY_DSN env var]` |
| **SDK** | `sentry-sdk 2.53.0` (backend), `@sentry/nextjs 10.40.0` (frontend) |
| **Traces Sample Rate** | 0.1 (10% of requests) |
| **PII Scrubbing** | `before_send` hook strips request bodies (Zero-Storage compliance) |
| **Environment** | `production` / `staging` |

### Alert Rules

| Alert | Condition | Action |
|-------|-----------|--------|
| Error rate spike | > 5% of requests in 5-min window | Email notification to team |
| Login failure surge | > 100 failed logins / 5 min | Email + escalation |
| Unhandled exception | Any unhandled exception | Sentry issue created |

### Team Access
- **CEO ACTION:** Export team member list from Sentry → Settings → Teams and file to `soc2-evidence/s3/sentry-team-access-YYYYMM.png`

---

## 2. Prometheus Metrics

| Setting | Value |
|---------|-------|
| **Endpoint** | `/metrics` (backend) |
| **Library** | `prometheus_client 0.22.0` |
| **Scrape interval** | Platform-dependent (Render metrics or external scraper) |

### Counters

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `paciolus_file_upload_total` | File uploads by format | N/A (informational) |
| `paciolus_billing_redirect_injection_attempt_total` | Checkout redirect tampering | > 0 = investigate |
| `paciolus_billing_event_total` | Billing events by type | N/A (analytics) |
| `paciolus_csrf_token_misuse_total` | CSRF validation failures | > 10/min = investigate |

### TOML Alert Thresholds
Defined in `backend/alert_thresholds.toml`:
- File upload error rate
- Parse failure rate by format
- ODS processing time

---

## 3. On-Call Rotation

| Role | Contact | Escalation |
|------|---------|------------|
| Primary | CEO (until team grows) | N/A |
| Escalation | N/A | N/A |

**Acknowledgment SLA:** Per IRP §3.3:
- P0: 15 min
- P1: 1 hour
- P2: 4 hours
- P3: Next business day

**CEO ACTION:** Configure PagerDuty/OpsGenie when team size > 1. Update this table with actual rotation.

---

## 4. Evidence Collection Schedule

| Artifact | Frequency | Location |
|----------|-----------|----------|
| Sentry config export | Quarterly | `soc2-evidence/s3/sentry-config-YYYYMM.json` |
| Prometheus config | Quarterly | `soc2-evidence/s3/prometheus-config-YYYYMM.yaml` |
| Alert delivery test | Quarterly | `soc2-evidence/s3/alert-test-YYYYMM.md` |
| Team access list | Quarterly | `soc2-evidence/s3/sentry-team-access-YYYYMM.png` |

---

## 5. CI Status Badges

| Workflow | Status |
|----------|--------|
| Backend Tests | See `.github/workflows/ci.yml` |
| Frontend Build | See `.github/workflows/ci.yml` |
| Backup Integrity | See `.github/workflows/backup-integrity-check.yml` |
| DR Test (Monthly) | See `.github/workflows/dr-test-monthly.yml` (Sprint 465) |

---

*Last updated: 2026-03-01 — Sprint 462*
