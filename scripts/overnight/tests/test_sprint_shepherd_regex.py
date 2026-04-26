"""Sprint 730 — Sprint Shepherd risk-keyword regex regression tests.

The original substring match in ``_find_risk_signals`` triggered YELLOW on any
commit message containing the literal substring "TODO" (or "WIP", "temp", etc.)
even when embedded in a larger word or quoted in a hotfix description. The
2026-04-23 hotfix entry "fix: archive_sprints.sh ... (TODO list bug)" was the
canonical false-positive that motivated this test.

Sprint 730 swapped to word-boundary regex + conventional-commit prefix skip.
This test pins both fixes so a future "simplification" doesn't reintroduce
either failure mode.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.overnight.agents.sprint_shepherd import _find_risk_signals


def _commit(message: str, sha: str = "deadbee") -> dict:
    return {"hash": sha, "message": message, "timestamp": "2026-04-25T12:00:00Z", "author": "Test"}


# ---------------------------------------------------------------------------
# Word-boundary matching
# ---------------------------------------------------------------------------


class TestWordBoundary:
    def test_standalone_todo_is_flagged(self):
        risky = _find_risk_signals([_commit("Sprint 999: TODO before launch")])
        assert len(risky) == 1
        assert risky[0]["keyword"] == "TODO"

    def test_substring_in_larger_word_not_flagged(self):
        # The 2026-04-23 false-positive: "TODO" appears inside the parenthesized
        # description of a fix: hotfix. Word-boundary regex should NOT match
        # ``pytodo`` or ``TODOlistbug``-style embeddings.
        risky = _find_risk_signals([_commit("Sprint 999: refactor pytodolist module")])
        assert risky == []

    def test_word_boundary_on_punctuation(self):
        # "TODO." and "TODO," should still match — punctuation is a word boundary.
        for tail in (".", ",", ":", ";", ")", "]"):
            risky = _find_risk_signals([_commit(f"Sprint X: rebuild it (TODO{tail} fix later)")])
            assert len(risky) == 1, f"Expected match before '{tail}'"

    def test_case_insensitive_match(self):
        risky = _find_risk_signals([_commit("Sprint X: todo soonish")])
        assert len(risky) == 1
        assert risky[0]["keyword"].lower() == "todo"

    def test_all_keywords_independently(self):
        for keyword in ("WIP", "temp", "TODO", "fixme", "hack", "broken"):
            commits = [_commit(f"Sprint X: {keyword} placeholder")]
            risky = _find_risk_signals(commits)
            assert len(risky) == 1, f"Failed to flag {keyword}"


# ---------------------------------------------------------------------------
# Conventional-commit prefix skip
# ---------------------------------------------------------------------------


class TestSafePrefixSkip:
    def test_fix_prefix_skipped_even_with_todo(self):
        # The canonical false-positive from 2026-04-23.
        risky = _find_risk_signals([
            _commit("fix: archive_sprints.sh number-extraction (TODO list bug)")
        ])
        assert risky == [], "fix: prefix should suppress risk-signal flagging"

    def test_chore_prefix_skipped(self):
        risky = _find_risk_signals([_commit("chore: bump TODO-list dep to 2.0")])
        assert risky == []

    def test_sprint_prefix_still_flags(self):
        # Sprint commits SHOULD be checked — they're the substantive work.
        risky = _find_risk_signals([_commit("Sprint 999: temp shim until next week")])
        assert len(risky) == 1
        assert risky[0]["keyword"] == "temp"

    def test_no_prefix_still_flags(self):
        risky = _find_risk_signals([_commit("WIP refactor of payroll module")])
        assert len(risky) == 1
        assert risky[0]["keyword"] == "WIP"

    def test_safe_prefixes_full_list(self):
        for prefix in ("fix:", "chore:", "docs:", "style:", "test:", "build:", "ci:", "perf:"):
            risky = _find_risk_signals([_commit(f"{prefix} touch up TODO doc")])
            assert risky == [], f"{prefix} should suppress flagging"


# ---------------------------------------------------------------------------
# Empty / edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_empty_commit_list(self):
        assert _find_risk_signals([]) == []

    def test_empty_message_does_not_crash(self):
        risky = _find_risk_signals([_commit("")])
        assert risky == []

    def test_single_keyword_per_commit(self):
        # If a commit hits multiple keywords, only the first one is reported.
        # This is the original behavior preserved by ``re.search`` returning
        # the leftmost match.
        risky = _find_risk_signals([_commit("Sprint X: TODO and WIP and hack")])
        assert len(risky) == 1
