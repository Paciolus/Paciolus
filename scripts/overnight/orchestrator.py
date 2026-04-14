"""Orchestrator — single entry point for the Paciolus overnight agent system.

Run by Windows Task Scheduler at 2:00 AM daily.
Usage:
    python scripts/overnight/orchestrator.py            # Full run
    python scripts/overnight/orchestrator.py --dry-run  # Print plan without executing
"""

import datetime
import io
import json
import subprocess
import sys
import time
from pathlib import Path

# Force UTF-8 stdout on Windows to handle emoji in print()
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ── Bootstrap ──────────────────────────────────────────────────────────────
PROJECT_ROOT = Path("D:/Dev/Paciolus")
PYTHON_BIN = str(PROJECT_ROOT / "backend/venv/Scripts/python.exe")
REPORTS_DIR = PROJECT_ROOT / "reports/nightly"
TODAY = datetime.date.today().isoformat()

# Load environment from .env files before importing config
def _load_env() -> None:
    """Load .env files using python-dotenv."""
    try:
        from dotenv import load_dotenv
        # .env.overnight takes precedence
        overnight_env = PROJECT_ROOT / ".env.overnight"
        if overnight_env.exists():
            load_dotenv(overnight_env, override=True)
        # Backend .env as fallback
        backend_env = PROJECT_ROOT / "backend" / ".env"
        if backend_env.exists():
            load_dotenv(backend_env, override=False)
    except ImportError:
        print("WARNING: python-dotenv not installed. Environment variables must be set externally.")


_load_env()

# ── Agent schedule ─────────────────────────────────────────────────────────
# Each entry: (agent_name, script_path, target_hour, target_minute)
# Coverage Sentinel (Sprint 599) is scheduled at 3:00 — after Scout, before
# Sprint Shepherd — because a full pytest --cov run takes ~13–16 min and
# needs a clear 25-min window. See AGENT_TIMEOUT_OVERRIDES for the longer
# subprocess timeout.
AGENT_SCHEDULE = [
    ("qa_warden",            "scripts/overnight/agents/qa_warden.py",            2,  0),
    ("report_auditor",       "scripts/overnight/agents/report_auditor.py",       2, 15),
    ("scout",                "scripts/overnight/agents/scout.py",                2, 45),
    ("coverage_sentinel",    "scripts/overnight/agents/coverage_sentinel.py",    3,  0),
    ("sprint_shepherd",      "scripts/overnight/agents/sprint_shepherd.py",      3, 30),
    ("dependency_sentinel",  "scripts/overnight/agents/dependency_sentinel.py",  3, 45),
]

# Per-agent subprocess timeout override (seconds). Agents not listed use
# the default below. Coverage Sentinel re-runs the full backend test suite
# with coverage instrumentation, which is ~1.3–1.5x slower than the base
# QA Warden run.
DEFAULT_AGENT_TIMEOUT_S = 900
AGENT_TIMEOUT_OVERRIDES = {
    "coverage_sentinel": 1700,  # 28 min — pytest --cov + margin
}

BRIEFING_COMPILER = ("briefing_compiler", "scripts/overnight/briefing_compiler.py", 4, 0)


class RunLog:
    """Simple file-based run log."""

    def __init__(self) -> None:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        self.path = REPORTS_DIR / f".run_log_{TODAY}.txt"
        self._lines: list[str] = []
        self.log(f"=== Paciolus Overnight Run — {TODAY} ===")
        self.log(f"Start time: {datetime.datetime.now().isoformat()}")

    def log(self, msg: str) -> None:
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {msg}"
        self._lines.append(line)
        print(line)

    def save(self) -> None:
        self.path.write_text("\n".join(self._lines), encoding="utf-8")


def _sleep_until(target_hour: int, target_minute: int, log: RunLog) -> None:
    """Sleep until the target wall-clock time. Skip if already past."""
    now = datetime.datetime.now()
    target = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
    if target <= now:
        log.log(f"  Target {target_hour:02d}:{target_minute:02d} already passed — starting immediately.")
        return
    delta = (target - now).total_seconds()
    log.log(f"  Sleeping {delta:.0f}s until {target_hour:02d}:{target_minute:02d}...")
    time.sleep(delta)


def _run_agent(name: str, script: str, log: RunLog, dry_run: bool = False) -> bool:
    """Run a single agent as a subprocess. Returns True on success."""
    script_path = str(PROJECT_ROOT / script)
    log.log(f"--- Agent: {name} ---")

    if dry_run:
        log.log(f"  [DRY RUN] Would execute: {PYTHON_BIN} {script_path}")
        return True

    log.log(f"  Executing: {PYTHON_BIN} {script_path}")
    t0 = time.time()
    timeout_s = AGENT_TIMEOUT_OVERRIDES.get(name, DEFAULT_AGENT_TIMEOUT_S)

    try:
        result = subprocess.run(
            [PYTHON_BIN, script_path],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        elapsed = round(time.time() - t0, 1)

        if result.stdout.strip():
            for line in result.stdout.strip().splitlines()[-5:]:
                log.log(f"  stdout: {line}")

        if result.returncode != 0:
            log.log(f"  FAILED (exit code {result.returncode}) after {elapsed}s")
            if result.stderr.strip():
                for line in result.stderr.strip().splitlines()[-10:]:
                    log.log(f"  stderr: {line}")
            return False

        log.log(f"  Completed successfully in {elapsed}s")
        return True

    except subprocess.TimeoutExpired:
        log.log(f"  TIMEOUT after {timeout_s}s — killed subprocess")
        return False
    except Exception as e:
        log.log(f"  EXCEPTION: {e}")
        return False


def main() -> None:
    """Run the full overnight agent sequence."""
    dry_run = "--dry-run" in sys.argv

    log = RunLog()
    if dry_run:
        log.log("*** DRY RUN MODE — no agents will be executed ***")

    total_start = time.time()
    success_count = 0

    for name, script, hour, minute in AGENT_SCHEDULE:
        _sleep_until(hour, minute, log)
        ok = _run_agent(name, script, log, dry_run)
        if ok:
            success_count += 1
        # 2 min buffer between agents (skip if already past next target)
        if not dry_run:
            time.sleep(min(120, 5))  # In practice, sleep briefly; wall-clock sync handles rest

    # Briefing compiler
    bname, bscript, bhour, bminute = BRIEFING_COMPILER
    _sleep_until(bhour, bminute, log)
    ok = _run_agent(bname, bscript, log, dry_run)
    if ok:
        success_count += 1

    total_elapsed = round(time.time() - total_start, 1)
    total_agents = len(AGENT_SCHEDULE) + 1  # +1 for briefing compiler
    log.log(
        f"=== Run complete: {success_count}/{total_agents} agents succeeded "
        f"in {total_elapsed}s ==="
    )
    log.save()

    sys.exit(0)


if __name__ == "__main__":
    main()
