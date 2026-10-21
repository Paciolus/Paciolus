"""Sprint 717 — Catalog consistency tests.

Enforces the single-source-of-truth contract introduced in Sprint 717:

1. `backend/tools_registry.py` `MARKETING_AUDIT_TOOL_COUNT` matches
   `frontend/src/content/tool-ledger.ts` `CANONICAL_TOOL_COUNT` and
   `TOOL_LEDGER.length`.

2. Every tool in the registry has a corresponding entry in `tool-ledger.ts`
   (matched by slug == LedgerEntry.id), and vice-versa.

3. Every standard cited by any tool's `standards` tuple is registered in
   `standards_registry.py`.

4. Every test ID in `payroll_testing_memo_generator.PAYROLL_TEST_DESCRIPTIONS`
   has the correct prefix and a non-empty description (smoke check that
   the dict isn't half-deleted).

These tests fail at PR time if any drift returns. Run via `pytest
backend/tests/test_catalog_consistency.py -v`.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import standards_registry
import tools_registry

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL_LEDGER_PATH = REPO_ROOT / "frontend" / "src" / "content" / "tool-ledger.ts"


def _read_tool_ledger() -> str:
    return TOOL_LEDGER_PATH.read_text(encoding="utf-8")


def _ledger_canonical_count(ledger_text: str) -> int:
    match = re.search(r"export\s+const\s+CANONICAL_TOOL_COUNT\s*=\s*(\d+)", ledger_text)
    if not match:
        raise AssertionError("tool-ledger.ts does not declare `export const CANONICAL_TOOL_COUNT`")
    return int(match.group(1))


def _ledger_entry_ids(ledger_text: str) -> list[str]:
    return re.findall(r"^\s*id:\s*'([^']+)'", ledger_text, flags=re.MULTILINE)


# ───────────────────────── Tests ─────────────────────────


def test_marketing_count_matches_ledger_canonical_constant():
    """Registry MARKETING_AUDIT_TOOL_COUNT == ledger CANONICAL_TOOL_COUNT."""
    ledger_text = _read_tool_ledger()
    ledger_count = _ledger_canonical_count(ledger_text)
    assert tools_registry.MARKETING_AUDIT_TOOL_COUNT == ledger_count, (
        f"Registry MARKETING_AUDIT_TOOL_COUNT={tools_registry.MARKETING_AUDIT_TOOL_COUNT} "
        f"but tool-ledger.ts CANONICAL_TOOL_COUNT={ledger_count}. "
        "Update one or the other so they agree."
    )


def test_ledger_entry_count_matches_canonical_constant():
    """tool-ledger.ts entry count must equal its CANONICAL_TOOL_COUNT."""
    ledger_text = _read_tool_ledger()
    ledger_count = _ledger_canonical_count(ledger_text)
    entry_ids = _ledger_entry_ids(ledger_text)
    assert len(entry_ids) == ledger_count, (
        f"tool-ledger.ts has {len(entry_ids)} entries but CANONICAL_TOOL_COUNT={ledger_count}"
    )


def test_every_marketing_tool_has_ledger_entry():
    """Every registry tool with is_marketing_audit_tool=True appears in tool-ledger.ts."""
    ledger_text = _read_tool_ledger()
    ledger_ids = set(_ledger_entry_ids(ledger_text))
    registry_marketing_slugs = {t.slug for t in tools_registry.marketing_audit_tools()}

    missing = registry_marketing_slugs - ledger_ids
    extra = ledger_ids - registry_marketing_slugs

    assert not missing, (
        f"Tools in `tools_registry.marketing_audit_tools()` but not in tool-ledger.ts: {sorted(missing)}"
    )
    assert not extra, f"Entries in tool-ledger.ts not flagged is_marketing_audit_tool=True in registry: {sorted(extra)}"


def test_every_cited_standard_is_registered():
    """Every standards code referenced by any tool must exist in standards_registry."""
    cited: set[str] = set()
    for tool in tools_registry.all_tools():
        cited.update(tool.standards)

    registered = set(standards_registry.all_codes())
    unregistered = cited - registered

    assert not unregistered, (
        f"Standards cited by tools_registry but missing from standards_registry: {sorted(unregistered)}. "
        "Either register the standard in standards_registry.py or correct the citation."
    )


def test_no_duplicate_tool_slugs():
    """Tool slugs must be unique across the registry."""
    slugs = [t.slug for t in tools_registry.all_tools()]
    duplicates = {slug for slug in slugs if slugs.count(slug) > 1}
    assert not duplicates, f"Duplicate tool slugs: {sorted(duplicates)}"


def test_no_duplicate_standard_codes():
    """Standard codes must be unique across the registry."""
    codes = [s.code for s in standards_registry.STANDARDS]
    duplicates = {code for code in codes if codes.count(code) > 1}
    assert not duplicates, f"Duplicate standard codes: {sorted(duplicates)}"


def test_payroll_memo_descriptions_complete():
    """PR-T1 through PR-T13 must each have a description in PAYROLL_TEST_DESCRIPTIONS.

    Backfilled in Sprint 717 — PR-T12 and PR-T13 were missing per the
    Accounting Methodology Audit (2026-04-24).
    """
    from payroll_testing_memo_generator import PAYROLL_TEST_DESCRIPTIONS

    expected_keys = {f"PR-T{i}" for i in range(1, 14)}
    actual_keys = set(PAYROLL_TEST_DESCRIPTIONS.keys())
    missing = expected_keys - actual_keys
    assert not missing, (
        f"PAYROLL_TEST_DESCRIPTIONS missing keys: {sorted(missing)}. "
        "Per CLAUDE.md the payroll engine ships 13 tests; every test ID needs a description."
    )

    for key in expected_keys:
        desc = PAYROLL_TEST_DESCRIPTIONS[key]
        assert isinstance(desc, str) and desc.strip(), f"PAYROLL_TEST_DESCRIPTIONS[{key!r}] must be a non-empty string"


def test_marketing_count_is_exactly_eighteen():
    """Sprint 717 + Sprint 689 destination: 18 audit tools."""
    assert tools_registry.MARKETING_AUDIT_TOOL_COUNT == 18, (
        f"MARKETING_AUDIT_TOOL_COUNT={tools_registry.MARKETING_AUDIT_TOOL_COUNT}; "
        "Sprint 717 (and Sprint 689 destination) expects 18. If this changes, update "
        "this test, the marketing surfaces, and CLAUDE.md together."
    )


@pytest.mark.parametrize("tool", tools_registry.all_tools(), ids=lambda t: t.slug)
def test_tool_summary_nonempty(tool: tools_registry.Tool):
    """Every registry tool has a non-empty summary (used by tool-ledger.ts)."""
    assert tool.summary.strip(), f"Tool {tool.slug} has empty summary"


@pytest.mark.parametrize("tool", tools_registry.all_tools(), ids=lambda t: t.slug)
def test_tool_display_name_nonempty(tool: tools_registry.Tool):
    """Every registry tool has a non-empty display name."""
    assert tool.display_name.strip(), f"Tool {tool.slug} has empty display_name"


# ---------------------------------------------------------------------------
# Sprint 784b — features/status.json is the fourth edge of the catalog contract
# ---------------------------------------------------------------------------
#
# `AGENTS.md` makes `features/status.json` step 3 of every session's startup —
# "full feature inventory, what is built and what is not". It covered the
# pre-Sprint-689 catalog, so for six months a third of the tools were invisible
# in the file a new session is told to read first, and nothing guarded it. The
# registry↔ledger edge was tested, the registry↔standards edge was tested; this
# one was not.

# status.json uses prose ids; the registry uses slugs. Only the genuinely
# different ones are listed, and test_status_json_alias_map_is_minimal keeps
# this honest rather than letting it absorb drift.
_STATUS_ID_ALIASES: dict[str, str] = {
    "trial_balance": "tb-diagnostics",
    "multi_period": "multi-period-comparison",
    "ap_testing": "ap-payment-testing",
    "sod_checker": "segregation-of-duties",
    "w2_reconciliation": "w2-w3-reconciliation",
    "form_1099": "form-1099-preparation",
    "book_to_tax": "book-to-tax-reconciliation",
}


def _status_entries() -> list[dict]:
    import json

    path = Path(__file__).resolve().parents[2] / "features" / "status.json"
    assert path.exists(), "features/status.json is missing"
    return json.loads(path.read_text(encoding="utf-8"))


def _expected_status_id(slug: str) -> str:
    return _STATUS_ID_ALIASES.get(slug, slug.replace("_", "-"))


def test_every_marketing_tool_has_a_status_json_entry():
    """A tool absent from the feature inventory is invisible to the next session."""
    ids = {e["id"] for e in _status_entries()}
    missing = [
        f"{t.slug} (expected id {_expected_status_id(t.slug)!r})"
        for t in tools_registry.TOOLS
        if t.is_marketing_audit_tool and _expected_status_id(t.slug) not in ids
    ]
    assert not missing, f"features/status.json has no entry for: {missing}"


def test_status_json_alias_map_is_minimal():
    """Every alias must still be needed.

    An alias whose slug-derived id would already match is dead weight that hides
    the next rename — the same failure as the GUIDE_TOOL_HEADINGS entry that
    silently stopped matching a chapter title in Sprint 784c.
    """
    redundant = [slug for slug, alias in _STATUS_ID_ALIASES.items() if slug.replace("_", "-") == alias]
    assert not redundant, f"these aliases are redundant and should be removed: {redundant}"

    slugs = {t.slug for t in tools_registry.TOOLS}
    unknown = [slug for slug in _STATUS_ID_ALIASES if slug not in slugs]
    assert not unknown, f"these aliases reference slugs that no longer exist: {unknown}"


def test_status_json_entries_are_well_formed():
    """Catches a half-written entry, which reads as coverage without being it."""
    required = {"id", "category", "description", "verification_steps", "status"}
    problems: list[str] = []
    for e in _status_entries():
        missing = required - set(e)
        if missing:
            problems.append(f"{e.get('id', '<no id>')}: missing {sorted(missing)}")
            continue
        if not e["description"].strip():
            problems.append(f"{e['id']}: empty description")
        if not e["verification_steps"]:
            problems.append(f"{e['id']}: no verification steps")
        if e["status"] not in {"complete", "partial", "not-started"}:
            problems.append(f"{e['id']}: unexpected status {e['status']!r}")
    assert not problems, problems
