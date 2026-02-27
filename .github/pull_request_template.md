## Description

<!-- Briefly describe what this PR does and why. -->

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Refactor (no functional change)
- [ ] Documentation update
- [ ] Dependency update
- [ ] Infrastructure / CI change

## Security & Compliance Checklist

> **All boxes must be checked (or marked N/A with justification) before this PR can be merged.**
> This checklist enforces CC8.4 of the SOC 2 Trust Services Criteria.
> Reference: `docs/04-compliance/SECURE_SDL_CHANGE_MANAGEMENT.md §3.2`

- [ ] **Input validation verified** — no raw user input reaches the DB or shell without sanitization
- [ ] **No secrets hardcoded** — no API keys, tokens, or passwords appear in the diff
- [ ] **Zero-Storage compliance checked** — no financial data (account numbers, balances, TB rows) is persisted to the database
- [ ] **Error sanitization applied** — `sanitize_error()` (or equivalent) is used on all error responses exposed to clients
- [ ] **Authentication / authorization correct** — route guards (`require_current_user`, `require_verified_user`, entitlement checks) match the auth tier documented in `docs/04-compliance/ACCESS_CONTROL_POLICY.md`
- [ ] **Rate limiting added** — all new API endpoints have a rate limit decorator (or N/A: static asset / non-public route)
- [ ] **Pydantic `response_model` present** — all new FastAPI routes declare `response_model=` (or N/A: route returns `Response` directly)
- [ ] **Tests added or updated** — changed logic is covered by new or updated tests; `pytest` passes

## Testing

```
# Commands run to verify this PR:
pytest tests/<relevant_file>.py -v
npm run build
```

<!-- Paste pass/fail summary or link to CI run. -->

## Related Issues / Sprints

<!-- e.g. "Closes #123" or "Sprint 449" -->
