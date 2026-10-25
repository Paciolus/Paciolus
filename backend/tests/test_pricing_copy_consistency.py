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
    MAX_SELF_SERVE_SEATS_ENTERPRISE,
    MAX_SELF_SERVE_SEATS_PROFESSIONAL,
    PROFESSIONAL_SEAT_PRICE,
    TRIAL_PERIOD_DAYS,
)
from models import UserTier
from shared.entitlements import TIER_ENTITLEMENTS
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


def test_monthly_upload_limits_match_entitlements():
    row = re.search(r"feature: 'Monthly uploads',(.*?)\}", PRICING_TS).group(1)
    expected = {
        "free": TIER_ENTITLEMENTS[UserTier.FREE].uploads_per_month,
        "solo": TIER_ENTITLEMENTS[UserTier.SOLO].uploads_per_month,
        "professional": TIER_ENTITLEMENTS[UserTier.PROFESSIONAL].uploads_per_month,
        "enterprise": TIER_ENTITLEMENTS[UserTier.ENTERPRISE].uploads_per_month,
    }
    for tier, limit in expected.items():
        shown = re.search(rf"{tier}: '([^']+)'", row).group(1)
        assert shown == ("Unlimited" if limit == 0 else str(limit)), tier


def test_seat_configs_match_price_config():
    configs = re.findall(
        r"label: '(\w+)',\s*baseSeats: (\d+),\s*maxSeats: (\d+),\s*seatMonthly: (\d+),\s*seatAnnual: (\d+)", PRICING_TS
    )
    by_label = {c[0]: tuple(int(x) for x in c[1:]) for c in configs}
    assert by_label["Professional"][1:] == (
        MAX_SELF_SERVE_SEATS_PROFESSIONAL,
        PROFESSIONAL_SEAT_PRICE["monthly"] // 100,
        PROFESSIONAL_SEAT_PRICE["annual"] // 100,
    )
    assert by_label["Enterprise"][1:] == (
        MAX_SELF_SERVE_SEATS_ENTERPRISE,
        ENTERPRISE_SEAT_PRICE["monthly"] // 100,
        ENTERPRISE_SEAT_PRICE["annual"] // 100,
    )


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
