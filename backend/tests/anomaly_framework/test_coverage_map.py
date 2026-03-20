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
