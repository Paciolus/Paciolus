"""Sprint 787 — tie `ToolName` to the tool registry so the two cannot drift again.

Sprint 689 expanded the catalog 12 → 18 and Sprint 717 reconciled the frontend ledger,
but `engagement_model.ToolName` was missed and nothing noticed for six months. The
visible symptom was an Anomaly Summary PDF telling practitioners there were 13
available tools; the invisible one was that a run of any of the six newer tools could
not be recorded against an engagement at all.

`tests/test_catalog_consistency.py` already ties the registry to the frontend ledger.
This file closes the third edge of that triangle: registry ↔ `ToolName`.
"""

from __future__ import annotations

import re
from pathlib import Path

import tools_registry
from engagement_model import ToolName

BACKEND_DIR = Path(__file__).resolve().parents[1]

# ToolName members that are deliberately not marketing audit tools.
# `flux_analysis` is a free-tier diagnostic surface that engagements track like a
# tool run, but it is not one of the 18 sold tools.
NON_CATALOG_TOOLNAMES: frozenset[str] = frozenset({"flux_analysis"})


def _catalog_slugs() -> set[str]:
    return {t.slug for t in tools_registry.TOOLS if t.is_marketing_audit_tool}


def test_every_catalog_tool_is_trackable_on_an_engagement():
    """The failure Sprint 787 fixed: six sold tools had no enum member, so
    `ToolName(slug)` raised in tool_run_recorder and no run could be recorded."""
    enum_values = {t.value for t in ToolName}
    missing = sorted(_catalog_slugs() - enum_values)
    assert not missing, (
        f"These tools are in tools_registry.py but not in ToolName, so their runs "
        f"cannot be recorded against an engagement: {missing}. Add the members and an "
        f"Alembic migration adding the values to the Postgres `toolname` type."
    )


def test_every_toolname_member_is_either_a_catalog_tool_or_declared_non_catalog():
    """The reverse direction: an enum member with no registry entry would appear in
    the workpaper index and anomaly summary as a tool nobody can buy."""
    catalog = _catalog_slugs()
    unexpected = sorted({t.value for t in ToolName} - catalog - NON_CATALOG_TOOLNAMES)
    assert not unexpected, (
        f"ToolName members with no matching marketing audit tool: {unexpected}. Either add "
        f"the tool to tools_registry.py or list it in NON_CATALOG_TOOLNAMES with a reason."
    )


def test_toolname_covers_the_catalog_exactly_plus_declared_extras():
    expected = _catalog_slugs() | NON_CATALOG_TOOLNAMES
    assert {t.value for t in ToolName} == expected


def test_len_toolname_is_not_used_as_the_catalog_size():
    """`len(ToolName)` counts trackable run types, which includes flux_analysis — so
    it is not the number of tools a customer is sold, and never was. Three customer-
    facing strings in the anomaly summary used it as the denominator until Sprint 787."""
    assert len(ToolName) != tools_registry.MARKETING_AUDIT_TOOL_COUNT
    assert len(ToolName) == tools_registry.MARKETING_AUDIT_TOOL_COUNT + len(NON_CATALOG_TOOLNAMES)


def test_anomaly_summary_reports_the_catalog_count_not_the_enum_length():
    """Guards the specific defect: the PDF said "n of 13 available tools"."""
    text = (BACKEND_DIR / "anomaly_summary_generator.py").read_text(encoding="utf-8")
    assert "len(ToolName)" not in text, (
        "anomaly_summary_generator.py uses len(ToolName) as a customer-facing count again. "
        "Use tools_registry.MARKETING_AUDIT_TOOL_COUNT — the enum includes flux_analysis."
    )
    assert "MARKETING_AUDIT_TOOL_COUNT" in text


def test_label_and_reference_tables_cover_every_toolname():
    """A missing label silently degrades to the raw slug in a filed workpaper."""
    from anomaly_summary_generator import TOOL_CROSS_REFERENCES
    from workpaper_index_generator import TOOL_LABELS, TOOL_LEAD_SHEET_REFS

    for table_name, table in (
        ("workpaper_index_generator.TOOL_LABELS", TOOL_LABELS),
        ("workpaper_index_generator.TOOL_LEAD_SHEET_REFS", TOOL_LEAD_SHEET_REFS),
        ("anomaly_summary_generator.TOOL_CROSS_REFERENCES", TOOL_CROSS_REFERENCES),
    ):
        missing = sorted(t.value for t in ToolName if t not in table)
        assert not missing, f"{table_name} is missing entries for: {missing}"


def test_workpaper_references_are_unique():
    """Two tools sharing a workpaper reference would collide in a filed index."""
    from anomaly_summary_generator import TOOL_CROSS_REFERENCES

    refs = list(TOOL_CROSS_REFERENCES.values())
    duplicates = sorted({r for r in refs if refs.count(r) > 1})
    assert not duplicates, f"Duplicate workpaper references: {duplicates}"


def test_migration_covers_every_new_enum_value():
    """The Postgres `toolname` type is a native enum: a member added in Python
    without a migration raises on insert in production but passes every SQLite test."""
    versions = BACKEND_DIR / "migrations" / "alembic" / "versions"
    migration_text = "\n".join(
        p.read_text(encoding="utf-8")
        for p in versions.glob("*.py")
        if "toolname" in p.read_text(encoding="utf-8").lower()
    )
    # The original 12 were created with the type itself; everything added later needs
    # an explicit ALTER TYPE. flux_analysis (Sprint 308) and the Sprint 787 six.
    added_later = {
        "flux_analysis",
        "sod_checker",
        "intercompany_elimination",
        "w2_reconciliation",
        "form_1099",
        "book_to_tax",
        "cash_flow_projector",
    }
    missing = sorted(v for v in added_later if v not in migration_text)
    assert not missing, (
        f"These ToolName values have no ALTER TYPE migration, so inserting them will fail "
        f"on PostgreSQL while passing on SQLite: {missing}"
    )


def test_convergence_classification_covers_every_toolname():
    """Every tool must be classified as convergence-capable or excluded.

    `routes/engagements.py` reads both lists, and an unclassified tool would silently
    drop out of the convergence index rather than raising.
    """
    from domain_config.tool_taxonomy import CONVERGENCE_EXCLUDED, CONVERGENCE_TOOLS

    classified = set(CONVERGENCE_TOOLS) | set(CONVERGENCE_EXCLUDED)
    enum_values = {t.value for t in ToolName}
    assert classified == enum_values, (
        f"unclassified: {sorted(enum_values - classified)}; "
        f"classified but not a ToolName: {sorted(classified - enum_values)}"
    )


def test_convergence_tools_are_exactly_the_tools_with_account_extractors():
    """The classification rule, stated as a test.

    A tool can contribute to the convergence index only if something can pull GL
    account identifiers out of its result — i.e. only if it has an entry in
    ACCOUNT_EXTRACTORS. Before Sprint 787 that equivalence held by coincidence and
    careful maintenance; now adding a tool to CONVERGENCE_TOOLS without writing its
    extractor fails here, naming the missing piece.
    """
    from domain_config.tool_taxonomy import CONVERGENCE_TOOLS
    from shared.account_extractors import ACCOUNT_EXTRACTORS

    assert set(CONVERGENCE_TOOLS) == set(ACCOUNT_EXTRACTORS), (
        f"in CONVERGENCE_TOOLS with no extractor: {sorted(set(CONVERGENCE_TOOLS) - set(ACCOUNT_EXTRACTORS))}; "
        f"has an extractor but not classified as a convergence tool: "
        f"{sorted(set(ACCOUNT_EXTRACTORS) - set(CONVERGENCE_TOOLS))}"
    )


def test_tool_display_labels_cover_every_toolname():
    """A missing label degrades to a raw slug in the workpaper index and UI."""
    from domain_config.tool_taxonomy import TOOL_DISPLAY_LABELS

    missing = sorted(t.value for t in ToolName if t.value not in TOOL_DISPLAY_LABELS)
    assert not missing, f"tool_taxonomy.TOOL_DISPLAY_LABELS is missing: {missing}"


def test_no_stale_toolname_length_literals_in_the_suite():
    """Four separate tests asserted `len(ToolName) == 13`.

    They did not merely fail to catch the Sprint 689 drift — they **defended** it: a
    correct enum expansion turned them red, so the next person could reasonably have
    concluded the expansion was wrong. Any new hardcoded length belongs here instead,
    derived from the registry.
    """
    # Match an assert comparing len(ToolName) directly to a number. Deliberately
    # narrow: the first draft of this check used substring matching and flagged four
    # lines, all false — three docstrings quoting the old assertion to explain why it
    # was removed, and one `assert len(x) == len(ToolName) - 2`, which is the correct
    # derived form.
    pattern = re.compile(r"^\s*assert\s+len\(\s*ToolName\s*\)\s*==\s*\d+")
    offenders: list[str] = []
    for path in sorted((BACKEND_DIR / "tests").glob("test_*.py")):
        if path.name == "test_toolname_catalog_parity.py":
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if pattern.match(line):
                offenders.append(f"{path.name}:{lineno}")
    assert not offenders, (
        f"hardcoded ToolName length assertions: {offenders}. Derive from "
        f"tools_registry.MARKETING_AUDIT_TOOL_COUNT instead — a literal count becomes an "
        f"obstacle to the next correct catalog change."
    )
