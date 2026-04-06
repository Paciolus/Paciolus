# Codex Audit Prompt — Targeted Probe

> **When to use:** When you want to stress-test a specific subsystem in depth.
> Fill in the PROBE CONFIGURATION section below before running.

---

## ROLE & CONSTRAINTS

You are a read-only auditor operating on the Paciolus repository.

**Before doing anything else, read `docs/audit/BASELINE.md` in full.** It
contains the product context, architecture, resolved issues, and accepted
risks.

### Hard Rules

1. **READ ONLY.** Do not modify, create, or delete any file in the repository.
   Do not install or upgrade packages. Do not execute mutating commands.
2. Your only permitted outputs are:
   - A report file written to the `reports/` directory
   - Your chat response summarizing findings
3. Do not output secrets. Evidence-first. Prefer false positives for
   Security, Zero-Storage, and Correctness categories.

---

## PROBE CONFIGURATION

> **Instructions:** Fill in the fields below before handing this prompt to
> Codex. Delete the examples and replace with your actual values.

```
PROBE_NAME:        <descriptive name, e.g., "Billing Subscription Lifecycle">
TARGET_FILES:      <comma-separated file paths or glob patterns>
                   Example: backend/billing/*, backend/routes/billing.py
TARGET_DOMAINS:    <risk domains to focus on>
                   Example: Billing, Multi-Tenant, Security
HYPOTHESIS:        <what you suspect might be wrong, or "general review">
                   Example: "Seat add-on mutations may still use items[0]"
DEPTH:             <shallow | standard | exhaustive>
                   shallow  = read target files only, flag obvious issues
                   standard = read target files + one hop of dependencies
                   exhaustive = trace all call paths to/from target code
KNOWN_CONTEXT:     <any context the auditor should know>
                   Example: "This area was last touched in PR #142"
```

---

## AUDIT PROTOCOL

### Step 1 — Scope Mapping

Read every file matching `TARGET_FILES`. For `standard` and `exhaustive`
depth, also identify:
- What calls into these files (callers)
- What these files call out to (callees)
- What database models/tables are touched
- What frontend components consume these APIs (if applicable)

Produce a brief dependency map in the report.

### Step 2 — Domain-Specific Review

For each domain listed in `TARGET_DOMAINS`, apply the corresponding review
checklist:

**Security:**
- Auth dependency injection on every route
- Role AND org scope checks (not just role)
- Input validation and sanitization
- Secret exposure in error responses
- Timing attack susceptibility in auth comparisons

**Zero-Storage:**
- No financial data in logs, DB, cache, telemetry, temp files
- Export streams to client without intermediate disk writes
- Browser storage clean (no localStorage/sessionStorage/IndexedDB)

**Correctness:**
- `decimal.Decimal` throughout financial arithmetic
- Edge case handling (empty, negative, zero, null, max-length)
- Consistent rounding behavior
- Score/label derivation from computation (not hardcoded)

**Billing:**
- Org-scoped queries (no global aggregations)
- Webhook idempotency (duplicate event handling)
- Stripe line item identification (not positional)
- Quota enforcement accuracy
- Proration correctness on plan changes

**Multi-Tenant:**
- Tenant filter on every query
- No shared mutable state between tenants
- Admin endpoints scoped appropriately
- Export/sharing links scoped to originating org

**Architecture:**
- Consistent error response schema
- No circular imports or hidden coupling
- Separation of concerns (routes vs business logic vs data access)
- Test coverage for critical paths

**CI/CD:**
- Pinned action versions
- Secret masking
- Security scanning present and non-skippable
- Build reproducibility

**Performance:**
- No N+1 queries in loops
- Memory-bounded file processing
- Appropriate timeouts on external calls
- Connection pool sizing

### Step 3 — Hypothesis Testing

If `HYPOTHESIS` is not "general review," treat it as the primary
investigation target:
1. Locate the specific code path described in the hypothesis
2. Trace it end-to-end
3. Confirm or refute the hypothesis with evidence
4. If confirmed, classify severity and draft a repair prompt
5. If refuted, document why the code is correct

### Step 4 — Lateral Discovery

Even when focused on a specific hypothesis, scan the target files for any
findings outside the hypothesis. Targeted probes should not develop tunnel
vision.

---

## OUTPUT FORMAT

Write your report to:
```
reports/AUDIT-PROBE-<PROBE_NAME_SLUG>-<YYYY-MM-DD>.md
```

Structure the report as:

```markdown
# Paciolus Targeted Probe — <PROBE_NAME> — <DATE>

## Probe Configuration
- Target files: <list>
- Risk domains: <list>
- Depth: <level>
- Hypothesis: <statement or "general review">

## Dependency Map
<brief description of what calls in/out of the target files>

## Hypothesis Result
- **Status:** CONFIRMED / REFUTED / INCONCLUSIVE
- **Evidence:** <file:line and explanation>
- **Severity (if confirmed):** <level>

## Findings

### F-001: <Title>
- **Severity:** CRITICAL / HIGH / MEDIUM / LOW
- **Category:** <category>
- **Evidence:** `<file>:<line>` — <explanation>
- **Impact:** <what can fail>
- **Repair Prompt:** <stub per BASELINE.md § 9>

## Summary
- Total findings: <N>
- CRITICAL: <N> | HIGH: <N> | MEDIUM: <N> | LOW: <N>
- Hypothesis: <one-line result>
```

---

## COMMON PROBE PRESETS

Copy one of these into the PROBE CONFIGURATION section as a starting point:

### Preset: Billing Lifecycle
```
PROBE_NAME:     Billing Subscription Lifecycle
TARGET_FILES:   backend/billing/*, backend/routes/billing.py,
                backend/models/subscription.py
TARGET_DOMAINS: Billing, Multi-Tenant, Security
HYPOTHESIS:     general review
DEPTH:          exhaustive
KNOWN_CONTEXT:  Cross-tenant analytics leak and seat mutation bug were
                previously identified. Verify fixes hold.
```

### Preset: Upload Pipeline
```
PROBE_NAME:     File Upload & Processing Pipeline
TARGET_FILES:   backend/routes/upload.py, backend/services/parser*,
                backend/services/analysis*
TARGET_DOMAINS: Zero-Storage, Security, Correctness, Performance
HYPOTHESIS:     general review
DEPTH:          exhaustive
KNOWN_CONTEXT:  Zero-storage invariant is critical. Check for temp file
                creation, memory exhaustion on large files, and formula
                injection in CSV re-export.
```

### Preset: Diagnostic Engine
```
PROBE_NAME:     Diagnostic Computation Accuracy
TARGET_FILES:   backend/diagnostics/*, backend/services/scoring*
TARGET_DOMAINS: Correctness, Zero-Storage
HYPOTHESIS:     Float arithmetic may still be present in scoring paths
DEPTH:          exhaustive
KNOWN_CONTEXT:  Known bugs include identical data quality scores, hardcoded
                risk tier labels, and dashboard/PDF score divergence.
```

### Preset: Auth System
```
PROBE_NAME:     Authentication & Session Integrity
TARGET_FILES:   backend/auth/*, backend/middleware/*, backend/routes/auth.py
TARGET_DOMAINS: Security
HYPOTHESIS:     general review
DEPTH:          standard
KNOWN_CONTEXT:  AUDIT-02 covered this area. Focus on verifying no regressions
                and checking any new routes added since AUDIT-02.
```

### Preset: CI/CD Pipeline
```
PROBE_NAME:     CI/CD Security & Integrity
TARGET_FILES:   .github/workflows/*, Dockerfile*, docker-compose*
TARGET_DOMAINS: CI/CD, Security, Infra
HYPOTHESIS:     general review
DEPTH:          standard
KNOWN_CONTEXT:  AUDIT-04 covered this area. Check for unpinned actions,
                missing security gates, and secret exposure.
```
