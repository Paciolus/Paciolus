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
)


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
    result = subprocess.run(
        cmd_json, cwd=str(BACKEND_ROOT), capture_output=True, text=True, timeout=1200,
    )

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
    if "unrecognized arguments" in result.stderr or result.returncode == 4:
        cmd_plain = [str(python_bin), "-m", "pytest", "--tb=no", "-q"]
        result = subprocess.run(
            cmd_plain, cwd=str(BACKEND_ROOT), capture_output=True, text=True, timeout=1200,
        )

    # Parse stdout summary line
    output = result.stdout + "\n" + result.stderr
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


def _run_frontend_tests() -> dict:
    """Run Jest and capture summary."""
    cmd = ["npm", "test", "--", "--watchAll=false", "--json"]
    result = subprocess.run(
        cmd, cwd=str(FRONTEND_ROOT), capture_output=True, text=True,
        timeout=300, shell=True,
    )

    passed = failed = 0
    duration = 0.0

    # Try JSON parse first
    stdout = result.stdout
    try:
        # Jest --json outputs JSON to stdout
        data = json.loads(stdout)
        passed = data.get("numPassedTests", 0)
        failed = data.get("numFailedTests", 0)
        duration = (data.get("testResults", [{}])[0].get("endTime", 0)
                    - data.get("startTime", 0)) / 1000 if data.get("startTime") else 0
        return {"passed": passed, "failed": failed, "duration_s": round(duration, 1)}
    except (json.JSONDecodeError, KeyError, IndexError):
        pass

    # Fallback: parse summary line from stderr (Jest writes summaries to stderr)
    combined = stdout + "\n" + result.stderr
    # Pattern: "Tests:       1339 passed, 1339 total"
    m = re.search(r"Tests:\s+(?:(\d+)\s+failed,\s+)?(\d+)\s+passed", combined)
    if m:
        failed = int(m.group(1) or 0)
        passed = int(m.group(2))
    m_time = re.search(r"Time:\s+([\d.]+)\s*s", combined)
    if m_time:
        duration = float(m_time.group(1))

    return {"passed": passed, "failed": failed, "duration_s": round(duration, 1)}


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
    if collection_error:
        status = "red"
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
    summary_parts.append(
        f"Frontend: {frontend['passed']} passed / {frontend['failed']} failed in {frontend['duration_s']}s."
    )
    if new_failures:
        summary_parts.append(f"{len(new_failures)} new failure(s) since yesterday.")
    if resolved:
        summary_parts.append(f"{len(resolved)} failure(s) resolved.")

    result = {
        "agent": "qa_warden",
        "status": status,
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
