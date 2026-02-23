# Lint Baseline — Stabilization & Baseline Lock

> Captured: 2026-02-22
> Purpose: Freeze current quality state so improvements are measurable and non-regressive.

---

## Backend (ruff)

**Total: 131 errors (127 auto-fixable)**

| Count | Rule | Category | Auto-fix | Bucket |
|------:|------|----------|:--------:|--------|
| 62 | F401 | Unused imports | Yes | Auto-fixable style |
| 53 | I001 | Unsorted imports | Yes | Auto-fixable style |
| 9 | UP007 | Non-PEP 604 annotations (`Optional[X]` → `X \| None`) | Yes | Auto-fixable style |
| 4 | F821 | Undefined name | **No** | True semantic risk |
| 3 | UP035 | Deprecated typing imports | Yes | Auto-fixable style |

### F821 — Undefined Name (TRUE RISKS)

All 4 in `tests/test_revenue_testing.py`:
- Lines 1167, 1234, 1282, 1342: `ContractEvidenceLevel` used before import (import at line 1172)

**Fix:** Move the import above first usage.

### Bucket Summary (Backend)

| Bucket | Count | % |
|--------|------:|--:|
| Auto-fixable style | 127 | 97% |
| True semantic risk | 4 | 3% |
| Config/tooling mismatch | 0 | 0% |
| Accessibility | 0 | 0% |

---

## Frontend (eslint)

**Total: 0 issues (0 errors + 0 warnings) — FULLY REMEDIATED (Sprints 412–413)**

*(Original baseline was 556 issues: 55 errors + 501 warnings)*

---

## Combined Summary

| Bucket | Backend | Frontend | Total |
|--------|--------:|---------:|------:|
| Auto-fixable style | 127 | **0** | 127 |
| Accessibility | 0 | **0** | 0 |
| True semantic risk | 4 | **0** | 4 |
| Config/tooling mismatch | 0 | **0** | 0 |
| **Total** | **131** | **0** | **131** |

---

## Remediation Plan (Sprint Destinations)

### Immediate (this sprint)
- [x] Establish CI baseline reporting with "no increase" gate
- [ ] *Future:* `ruff check . --fix` for 127 auto-fixable backend issues
- [ ] *Future:* `eslint . --fix` for 500 auto-fixable frontend warnings

### Near-term (dedicated lint sprint)
- [ ] Fix 4 F821 undefined names in `test_revenue_testing.py`
- [x] Fix 3 `react-hooks/exhaustive-deps` issues — done Sprint 412 (plugin wiring) + Sprint 413 (fixes)
- [x] Fix 1 `@typescript-eslint/no-explicit-any` in BrandIcon — done Sprint 412 (dead directive removed)
- [x] Remove 1 unused eslint-disable in `telemetry.ts` — done Sprint 412
- [x] Add `coverage/` to eslint ignores (3 false positives) — done Sprint 411
- [x] 51 accessibility errors (jsx-a11y) — done Sprint 412c
- [x] 500 auto-fixable import warnings — done Sprint 412 + 412e
- [x] 4 `react-hooks/exhaustive-deps` final warnings — done Sprint 413

**Frontend ESLint: 100% remediated (556 → 0)**

---

## Baseline Lock Counts (for CI gate)

```
RUFF_BASELINE_ERRORS=131
ESLINT_BASELINE_ERRORS=0
ESLINT_BASELINE_WARNINGS=0
```
