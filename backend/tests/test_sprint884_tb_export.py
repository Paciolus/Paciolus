"""Sprint 884 / 9D (review OUT-04): the "Trial Balance" export is the trial balance.

The CSV and the workbook's TB tab listed only flagged accounts (the workbook
once per flag) above the full ledger's debit and credit totals — one flagged
row of 25 over totals of 1,000. Now: every account once, totals taken from
those rows, a column marking flagged accounts, and the flags on their own
"Flagged Accounts" tab, one row per flag, with subtotals equal to their rows.
"""

from __future__ import annotations

import csv
import io
from decimal import Decimal

import httpx
import pytest
from openpyxl import load_workbook

from excel_generator import generate_workpaper
from export.serializers.csv import serialize_trial_balance_csv
from shared.schemas import AuditResultInput

ALL_ACCOUNTS = [
    {"account": "Cash", "debit": 600.0, "credit": 0.0, "type": "asset"},
    {"account": "Accounts Receivable", "debit": 375.005, "credit": 0.0, "type": "asset"},
    {"account": "Suspense", "debit": 25.0, "credit": 0.0, "type": "asset"},
    {"account": "Accounts Payable", "debit": 0.0, "credit": 400.0, "type": "liability"},
    {"account": "Revenue", "debit": 0.0, "credit": 600.005, "type": "revenue"},
]
# Suspense is flagged twice; Accounts Payable once; the rest not at all.
FLAGS = [
    {
        "account": "Suspense",
        "type": "asset",
        "issue": "Suspense account with balance",
        "amount": 25.0,
        "debit": 25.0,
        "credit": 0.0,
        "materiality": "immaterial",
        "severity": "medium",
        "anomaly_type": "suspense_account",
    },
    {
        "account": "Suspense",
        "type": "asset",
        "issue": "Round amount",
        "amount": 25.0,
        "debit": 25.0,
        "credit": 0.0,
        "materiality": "immaterial",
        "severity": "low",
        "anomaly_type": "rounding_anomaly",
    },
    {
        "account": "Accounts Payable",
        "type": "liability",
        "issue": "Large balance",
        "amount": -400.0,
        "debit": 0.0,
        "credit": 400.0,
        "materiality": "material",
        "severity": "high",
        "anomaly_type": "abnormal_balance",
    },
]


def _payload(**overrides) -> dict:
    base = {
        "status": "balanced",
        "balanced": True,
        "total_debits": 1000.01,
        "total_credits": 1000.01,
        "difference": 0.0,
        "row_count": 5,
        "message": "ok",
        "abnormal_balances": FLAGS,
        "has_risk_alerts": True,
        "materiality_threshold": 100.0,
        "material_count": 1,
        "immaterial_count": 2,
        "filename": "tb",
        "all_accounts": ALL_ACCOUNTS,
    }
    base.update(overrides)
    return base


def _csv_rows(data: bytes) -> list[list[str]]:
    return list(csv.reader(io.StringIO(data.decode("utf-8-sig"))))


def _d(value) -> Decimal:
    return Decimal(str(value or 0))


# ─────────────────────────────── CSV ───────────────────────────────


class TestTrialBalanceCsv:
    def test_every_account_once_with_a_flag_column(self):
        rows = _csv_rows(serialize_trial_balance_csv(AuditResultInput(**_payload())))
        header = rows[0]
        assert "Flagged" in header
        body = [dict(zip(header, r)) for r in rows[1:] if r and r[0].startswith("TB-")]
        assert [r["Account"] for r in body] == [a["account"] for a in ALL_ACCOUNTS]
        flagged = {r["Account"]: r["Flagged"] for r in body}
        assert flagged == {
            "Cash": "",
            "Accounts Receivable": "",
            "Suspense": "Yes (2)",
            "Accounts Payable": "Yes (1)",
            "Revenue": "",
        }

    def test_totals_are_the_sum_of_the_rows_shown(self):
        rows = _csv_rows(serialize_trial_balance_csv(AuditResultInput(**_payload())))
        header = rows[0]
        body = [dict(zip(header, r)) for r in rows[1:] if r and r[0].startswith("TB-")]
        totals = dict(zip(header, next(r for r in rows if r and r[0] == "TOTALS")))
        for col in ("Debit", "Credit", "Net Balance"):
            assert _d(totals[col]) == sum((_d(r[col]) for r in body), Decimal("0")), col
        # 375.005 and 600.005 are shown half-up as 375.01 and 600.01.
        assert totals["Debit"] == "1000.01"
        assert totals["Credit"] == "1000.01"
        assert totals["Net Balance"] == "0.00"

    def test_without_the_account_list_it_refuses_rather_than_export_a_partial_tb(self):
        with pytest.raises(ValueError, match="all_accounts"):
            serialize_trial_balance_csv(AuditResultInput(**_payload(all_accounts=None)))

    @pytest.mark.asyncio
    @pytest.mark.usefixtures("bypass_csrf")
    async def test_route_without_the_account_list_is_a_400(self, override_auth_verified):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/export/csv/trial-balance", json=_payload(all_accounts=None))
        assert response.status_code == 400
        assert "all_accounts" in response.text


# ─────────────────────────────── Workbook ───────────────────────────────


def _workbook(payload: dict):
    return load_workbook(io.BytesIO(generate_workpaper(payload, filename="tb")))


def _table(ws, header_row: int) -> tuple[list, list[tuple]]:
    rows = list(ws.iter_rows(values_only=True))
    return list(rows[header_row - 1]), rows[header_row:]


class TestWorkbook:
    def test_trial_balance_tab_lists_every_account_once(self):
        ws = _workbook(_payload())["Trial Balance"]
        header, rows = _table(ws, 3)
        body = [dict(zip(header, r)) for r in rows if r[0] and r[0] != "TOTALS"]
        assert [r["Account"] for r in body] == [a["account"] for a in ALL_ACCOUNTS]
        assert {r["Account"]: r["Flagged"] for r in body}["Suspense"] == "Yes (2)"
        assert {r["Account"]: r["Flagged"] for r in body}["Cash"] in (None, "")

    def test_trial_balance_totals_are_the_sum_of_its_rows(self):
        ws = _workbook(_payload())["Trial Balance"]
        header, rows = _table(ws, 3)
        body = [dict(zip(header, r)) for r in rows if r[0] and r[0] != "TOTALS"]
        totals = dict(zip(header, next(r for r in rows if r[0] == "TOTALS")))
        for col in ("Debit", "Credit", "Net"):
            assert _d(totals[col]) == sum((_d(r[col]) for r in body), Decimal("0")), col
        assert _d(totals["Debit"]) == Decimal("1000.01")

    def test_flags_tab_has_one_row_per_flag_and_subtotals_equal_their_rows(self):
        wb = _workbook(_payload())
        assert "Flagged Accounts" in wb.sheetnames
        ws = wb["Flagged Accounts"]
        rows = list(ws.iter_rows(values_only=True))
        flag_rows = [r for r in rows if isinstance(r[0], str) and r[0].startswith("TB-")]
        assert len(flag_rows) == len(FLAGS)
        assert sum(1 for r in flag_rows if r[1] == "Suspense") == 2

        subtotals = {r[0]: _d(r[4]) for r in rows if isinstance(r[0], str) and r[0].startswith("Subtotal")}
        material = sum((_d(r[4]) for r in flag_rows if r[0].startswith("TB-M")), Decimal("0"))
        immaterial = sum((_d(r[4]) for r in flag_rows if r[0].startswith("TB-I")), Decimal("0"))
        assert subtotals == {"Subtotal — material": material, "Subtotal — immaterial": immaterial}
        total = next(_d(r[4]) for r in rows if r[0] == "Total — all flags")
        assert total == material + immaterial

    def test_without_the_account_list_the_tab_says_so_and_shows_no_totals(self):
        ws = _workbook(_payload(all_accounts=None))["Trial Balance"]
        values = [v for row in ws.iter_rows(values_only=True) for v in row if v is not None]
        assert any("account list was not supplied" in str(v) for v in values)
        assert "TOTALS" not in values
