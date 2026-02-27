# Encryption at Rest Verification

**Document:** Monthly Verification Record
**Period:** February 2026
**SOC 2 Criteria:** CC7.2 / S1.2
**Verification Frequency:** Monthly
**Completed By:** _[CEO/CISO — see ACTION REQUIRED sections below]_
**Date Completed:** _[YYYY-MM-DD]_

---

## Purpose

This document records the monthly verification that encryption at rest is enabled on all Paciolus managed storage providers. The SECURITY_POLICY.md §2.2 asserts AES-256 provider-level encryption for all persisted data. This record provides the SOC 2 audit evidence that the assertion has been actively verified, not merely assumed.

---

## Provider 1 — Render (PostgreSQL)

**Role:** Primary application database (user accounts, client metadata, engagement records, subscriptions, activity logs, tool runs, diagnostic summaries)
**Encryption expected:** AES-256 at rest (Render managed database standard)

### Verification Steps

1. Log into Render dashboard → `https://dashboard.render.com`
2. Navigate to **PostgreSQL** instance for Paciolus production
3. Open instance settings / info panel
4. Confirm "Encryption at Rest" or equivalent field is enabled
5. Screenshot the confirmation and save to `docs/08-internal/soc2-evidence/cc7/render-postgres-encryption-202602.png`

### Evidence

| Field | Value |
|-------|-------|
| Provider | Render |
| Service type | Managed PostgreSQL |
| Setting name | _[Screenshot: paste exact field name from dashboard]_ |
| Setting value | _[Enabled / AES-256 / or equivalent]_ |
| Screenshot file | `soc2-evidence/cc7/render-postgres-encryption-202602.png` |
| Verified by | _[Name]_ |
| Verification date | _[YYYY-MM-DD]_ |

> **CEO ACTION REQUIRED:** Log into Render dashboard, locate the encryption-at-rest setting on the PostgreSQL instance, take a screenshot, save it as `docs/08-internal/soc2-evidence/cc7/render-postgres-encryption-202602.png`, and fill in the table above.

---

## Provider 2 — Vercel (Frontend Hosting)

**Role:** Next.js frontend static/SSR delivery
**Persistent storage configured:** None — Paciolus uses Vercel exclusively for compute (SSR) and CDN delivery. No Vercel KV, Vercel Blob, Vercel Postgres, or Edge Config is provisioned. All application data resides exclusively on Render PostgreSQL.

### Verification Steps

1. Log into Vercel dashboard → `https://vercel.com/dashboard`
2. Navigate to the Paciolus project
3. Confirm no Storage integrations are connected (Settings → Storage)
4. Screenshot the empty Storage tab as evidence of no persistent data
5. Save to `docs/08-internal/soc2-evidence/cc7/vercel-no-storage-202602.png`

### Evidence

| Field | Value |
|-------|-------|
| Provider | Vercel |
| Persistent storage provisioned | _[None / confirm in dashboard]_ |
| Screenshot file | `soc2-evidence/cc7/vercel-no-storage-202602.png` |
| Verified by | _[Name]_ |
| Verification date | _[YYYY-MM-DD]_ |

> **CEO ACTION REQUIRED:** Log into Vercel dashboard, navigate to the Paciolus project → Settings → Storage, confirm no storage is attached, screenshot the empty state, and save as `docs/08-internal/soc2-evidence/cc7/vercel-no-storage-202602.png`.

---

## Summary

| Provider | Data Stored | Encryption at Rest | Verified |
|----------|-------------|-------------------|---------|
| Render PostgreSQL | User accounts, client metadata, engagement records, subscriptions, activity logs, tool runs | AES-256 (managed) | _[ ] Pending CEO verification_ |
| Vercel | No persistent data | N/A | _[ ] Pending CEO verification_ |

**Overall Status:** _Pending CEO sign-off_

---

## Next Verification

**Due:** 2026-03-27 (monthly)
**Reminder:** Add a recurring calendar event: "Paciolus — Monthly Encryption at Rest Verification" → first of each month → complete and file to `docs/08-internal/` as `encryption-at-rest-verification-YYYYMM.md`

> **CEO ACTION REQUIRED:** Set a recurring monthly calendar reminder for this verification task.

---

## Template for Subsequent Months

Copy this file, rename to `encryption-at-rest-verification-YYYYMM.md`, update the period and date fields, take fresh screenshots, and update the Summary table.
