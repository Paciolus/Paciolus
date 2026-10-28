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
RUN_MANIFEST_PATH = REPORTS_DIR / f".run_manifest_{TODAY}.json"
PREFLIGHT_PATH = REPORTS_DIR / f".env_preflight_{TODAY}.json"
REQUIREMENTS_FILE = PROJECT_ROOT / "backend/requirements.txt"
REQUIREMENTS_DEV_FILE = PROJECT_ROOT / "backend/requirements-dev.txt"

# Run as `python scripts/overnight/orchestrator.py`, sys.path[0] is
# scripts/overnight; the repo root is needed to import the `scripts` package.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
from scripts.overnight import env_parity


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
    "qa_warden": 1700,  # 28 min — internal budget is 1200s pytest + 300s jest + margin
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


# How much of a failed agent's stderr reaches the run log. Was 10 — on
# 2026-10-28 that cut off the head of QA Warden's traceback.
STDERR_TAIL_LINES = 25


def _run_agent(name: str, script: str, log: RunLog, dry_run: bool = False) -> dict:
    """Run a single agent as a subprocess.

    Returns an outcome record for the run manifest: ``outcome`` is one of
    ``ok`` / ``failed`` / ``timeout`` / ``exception`` / ``dry_run``.
    """
    script_path = str(PROJECT_ROOT / script)
    log.log(f"--- Agent: {name} ---")
    started_at = datetime.datetime.now().isoformat(timespec="seconds")

    def _outcome(outcome: str, elapsed: float = 0.0, exit_code: int | None = None,
                 detail: str | None = None) -> dict:
        return {"outcome": outcome, "started_at": started_at, "elapsed_s": elapsed,
                "exit_code": exit_code, "detail": detail}

    if dry_run:
        log.log(f"  [DRY RUN] Would execute: {PYTHON_BIN} {script_path}")
        return _outcome("dry_run")

    log.log(f"  Executing: {PYTHON_BIN} {script_path}")
    t0 = time.time()
    timeout_s = AGENT_TIMEOUT_OVERRIDES.get(name, DEFAULT_AGENT_TIMEOUT_S)

    try:
        # Sprint 854: decode as UTF-8. The locale default (cp1252) kills the
        # reader thread on some UTF-8 bytes and leaves stdout as None.
        result = subprocess.run(
            [PYTHON_BIN, script_path],
            check=False,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_s,
        )
        elapsed = round(time.time() - t0, 1)
        stdout = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()

        if stdout:
            for line in stdout.splitlines()[-5:]:
                log.log(f"  stdout: {line}")

        if result.returncode != 0:
            log.log(f"  FAILED (exit code {result.returncode}) after {elapsed}s")
            for line in stderr.splitlines()[-STDERR_TAIL_LINES:]:
                log.log(f"  stderr: {line}")
            last = stderr.splitlines()[-1] if stderr else "no stderr"
            return _outcome("failed", elapsed, result.returncode, last)

        log.log(f"  Completed successfully in {elapsed}s")
        return _outcome("ok", elapsed, 0)

    except subprocess.TimeoutExpired:
        log.log(f"  TIMEOUT after {timeout_s}s — killed subprocess")
        return _outcome("timeout", float(timeout_s), None, f"killed after {timeout_s}s")
    except Exception as e:
        log.log(f"  EXCEPTION: {e}")
        return _outcome("exception", round(time.time() - t0, 1), None, str(e))


class RunManifest:
    """Sprint 854: what this run tested, and how each step ended.

    Written at run start and after every step, so the briefing compiler (and a
    human the next morning) can tell an agent that crashed from one that never
    started, and can state the SHA + time the suites actually ran against —
    not whatever HEAD happens to be at 04:00.
    """

    def __init__(self, path: Path, dry_run: bool) -> None:
        self.path = path
        self.data: dict = {
            "date": TODAY,
            "started_at": datetime.datetime.now().isoformat(timespec="seconds"),
            "head_sha": _git_head_sha(),
            "dry_run": dry_run,
            "preflight": None,
            "agents": {},
        }

    def record(self, name: str, outcome: dict) -> None:
        self.data["agents"][name] = outcome
        self.save()

    def save(self) -> None:
        if self.data.get("dry_run"):
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")


def _git_head_sha() -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=str(PROJECT_ROOT), capture_output=True,
            text=True, check=True, timeout=30,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return None
    return completed.stdout.strip() or None


def _run_preflight(log: RunLog, dry_run: bool) -> dict:
    """Sync the venv from requirements, then verify the == pins (Sprint 854)."""
    log.log("--- Pre-flight: environment parity ---")
    if dry_run:
        log.log(f"  [DRY RUN] Would sync {PYTHON_BIN} from {REQUIREMENTS_DEV_FILE} and check == pins")
        return {"status": "dry_run", "reasons": [], "summary": "dry run"}
    result = env_parity.run_preflight(
        Path(PYTHON_BIN), REQUIREMENTS_FILE, REQUIREMENTS_DEV_FILE, out_path=PREFLIGHT_PATH,
    )
    sync = result.get("sync", {})
    log.log(f"  venv sync: {'ok' if sync.get('ok') else 'FAILED'} in {sync.get('elapsed_s')}s")
    if result["status"] == "red":
        log.log(f"  PRE-FLIGHT RED: {result['summary']}")
    else:
        log.log(f"  {result['summary']}")
    return result


# Sprint 822 (CEO decision 5, 2026-10-24): nightly reports are no longer
# committed. They stay on this machine for 90 days and are pruned here; the
# baseline the agents compare against is kept.
REPORT_RETENTION_DAYS = 90
_KEEP_FOREVER = {".baseline.json"}


def _prune_old_reports(log: RunLog) -> None:
    """Delete nightly report files older than REPORT_RETENTION_DAYS."""
    cutoff = time.time() - REPORT_RETENTION_DAYS * 86400
    removed = 0
    for path in REPORTS_DIR.iterdir():
        if path.is_file() and path.name not in _KEEP_FOREVER and path.stat().st_mtime < cutoff:
            path.unlink()
            removed += 1
    if removed:
        log.log(f"Pruned {removed} report file(s) older than {REPORT_RETENTION_DAYS} days")


def main() -> None:
    """Run the full overnight agent sequence."""
    dry_run = "--dry-run" in sys.argv

    log = RunLog()
    if dry_run:
        log.log("*** DRY RUN MODE — no agents will be executed ***")

    total_start = time.time()
    success_count = 0

    manifest = RunManifest(RUN_MANIFEST_PATH, dry_run)
    log.log(f"Testing commit {manifest.data['head_sha'] or 'UNKNOWN'} as of {manifest.data['started_at']}")
    manifest.save()

    # Sprint 854: sync + pin check before anything runs tests. A RED pre-flight
    # does not stop the run — the other agents still have something to say —
    # but the brief leads with it, and this process exits non-zero.
    preflight = _run_preflight(log, dry_run)
    manifest.data["preflight"] = {
        "status": preflight.get("status"), "summary": preflight.get("summary"),
    }
    manifest.save()

    failed_steps: list[str] = []
    for name, script, hour, minute in AGENT_SCHEDULE:
        _sleep_until(hour, minute, log)
        outcome = _run_agent(name, script, log, dry_run)
        manifest.record(name, outcome)
        if outcome["outcome"] in ("ok", "dry_run"):
            success_count += 1
        else:
            failed_steps.append(name)
        # 2 min buffer between agents (skip if already past next target)
        if not dry_run:
            time.sleep(min(120, 5))  # In practice, sleep briefly; wall-clock sync handles rest

    # Briefing compiler
    bname, bscript, bhour, bminute = BRIEFING_COMPILER
    _sleep_until(bhour, bminute, log)
    outcome = _run_agent(bname, bscript, log, dry_run)
    manifest.record(bname, outcome)
    if outcome["outcome"] in ("ok", "dry_run"):
        success_count += 1
    else:
        failed_steps.append(bname)

    total_elapsed = round(time.time() - total_start, 1)
    total_agents = len(AGENT_SCHEDULE) + 1  # +1 for briefing compiler
    log.log(
        f"=== Run complete: {success_count}/{total_agents} agents succeeded "
        f"in {total_elapsed}s ==="
    )
    if failed_steps:
        log.log(f"=== FAILED: {', '.join(failed_steps)} ===")
    if preflight.get("status") == "red":
        log.log(f"=== PRE-FLIGHT RED: {preflight.get('summary')} ===")
    if not dry_run:
        _prune_old_reports(log)
    log.save()

    # Sprint 854: exit non-zero when anything failed, so Task Scheduler's
    # "Last Run Result" shows it. It used to exit 0 unconditionally, which is
    # how 66 of 109 dormant-period nights lost QA Warden without anyone noticing.
    sys.exit(_exit_code(failed_steps, preflight, dry_run))


def _exit_code(failed_steps: list[str], preflight: dict, dry_run: bool) -> int:
    if dry_run:
        return 0
    return 1 if failed_steps or preflight.get("status") == "red" else 0


if __name__ == "__main__":
    main()
