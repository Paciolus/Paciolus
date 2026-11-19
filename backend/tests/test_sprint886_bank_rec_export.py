"""Sprint 886 / 11B + 11G (review OUT-10, OUT-16): the bank reconciliation memo and CSV
carry the tests, score, aging and thresholds of the run.

The page sent only the summary, the column detections and the split-search
disclosure; ``BankRecMemoInput`` declared nothing else. The memo then printed a
LOW tier and a 0/100 score, read an aging structure the engine never emits
(``aging_summary`` / ``outstanding_deposits``), and said nothing about the
thresholds the run applied. The CSV carried none of it.

Each test runs a real reconciliation through ``/audit/bank-reconciliation``
(its response is what the screen renders) and posts that response, as the page
now sends it, to the memo and CSV routes.
"""

from __future__ import annotations

import csv
import io
import re

import httpx
import pytest

# Statement closes 2026-03-31 (ages are measured to it, not to today).
BANK_CSV = (
    "Date,Description,Amount\n"
    "2026-03-01,Opening deposit,5000.00\n"
    "2026-03-31,Bank service fee,-25.00\n"
    "2026-03-31,Incoming wire,20000.00\n"
).encode()
LEDGER_CSV = (
    "Date,Description,Amount\n"
    "2026-03-01,Opening deposit,5000.00\n"
    "2026-03-05,Customer deposit,800.00\n"
    "2025-11-20,Check 1001,-300.00\n"
).encode()


def _pdf_text(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return " ".join(" ".join((p.extract_text() or "") for p in reader.pages).split())


async def _post(path: str, **kwargs) -> httpx.Response:
    from main import app

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        return await client.post(path, **kwargs)


async def _reconcile(**thresholds: str) -> dict:
    response = await _post(
        "/audit/bank-reconciliation",
        files={
            "bank_file": ("bank.csv", BANK_CSV, "text/csv"),
            "ledger_file": ("ledger.csv", LEDGER_CSV, "text/csv"),
        },
        data=thresholds,
    )
    assert response.status_code == 200, response.text
    return response.json()


def _memo_body(screen: dict) -> dict:
    """What the page sends to /export/bank-rec-memo: every result except the match list."""
    body = {k: v for k, v in screen.items() if k != "summary"}
    body["summary"] = {k: v for k, v in screen["summary"].items() if k != "matches"}
    body["filename"] = "bank"
    return body


def _csv_body(screen: dict) -> dict:
    return {**screen, "matches": screen["summary"]["matches"], "filename": "bank"}


def _csv_rows(data: bytes) -> list[list[str]]:
    return list(csv.reader(io.StringIO(data.decode("utf-8-sig"))))


def _section(rows: list[list[str]], title: str) -> list[list[str]]:
    start = rows.index([title]) + 2
    out = []
    for row in rows[start:]:
        if not row:
            break
        out.append(row)
    return out


@pytest.mark.asyncio
@pytest.mark.usefixtures("bypass_csrf", "override_auth_verified")
class TestMemoAndCsvMatchTheRun:
    async def test_fixture_flags_stale_high_value_and_unmatched_items(self):
        screen = await _reconcile(materiality="1000", performance_materiality="750")
        counts = {t["test_name"]: t["flagged_count"] for t in screen["rec_tests"]}
        assert counts["Stale Deposits (>10 days)"] == 1
        assert counts["Stale Checks (>90 days)"] == 1
        assert counts["High Value (>Materiality)"] >= 1
        assert screen["summary"]["bank_only_count"] == 2
        assert screen["composite_score"]["score"] > 0

    async def test_memo_carries_score_tests_aging_and_thresholds(self):
        screen = await _reconcile(materiality="1000", performance_materiality="750")
        response = await _post("/export/bank-rec-memo", json=_memo_body(screen))
        assert response.status_code == 200, response.text
        text = _pdf_text(response.content)

        composite = screen["composite_score"]
        score = f"{composite['score']:.1f}"
        assert re.search(rf"Composite Diagnostic Score\s*\.*\s*{re.escape(score)} / 100", text)
        assert "LOW (0/100)" not in text
        assert not re.search(r"(?<![\d.])0(\.0)? ?/ ?100", text)
        tier = composite["risk_tier"].upper()
        assert re.search(rf"Diagnostic Tier\s*\.*\s*{tier} \({re.escape(score)}/100\)", text)

        for test in screen["rec_tests"]:
            assert re.search(rf"{re.escape(test['test_name'])}\s+{test['flagged_count']}\b", text), test["test_name"]
        # One count per test, as on screen: 5 tests, not the 8 the score used to claim.
        assert re.search(rf"Tests Executed\s+{len(screen['rec_tests'])}\b", text)

        for aging in screen["outstanding_aging"]:
            label = {"bank_only": "Bank only", "ledger_only": "Ledger only"}[aging["category"]]
            assert re.search(
                rf"{label}\s+{aging['total_count']}\s+{aging['over_10_days']}\s+{aging['over_30_days']}\b", text
            ), label

        assert re.search(r"Materiality \(overall\)\s*\.*\s*\$1,000\.00 — entered for this run", text)
        assert re.search(r"Performance materiality\s*\.*\s*\$750\.00 — entered for this run", text)

    async def test_default_thresholds_are_named_as_the_paciolus_default(self):
        screen = await _reconcile()
        text = _pdf_text((await _post("/export/bank-rec-memo", json=_memo_body(screen))).content)
        assert re.search(r"Materiality \(overall\)\s*\.*\s*\$50,000\.00 — Paciolus default", text)
        assert re.search(r"Performance materiality\s*\.*\s*\$\S+ — Paciolus default", text)

    async def test_csv_carries_the_same_score_tests_aging_and_thresholds(self):
        screen = await _reconcile(materiality="1000", performance_materiality="750")
        response = await _post("/export/csv/bank-rec", json=_csv_body(screen))
        assert response.status_code == 200, response.text
        rows = _csv_rows(response.content)

        tests = {r[0]: r[1] for r in _section(rows, "RECONCILIATION TESTS")}
        for test in screen["rec_tests"]:
            assert tests[test["test_name"]] == str(test["flagged_count"])

        aging = {r[0]: r[1:4] for r in _section(rows, "OUTSTANDING ITEMS AGING")}
        for a in screen["outstanding_aging"]:
            label = {"bank_only": "Bank only", "ledger_only": "Ledger only"}[a["category"]]
            assert aging[label] == [str(a["total_count"]), str(a["over_10_days"]), str(a["over_30_days"])]

        score = {r[0]: r[1] for r in _section(rows, "DIAGNOSTIC SCORE")}
        assert score["Composite Diagnostic Score"] == f"{screen['composite_score']['score']:.1f}"
        assert score["Diagnostic Tier"] == screen["composite_score"]["risk_tier"].upper()

        thresholds = {r[0]: r[1:] for r in _section(rows, "THRESHOLDS APPLIED")}
        assert thresholds["Materiality (overall)"] == ["1000.00", "Entered for this run"]
        assert thresholds["Performance materiality"] == ["750.00", "Entered for this run"]


@pytest.mark.asyncio
@pytest.mark.usefixtures("bypass_csrf", "override_auth_verified")
class TestNotSuppliedIsNotLow:
    async def test_memo_without_score_says_not_available_not_low(self):
        screen = await _reconcile(materiality="1000", performance_materiality="750")
        body = _memo_body(screen)
        for key in ("composite_score", "rec_tests", "outstanding_aging", "active_thresholds"):
            body.pop(key)
        text = _pdf_text((await _post("/export/bank-rec-memo", json=body)).content)

        assert re.search(r"Composite Diagnostic Score\s*\.*\s*Not available", text)
        assert "LOW (0/100)" not in text
        assert not re.search(r"(?<![\d.])0(\.0)? ?/ ?100", text)
        assert re.search(r"Thresholds\s*\.*\s*Not available", text)
        assert re.search(r"Aging\s*\.*\s*Not available", text)

    async def test_csv_without_score_says_not_available(self):
        screen = await _reconcile()
        body = _csv_body(screen)
        body.pop("composite_score")
        rows = _csv_rows((await _post("/export/csv/bank-rec", json=body)).content)
        score = {r[0]: r[1] for r in _section(rows, "DIAGNOSTIC SCORE")}
        assert score["Composite Diagnostic Score"] == "Not available"
