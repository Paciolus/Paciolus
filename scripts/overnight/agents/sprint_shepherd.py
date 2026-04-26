"""Sprint Shepherd — assesses sprint progress from git history and surfaces drift."""

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
from scripts.overnight.config import PROJECT_ROOT, REPORTS_DIR, TODAY

WORK_CATEGORIES = [
    "bug fix", "report", "audit", "test", "billing", "ui", "api", "refactor", "perf",
]

# Sprint 730: word-boundary matching prevents false-positives on substrings
# like "fix typo in TODO list" or "chore: bump pytodo dep". The regex is
# applied case-insensitively against each commit message.
RISK_KEYWORDS = ["WIP", "temp", "TODO", "fixme", "hack", "broken"]
RISK_KEYWORD_RE = re.compile(r"\b(" + "|".join(re.escape(k) for k in RISK_KEYWORDS) + r")\b", re.IGNORECASE)

# Conventional-commit prefixes that pre-classify the commit; risk keywords
# inside the *description* of these commits are not load-bearing because the
# prefix itself signals intent ("fix:" already says it's a fix). Sprint 730
# false-positive: "fix: archive_sprints.sh number-extraction (TODO list bug)".
SAFE_PREFIXES = ("fix:", "chore:", "docs:", "style:", "test:", "build:", "ci:", "perf:")

CHECKLIST_LOCATIONS = [
    PROJECT_ROOT / "SPRINT_CHECKLIST.md",
    PROJECT_ROOT / "docs" / "SPRINT_CHECKLIST.md",
    PROJECT_ROOT / "scripts" / "sprint_checklist.md",
]


def _git_log(since: str) -> list[dict]:
    """Run git log and parse into structured commits."""
    cmd = [
        "git", "log", "--oneline",
        f"--since={since}",
        "--format=%h|%ai|%s",
    ]
    result = subprocess.run(
        cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True, timeout=30,
    )
    commits = []
    for line in result.stdout.strip().splitlines():
        parts = line.split("|", 2)
        if len(parts) == 3:
            commits.append({
                "hash": parts[0].strip(),
                "timestamp": parts[1].strip(),
                "message": parts[2].strip(),
            })
    return commits


def _parse_checklist(path: Path) -> dict:
    """Parse markdown checklist file into completion stats."""
    if not path.exists():
        return {"found": False, "total": 0, "completed": 0, "pct": 0, "open_items": []}

    content = path.read_text(encoding="utf-8", errors="ignore")
    total = 0
    completed = 0
    open_items: list[str] = []

    for line in content.splitlines():
        m = re.match(r"\s*-\s*\[([ xX])\]\s*(.*)", line)
        if m:
            total += 1
            if m.group(1).lower() == "x":
                completed += 1
            else:
                open_items.append(m.group(2).strip())

    pct = round((completed / total * 100) if total > 0 else 0, 1)
    return {
        "found": True,
        "total": total,
        "completed": completed,
        "pct": pct,
        "open_items": open_items,
    }


def _categorize_commit(message: str) -> str:
    """Tag a commit message with a work category."""
    msg_lower = message.lower()

    # Check explicit patterns first
    if re.search(r"\bfix[:\s]|\bbug\b", msg_lower):
        return "bug fix"
    for cat in WORK_CATEGORIES:
        if cat in msg_lower:
            return cat

    # Sprint prefix typically indicates feature/report work
    if msg_lower.startswith("sprint"):
        return "report"

    return "other"


def _find_risk_signals(commits: list[dict]) -> list[dict]:
    """Flag commits with risk keywords in their messages.

    Sprint 730: applies word-boundary matching (no false positives on substrings
    like "TODO list" embedded in larger words) and skips conventional-commit
    prefixes that pre-classify intent ("fix:", "chore:", etc. already signal
    that the commit is a non-feature change).
    """
    risky: list[dict] = []
    for c in commits:
        message = c["message"]
        # Skip if the commit is conventionally tagged (fix:, chore:, etc.).
        # The first token before whitespace is the prefix.
        first_token = message.split(maxsplit=1)[0].lower() if message else ""
        if first_token in SAFE_PREFIXES:
            continue
        match = RISK_KEYWORD_RE.search(message)
        if match:
            risky.append({"hash": c["hash"], "message": message, "keyword": match.group(1)})
    return risky


def run() -> dict:
    """Execute Sprint Shepherd and return structured results."""
    t0 = time.time()

    commits_24h = _git_log("24 hours ago")
    commits_7d = _git_log("7 days ago")

    # Categorize 24h commits
    categories: dict[str, int] = {}
    for c in commits_24h:
        cat = _categorize_commit(c["message"])
        categories[cat] = categories.get(cat, 0) + 1

    # Risk signals
    risk_commits = _find_risk_signals(commits_24h)

    # Sprint checklist
    checklist = {"found": False, "total": 0, "completed": 0, "pct": 0, "open_items": []}
    for loc in CHECKLIST_LOCATIONS:
        result = _parse_checklist(loc)
        if result["found"]:
            checklist = result
            break

    # Determine status
    if checklist["found"]:
        pct = checklist["pct"]
        if pct >= 70:
            status = "green"
        elif pct >= 40:
            status = "yellow"
        else:
            status = "red"
    else:
        status = "green"  # No checklist = no sprint tracking issues

    if risk_commits:
        status = "yellow" if status == "green" else status

    summary_parts = [
        f"{len(commits_24h)} commits in last 24h, {len(commits_7d)} in last 7d.",
    ]
    if checklist["found"]:
        summary_parts.append(
            f"Sprint checklist: {checklist['completed']}/{checklist['total']} ({checklist['pct']}%)."
        )
    if risk_commits:
        summary_parts.append(f"{len(risk_commits)} risk signal(s) detected.")

    result_data = {
        "agent": "sprint_shepherd",
        "status": status,
        "commits_last_24h": len(commits_24h),
        "commits_last_7d": len(commits_7d),
        "work_categories_24h": categories,
        "risk_commits": risk_commits,
        "sprint_checklist": {
            "found": checklist["found"],
            "total": checklist["total"],
            "completed": checklist["completed"],
            "pct": checklist["pct"],
        },
        "open_items": checklist.get("open_items", []),
        "summary": " ".join(summary_parts),
    }

    out_path = REPORTS_DIR / f".sprint_shepherd_{TODAY}.json"
    out_path.write_text(json.dumps(result_data, indent=2), encoding="utf-8")

    elapsed = round(time.time() - t0, 1)
    print(f"Sprint Shepherd completed in {elapsed}s — status: {status}")
    return result_data


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
