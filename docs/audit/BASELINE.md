# Paciolus — Audit Baseline

> **Purpose:** This document is the single source of truth for any read-only
> auditor operating on the Paciolus repository. Read this file in full before
> beginning any audit pass. It tells you what Paciolus is, what has already been
> audited, what has been resolved, and what has been accepted as a known risk or
> intentional decision. Do not re-flag items listed here unless you find evidence
> that a resolved item has regressed.

---

## 1. Product Identity

Paciolus is a zero-storage audit intelligence platform for CPAs and accounting
firms. Users upload CSV or Excel trial balance files and receive automated
diagnostics, anomaly detection, and suggested audit procedures. The platform's
core architectural invariant is **zero-storage**: uploaded financial data is
processed entirely in-memory and is never persisted to disk, database, logs,
telemetry, caches, or any other durable medium. Only non-financial metadata
(user accounts, subscription state, upload timestamps, aggregate usage metrics)
is persisted.

**Zero-storage boundary clarification:** The invariant protects *raw financial
data* — individual account names, balances, transaction details, and any content
that could identify a client's financial position. *Derived aggregates* (e.g.,
total debits/credits, materiality thresholds, category ratios) are classified as
operational metadata and may be persisted in the database for history/UX
purposes. These aggregates cannot be reverse-engineered to reconstruct the
original trial balance. However, **no financial data — raw or derived — may be
stored in browser storage** (localStorage, sessionStorage, IndexedDB). Browser
storage is untrusted and outside the platform's security perimeter.

---

## 2. Architecture Snapshot

| Layer        | Technology                                                    |
|--------------|---------------------------------------------------------------|
| Backend      | FastAPI (Python 3.11+), Gunicorn                              |
| Frontend     | Next.js 16, React 18, TypeScript                              |
| Database     | PostgreSQL                                                    |
| Payments     | Stripe (webhooks, subscription lifecycle, seat management)    |
| Auth         | JWT access tokens + refresh cookie, bcrypt passwords,         |
|              | stateless HMAC CSRF, account lockout, email verification      |
| Infra        | Docker, GitHub Actions CI/CD                                  |
| Scheduling   | APScheduler (runs inside Gunicorn workers)                    |

### Key Architectural Decisions

- **Stateless CSRF via HMAC** — Replaced earlier in-memory CSRF token storage
  that broke across Gunicorn workers. The current implementation is stateless
  and database-backed for sessions. This was a major production bug that has
  been fully resolved.
- **Database-backed sessions** — Sessions moved from in-memory to PostgreSQL
  to survive worker restarts and multi-worker deployments.
- **Upload-based quota enforcement** — Billing tiers gate access by upload
  count per billing period, not by compute time or report count.

---

## 3. Pricing Tiers

| Tier         | Price/mo | Upload Quota | Seats | Notable Features                       |
|--------------|----------|--------------|-------|----------------------------------------|
| Free         | $0       | 10           | 1     | TB diagnostics + flux analysis only    |
| Solo         | $100     | 100          | 1     | All tools, exports                     |
| Professional | $500     | 500          | 7     | + export sharing, audit logs, admin    |
| Enterprise   | $1,000   | Unlimited    | 20    | + bulk upload, custom PDF branding     |

---

## 4. Diagnostic Suite

The platform includes 21 diagnostic reports (RPT-01 through RPT-21) plus a
summary dashboard (DASH-01). The full suite covers: trial balance analysis,
journal entry testing, AP/payroll/revenue/AR aging, fixed assets, inventory,
bank reconciliation, three-way match, and multi-period comparison.

A **Synthetic Anomaly Testing Framework** exists to inject known financial
anomalies into trial balance data for validation of detection logic.

---

## 5. Completed Audit History

The following audits have been executed. Their findings have been processed
into remediation prompts and worked through. Do not re-audit these areas from
scratch — instead, verify that resolutions hold and flag any regressions.

| Audit ID  | Scope                                    | Status    |
|-----------|------------------------------------------|-----------|
| AUDIT-02  | Authentication & session integrity       | Completed |
| AUDIT-03  | Browser storage violations (zero-storage)| Completed |
| AUDIT-04  | CI/CD pipeline security                  | Completed |
| AUDIT-05  | Error handling & information leakage     | Completed |
| AUDIT-06  | Business logic & computational integrity | Prompted  |
| AUDIT-07  | Rate limiting & abuse prevention         | Prompted  |
| AUDIT-08  | Multi-tenant isolation correctness       | Prompted  |
| AUDIT-09  | License compliance                       | Prompted  |
| AUDIT-10  | Disaster recovery validation             | Prompted  |
| —         | Marketing copy & trust language audit    | Completed |
| —         | Billing security & correctness review    | Completed |
| —         | Code quality / structural debt review    | Completed |
| FULL-SWEEP| Full sweep (2026-03-26)                  | Completed |

### Open Findings From Full Sweep (2026-03-26)

These findings are confirmed and queued for remediation. Do not re-flag them;
verify their resolution status on the next sweep.

| Finding | Severity | Summary                                              | Status     |
|---------|----------|------------------------------------------------------|------------|
| F-001   | HIGH     | sessionStorage fallback stores derived financial data | REMEDIATE  |
| F-002   | MEDIUM   | `/auth/refresh` CSRF-exempt despite cookie auth      | REMEDIATE  |
| F-003   | MEDIUM   | Stripe `items[0]` positional assumption in sync path | REMEDIATE  |
| F-004   | MEDIUM   | Float conversion in monetary API/model helpers       | REMEDIATE  |

Note: F-001's database persistence component (total_debits, total_credits,
materiality_threshold in ActivityLog/DiagnosticSummary) was reviewed and
accepted as operational metadata — see § 8. Only the browser sessionStorage
fallback portion requires remediation.

**"Completed"** = audit ran, findings generated, remediation prompts executed.
**"Prompted"** = audit prompt was written and delivered but execution status in
Codex is unconfirmed. Treat these areas as partially covered — verify findings
if the reports exist in `reports/`, otherwise treat as unaudited.

---

## 6. Resolved Issues — Do Not Re-Flag

The following issues have been identified, remediated, and verified. Only
re-flag these if you find concrete evidence of regression (not just theoretical
risk that the fix *could* break).

### Infrastructure & Auth
- **In-memory state across Gunicorn workers** — Fixed. Sessions are now
  database-backed. CSRF is stateless HMAC. Do not flag in-memory session
  storage as a finding.
- **CSRF/refresh cookie coupling** — Audited in AUDIT-02. The lifecycle is
  intentional: HMAC CSRF tokens are tied to the session, refresh cookies are
  HttpOnly/Secure/SameSite=Strict.

### Marketing & Copy
- **Performance claim drift** ("< 2s" vs "under 3 seconds" vs "under three
  seconds") — Identified and queued for copy consolidation. Do not re-flag
  the existence of the drift; flag only if new contradictory claims appear.
- **Domain inconsistency** (`@paciolus.io` vs `@paciolus.com`) — Identified.
  Do not re-flag unless it has spread to new locations.
- **Response SLA wording drift** ("one business day" vs "1–2 business days")
  — Identified.

### Billing
- **Cross-tenant data leakage in billing analytics** — The
  `GET /billing/analytics/weekly-review` endpoint was globally scoped.
  Remediation prompt issued to scope by org_id. Verify the fix is in place;
  do not re-discover the finding.

---

## 7. Known Systemic Bugs — Verify Status

These bugs were identified during the RPT-01–RPT-21 diagnostic review cycle.
Remediation prompts were generated. Their resolution status should be verified
on each full sweep — report as RESOLVED, PARTIAL, or STILL PRESENT with
file paths and evidence.

| Bug                                | Summary                                                       |
|------------------------------------|---------------------------------------------------------------|
| Suggested procedures rotation      | Procedures not rotating across repeated runs on same input    |
| Hardcoded risk tier labels         | Labels not driven by computed data                            |
| PDF cell overflow                  | Long text escaping cell boundaries in generated reports       |
| Orphaned ASC 250-10 references     | Standard references in output without corresponding logic     |
| PP&E ampersand escaping            | `&` in account names not escaped in PDF/HTML output           |
| Identical data quality scores      | Multiple accounts receiving same score despite different data  |
| Empty drill-down stubs            | Drill-down actions returning empty results                    |
| Dashboard vs PDF risk score divergence | Dashboard showing 14/High while PDF shows 100/100/HIGH RISK |
| Identical procedure language       | All findings receiving word-for-word same suggested procedures|

---

## 8. Accepted Risks & Intentional Decisions

Do not flag these as findings. They are conscious architectural or business
decisions.

- **APScheduler running inside Gunicorn workers** — Known limitation. A
  dedicated scheduler process is the long-term fix but is not prioritized
  pre-launch. Flag only if you find a concrete bug caused by this (e.g.,
  duplicate job execution), not the architectural choice itself.
- **Aggregate metadata storage** — The zero-storage invariant applies to
  financial data. Non-financial metadata (timestamps, upload counts, user
  profiles, subscription state) is intentionally persisted. Do not flag
  metadata persistence as a zero-storage violation.
- **Derived financial aggregates in database** — Summary statistics
  (total_debits, total_credits, materiality_threshold, category ratios) in
  `ActivityLog` and `DiagnosticSummary` tables are classified as operational
  metadata. They cannot reconstruct the original trial balance and are
  retained for history UX. Do not flag these as zero-storage violations.
  **However**, any derived financial data in browser storage (sessionStorage,
  localStorage, IndexedDB) IS a violation and should be flagged — browser
  storage is outside the security perimeter.
- **Solo founder operation** — There is no team. Do not recommend "assign to
  a team member" or "establish a review committee." All recommendations must
  be actionable by a single developer.
- **Pre-launch state** — The product has zero paying customers. Findings
  should be prioritized by "would this cause harm or liability when customers
  arrive" rather than "is this not enterprise-grade today."

---

## 9. Report Output Conventions

All audit output goes to the `reports/` directory. Use the naming convention:

```
reports/AUDIT-<TYPE>-<YYYY-MM-DD>.md
```

Examples:
- `reports/AUDIT-FULL-SWEEP-2026-03-26.md`
- `reports/AUDIT-DELTA-2026-03-26.md`
- `reports/AUDIT-PROBE-BILLING-2026-03-26.md`

Each finding must include:
1. File path and line number(s)
2. Description of the issue
3. Severity: CRITICAL / HIGH / MEDIUM / LOW
4. Category: Security | Zero-Storage | Correctness | Architecture |
   Performance | Billing | DX | Types/Contracts | CI/CD | Infra
5. Impact statement
6. Recommended remediation (prose — do not implement)
7. Repair prompt stub (copy/paste-ready for Claude Code)

### Repair Prompt Format

For CRITICAL/HIGH findings, include a detailed repair prompt:

```
[REPAIR PROMPT — <SEVERITY>]
Goal: <one sentence>
Files in scope: <explicit list>
Constraints:
  - Preserve external behavior unless explicitly stated
  - Maintain zero-storage invariant
  - Keep OpenAPI/TS types synchronized if APIs change
  - Add or adjust tests to prove the fix
Plan:
  1. <step with file/function references>
  2. <step>
  3. <step>
Acceptance criteria:
  - <concrete, testable statement>
```

For MEDIUM/LOW findings, a brief recommendation is sufficient:

```
[REPAIR PROMPT — <SEVERITY>]
Goal: <one sentence>
Files: <list>
Action: <1-2 sentence description>
```
