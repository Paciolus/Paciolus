"""Sprint 731 — Dependency Sentinel cadence-window deadline gate tests.

Verifies that:
- New outdated security-relevant packages are stamped with today's date.
- Packages stay YELLOW within the cadence window.
- Packages flip to RED past the cadence window (patch=7d, minor=14d).
- Stale entries (packages no longer outdated) are pruned from the first_seen map.
- The first_seen map round-trips correctly through baseline.json.

These are direct unit tests against the helper functions; the full
``run()`` flow is exercised by the nightly job itself.
"""

from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture(autouse=True)
def _isolate_baseline(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Redirect BASELINE_FILE to a tmp file so tests don't mutate the real one."""
    fake_baseline = tmp_path / "baseline.json"
    monkeypatch.setattr(
        "scripts.overnight.config.BASELINE_FILE",
        fake_baseline,
    )
    # Also patch the already-imported module-level reference if the sentinel
    # has already been imported.
    import scripts.overnight.agents.dependency_sentinel as ds  # noqa: WPS433

    monkeypatch.setattr(ds, "BASELINE_FILE", fake_baseline)
    monkeypatch.setattr(ds, "REPORTS_DIR", tmp_path)
    yield fake_baseline


# ---------------------------------------------------------------------------
# _is_past_deadline
# ---------------------------------------------------------------------------


class TestIsPastDeadline:
    def test_patch_under_7d_not_past_deadline(self):
        from scripts.overnight.agents.dependency_sentinel import _is_past_deadline

        five_days_ago = (datetime.date.today() - datetime.timedelta(days=5)).isoformat()
        assert _is_past_deadline("patch", five_days_ago) is False

    def test_patch_over_7d_past_deadline(self):
        from scripts.overnight.agents.dependency_sentinel import _is_past_deadline

        ten_days_ago = (datetime.date.today() - datetime.timedelta(days=10)).isoformat()
        assert _is_past_deadline("patch", ten_days_ago) is True

    def test_minor_under_14d_not_past_deadline(self):
        from scripts.overnight.agents.dependency_sentinel import _is_past_deadline

        ten_days_ago = (datetime.date.today() - datetime.timedelta(days=10)).isoformat()
        assert _is_past_deadline("minor", ten_days_ago) is False

    def test_minor_over_14d_past_deadline(self):
        from scripts.overnight.agents.dependency_sentinel import _is_past_deadline

        twenty_days_ago = (datetime.date.today() - datetime.timedelta(days=20)).isoformat()
        assert _is_past_deadline("minor", twenty_days_ago) is True

    def test_major_no_deadline(self):
        from scripts.overnight.agents.dependency_sentinel import _is_past_deadline

        # Even 365 days ago, major has no deadline in CADENCE_DAYS.
        very_old = (datetime.date.today() - datetime.timedelta(days=365)).isoformat()
        assert _is_past_deadline("major", very_old) is False

    def test_invalid_date_returns_false(self):
        from scripts.overnight.agents.dependency_sentinel import _is_past_deadline

        assert _is_past_deadline("patch", "not-a-date") is False
        assert _is_past_deadline("patch", "") is False


# ---------------------------------------------------------------------------
# first_seen round-trip
# ---------------------------------------------------------------------------


class TestFirstSeenRoundtrip:
    def test_save_and_load_round_trip(self, _isolate_baseline: Path):
        from scripts.overnight.agents.dependency_sentinel import _load_first_seen, _save_first_seen

        original = {"backend:fastapi@0.136.1": "2026-04-20", "backend:stripe@15.1.0": "2026-04-15"}
        _save_first_seen(original)
        loaded = _load_first_seen()
        assert loaded == original

    def test_load_missing_baseline_returns_empty(self, _isolate_baseline: Path):
        from scripts.overnight.agents.dependency_sentinel import _load_first_seen

        # baseline file doesn't exist yet (fixture creates path but not file).
        assert _load_first_seen() == {}

    def test_save_preserves_other_baseline_sections(self, _isolate_baseline: Path):
        # Populate baseline with another section first; verify save() preserves it.
        _isolate_baseline.write_text(
            json.dumps({"coverage_sentinel": {"history": [{"date": "2026-04-01", "percent_covered": 92.0}]}}),
            encoding="utf-8",
        )

        from scripts.overnight.agents.dependency_sentinel import _save_first_seen

        _save_first_seen({"backend:fastapi@0.136.1": "2026-04-20"})

        baseline = json.loads(_isolate_baseline.read_text(encoding="utf-8"))
        assert "coverage_sentinel" in baseline
        assert baseline["coverage_sentinel"]["history"][0]["percent_covered"] == 92.0
        assert baseline["dependency_sentinel"]["first_seen"]["backend:fastapi@0.136.1"] == "2026-04-20"


# ---------------------------------------------------------------------------
# _update_first_seen — stamps new, prunes stale, attaches metadata
# ---------------------------------------------------------------------------


class TestUpdateFirstSeen:
    def test_new_package_gets_stamped_with_today(self):
        from scripts.overnight.agents.dependency_sentinel import _update_first_seen

        pkg = {
            "package": "fastapi",
            "current": "0.136.0",
            "latest": "0.136.1",
            "severity": "patch",
            "watchlist": True,
        }
        updated, first_seen = _update_first_seen([pkg], {})
        today = datetime.date.today().isoformat()
        assert updated[0]["first_seen"] == today
        assert updated[0]["past_deadline"] is False
        assert updated[0]["days_outdated"] == 0
        assert "backend:fastapi@0.136.1" in first_seen

    def test_known_package_uses_existing_date(self):
        from scripts.overnight.agents.dependency_sentinel import _update_first_seen

        pkg = {
            "package": "fastapi",
            "current": "0.136.0",
            "latest": "0.136.1",
            "severity": "patch",
            "watchlist": True,
        }
        eight_days_ago = (datetime.date.today() - datetime.timedelta(days=8)).isoformat()
        first_seen_in = {"backend:fastapi@0.136.1": eight_days_ago}

        updated, first_seen_out = _update_first_seen([pkg], first_seen_in)
        assert updated[0]["first_seen"] == eight_days_ago
        # 8 days > 7-day patch deadline → past deadline.
        assert updated[0]["past_deadline"] is True
        assert updated[0]["days_outdated"] == 8

    def test_stale_entry_pruned(self):
        from scripts.overnight.agents.dependency_sentinel import _update_first_seen

        # No packages outdated this run; the prior first_seen entry should be removed.
        first_seen_in = {"backend:fastapi@0.136.1": "2026-04-15"}
        _, first_seen_out = _update_first_seen([], first_seen_in)
        assert first_seen_out == {}

    def test_partial_pruning(self):
        from scripts.overnight.agents.dependency_sentinel import _update_first_seen

        pkg = {
            "package": "fastapi",
            "current": "0.136.0",
            "latest": "0.136.1",
            "severity": "patch",
            "watchlist": True,
        }
        first_seen_in = {
            "backend:fastapi@0.136.1": "2026-04-15",
            "backend:gone-package@9.9.9": "2026-04-10",
        }
        _, first_seen_out = _update_first_seen([pkg], first_seen_in)
        # fastapi entry preserved (still outdated), gone-package pruned.
        assert "backend:fastapi@0.136.1" in first_seen_out
        assert "backend:gone-package@9.9.9" not in first_seen_out
