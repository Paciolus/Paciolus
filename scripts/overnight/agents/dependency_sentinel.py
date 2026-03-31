"""Dependency Sentinel — surfaces outdated or vulnerable dependencies."""

import datetime
import io
import json
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
    ANTHROPIC_API_KEY,
    BACKEND_ROOT,
    CLAUDE_MODEL,
    FRONTEND_ROOT,
    REPORTS_DIR,
    SYSTEM_PYTHON,
    TODAY,
)

# Always report these packages regardless of version gap
BACKEND_WATCHLIST = {"stripe", "fastapi", "pyjwt", "cryptography", "sqlalchemy"}
FRONTEND_WATCHLIST = {"next", "react", "stripe"}

# Deferrals file: packages intentionally held back (waiting on ecosystem, etc.)
DEFERRALS_FILE = Path(__file__).resolve().parent.parent / "dependency_deferrals.json"


def _load_deferrals() -> dict:
    """Load the deferrals config. Returns {package_name: {...}} or {}."""
    if not DEFERRALS_FILE.exists():
        return {}
    try:
        data = json.loads(DEFERRALS_FILE.read_text(encoding="utf-8"))
        # Strip the _comment key
        return {k: v for k, v in data.items() if not k.startswith("_")}
    except (json.JSONDecodeError, OSError):
        return {}


def _is_deferred(pkg_name: str, latest: str, deferrals: dict) -> dict | None:
    """Check if a package has an active (non-expired) deferral.

    Returns the deferral record if active, None otherwise.
    A deferral is active when:
      1. The available version <= the deferred version (no new release since deferral)
      2. The review_by date has not passed
    """
    deferral = deferrals.get(pkg_name)
    if not deferral:
        return None

    # Check if a newer version than the deferred one is now available
    deferred_ver = _parse_version(deferral.get("deferred_version", "0"))
    latest_ver = _parse_version(latest)
    if latest_ver > deferred_ver:
        return None  # New release — re-evaluate

    # Check if the deferral has expired
    review_by = deferral.get("review_by", "")
    if review_by:
        try:
            if datetime.date.fromisoformat(review_by) < datetime.date.today():
                return None  # Expired — re-evaluate
        except ValueError:
            pass

    return deferral


def _parse_version(v: str) -> tuple[int, ...]:
    """Parse a version string into a tuple of ints for comparison."""
    parts = []
    for segment in v.split(".")[:3]:
        # Strip non-numeric suffixes like 'rc1', 'b2', etc.
        num = ""
        for ch in segment:
            if ch.isdigit():
                num += ch
            else:
                break
        parts.append(int(num) if num else 0)
    return tuple(parts)


def _is_calver(version: str) -> bool:
    """Detect calendar versioning (e.g., 20260107) — no dots, large number."""
    return "." not in version and version.isdigit() and int(version) > 1_000_000


def _severity(current: str, latest: str) -> str:
    """Determine update severity: major, minor, or patch."""
    # Calendar-versioned packages (YYYYMMDD) have no semver "major" concept
    if _is_calver(current) or _is_calver(latest):
        return "minor"
    cur = _parse_version(current)
    lat = _parse_version(latest)
    if lat[0] > cur[0]:
        return "major"
    if len(lat) > 1 and len(cur) > 1 and lat[1] > cur[1]:
        return "minor"
    return "patch"


def _check_backend() -> list[dict]:
    """Run pip list --outdated and parse results."""
    cmd = [str(SYSTEM_PYTHON), "-m", "pip", "list", "--outdated", "--format=json"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

    outdated = []
    try:
        packages = json.loads(result.stdout)
        for pkg in packages:
            name = pkg.get("name", "").lower()
            current = pkg.get("version", "0")
            latest = pkg.get("latest_version", "0")
            sev = _severity(current, latest)
            outdated.append({
                "package": pkg.get("name", ""),
                "current": current,
                "latest": latest,
                "severity": sev,
                "watchlist": name in BACKEND_WATCHLIST,
            })
    except (json.JSONDecodeError, KeyError):
        # Fallback: no parseable output
        pass

    return outdated


def _check_frontend() -> list[dict]:
    """Run npm outdated --json and parse results."""
    cmd = ["npm", "outdated", "--json"]
    result = subprocess.run(
        cmd, cwd=str(FRONTEND_ROOT), capture_output=True, text=True,
        timeout=120, shell=True,
    )

    outdated = []
    try:
        packages = json.loads(result.stdout) if result.stdout.strip() else {}
        for name, info in packages.items():
            current = info.get("current", "0.0.0")
            wanted = info.get("wanted", current)
            latest = info.get("latest", wanted)
            sev = _severity(current, latest)
            outdated.append({
                "package": name,
                "current": current,
                "latest": latest,
                "severity": sev,
                "watchlist": name.lower() in FRONTEND_WATCHLIST,
            })
    except (json.JSONDecodeError, KeyError):
        pass

    return outdated


def _get_update_notes(packages: list[dict]) -> list[dict]:
    """For top 5 most outdated packages, add a one-line update note."""
    # Sort by severity (major first) then by name
    severity_order = {"major": 0, "minor": 1, "patch": 2}
    sorted_pkgs = sorted(packages, key=lambda p: severity_order.get(p["severity"], 3))
    top5 = sorted_pkgs[:5]

    if not ANTHROPIC_API_KEY or not top5:
        return top5

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        pkg_list = "\n".join(
            f"- {p['package']}: {p['current']} → {p['latest']}" for p in top5
        )
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": (
                    f"For each package update below, write ONE brief sentence about "
                    f"what's new or changed. Return valid JSON array of objects with "
                    f"'package' and 'note' keys. No markdown.\n\n{pkg_list}"
                ),
            }],
        )
        text = ""
        for block in response.content:
            if hasattr(block, "text"):
                text += block.text
        clean = text.strip()
        if clean.startswith("```"):
            lines = clean.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            clean = "\n".join(lines)
        notes = json.loads(clean)
        note_map = {n["package"]: n["note"] for n in notes if "package" in n}
        for p in top5:
            p["note"] = note_map.get(p["package"], "")
    except Exception as e:
        print(f"  Warning: could not get update notes: {e}")

    return top5


def run() -> dict:
    """Execute Dependency Sentinel and return structured results."""
    t0 = time.time()

    backend_outdated = _check_backend()
    frontend_outdated = _check_frontend()

    all_outdated = backend_outdated + frontend_outdated

    # Load deferrals and tag each package
    deferrals = _load_deferrals()
    deferred_pkgs = []
    for p in all_outdated:
        deferral = _is_deferred(p["package"], p["latest"], deferrals)
        if deferral:
            p["deferred"] = True
            p["deferral_reason"] = deferral.get("reason", "")
            p["deferral_review_by"] = deferral.get("review_by", "")
            deferred_pkgs.append(p)
        else:
            p["deferred"] = False

    # Packages that actually count toward status (not actively deferred)
    actionable = [p for p in all_outdated if not p["deferred"]]

    # Security-flagged: watchlist packages with available updates (only actionable)
    security_flagged = [p for p in actionable if p.get("watchlist")]

    # Top 5 with notes (from actionable packages only)
    top5 = _get_update_notes(actionable)

    # Determine status based on actionable packages only
    major_security = any(
        p["severity"] == "major" for p in security_flagged
    )
    has_major = any(p["severity"] == "major" for p in actionable)

    if major_security:
        status = "red"
    elif has_major or security_flagged:
        status = "yellow"
    else:
        status = "green"

    result = {
        "agent": "dependency_sentinel",
        "status": status,
        "backend_outdated": backend_outdated,
        "frontend_outdated": frontend_outdated,
        "security_flagged": security_flagged,
        "deferred": deferred_pkgs,
        "top5_updates": top5,
        "summary": (
            f"Backend: {len(backend_outdated)} outdated. "
            f"Frontend: {len(frontend_outdated)} outdated. "
            f"{len(security_flagged)} security-relevant packages have updates."
            + (f" {len(deferred_pkgs)} deferred." if deferred_pkgs else "")
        ),
    }

    out_path = REPORTS_DIR / f".dependency_sentinel_{TODAY}.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    elapsed = round(time.time() - t0, 1)
    print(f"Dependency Sentinel completed in {elapsed}s — status: {status}")
    return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
