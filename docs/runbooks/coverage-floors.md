# Coverage Floors Runbook

**Sprint:** 723

The repo enforces two layers of coverage discipline in CI:

1. **Aggregate floor** — `pytest --cov-fail-under=80` blocks any PR whose
   total backend coverage drops below 80%. Fast, file-agnostic, shipped
   pre-Sprint-723.
2. **Per-file floors** — Sprint 723 added `backend/coverage_floors.toml`
   and `scripts/check_coverage_floors.py`, which fail CI when any of the
   ~10 worst-covered production-critical files drops below its declared
   floor. The aggregate gate misses targeted regressions because moving
   coverage *between* files leaves the average unchanged; the per-file
   gate fixes that.

This runbook covers the per-file gate.

## 1. Architecture

| Component | Path | Purpose |
|---|---|---|
| Floor declarations | `backend/coverage_floors.toml` | Forward-slash file path → minimum percent. Comments explain *why* each file is on the list. |
| Checker script | `scripts/check_coverage_floors.py` | Reads floors + `coverage.json`. Exits non-zero on any breach. |
| CI integration | `.github/workflows/ci.yml` (`backend-tests` job, `backend-tests-postgres` job) | Runs after `pytest --cov-report=json:coverage.json`. |
| Tests | `backend/tests/test_coverage_floors.py` | 26 tests covering TOML loading, path normalization, breach detection, CLI exit codes. |

## 2. Daily flow

A PR-time CI failure on the per-file gate looks like:

```
Coverage Floor Check — 9 floor(s) configured
  [FAIL] excel_generator.py: 41.20% < 44%
  [ OK ] billing/webhook_handler.py: 60.10% >= 58%
  ...

FAILURES (1):
  ✗ excel_generator.py: 41.20% below floor 44% (deficit 2.80pp)
```

The PR introduced a regression on `excel_generator.py`. Either:
- (most common) restore the test that was removed / fix the test that
  started failing silently, or
- (rare, justified) make the case in the PR that this regression is
  intentional — see §4 *Lowering a floor*.

## 3. Raising a floor (the natural cadence)

After landing backfill tests that lift coverage on a floored file:

1. Run `pytest --cov --cov-report=json:coverage.json` locally.
2. Read the new `percent_covered` for the target file from `coverage.json`.
3. Edit `backend/coverage_floors.toml` and set the floor to
   `floor(new_pct - 1)` so a tiny coverage shift on a future PR doesn't
   false-fail CI.
4. Commit the floors edit alongside the backfill tests in the same PR.

The floor only ratchets up — it never drifts down silently.

## 4. Lowering a floor (rare, requires justification)

Lowering a floor requires:
1. A CODEOWNERS-approved PR with the rationale in the commit message.
2. The PR description must explain why the regression is intentional
   (e.g., scope reduction, code path being removed, hand-off to a
   different module).

A bare "make CI green" lowering is not acceptable — that's the failure
mode the gate exists to prevent. If you are tempted to lower a floor
because a test was deleted, restore the test instead.

## 5. Adding a new floor

When a new high-risk module lands (parser, generator, route handler with
security implications, billing code path, anything in `backend/billing/`,
`backend/routes/`, `backend/security_*`, or any new `*_engine.py` /
`*_memo_generator.py`):

1. Run pytest with coverage and read `percent_covered` for the new file.
2. Add an entry to `backend/coverage_floors.toml`:
   ```toml
   "your_new_module.py" = N    # current N+1.X
   ```
3. Briefly comment why the file is on the floors list (vs only the
   aggregate gate) — typically "first-touch parser", "billing code path",
   or "route handler with security implications".

The floor doesn't have to be high — even setting it at the current level
prevents a silent slow-bleed regression.

## 6. Path matching

Floor paths use forward slashes (`billing/webhook_handler.py`). The
checker normalizes both sides:

- Backslashes (Windows local dev) → forward slashes
- Lowercased for case-insensitive Windows filesystems
- `./` prefix stripped

Both the floors file and the coverage report can use either separator;
the checker matches them up.

## 7. Common failure modes

### 7a. File renamed or moved
Symptom: `[FAIL] foo.py: not present in coverage report (file renamed or excluded?)`

Action: update the floor entry to the new path, or remove the entry if
the file was deleted.

For multi-PR rename windows, run the checker with `--missing-ok` to
downgrade missing-file failures to warnings while the rename lands.

### 7b. Aggregate gate green but per-file gate red
This is the gate working as designed. Coverage shifted between files
without changing the total; the per-file gate caught the targeted drop.
Restore the deleted/disabled test on the floored file.

### 7c. New file missing a floor entry
Sprint 723 doesn't yet auto-detect new high-risk modules. The floors list
is curated. If a reviewer notices a new high-risk module without a floor,
ask the PR author to add one (§5). A future enhancement (Sprint 723b?)
can add an AST-based "new high-risk module without floor" detection.

## 8. Why TOML, not YAML

The Sprint 723 plan called for `coverage_floors.yaml`. We shipped TOML
because:
- Python 3.12 has `tomllib` in the stdlib — no `pyyaml` dependency added
  to backend requirements.
- TOML's commenting + key-quoting matches the use case (file paths as
  keys with `.` and `/` characters need quoting in both formats; TOML
  inline-table comments are more readable than YAML's).

The format is internal to CI — the swap doesn't affect any caller.

## 9. Related

- Sprint 599: original `coverage_sentinel` advisory nightly artifact
  (still runs; this Sprint 723 gate is the PR-time complement).
- Sprint 722: memory budget — same pattern (probe + soft threshold +
  CI gate at the chokepoint).
- Sprint 712: nightly false-green incident — read alongside this when
  interpreting CI signal.
