"""Sprint 890 (CEO brief 15C): the frontend's required-response-keys file matches the OpenAPI snapshot."""

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def test_generated_required_keys_are_current():
    out = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "generate_response_required_keys.py"), "--check"],
        capture_output=True,
        text=True,
    )
    assert out.returncode == 0, out.stdout + out.stderr
