# Phase XXXIV — Multi-Currency Conversion (Sprints 255–260)

> **Focus:** Deliver Multi-Currency conversion — highest-demand deferred feature + critical security pre-flight
> **Source:** Agent Council assessment (2026-02-15) — Path C selected (Feature Phase First)
> **Strategy:** Pre-flight security fix (python-jose → PyJWT, package rename), then RFC-driven feature delivery
> **Design:** User-provided exchange rates (CSV upload or manual entry), TB-level conversion, Zero-Storage compliant (rate tables ephemeral)
> **Version:** 1.3.0
> **Tests:** 3,129 backend + 520 frontend

| Sprint | Feature | Complexity | Agent Lead | Status |
|--------|---------|:---:|:---|:---:|
| 255 | Security Pre-Flight: python-jose → PyJWT, package.json rename | 3/10 | BackendCritic + QualityGuardian | COMPLETE |
| 256 | Multi-Currency RFC: exchange rate model, IAS 21/ASC 830 scope, rounding rules | 3/10 | AccountingExpertAuditor | COMPLETE |
| 257 | Currency conversion engine: rate lookup, temporal matching, conversion | 7/10 | BackendCritic | COMPLETE |
| 258 | API endpoints (rate upload, conversion) + Frontend currency UI | 6/10 | BackendCritic + FrontendExecutor | COMPLETE |
| 259 | Testing suite + memo generator + export integration | 4/10 | QualityGuardian | COMPLETE |
| 260 | Phase XXXIV Wrap — regression, documentation, v1.3.0 | 2/10 | QualityGuardian | COMPLETE |

## Sprint 255 — Security Pre-Flight
- [x] Replaced `python-jose[cryptography]` with `PyJWT[crypto]==2.10.1`
- [x] Removed `types-python-jose` from `requirements-dev.txt`
- [x] Updated `auth.py`: `from jose import JWTError, jwt` → `import jwt` + `from jwt.exceptions import PyJWTError`
- [x] Updated `tests/test_password_revocation.py` and `tests/test_sprint201_cleanup.py`
- [x] Renamed `closesignify-frontend` → `paciolus-frontend` in `package.json`
- [x] Updated `docs/02-technical/ARCHITECTURE.md`
- [x] 3,050 backend tests pass, frontend build passes

## Sprint 256 — Multi-Currency RFC
- [x] RFC document at `docs/02-technical/rfc-multi-currency.md`
- [x] Closing-rate MVP scope (defers average/historical rates)
- [x] IAS 21 / ASC 830 guardrails documented
- [x] Zero-Storage compliance: session-scoped rate tables
- [x] AccountingExpertAuditor review completed

## Sprint 257 — Conversion Engine
- [x] Created `backend/currency_engine.py` (450+ lines)
- [x] Rate table parsing with ISO 4217 validation
- [x] Rate lookup: exact match → nearest prior date fallback → inverse rate
- [x] Stale rate detection (> 90 days)
- [x] Currency column auto-detection via `column_detector.py` patterns
- [x] Vectorized TB conversion with Decimal precision (4 internal, 2 display)
- [x] Unconverted item flagging with severity recalculation
- [x] 55 unit tests (`test_currency_engine.py`)

## Sprint 258 — API + Frontend
- [x] 4 endpoints: `POST /audit/currency-rates`, `POST /audit/currency-rate`, `GET /audit/currency-rates`, `DELETE /audit/currency-rates`
- [x] Session-scoped rate storage with TTL (2h) and max sessions (500)
- [x] Auto-conversion integrated into TB upload flow (`routes/audit.py`)
- [x] Frontend: `useCurrencyRates` hook with auth token
- [x] Frontend: `CurrencyRatePanel` component (CSV upload + manual entry)
- [x] Panel integrated into trial-balance page
- [x] 15 route tests (`test_currency_routes.py`)

## Sprint 259 — Testing + Memo + Export
- [x] Currency conversion memo PDF generator (`currency_memo_generator.py`)
- [x] `CurrencyConversionMemoInput` schema in `shared/export_schemas.py`
- [x] Export endpoint `/export/currency-conversion-memo` registered
- [x] Backward-compatible re-export in `routes/export.py`
- [x] 9 memo tests (`test_currency_memo.py`)

## Sprint 260 — Phase XXXIV Wrap
- [x] Full regression: 3,129 backend tests pass
- [x] Frontend build passes
- [x] Zero-Storage compliance verified (rate tables ephemeral)
- [x] Version bump to 1.3.0
- [x] Documentation archived, CLAUDE.md + MEMORY.md updated

## Key Deliverables
- **New files:** `currency_engine.py`, `currency_memo_generator.py`, `routes/currency.py`, `docs/02-technical/rfc-multi-currency.md`
- **New frontend:** `hooks/useCurrencyRates.ts`, `components/currencyRates/CurrencyRatePanel.tsx`
- **New tests:** 79 (55 engine + 15 route + 9 memo)
- **Modified:** `auth.py` (PyJWT migration), `routes/audit.py` (auto-conversion), `routes/__init__.py`, `export_memos.py`, `export.py`, `export_schemas.py`

## Lessons Learned
- `generate_reference_number()` takes no arguments (not a prefix)
- `build_memo_header()` signature: `(story, styles, doc_width, title, reference, client_name)` — no filename/prepared_by
- `ClassicalColors` uses `OBSIDIAN_700` not `OBSIDIAN_LIGHT`, `OATMEAL_400` not `OATMEAL_DARK`
- Style key is `MemoSection` not `MemoSectionHeader`
- `apiFetch/apiPost/apiDelete` all require `token` as second parameter
- `sanitize_error` is in `shared.error_messages`, not `shared.helpers`
