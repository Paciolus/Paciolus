# Deployment Governance

> Last updated: 2026-03-18 (Sprint 555 — AUDIT-04)

## Branch Protection Rules (main)

The following rules are enforced on the `main` branch via GitHub repository settings:

### Required Status Checks

All of the following CI jobs must pass before a PR can be merged to `main`:

| Job | Purpose |
|-----|---------|
| `backend-tests` | Python test suite (matrix: 3.11, 3.12) |
| `frontend-build` | Next.js build + ESLint |
| `frontend-tests` | Jest test suite (1,400+ tests) |
| `backend-lint` | Ruff linter |
| `lint-baseline-gate` | Ensures no lint regression above baseline |
| `pip-audit-blocking` | Python dependency audit (HIGH/CRITICAL) |
| `npm-audit-blocking` | Node dependency audit (HIGH/CRITICAL) |
| `bandit` | Python SAST (HIGH severity) |
| `secrets-scan` | TruffleHog secret detection |
| `mypy-check` | Python type checking |
| `openapi-drift-check` | OpenAPI schema consistency |

### Advisory Jobs (Do Not Block Merge)

| Job | Purpose |
|-----|---------|
| `pip-audit-advisory` | Full Python vulnerability report |
| `npm-audit-advisory` | Full Node vulnerability report |
| `merge-revert-guard` | Detects silent reverts (PR-only) |
| `e2e-smoke` | Playwright smoke tests (requires secrets) |

### Branch Protection Settings

- **Require status checks to pass before merging:** Enabled (jobs listed above)
- **Require branches to be up to date before merging:** Enabled
- **Dismiss stale pull request approvals when new commits are pushed:** Enabled
- **Require pull request reviews before merging:** Recommended (single-maintainer repo — currently advisory)

## Production Deployment Pipeline

### Frontend (Vercel)

- **Trigger:** Automatic deployment on merge to `main`
- **Platform:** Vercel (auto-deploy)
- **Preview:** Every PR gets a preview deployment
- **Rollback:** Instant via Vercel dashboard (previous deployment promotion)

### Backend (Render)

- **Trigger:** Automatic deployment on merge to `main`
- **Platform:** Render (auto-deploy from GitHub)
- **Health check:** `/health/live` endpoint verified post-deploy
- **Rollback:** Manual via Render dashboard (redeploy previous commit)

### Deployment Flow

```
PR opened → CI runs all jobs → Required checks must pass → Merge to main
                                                              ↓
                                                    Vercel auto-deploys frontend
                                                    Render auto-deploys backend
                                                    (Alembic migrations run on startup)
```

## Override Authorization

- **Who can bypass branch protection:** Repository owner only
- **When:** Emergency hotfixes where CI infrastructure itself is broken
- **Requirement:** Post-merge, a follow-up PR must be created to verify CI passes on the merged code
- **Audit trail:** GitHub records all bypass events in the repository audit log

## Related Documents

- CI workflow: `.github/workflows/ci.yml`
- Pinned actions registry: `.github/actions-pin-registry.md`
- Incident Response Plan: `docs/04-compliance/INCIDENT_RESPONSE_PLAN.md`
- BCP/DR Plan: `docs/04-compliance/BCP_DR_PLAN.md`
