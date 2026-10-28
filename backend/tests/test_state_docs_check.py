"""Sprint 857 — tests for scripts/check_state_docs.py (state-doc drift check).

The script is wired into CI's Lint Baseline Gate job; these tests pin its parsing and
failure modes, and run it once against the real repo docs.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "check_state_docs.py"


def _load():
    spec = importlib.util.spec_from_file_location("check_state_docs", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


csd = _load()


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A tiny git repo with main (two commits) and an unrelated side branch."""
    _git(tmp_path, "init", "-q", "-b", "main")
    _git(tmp_path, "config", "user.email", "t@example.com")
    _git(tmp_path, "config", "user.name", "t")
    _git(tmp_path, "config", "commit.gpgsign", "false")
    for n in ("one", "two"):
        (tmp_path / f"{n}.txt").write_text(n)
        _git(tmp_path, "add", ".")
        _git(tmp_path, "commit", "-q", "-m", n)
    _git(tmp_path, "checkout", "-q", "-b", "side", "HEAD~1")
    (tmp_path / "side.txt").write_text("side")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-q", "-m", "side")
    _git(tmp_path, "checkout", "-q", "main")
    return tmp_path


def _state(repo: Path, body: str) -> Path:
    path = repo / "SESSION_STATE.md"
    path.write_text(f"# Session State\n\n{body}\n", encoding="utf-8")
    return path


# ── Check 1: main SHA ancestry ─────────────────────────────────────────────


def test_ancestor_sha_passes(repo: Path) -> None:
    sha = _git(repo, "rev-parse", "--short", "HEAD~1")
    assert csd.check_main_sha(_state(repo, f"**Main SHA:** `{sha}`"), repo) == []


def test_head_sha_passes(repo: Path) -> None:
    sha = _git(repo, "rev-parse", "HEAD")
    assert csd.check_main_sha(_state(repo, f"**Main SHA:** `{sha}`"), repo) == []


def test_non_ancestor_sha_fails(repo: Path) -> None:
    sha = _git(repo, "rev-parse", "--short", "side")
    errors = csd.check_main_sha(_state(repo, f"**Main SHA:** `{sha}`"), repo)
    assert len(errors) == 1 and "not an ancestor" in errors[0]
    assert "git rev-parse --short origin/main" in errors[0]


def test_unknown_sha_fails_and_mentions_shallow_clone(repo: Path) -> None:
    errors = csd.check_main_sha(_state(repo, "**Main SHA:** `deadbeef`"), repo)
    assert len(errors) == 1 and "does not resolve" in errors[0] and "fetch-depth" in errors[0]


def test_missing_line_fails_with_format(repo: Path) -> None:
    errors = csd.check_main_sha(_state(repo, "`main` is `abc1234` and live."), repo)
    assert len(errors) == 1 and "missing" in errors[0] and "**Main SHA:**" in errors[0]


def test_two_lines_fail(repo: Path) -> None:
    sha = _git(repo, "rev-parse", "--short", "HEAD")
    errors = csd.check_main_sha(_state(repo, f"**Main SHA:** `{sha}`\n**Main SHA:** `{sha}`"), repo)
    assert len(errors) == 1 and "2 times" in errors[0]


def test_inline_mention_is_not_the_line() -> None:
    # The format rule documented in SESSION_STATE.md quotes the line mid-sentence; only a
    # line that *starts* with it counts.
    assert csd.find_main_sha("keep one line like **Main SHA:** `abc1234` here") == []
    assert csd.find_main_sha("**Main SHA:** `abc1234`") == ["abc1234"]


# ── Check 2: sprint-id uniqueness ──────────────────────────────────────────


def _docs(tmp_path: Path, todo: str, archive: str = "") -> list[Path]:
    (tmp_path / "todo.md").write_text(todo, encoding="utf-8")
    (tmp_path / "archive.md").write_text(archive, encoding="utf-8")
    return [tmp_path / "todo.md", tmp_path / "archive.md"]


def test_same_id_different_titles_fails(tmp_path: Path) -> None:
    files = _docs(tmp_path, "### Sprint 846: Billing copy\n", "### Sprint 846: Parser hardening\n")
    errors = csd.check_sprint_ids(files, tmp_path, allow=frozenset())
    assert len(errors) == 1 and "Sprint 846" in errors[0]
    assert "todo.md:1" in errors[0] and "archive.md:1" in errors[0]


def test_same_sprint_in_todo_and_archive_passes(tmp_path: Path) -> None:
    files = _docs(tmp_path, "### Sprint 846: Billing copy\n", "### Sprint 846: Billing copy — COMPLETE\n")
    assert csd.check_sprint_ids(files, tmp_path, allow=frozenset()) == []


def test_sub_sprints_are_distinct_ids(tmp_path: Path) -> None:
    files = _docs(tmp_path, "### Sprint 689: Catalog\n### Sprint 689a: SoD\n### Sprint 689b: IC\n")
    assert csd.check_sprint_ids(files, tmp_path, allow=frozenset()) == []


def test_heading_variants_parse(tmp_path: Path) -> None:
    files = _docs(
        tmp_path,
        "### Sprint 195 — Upload hardening\n### Sprint 699 (A): Multi-currency\n"
        "### Sprint 96.5: Test infra\n### Sprint A: Lettered phase\n",
    )
    found = csd.collect_headings(files, tmp_path)
    assert set(found) == {"195", "699", "96.5"}


def test_allowlist_suppresses_only_listed_ids(tmp_path: Path) -> None:
    files = _docs(tmp_path, "### Sprint 1: X\n### Sprint 2: X\n", "### Sprint 1: Y\n### Sprint 2: Y\n")
    errors = csd.check_sprint_ids(files, tmp_path, allow=frozenset({"1"}))
    assert len(errors) == 1 and "Sprint 2 " in errors[0]


def test_allowlist_is_exactly_the_historical_set() -> None:
    """A stale allowlist entry hides nothing today but would mask a future reuse of that id."""
    found = csd.collect_headings(csd.sprint_doc_files(REPO_ROOT), REPO_ROOT)
    assert set(csd.duplicate_ids(found)) == csd.HISTORICAL_DUPLICATES


# ── The real repo ──────────────────────────────────────────────────────────


def test_real_repo_sprint_ids_unique() -> None:
    assert csd.check_sprint_ids(csd.sprint_doc_files(REPO_ROOT), REPO_ROOT) == []


def test_real_repo_has_main_sha_line() -> None:
    text = (REPO_ROOT / "SESSION_STATE.md").read_text(encoding="utf-8")
    assert len(csd.find_main_sha(text)) == 1


def test_real_repo_main_sha_is_ancestor() -> None:
    # Backend Tests check out at depth 1; ancestry is enforced by the full-history
    # Lint Baseline Gate step instead.
    shallow = _git(REPO_ROOT, "rev-parse", "--is-shallow-repository")
    if shallow == "true":
        pytest.skip("shallow clone — ancestry checked in the Lint Baseline Gate job")
    assert csd.check_main_sha(REPO_ROOT / "SESSION_STATE.md", REPO_ROOT) == []
