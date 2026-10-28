"""QA Warden — runs both test suites and compares to yesterday's baseline."""

import io
import json
import re
import subprocess
import sys
import time
from pathlib import Path

# Force UTF-8 stdout on Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Allow running as standalone script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
from scripts.overnight.config import (
    BACKEND_ROOT,
    BASELINE_FILE,
    FRONTEND_ROOT,
    PYTHON_BIN,
    REPORTS_DIR,
    SYSTEM_PYTHON,
    TODAY,
    run_stamp,
)

# Budget for the backend pytest subprocess, in seconds.
#
# MUST stay below `orchestrator.AGENT_TIMEOUT_OVERRIDES["qa_warden"]` (1700s),
# which also has to cover the Jest run (300s) and process overhead — otherwise
# the outer timeout kills the agent before the inner one can report *why* it
# was slow. `tests/test_overnight_timeouts.py` asserts that ordering.
PYTEST_TIMEOUT_S = 1200

# Budget for the frontend Jest subprocess.
JEST_TIMEOUT_S = 300


def _run_backend_tests() -> dict:
    """Run pytest and capture summary."""
    json_report = REPORTS_DIR / ".pytest_results.json"

    # Sprint 712: venv is the source of truth for backend deps (installed from
    # requirements.txt). System Python is a degraded fallback for fresh-checkout
    # environments where the venv hasn't been provisioned. The older SYSTEM_PYTHON
    # path missed deps added after Sprint 675 (e.g. argon2-cffi added Sprint 697),
    # which caused the 2026-04-22 nightly false-green.
    python_bin = PYTHON_BIN if PYTHON_BIN.exists() else SYSTEM_PYTHON

    # Try with --json-report first
    cmd_json = [
        str(python_bin), "-m", "pytest",
        "--tb=no", "-q",
        "--json-report", f"--json-report-file={json_report}",
    ]
    # Sprint 802: catch the timeout rather than letting it propagate.
    #
    # The agent crashing is already reported honestly — the orchestrator logs
    # the failure and `briefing_compiler` renders a missing agent as RED with
    # `status: "DID_NOT_RUN"`. But the brief could only say *that* the agent
    # died, not *why*. A suite that has outgrown its budget and a suite that
    # hangs on a deadlock want very different responses at 02:00.
    #
    # Headroom at the time of writing: 690.7s observed against this 1200s
    # budget (1.74x) at 9,126 collected tests, i.e. ~76ms/test. The cap is
    # reached somewhere near 15,800 tests. That is not close, but the suite
    # grew by 114 in a single session, so it is a clock rather than a
    # non-issue (lessons.md, Sprint 674).
    try:
        result = subprocess.run(
            cmd_json, check=False, cwd=str(BACKEND_ROOT), capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=PYTEST_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        return {
            "passed": 0, "failed": 0, "errors": 0, "duration_s": float(PYTEST_TIMEOUT_S),
            "failing_tests": [],
            "collection_error": (
                f"Backend pytest exceeded its {PYTEST_TIMEOUT_S}s budget and was killed. "
                f"This is a 'did not run', not a pass: no result was produced. Either the "
                f"suite has outgrown the budget (raise PYTEST_TIMEOUT_S here and the "
                f"matching qa_warden entry in orchestrator.AGENT_TIMEOUT_OVERRIDES, which "
                f"must stay larger) or a test is hanging."
            ),
        }

    passed = failed = errors = 0
    duration = 0.0
    failing_tests: list[str] = []

    # Check if json-report worked
    if json_report.exists():
        try:
            data = json.loads(json_report.read_text(encoding="utf-8"))
            summary = data.get("summary", {})
            passed = summary.get("passed", 0)
            failed = summary.get("failed", 0)
            errors = summary.get("error", 0)
            duration = summary.get("duration", 0.0)
            for t in data.get("tests", []):
                if t.get("outcome") in ("failed", "error"):
                    failing_tests.append(t.get("nodeid", "unknown"))
            return {
                "passed": passed, "failed": failed, "errors": errors,
                "duration_s": round(duration, 1), "failing_tests": failing_tests,
                "collection_error": None,
            }
        except (json.JSONDecodeError, KeyError):
            pass

    # json-report plugin not installed or failed — retry without it
    if "unrecognized arguments" in (result.stderr or "") or result.returncode == 4:
        cmd_plain = [str(python_bin), "-m", "pytest", "--tb=no", "-q"]
        try:
            result = subprocess.run(
                cmd_plain, check=False, cwd=str(BACKEND_ROOT), capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=PYTEST_TIMEOUT_S,
            )
        except subprocess.TimeoutExpired:
            return {
                "passed": 0, "failed": 0, "errors": 0, "duration_s": float(PYTEST_TIMEOUT_S),
                "failing_tests": [],
                "collection_error": (
                    f"Backend pytest (no-json-report fallback) exceeded its "
                    f"{PYTEST_TIMEOUT_S}s budget and was killed."
                ),
            }

    # Parse stdout summary line
    output = (result.stdout or "") + "\n" + (result.stderr or "")
    # Pattern: "6531 passed, 2 failed, 1 error in 293.38s"
    m = re.search(
        r"(\d+)\s+passed(?:,\s*(\d+)\s+failed)?(?:,\s*(\d+)\s+error)?.*?in\s+([\d.]+)s",
        output,
    )
    if m:
        passed = int(m.group(1))
        failed = int(m.group(2) or 0)
        errors = int(m.group(3) or 0)
        duration = float(m.group(4))

    # Extract FAILED test names from short summary
    for line in output.splitlines():
        if line.startswith("FAILED "):
            failing_tests.append(line.replace("FAILED ", "").strip())

    # Reconcile: if FAILED lines found but summary said 0, trust the FAILED lines
    if failing_tests and failed == 0:
        failed = len(failing_tests)

    # Sprint 712: false-green guard. Collection errors (pytest exit 2) or
    # internal errors (exit 3) emit no "N passed in Xs" line, so the regex above
    # matches nothing and the caller would record the run as 0-passed / 0-failed
    # — which the status classifier treats as GREEN. Exit code 5 ("no tests
    # collected") is a legitimate empty-subset signal and stays unescalated.
    collection_error: str | None = None
    if (passed + failed + errors == 0) and result.returncode not in (0, 5):
        tail_lines = output.strip().splitlines()[-15:]
        collection_error = "\n".join(tail_lines) or (
            f"pytest exited {result.returncode} with no parseable summary"
        )

    return {
        "passed": passed, "failed": failed, "errors": errors,
        "duration_s": round(duration, 1), "failing_tests": failing_tests,
        "collection_error": collection_error,
    }


def _jest_did_not_run(reason: str) -> dict:
    """A frontend result that cannot be mistaken for a pass (Sprint 854)."""
    return {"passed": 0, "failed": 0, "duration_s": 0.0, "did_not_run": reason}


def _parse_jest_json(data: dict) -> dict:
    passed = data.get("numPassedTests", 0)
    failed = data.get("numFailedTests", 0)
    start = data.get("startTime") or 0
    ends = [r.get("endTime", 0) for r in data.get("testResults", []) if r.get("endTime")]
    duration = (max(ends) - start) / 1000 if start and ends else 0.0
    return {"passed": passed, "failed": failed, "duration_s": round(duration, 1), "did_not_run": None}


def _run_frontend_tests() -> dict:
    """Run Jest and capture summary.

    Sprint 854 — the 2026-10-28 crash. `subprocess.run(..., text=True)` with no
    `encoding` decodes with the locale codepage (cp1252 on the nightly box).
    Jest prints UTF-8 glyphs such as `●` (bytes E2 97 8F; 0x8F is undefined in
    cp1252), so the stdout reader thread died with a UnicodeDecodeError and
    CPython's Windows `communicate()` returned `stdout=None`. `json.loads(None)`
    then raised TypeError and the agent wrote no sentinel at all. Fixes: decode
    as UTF-8 with replacement, have Jest write its JSON to a file instead of
    sharing stdout with npm's banner, and turn every no-result path into an
    explicit "did not run" rather than a crash or a silent 0/0.
    """
    json_out = REPORTS_DIR / ".jest_results.json"
    try:
        json_out.unlink()
    except OSError:
        pass

    cmd = ["npm", "test", "--", "--watchAll=false", "--json", f"--outputFile={json_out}"]
    try:
        result = subprocess.run(
            cmd, check=False, cwd=str(FRONTEND_ROOT), capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=JEST_TIMEOUT_S, shell=True,
        )
    except subprocess.TimeoutExpired:
        return _jest_did_not_run(f"Jest exceeded its {JEST_TIMEOUT_S}s budget and was killed.")
    except OSError as e:
        return _jest_did_not_run(f"Jest could not be started: {e}")

    stdout = result.stdout or ""
    stderr = result.stderr or ""

    # 1. The results file Jest wrote itself.
    if json_out.exists():
        try:
            return _parse_jest_json(json.loads(json_out.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, AttributeError, TypeError):
            pass

    # 2. JSON on stdout (the pre-854 path, kept as a fallback).
    if stdout.strip():
        try:
            return _parse_jest_json(json.loads(stdout))
        except (json.JSONDecodeError, AttributeError, TypeError):
            pass

    # 3. The human summary line (Jest writes summaries to stderr).
    combined = stdout + "\n" + stderr
    # Pattern: "Tests:       1339 passed, 1339 total"
    m = re.search(r"Tests:\s+(?:(\d+)\s+failed,\s+)?(\d+)\s+passed", combined)
    if m:
        duration = 0.0
        m_time = re.search(r"Time:\s+([\d.]+)\s*s", combined)
        if m_time:
            duration = float(m_time.group(1))
        return {
            "passed": int(m.group(2)), "failed": int(m.group(1) or 0),
            "duration_s": round(duration, 1), "did_not_run": None,
        }

    tail = " | ".join([ln for ln in combined.strip().splitlines() if ln.strip()][-3:])
    return _jest_did_not_run(
        f"Jest produced no parseable result (exit {result.returncode})"
        + (f": {tail}" if tail else "; no output captured")
    )


def _load_baseline() -> dict:
    """Load yesterday's baseline if it exists."""
    if BASELINE_FILE.exists():
        try:
            return json.loads(BASELINE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, KeyError):
            pass
    return {}


def _save_baseline(backend: dict, frontend: dict) -> None:
    """Write today's results as the new baseline."""
    baseline = _load_baseline()
    baseline["qa_warden"] = {
        "date": TODAY,
        "backend": backend,
        "frontend": frontend,
    }
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    BASELINE_FILE.write_text(json.dumps(baseline, indent=2), encoding="utf-8")


def run() -> dict:
    """Execute QA Warden and return structured results."""
    t0 = time.time()
    stamp = run_stamp()

    backend = _run_backend_tests()
    frontend = _run_frontend_tests()

    # Compare to baseline
    baseline = _load_baseline()
    prev = baseline.get("qa_warden", {})
    prev_backend = prev.get("backend", {})
    prev_failing = set(prev_backend.get("failing_tests", []))
    curr_failing = set(backend.get("failing_tests", []))

    new_failures = sorted(curr_failing - prev_failing)
    resolved = sorted(prev_failing - curr_failing)

    backend["new_failures"] = new_failures
    backend["resolved"] = resolved

    # Determine status. Sprint 712: a collection_error signals that pytest
    # could not even enumerate the suite (e.g. missing runtime dep) — this MUST
    # escalate to red, even though failed+errors parse as zero. Hiding that
    # behind a green badge caused the 2026-04-22 false-green incident.
    total_failures = backend["failed"] + backend["errors"] + frontend["failed"]
    collection_error = backend.get("collection_error")
    frontend_did_not_run = frontend.get("did_not_run")
    # Sprint 854: a suite that ran zero tests verified nothing. That is not
    # GREEN — say so, rather than letting "0 failed" read as a pass.
    backend_empty = backend["passed"] + backend["failed"] + backend["errors"] == 0
    frontend_empty = frontend["passed"] + frontend["failed"] == 0
    if collection_error or frontend_did_not_run:
        status = "red"
    elif total_failures == 0 and (backend_empty or frontend_empty):
        status = "unverified"
    elif total_failures == 0:
        status = "green"
    elif new_failures:
        status = "red"
    else:
        status = "yellow"

    # Save updated baseline
    _save_baseline(backend, frontend)

    summary_parts = []
    if collection_error:
        # Lead with the collection failure — it's the most important signal.
        summary_parts.append(
            "Backend: pytest collection FAILED — see reports/nightly/.run_log for details."
        )
    else:
        summary_parts.append(
            f"Backend: {backend['passed']} passed / {backend['failed']} failed in {backend['duration_s']}s."
        )
    if frontend_did_not_run:
        summary_parts.append(f"Frontend: DID NOT RUN — {frontend_did_not_run}")
    else:
        summary_parts.append(
            f"Frontend: {frontend['passed']} passed / {frontend['failed']} failed in {frontend['duration_s']}s."
        )
    if status == "unverified":
        summary_parts.append("UNVERIFIED: a suite ran 0 tests, so nothing was checked.")
    if new_failures:
        summary_parts.append(f"{len(new_failures)} new failure(s) since yesterday.")
    if resolved:
        summary_parts.append(f"{len(resolved)} failure(s) resolved.")

    result = {
        "agent": "qa_warden",
        "status": status,
        **stamp,
        "backend": backend,
        "frontend": frontend,
        "summary": " ".join(summary_parts),
    }

    # Save agent output
    out_path = REPORTS_DIR / f".qa_warden_{TODAY}.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    elapsed = round(time.time() - t0, 1)
    print(f"QA Warden completed in {elapsed}s — status: {status}")
    return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
