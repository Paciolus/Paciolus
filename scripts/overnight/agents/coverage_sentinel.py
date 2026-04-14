"""Coverage Sentinel — runs pytest --cov against the backend suite and reports deltas.

Sprint 599: replaces the LLM-introspected "coverage gap" analysis (which was
hallucination-prone) with a deterministic pytest --cov --cov-report=json run.
Tracks a 7-day rolling percent_covered in baseline.json so the daily brief can
show coverage drift.

Output: reports/nightly/.coverage_sentinel_<DATE>.json — conforms to the same
dict shape as the other agents (agent, status, summary, + metrics).
"""

import io
import json
import subprocess
import sys
import time
from pathlib import Path
from statistics import mean

# Force UTF-8 stdout on Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Allow running as standalone script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
from scripts.overnight.config import (
    BACKEND_ROOT,
    BASELINE_FILE,
    REPORTS_DIR,
    SYSTEM_PYTHON,
    TODAY,
)

# ── Tuning knobs ───────────────────────────────────────────────────────────
# Thresholds for status color. These are chosen against the observed baseline
# (~92.8% in Feb 2026) with some headroom. Adjust if the project baseline
# moves materially.
FLOOR_GREEN_PCT = 90.0          # anything at or above → green (absent regression)
FLOOR_YELLOW_PCT = 85.0         # anything below → red
DRIFT_WARN_PP = 0.5             # warn if current > 0.5pp below 7-day mean
DRIFT_FAIL_PP = 2.0             # fail if current > 2pp below 7-day mean
ROLLING_WINDOW_DAYS = 7

PYTEST_TIMEOUT_S = 1500         # 25 min ceiling for pytest run w/ coverage


def _run_pytest_with_coverage() -> tuple[dict | None, str]:
    """Run pytest --cov=. and return (parsed coverage.json dict, stderr tail)."""
    cov_report = BACKEND_ROOT / ".coverage_sentinel_tmp.json"
    # Remove any prior run's artifact so a crash can't silently reuse stale data
    if cov_report.exists():
        cov_report.unlink()

    cmd = [
        str(SYSTEM_PYTHON), "-m", "pytest",
        "--tb=no", "-q",
        "--cov=.",
        f"--cov-report=json:{cov_report}",
        "--cov-report=",  # Suppress terminal report; we parse the JSON only
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=str(BACKEND_ROOT),
            capture_output=True,
            text=True,
            timeout=PYTEST_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        return None, f"pytest --cov timed out after {PYTEST_TIMEOUT_S}s"

    if not cov_report.exists():
        # Coverage JSON didn't materialize — surface stderr tail for debugging
        tail = (result.stderr or result.stdout or "").strip().splitlines()[-15:]
        return None, "\n".join(tail)

    try:
        data = json.loads(cov_report.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, KeyError) as exc:
        return None, f"failed to parse coverage.json: {exc}"
    finally:
        cov_report.unlink(missing_ok=True)

    return data, ""


def _load_history() -> list[dict]:
    """Return the rolling list of (date, percent_covered) entries."""
    if not BASELINE_FILE.exists():
        return []
    try:
        baseline = json.loads(BASELINE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, KeyError):
        return []
    entry = baseline.get("coverage_sentinel", {})
    history = entry.get("history", [])
    if isinstance(history, list):
        # Defensive: filter malformed entries
        return [
            h for h in history
            if isinstance(h, dict) and "date" in h and "percent_covered" in h
        ]
    return []


def _save_history(history: list[dict]) -> None:
    """Persist the rolling history back to baseline.json."""
    baseline: dict = {}
    if BASELINE_FILE.exists():
        try:
            baseline = json.loads(BASELINE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, KeyError):
            baseline = {}

    baseline["coverage_sentinel"] = {
        "date": TODAY,
        "history": history,
    }
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    BASELINE_FILE.write_text(json.dumps(baseline, indent=2), encoding="utf-8")


def _top_uncovered_files(files: dict, limit: int = 10) -> list[dict]:
    """Rank files by uncovered line count, descending."""
    ranked: list[dict] = []
    for path, entry in files.items():
        summary = entry.get("summary", {}) if isinstance(entry, dict) else {}
        missing = summary.get("missing_lines", 0)
        num_statements = summary.get("num_statements", 0)
        pct = summary.get("percent_covered", 0.0)
        if num_statements == 0:
            continue
        ranked.append({
            "path": path,
            "percent_covered": round(pct, 2),
            "missing_lines": missing,
            "num_statements": num_statements,
        })
    ranked.sort(key=lambda r: (r["missing_lines"], -r["percent_covered"]), reverse=True)
    return ranked[:limit]


def _classify_status(current_pct: float, delta_pp: float | None) -> tuple[str, list[str]]:
    """Map the current coverage + drift to green/yellow/red with reasons."""
    reasons: list[str] = []
    status = "green"

    if current_pct < FLOOR_YELLOW_PCT:
        status = "red"
        reasons.append(f"coverage {current_pct:.2f}% below red floor {FLOOR_YELLOW_PCT}%")
    elif current_pct < FLOOR_GREEN_PCT:
        status = "yellow"
        reasons.append(f"coverage {current_pct:.2f}% below green floor {FLOOR_GREEN_PCT}%")

    if delta_pp is not None:
        if delta_pp <= -DRIFT_FAIL_PP:
            status = "red"
            reasons.append(f"coverage dropped {abs(delta_pp):.2f}pp vs 7-day mean")
        elif delta_pp <= -DRIFT_WARN_PP and status == "green":
            status = "yellow"
            reasons.append(f"coverage drifted {abs(delta_pp):.2f}pp below 7-day mean")

    return status, reasons


def run() -> dict:
    """Execute Coverage Sentinel and return structured results."""
    t0 = time.time()

    cov_data, err = _run_pytest_with_coverage()
    if cov_data is None:
        result = {
            "agent": "coverage_sentinel",
            "status": "red",
            "error": err or "pytest --cov produced no coverage.json",
            "summary": "Coverage run failed — see reports/nightly/.run_log for details.",
        }
        out_path = REPORTS_DIR / f".coverage_sentinel_{TODAY}.json"
        out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        elapsed = round(time.time() - t0, 1)
        print(f"Coverage Sentinel FAILED in {elapsed}s — {err[:120]}")
        return result

    totals = cov_data.get("totals", {})
    files = cov_data.get("files", {}) or {}

    current_pct = float(totals.get("percent_covered", 0.0))
    covered_lines = int(totals.get("covered_lines", 0))
    num_statements = int(totals.get("num_statements", 0))
    missing_lines = int(totals.get("missing_lines", 0))

    # Rolling window maintenance
    history = _load_history()
    # Drop any prior entry for TODAY so reruns don't double-count
    history = [h for h in history if h.get("date") != TODAY]
    prior_pcts = [float(h["percent_covered"]) for h in history][-ROLLING_WINDOW_DAYS:]
    rolling_mean = round(mean(prior_pcts), 2) if prior_pcts else None
    delta_pp = round(current_pct - rolling_mean, 2) if rolling_mean is not None else None

    # Append today and trim to window
    history.append({"date": TODAY, "percent_covered": round(current_pct, 2)})
    history = history[-ROLLING_WINDOW_DAYS * 2:]  # keep 14 days for headroom
    _save_history(history)

    status, status_reasons = _classify_status(current_pct, delta_pp)
    top_uncovered = _top_uncovered_files(files, limit=10)

    summary_parts = [
        f"Backend coverage: {current_pct:.2f}% "
        f"({covered_lines:,}/{num_statements:,} statements, "
        f"{missing_lines:,} uncovered).",
    ]
    if rolling_mean is not None:
        sign = "+" if (delta_pp or 0) >= 0 else ""
        summary_parts.append(
            f"7-day mean: {rolling_mean:.2f}% ({sign}{delta_pp:.2f}pp)."
        )
    else:
        summary_parts.append("7-day mean: building baseline.")
    if status_reasons:
        summary_parts.append("Flags: " + "; ".join(status_reasons) + ".")

    result = {
        "agent": "coverage_sentinel",
        "status": status,
        "percent_covered": round(current_pct, 2),
        "covered_lines": covered_lines,
        "num_statements": num_statements,
        "missing_lines": missing_lines,
        "rolling_mean_pct": rolling_mean,
        "delta_pp": delta_pp,
        "rolling_window_days": ROLLING_WINDOW_DAYS,
        "history": history,
        "top_uncovered_files": top_uncovered,
        "reasons": status_reasons,
        "summary": " ".join(summary_parts),
    }

    out_path = REPORTS_DIR / f".coverage_sentinel_{TODAY}.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    elapsed = round(time.time() - t0, 1)
    print(
        f"Coverage Sentinel completed in {elapsed}s — status: {status} "
        f"({current_pct:.2f}% covered)"
    )
    return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, default=str))
