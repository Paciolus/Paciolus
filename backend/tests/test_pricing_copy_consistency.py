"""Sprint 842: the numbers in pricing and marketing copy come from the code.

The claims review found copy that had drifted from what the product does:
"no credit card required" (checkout collects one), "140+ automated tests"
(the registry sums to 97), a 50 MB file limit (it is 100 MB), "$80/$70 per
seat, 8-22" (it is $65 up to 20 / $45 up to 100), Professional "unlimited
uploads" (it is 500), "next business day" / "8 hr" / "custom SLA" support
promises nobody staffs. These tests tie each figure to its source.
"""

import re
from pathlib import Path

import tools_registry
from billing.price_config import (
    ENTERPRISE_SEAT_PRICE,
    PROFESSIONAL_SEAT_PRICE,
    SELF_SERVE_TEAM_TIERS_ENABLED,
    TRIAL_PERIOD_DAYS,
)
from shared.upload_pipeline import MAX_FILE_SIZE_MB, MAX_ROW_COUNT

REPO = Path(__file__).resolve().parents[2]
PRICING_TS = (REPO / "frontend/src/domain/pricing.ts").read_text(encoding="utf-8")
LEDGER_TS = (REPO / "frontend/src/content/tool-ledger.ts").read_text(encoding="utf-8")
USER_GUIDE = (REPO / "docs/07-user-facing/USER_GUIDE.md").read_text(encoding="utf-8")


def _ts_number(source: str, name: str) -> int:
    match = re.search(rf"export const {name} = (\d+)", source)
    assert match, f"{name} not found"
    return int(match.group(1))


def test_trial_length_matches_backend():
    assert _ts_number(PRICING_TS, "TRIAL_DAYS") == TRIAL_PERIOD_DAYS


def test_self_serve_team_tier_flag_matches_backend():
    """Sprint 858: the pricing page's "Contact us" switch mirrors the checkout gate."""
    match = re.search(r"export const SELF_SERVE_TEAM_TIERS_ENABLED = (true|false)", PRICING_TS)
    assert match, "SELF_SERVE_TEAM_TIERS_ENABLED not found"
    assert (match.group(1) == "true") is SELF_SERVE_TEAM_TIERS_ENABLED


def test_ledger_test_counts_match_the_registry():
    ledger_total = sum(int(n) for n in re.findall(r"testCount: (\d+)", LEDGER_TS))
    registry_total = sum(t.test_count or 0 for t in tools_registry.all_tools())
    assert ledger_total == registry_total


def test_marketing_test_count_is_derived_not_typed():
    for rel in (
        "frontend/src/components/marketing/EvidenceBand.tsx",
        "frontend/src/components/marketing/BottomProof.tsx",
    ):
        source = (REPO / rel).read_text(encoding="utf-8")
        assert "TOTAL_AUTOMATED_TESTS" in source, rel
        assert "140" not in source, rel


def test_monthly_upload_limits_are_derived_from_the_plan_file():
    """Sprint 891 (16B): the row reads the plan file both sides load, so it cannot drift.

    (Before, this test parsed the literal numbers; frontend/src/__tests__/Sprint891PlanFile.test.ts
    now pins the values the page shows.)
    """
    row = re.search(r"feature: 'Monthly uploads',(.*?)\}", PRICING_TS).group(1)
    for tier in ("free", "solo", "professional", "enterprise"):
        assert f"uploadsPerMonth('{tier}')" in row, tier
    assert re.search(r"'\d+'", row) is None, "a literal limit is back in the Monthly uploads row"


def test_seat_configs_are_derived_from_the_plan_file():
    block = PRICING_TS[PRICING_TS.index("export const SEAT_CONFIGS") :]
    block = block[: block.index("}))") + 3]
    assert "PLANS.seat_price_cents" in block and "max_team_seats" in block
    assert not re.search(r"(seatMonthly|maxSeats|baseSeats):\s*\d", block), "a literal seat figure is back"


def test_file_limits_in_copy_match_the_upload_pipeline():
    limit_text = f"{MAX_FILE_SIZE_MB} MB and {MAX_ROW_COUNT:,} rows"
    assert limit_text in PRICING_TS
    assert limit_text in USER_GUIDE
    assert "50 MB" not in USER_GUIDE


def test_user_guide_seat_prices_match_price_config():
    assert f"${PROFESSIONAL_SEAT_PRICE['monthly'] // 100}/month" in USER_GUIDE
    assert f"${ENTERPRISE_SEAT_PRICE['monthly'] // 100}/month" in USER_GUIDE


RETIRED_BILLING_CLAIMS = (
    "no credit card required",
    "most popular",
    "dedicated account manager",
    "custom sla",
    "8 hr response",
    "next business day",
    "no hard row limit",
    "start of each calendar month",
    "can also be invoiced",
)


def test_retired_billing_claims_stay_retired():
    hits = []
    for rel in (
        "frontend/src/domain/pricing.ts",
        "frontend/src/app/(marketing)/pricing/page.tsx",
        "frontend/src/components/marketing/hero/HeroProductFilm.tsx",
        "docs/07-user-facing/USER_GUIDE.md",
    ):
        text = (REPO / rel).read_text(encoding="utf-8").lower()
        hits += [f"{rel}: {p!r}" for p in RETIRED_BILLING_CLAIMS if p in text]
    assert not hits, hits


def test_standard_setter_count_matches_the_registry():
    """BottomProof shows the number of standard-setters cited (Sprint 843)."""
    import standards_registry

    setter = {
        "ISA": "IAASB",
        "PCAOB": "PCAOB",
        "AICPA": "AICPA",
        "ASC": "FASB",
        "IFRS": "IASB",
        "IAS": "IASB",
        "IRS": "IRS",
    }
    bodies = {setter[s.body] for s in standards_registry.STANDARDS if s.body in setter}
    source = (REPO / "frontend/src/components/marketing/BottomProof.tsx").read_text(encoding="utf-8")
    assert f"target: {len(bodies)}," in source
    for name in bodies:
        assert name in source
