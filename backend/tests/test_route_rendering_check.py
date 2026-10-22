"""The route-rendering checker — Sprint 786b.

`scripts/check_route_rendering.py` enforces an invariant that `CLAUDE.md` and
the project memory both state and **nothing checked**: every page route must be
`ƒ (Dynamic)`. Nonce-based CSP needs HTML generated per request, because a
prerendered page carries a build-time nonce that will not match the one the
proxy sends, and every inline script on it is then blocked.

The invariant held only because `await headers()` in the root layout forces
dynamic rendering — one line, in one file, removable by anyone who does not
know why it is there.

The checker parses build output, so it needs the same treatment every parser
in this sprint has needed: **a test that it parsed everything**, not just that
it reached a verdict. The fixture below is the real route table from a
`npm run build` on 2026-10-22, trimmed in the middle but structurally intact —
including the `┌` tree-root line, which a naive `^[├└]` scan misses and which
is the homepage.
"""

from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CHECKER = REPO_ROOT / "scripts" / "check_route_rendering.py"


def _load():
    spec = importlib.util.spec_from_file_location("check_route_rendering", CHECKER)
    assert spec and spec.loader, "could not load the checker"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checker = _load()

# Real output, 2026-10-22, from Next.js 16.4.2 with Turbopack — the version
# header is copied rather than remembered, after a first draft invented
# "16.2.0" in a fixture whose docstring claimed it was real output.
#
# The `┌` on the homepage is load-bearing: a scan for `^[├└]` finds 65 routes
# here and misses `/` entirely.
REAL_OUTPUT = """
   ▲ Next.js 16.4.2 (Turbopack)

 ✓ Compiled successfully in 8.0s
 ✓ Collecting page data
 ✓ Generating static pages (2/2)

Route (app)                                 Size  First Load JS
┌ ƒ /                                    5.42 kB         142 kB
├ ƒ /_not-found                            124 B         102 kB
├ ƒ /about                                3.11 kB         139 kB
├ ƒ /api/telemetry                         124 B         102 kB
├ ○ /icon.png                                0 B            0 B
├ ƒ /pricing                             6.84 kB         148 kB
├ ○ /sitemap.xml                             0 B            0 B
├ ƒ /tools/trial-balance                 12.1 kB         171 kB
└ ƒ /verify-email                        2.98 kB         136 kB

ƒ Proxy (Middleware)                      58.2 kB

○  (Static)   prerendered as static content
ƒ  (Dynamic)  server-rendered on demand
"""


def test_the_checker_exists_and_is_runnable():
    assert CHECKER.is_file(), f"missing {CHECKER}"


def test_it_parses_every_route_including_the_tree_root():
    """The coverage self-check.

    A parser that silently skips a line shrinks the check without shrinking
    the confidence. The `┌` case is the one that actually bit: the homepage
    sits on the tree-root line, so a `^[├└]` scan omits it and reports success
    over everything else.
    """
    routes = checker.parse_routes(REAL_OUTPUT)
    paths = {p for _m, p in routes}

    naive = {m.group(1) for m in re.finditer(r"^[├└]\s+[ƒ○]\s+(/\S*)", REAL_OUTPUT, re.MULTILINE)}
    assert naive, "the naive comparison found nothing — this check proves nothing"
    assert naive < paths, "the parser should see strictly more than a naive scan of ├/└ lines"
    assert "/" in paths, "the tree-root route was skipped — the exact gap this test exists for"
    assert len(routes) == 9, f"expected 9 routes in the fixture, parsed {len(routes)}: {sorted(paths)}"


def test_the_legend_is_not_mistaken_for_a_route():
    """`○  (Static)   prerendered as static content` looks like a route line."""
    routes = checker.parse_routes(REAL_OUTPUT)
    for _marker, path in routes:
        assert not path.startswith("("), f"parsed a legend line as a route: {path}"
    assert "(Static)" not in {p for _m, p in routes}


@pytest.mark.parametrize(
    "path,expected",
    [
        ("/icon.png", True),
        ("/sitemap.xml", True),
        ("/robots.txt", True),
        ("/", False),
        ("/pricing", False),
        ("/tools/trial-balance", False),
        ("/api/telemetry", False),
        ("/_not-found", False),
    ],
)
def test_asset_detection_is_derived_from_the_path(path, expected):
    """Assets are allowed to be static; pages are not.

    Derived from the path rather than a hand-kept allowlist, so adding an
    asset does not mean editing the checker — Sprint 792's ranking, where an
    explicit list of paths is the tier that silently stops covering things.
    """
    assert checker.is_asset(path) is expected


def _run(text: str, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    target = tmp_path / "build.txt"
    target.write_text(text, encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(CHECKER), str(target)],
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_real_output_passes(tmp_path):
    result = _run(REAL_OUTPUT, tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "All 7 page routes are dynamic." in result.stdout, result.stdout


def test_a_static_page_route_fails(tmp_path):
    """The whole point. A prerendered page breaks nonce-based CSP."""
    broken = REAL_OUTPUT.replace("├ ƒ /pricing", "├ ○ /pricing")
    result = _run(broken, tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "/pricing" in result.stdout
    assert "nonce" in result.stdout.lower(), "the failure should say why it matters"


def test_a_static_asset_route_still_passes(tmp_path):
    """`/icon.png` being prerendered is correct, not a violation."""
    result = _run(REAL_OUTPUT, tmp_path)
    assert result.returncode == 0
    assert "/icon.png" in result.stdout


@pytest.mark.parametrize(
    "text",
    [
        "",
        "   ",
        "Build failed with 3 errors.",
        "Route (app)\n(no routes)\n",
    ],
)
def test_output_with_no_route_table_fails_rather_than_passing(text, tmp_path):
    """A check that cannot see its subject must not report success.

    This is the shape the whole session kept finding — a gate that cannot
    distinguish "nothing wrong" from "I did not look". If the build failed or
    Next.js changed its output format, this exits 1.
    """
    result = _run(text, tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "no route table" in result.stdout.lower()


def test_a_table_of_only_assets_fails(tmp_path):
    """Guards against the asset heuristic swallowing the whole table.

    If a future Next.js version appended sizes such that every path looked
    like it had an extension, the page list would be empty and every
    assertion below it would be vacuously true.
    """
    assets_only = """
Route (app)
┌ ○ /icon.png                                0 B            0 B
├ ○ /sitemap.xml                             0 B            0 B

○  (Static)   prerendered as static content
"""
    result = _run(assets_only, tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "none of them is a page" in result.stdout
