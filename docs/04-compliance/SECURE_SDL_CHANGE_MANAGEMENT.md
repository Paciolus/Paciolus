# Secure Development and Change Management

**Version:** 2.0 · **Effective:** 2026-10-24 · **Owner:** security@paciolus.com · **Classification:** Public

Version 1.1 required at least one approving reviewer on every pull request, forbade self-approval and
required CTO sign-off for off-hours, weekend and destructive-migration changes. Paciolus has one
developer, so none of that could happen; branch protection does not require an approval. This version
describes the controls that actually gate a change. The previous text is in
[`archive/SECURE_SDL_CHANGE_MANAGEMENT_pre-sprint-845_2026-10-24.md`](archive/SECURE_SDL_CHANGE_MANAGEMENT_pre-sprint-845_2026-10-24.md).

## How a change reaches production

1. Work happens on a branch and is opened as a pull request into `main`.
2. **Required status checks** (branch protection, enforced by GitHub): secrets scan; backend tests on
   Python 3.11, 3.12 and PostgreSQL 15; backend lint (ruff) and type check (mypy); lint baseline gate;
   frontend build + lint and tests (Jest); Python and Node dependency audits; Bandit SAST. CI also runs
   an OpenAPI drift check and the accounting-policy guard (no float money columns, no hard deletes of
   audit tables, adjustment gating and more).
3. **All review conversations must be resolved** before merge, including automated review comments.
   Linear history is required. No human approval is required — there is no second engineer.
4. Pre-commit hooks run linting and the frontend test gate locally; the commit-message hook enforces
   sprint bookkeeping.
5. Merging to `main` deploys automatically: frontend to Vercel, backend to Render. Database migrations
   run (`alembic upgrade head`) on backend start; a failed migration fails the deploy.
6. **The live deploy is checked against `main`**, because Render keeps serving the previous image when
   a deploy fails at startup.

## Security practices

- Dependencies: Dependabot plus blocking `pip-audit` and `npm audit` in CI.
- Secrets live in the Render and Vercel dashboards; the secrets scan blocks committed credentials.
- Customer-facing claims are guarded by tests: storage wording (`test_storage_claims.py`), pricing
  figures (`test_pricing_copy_consistency.py`), tool counts and cited standards (catalog and citation
  consistency tests), subprocessor coverage (`scripts/lint_subprocessors.py`).

## Rolling back

Revert the pull request (or redeploy the previous Render image). Migrations are written to be guarded
and additive; a destructive migration is called out in its pull request.
