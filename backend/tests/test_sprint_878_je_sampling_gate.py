"""Sprint 878 (review AZ-06): JE sampling is part of the journal-entry tool.

``POST /audit/journal-entries/sample`` and ``/sample/preview`` depended only on
``require_verified_user``. The main JE endpoint is gated with
``tool_name="journal_entry_testing"`` and meters the upload allowance; the
sampling routes did neither, so a Free account could run them and a paid
account at its cap could keep sampling.

Decision (CEO): a sampling preview uses no upload; a sampling run does.
Both routes enforce the tool gate. The run is checked against the allowance
and consumes one unit when it succeeds.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from models import UserTier
from tests.test_firm_owned_records import _auth, api  # noqa: F401 — `api` is a fixture
from tests.test_sprint_790_upload_metering import _counter, _subscribe

pytestmark = pytest.mark.usefixtures("bypass_csrf")

GL = (
    b"Entry ID,Date,Account,Debit,Credit,Description\n"
    b"JE-001,2025-03-01,Cash,1000.00,0,Receipt\n"
    b"JE-001,2025-03-01,Revenue,0,1000.00,Receipt\n"
    b"JE-002,2025-03-02,Supplies,500.00,0,Purchase\n"
    b"JE-002,2025-03-02,AP,0,500.00,Purchase\n"
)
RUN = "/audit/journal-entries/sample"
PREVIEW = "/audit/journal-entries/sample/preview"


async def _post(api, path, hdr):  # noqa: ANN001, ANN202
    return await api.post(
        path,
        files={"file": ("gl.csv", GL, "text/csv")},
        data={"sample_rate": "0.5"} if path == RUN else {},
        headers=hdr,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("path", [RUN, PREVIEW])
async def test_free_is_refused_on_both_routes(api, make_user, path):  # noqa: ANN001
    user = make_user(email=f"free-je-{path.rsplit('/', 1)[-1]}@example.com", tier=UserTier.FREE)
    with patch("routes.je_testing.parse_uploaded_file", side_effect=AssertionError("parsed for Free")) as parse:
        r = await _post(api, path, _auth(user))
    assert r.status_code == 403, r.text
    assert r.json()["detail"]["resource"] == "tool_access"
    assert not parse.called


@pytest.mark.asyncio
@pytest.mark.parametrize("path", [RUN, PREVIEW])
async def test_lapsed_solo_is_refused_on_both_routes(api, make_user, db_session, path):  # noqa: ANN001
    from subscription_model import SubscriptionStatus

    user = make_user(email=f"lapsed-je-{path.rsplit('/', 1)[-1]}@example.com", tier=UserTier.SOLO)
    _subscribe(db_session, user, tier="solo", status=SubscriptionStatus.CANCELED)
    r = await _post(api, path, _auth(user))
    assert r.status_code == 403, r.text


@pytest.mark.asyncio
async def test_solo_at_its_allowance_cannot_run_sampling(api, make_user, db_session):  # noqa: ANN001
    user = make_user(email="capped-je@example.com", tier=UserTier.SOLO)
    _subscribe(db_session, user, used=100, tier="solo")
    with patch("routes.je_testing.parse_uploaded_file", side_effect=AssertionError("parsed past the cap")) as parse:
        r = await _post(api, RUN, _auth(user))
    assert r.status_code == 403, r.text
    assert r.json()["detail"]["resource"] == "uploads"
    assert not parse.called
    assert _counter(db_session, user.id) == 100


@pytest.mark.asyncio
async def test_a_successful_run_consumes_exactly_one(api, make_user, db_session):  # noqa: ANN001
    user = make_user(email="run-je@example.com", tier=UserTier.SOLO)
    _subscribe(db_session, user, used=7, tier="solo")
    r = await _post(api, RUN, _auth(user))
    assert r.status_code == 200, r.text
    assert _counter(db_session, user.id) == 8


@pytest.mark.asyncio
async def test_a_failed_run_consumes_nothing(api, make_user, db_session):  # noqa: ANN001
    user = make_user(email="fail-je@example.com", tier=UserTier.SOLO)
    _subscribe(db_session, user, used=7, tier="solo")
    with patch("routes.je_testing.run_stratified_sampling", side_effect=ValueError("bad input")):
        r = await _post(api, RUN, _auth(user))
    assert r.status_code == 400, r.text
    assert _counter(db_session, user.id) == 7


@pytest.mark.asyncio
async def test_preview_uses_no_allowance_even_at_the_cap(api, make_user, db_session):  # noqa: ANN001
    user = make_user(email="preview-je@example.com", tier=UserTier.SOLO)
    _subscribe(db_session, user, used=100, tier="solo")
    r = await _post(api, PREVIEW, _auth(user))
    assert r.status_code == 200, r.text
    assert r.json()["total_population"] > 0
    assert _counter(db_session, user.id) == 100
