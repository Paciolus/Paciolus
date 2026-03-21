#!/usr/bin/env python3
"""Generate Claude-powered synthetic anomaly fixture scenarios.

Saves to backend/tests/anomaly_framework/fixtures/generated/<generator_name>_<n>.csv
Run manually to refresh the fixture library. Commit the results.

Requires ANTHROPIC_API_KEY in environment. Not run in CI.

Usage:
    python scripts/generate_anomaly_fixtures.py
    python scripts/generate_anomaly_fixtures.py --generator round_number --count 3
"""

import json
import csv
import argparse
import sys
from pathlib import Path

# Add backend to path so we can import the registry
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))


SYSTEM_PROMPT = """You generate synthetic financial trial balance data for audit testing.
Respond ONLY with a valid JSON object — no markdown, no backticks, no preamble.

Schema:
{
  "rows": [
    {
      "Account": "1000",
      "Account Name": "Cash - Operating",
      "Account Type": "Asset",
      "Debit": 150000.00,
      "Credit": 0.00
    }
  ],
  "injected_anomalies": [
    {
      "type": "round_number",
      "description": "Account 1000 has a suspiciously round balance of $150,000"
    }
  ]
}

Rules:
- Include 15-25 rows
- Trial balance must be balanced (sum Debit == sum Credit)
- Account Types must be one of: Asset, Liability, Equity, Revenue, Expense
- Use Meridian Capital Group LLC naming conventions
- Inject exactly the anomaly type specified by the user
"""


def generate_scenario(generator_name: str, scenario_index: int) -> dict:
    """Generate a single anomaly scenario using the Claude API.

    Args:
        generator_name: The anomaly type to inject.
        scenario_index: Scenario number for variation.

    Returns:
        Parsed JSON dict with 'rows' and 'injected_anomalies' keys.
    """
    import anthropic

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Generate scenario #{scenario_index} for anomaly type: {generator_name}. "
                    f"Vary the account mix, company size, and anomaly placement from prior scenarios."
                ),
            }
        ],
    )
    return json.loads(response.content[0].text)


def save_as_csv(data: dict, path: Path) -> None:
    """Save generated scenario as CSV + anomaly metadata JSON.

    Args:
        data: Dict with 'rows' and 'injected_anomalies' keys.
        path: Output path for the CSV file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["Account", "Account Name", "Account Type", "Debit", "Credit"],
        )
        writer.writeheader()
        writer.writerows(data["rows"])
    path.with_suffix(".anomalies.json").write_text(
        json.dumps(data["injected_anomalies"], indent=2)
    )


def main() -> None:
    """Entry point for fixture generation."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic anomaly fixtures using Claude API"
    )
    parser.add_argument(
        "--generator",
        default="all",
        help="Generator name or 'all' (default: all)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=3,
        help="Number of scenarios per generator (default: 3)",
    )
    args = parser.parse_args()

    from tests.anomaly_framework.registry import ANOMALY_REGISTRY

    generators = (
        ANOMALY_REGISTRY
        if args.generator == "all"
        else [g for g in ANOMALY_REGISTRY if g.name == args.generator]
    )

    if not generators:
        print(f"Error: No generator found matching '{args.generator}'")
        sys.exit(1)

    output_base = Path("backend/tests/anomaly_framework/fixtures/generated")
    for gen in generators:
        print(f"Generating {args.count} scenarios for: {gen.name}")
        for i in range(1, args.count + 1):
            data = generate_scenario(gen.name, i)
            save_as_csv(data, output_base / f"{gen.name}_{i:02d}.csv")
            print(f"  OK {gen.name}_{i:02d}.csv")


if __name__ == "__main__":
    main()
