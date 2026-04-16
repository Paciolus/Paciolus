# Sprints 610, 612–615 Details

> Archived from `tasks/todo.md` Active Phase on 2026-04-15.

---

### Sprint 610: LIKE Wildcard Escape In Admin + Client Search
**Status:** COMPLETE
**Source:** Critic — perf DoS + correctness
**File:** `backend/billing/admin_customers.py:107`, `backend/client_manager.py:305`
**Problem:** User input goes directly into `.ilike(f"%{search}%")` without escaping `%` / `_` / `\`. Superadmin searching `%` triggers full table scan on User+Organization. Type-ahead widget on a 50k-user table = DoS.
**Changes:**
- [x] Add LIKE-escape helper in `backend/shared/helpers.py` — `escape_like_wildcards()` escapes `\`, `%`, `_` in that order
- [x] Apply at both call-sites with `.ilike(pattern, escape="\\")`
- [x] Add tests: 6 unit tests for helper + 3 integration tests on `ClientManager.search_clients` (literal `%`, literal `_`, normal search still works)
- [x] 9 tests, all green

---

### Sprint 612: Constant-Time Passcode Compare
**Status:** COMPLETE
**Source:** Critic — timing consistency
**File:** `backend/routes/export_sharing.py:220`
**Problem:** `hashlib.sha256(...).hexdigest() != share.passcode_hash` uses Python `!=` which short-circuits. Inconsistent with `security_middleware.py:408` which uses `hmac.compare_digest`. Low real-world risk but violates the codebase's own constant-time comparison standard.
**Changes:**
- [x] Replace with `hmac.compare_digest(computed, stored)`
- [x] Grep remaining hex-digest `!=` comparisons in backend — none found; this was the only site

---

### Sprint 613: Anomaly Detection xfail Resolution (Bank Rec / TWM / Currency)
**Status:** COMPLETE
**Source:** Guardian — test debt on production tools
**File:** `backend/tests/test_tool_anomaly_detection.py:224, 263, 361` (and :92, 111, 150, 191, 210 runtime xfails)
**Problem:** Three `@pytest.mark.xfail` markers permanently disable anomaly detection tests for Bank Rec, Three-Way Match, and Currency engines. Reason cited: engine returns typed objects instead of dicts — "needs adapter". Runtime `pytest.xfail()` calls also hide detection gaps in revenue_contra_anomaly and duplicate_names. 3 of 12 production tools have zero anomaly-detection coverage.
**Changes:**
- [x] Bank rec: call `reconcile_bank_statement()` (raw rows → typed pipeline → BankRecResult), assert on summary counts — 4/4 pass
- [x] TWM: parse raw rows via `detect_*_columns()` + `parse_*()` into typed objects before `run_three_way_match()` — 4/4 pass
- [x] Currency: build `CurrencyRateTable` from raw rate dicts, call `convert_trial_balance()` — 2/5 pass, 3 xfail (engine doesn't validate zero/negative/stale rates — genuine capability gap, not a test-wiring issue)
- [x] All 3 permanent `@pytest.mark.xfail` decorators removed. 10 tests now pass (was 0). Runtime xfails for revenue/payroll/AR/FA/inventory remain (generator-engine alignment issues — separate from the typed-object adapter problem)
- [x] 10 passed, 3 xfailed (currency rate quality), 0 failed

---

### Sprint 614: Thread-Safe Classification Counter
**Status:** COMPLETE
**Source:** Guardian — unprotected shared state
**File:** `backend/audit/classification.py:140-157`
**Problem:** Module-level `_csv_type_log_count` mutated without lock. Under Gunicorn multi-worker two requests can double-increment, cap becomes unreliable. Violates "no unprotected shared state" rule.
**Changes:**
- [x] Wrapped counter in `threading.Lock()` with double-checked locking pattern (check-before-lock + check-inside-lock avoids lock acquisition on the hot path after the 5th call)

---

### Sprint 615: Sentry before_send Hook Hardening
**Status:** COMPLETE
**Source:** Guardian — zero-storage leak risk
**File:** `backend/main.py:84-88`
**Problem:** `_before_send` strips `event["request"]["data"]` only. Misses `query_string`, `contexts`, `extra`. Future `sentry_sdk.set_context()` / `set_extra()` callsites would bypass the strip. Not defensive against additions.
**Changes:**
- [x] Strip `event["request"]["query_string"]` via `req.pop("query_string", None)`
- [x] Filter `event["extra"]` against `_SAFE_EXTRA_KEYS` allowlist
- [x] Filter `event["contexts"]` against `_SAFE_CONTEXT_KEYS` allowlist
- [x] Updated test suite: 8 tests (3 updated + 3 new: query_string strip, unsafe extra, unsafe contexts)

---

