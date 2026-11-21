"""Sprint 891 (CEO brief 16C, review ST-17): entry documents name the real commands and counts."""

import json
import re
from pathlib import Path

from tools_registry import TOOLS_BY_SLUG

REPO = Path(__file__).resolve().parents[2]
AGENTS = (REPO / "AGENTS.md").read_text(encoding="utf-8")
CONTRIBUTING = (REPO / "CONTRIBUTING.md").read_text(encoding="utf-8")
PACKAGE = json.loads((REPO / "frontend" / "package.json").read_text(encoding="utf-8"))
STATUS = json.loads((REPO / "features" / "status.json").read_text(encoding="utf-8"))


def test_every_npm_run_command_in_agents_md_exists():
    for script in re.findall(r"npm run ([a-z:-]+)", AGENTS):
        assert script in PACKAGE["scripts"], script
    assert "next lint" not in AGENTS


def test_agents_md_does_not_count_multi_currency_among_the_18():
    line = next(l for l in AGENTS.splitlines() if "18 diagnostic tools" in l)
    assert "side-car" in line and "tools_registry.py" in line


def test_contributing_states_the_mypy_baseline_ci_uses():
    ci = (REPO / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "lint-baseline.json" in ci and "mypy" in ci
    assert "zero errors" not in CONTRIBUTING
    assert "lint-baseline.json" in CONTRIBUTING


_SLUG = {
    "journal-entry-testing": "journal_entry_testing",
    "ap-payment-testing": "ap_testing",
    "payroll-testing": "payroll_testing",
    "revenue-testing": "revenue_testing",
    "ar-aging": "ar_aging",
    "fixed-asset-testing": "fixed_asset_testing",
    "inventory-testing": "inventory_testing",
}


def test_feature_inventory_test_counts_equal_the_registry():
    for entry in STATUS:
        if entry.get("id") in _SLUG:
            n = int(re.search(r"(\d+)-test", entry["description"]).group(1))
            assert n == TOOLS_BY_SLUG[_SLUG[entry["id"]]].test_count, entry["id"]


def test_old_baseline_is_a_pointer_page():
    text = (REPO / "docs" / "audit" / "BASELINE.md").read_text(encoding="utf-8")
    assert "superseded" in text.lower() and "single source of truth" not in text
