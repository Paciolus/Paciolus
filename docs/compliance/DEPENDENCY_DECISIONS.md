# Dependency Decisions

> Documented risk acceptances and replacement assessments for dependencies
> flagged by automated or manual review. Each entry records the decision,
> rationale, and conditions for revisiting.

Last updated: 2026-10-22

---

## slowapi (accepted risk)

- **Version:** 0.1.10 (raised from 0.1.9 in Sprint 786b, 2026-10-22)
- **Status:** Low-frequency maintained upstream. Verified against PyPI's release history on
  2026-10-22: `0.1.7` 2022-11-28, `0.1.8` 2023-04-07, `0.1.9` 2024-02-05, **`0.1.10` 2026-06-13**.
  The 0.1.10 release landed during this repository's dormancy, after a two-year gap, and declares
  support through Python 3.13. The underlying `limits` library is actively maintained (v5.8.0).
- **Risk:** Reduced but not eliminated. A release in the last four months is evidence the wrapper
  layer is not abandoned, so a CVE against slowapi itself is now less likely to go unpatched
  forever — but a two-year gap preceded it, so "maintained" should be read as *low frequency*, not
  *responsive*. The structural mitigation is unchanged and is what the acceptance really rests on:
  the rate-limiting logic lives in `limits`, not in slowapi's ~200 lines of Starlette glue. A
  future Starlette major may still break middleware registration.
- **Alternatives assessed:**
  - `fastapi-limiter` 0.2.0 (Feb 2026) — actively maintained, but uses dependency-injection pattern incompatible with Paciolus's decorator-based `TieredLimit` + `ContextVar` system (123 decorator sites across 31 route files). Not a drop-in replacement.
  - Direct `limits` middleware — viable lowest-risk migration path documented in `docs/runbooks/rate-limiter-modernization.md`. Estimated effort: 3–4 sprints.
  - No maintained forks of slowapi exist on PyPI.
- **Decision:** Accept risk. Stay on slowapi, now at 0.1.10.
- **Accepted:** 2026-03-20 (re-affirmed 2026-10-22 on the corrected release data)
- **Revisit if:**
  - A CVE is filed against slowapi directly
  - `limits` library drops backward compatibility that slowapi depends on
  - A Starlette upgrade breaks slowapi's middleware registration
  - The canary tests in `backend/tests/test_rate_limit_slowapi_health.py` fail
- **Migration plan:** `docs/runbooks/rate-limiter-modernization.md`
- **Owner:** Engineering
