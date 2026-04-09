"""Report Auditor — runs Meridian smoke tests and tracks known bug status."""

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

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
from scripts.overnight.config import (
    BACKEND_ROOT,
    BASELINE_FILE,
    BUG_KEYWORDS,
    KNOWN_BUGS,
    REPORTS_DIR,
    SYSTEM_PYTHON,
    TODAY,
)


def _run_meridian_tests() -> tuple[int, int, list[str], str]:
    """Run pytest filtered to Meridian tests. Returns (passed, failed, failures, raw_output)."""
    cmd = [
        str(SYSTEM_PYTHON), "-m", "pytest",
        "tests/", "-k", "meridian or Meridian",
        "--tb=short", "-q",
    ]
    result = subprocess.run(
        cmd, cwd=str(BACKEND_ROOT), capture_output=True, text=True, timeout=600,
    )
    output = result.stdout + "\n" + result.stderr

    passed = failed = 0
    failures: list[str] = []

    # Parse summary line
    m = re.search(
        r"(\d+)\s+passed(?:,\s*(\d+)\s+failed)?", output,
    )
    if m:
        passed = int(m.group(1))
        failed = int(m.group(2) or 0)

    # Collect failure names
    for line in output.splitlines():
        stripped = line.strip()
        if stripped.startswith("FAILED "):
            failures.append(stripped.replace("FAILED ", "").strip())

    return passed, failed, failures, output


def _scan_source_for_bug(bug_id: str, keywords: list[str]) -> bool:
    """Scan backend source for patterns associated with a known bug."""
    scan_dirs = [
        BACKEND_ROOT / "services" / "audit",
        BACKEND_ROOT / "shared" / "report_standardization",
        BACKEND_ROOT / "shared",
    ]
    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            continue
        for py_file in scan_dir.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore").lower()
                for kw in keywords:
                    if kw.lower() in content:
                        return True
            except OSError:
                continue
    return False


def _check_bug_status(
    bug_id: str, keywords: list[str], test_output: str, prev_entry: dict
) -> tuple[str, str | None]:
    """Determine bug status from test output, source scan, and history.

    Returns (status, possibly_fixed_since) where status is one of:
      CONFIRMED_OPEN, POSSIBLY_FIXED, CLOSED

    Promotion rule: POSSIBLY_FIXED for 3+ consecutive days → CLOSED.
    Once CLOSED, stays CLOSED unless keywords reappear (regression).
    """
    output_lower = test_output.lower()

    # Check if any test failure mentions bug keywords
    in_failures = any(kw.lower() in output_lower for kw in keywords)
    if in_failures:
        return "CONFIRMED_OPEN", None

    # Check source code for patterns
    in_source = _scan_source_for_bug(bug_id, keywords)
    if in_source:
        return "CONFIRMED_OPEN", None

    # Not found anywhere — either POSSIBLY_FIXED or promoted to CLOSED
    prev_status = prev_entry.get("status", "")
    prev_since = prev_entry.get("possibly_fixed_since")

    if prev_status == "CLOSED":
        # Stay CLOSED (no regression detected)
        return "CLOSED", None

    if prev_status == "POSSIBLY_FIXED" and prev_since:
        # Check if 3+ days have elapsed since first marked POSSIBLY_FIXED
        try:
            from datetime import date, timedelta

            since_date = date.fromisoformat(prev_since)
            if date.today() - since_date >= timedelta(days=3):
                return "CLOSED", None
        except (ValueError, TypeError):
            pass
        return "POSSIBLY_FIXED", prev_since

    # First time reaching POSSIBLY_FIXED — start the clock
    return "POSSIBLY_FIXED", TODAY


def _load_previous_bug_status() -> dict:
    """Load yesterday's bug status from baseline."""
    if BASELINE_FILE.exists():
        try:
            baseline = json.loads(BASELINE_FILE.read_text(encoding="utf-8"))
            return baseline.get("report_auditor", {}).get("bug_tracker", {})
        except (json.JSONDecodeError, KeyError):
            pass
    return {}


def _save_to_baseline(bug_tracker: dict) -> None:
    """Persist bug tracker to baseline file."""
    baseline = {}
    if BASELINE_FILE.exists():
        try:
            baseline = json.loads(BASELINE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, KeyError):
            pass
    baseline["report_auditor"] = {"date": TODAY, "bug_tracker": bug_tracker}
    BASELINE_FILE.write_text(json.dumps(baseline, indent=2), encoding="utf-8")


def run() -> dict:
    """Execute Report Auditor and return structured results."""
    t0 = time.time()

    passed, failed, failures, raw_output = _run_meridian_tests()

    # Check each known bug
    prev_status = _load_previous_bug_status()
    bug_tracker: dict[str, dict] = {}
    open_count = 0

    for bug_id, description in KNOWN_BUGS.items():
        keywords = BUG_KEYWORDS[bug_id]
        prev_entry = prev_status.get(bug_id, {})
        status, possibly_fixed_since = _check_bug_status(
            bug_id, keywords, raw_output, prev_entry
        )

        prev_st = prev_entry.get("status", "")
        changed_today = bool(prev_st and prev_st != status)

        entry: dict = {
            "description": description,
            "status": status,
            "changed_today": changed_today,
        }
        if possibly_fixed_since:
            entry["possibly_fixed_since"] = possibly_fixed_since
        bug_tracker[bug_id] = entry
        if status == "CONFIRMED_OPEN":
            open_count += 1

    _save_to_baseline(bug_tracker)

    # Determine overall status
    if failed > 0:
        overall = "red"
    elif open_count > 3:
        overall = "yellow"
    else:
        overall = "green"

    result = {
        "agent": "report_auditor",
        "status": overall,
        "meridian_tests": {"passed": passed, "failed": failed, "failures": failures},
        "bug_tracker": bug_tracker,
        "open_bug_count": open_count,
        "summary": (
            f"Meridian tests: {passed} passed, {failed} failed. "
            f"{open_count}/{len(KNOWN_BUGS)} known bugs confirmed open."
        ),
    }

    out_path = REPORTS_DIR / f".report_auditor_{TODAY}.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    elapsed = round(time.time() - t0, 1)
    print(f"Report Auditor completed in {elapsed}s — status: {overall}")
    return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
