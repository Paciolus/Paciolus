"""
GitHub Actions pin hygiene — Sprint 786c.

Two properties of `.github/workflows/*.yml`, both of which rested entirely on
discipline until now:

1. **Every action is pinned to a 40-character commit SHA, never a tag.** A tag
   is mutable: whoever controls the action's repository can repoint `v7` at new
   code, and that code runs in this repository's CI with its credentials and
   its `GITHUB_TOKEN`. This is the single highest-leverage supply-chain control
   in the repo and nothing was checking it.

2. **Every pin carries a `# pin: vX.Y.Z` comment.** A bare SHA is unreadable —
   you cannot tell a six-month-old pin from a current one without an API call,
   which is precisely why these went stale. Four Dependabot PRs for them sat
   until their own targets went stale too (closed as superseded in Sprint 785),
   and when Sprint 786c finally resolved them, every one of the six was behind:
   `checkout` v6.0.2, `setup-node` v6.3.0, `setup-python` v6.2.0,
   `github-script` v8.0.0, `upload-artifact` v7.0.0, `download-artifact` v8.0.1.

These tests deliberately do **not** check that the pins are *current* — that
needs a network call and would make CI fail for reasons outside the commit.
Currency is Dependabot's job; readability and immutability are these tests'.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

WORKFLOWS_DIR = Path(__file__).resolve().parents[2] / ".github" / "workflows"

# `uses:` lines come in three shapes: a pinned external action, a local action
# path (`./.github/actions/...`), and a reusable workflow. Only the first is in
# scope here.
#
# The `(?:-\s+)?` is load-bearing (PR #188 review). The first draft was
# `^\s*uses:` and YAML list items are written `- uses: actions/checkout@...`,
# so it matched only the 15 entries where a `- name:` came first and skipped
# **49 of the 64** references in these workflows — every `setup-node` and
# `download-artifact` use, and 25 of 27 `checkout` uses. All five tests were
# green while covering 23% of the file.
_USES = re.compile(r"^\s*(?:-\s+)?uses:\s*(?P<ref>\S+)(?P<rest>.*)$")
_SHA40 = re.compile(r"^[0-9a-f]{40}$")
_PIN_COMMENT = re.compile(r"#\s*pin:\s*v?\d+\.\d+\.\d+", re.IGNORECASE)


def _workflow_files() -> list[Path]:
    return sorted(WORKFLOWS_DIR.glob("*.yml")) + sorted(WORKFLOWS_DIR.glob("*.yaml"))


def _external_uses() -> list[tuple[Path, int, str, str]]:
    """Every external `uses:` as (path, line number, reference, trailing text)."""
    found: list[tuple[Path, int, str, str]] = []
    for path in _workflow_files():
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            m = _USES.match(line)
            if not m:
                continue
            ref = m.group("ref")
            if ref.startswith("./") or ref.startswith("."):
                continue  # local composite action — no pin to check
            found.append((path, i, ref, m.group("rest")))
    return found


def test_workflow_directory_is_where_we_think_it_is():
    """A glob that matches nothing covers nothing."""
    assert WORKFLOWS_DIR.is_dir(), f"no workflows directory at {WORKFLOWS_DIR}"
    assert _workflow_files(), "no workflow files found — this check now covers nothing"


def test_the_parser_sees_every_uses_line_in_every_workflow():
    """The guard against this guard silently shrinking.

    PR #188 review: the first `_USES` pattern required `uses:` after only
    whitespace, so it skipped every YAML list item (`- uses: ...`) — 49 of 64
    references. The four checks below all passed while inspecting 23% of the
    file, and the regression proof happened to pick a line inside that 23%.

    A parser-based scan can narrow without any test noticing, because the cases
    it stops seeing stop being asserted. So count the `uses:` lines the naive
    way and require the parser to account for all of them. This test does not
    care *what* the references are — only that none became invisible.
    """
    naive_total = 0
    for path in _workflow_files():
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("uses:") or stripped.startswith("- uses:"):
                naive_total += 1

    parsed = _external_uses()
    local = sum(
        1
        for path in _workflow_files()
        for line in path.read_text(encoding="utf-8").splitlines()
        if (st := line.strip()).startswith(("uses:", "- uses:")) and "uses: ." in st
    )

    assert naive_total > 0, "no `uses:` lines found at all — this check now covers nothing"
    assert len(parsed) + local == naive_total, (
        f"the parser accounts for {len(parsed)} external + {local} local = "
        f"{len(parsed) + local} of {naive_total} `uses:` lines. The ones it no longer "
        "sees are no longer checked by anything in this file."
    )


def test_every_external_action_is_pinned_to_a_commit_sha():
    """No tag or branch refs. A tag is mutable; a SHA is not."""
    uses = _external_uses()
    assert uses, "no external `uses:` found — this check now covers nothing"

    offenders: list[str] = []
    for path, line_no, ref, _rest in uses:
        if "@" not in ref:
            offenders.append(f"{path.name}:{line_no} {ref} (no ref at all)")
            continue
        _action, _, version = ref.partition("@")
        if not _SHA40.match(version):
            offenders.append(f"{path.name}:{line_no} {ref}")

    assert offenders == [], (
        "These actions are pinned to a mutable ref. Whoever controls the action's "
        "repository can repoint it at new code, which then runs here with this "
        "repository's credentials. Pin to the 40-character commit SHA of the release "
        f"and add a `# pin: vX.Y.Z` comment: {offenders}"
    )


def test_every_pin_records_its_version_in_a_comment():
    """A bare SHA cannot be read. This is why the pins went stale unnoticed."""
    offenders: list[str] = []
    for path, line_no, ref, rest in _external_uses():
        if not _PIN_COMMENT.search(rest):
            offenders.append(f"{path.name}:{line_no} {ref.split('@')[0]}")

    assert offenders == [], (
        "These pins have no `# pin: vX.Y.Z` comment, so a reader cannot tell which "
        "version they are without an API call — which is how six of them drifted a "
        f"full major behind before anyone noticed: {offenders}"
    )


@pytest.mark.parametrize("action", ["actions/checkout", "actions/setup-python"])
def test_the_most_used_actions_share_one_pin(action: str):
    """One SHA per action across every workflow.

    `checkout` appears 27 times and `setup-python` 17. A partial bump leaves
    some jobs on an old version indefinitely, and the difference is invisible
    at a glance because the differing part is a hex string.
    """
    pins = {ref.partition("@")[2] for _p, _l, ref, _r in _external_uses() if ref.startswith(action + "@")}
    assert len(pins) <= 1, f"{action} is pinned to {len(pins)} different SHAs: {sorted(pins)}"
