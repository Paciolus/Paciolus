"""Sprint 891 (CEO brief 16B, review ST-06): plan facts have one source, shared/plans.json.

The first step moved every price, seat rate, seat ceiling, limit and feature gate into the plan
file without changing a value. ``fixtures/plan_values_before_sprint_891.json`` was dumped from the
code before the move; this test reproduces the same dump from the code after it.
"""

import dataclasses
import json
from pathlib import Path

from billing import price_config as pc
from shared.entitlements import PLANS, TIER_ENTITLEMENTS

BEFORE = json.loads((Path(__file__).parent / "fixtures" / "plan_values_before_sprint_891.json").read_text())


def _ent(e):
    return {k: (sorted(v) if isinstance(v, (set, frozenset)) else v) for k, v in dataclasses.asdict(e).items()}


def _dump() -> dict:
    return {
        "PRICE_TABLE": pc.PRICE_TABLE,
        "PROFESSIONAL_SEAT_PRICE": pc.PROFESSIONAL_SEAT_PRICE,
        "ENTERPRISE_SEAT_PRICE": pc.ENTERPRISE_SEAT_PRICE,
        "MAX_SELF_SERVE_SEATS_PROFESSIONAL": pc.MAX_SELF_SERVE_SEATS_PROFESSIONAL,
        "MAX_SELF_SERVE_SEATS_ENTERPRISE": pc.MAX_SELF_SERVE_SEATS_ENTERPRISE,
        "seat_prices": {
            t: {i: [pc.get_seat_price_cents(n, i, t) for n in range(1, 102)] for i in ("monthly", "annual")}
            for t in ("professional", "enterprise")
        },
        "TIER_ENTITLEMENTS": {k.value: _ent(v) for k, v in TIER_ENTITLEMENTS.items()},
    }


def test_every_price_limit_and_gate_is_unchanged_by_the_move():
    assert json.loads(json.dumps(_dump(), sort_keys=True)) == BEFORE


def test_seat_ceilings_are_held_once():
    assert pc.MAX_SELF_SERVE_SEATS_PROFESSIONAL == PLANS["tiers"]["professional"]["entitlements"]["max_team_seats"]
    assert pc.MAX_SELF_SERVE_SEATS_ENTERPRISE == PLANS["tiers"]["enterprise"]["entitlements"]["max_team_seats"]


def test_plan_file_covers_every_tier():
    assert set(PLANS["tiers"]) == {"free", "solo", "professional", "enterprise"}


def test_generated_frontend_plan_module_is_current():
    import subprocess
    import sys

    repo = Path(__file__).resolve().parents[2]
    out = subprocess.run(
        [sys.executable, str(repo / "scripts" / "generate_plans_ts.py"), "--check"], capture_output=True, text=True
    )
    assert out.returncode == 0, out.stdout + out.stderr
