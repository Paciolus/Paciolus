"""Sprint 878 (review AZ-04): a preview token must not carry a PDF past the Free format limit.

``POST /audit/preview-pdf`` cached the uploaded PDF with no format check.
``POST /audit/trial-balance`` then checked ``enforce_format_access`` against
the *new* upload's filename but analysed ``cached_entry.file_bytes`` and
``cached_entry.filename`` - so a Free account could preview a PDF and submit
the token next to a file named ``placeholder.csv``.

Now the preview checks the format, and the analysis checks the format of the
input it will actually process (the cached file, or the uploaded file with its
format detected from the bytes when the name carries no extension) against the
caller's plan *at analysis time*.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from unittest.mock import patch

import pytest

from models import UserTier
from shared.preflight_cache import preflight_cache
from tests.test_firm_owned_records import _auth, _subscribe, api  # noqa: F401 — `api` is a fixture

pytestmark = pytest.mark.usefixtures("bypass_csrf")

PDF_BYTES = b"%PDF-1.4\n% fake trial balance\n"
CSV_BYTES = b"Account,Debit,Credit\nCash,100,0\nRevenue,0,100\n"
ENGINE = "routes.audit_pipeline.audit_trial_balance_streaming"


@dataclass
class _Meta:
    page_count: int = 1
    tables_found: int = 1
    extraction_confidence: float = 0.9
    header_confidence: float = 0.9
    numeric_density: float = 0.7
    row_consistency: float = 0.95
    remediation_hints: list = field(default_factory=list)


@dataclass
class _Extract:
    column_names: list = field(default_factory=lambda: ["Account", "Debit", "Credit"])
    rows: list = field(default_factory=lambda: [["Cash", "100", "0"]])
    metadata: _Meta = field(default_factory=_Meta)


def _engine_stop(*_args, **kwargs):  # noqa: ANN002, ANN003, ANN202
    """Stands in for the engine: proves the gate was passed, then ends the request with a 400."""
    raise ValueError(f"engine reached with {kwargs.get('filename')!r}")


async def _preview(api, hdr):  # noqa: ANN001, ANN202
    with patch("shared.pdf_parser.extract_pdf_tables", return_value=_Extract()):
        return await api.post(
            "/audit/preview-pdf", files={"file": ("tb.pdf", PDF_BYTES, "application/pdf")}, headers=hdr
        )


async def _analyse(api, hdr, *, token=None, name="placeholder.csv", body=CSV_BYTES):  # noqa: ANN001, ANN202
    data = {"force_resubmit": "true"}
    if token:
        data["preflight_token"] = token
    return await api.post("/audit/trial-balance", files={"file": (name, body, "text/csv")}, data=data, headers=hdr)


@pytest.mark.asyncio
async def test_free_preview_of_a_pdf_is_refused_and_caches_nothing(api, make_user):  # noqa: ANN001
    user = make_user(email="free-preview@example.com", tier=UserTier.FREE)
    with patch("shared.pdf_parser.extract_pdf_tables") as extract:
        r = await api.post(
            "/audit/preview-pdf", files={"file": ("tb.pdf", PDF_BYTES, "application/pdf")}, headers=_auth(user)
        )
    assert r.status_code == 403, r.text
    assert r.json()["detail"]["resource"] == "format_access"
    assert not extract.called


@pytest.mark.asyncio
async def test_free_sequence_preview_then_analysis_never_analyses_the_pdf(api, make_user):  # noqa: ANN001
    """The whole attack: preview the PDF, then submit its token beside placeholder.csv."""
    user = make_user(email="free-seq@example.com", tier=UserTier.FREE)
    hdr = _auth(user)
    r = await _preview(api, hdr)
    assert r.status_code == 403, r.text

    # Even holding a cached PDF for this user (as an earlier preview would have
    # left), the analysis refuses it: the check follows the cached file, not
    # the placeholder upload.
    token = preflight_cache.put(PDF_BYTES, "tb.pdf", owner_id=user.id)
    with patch(ENGINE, side_effect=AssertionError("engine ran on a Free user's PDF")) as engine:
        r = await _analyse(api, hdr, token=token)
    assert r.status_code == 403, r.text
    assert r.json()["detail"]["resource"] == "format_access"
    assert not engine.called


@pytest.mark.asyncio
async def test_paid_preview_then_downgrade_is_refused_at_analysis(api, make_user, db_session):  # noqa: ANN001
    from subscription_model import SubscriptionStatus

    user = make_user(email="downgrade-seq@example.com", tier=UserTier.SOLO)
    sub = _subscribe(db_session, user, tier="solo")
    hdr = _auth(user)
    r = await _preview(api, hdr)
    assert r.status_code == 200, r.text
    token = r.json()["preflight_token"]
    assert token

    sub.status = SubscriptionStatus.CANCELED
    db_session.flush()

    with patch(ENGINE, side_effect=AssertionError("engine ran after the downgrade")) as engine:
        r = await _analyse(api, hdr, token=token)
    assert r.status_code == 403, r.text
    assert r.json()["detail"]["resource"] == "format_access"
    assert not engine.called


@pytest.mark.asyncio
async def test_paid_preview_then_analysis_reaches_the_engine_with_the_cached_pdf(api, make_user, db_session):  # noqa: ANN001
    user = make_user(email="paid-seq@example.com", tier=UserTier.SOLO)
    _subscribe(db_session, user, tier="solo")
    hdr = _auth(user)
    r = await _preview(api, hdr)
    assert r.status_code == 200, r.text
    with patch(ENGINE, side_effect=_engine_stop) as engine:
        r = await _analyse(api, hdr, token=r.json()["preflight_token"])
    assert r.status_code == 400, r.text
    assert engine.call_args.kwargs["filename"] == "tb.pdf"


@pytest.mark.asyncio
async def test_free_upload_of_pdf_bytes_without_an_extension_is_refused(api, make_user):  # noqa: ANN001
    """No extension to read: the format is detected from the bytes, as the parser would."""
    user = make_user(email="free-noext@example.com", tier=UserTier.FREE)
    with patch(ENGINE, side_effect=AssertionError("engine ran on extensionless PDF bytes")) as engine:
        r = await _analyse(api, _auth(user), name="trial_balance", body=PDF_BYTES)
    assert r.status_code == 403, r.text
    assert not engine.called


@pytest.mark.asyncio
async def test_free_csv_upload_still_reaches_the_engine(api, make_user):  # noqa: ANN001
    user = make_user(email="free-csv@example.com", tier=UserTier.FREE)
    with patch(ENGINE, side_effect=_engine_stop) as engine:
        r = await _analyse(api, _auth(user))
    assert r.status_code == 400, r.text
    assert engine.call_args.kwargs["filename"] == "placeholder.csv"
