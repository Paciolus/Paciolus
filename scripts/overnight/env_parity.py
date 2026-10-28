"""Environment parity for the nightly: sync the venv, then prove it matches the pins.

Sprint 854. The 2026-10-28 nightly went RED with no defect in the code:
`backend/venv` still had fastapi 0.136.1 while Sprint 786 had moved
`requirements.txt` to `fastapi==0.162.0`, so 99 test modules failed to import
and the brief reported that as a test failure. A hand rebuild of the venv fixes
one night and rots again by the next pin bump, so the orchestrator now:

1. **Syncs** the venv from `requirements-dev.txt` (which includes
   `requirements.txt`) before every run, with a hard timeout so a network
   outage cannot hang the night.
2. **Checks** every `==` pin against what is actually installed, and fails the
   nightly RED with the mismatching package named if the sync did not fix it.

Both outcomes are written to `.env_preflight_<date>.json`, which the briefing
compiler reads. Nothing here raises: every failure becomes a named reason.
"""

from __future__ import annotations

import datetime
import json
import re
import subprocess
from pathlib import Path

# pip's own per-request socket timeout and retry count. These bound a single
# slow request; SYNC_TIMEOUT_S bounds the whole install.
PIP_SOCKET_TIMEOUT_S = 30
PIP_RETRIES = 2
# A no-op sync (everything already satisfied) takes ~10-20s. A real bump of a
# few packages takes a minute or two. Ten minutes is generous without letting
# a stalled index eat the 02:00-02:15 window and push every agent late.
SYNC_TIMEOUT_S = 600
INSTALLED_LIST_TIMEOUT_S = 120

_PIN_RE = re.compile(
    r"^\s*(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)\s*(?:\[[^\]]*\])?\s*==\s*(?P<version>[^\s;,#]+)"
)
_INCLUDE_RE = re.compile(r"^\s*(?:-r|--requirement)\s*(?:=\s*)?(?P<path>\S+)")

# Prints {normalized-name: version} for everything importlib.metadata can see.
# Run inside the target interpreter, so it reports *that* venv, not ours.
_LIST_INSTALLED = (
    "import json, re\n"
    "from importlib.metadata import distributions\n"
    "out = {}\n"
    "for d in distributions():\n"
    "    n = d.metadata['Name']\n"
    "    if n:\n"
    "        out[re.sub(r'[-_.]+', '-', n).lower()] = d.version\n"
    "print(json.dumps(out))\n"
)


def normalize_name(name: str) -> str:
    """PEP 503 normalisation, so `PyJWT`, `pyjwt` and `py_jwt` compare equal."""
    return re.sub(r"[-_.]+", "-", name).lower()


def parse_exact_pins(requirements: Path, _seen: set[Path] | None = None) -> dict[str, str]:
    """Every `name==version` pin in `requirements`, following `-r` includes.

    Floors (`>=`) are deliberately ignored: the pinning rule at the top of
    `requirements.txt` says they are allowed to move.
    """
    seen = _seen if _seen is not None else set()
    path = requirements.resolve()
    if path in seen or not path.exists():
        return {}
    seen.add(path)

    pins: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split(" #", 1)[0].strip()
        if not line or line.startswith("#"):
            continue
        inc = _INCLUDE_RE.match(line)
        if inc:
            pins.update(parse_exact_pins(path.parent / inc.group("path"), seen))
            continue
        m = _PIN_RE.match(line)
        if m:
            pins[normalize_name(m.group("name"))] = m.group("version")
    return pins


def compare_pins(pins: dict[str, str], installed: dict[str, str]) -> list[dict]:
    """Pins whose installed version differs, or which are not installed at all."""
    mismatches = []
    for name, pinned in sorted(pins.items()):
        have = installed.get(name)
        if have != pinned:
            mismatches.append({"package": name, "pinned": pinned, "installed": have})
    return mismatches


def _tail(text: str | None, n: int = 3) -> str:
    lines = [ln for ln in (text or "").strip().splitlines() if ln.strip()]
    return " | ".join(lines[-n:])


def sync_venv(python_bin: Path, requirements: Path, timeout_s: int = SYNC_TIMEOUT_S) -> dict:
    """`pip install -r` into the venv. Returns {"ok", "reason", "elapsed_s"}; never raises."""
    t0 = datetime.datetime.now()

    def _done(ok: bool, reason: str | None) -> dict:
        elapsed = round((datetime.datetime.now() - t0).total_seconds(), 1)
        return {"ok": ok, "reason": reason, "elapsed_s": elapsed}

    if not python_bin.exists():
        return _done(False, f"venv interpreter not found at {python_bin}")
    if not requirements.exists():
        return _done(False, f"requirements file not found at {requirements}")
    # pip runs with cwd = the requirements' directory (so nested `-r` resolve),
    # so the path itself must not be relative to *our* cwd.
    requirements = requirements.resolve()

    cmd = [
        str(python_bin), "-m", "pip", "install",
        "--disable-pip-version-check", "--no-input", "-q",
        "--timeout", str(PIP_SOCKET_TIMEOUT_S), "--retries", str(PIP_RETRIES),
        "-r", str(requirements),
    ]
    try:
        result = subprocess.run(
            cmd, check=False, cwd=str(requirements.parent), capture_output=True,
            text=True, encoding="utf-8", errors="replace", timeout=timeout_s,
        )
    except subprocess.TimeoutExpired:
        return _done(False, f"venv sync timed out after {timeout_s}s (pip install -r {requirements.name}; "
                            f"package index unreachable or slow?)")
    except OSError as e:
        return _done(False, f"venv sync could not start pip: {e}")

    if result.returncode != 0:
        detail = _tail(result.stderr) or _tail(result.stdout) or "no output"
        return _done(False, f"venv sync failed: pip exited {result.returncode}: {detail}")
    return _done(True, None)


def installed_versions(python_bin: Path) -> tuple[dict[str, str] | None, str | None]:
    """(versions, error) for the distributions installed in `python_bin`'s environment."""
    try:
        result = subprocess.run(
            [str(python_bin), "-c", _LIST_INSTALLED], check=False, capture_output=True,
            text=True, encoding="utf-8", errors="replace", timeout=INSTALLED_LIST_TIMEOUT_S,
        )
    except (subprocess.TimeoutExpired, OSError) as e:
        return None, f"could not list installed packages: {e}"
    if result.returncode != 0 or not result.stdout:
        return None, f"could not list installed packages: {_tail(result.stderr) or 'no output'}"
    try:
        return json.loads(result.stdout), None
    except json.JSONDecodeError as e:
        return None, f"could not parse installed package list: {e}"


def evaluate(sync: dict, pins: dict[str, str], installed: dict[str, str] | None,
             list_error: str | None) -> dict:
    """Combine the sync result and the pin check into one RED/GREEN verdict with reasons."""
    reasons: list[str] = []
    mismatches: list[dict] = []

    if not sync.get("ok"):
        reasons.append(sync.get("reason") or "venv sync failed")

    if installed is None:
        reasons.append(list_error or "could not list installed packages")
    elif not pins:
        reasons.append("no `==` pins found in requirements — nothing to verify the venv against")
    else:
        mismatches = compare_pins(pins, installed)
        if mismatches:
            shown = ", ".join(
                f"{m['package']} pinned {m['pinned']}, installed {m['installed'] or 'MISSING'}"
                for m in mismatches[:5]
            )
            more = f" (+{len(mismatches) - 5} more)" if len(mismatches) > 5 else ""
            reasons.append(f"{len(mismatches)} installed version(s) differ from the == pins: {shown}{more}")

    status = "red" if reasons else "green"
    if reasons:
        summary = "Environment pre-flight FAILED: " + "; ".join(reasons) + "."
    else:
        summary = f"Environment pre-flight passed: venv synced, all {len(pins)} == pins match."
    return {
        "agent": "env_preflight",
        "status": status,
        "reasons": reasons,
        "sync": sync,
        "pins_checked": len(pins),
        "mismatches": mismatches,
        "summary": summary,
    }


def run_preflight(python_bin: Path, requirements: Path, sync_requirements: Path,
                  out_path: Path | None = None, sync_timeout_s: int = SYNC_TIMEOUT_S) -> dict:
    """Sync from `sync_requirements`, then verify the `==` pins in `requirements`."""
    sync = sync_venv(python_bin, sync_requirements, timeout_s=sync_timeout_s)
    pins = parse_exact_pins(requirements)
    if python_bin.exists():
        installed, list_error = installed_versions(python_bin)
    else:
        installed, list_error = None, f"venv interpreter not found at {python_bin}"
    result = evaluate(sync, pins, installed, list_error)
    result["checked_at"] = datetime.datetime.now().isoformat(timespec="seconds")
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result
