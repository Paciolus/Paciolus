#!/usr/bin/env bash
# Run the full Synthetic Anomaly Testing Framework suite.
# Usage: bash scripts/run_anomaly_tests.sh [--property]
#
#   No flags    → detection tests only (fast, ~3s)
#   --property  → detection + property-based tests (~18s)

set -e
cd "$(dirname "$0")/../backend"

echo "=== Synthetic Anomaly Testing Framework ==="
echo ""

if [[ "$1" == "--property" ]]; then
    echo "Running detection + property tests..."
    echo ""
    python -m pytest tests/test_anomaly_detection.py tests/test_anomaly_properties.py -v --tb=short
else
    echo "Running detection tests..."
    echo "(use --property to include Hypothesis fuzz tests)"
    echo ""
    python -m pytest tests/test_anomaly_detection.py -v --tb=short
fi
