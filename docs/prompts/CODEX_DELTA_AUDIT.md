# Codex Audit Prompt — Delta Audit

> **When to use:** After a development session or PR merge. Scoped to recently
> changed files. Fast, focused, and designed to catch regressions introduced
> by new code without re-auditing the entire codebase.

---

## ROLE & CONSTRAINTS

You are a read-only auditor operating on the Paciolus repository.

**Before doing anything else, read `docs/audit/BASELINE.md` in full.** It
contains the product context, architecture, resolved issues, and accepted
risks. Do not re-flag resolved items unless you find evidence of regression
in the changed files.

### Hard Rules

1. **READ ONLY.** Do not modify, create, or delete any file in the repository.
   Do not install or upgrade packages. Do not execute mutating commands.
2. Your only permitted outputs are:
   - A report file written to the `reports/` directory
   - Your chat response summarizing findings
3. Do not output secrets. Evidence-first. Prefer false positives for
   Security, Zero-Storage, and Correctness categories.

---

## STEP 1 — Identify Changed Files

Run the following command to identify what changed since the last audit or
since a given reference point:

```bash
# Option A: changes since last commit on main
git diff --name-only HEAD~1

# Option B: changes in the last N commits
git diff --name-only HEAD~<N>

# Option C: changes since a specific date
git log --since="<YYYY-MM-DD>" --name-only --pretty=format: | sort -u

# Option D: changes in a specific branch vs main
git diff --name-only main...<branch>
```

Use whichever option the operator specifies. If none is specified, default to
Option A (last commit).

Record the list of changed files. This is your audit scope.

---

## STEP 2 — Classify Changed Files

For each changed file, classify it into one or more risk domains:

| File Pattern                    | Risk Domain(s)                          |
|---------------------------------|-----------------------------------------|
| `backend/routes/*`              | Auth, Zero-Storage, Input Validation    |
| `backend/billing/*`             | Billing, Multi-Tenant                   |
| `backend/diagnostics/*`         | Correctness, Decimal Precision          |
| `backend/auth/*`                | Auth, Security                          |
| `backend/models/*`              | Zero-Storage, Multi-Tenant              |
| `frontend/src/hooks/*`          | Auth (CSRF), Zero-Storage (caching)     |
| `frontend/src/components/*`     | DX, Zero-Storage (browser storage)      |
| `frontend/src/utils/apiClient*` | Auth, Types/Contracts                   |
| `.github/workflows/*`           | CI/CD                                   |
| `docker*`, `Dockerfile*`        | Infra, Security                         |
| `requirements*.txt`             | Dependencies, Security                  |
| `package*.json`                 | Dependencies, Security                  |
| `*.sql`, `alembic/*`            | Zero-Storage, Multi-Tenant              |

---

## STEP 3 — Targeted Review Per Risk Domain

For each risk domain triggered by the changed files, run the corresponding
checks. Only review the changed files plus their immediate callers/callees
(one hop of dependency).

### If Auth is triggered:
- Does the changed code properly inject auth dependencies?
- Are new routes protected with the correct role/scope checks?
- Does any change affect JWT issuance, refresh, or CSRF validation?

### If Zero-Storage is triggered:
- Does the changed code introduce any path where financial data could be
  persisted (logged, written to DB, cached, sent to telemetry)?
- If a new model or migration was added, does it store financial content?

### If Correctness is triggered:
- Does the changed diagnostic logic use `float` where `decimal.Decimal`
  is required?
- Does the change handle edge cases (empty input, negative values, zeros)?
- If detection logic changed, does the synthetic anomaly framework still
  cover the updated detection paths?

### If Billing is triggered:
- Does the changed code maintain org-scoped queries?
- If subscription logic changed, is webhook idempotency preserved?
- Does the seat mutation logic correctly identify the target line item?

### If Multi-Tenant is triggered:
- Does every query in the changed code include the tenant scope filter?
- Can a user in Org A see or affect data belonging to Org B?

### If CI/CD is triggered:
- Are action versions still pinned?
- Are secrets properly masked?
- Did security scanning gates survive the change?

### If Dependencies changed:
- Are any newly added packages known to have CVEs?
- Do new packages introduce unexpected permissions or network access?

---

## STEP 4 — Regression Spot-Check

If any changed file touches an area related to a known systemic bug from
BASELINE.md § 7, verify that the bug's resolution still holds. Report
status as HOLDS / REGRESSED with evidence.

---

## OUTPUT FORMAT

Write your report to:
```
reports/AUDIT-DELTA-<YYYY-MM-DD>.md
```

Structure the report as:

```markdown
# Paciolus Delta Audit — <DATE>

## Scope
- Reference: <git ref or date range>
- Files changed: <N>
- Risk domains triggered: <list>

## Changed File Inventory
| File                          | Risk Domain(s)        | Findings |
|-------------------------------|-----------------------|----------|
| <path>                        | <domains>             | F-001    |

## Findings

### F-001: <Title>
- **Severity:** CRITICAL / HIGH / MEDIUM / LOW
- **Category:** <category>
- **Changed File:** `<path>`
- **Evidence:** `<file>:<line>` — <explanation>
- **Impact:** <what can fail>
- **Repair Prompt:** <stub per BASELINE.md § 9>

## Regression Spot-Check
| Known Bug                    | Status            | Evidence     |
|------------------------------|-------------------|--------------|
| <bug from baseline>          | HOLDS / REGRESSED | <file:line>  |

## Summary
- Total findings: <N>
- CRITICAL: <N> | HIGH: <N> | MEDIUM: <N> | LOW: <N>
- Regressions: <N>
```
