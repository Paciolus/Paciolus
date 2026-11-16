"""Sprint 879a (review DH-03): uploaded values never reach the logs.

The data statement says uploaded files are processed in memory and not kept.
A log line is kept (stdout → Render, Loki, Sentry), so nothing copied from an
upload may appear in one: no account numbers or suffixes, currencies, account
types, cell values, filenames or exception messages quoting them.

Every upload below carries unique marker strings. The app logs through the
real ``setup_logging()`` (production JSON and development formats), with the
Loki handler attached and its network push captured, and with Sentry
initialised with the production options, scrubber and a capturing transport.
Sentry's logging integration is turned up so *every* record becomes an event —
stricter than production, which only sends ERROR. The whole run is repeated
at INFO and at DEBUG. No marker may appear anywhere.
"""

from __future__ import annotations

import io
import json
import logging
import sys
from unittest.mock import patch

import pytest

from models import UserTier
from tests.test_firm_owned_records import _auth, api  # noqa: F401 — `api` is a fixture

pytestmark = pytest.mark.usefixtures("bypass_csrf")

M_ACCT = "QZ7W"  # the last four characters of the account number
M_CURRENCY = "MKRCURZZ1"
M_TYPE = "MKRTYPEZZ2"
M_FILE = "MKRFILEZZ3"
M_CELL = "MKRCELLZZ4"
M_PARSE = "MKRPARSEZZ5"
M_FORM = "MKRFORMZZ6"
M_XML = "MKRXMLZZ7"
M_NAME = "MKRNAMEZZ8"
MARKERS = (M_ACCT, M_CURRENCY, M_TYPE, M_FILE, M_CELL, M_PARSE, M_FORM, M_XML, M_NAME)


def _ofx(*, xml_v2: bool) -> bytes:
    if xml_v2:
        head = '<?xml version="1.0"?>\n<?OFX OFXHEADER="200" VERSION="220" SECURITY="NONE"?>\n'
        close = lambda tag, v: f"<{tag}>{v}</{tag}>"  # noqa: E731
    else:
        head = "OFXHEADER:100\nDATA:OFXSGML\nVERSION:102\nSECURITY:NONE\nENCODING:USASCII\n\n"
        close = lambda tag, v: f"<{tag}>{v}"  # noqa: E731
    txn = lambda d, amt, fid, name: (  # noqa: E731
        "<STMTTRN>"
        + close("TRNTYPE", "DEBIT")
        + close("DTPOSTED", d)
        + close("TRNAMT", amt)
        + close("FITID", fid)
        + close("NAME", name)
        + "</STMTTRN>"
    )
    body = (
        "<OFX><BANKMSGSRSV1><STMTTRNRS><STMTRS>"
        + close("CURDEF", M_CURRENCY)
        + "<BANKACCTFROM>"
        + close("BANKID", "021000021")
        + close("ACCTID", "99881" + M_ACCT)
        + close("ACCTTYPE", M_TYPE)
        + "</BANKACCTFROM><BANKTRANLIST>"
        + close("DTSTART", "20250101")
        + close("DTEND", "20250131")
        + txn("20250105", "-45.99", "F1", "Vendor A")
        + txn("20250120", "3500.00", "F2", "Deposit B")
        + "</BANKTRANLIST></STMTRS></STMTTRNRS></BANKMSGSRSV1></OFX>\n"
    )
    return (head + body).encode()


LEDGER = b"Date,Amount,Description\n2025-01-05,-45.99,Vendor A\n2025-01-20,3500.00,Deposit B\n"
TB = b"Account,Debit,Credit\nCash,1000,0\nRevenue,0,1000\n"
BAD_TB = f"Account,Debit,Credit\nCash,{M_CELL},0\nRevenue,0,1000\n".encode()
BAD_OFX = f"OFXHEADER:100\n\n<OFX><BANKMSGSRSV1><<{M_XML}</OFX>".encode()


class _SentryCapture:
    def __init__(self) -> None:
        self.payloads: list[str] = []

    def __call__(self, envelope_or_event) -> None:  # noqa: ANN001
        self.payloads.append(repr(envelope_or_event))


@pytest.fixture
def captured_logs(monkeypatch, request):  # noqa: ANN001, ANN201
    """Real setup_logging() into a buffer + Loki capture + Sentry capture."""
    import sentry_sdk
    from sentry_sdk.integrations.logging import LoggingIntegration
    from sentry_sdk.transport import Transport

    import logging_config
    from loki_handler import LokiHandler
    from shared.sentry_scrubber import SENTRY_INIT_OPTIONS, before_send

    level, env_mode = request.param
    out = io.StringIO()
    loki_payloads: list[str] = []
    sentry_events: list[str] = []

    class _Transport(Transport):
        def capture_envelope(self, envelope) -> None:  # noqa: ANN001
            for item in envelope.items:
                sentry_events.append(item.get_bytes().decode("utf-8", "replace"))

    root = logging.getLogger()
    saved_handlers, saved_level = root.handlers[:], root.level
    monkeypatch.setattr(sys, "stdout", out)
    monkeypatch.setattr(logging_config, "DEBUG", level == logging.DEBUG)
    monkeypatch.setattr(logging_config, "ENV_MODE", env_mode)
    monkeypatch.setattr(logging_config, "LOKI_ENABLED", True)
    monkeypatch.setattr(LokiHandler, "_post", lambda self, payload: loki_payloads.append(json.dumps(payload)))
    monkeypatch.setenv("REDACT_LOG_TRACEBACKS", "false")  # the opt-out must not re-open the leak

    sentry_sdk.init(
        dsn="https://public@sentry.invalid/1",
        transport=_Transport,
        before_send=before_send,
        integrations=[LoggingIntegration(level=logging.DEBUG, event_level=logging.DEBUG)],
        default_integrations=False,
        **SENTRY_INIT_OPTIONS,
    )
    logging_config.setup_logging()
    try:
        yield lambda: (out, loki_payloads, sentry_events)
    finally:
        for h in root.handlers:
            if isinstance(h, LokiHandler):
                h.close()
        sentry_sdk.flush()
        sentry_sdk.init(dsn=None)
        root.handlers[:] = saved_handlers
        root.setLevel(saved_level)


def _everything(captured) -> str:  # noqa: ANN001
    for h in logging.getLogger().handlers:
        h.flush()
    from loki_handler import LokiHandler

    for h in logging.getLogger().handlers:
        if isinstance(h, LokiHandler):
            h.close()
    import sentry_sdk

    sentry_sdk.flush()
    out, loki, sentry = captured()
    return "\n".join([out.getvalue(), *loki, *sentry])


async def _run_uploads(api, user) -> None:  # noqa: ANN001
    hdr = _auth(user)
    # OFX (SGML v1) and QBO (XML v2) bank statements with marker metadata.
    for name, body in ((f"stmt-{M_FILE}.ofx", _ofx(xml_v2=False)), (f"stmt-{M_FILE}.qbo", _ofx(xml_v2=True))):
        r = await api.post(
            "/audit/bank-reconciliation",
            files={
                "bank_file": (name, body, "application/octet-stream"),
                "ledger_file": ("ledger.csv", LEDGER, "text/csv"),
            },
            headers=hdr,
        )
        assert r.status_code in (200, 400), r.text
    # Malformed OFX whose parse error could quote the input.
    await api.post(
        "/audit/bank-reconciliation",
        files={
            "bank_file": (f"bad-{M_FILE}.ofx", BAD_OFX, "application/octet-stream"),
            "ledger_file": ("l.csv", LEDGER, "text/csv"),
        },
        headers=hdr,
    )
    # A cell value the parser cannot read, on the TB route and a file-tool route.
    for path in ("/audit/trial-balance", "/audit/preflight"):
        try:
            await api.post(path, files={"file": (f"tb-{M_FILE}.csv", BAD_TB, "text/csv")}, headers=hdr)
        except Exception:  # noqa: BLE001 — ASGITransport re-raises an unhandled 500 after the app logged it
            pass
    # Parser errors routinely quote the offending text — both rejection handlers.
    with patch(
        "routes.audit_pipeline.audit_trial_balance_streaming", side_effect=ValueError(f"could not convert '{M_PARSE}'")
    ):
        r = await api.post("/audit/trial-balance", files={"file": ("tb.csv", TB, "text/csv")}, headers=hdr)
        assert r.status_code == 400, r.text
    with patch("preflight_engine.run_preflight", side_effect=ValueError(f"could not convert '{M_PARSE}'")):
        r = await api.post("/audit/preflight", files={"file": ("pf.csv", TB, "text/csv")}, headers=hdr)
        assert r.status_code == 400, r.text
    # A 422 whose validation error carries the submitted value.
    r = await api.post(
        "/audit/trial-balance",
        files={"file": ("tb.csv", TB, "text/csv")},
        data={"materiality_threshold": M_FORM},
        headers=hdr,
    )
    assert r.status_code == 422, r.text


CONFIGS = [
    (logging.INFO, "production"),
    (logging.DEBUG, "production"),
    (logging.INFO, "development"),
    (logging.DEBUG, "development"),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("captured_logs", CONFIGS, indirect=True, ids=lambda c: f"{logging.getLevelName(c[0])}-{c[1]}")
async def test_no_uploaded_value_reaches_any_log_sink(api, make_user, captured_logs):  # noqa: ANN001
    user = make_user(email="logs-879@example.com", tier=UserTier.SOLO)
    await _run_uploads(api, user)
    text = _everything(captured_logs)
    out, loki, sentry = captured_logs()
    # Each sink must have received records, or a pass proves nothing.
    assert "/audit/trial-balance" in out.getvalue(), "stdout handler not wired"
    assert loki, "Loki handler not wired"
    assert sentry, "Sentry transport not wired"
    leaked = [m for m in MARKERS if m in text]
    assert not leaked, f"uploaded values reached the logs: {leaked}"


def test_record_factory_strips_exception_text_at_creation():
    """Enforced where the record is made, not in a handler: any handler sees the scrubbed record."""
    import logging_config

    logging_config.install_safe_log_records()
    seen: list[logging.LogRecord] = []

    class _Keep(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            seen.append(record)

    lg = logging.getLogger("paciolus.test879")
    h = _Keep(level=logging.DEBUG)
    lg.addHandler(h)
    lg.setLevel(logging.DEBUG)
    try:
        try:
            raise ValueError(f"bad value {M_PARSE}")
        except ValueError as e:
            lg.debug("rejected: %s", e, exc_info=True)
            lg.warning(e)
    finally:
        lg.removeHandler(h)
    rendered = [logging.Formatter().format(r) for r in seen]
    assert len(rendered) == 2
    assert all(M_PARSE not in line for line in rendered), rendered
    assert all("ValueError" in line for line in rendered), rendered
