#!/usr/bin/env python3
"""Generate OpenAPI snapshot from the FastAPI application.

Writes the current OpenAPI spec to scripts/openapi-snapshot.json.
Run this whenever you intentionally change backend schemas:

    python scripts/generate_openapi_snapshot.py

The snapshot is committed to the repo and checked by CI via
check_openapi_drift.py.

Sprint 518 (DEC F-020): Schema drift detection between backend
OpenAPI spec and frontend TypeScript types.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Environment setup — provide minimal config so we can import the app
# without a real .env file (e.g., in CI).
# ---------------------------------------------------------------------------
os.environ.setdefault("API_HOST", "0.0.0.0")
os.environ.setdefault("API_PORT", "8000")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")
os.environ.setdefault("DATABASE_URL", "sqlite:///./openapi_snapshot.db")
os.environ.setdefault("ENV_MODE", "development")

# Add backend to sys.path so `from main import app` works
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

SNAPSHOT_PATH = Path(__file__).resolve().parent / "openapi-snapshot.json"


def generate_snapshot() -> None:
    """Extract OpenAPI spec from the FastAPI app and write it to disk."""
    from main import app

    spec = app.openapi()

    # Sort keys for deterministic output (avoids false diffs from dict ordering)
    snapshot = json.dumps(spec, indent=2, sort_keys=True, ensure_ascii=False)

    SNAPSHOT_PATH.write_text(snapshot + "\n", encoding="utf-8")
    schema_count = len(spec.get("components", {}).get("schemas", {}))
    path_count = len(spec.get("paths", {}))
    print(f"OpenAPI snapshot written to {SNAPSHOT_PATH}")
    print(f"  Paths: {path_count}")
    print(f"  Schemas: {schema_count}")
    print(f"  Size: {len(snapshot):,} bytes")


if __name__ == "__main__":
    generate_snapshot()
