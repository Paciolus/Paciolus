# Contributing to Paciolus

## Pull Request Process

Every PR to `main` must complete the **Security & Compliance Checklist** embedded in the PR template (`.github/pull_request_template.md`).

GitHub populates this template automatically when you open a new pull request. All eight checklist items must be checked (or explicitly marked N/A with justification) before the PR is eligible for review.

The checklist enforces **CC8.4** of the SOC 2 Trust Services Criteria and mirrors the code review requirements in `docs/04-compliance/SECURE_SDL_CHANGE_MANAGEMENT.md §3.2`.

## CI Gates

All PRs must pass the following CI checks before merging:

| Job | Requirement |
|-----|-------------|
| `backend-tests` | All pytest tests pass (Python 3.11 + 3.12) |
| `frontend-build` | `npm run build` succeeds with no errors |
| `backend-lint` | Ruff error count ≤ baseline |
| `lint-baseline-gate` | ESLint errors + warnings ≤ baseline |
| `bandit` | No HIGH-severity security findings |
| `accounting-policy` | Accounting invariant checkers pass |
| `report-standards` | Report standards validator passes |
| `pip-audit-blocking` | No HIGH/CRITICAL Python CVEs |
| `npm-audit-blocking` | No HIGH/CRITICAL Node CVEs |

## Commit Messages

Use the format: `Sprint N: Brief description of change`

Example: `Sprint 449: Add PR security checklist template`

## Branch Protection

The `main` branch requires all CI status checks to pass and branches to be up to date before merging.
