#!/usr/bin/env bash
# OpenAPI → TypeScript Type Generation
# Sprint 222: API Contract Tests + Type Generation Infrastructure
#
# Usage:
#   npm run generate:types              # Generate from running server
#   npm run generate:types:file         # Generate from exported schema file
#
# Prerequisites:
#   npm install -D openapi-typescript   (installed by this script if missing)
#
# When to regenerate:
#   - After adding/modifying Pydantic response models in backend/shared/
#   - After changing Literal/Enum types in route models
#   - After adding new response_model= decorators to endpoints
#
# How to review:
#   1. Run this script
#   2. Diff against existing manual types: git diff src/types/api-generated.ts
#   3. Update manual types if needed to match generated types

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$(dirname "$FRONTEND_DIR")/backend"
OUTPUT_FILE="$FRONTEND_DIR/src/types/api-generated.ts"
SCHEMA_FILE="$BACKEND_DIR/openapi.json"

# Ensure openapi-typescript is available
if ! npx --no openapi-typescript --help >/dev/null 2>&1; then
  echo "Installing openapi-typescript..."
  npm install -D openapi-typescript
fi

# Option 1: Generate from running backend server
if curl -s http://localhost:8000/openapi.json >/dev/null 2>&1; then
  echo "Generating types from running server at http://localhost:8000..."
  npx openapi-typescript http://localhost:8000/openapi.json -o "$OUTPUT_FILE"
  echo "Types written to $OUTPUT_FILE"
  exit 0
fi

# Option 2: Export schema from Python, then generate
echo "No running server detected. Exporting OpenAPI schema from Python..."
cd "$BACKEND_DIR"
python -c "
import json
from main import app
schema = app.openapi()
with open('openapi.json', 'w') as f:
    json.dump(schema, f, indent=2)
print('Schema exported to openapi.json')
"

if [ -f "$SCHEMA_FILE" ]; then
  npx openapi-typescript "$SCHEMA_FILE" -o "$OUTPUT_FILE"
  echo "Types written to $OUTPUT_FILE"
  # Clean up exported schema
  rm -f "$SCHEMA_FILE"
else
  echo "ERROR: Failed to export OpenAPI schema"
  exit 1
fi
