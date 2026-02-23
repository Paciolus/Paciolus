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

**Total: 556 issues (55 errors + 501 warnings)**

### Errors (55 across 26 files)

| Count | Rule | Bucket |
|------:|------|--------|
| 19 | jsx-a11y/click-events-have-key-events | Accessibility |
| 19 | jsx-a11y/no-static-element-interactions | Accessibility |
| 5 | jsx-a11y/label-has-associated-control | Accessibility |
| 4 | jsx-a11y/mouse-events-have-key-events | Accessibility |
| 3 | jsx-a11y/no-redundant-roles | Accessibility |
| 3 | react-hooks/exhaustive-deps | True semantic risk |
| 1 | @typescript-eslint/no-explicit-any | True semantic risk |
| 1 | jsx-a11y/anchor-is-valid | Accessibility |

### Warnings (504 across 252 files)

| Count | Rule | Bucket |
|------:|------|--------|
| 492 | import/order | Auto-fixable style |
| 8 | import/no-duplicates | Auto-fixable style |
| 1 | (unused eslint-disable) | Config/tooling mismatch |

### Bucket Summary (Frontend)

| Bucket | Count | % |
|--------|------:|--:|
| Auto-fixable style | 500 | 90% |
| Accessibility | 51 | 9% |
| True semantic risk | 4 | 1% |
| Config/tooling mismatch | 1 | 0% |

---

## Combined Summary

| Bucket | Backend | Frontend | Total |
|--------|--------:|---------:|------:|
| Auto-fixable style | 127 | 500 | 627 |
| Accessibility | 0 | 51 | 51 |
| True semantic risk | 4 | 4 | 8 |
| Config/tooling mismatch | 0 | 1 | 1 |
| **Total** | **131** | **556** | **687** |

---

## Remediation Plan (Sprint Destinations)

### Immediate (this sprint)
- [x] Establish CI baseline reporting with "no increase" gate
- [ ] *Future:* `ruff check . --fix` for 127 auto-fixable backend issues
- [ ] *Future:* `eslint . --fix` for 500 auto-fixable frontend warnings

### Near-term (dedicated lint sprint)
- [ ] Fix 4 F821 undefined names in `test_revenue_testing.py`
- [ ] Fix 3 `react-hooks/exhaustive-deps` issues
- [ ] Fix 1 `@typescript-eslint/no-explicit-any` in BrandIcon
- [ ] Remove 1 unused eslint-disable in `telemetry.ts`
- [x] Add `coverage/` to eslint ignores (3 false positives) — done Sprint 411

### Scheduled (accessibility sprint)
- [ ] 19 click-events-have-key-events (add keyboard handlers to interactive elements)
- [ ] 19 no-static-element-interactions (change `<div onClick>` to `<button>` or add role)
- [ ] 5 label-has-associated-control (add `htmlFor` or nest inputs)
- [ ] 4 mouse-events-have-key-events (add `onFocus`/`onBlur` equivalents)
- [ ] 3 no-redundant-roles (remove redundant `role` attributes)
- [ ] 1 anchor-is-valid (fix anchor href)

---

## Baseline Lock Counts (for CI gate)

```
RUFF_BASELINE_ERRORS=131
ESLINT_BASELINE_ERRORS=55
ESLINT_BASELINE_WARNINGS=501
```
