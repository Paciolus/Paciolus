# Test Redundancy & Quality Audit — Paciolus

**Date:** 2026-02-26
**Scope:** ~5,249 backend test functions (154 files) + ~1,327 frontend test blocks (111 files)

---

## TL;DR — Can You Have Too Many Tests?

**Yes.** Redundant tests:
- **Slow CI** — every duplicated test adds wall-clock time
- **Obscure failures** — when 10 tests fail from one change, the signal-to-noise ratio drops
- **Create maintenance burden** — copypasted tests must all be updated when the interface changes
- **Give false confidence** — 5,000 tests that all check the same paths leave edge cases untested

This audit found **actionable redundancy** in both backend and frontend, plus several quality issues.

---

## Finding 1: Frontend Tool Page Tests Are Copypasted (CONSOLIDATION CANDIDATE)

**Impact: ~90 tests across 10 files → could be ~25 tests in 1 shared helper + 10 thin files**

The 10 tool page tests (`APTestingPage`, `ARAgingPage`, `BankRecPage`, `FixedAssetTestingPage`, `InventoryTestingPage`, `JournalEntryTestingPage`, `MultiPeriodPage`, `PayrollTestingPage`, `RevenueTestingPage`, `ThreeWayMatchPage`) are near-identical copypastes. Each contains this same test battery:

| Test description | Copies |
|-----------------|--------|
| `renders hero header` | 10 |
| `shows sign-in CTA for unauthenticated user` | 10 |
| `shows error state with retry button` | 10 |
| `shows result components on success` | 9 |
| `shows loading state` | 9 |
| `shows info cards in idle state` | 9 |
| `shows export buttons on success` | 8 |
| `shows upload zone for authenticated verified user` | 7 |

**A `diff` between `APTestingPage.test.tsx` and `ARAgingPage.test.tsx` shows only component names and test IDs differ** — the test structure, mock setup, and assertion patterns are identical.

**Recommendation:** Create a `createToolPageTests(config)` helper (similar to the existing `createTestingHook.ts` pattern) that generates the common test battery. Each tool file then only needs:
```typescript
createToolPageTests({
  component: APTestingPage,
  hookName: 'useAPTesting',
  heroText: 'AP Payment Testing',
  testIds: { scoreCard: 'ap-score-card', grid: 'ap-test-grid', ... },
})
```
This would **reduce ~900 lines to ~200** while preserving every assertion.

---

## Finding 2: Backend Duplicate Test Function Names (305 duplicates)

**305 test function names appear in multiple locations.** Most are class-scoped (e.g., `test_to_dict` in different `TestXxxSerialization` classes), which is technically fine for pytest since the class qualifies the test ID. However:

### Genuinely Problematic Duplicates

| Name | Files | Issue |
|------|-------|-------|
| `test_to_dict` | 40 occurrences across 12 files | Over-fragmented: each dataclass gets its own `test_to_dict`. These are boilerplate serialization checks that could be parametrized |
| `test_empty_input` | 6 files | Same empty-DataFrame edge case tested identically in each engine file |
| `test_empty_data` | 6 files | Same pattern as above |
| `test_route_registered` | Multiple API test files | Verifies route exists in the router — essentially a smoke test that duplicates what the router itself guarantees |
| `test_pdf_route_registered` | Multiple export test files | Same as above |
| `test_csv_route_registered` | Multiple export test files | Same as above |

### Recommendation
- **Parametrize `to_dict` tests** — a single `@pytest.mark.parametrize("model_class,kwargs", [...])` covering all dataclasses would replace 40 scattered tests with 1
- **Shared empty-input fixture** — a `test_engine_handles_empty_input(engine_func)` parametrized test covering all engines
- **Remove `route_registered` tests** — these test FastAPI's router, not your code. If the route works when called, it's registered. These add CI time with zero value.

---

## Finding 3: Weak Backend Tests (status-code-only assertions)

8 test functions assert only `response.status_code` without checking the response body:

| File | Test |
|------|------|
| `conftest.py` | `test_dialect` |
| `test_accounting_policy_guard.py` | `test_db_delete_non_protected_passes` |
| `test_accounting_policy_guard.py` | `test_soft_delete_passes` |
| `test_accounting_policy_guard.py` | `test_query_delete_flagged` |
| `test_accounting_policy_guard.py` | `test_comment_lines_ignored` |
| `test_accounting_policy_guard.py` | `test_posted_not_terminal_flagged` |
| `test_accounting_policy_guard.py` | `test_proposed_conditional_passes` |
| `test_accounting_policy_guard.py` | `test_proposed_unconditional_in_set_flagged` |

**Recommendation:** Either add body assertions or mark as smoke tests. A test that only checks "didn't crash" gives false confidence.

---

## Finding 4: Stale/Skipped Tests

Only **1 skipped test** found (good hygiene):
- `test_audit_core.py:547` — `@pytest.mark.skip(reason="Flaky under full-suite load; passes in isolation. Deferred to dedicated perf job.")`

Plus 2 conditional skips (legitimate):
- `test_parser_resource_guards.py:163` — `pytest.skip("Compression ratio not high enough to trigger guard")` (data-dependent)
- `test_timestamp_defaults.py:201` — `@pytest.mark.skipif(not _is_test_sqlite, ...)` (DB-specific)

**Frontend: 0 skipped tests.** Clean.

**Recommendation:** The flaky `test_audit_core.py:547` has been deferred indefinitely — either fix the root cause (likely a shared-state issue) or delete it. Stale skips accumulate.

---

## Finding 5: Snapshot Tests (Low risk)

Only **5 inline snapshots** in `motionTokens.test.ts` — these lock down animation token values. This is a reasonable use (preventing accidental motion regressions). No stale `.snap` files found.

---

## Finding 6: Monolithic Test Files

### Backend (largest files)
| File | Lines | Tests | Verdict |
|------|-------|-------|---------|
| `test_pricing_launch_validation.py` | 1,835 | 157 | **Keep** — well-organized into 7 classes, parametrized |
| `test_upload_validation.py` | 1,599 | 141 | **Keep** — logically grouped by validation type |
| `test_revenue_testing.py` | 1,444 | 120 | **Consider split** — 18+ classes, mixes unit + integration |
| `test_inventory_testing.py` | 1,200 | 136 | **Consider split** — same pattern as revenue |
| `test_three_way_match.py` | 1,176 | 115 | **Consider split** |

### Frontend (largest files)
| File | Lines | Tests | Verdict |
|------|-------|-------|---------|
| `apiClient.test.ts` | 1,029 | 60 | **Keep** — comprehensive API client coverage |
| `useTrialBalanceAudit.test.ts` | 501 | 20 | **Keep** — proportional to hook complexity |
| `BillingComponents.test.tsx` | 485 | 50 | **Consider split** by component |

---

## Finding 7: Auth Pattern Duplication (Backend)

The `test_401_without_auth` pattern is copypasted across 8 API test files. Each one:
1. Clears dependency overrides
2. Creates an httpx client
3. Makes a request
4. Asserts 401

**Recommendation:** Create a shared `assert_requires_auth(method, path)` helper. The 8 copypasted tests become 8 one-liner calls.

---

## Summary: Actionable Cleanup

### Safe to Remove (saves CI time, no coverage loss)
| Category | Est. tests | Rationale |
|----------|-----------|-----------|
| `route_registered` / `pdf_route_registered` / `csv_route_registered` smoke tests | ~20-30 | Test FastAPI internals, not application logic |
| Flaky skipped test in `test_audit_core.py` | 1 | Has been deferred indefinitely |

### Safe to Consolidate (same coverage, less maintenance)
| Category | Before → After | Rationale |
|----------|---------------|-----------|
| Frontend tool page copypastes | ~90 tests → ~25 shared + 10 thin wrappers | Identical structure across 10 files |
| Backend `to_dict` tests | ~40 → ~1 parametrized | Boilerplate serialization |
| Backend `empty_input`/`empty_data` tests | ~12 → ~1 parametrized | Same edge case tested identically |
| Backend auth guard tests | ~8 copypastes → ~8 one-liners | Shared helper |

### Should Strengthen (keep but add assertions)
| Category | Count | Issue |
|----------|-------|-------|
| Status-code-only tests | 8 | Assert body content or remove |

### Total Estimated Savings
- **~80-100 redundant tests removable** without losing any coverage
- **~900 lines of frontend copypaste** consolidatable to ~200
- **~40 backend `to_dict` tests** consolidatable to 1 parametrized file
