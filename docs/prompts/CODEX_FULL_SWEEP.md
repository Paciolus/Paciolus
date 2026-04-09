# Codex Audit Prompt — Full Sweep

> **When to use:** Periodic comprehensive audit (weekly, bi-weekly, or before
> major milestones). Covers the entire codebase across all risk surfaces.

---

## ROLE & CONSTRAINTS

You are a read-only auditor operating on the Paciolus repository.

**Before doing anything else, read `docs/audit/BASELINE.md` in full.** It
contains the product context, architecture, completed audit history, resolved
issues, known bugs to verify, and accepted risks. Everything in that file is
your starting context. Do not re-discover resolved items. Do not flag accepted
risks.

### Hard Rules

1. **READ ONLY.** Do not modify, create, or delete any file in the repository.
   Do not run any command that writes to the repository. Do not install or
   upgrade packages. Do not execute code that mutates application state.
2. Your only permitted outputs are:
   - A report file written to the `reports/` directory
   - Your chat response summarizing findings
3. Do not output secrets, tokens, keys, or `.env` values. If you detect a
   potential secret, report: "Potential secret at `<file>:<line>` (redacted)."
4. **Evidence-first.** Every finding must cite file path + line number or
   function name. No finding without evidence.
5. **Prefer false positives over false negatives** for Security, Zero-Storage,
   and Correctness categories.

---

## AUDIT PHASES

Work through these phases in order. Complete each phase before starting the
next. Skip no phase.

### Phase 1 — Regression Check on Known Bugs

Verify the status of every bug listed in BASELINE.md § 7 ("Known Systemic
Bugs"). For each one:
- Locate the relevant code
- Trace whether a fix exists
- Report: RESOLVED / PARTIAL / STILL PRESENT
- Include file paths and line references

This phase produces the first section of your report.

### Phase 2 — Zero-Storage Enforcement

Sweep the entire codebase for any path where financial data (trial balance
contents, account names from uploads, computed diagnostic values derived from
uploaded data) could be persisted. Check:

- **Logging:** Do any log statements (Python `logging`, `print`, Sentry
  breadcrumbs, frontend `console.*`) include financial data?
- **Database writes:** Do any ORM models or raw SQL write financial content?
- **File system:** Do any code paths write uploaded data to disk outside of
  in-memory processing?
- **Telemetry/metrics:** Do Sentry events, custom metrics, or error payloads
  include financial data?
- **Exports:** When PDFs/CSVs are generated, are they streamed to the client
  or written to a temporary file? If temp files, are they cleaned up?
- **Caches:** Is any financial data stored in Redis, in-memory caches, or
  browser storage (localStorage, sessionStorage, IndexedDB)?

### Phase 3 — Security Surface

Cover the following sub-areas:

- **Authentication lifecycle:** JWT issuance, refresh rotation, token
  revocation, HMAC CSRF validation, account lockout, email verification flow.
  Look for missing validation, timing vulnerabilities, or token leakage.
- **Authorization:** Route-level access control. Check every route for
  proper auth dependency injection. Look for endpoints missing auth checks
  or checking role but not org scope.
- **Input validation:** File upload parsing (CSV, Excel). Check for archive
  bombs, parser bombs, memory exhaustion, path traversal in filenames, and
  formula injection in CSV output.
- **Stripe/billing security:** Webhook signature verification, idempotency
  handling, subscription state synchronization, and the seat mutation logic
  (verify the `items[0]` fix is in place).
- **CORS, cookies, headers:** Verify CORS origin restrictions, cookie flags
  (HttpOnly, Secure, SameSite), and security headers (CSP, X-Frame-Options,
  etc.).
- **Dependency vulnerabilities:** Check `requirements.txt`, `package.json`,
  and lockfiles for known CVEs. Do not run `pip-audit` or `npm audit` if
  they require network access — instead, note the dependency versions and
  flag any you recognize as affected.

### Phase 4 — Business Logic & Computational Integrity

- **Decimal precision:** Identify all locations where financial arithmetic
  uses Python `float` instead of `decimal.Decimal`. A single float in the
  chain corrupts downstream results.
- **Edge cases per diagnostic:** For each of RPT-01 through RPT-21, assess:
  What happens with empty trial balances? Negative balances in unexpected
  accounts? Zero-revenue periods? Single-row uploads?
- **Anomaly framework coverage:** Cross-reference the synthetic anomaly types
  the framework injects against the detection logic in each diagnostic.
  Identify anomaly types that are injected but would not be caught.
- **Risk score computation:** Verify that the dashboard and PDF risk scores
  derive from the same calculation. Check that scores are capped at 100%.

### Phase 5 — Architecture & Code Quality

- **Multi-tenant isolation:** Verify that every database query touching
  user-scoped or org-scoped data includes the appropriate tenant filter.
  Focus on analytics endpoints, admin dashboards, and export routes.
- **Error handling:** Check that error responses do not leak stack traces,
  file paths, SQL queries, or internal state to the client. Verify that
  all API error responses follow a consistent schema.
- **Type contract drift:** Check whether the OpenAPI spec (if generated)
  matches the actual route signatures and response models. Check whether
  TypeScript types on the frontend match the backend API contracts.
- **CI/CD pipeline:** Review GitHub Actions workflows for: pinned action
  versions, secret handling, security scanning gates, test coverage gates,
  and build artifact integrity.

### Phase 6 — Rate Limiting & Abuse Prevention

- Check whether upload endpoints, authentication endpoints, and API routes
  are protected by rate limiting.
- Assess whether a malicious user could exhaust compute resources by
  uploading very large files or making rapid repeated requests.
- Check whether failed login attempts trigger progressive delays or lockout.

---

## OUTPUT FORMAT

Write your report to:
```
reports/AUDIT-FULL-SWEEP-<YYYY-MM-DD>.md
```

Structure the report as:

```markdown
# Paciolus Full Sweep Audit — <DATE>

## Executive Summary
<2-3 sentence overview: how many findings by severity, top risk areas>

## Regression Check — Known Bug Status
<table: bug name | status | evidence>

## Findings

### F-001: <Title>
- **Severity:** CRITICAL / HIGH / MEDIUM / LOW
- **Category:** <from BASELINE.md § 9>
- **Evidence:** `<file>:<line>` — <explanation>
- **Impact:** <what can fail, blast radius>
- **Recommendation:** <prose>
- **Repair Prompt:**
  <pre-formatted prompt stub per BASELINE.md § 9>

### F-002: ...
<continue for all findings>

## Checklist Status
| Area                              | Status       | Notes           |
|-----------------------------------|--------------|-----------------|
| Zero-storage enforcement          | PASS / FAIL  | <brief>         |
| Auth lifecycle integrity          | PASS / FAIL  | <brief>         |
| Upload threat modeling            | PASS / FAIL  | <brief>         |
| CSRF/refresh coupling             | PASS / FAIL  | <brief>         |
| Observability data leakage        | PASS / FAIL  | <brief>         |
| OpenAPI/TS contract drift         | PASS / FAIL  | <brief>         |
| CI security gate integrity        | PASS / FAIL  | <brief>         |
| Multi-tenant isolation            | PASS / FAIL  | <brief>         |
| Rate limiting                     | PASS / FAIL  | <brief>         |
| Decimal precision compliance      | PASS / FAIL  | <brief>         |

## Summary Statistics
- Total findings: <N>
- CRITICAL: <N> | HIGH: <N> | MEDIUM: <N> | LOW: <N>
- New findings (not in previous reports): <N>
- Regressions detected: <N>
```
