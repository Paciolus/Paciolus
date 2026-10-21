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


# Sprint 308 added `flux_analysis` to the Postgres `toolname` type in lowercase
# (migration f8a3d1c09b72) while the ORM binds `FLUX_ANALYSIS`. On a database carrying
# that label a flux-analysis tool run cannot be inserted. Recorded here rather than
# tolerated silently; Sprint 741c repairs it and empties this set.
# Empty: Sprint 787's migration now adds FLUX_ANALYSIS and STATISTICAL_SAMPLING as member
# names, so every ToolName member has a label on a chain-built database. The stale
# lowercase 'flux_analysis' label from Sprint 308 remains in the type, unused — dropping it
# means recreating the type, which is Sprint 741c.
KNOWN_LABEL_DRIFT: frozenset[str] = frozenset()


def test_migration_adds_the_labels_sqlalchemy_actually_binds():
    """Enum migrations must add member NAMES, not slugs.

    `Enum(ToolName)` has no `values_callable`, so SQLAlchemy binds `.name` — it sends
    `SOD_CHECKER`, never `sod_checker`. The baseline migration gets this right
    (`sa.Enum('TRIAL_BALANCE', ...)`); Sprint 787's first draft got it wrong by copying the
    slug list from `tools_registry`, and this test passed anyway because it searched for
    the slugs. A Python enum member whose label was never added — or added in the wrong
    case — inserts fine on SQLite and fails on PostgreSQL.
    """
    versions = BACKEND_DIR / "migrations" / "alembic" / "versions"
    migration_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in versions.glob("*.py")
        if "toolname" in path.read_text(encoding="utf-8").lower()
    )

    # The original eleven came with the type itself in the baseline migration; anything
    # added later needs its own ALTER TYPE.
    added_later = {
        "FLUX_ANALYSIS",
        "SOD_CHECKER",
        "INTERCOMPANY_ELIMINATION",
        "W2_RECONCILIATION",
        "FORM_1099",
        "BOOK_TO_TAX",
        "CASH_FLOW_PROJECTOR",
    }
    missing = sorted(name for name in added_later - KNOWN_LABEL_DRIFT if name not in migration_text)
    assert not missing, (
        f"these ToolName members have no ALTER TYPE adding their *name* as a label: {missing}. "
        f"SQLAlchemy binds the member name, so inserting them succeeds on SQLite and fails "
        f"on PostgreSQL with 22P02."
    )


def test_known_label_drift_is_empty():
    """The exemption set must stay empty.

    It briefly held FLUX_ANALYSIS, until it became clear that adding a label is just
    `ADD VALUE IF NOT EXISTS` and needed no exemption at all. If this fails, someone added
    an enum member without a migration and exempted it instead of writing one.
    """
    assert KNOWN_LABEL_DRIFT == frozenset()


def test_every_toolname_member_appears_in_some_migration_or_the_baseline():
    """Nothing may rely on `create_all` to exist in production.

    Production's schema was built by `create_all` and stamped (see Sprint 741b/741c), which
    is exactly why this check matters: a member present only via `create_all` works there
    and is absent from any database rebuilt from the chain.
    """
    versions = BACKEND_DIR / "migrations" / "alembic" / "versions"
    all_migration_text = "\n".join(path.read_text(encoding="utf-8") for path in versions.glob("*.py"))
    missing = sorted(t.name for t in ToolName if t.name not in all_migration_text and t.name not in KNOWN_LABEL_DRIFT)
    assert not missing, f"ToolName members absent from every migration: {missing}"
