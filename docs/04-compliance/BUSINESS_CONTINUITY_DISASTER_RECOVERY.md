# Business Continuity and Disaster Recovery

**Version:** 2.0 · **Effective:** 2026-10-24 · **Owner:** security@paciolus.com · **Classification:** Public

Version 1.2 promised a 99.9% SLA, daily backups with 28-day retention, a 1-hour recovery point and
2-hour recovery time, and tested restores. **None of those were true:** the backup workflows queried a
database that had moved to another provider, and no restore had ever been tested. This version states
the position plainly. The previous text is in
[`archive/BUSINESS_CONTINUITY_DISASTER_RECOVERY_pre-sprint-845_2026-10-24.md`](archive/BUSINESS_CONTINUITY_DISASTER_RECOVERY_pre-sprint-845_2026-10-24.md).

## No uptime or recovery commitment

Paciolus makes **no uptime SLA and no recovery-time or recovery-point commitment**. We aim to keep the
service available and to restore it quickly, and we will tell customers what happened if it is not.

## What protects the data today

- **Database:** Neon PostgreSQL with Neon's point-in-time recovery. The recovery window is the one
  included in the current Neon plan; the exact figure is being confirmed.
- **Uploaded files:** not kept, so there is nothing to back up or lose.
- **Shared report files (R2):** short-lived by design (24–48 hours); not backed up.
- **Code and configuration:** in GitHub; the backend and frontend can be redeployed from it.

## What does not exist yet

- **An independent, off-provider backup.** A scheduled `pg_dump` to Cloudflare R2 (`paciolus-backups`)
  is planned and the bucket is provisioned, but nothing writes to it yet (Sprint 778b).
- **A tested restore.** No restore from Neon PITR or from any backup has been performed. Until one has,
  recovery is unproven.
- The monthly DR and backup-integrity workflows report **UNVERIFIED** rather than pass until both exist.

## If a provider fails

| Failure | Effect | Response |
|---------|--------|----------|
| Render (backend) | App unavailable | Wait for Render, or redeploy the container elsewhere from GitHub. |
| Neon (database) | App unavailable; data at Neon's risk | Neon PITR restore; independent backup once built. |
| Render Key Value (rate limiting) | Rate limits fall back to per-process memory | Automatic (degraded mode). |
| Cloudflare R2 | Share links fail | Users download reports directly instead. |
| Vercel (frontend) | Site unavailable | Wait for Vercel or redeploy elsewhere. |
| Stripe / SendGrid | Checkout or email fails | Wait for the provider. |
