# Audit Logging and Evidence Retention

**Version:** 2.0 · **Effective:** 2026-10-24 · **Owner:** security@paciolus.com · **Classification:** Public

Version 1.1 said authentication events were kept in the database for 365 days (they were held in an
in-memory list and lost on every restart) and described a tamper-evident hash chain that could not
verify once two users' activity interleaved. Both were fixed in Sprints 840 and 845; this version
describes the result. The previous text is in
[`archive/AUDIT_LOGGING_AND_EVIDENCE_RETENTION_pre-sprint-845_2026-10-24.md`](archive/AUDIT_LOGGING_AND_EVIDENCE_RETENTION_pre-sprint-845_2026-10-24.md).

## What is logged, and for how long

| Log | Contents | Where | Retention |
|-----|----------|-------|-----------|
| **Security events** | Failed logins, lockouts, IP blocks, refresh-token reuse, session revocation, password change/reset, email change, impersonation, account erasure and data export. User ID and a hash of the client IP — never the raw IP, never file contents. | `security_events` table | 365 days, then deleted |
| **Activity history** | One row per analysis: timestamp, row count, totals, materiality, balanced flag, anomaly counts, first characters of the filename and its hash | `activity_logs` table | Archived after 365 days |
| **Admin audit log** | Every platform-administrator action on a customer account (plan changes, credits, refunds, impersonation start/end, session revocation, account erasure) | `admin_audit_logs` table | Kept; deletion is blocked in code |
| **Application logs** | Requests and errors; exception type names only, tracebacks stripped in production; no uploaded file contents or filenames | Render log stream (and Grafana Cloud Loki if enabled) | Per the provider's log retention |
| **Error reports** | Error type and stack location; no request bodies, local variables, exception messages or breadcrumbs | Sentry | Per the Sentry plan |

## Tamper evidence

Each `activity_logs` row carries an HMAC-SHA512 `chain_hash` over its contents and the previous row
**of the same user**, keyed with `AUDIT_CHAIN_SECRET_KEY`. A user can verify their own range at
`GET /audit/chain-verify`. Archived rows stay in the chain. Rows written before chaining existed
(Sprint 461) have no hash; verification reports how many it could not check rather than skipping them
silently. Rows chained under the earlier cross-user rule still verify. The chain detects edits to stored
rows by anyone without the key; it does not prove completeness and is not an external timestamp.

## Immutability and deletion

Activity logs, diagnostic summaries, tool runs, follow-up items and comments, and the admin audit log
cannot be deleted by ordinary code paths — the ORM refuses, and a CI guard rejects new hard-delete code.
"Clear history" and "delete engagement" archive rather than delete. The one exception is **account
erasure** (Settings → Profile → Your Data, or a request to privacy@paciolus.com): it physically removes
the user's own records, and records that it happened in the security log.
