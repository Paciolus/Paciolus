#!/usr/bin/env python3
"""Check for OpenAPI schema drift between committed snapshot and current app.

Compares the committed openapi-snapshot.json against the live OpenAPI spec
generated from the FastAPI application. Reports structural differences
(added/removed/changed paths, schemas, and fields).

Exit codes:
    0 — no drift detected (snapshot matches live spec)
    1 — drift detected (snapshot is stale; run generate_openapi_snapshot.py)
    2 — snapshot file missing (never generated)

Sprint 518 (DEC F-020): Schema drift detection between backend
OpenAPI spec and frontend TypeScript types.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Environment setup — provide minimal config so we can import the app
# without a real .env file (e.g., in CI).
# ---------------------------------------------------------------------------
os.environ.setdefault("API_HOST", "0.0.0.0")
os.environ.setdefault("API_PORT", "8000")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")
os.environ.setdefault("DATABASE_URL", "sqlite:///./openapi_drift_check.db")
os.environ.setdefault("ENV_MODE", "development")

# Add backend to sys.path so `from main import app` works
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

SNAPSHOT_PATH = Path(__file__).resolve().parent / "openapi-snapshot.json"

# Maximum number of individual field-level diffs to report before truncating
MAX_FIELD_DIFFS = 50


# ---------------------------------------------------------------------------
# Diff helpers
# ---------------------------------------------------------------------------


def _diff_keys(label: str, old: dict, new: dict) -> list[str]:
    """Report added/removed keys at one level of a dict."""
    diffs: list[str] = []
    old_keys = set(old.keys())
    new_keys = set(new.keys())

    for key in sorted(new_keys - old_keys):
        diffs.append(f"  + {label}/{key}  (ADDED)")
    for key in sorted(old_keys - new_keys):
        diffs.append(f"  - {label}/{key}  (REMOVED)")

    return diffs


def _diff_schema_fields(
    schema_name: str, old_schema: dict[str, Any], new_schema: dict[str, Any]
) -> list[str]:
    """Report field-level differences within a single schema."""
    diffs: list[str] = []

    old_props = old_schema.get("properties", {})
    new_props = new_schema.get("properties", {})

    # Added / removed properties
    for prop in sorted(set(new_props) - set(old_props)):
        prop_type = _summarize_type(new_props[prop])
        diffs.append(f"  + Schema '{schema_name}' field '{prop}' ({prop_type})  (ADDED)")
    for prop in sorted(set(old_props) - set(new_props)):
        prop_type = _summarize_type(old_props[prop])
        diffs.append(f"  - Schema '{schema_name}' field '{prop}' ({prop_type})  (REMOVED)")

    # Changed properties (type or structure change)
    for prop in sorted(set(old_props) & set(new_props)):
        old_type = _summarize_type(old_props[prop])
        new_type = _summarize_type(new_props[prop])
        if old_type != new_type:
            diffs.append(
                f"  ~ Schema '{schema_name}' field '{prop}': "
                f"{old_type} -> {new_type}  (TYPE CHANGED)"
            )

    # Required fields change
    old_required = set(old_schema.get("required", []))
    new_required = set(new_schema.get("required", []))
    for field in sorted(new_required - old_required):
        if field in new_props:
            diffs.append(f"  ~ Schema '{schema_name}' field '{field}'  (NOW REQUIRED)")
    for field in sorted(old_required - new_required):
        if field in old_props:
            diffs.append(f"  ~ Schema '{schema_name}' field '{field}'  (NOW OPTIONAL)")

    return diffs


def _summarize_type(prop: dict[str, Any]) -> str:
    """Produce a human-readable type summary for an OpenAPI property."""
    if "$ref" in prop:
        ref = prop["$ref"]
        return ref.rsplit("/", 1)[-1]

    if "anyOf" in prop:
        parts = [_summarize_type(p) for p in prop["anyOf"]]
        return " | ".join(parts)

    if "allOf" in prop:
        parts = [_summarize_type(p) for p in prop["allOf"]]
        return " & ".join(parts)

    t = prop.get("type", "unknown")
    if t == "array":
        items = prop.get("items", {})
        return f"array<{_summarize_type(items)}>"
    if t == "null":
        return "null"
    if "enum" in prop:
        return f"{t}(enum)"

    fmt = prop.get("format")
    if fmt:
        return f"{t}({fmt})"
    return str(t)


def _diff_endpoint_signatures(
    path: str, old_path: dict[str, Any], new_path: dict[str, Any]
) -> list[str]:
    """Report changes to endpoint methods and response models."""
    diffs: list[str] = []

    old_methods = set(old_path.keys())
    new_methods = set(new_path.keys())

    for method in sorted(new_methods - old_methods):
        diffs.append(f"  + {method.upper()} {path}  (ENDPOINT ADDED)")
    for method in sorted(old_methods - new_methods):
        diffs.append(f"  - {method.upper()} {path}  (ENDPOINT REMOVED)")

    # Check shared methods for response model changes
    for method in sorted(old_methods & new_methods):
        old_op = old_path[method]
        new_op = new_path[method]

        # Compare response schemas (200/201 responses)
        for status in ("200", "201"):
            old_resp = (
                old_op.get("responses", {})
                .get(status, {})
                .get("content", {})
                .get("application/json", {})
                .get("schema", {})
            )
            new_resp = (
                new_op.get("responses", {})
                .get(status, {})
                .get("content", {})
                .get("application/json", {})
                .get("schema", {})
            )
            if old_resp != new_resp:
                old_ref = old_resp.get("$ref", str(old_resp)[:60]) if old_resp else "(none)"
                new_ref = new_resp.get("$ref", str(new_resp)[:60]) if new_resp else "(none)"
                diffs.append(
                    f"  ~ {method.upper()} {path} [{status}]: "
                    f"response schema changed ({old_ref} -> {new_ref})"
                )

    return diffs


# ---------------------------------------------------------------------------
# Main comparison
# ---------------------------------------------------------------------------


def compare_specs(
    old_spec: dict[str, Any], new_spec: dict[str, Any]
) -> list[str]:
    """Compare two OpenAPI specs and return a list of human-readable diffs."""
    all_diffs: list[str] = []

    # --- Paths (endpoints) ---
    old_paths = old_spec.get("paths", {})
    new_paths = new_spec.get("paths", {})

    all_diffs.extend(_diff_keys("paths", old_paths, new_paths))

    for path in sorted(set(old_paths) & set(new_paths)):
        all_diffs.extend(
            _diff_endpoint_signatures(path, old_paths[path], new_paths[path])
        )

    # --- Schemas (component definitions) ---
    old_schemas = old_spec.get("components", {}).get("schemas", {})
    new_schemas = new_spec.get("components", {}).get("schemas", {})

    all_diffs.extend(_diff_keys("schemas", old_schemas, new_schemas))

    for schema_name in sorted(set(old_schemas) & set(new_schemas)):
        all_diffs.extend(
            _diff_schema_fields(schema_name, old_schemas[schema_name], new_schemas[schema_name])
        )

    return all_diffs


def main() -> int:
    """Run the drift check."""

    # 1. Load committed snapshot
    if not SNAPSHOT_PATH.exists():
        print("ERROR: OpenAPI snapshot not found.")
        print(f"  Expected: {SNAPSHOT_PATH}")
        print("  Run: python scripts/generate_openapi_snapshot.py")
        return 2

    try:
        old_spec = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"ERROR: Failed to read snapshot: {exc}")
        return 2

    # 2. Generate live spec from app
    print("Extracting live OpenAPI spec from FastAPI app...")
    from main import app

    new_spec = app.openapi()

    # 3. Normalize for comparison (sort keys)
    old_normalized = json.loads(json.dumps(old_spec, sort_keys=True))
    new_normalized = json.loads(json.dumps(new_spec, sort_keys=True))

    # 4. Quick check: exact match
    if old_normalized == new_normalized:
        old_schema_count = len(old_spec.get("components", {}).get("schemas", {}))
        old_path_count = len(old_spec.get("paths", {}))
        print(f"No drift detected. Snapshot is up to date.")
        print(f"  Paths: {old_path_count}")
        print(f"  Schemas: {old_schema_count}")
        return 0

    # 5. Detailed diff
    diffs = compare_specs(old_normalized, new_normalized)

    if not diffs:
        # Structural diff in non-schema/non-path areas (e.g., info, version)
        # Still counts as drift but is less critical
        print("WARNING: OpenAPI spec differs from snapshot in metadata (info/version).")
        print("  Run: python scripts/generate_openapi_snapshot.py")
        return 1

    print(f"\nOpenAPI SCHEMA DRIFT DETECTED — {len(diffs)} difference(s):\n")

    displayed = diffs[:MAX_FIELD_DIFFS]
    for diff in displayed:
        print(diff)

    if len(diffs) > MAX_FIELD_DIFFS:
        print(f"\n  ... and {len(diffs) - MAX_FIELD_DIFFS} more difference(s) (truncated)")

    print(f"\n{'=' * 60}")
    print("The committed OpenAPI snapshot is STALE.")
    print("If these changes are intentional, update the snapshot:")
    print("  python scripts/generate_openapi_snapshot.py")
    print("Then commit the updated scripts/openapi-snapshot.json.")
    print(f"{'=' * 60}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
