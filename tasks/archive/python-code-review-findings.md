# Python & Full-Stack Code Review Findings

> **Date:** 2026-03-01
> **Tools:** ruff 0.15.4, bandit 1.9.4, mypy 1.19.1, ESLint 10.0, TypeScript 5.x, npm audit
> **Scope:** Backend (`backend/`), Frontend (`frontend/`), CI infrastructure

---

## Executive Summary

| Area | Status | Issues Found |
|------|--------|-------------|
| **Ruff (Python lint)** | PASS | 0 violations |
| **Bandit (SAST)** | 2 Medium + 18 Low | 1 real vulnerability, rest are false positives / acceptable |
| **mypy (type safety)** | 370 errors (non-test) | ~214 missing annotations, ~30 potential logic bugs, ~126 strict-mode noise |
| **ESLint** | PASS | 0 errors, 0 warnings |
| **TypeScript (tsc)** | PASS (source) | 0 non-test errors; 1,182 test-file errors from missing `@types/jest` at tsc layer (benign — works under Jest) |
| **npm audit** | 8 vulnerabilities | All in `@sentry/nextjs` → webpack → serialize-javascript chain |
| **Broad exceptions** | PASS | 0 bare excepts in application code |

---

## Finding Categories

### CRITICAL (0 findings)
None.

### HIGH (2 findings)

#### H1. XML Parsing Without defusedxml (B314 / CWE-20)
- **File:** `shared/ofx_parser.py:423`
- **Issue:** `xml.etree.ElementTree.fromstring()` used to parse user-uploaded OFX/QBO files. Vulnerable to XML bomb (billion laughs), XXE attacks.
- **Impact:** Denial of service; potential server-side request forgery if external entities are processed.
- **Fix:** Replace `import xml.etree.ElementTree as ET` with `import defusedxml.ElementTree as ET`. Add `defusedxml` to `requirements.txt`.
- **Effort:** Trivial (3 lines changed + 1 dependency)

#### H2. npm Dependency Vulnerabilities (serialize-javascript RCE)
- **File:** `frontend/package.json` — `@sentry/nextjs: ^10.39.0`
- **Issue:** 8 vulnerabilities (1 moderate, 7 high) in the `@sentry/nextjs` → `@sentry/webpack-plugin` → `webpack` → `terser-webpack-plugin` → `serialize-javascript` chain. `serialize-javascript <=7.0.2` is vulnerable to RCE via `RegExp.flags` and `Date.prototype.toISOString()`.
- **Impact:** Supply chain risk during build; no runtime exposure (build-time only).
- **Fix:** Upgrade `@sentry/nextjs` to latest patch. If chain persists, add resolution override for `serialize-javascript >=7.0.3`.
- **Effort:** Small (dependency bump + test build)

### MEDIUM (6 findings)

#### M1. mypy Type Errors with Potential Runtime Impact (6 locations)
These are mypy errors where the type system identifies possible `None` arithmetic or wrong-type assignments. All verified to be **false positives at runtime** (None guards exist but mypy can't trace them through boolean intermediates), but they should be fixed with explicit narrowing to improve code clarity and prevent regressions:

| File | Line | Issue | Runtime Risk |
|------|------|-------|-------------|
| `going_concern_engine.py` | 226 | `prior_revenue - prior_expenses` when both `Optional[float]` | False positive — guarded by `prior_loss` bool |
| `currency_engine.py` | 632 | `amount * rate` where `rate` from tuple unpack | False positive — `continue` exits before reaching this line when rate_info is None |
| `accrual_completeness_engine.py` | 176 | `prior_operating_expenses / MONTHS_PER_YEAR` | False positive — guarded by `prior_available` bool |
| `bank_reconciliation.py` | 561 | `LedgerTransaction` assigned to var previously typed `BankTransaction` | False positive — variable reuse in sequential loop blocks |
| `prior_period_comparison.py` | 340 | `RatioVariance` assigned to var previously typed `CategoryVariance` | False positive — variable reuse across loop blocks |
| `excel_generator.py` | 657/661 | `_write_statement_sheet` returns `int` but declared `-> None` | Real annotation bug — needs `-> int` return type |

**Fix:** Add explicit `assert x is not None` narrowing or type annotations. Effort: Small.

#### M2. Missing Return Type Annotation on `_write_statement_sheet`
- **File:** `excel_generator.py:657`
- **Issue:** Function returns `row` (int) but has no return type annotation. Line 661 uses the return value. mypy reports both "No return value expected" and "does not return a value."
- **Fix:** Add `-> int` return type annotation.
- **Effort:** Trivial.

#### M3. `callable` Used as Type Annotation (3 locations)
- **File:** `ratio_engine.py:1507, 1728, 1903`
- **Issue:** `callable` (builtin function) used where `Callable` (from `typing`) is needed.
- **Fix:** Replace `callable` with `Callable[..., Any]` or appropriate signature.
- **Effort:** Trivial.

#### M4. Hardcoded Bind All Interfaces Warning (B104)
- **File:** `config.py:120`
- **Issue:** `API_HOST in ("0.0.0.0", "::")` flagged by Bandit. This is a **warning check** (not the actual bind), so it's a false positive.
- **Fix:** Add `# nosec B104` comment with explanation.
- **Effort:** Trivial.

#### M5. `iif_parser.py` Integer-to-String Assignment (2 locations)
- **File:** `shared/iif_parser.py:198, 211`
- **Issue:** `int` assigned to a variable typed `str`.
- **Fix:** Add `str()` conversion or fix type annotation.
- **Effort:** Trivial.

#### M6. `engagement_manager.py:434` Unsupported Unary Minus
- **File:** `engagement_manager.py:434`
- **Issue:** Unary `-` on `object` type.
- **Fix:** Add explicit numeric type narrowing.
- **Effort:** Trivial.

### LOW (4 categories)

#### L1. Missing Type Annotations (214 `[no-untyped-def]` errors)
- **Top offenders:** `generate_sample_reports.py` (26), `multi_period_comparison.py` (19), `routes/export_memos.py` (18), `routes/engagements.py` (16), `routes/audit.py` (16), `pdf_generator.py` (13)
- **Impact:** No runtime risk. Reduces IDE support and refactoring confidence.
- **Fix:** Add function signatures progressively.
- **Effort:** Large (spread across ~60 files, 370 errors total)

#### L2. `no-any-return` Errors (53 instances)
- **Files:** `secrets_manager.py`, `financial_statement_builder.py`, `pdf_generator.py`, `shared/` modules
- **Impact:** Type narrowing missed — return types collapse to `Any`.
- **Fix:** Add explicit casts or intermediate typed variables.
- **Effort:** Medium (53 locations, but formulaic fixes)

#### L3. Bandit False Positives (18 Low severity)
- `B105/B106`: Hardcoded "passwords" in Pydantic `json_schema_extra` examples and `token_type="bearer"` — all false positives.
- `B311`: `random.random()` in `generate_large_tb.py` — test data generator, not security context.
- `B110`: `try/except/pass` in `security_middleware.py:181` — intentional graceful degradation for JWT decode.
- `B405`: `xml.etree.ElementTree` import — covered by H1 above.
- **Fix:** Add targeted `# nosec` comments where appropriate.
- **Effort:** Trivial.

#### L4. Test File mypy Errors (139 errors)
- **Top offender:** `tests/test_password_revocation.py` (51 errors) — almost entirely missing type annotations on test functions.
- **Impact:** Zero runtime risk; tests pass under pytest.
- **Fix:** Add type annotations to test functions.
- **Effort:** Medium (formulaic but numerous).

---

## Findings NOT Requiring Fixes

1. **ESLint**: 0 errors, 0 warnings — fully clean.
2. **Ruff**: 0 violations — fully clean.
3. **TypeScript (source)**: 0 non-test errors — fully clean.
4. **Frontend tsc test errors**: All 1,182 are `Cannot find name 'jest'` / `Cannot find name 'describe'` — `@types/jest` is configured for Jest only, not for `tsc --noEmit`. These work correctly in the Jest test runner.
5. **Broad exception handling**: Zero bare `except:` in application code; only one intentional `except Exception: pass` in security middleware (graceful JWT decode fallback).
