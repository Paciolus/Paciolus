"""Sprint 878 (review AZ-03): every download needs the export gate.

The CSV exports of the account risk heatmap, depreciation, lease accounting
and bank reconciliation depended only on ``require_verified_user`` and never
called ``check_export_access``, so a verified Free account downloaded them.
Free is view-only: no PDF, Excel or CSV.

Each route is called with a real access token. A Free caller is refused with
403 before the generator runs (the generator is replaced by one that fails the
test if called); an active Solo caller gets the file.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from models import UserTier
from tests.test_firm_owned_records import _auth, _subscribe, api  # noqa: F401 — `api` is a fixture

pytestmark = pytest.mark.usefixtures("bypass_csrf")

_BANK_REC_SUMMARY = {
    "matched_count": 0,
    "matched_amount": 0.0,
    "bank_only_count": 0,
    "bank_only_amount": 0.0,
    "ledger_only_count": 0,
    "ledger_only_amount": 0.0,
    "reconciling_difference": 0.0,
    "total_bank": 0.0,
    "total_ledger": 0.0,
}

# (path, JSON body, the generator the route runs)
EXPORTS = {
    "account_risk_heatmap": (
        "/audit/account-risk-heatmap/export.csv",
        {"signals": []},
        "routes.account_risk_heatmap.compute_account_heatmap",
    ),
    "depreciation": (
        "/audit/depreciation/export.csv",
        {"asset_name": "Press", "cost": "10000", "useful_life_years": 5, "placed_in_service_year": 2025},
        "routes.depreciation.generate_depreciation_schedule",
    ),
    "lease_accounting": (
        "/audit/lease-accounting/export.csv",
        {"lease_name": "Office", "payment_amount": "1000", "term_periods": 12, "annual_discount_rate": "0.05"},
        "routes.lease_accounting.compute_lease_accounting",
    ),
    "bank_reconciliation": (
        "/export/csv/bank-rec",
        {"summary": _BANK_REC_SUMMARY, "matches": []},
        "routes.bank_reconciliation.export_reconciliation_csv",
    ),
}


@pytest.mark.asyncio
@pytest.mark.parametrize("name", sorted(EXPORTS))
async def test_free_is_refused_before_the_generator_runs(api, make_user, name):  # noqa: ANN001
    path, body, generator = EXPORTS[name]
    user = make_user(email=f"free-{name}@example.com", tier=UserTier.FREE)
    with patch(generator, side_effect=AssertionError(f"{generator} ran for a Free user")) as gen:
        r = await api.post(path, json=body, headers=_auth(user))
    assert r.status_code == 403, f"{name}: {r.status_code} {r.text}"
    assert r.json()["detail"]["resource"] == "export"
    assert not gen.called


@pytest.mark.asyncio
@pytest.mark.parametrize("name", sorted(EXPORTS))
async def test_lapsed_solo_is_refused(api, make_user, db_session, name):  # noqa: ANN001
    from subscription_model import SubscriptionStatus

    path, body, generator = EXPORTS[name]
    user = make_user(email=f"lapsed-{name}@example.com", tier=UserTier.SOLO)
    _subscribe(db_session, user, tier="solo").status = SubscriptionStatus.PAST_DUE
    db_session.flush()
    with patch(generator, side_effect=AssertionError(f"{generator} ran for a lapsed user")) as gen:
        r = await api.post(path, json=body, headers=_auth(user))
    assert r.status_code == 403, f"{name}: {r.status_code} {r.text}"
    assert not gen.called


@pytest.mark.asyncio
@pytest.mark.parametrize("name", sorted(EXPORTS))
async def test_active_solo_receives_the_file(api, make_user, db_session, name):  # noqa: ANN001
    path, body, _ = EXPORTS[name]
    user = make_user(email=f"solo-{name}@example.com", tier=UserTier.SOLO)
    _subscribe(db_session, user, tier="solo")
    r = await api.post(path, json=body, headers=_auth(user))
    assert r.status_code == 200, f"{name}: {r.status_code} {r.text}"
    assert r.headers["content-type"].startswith("text/csv")
    assert "attachment" in r.headers.get("content-disposition", "")
    assert r.content
