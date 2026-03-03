# Lint Baseline — Stabilization & Baseline Lock

> Captured: 2026-02-22
> Updated: 2026-02-23
> Purpose: Freeze current quality state so improvements are measurable and non-regressive.

---

## Backend (ruff)

**Total: 0 errors — FULLY REMEDIATED (Sprint 414)**

*(Original baseline was 131 errors: 127 auto-fixable + 4 F821)*

---

## Frontend (eslint)

**Total: 0 issues (0 errors + 0 warnings) — FULLY REMEDIATED (Sprints 412–413)**

*(Original baseline was 556 issues: 55 errors + 501 warnings)*

---

## Combined Summary

| Component | Original | Current | Status |
|-----------|--------:|---------:|--------|
| Backend (ruff) | 131 | **0** | Clean |
| Frontend (eslint) | 556 | **0** | Clean |
| **Total** | **687** | **0** | **100% remediated** |

---

## Remediation History

| Sprint | Scope | Issues Fixed |
|--------|-------|-------------|
| 411 | Baseline capture + CI gate | 0 (process only) |
| 412 | ESLint toolchain + import auto-fix | −355 frontend |
| 412c | Accessibility errors (jsx-a11y) | −51 frontend |
| 412e | Import order warnings | −146 frontend |
| 413 | exhaustive-deps warnings | −4 frontend |
| **414** | **ruff --fix + F821 manual fix** | **−131 backend** |
| **Total** | | **−687** |

---

## Baseline Lock Counts (for CI gate)

```
RUFF_BASELINE_ERRORS=0
ESLINT_BASELINE_ERRORS=0
ESLINT_BASELINE_WARNINGS=0
```
