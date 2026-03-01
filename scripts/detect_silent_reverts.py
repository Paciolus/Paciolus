#!/usr/bin/env python3
"""Silent Revert Detector — merge conflict resolution guard.

Detects when a merge-conflict resolution commit accidentally drops lines
that were intentionally added by a recently-merged PR.  Designed to run
as an advisory CI job on every PR targeting main.

Usage:
    python scripts/detect_silent_reverts.py [--pr-count N] [--overlap-threshold T]

Exit codes:
    0 — no potential silent reverts detected (or detection completed with warnings)
    1 — potential silent reverts found (advisory, CI should continue-on-error)
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

def run_git(*args: str) -> str:
    """Run a git command and return stripped stdout."""
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        # Some commands (e.g. diff on empty range) return non-zero legitimately
        return result.stdout.strip()
    return result.stdout.strip()


def resolve_target_branch() -> str:
    """Determine the target branch (main or master).

    Prefers remote tracking refs (origin/main) since CI often operates
    on detached HEADs where local branch names may differ.
    """
    for candidate in ("origin/main", "main", "origin/master", "master"):
        result = subprocess.run(
            ["git", "rev-parse", "--verify", candidate],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return candidate
    return "main"


def get_merge_base(branch: str | None = None) -> str:
    """Get the merge base between HEAD and the target branch."""
    if branch is None:
        branch = resolve_target_branch()
    return run_git("merge-base", branch, "HEAD")


def get_pr_commits(merge_base: str) -> list[str]:
    """Get commit hashes in the PR (merge_base..HEAD)."""
    raw = run_git("log", "--format=%H", f"{merge_base}..HEAD")
    if not raw:
        return []
    return raw.splitlines()


def get_commit_message(sha: str) -> str:
    """Get the full commit message for a SHA."""
    return run_git("log", "-1", "--format=%B", sha)


def get_commit_short(sha: str) -> str:
    """Get short SHA + first line of message."""
    return run_git("log", "-1", "--format=%h %s", sha)


def get_diff_lines(base: str, tip: str) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Get added and removed lines per file between two commits.

    Returns (added, removed) where each is {filepath: [lines...]}.
    Lines are stripped of leading +/- but preserve content whitespace.
    """
    raw = run_git("diff", base, tip, "--unified=0", "--no-color")
    added: dict[str, list[str]] = {}
    removed: dict[str, list[str]] = {}
    current_file: str | None = None

    for line in raw.splitlines():
        # Track current file from diff headers
        if line.startswith("+++ b/"):
            current_file = line[6:]
            continue
        if line.startswith("--- a/"):
            continue
        if current_file is None:
            continue
        # Skip diff metadata
        if line.startswith("@@") or line.startswith("diff ") or line.startswith("index "):
            continue
        # Added lines
        if line.startswith("+") and not line.startswith("+++"):
            content = line[1:]
            if content.strip():  # skip blank lines
                added.setdefault(current_file, []).append(content)
        # Removed lines
        elif line.startswith("-") and not line.startswith("---"):
            content = line[1:]
            if content.strip():  # skip blank lines
                removed.setdefault(current_file, []).append(content)

    return added, removed


def get_commit_diff_removed(sha: str) -> dict[str, list[str]]:
    """Get lines removed by a specific commit."""
    raw = run_git("diff", f"{sha}~1", sha, "--unified=0", "--no-color")
    removed: dict[str, list[str]] = {}
    current_file: str | None = None

    for line in raw.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:]
            continue
        if line.startswith("--- a/"):
            continue
        if current_file is None:
            continue
        if line.startswith("@@") or line.startswith("diff ") or line.startswith("index "):
            continue
        if line.startswith("-") and not line.startswith("---"):
            content = line[1:]
            if content.strip():
                removed.setdefault(current_file, []).append(content)

    return removed


def get_recent_merged_prs(count: int, branch: str | None = None) -> list[dict[str, str]]:
    """Get the last N merge commits on the target branch (representing merged PRs).

    Returns list of dicts with 'sha', 'message', 'parents'.
    """
    if branch is None:
        branch = resolve_target_branch()
    raw = run_git(
        "log", branch, f"--max-count={count}",
        "--merges", "--format=%H|%P|%s",
    )
    if not raw:
        return []

    prs = []
    for line in raw.splitlines():
        parts = line.split("|", 2)
        if len(parts) < 3:
            continue
        sha, parents, message = parts
        prs.append({
            "sha": sha.strip(),
            "parents": parents.strip(),
            "message": message.strip(),
        })
    return prs


def get_merge_pr_added_lines(merge_sha: str, parents: str) -> dict[str, list[str]]:
    """Get lines added by a merged PR by diffing the merge commit's first parent
    against the merge commit itself.

    For a merge commit M with parents P1 (main before merge) and P2 (PR branch tip),
    `diff P1..M` shows what the merge brought in.
    """
    parent_list = parents.split()
    if not parent_list:
        return {}
    first_parent = parent_list[0]
    added, _ = get_diff_lines(first_parent, merge_sha)
    return added


# ---------------------------------------------------------------------------
# Conflict resolution commit detection
# ---------------------------------------------------------------------------

CONFLICT_PATTERNS = [
    re.compile(r"resolve[ds]?\s+merge\s+conflict", re.IGNORECASE),
    re.compile(r"fix\s+merge\s+conflict", re.IGNORECASE),
    re.compile(r"merge\s+conflict\s+resolution", re.IGNORECASE),
    re.compile(r"resolved?\s+conflict", re.IGNORECASE),
    re.compile(r"fix\s+conflict", re.IGNORECASE),
]


def is_conflict_resolution_commit(sha: str) -> bool:
    """Check if a commit looks like a merge conflict resolution."""
    message = get_commit_message(sha)
    for pattern in CONFLICT_PATTERNS:
        if pattern.search(message):
            return True
    return False


# ---------------------------------------------------------------------------
# Overlap detection
# ---------------------------------------------------------------------------

@dataclass
class RevertWarning:
    """A potential silent revert detection."""
    conflict_commit: str
    conflict_commit_desc: str
    reverted_pr_sha: str
    reverted_pr_desc: str
    files: list[str]
    sample_lines: list[str]
    overlap_count: int


def normalize_line(line: str) -> str:
    """Normalize a line for comparison: strip and collapse whitespace."""
    return " ".join(line.split())


def find_overlap(
    removed_by_conflict: dict[str, list[str]],
    added_by_pr: dict[str, list[str]],
    threshold: int,
) -> tuple[list[str], list[str], int]:
    """Find overlapping lines between conflict removals and PR additions.

    Returns (files, sample_lines, overlap_count).
    Only considers files that appear in both diffs.
    """
    overlapping_files: list[str] = []
    all_matching_lines: list[str] = []
    total_overlap = 0

    for filepath in removed_by_conflict:
        if filepath not in added_by_pr:
            continue

        removed_normalized = {normalize_line(l) for l in removed_by_conflict[filepath]}
        added_normalized = {normalize_line(l) for l in added_by_pr[filepath]}

        overlap = removed_normalized & added_normalized
        # Filter out trivially short lines (imports, braces, etc.)
        significant = {l for l in overlap if len(l) > 10}

        if significant:
            overlapping_files.append(filepath)
            total_overlap += len(significant)
            for line in sorted(significant)[:5]:  # sample up to 5 per file
                all_matching_lines.append(f"  {filepath}: {line[:120]}")

    return overlapping_files, all_matching_lines[:10], total_overlap


# ---------------------------------------------------------------------------
# Main detection
# ---------------------------------------------------------------------------

def detect_silent_reverts(
    pr_count: int = 15,
    overlap_threshold: int = 3,
) -> list[RevertWarning]:
    """Run the silent revert detection.

    1. Find conflict resolution commits in the current PR
    2. For each, compare its removed lines against recent merged PR additions
    3. Flag significant overlaps
    """
    # Find the merge base with the target branch
    target_branch = resolve_target_branch()
    merge_base = get_merge_base(target_branch)
    if not merge_base:
        print("::notice::Could not determine merge base with target branch. Skipping.")
        return []

    # Get commits in the PR
    pr_commits = get_pr_commits(merge_base)
    if not pr_commits:
        print("::notice::No commits found in PR range. Skipping.")
        return []

    # Identify conflict resolution commits
    conflict_commits = [sha for sha in pr_commits if is_conflict_resolution_commit(sha)]
    if not conflict_commits:
        print("::notice::No conflict resolution commits detected in this PR. All clear.")
        return []

    print(f"Found {len(conflict_commits)} conflict resolution commit(s):")
    for sha in conflict_commits:
        print(f"  - {get_commit_short(sha)}")

    # Get recent merged PRs on the target branch
    merged_prs = get_recent_merged_prs(pr_count, target_branch)
    if not merged_prs:
        print("::notice::No recent merged PRs found on main. Skipping.")
        return []

    print(f"\nChecking against {len(merged_prs)} recent merged PR(s) on main...")

    # For each conflict commit, check for overlaps with each merged PR
    warnings: list[RevertWarning] = []

    for conflict_sha in conflict_commits:
        removed = get_commit_diff_removed(conflict_sha)
        if not removed:
            continue

        conflict_desc = get_commit_short(conflict_sha)

        for pr in merged_prs:
            pr_added = get_merge_pr_added_lines(pr["sha"], pr["parents"])
            if not pr_added:
                continue

            files, sample, count = find_overlap(removed, pr_added, overlap_threshold)
            if count >= overlap_threshold:
                warnings.append(RevertWarning(
                    conflict_commit=conflict_sha,
                    conflict_commit_desc=conflict_desc,
                    reverted_pr_sha=pr["sha"],
                    reverted_pr_desc=pr["message"],
                    files=files,
                    sample_lines=sample,
                    overlap_count=count,
                ))

    return warnings


def format_warnings(warnings: list[RevertWarning]) -> str:
    """Format warnings for CI output."""
    lines = []
    lines.append(f"⚠ SILENT REVERT DETECTOR: {len(warnings)} potential revert(s) found\n")

    for i, w in enumerate(warnings, 1):
        lines.append(f"─── Warning {i} ───")
        lines.append(f"  Conflict commit : {w.conflict_commit_desc}")
        lines.append(f"  May revert PR   : {w.reverted_pr_desc}")
        lines.append(f"  Affected file(s): {', '.join(w.files)}")
        lines.append(f"  Overlapping lines: {w.overlap_count}")
        if w.sample_lines:
            lines.append("  Sample dropped lines:")
            for sl in w.sample_lines:
                lines.append(f"    {sl}")
        lines.append("")

    lines.append(
        "Action: Review the conflict resolution commit(s) above to confirm "
        "the removals were intentional, not accidental reverts of recent work."
    )
    return "\n".join(lines)


def emit_github_annotations(warnings: list[RevertWarning]) -> None:
    """Emit GitHub Actions warning annotations."""
    for w in warnings:
        files_str = ", ".join(w.files)
        msg = (
            f"Potential silent revert: commit {w.conflict_commit_desc} "
            f"may have reverted changes from '{w.reverted_pr_desc}' "
            f"in {files_str} ({w.overlap_count} overlapping lines)"
        )
        # GitHub Actions annotation format
        print(f"::warning::{msg}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Detect silent reverts in merge conflict resolution commits.",
    )
    parser.add_argument(
        "--pr-count",
        type=int,
        default=15,
        help="Number of recent merged PRs to check against (default: 15)",
    )
    parser.add_argument(
        "--overlap-threshold",
        type=int,
        default=3,
        help="Minimum overlapping non-whitespace lines to flag (default: 3)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )

    args = parser.parse_args()

    print("Silent Revert Detector")
    print(f"  PR count: {args.pr_count}, Overlap threshold: {args.overlap_threshold}\n")

    warnings = detect_silent_reverts(
        pr_count=args.pr_count,
        overlap_threshold=args.overlap_threshold,
    )

    if not warnings:
        print("\n✓ No potential silent reverts detected.")
        return 0

    # Human-readable output
    print("\n" + format_warnings(warnings))

    # GitHub Actions annotations
    emit_github_annotations(warnings)

    # JSON output if requested
    if args.json:
        json_output = [
            {
                "conflict_commit": w.conflict_commit,
                "conflict_commit_desc": w.conflict_commit_desc,
                "reverted_pr_sha": w.reverted_pr_sha,
                "reverted_pr_desc": w.reverted_pr_desc,
                "files": w.files,
                "sample_lines": w.sample_lines,
                "overlap_count": w.overlap_count,
            }
            for w in warnings
        ]
        print("\n--- JSON Output ---")
        print(json.dumps(json_output, indent=2))

    return 1


if __name__ == "__main__":
    sys.exit(main())
