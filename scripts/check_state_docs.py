#!/usr/bin/env python3
"""Sprint 857 — state-doc drift check (two deterministic checks, nothing fuzzy).

1. ``SESSION_STATE.md`` names the current ``main`` SHA on exactly one line of the form

       **Main SHA:** `1435b0e4`

   That SHA must resolve and be an ancestor of HEAD. A stale-but-ancestral SHA passes
   (the doc may lag ``main``); a SHA from an abandoned branch or a typo fails.

2. No sprint id appears in two ``### Sprint <id>:`` headings with different titles across
   ``tasks/todo.md`` and ``tasks/archive/*.md`` (the Sprint 846 collision). Sub-sprint ids
   (``689a``, ``793b``) are distinct from their parents. Historical collisions that predate
   this check are listed in ``HISTORICAL_DUPLICATES`` and ignored; any *new* id must be unique.

PR titles are deliberately not checked (that needs a GitHub token in CI).

Pure stdlib + ``git``. Exit 0 on pass, 1 on any failure. Run from anywhere:
``python scripts/check_state_docs.py``.
"""

from __future__ import annotations

import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

MAIN_SHA_RE = re.compile(r"^\*\*Main SHA:\*\* `([0-9a-f]{7,40})`\s*$", re.MULTILINE)
MAIN_SHA_EXAMPLE = "**Main SHA:** `<7-40 hex chars of origin/main>`"

# `### Sprint 857: Title`, `### Sprint 96.5: Title`, `### Sprint 699 (A): Title`,
# `### Sprint 195 — Title`. Lettered-only ids (`Sprint A:`) are not sprint numbers.
HEADING_RE = re.compile(
    r"^### Sprint (\d+(?:\.\d+)?[a-z]?)(?:\s*\([^)]*\))?\s*(?::|—)\s*(.*?)\s*$",
    re.MULTILINE,
)
# Status suffixes that do not change what a sprint *is*: "— COMPLETE", "(COMPLETE)".
_STATUS_SUFFIX_RE = re.compile(
    r"[\s—\-:(]*\b(complete|completed|done|pending)\b\)?\s*$", re.IGNORECASE
)

# Historical collisions measured when this check landed (2026-10-28). Each id here was
# reused for a different sprint before the guard existed; renumbering archived history
# would break every commit message and cross-reference that cites it. Do not add to this
# list — give a new sprint a fresh number instead.
HISTORICAL_DUPLICATES: frozenset[str] = frozenset(
    {
        # Per-phase "Sprint 1..4" numbering restarted inside older phase archives.
        "1",
        "2",
        "3",
        "4",
        # Same sprint, two wordings of its title (DEC 2026-03-10 P2 remediation).
        "527",
        # Two unrelated sprints shared the number.
        "677",
        # 699-703 were reused: the lettered (A)-(E) anomaly-framework series vs. the
        # export-sharing / polish sprints.
        "699",
        "700",
        "701",
        "702",
        "703",
    }
)


def normalize_title(title: str) -> str:
    title = title.replace("*", "").replace("`", "")
    prev = None
    while prev != title:
        prev = title
        title = _STATUS_SUFFIX_RE.sub("", title)
    return " ".join(title.split()).casefold()


def find_main_sha(text: str) -> list[str]:
    return MAIN_SHA_RE.findall(text)


def check_main_sha(session_state: Path, repo: Path) -> list[str]:
    """Return failure messages for check 1 (empty list = pass)."""
    if not session_state.is_file():
        return [f"{session_state.name} not found at {session_state}."]
    shas = find_main_sha(session_state.read_text(encoding="utf-8"))
    if len(shas) != 1:
        what = "is missing" if not shas else f"appears {len(shas)} times"
        return [
            (
                f"{session_state.name}: the main-SHA line {what}. Add exactly one line of the form\n"
                f"    {MAIN_SHA_EXAMPLE}\n"
                "  Fix: `git rev-parse --short origin/main` and paste the result."
            )
        ]
    sha = shas[0]

    def git(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args], cwd=repo, capture_output=True, text=True, check=False
        )

    if git("cat-file", "-e", f"{sha}^{{commit}}").returncode != 0:
        return [
            (
                f"{session_state.name}: Main SHA `{sha}` does not resolve to a commit. Either it is a typo, "
                "or the checkout is shallow (CI needs `fetch-depth: 0`).\n"
                "  Fix: set it to `git rev-parse --short origin/main`."
            )
        ]
    if git("merge-base", "--is-ancestor", sha, "HEAD").returncode != 0:
        return [
            (
                f"{session_state.name}: Main SHA `{sha}` is not an ancestor of HEAD — it names a commit "
                "that is not on this branch's history (abandoned branch, or a pre-squash SHA).\n"
                "  Fix: set it to `git rev-parse --short origin/main`."
            )
        ]
    return []


def collect_headings(files: list[Path], root: Path) -> dict[str, dict[str, list[str]]]:
    """id -> normalized title -> ["path:line", ...]."""
    found: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for path in files:
        text = path.read_text(encoding="utf-8")
        for m in HEADING_RE.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            try:
                where = f"{path.relative_to(root).as_posix()}:{line}"
            except ValueError:
                where = f"{path.as_posix()}:{line}"
            found[m.group(1)][normalize_title(m.group(2))].append(where)
    return found


def duplicate_ids(
    found: dict[str, dict[str, list[str]]],
) -> dict[str, dict[str, list[str]]]:
    return {sid: titles for sid, titles in found.items() if len(titles) > 1}


def check_sprint_ids(
    files: list[Path], root: Path, allow: frozenset[str] = HISTORICAL_DUPLICATES
) -> list[str]:
    errors = []
    dups = duplicate_ids(collect_headings(files, root))
    for sid in sorted(set(dups) - allow, key=_sort_key):
        lines = "\n".join(
            f"    {', '.join(locs)}: {title!r}" for title, locs in dups[sid].items()
        )
        errors.append(
            f"Sprint {sid} is used by {len(dups[sid])} different sprint headings:\n{lines}\n"
            "  Fix: renumber the newer sprint (next free number), or make the titles match if they "
            "are the same sprint."
        )
    return errors


def _sort_key(sid: str) -> tuple[float, str]:
    m = re.match(r"(\d+(?:\.\d+)?)(.*)", sid)
    return (float(m.group(1)), m.group(2)) if m else (float("inf"), sid)


def sprint_doc_files(root: Path) -> list[Path]:
    return [
        root / "tasks" / "todo.md",
        *sorted((root / "tasks" / "archive").glob("*.md")),
    ]


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if args == ["--list-duplicates"]:
        dups = duplicate_ids(collect_headings(sprint_doc_files(REPO_ROOT), REPO_ROOT))
        for sid in sorted(dups, key=_sort_key):
            print(f"{sid}: {sorted(dups[sid])}")
        print(f"{len(dups)} duplicated id(s)")
        return 0

    errors = check_main_sha(REPO_ROOT / "SESSION_STATE.md", REPO_ROOT)
    errors += check_sprint_ids(sprint_doc_files(REPO_ROOT), REPO_ROOT)
    if errors:
        for e in errors:
            print(f"::error::{e}" if "\n" not in e else f"ERROR: {e}")
        print(f"\nState-doc drift check FAILED ({len(errors)} problem(s)).")
        return 1
    print(
        "State-doc drift check passed (main SHA is an ancestor of HEAD; sprint ids unique)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
