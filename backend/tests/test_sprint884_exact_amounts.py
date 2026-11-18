"""Sprint 884 / 9B (review TQ-12, OUT-19): amounts stay exact from engine to export.

Monetary values were turned into floats before output (lead sheets, the
financial statement builder, the payroll / fixed-asset / inventory /
three-way-match serializers, the loan workbook), so 90,071,992,547,409.93 came
back as ...409.94 and 9,007,199,254,740,993.01 reached Excel as ...994.0.

Decided (CEO, 2026-11-18): the largest supported amount is
999,999,999,999,999.99 — above it, a clear error. The API sends amounts as
JSON numbers carrying their exact digits. Excel holds 15 significant digits:
where a value has more, the workbook keeps the number, writes an exact text
copy beside it, and says the number is approximate.
"""

from __future__ import annotations

import io
import json
import re
import zipfile
from datetime import date
from decimal import Decimal

import httpx
import pytest
from pydantic import BaseModel

from shared.monetary import MAX_SUPPORTED_AMOUNT, AmountTooLargeError
from shared.parsing_helpers import parse_amount, safe_decimal

BIG = "90071992547409.93"  # first cent above 2**53 cents: a float cannot hold it
HALF = "1234.005"  # → 1234.01
NHALF = "-1234.005"  # → -1234.01
TOO_BIG = "9007199254740993.01"


def _loads(text: str):
    return json.loads(text, parse_float=Decimal)


def _xlsx_xml(data: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        return "\n".join(z.read(n).decode("utf-8") for n in z.namelist() if n.endswith(".xml"))


def _pdf_text(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return " ".join(" ".join((p.extract_text() or "") for p in reader.pages).split())


# ─────────────────────────────── The limit ───────────────────────────────


class TestLargestSupportedAmount:
    def test_the_limit(self):
        assert MAX_SUPPORTED_AMOUNT == Decimal("999999999999999.99")

    @pytest.mark.parametrize("text", ["999999999999999.99", "-999999999999999.99", BIG])
    def test_amounts_up_to_the_limit_parse(self, text):
        assert parse_amount(text) == Decimal(text)

    @pytest.mark.parametrize("text", [TOO_BIG, "1000000000000000", "-1,000,000,000,000,000.00", "1e16"])
    def test_amounts_above_the_limit_are_an_error_not_a_zero(self, text):
        with pytest.raises(AmountTooLargeError, match="999,999,999,999,999.99"):
            parse_amount(text)
        with pytest.raises(AmountTooLargeError):
            parse_amount(text, on_invalid="error")
        with pytest.raises(AmountTooLargeError):
            safe_decimal(text)

    @pytest.mark.asyncio
    @pytest.mark.usefixtures("bypass_csrf")
    async def test_tb_upload_above_the_limit_is_a_400_naming_the_limit(self, override_auth_verified):
        from main import app

        csv = f"Account Name,Debit,Credit\nCash,{TOO_BIG},0\nRevenue,0,{TOO_BIG}\n".encode()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/audit/trial-balance", files={"file": ("tb.csv", csv, "text/csv")})
        assert response.status_code == 400, response.text
        assert "999,999,999,999,999.99" in response.text


# ─────────────────────────────── Exact JSON ───────────────────────────────


class TestExactJson:
    def test_values_a_float_holds_exactly_stay_plain_floats(self):
        from shared.exact_json import exact_number

        assert exact_number(Decimal("1234.01")) == 1234.01
        assert isinstance(exact_number(Decimal("-0.01")), float)

    def test_a_response_model_writes_the_exact_digits(self):
        from shared.diagnostic_response_schemas import MonetaryDecimal
        from shared.exact_json import restore_exact_numbers

        class M(BaseModel):
            amount: MonetaryDecimal
            small: MonetaryDecimal

        raw = M(amount=Decimal(BIG), small=Decimal("0.10")).model_dump_json().encode()
        assert restore_exact_numbers(raw) == f'{{"amount":{BIG},"small":0.1}}'.encode()

    def test_above_the_limit_serialization_refuses(self):
        from shared.exact_json import exact_number

        with pytest.raises(AmountTooLargeError):
            exact_number(Decimal(TOO_BIG))


# ─────────────────────────────── Lead sheets ───────────────────────────────


def _accounts() -> list[dict]:
    rows = [
        {"account": "Cash", "debit": Decimal(BIG), "credit": Decimal("0"), "type": "asset"},
        {"account": "Revenue", "debit": Decimal("0"), "credit": Decimal(BIG), "type": "revenue"},
        {"account": "Accounts Receivable", "debit": Decimal(HALF), "credit": Decimal("0"), "type": "asset"},
        {"account": "Accounts Payable", "debit": Decimal("0"), "credit": Decimal(HALF), "type": "liability"},
    ]
    # 100 one-cent prepaid balances: a float sum drifts, a Decimal sum is 1.00.
    rows += [
        {"account": f"Prepaid Expense {i:03d}", "debit": Decimal("0.01"), "credit": Decimal("0"), "type": "asset"}
        for i in range(100)
    ]
    return rows


def _summary(grouping: dict, letter: str) -> dict:
    return next(s for s in grouping["summaries"] if s["lead_sheet"] == letter)


class TestLeadSheets:
    def test_lead_sheet_totals_are_exact_decimals(self):
        from lead_sheet_mapping import group_by_lead_sheet, lead_sheet_grouping_to_dict

        g = lead_sheet_grouping_to_dict(group_by_lead_sheet(_accounts()))
        assert _summary(g, "A")["net_balance"] == Decimal(BIG)
        assert isinstance(_summary(g, "A")["net_balance"], Decimal)
        assert _summary(g, "B")["net_balance"] == Decimal("1234.01")
        assert _summary(g, "G")["net_balance"] == Decimal("-1234.01")
        assert _summary(g, "D")["net_balance"] == Decimal("1.00")
        assert g["total_debits"] == Decimal(BIG) + Decimal("1234.01") + Decimal("1.00")


@pytest.mark.usefixtures("bypass_csrf")
class TestTrialBalanceApi:
    @pytest.mark.asyncio
    async def test_api_response_carries_the_exact_digits(self, override_auth_verified):
        from main import app

        lines = ["Account Name,Debit,Credit", f"Cash,{BIG},0", f"Revenue,0,{BIG}"]
        lines += [f"Accounts Receivable,{HALF},0", f"Accounts Payable,0,{HALF}"]
        lines += [f"Prepaid Expense {i:03d},0.01,0" for i in range(100)]
        lines += ["Prepaid Offset,0,1.00"]
        csv = ("\n".join(lines) + "\n").encode()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/audit/trial-balance", files={"file": ("tb.csv", csv, "text/csv")})
        assert response.status_code == 200, response.text[:500]
        assert re.search(rf"[:\[,]{re.escape(BIG)}[,\]}}]", response.text), "BIG is not an unquoted JSON number"
        assert "\\u0000" not in response.text
        body = _loads(response.text)
        assert body["total_debits"] == Decimal(BIG) + Decimal("1234.01") + Decimal("1.00")
        assert body["total_credits"] == Decimal(BIG) + Decimal("1234.01") + Decimal("1.00")
        g = body["lead_sheet_grouping"]
        assert _summary(g, "A")["net_balance"] == Decimal(BIG)
        assert _summary(g, "B")["net_balance"] == Decimal("1234.01")
        assert _summary(g, "G")["net_balance"] == Decimal("-1234.01")


# ─────────────────────────── Financial statements ───────────────────────────


GROUPING_JSON = (
    '{"lead_sheet_grouping": {"summaries": ['
    f'{{"lead_sheet": "A", "name": "Cash", "net_balance": {BIG}, "accounts": []}},'
    f'{{"lead_sheet": "B", "name": "Receivables", "net_balance": {HALF}, "accounts": []}},'
    f'{{"lead_sheet": "D", "name": "Prepaid", "net_balance": {NHALF}, "accounts": []}},'
    f'{{"lead_sheet": "K", "name": "Equity", "net_balance": -{BIG}, "accounts": []}}'
    ']}, "filename": "fs", "entity_name": "Exact Co", "period_end": "2026-12-31"}'
)


class TestFinancialStatements:
    def test_builder_keeps_exact_decimals(self):
        from financial_statement_builder import FinancialStatementBuilder

        grouping = _loads(GROUPING_JSON)["lead_sheet_grouping"]
        fs = FinancialStatementBuilder(grouping).build()
        lines = {li.label: li.amount for li in fs.balance_sheet}
        assert lines["Cash and Cash Equivalents"] == Decimal(BIG)
        assert lines["Receivables"] == Decimal("1234.01")
        assert lines["Prepaid Expenses"] == Decimal("-1234.01")
        assert fs.total_assets == Decimal(BIG)  # 1234.01 - 1234.01
        assert isinstance(fs.total_assets, Decimal)

    @pytest.mark.asyncio
    @pytest.mark.usefixtures("bypass_csrf")
    async def test_pdf_route_with_the_real_builder_and_renderer(self, override_auth_verified):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/export/financial-statements?format=pdf",
                content=GROUPING_JSON,
                headers={"Content-Type": "application/json"},
            )
        assert response.status_code == 200, response.text[:300]
        text = _pdf_text(response.content)
        assert "$90,071,992,547,409.93" in text
        assert "$1,234.01" in text
        assert "-1,234.01" in text

    @pytest.mark.asyncio
    @pytest.mark.usefixtures("bypass_csrf")
    async def test_excel_route_writes_exact_xml_and_an_exact_text_copy(self, override_auth_verified):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/export/financial-statements?format=excel",
                content=GROUPING_JSON,
                headers={"Content-Type": "application/json"},
            )
        assert response.status_code == 200, response.text[:300]
        xml = _xlsx_xml(response.content)
        assert f"<v>{BIG}</v>" in xml
        assert "<v>1234.01</v>" in xml
        assert "<v>-1234.01</v>" in xml
        assert "90,071,992,547,409.93" in xml  # the exact text copy
        assert "approximate" in xml.lower()


# ─────────────────────────────── Loan workbook ───────────────────────────────


class TestLoanWorkbook:
    def _workbook_xml(self, principal: str, periods: int = 1) -> str:
        from loan_amortization_engine import LoanConfig, generate_amortization_schedule
        from loan_amortization_excel import build_amortization_workbook

        cfg = LoanConfig(
            principal=Decimal(principal), annual_rate=Decimal("0"), term_periods=periods, start_date=date(2026, 1, 1)
        )
        return _xlsx_xml(build_amortization_workbook(generate_amortization_schedule(cfg)))

    def test_large_principal_is_exact_in_the_xml_with_a_text_copy(self):
        xml = self._workbook_xml(BIG)
        assert f"<v>{BIG}</v>" in xml
        assert "90,071,992,547,409.93" in xml
        assert "approximate" in xml.lower()

    def test_ordinary_amounts_get_no_text_copy(self):
        xml = self._workbook_xml("1234.01")
        assert "<v>1234.01</v>" in xml
        assert "approximate" not in xml.lower()

    def test_repeated_cents_total_exactly(self):
        xml = self._workbook_xml("0.03", periods=3)
        assert xml.count("<v>0.01</v>") >= 6  # payment and principal, three periods
        assert "<v>0.03</v>" in xml


# ─────────────────── Payroll, fixed assets, inventory, 3-way match ───────────────────


class TestToolSerializers:
    def test_payroll_entry(self):
        from services.audit.payroll_testing.analysis import PayrollEntry

        d = PayrollEntry(gross_pay=Decimal(BIG), net_pay=Decimal(HALF), deductions=Decimal(NHALF)).to_dict()
        assert (d["gross_pay"], d["net_pay"], d["deductions"]) == (
            Decimal(BIG),
            Decimal("1234.01"),
            Decimal("-1234.01"),
        )

    def test_fixed_asset_entry(self):
        from services.audit.fixed_asset_testing.analysis import FixedAssetEntry

        d = FixedAssetEntry(cost=Decimal(BIG), accumulated_depreciation=Decimal(HALF)).to_dict()
        assert (d["cost"], d["accumulated_depreciation"]) == (Decimal(BIG), Decimal("1234.01"))

    def test_inventory_entry(self):
        from services.audit.inventory_testing.analysis import InventoryEntry

        d = InventoryEntry(unit_cost=Decimal("0.0125"), extended_value=Decimal(BIG)).to_dict()
        assert d["extended_value"] == Decimal(BIG)
        assert d["unit_cost"] == Decimal("0.0125")  # a unit price is not rounded to cents

    def test_three_way_match_documents(self):
        from three_way_match_engine import Invoice, PurchaseOrder

        po = PurchaseOrder(total_amount=Decimal(BIG), unit_price=Decimal("0.0125")).to_dict()
        inv = Invoice(total_amount=Decimal(NHALF)).to_dict()
        assert po["total_amount"] == Decimal(BIG)
        assert po["unit_price"] == Decimal("0.0125")
        assert inv["total_amount"] == Decimal("-1234.01")

    @pytest.mark.parametrize(
        "model_path",
        [
            "PayrollEntryResponse.gross_pay",
            "FixedAssetEntryResponse.cost",
            "InventoryEntryResponse.extended_value",
            "PurchaseOrderResponse.total_amount",
        ],
    )
    def test_response_schemas_send_exact_numbers(self, model_path):
        import shared.testing_response_schemas as schemas

        model_name, field = model_path.split(".")
        model = getattr(schemas, model_name)
        assert model.model_fields[field].annotation is not float, f"{model_path} is still a float"
