"""
Sprint 810 (finding T-4) — the nightly brief must say which tree it tested.

`reports/nightly/2026-10-22.md` published **RED** with 14 failures across
`test_npm_audit_gate.py` and `test_pip_audit_gate.py`. Re-run on the tree later
the same day: **60 passed, 0 failed**. The suite runs at 02:00 and the fixes
landed during the day. The DEC report records the identical artifact for the
prior day — two consecutive briefs whose headline verdict was wrong by clock.

The danger is not the wrong number. It is that a RED which is routinely a timing
artifact trains its reader to discount RED, which is how a real one gets missed.
A verdict with no record of what it is a verdict *about* cannot be checked.

Why these tests shell out: `scripts/overnight/briefing_compiler.py` imports
`scripts.overnight.config`, and from the backend test context the name `scripts`
resolves to **`backend/scripts`**, which shadows the repo-root package. Fixing
that by reordering `sys.path` in-process would change how every other test
resolves `scripts.*`, so the compiler is exercised in a subprocess rooted at the
repository instead.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

_PROBE = """
import json, sys
sys.path.insert(0, {root!r})
from scripts.overnight.briefing_compiler import _head_sha, _supersession_notice

a, b = "a" * 40, "b" * 40
print(json.dumps({{
    "head": _head_sha(),
    "unchanged": _supersession_notice(a, a),
    "moved": _supersession_notice(a, b),
    "tested_unknown": _supersession_notice(None, b),
    "head_unreadable": _supersession_notice(a, None),
    "both_unknown": _supersession_notice(None, None),
}}))
"""


@pytest.fixture(scope="module")
def probe() -> dict[str, str | None]:
    completed = subprocess.run(
        [sys.executable, "-c", _PROBE.format(root=str(REPO_ROOT))],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert completed.returncode == 0, f"probe failed:\n{completed.stderr}"
    # The compiler prints a dev-mode warning on import; take the last JSON line.
    payload = [line for line in completed.stdout.splitlines() if line.startswith("{")]
    assert payload, f"no JSON in probe output:\n{completed.stdout}\n{completed.stderr}"
    return json.loads(payload[-1])


class TestTestedShaIsRecorded:
    def test_head_sha_is_a_full_commit_hash(self, probe):
        sha = probe["head"]

        assert sha is not None, "the compiler cannot read HEAD, so it cannot stamp a brief"
        assert len(sha) == 40, sha
        assert all(c in "0123456789abcdef" for c in sha), sha

    def test_the_report_template_stamps_the_tested_commit(self):
        """
        The stamp has to reach the artifact, not just the return payload — the
        brief is what a human reads at 08:00.
        """
        source = (REPO_ROOT / "scripts" / "overnight" / "briefing_compiler.py").read_text(encoding="utf-8")

        assert "**Tested commit:**" in source
        assert "{supersession}" in source
        assert '"tested_sha": tested_sha' in source


class TestSupersessionNotice:
    def test_an_unchanged_tree_says_the_verdict_still_applies(self, probe):
        notice = probe["unchanged"]

        assert "still HEAD" in notice
        assert "SUPERSEDED" not in notice
        assert "aaaaaaaa" in notice

    def test_a_moved_tree_is_marked_superseded(self, probe):
        notice = probe["moved"]

        assert "SUPERSEDED" in notice
        # Both SHAs, so the reader can see that the tree has moved.
        assert "aaaaaaaa" in notice
        assert "bbbbbbbb" in notice
        # And the actionable instruction, which is the whole point.
        assert "re-run" in notice.lower()

    def test_a_superseded_notice_explains_why_this_matters(self, probe):
        """
        The reason belongs in the artifact, not only in the sprint notes. A
        reader who has learned to discount RED needs to see why this brief might
        be one of those.
        """
        notice = probe["moved"]

        assert "T-4" in notice
        assert "02:00" in notice

    def test_an_unknown_tested_sha_is_stated_rather_than_hidden(self, probe):
        notice = probe["tested_unknown"]

        assert "unknown" in notice.lower()
        assert "cannot be confirmed" in notice

    def test_an_unreadable_head_is_stated_rather_than_assumed_equal(self, probe):
        """
        Being unable to read HEAD must not render as 'still HEAD'. Defaulting to
        the reassuring answer is how a stale verdict looks current.
        """
        notice = probe["head_unreadable"]

        assert "still HEAD" not in notice
        assert "could not be read" in notice

    def test_the_notice_is_a_blockquote_so_it_renders_above_the_summary(self, probe):
        for key in ("unchanged", "moved", "tested_unknown", "head_unreadable", "both_unknown"):
            assert probe[key].startswith("> "), f"{key}: {probe[key]}"
