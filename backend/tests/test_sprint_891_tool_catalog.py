"""Sprint 891 (CEO brief 16A, review ST-07): the tool registry drives the live catalogs."""

import re
import subprocess
import sys
from pathlib import Path

from routes.activity import TOOL_LABELS
from tools_registry import TOOLS

REPO = Path(__file__).resolve().parents[2]


def test_generated_frontend_catalog_is_current():
    out = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "generate_tool_catalog_ts.py"), "--check"],
        capture_output=True,
        text=True,
    )
    assert out.returncode == 0, out.stdout + out.stderr


def test_every_catalog_tool_has_an_activity_label_not_its_slug():
    for t in TOOLS:
        assert t.slug in TOOL_LABELS
        assert TOOL_LABELS[t.slug] != t.slug, t.slug
    assert TOOL_LABELS["book_to_tax"] == "Book-to-Tax"
    assert TOOL_LABELS["flux_analysis"] == "Flux Analysis"  # explicit override


def test_every_marketed_tool_is_on_the_dashboard_with_a_page():
    for t in TOOLS:
        if not t.is_marketing_audit_tool:
            continue
        assert t.dashboard_description and t.dashboard_icon, t.slug
        assert t.href and t.short_label, t.slug


def test_every_href_is_a_real_page():
    for t in TOOLS:
        if t.href:
            page = REPO / "frontend" / "src" / "app" / Path(*t.href.strip("/").split("/")) / "page.tsx"
            assert page.exists(), (t.slug, t.href)


def test_dashboard_icons_exist():
    icons_ts = (REPO / "frontend" / "src" / "components" / "dashboard" / "ToolIcon.tsx").read_text(encoding="utf-8")
    for t in TOOLS:
        if t.dashboard_icon:
            assert re.search(rf"\b{t.dashboard_icon}\s*:", icons_ts), (t.slug, t.dashboard_icon)


def test_command_palette_links_match_the_catalog():
    """The palette keeps its own labels and keywords (explicit overrides), but every tool's link is the catalog's."""
    registry = (REPO / "frontend" / "src" / "lib" / "commandRegistry.ts").read_text(encoding="utf-8")
    for href, tool_name in re.findall(r"href: '([^']+)', toolName: '([a-z_0-9]+)'", registry):
        tool = next((t for t in TOOLS if t.slug == tool_name), None)
        if tool is not None:
            assert tool.href == href, (tool_name, href, tool.href)
