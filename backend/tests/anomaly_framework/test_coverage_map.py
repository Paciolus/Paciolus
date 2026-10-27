"""Coverage map completeness validation.

Confirms that every anomaly type in the registry has a corresponding entry
in COVERAGE_MAP.md and a non-None production detector reference.
Fails if a new anomaly is added to the registry without updating the map.
"""

from pathlib import Path

from tests.anomaly_framework.registry import ANOMALY_REGISTRY

COVERAGE_MAP_PATH = Path(__file__).parent / "COVERAGE_MAP.md"


def _parse_coverage_map() -> dict[str, dict[str, str]]:
    """Parse COVERAGE_MAP.md and return {anomaly_type: {column: value}}."""
    text = COVERAGE_MAP_PATH.read_text(encoding="utf-8")

    # Find the markdown table — look for the header row with "Anomaly type"
    lines = text.splitlines()
    header_idx = None
    for i, line in enumerate(lines):
        if "Anomaly type" in line and "|" in line:
            header_idx = i
            break

    if header_idx is None:
        raise ValueError("Could not find coverage map table header in COVERAGE_MAP.md")

    # Parse header columns
    header_cells = [c.strip() for c in lines[header_idx].split("|")]
    # Remove empty strings from leading/trailing pipes
    header_cells = [c for c in header_cells if c]

    # Skip the separator row (header_idx + 1), then parse data rows
    entries: dict[str, dict[str, str]] = {}
    for line in lines[header_idx + 2 :]:
        line = line.strip()
        if not line or not line.startswith("|"):
            break
        cells = [c.strip() for c in line.split("|")]
        cells = [c for c in cells if c != ""]
        if len(cells) < len(header_cells):
            continue

        row = dict(zip(header_cells, cells))
        # Extract anomaly type — strip backticks
        anomaly_type = row.get("Anomaly type", "").strip("`").strip()
        if anomaly_type:
            entries[anomaly_type] = row

    return entries


def test_every_registry_anomaly_has_coverage_map_entry():
    """Confirms that every anomaly type in the registry has a corresponding entry
    in COVERAGE_MAP.md and a non-None production detector reference.
    Fails if a new anomaly is added to the registry without updating the map.
    """
    assert COVERAGE_MAP_PATH.exists(), (
        f"COVERAGE_MAP.md not found at {COVERAGE_MAP_PATH}. Create it before adding new anomaly types to the registry."
    )

    coverage_map = _parse_coverage_map()
    registry_names = {g.name for g in ANOMALY_REGISTRY}

    # Every registry anomaly must have a coverage map row
    missing_from_map = registry_names - set(coverage_map.keys())
    assert not missing_from_map, (
        f"Anomaly types in registry but missing from COVERAGE_MAP.md: {missing_from_map}. "
        "Add a row for each new anomaly type."
    )

    # Every coverage map row must have a non-empty Production detector
    # (blank or omitted is not allowed — gaps must be explicitly labeled as GAP)
    for anomaly_type in registry_names:
        row = coverage_map[anomaly_type]
        detector = row.get("Production detector", "").strip()
        assert detector, (
            f"Anomaly type '{anomaly_type}' has a blank 'Production detector' column "
            "in COVERAGE_MAP.md. If detection is fragmented or absent, explicitly "
            "label the coverage status as GAP and describe the detection path."
        )


def test_coverage_map_has_no_orphan_entries():
    """Verify that coverage map doesn't reference anomaly types not in the registry."""
    coverage_map = _parse_coverage_map()
    registry_names = {g.name for g in ANOMALY_REGISTRY}

    orphans = set(coverage_map.keys()) - registry_names
    assert not orphans, (
        f"COVERAGE_MAP.md contains entries not in the registry: {orphans}. "
        "Remove stale entries or add the corresponding generator to the registry."
    )


# --- Per-tool generator coverage (Sprint 823 item 3) -------------------------


def _parse_tool_table() -> dict[str, dict[str, str]]:
    """Parse the per-tool table (first header cell ``Tool``) into {slug: row}."""
    lines = COVERAGE_MAP_PATH.read_text(encoding="utf-8").splitlines()
    header_idx = next(
        (i for i, line in enumerate(lines) if line.startswith("|") and line.split("|")[1].strip() == "Tool"),
        None,
    )
    assert header_idx is not None, "COVERAGE_MAP.md has no per-tool table (header row starting '| Tool |')"
    header = [c.strip() for c in lines[header_idx].strip().strip("|").split("|")]
    rows: dict[str, dict[str, str]] = {}
    for line in lines[header_idx + 2 :]:
        if not line.startswith("|"):
            break
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        row = dict(zip(header, cells))
        rows[row["Tool"].strip("`")] = row
    return rows


def test_every_marketing_tool_has_a_generator_registry_and_a_map_row():
    """All eighteen tools — not only the trial balance — are registered and mapped.

    Sprint 823 found six of the eighteen had never been exercised by the
    framework, invisibly: nothing tied the framework to the catalog.
    """
    from tests.anomaly_framework.registry import TOOL_GENERATOR_REGISTRY
    from tools_registry import marketing_audit_tools

    catalog = {t.slug for t in marketing_audit_tools()}
    rows = _parse_tool_table()

    assert set(TOOL_GENERATOR_REGISTRY) == catalog, (
        f"registry vs catalog — missing: {catalog - set(TOOL_GENERATOR_REGISTRY)}, "
        f"unknown: {set(TOOL_GENERATOR_REGISTRY) - catalog}"
    )
    assert set(rows) == catalog, f"map vs catalog — missing: {catalog - set(rows)}, unknown: {set(rows) - catalog}"
    empty = [slug for slug, generators in TOOL_GENERATOR_REGISTRY.items() if not generators]
    assert not empty, f"tools registered with no generators: {empty}"


def test_tool_table_generator_counts_match_the_registry():
    from tests.anomaly_framework.registry import TOOL_GENERATOR_REGISTRY

    rows = _parse_tool_table()
    wrong = {
        slug: (rows[slug]["Generators"], len(generators))
        for slug, generators in TOOL_GENERATOR_REGISTRY.items()
        if slug in rows and rows[slug]["Generators"] != str(len(generators))
    }
    assert not wrong, f"COVERAGE_MAP.md generator counts (map, registry) disagree: {wrong}"
    for slug, row in rows.items():
        assert row.get("Coverage status"), f"{slug}: blank coverage status"
        assert row.get("Engine entry point"), f"{slug}: blank engine entry point"


def test_generator_names_are_unique_across_all_tools():
    from tests.anomaly_framework.registry import TOOL_GENERATOR_REGISTRY

    names = [g.name for generators in TOOL_GENERATOR_REGISTRY.values() for g in generators]
    duplicates = sorted({n for n in names if names.count(n) > 1})
    assert not duplicates, f"generator names reused across tools: {duplicates}"
