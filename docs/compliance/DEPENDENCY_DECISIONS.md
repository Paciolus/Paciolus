# Dependency Decisions

> Documented risk acceptances and replacement assessments for dependencies
> flagged by automated or manual review. Each entry records the decision,
> rationale, and conditions for revisiting.

Last updated: 2026-03-20

---

## slowapi (accepted risk)

- **Version:** 0.1.9
- **Status:** Low-frequency maintained upstream (last release Feb 2024, CI updates Aug 2025); underlying `limits` library is actively maintained (v5.8.0, Feb 2026)
- **Risk:** No active security patches for the slowapi wrapper layer; future Starlette major versions may break middleware registration
- **Alternatives assessed:**
  - `fastapi-limiter` 0.2.0 (Feb 2026) — actively maintained, but uses dependency-injection pattern incompatible with Paciolus's decorator-based `TieredLimit` + `ContextVar` system (123 decorator sites across 31 route files). Not a drop-in replacement.
  - Direct `limits` middleware — viable lowest-risk migration path documented in `docs/runbooks/rate-limiter-modernization.md`. Estimated effort: 3–4 sprints.
  - No maintained forks of slowapi exist on PyPI.
- **Decision:** Accept risk. Keep slowapi 0.1.9.
- **Accepted:** 2026-03-20
- **Revisit if:**
  - A CVE is filed against slowapi directly
  - `limits` library drops backward compatibility that slowapi depends on
  - A Starlette upgrade breaks slowapi's middleware registration
  - The canary tests in `backend/tests/test_rate_limit_slowapi_health.py` fail
- **Migration plan:** `docs/runbooks/rate-limiter-modernization.md`
- **Owner:** Engineering
