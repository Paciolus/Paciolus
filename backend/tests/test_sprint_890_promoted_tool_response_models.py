"""Sprint 890 (CEO brief 15C, review ST-10): the five promoted JSON tools have response models.

``shared/promoted_tool_response_schemas.py`` models each engine's ``to_dict()``
exactly. Two properties are pinned here for every tool:

1. **The model accepts the engine's output** — on a full case and on a case
   that takes the optional/empty branches (None fields, empty lists).
2. **The round trip is exact** — ``model_dump(mode="json") == to_dict()``. That
   proves nothing is added, dropped or coerced; in particular every amount
   stays the engine's exact decimal string.

A route-level test per tool then checks the live response still validates and
still carries amounts as strings after FastAPI's ``response_model`` pass.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

import httpx
import pytest
from pydantic import BaseModel, ValidationError

from book_to_tax_engine import (
    AdjustmentDirection,
    AdjustmentEntry,
    BookToTaxConfig,
    DeferredTaxRollforwardInput,
    DifferenceType,
    calculate_book_to_tax,
)
from cash_flow_projector_engine import AgingBuckets, CashFlowConfig, RecurringFlow, project_cash_flow
from form_1099_engine import (
    EntityType,
    Form1099Config,
    PaymentCategory,
    PaymentMethod,
    VendorPayment,
    VendorRecord,
    prepare_1099s,
)
from intercompany_elimination_engine import (
    EntityAccount,
    EntityTrialBalance,
    IntercompanyConfig,
    run_intercompany_elimination,
)
from shared.promoted_tool_response_schemas import (
    BookToTaxResponse,
    CashFlowForecastResponse,
    Form1099Response,
    IntercompanyEliminationResponse,
    W2ReconciliationResponse,
)
from tests.test_promoted_tool_engagement_wiring import (
    _book_to_tax_payload,
    _cash_flow_payload,
    _form_1099_payload,
    _intercompany_payload,
    _w2_payload,
)
from w2_reconciliation_engine import (
    EmployeePayroll,
    EmployeeW2Draft,
    Form941Quarter,
    HsaCoverage,
    W2ReconciliationConfig,
    reconcile_w2,
)

D = Decimal


def _assert_exact_round_trip(model: type[BaseModel], d: dict[str, Any]) -> BaseModel:
    parsed = model.model_validate(d)
    assert parsed.model_dump(mode="json") == d
    return parsed


# =============================================================================
# Form 1099
# =============================================================================


def _form_1099_full() -> dict[str, Any]:
    vendors = [
        VendorRecord(
            "V1", "Acme Consulting LLC", tin="12-3456789", entity_type=EntityType.LLC, address_line_1="1 Main"
        ),
        VendorRecord("V2", "Bob Smith", tin=None, entity_type=EntityType.INDIVIDUAL),
        VendorRecord("V3", "Landlord Partners", tin="123", entity_type=EntityType.PARTNERSHIP),
        VendorRecord("V4", "Small Payee", tin="98-7654321", entity_type=EntityType.UNKNOWN),
        VendorRecord("V5", "MegaCorp Inc", tin="11-1111111", entity_type=EntityType.CORPORATION),
    ]
    payments = [
        VendorPayment("V1", D("2500.00"), PaymentCategory.NONEMPLOYEE_COMP, PaymentMethod.CHECK, "2026-03-01"),
        VendorPayment("V1", D("400.00"), PaymentCategory.NONEMPLOYEE_COMP, PaymentMethod.CREDIT_CARD, "2026-04-01"),
        VendorPayment("V2", D("3000.00"), PaymentCategory.NONEMPLOYEE_COMP, PaymentMethod.ACH, "2026-05-01"),
        VendorPayment("V3", D("24000.00"), PaymentCategory.RENTS, PaymentMethod.CHECK, "2026-06-01"),
        VendorPayment("V3", D("50.00"), PaymentCategory.ROYALTIES, PaymentMethod.CHECK, "2026-06-02"),
        VendorPayment("V4", D("900.00"), PaymentCategory.NONEMPLOYEE_COMP, PaymentMethod.CHECK, "2026-07-01"),
        VendorPayment("V5", D("5000.00"), PaymentCategory.NONEMPLOYEE_COMP, PaymentMethod.CHECK, "2026-07-02"),
        VendorPayment("V5", D("1200.00"), PaymentCategory.ATTORNEY_FEES, PaymentMethod.WIRE, "2026-07-03"),
        VendorPayment("V9", D("100.00"), PaymentCategory.OTHER, PaymentMethod.CHECK, "2026-07-04"),
        VendorPayment("V1", D("100.00"), PaymentCategory.NONEMPLOYEE_COMP, PaymentMethod.CHECK, "2025-12-31"),
    ]
    return prepare_1099s(Form1099Config(tax_year=2026, vendors=vendors, payments=payments)).to_dict()


class TestForm1099Model:
    def test_full_case_round_trips_exactly(self):
        d = _form_1099_full()
        parsed = _assert_exact_round_trip(Form1099Response, d)
        assert parsed.candidates, "the case should produce filing candidates"
        assert parsed.below_threshold_payees, "the 2026 $2,000 threshold should leave a payee below it"
        assert parsed.w9_collection_list
        assert parsed.notices
        assert isinstance(d["candidates"][0]["total_reportable"], str)

    def test_empty_inputs_round_trip(self):
        d = prepare_1099s(Form1099Config(tax_year=2025, vendors=[], payments=[])).to_dict()
        parsed = _assert_exact_round_trip(Form1099Response, d)
        assert parsed.candidates == [] and parsed.below_threshold_payees == []
        assert parsed.summary.totals_by_form == {}

    def test_thresholds_none_is_accepted(self):
        d = _form_1099_full()
        d["thresholds"] = None
        _assert_exact_round_trip(Form1099Response, d)

    def test_drift_is_rejected(self):
        d = _form_1099_full()
        d["unexpected"] = 1
        with pytest.raises(ValidationError):
            Form1099Response.model_validate(d)
        d = _form_1099_full()
        d["candidates"][0]["total_reportable"] = 2500.0
        with pytest.raises(ValidationError):
            Form1099Response.model_validate(d)


# =============================================================================
# Book-to-tax
# =============================================================================


def _book_to_tax(income: str, adjustments: list[AdjustmentEntry], total_assets: str = "50000000") -> dict[str, Any]:
    return calculate_book_to_tax(
        BookToTaxConfig(
            tax_year=2026,
            book_pretax_income=D(income),
            total_assets=D(total_assets),
            federal_tax_rate=D("0.21"),
            adjustments=adjustments,
            rollforward=DeferredTaxRollforwardInput(beginning_dta=D("1500.00"), beginning_dtl=D("4200.00")),
            state_tax_rate=D("0.05"),
        )
    ).to_dict()


_ALL_ADJUSTMENT_KINDS = [
    AdjustmentEntry("Meals (50%)", D("10000.00"), DifferenceType.PERMANENT, AdjustmentDirection.ADD, "meals_50pct"),
    AdjustmentEntry("Muni interest", D("2500.00"), DifferenceType.PERMANENT, AdjustmentDirection.SUBTRACT),
    AdjustmentEntry("Bad debt reserve", D("7000.00"), DifferenceType.TEMPORARY, AdjustmentDirection.ADD),
    AdjustmentEntry(
        "Bonus depreciation",
        D("40000.00"),
        DifferenceType.TEMPORARY,
        AdjustmentDirection.SUBTRACT,
        "depreciation_timing",
    ),
]


class TestBookToTaxModel:
    def test_full_case_round_trips_exactly(self):
        d = _book_to_tax("500000.00", _ALL_ADJUSTMENT_KINDS)
        parsed = _assert_exact_round_trip(BookToTaxResponse, d)
        assert parsed.entity_size == "large"
        m1 = parsed.schedule_m1
        assert m1.permanent_additions and m1.temporary_additions
        assert m1.permanent_subtractions and m1.temporary_subtractions
        assert parsed.schedule_m3.income_items and parsed.schedule_m3.expense_items
        assert isinstance(d["tax_provision"]["total_tax_expense"], str)

    def test_loss_year_with_no_adjustments_round_trips(self):
        d = _book_to_tax("-100000", [], total_assets="1000000")
        parsed = _assert_exact_round_trip(BookToTaxResponse, d)
        assert parsed.entity_size == "small"
        assert parsed.tax_provision.is_complete is False
        assert parsed.tax_provision.limitations
        assert parsed.schedule_m1.permanent_additions == []
        assert parsed.schedule_m3.income_items == [] and parsed.schedule_m3.expense_items == []

    def test_drift_is_rejected(self):
        d = _book_to_tax("500000.00", _ALL_ADJUSTMENT_KINDS)
        d["tax_provision"]["effective_rate"] = 0.26
        with pytest.raises(ValidationError):
            BookToTaxResponse.model_validate(d)


# =============================================================================
# Cash-flow projector
# =============================================================================


def _cash_flow(opening: str, *, ar: AgingBuckets, ap: AgingBuckets, flows, min_safe: str | None) -> dict[str, Any]:
    return project_cash_flow(
        CashFlowConfig(
            opening_balance=D(opening),
            start_date=date(2026, 5, 1),
            ar_aging=ar,
            ap_aging=ap,
            recurring_flows=flows,
            min_safe_cash=D(min_safe) if min_safe is not None else None,
        )
    ).to_dict()


class TestCashFlowModel:
    def test_full_case_round_trips_exactly(self):
        d = _cash_flow(
            "20000.00",
            ar=AgingBuckets(D("50000"), D("25000"), D("10000"), D("5000"), D("2000")),
            ap=AgingBuckets(D("20000"), D("10000"), D("8000"), D("4000"), D("3000")),
            flows=[RecurringFlow("Payroll", D("-30000"), "biweekly", date(2026, 5, 1))],
            min_safe="10000",
        )
        parsed = _assert_exact_round_trip(CashFlowForecastResponse, d)
        assert set(d["scenarios"]) == {"base", "stress", "best"}
        assert set(d["scenarios"]["base"]["horizon"]) == {"30", "60", "90"}
        assert parsed.scenarios.base.ap_deferral_candidates
        assert parsed.scenarios.base.ap_deferral_rule is not None
        assert parsed.scenarios.stress.ap_deferral_candidates == []
        assert parsed.scenarios.stress.goes_negative is True
        assert isinstance(d["scenarios"]["base"]["daily"][0]["ending_balance"], str)

    def test_empty_aging_no_flows_no_min_cash_round_trips(self):
        d = _cash_flow("1000.00", ar=AgingBuckets(), ap=AgingBuckets(), flows=[], min_safe=None)
        parsed = _assert_exact_round_trip(CashFlowForecastResponse, d)
        assert parsed.inputs.min_safe_cash is None
        base = parsed.scenarios.base
        assert base.first_negative_day is None and base.ap_deferral_rule is None
        assert base.collection_priorities == [] and base.ap_deferral_candidates == []

    def test_drift_is_rejected(self):
        d = _cash_flow("1000.00", ar=AgingBuckets(), ap=AgingBuckets(), flows=[], min_safe=None)
        d["scenarios"]["worst"] = d["scenarios"]["base"]
        with pytest.raises(ValidationError):
            CashFlowForecastResponse.model_validate(d)


# =============================================================================
# Intercompany elimination
# =============================================================================


def _intercompany_full() -> dict[str, Any]:
    return run_intercompany_elimination(
        IntercompanyConfig(
            entities=[
                EntityTrialBalance(
                    "P",
                    "Parent Co",
                    [
                        EntityAccount("Cash", D("50000.00"), D("0")),
                        EntityAccount("Due From Sub One", D("10000.00"), D("0"), counterparty_entity="S1"),
                        EntityAccount("Intercompany Receivable - Sub Two", D("5000.00"), D("0"), "S2"),
                        EntityAccount("Intercompany management fee revenue", D("0"), D("3000.00"), "S3"),
                    ],
                ),
                EntityTrialBalance(
                    "S1",
                    "Sub One",
                    [
                        EntityAccount("Due To Parent Co", D("0"), D("10000.00"), counterparty_entity="P"),
                        EntityAccount("Retained earnings", D("0"), D("2000.00")),
                    ],
                ),
                EntityTrialBalance(
                    "S2",
                    "Sub Two",
                    [EntityAccount("Intercompany Payable - Parent Co", D("0"), D("4200.00"), "P")],
                ),
            ],
            tolerance=D("1.00"),
        )
    ).to_dict()


class TestIntercompanyModel:
    def test_full_case_round_trips_exactly(self):
        d = _intercompany_full()
        parsed = _assert_exact_round_trip(IntercompanyEliminationResponse, d)
        assert parsed.pairs and parsed.mismatches and parsed.elimination_journal_entries
        assert parsed.summary.consolidation_complete is False
        assert {m.kind for m in parsed.mismatches} >= {"amount_mismatch", "no_reciprocal"}
        assert isinstance(d["worksheet"]["consolidated_debits"], str)

    def test_no_intercompany_activity_round_trips(self):
        d = run_intercompany_elimination(
            IntercompanyConfig(
                entities=[
                    EntityTrialBalance("A", "Alpha", [EntityAccount("Cash", D("100"), D("0"))]),
                    EntityTrialBalance("B", "Beta", [EntityAccount("Revenue", D("0"), D("100"))]),
                ]
            )
        ).to_dict()
        parsed = _assert_exact_round_trip(IntercompanyEliminationResponse, d)
        assert parsed.intercompany_lines == [] and parsed.pairs == [] and parsed.mismatches == []
        assert parsed.summary.consolidation_complete is True

    def test_drift_is_rejected(self):
        d = _intercompany_full()
        d["summary"]["entity_count"] = "3"
        with pytest.raises(ValidationError):
            IntercompanyEliminationResponse.model_validate(d)


# =============================================================================
# W-2 / W-3 reconciliation
# =============================================================================


def _w2_full() -> dict[str, Any]:
    employees = [
        EmployeePayroll(
            "E1",
            "Alice",
            age=None,
            federal_wages=D("80000.00"),
            federal_withholding=D("12000.00"),
            ss_wages=D("80000.00"),
            ss_tax_withheld=D("4960.00"),
            medicare_wages=D("80000.00"),
            medicare_tax_withheld=D("1160.00"),
            hsa_contributions=D("5000.00"),
            hsa_coverage=HsaCoverage.SELF_ONLY,
        ),
        EmployeePayroll(
            "E2",
            "Bob",
            age=45,
            federal_wages=D("250000.00"),
            federal_withholding=D("60000.00"),
            ss_wages=D("250000.00"),
            ss_tax_withheld=D("15500.00"),
            medicare_wages=D("250000.00"),
            medicare_tax_withheld=D("3625.00"),
        ),
        EmployeePayroll("E3", "Carol", federal_wages=D("40000.00"), ss_wages=D("40000.00"), medicare_wages=D("40000")),
    ]
    drafts = [
        EmployeeW2Draft("E1", D("80000.00"), D("12000.00"), D("80000.00"), D("4960.00"), D("80000.00"), D("1160.00")),
        EmployeeW2Draft(
            "E2", D("249000.00"), D("60000.00"), D("250000.00"), D("15500.00"), D("250000.00"), D("3625.00")
        ),
        EmployeeW2Draft("E2", D("1.00")),
        EmployeeW2Draft("X9", D("500.00")),
    ]
    quarters = [Form941Quarter(q, D("90000"), D("18000"), D("90000"), D("90000")) for q in (1, 2, 3, 4)]
    return reconcile_w2(
        W2ReconciliationConfig(tax_year=2025, employees=employees, w2_drafts=drafts, form_941_quarters=quarters)
    ).to_dict()


class TestW2Model:
    def test_full_case_round_trips_exactly(self):
        d = _w2_full()
        parsed = _assert_exact_round_trip(W2ReconciliationResponse, d)
        assert parsed.employee_discrepancies and parsed.form_941_mismatches
        assert parsed.w3_totals is not None
        assert parsed.checks_not_run
        assert parsed.summary.duplicate_w2_drafts == ["E2"] and parsed.summary.orphan_w2_drafts == ["X9"]
        assert {m.compared_with for m in parsed.form_941_mismatches} == {"payroll_ytd", "w3"}
        assert isinstance(d["w3_totals"]["total_federal_wages"], str)

    def test_no_drafts_and_incomplete_941s_round_trip(self):
        d = reconcile_w2(
            W2ReconciliationConfig(
                tax_year=2025,
                employees=[EmployeePayroll("E1", "Alice", federal_wages=D("1000"))],
                form_941_quarters=[Form941Quarter(1), Form941Quarter(2), Form941Quarter(2)],
            )
        ).to_dict()
        parsed = _assert_exact_round_trip(W2ReconciliationResponse, d)
        assert parsed.w3_totals is None and parsed.summary.w3_status is not None
        assert parsed.form_941_mismatches == []
        assert parsed.summary.form_941_quarters_missing == [3, 4]
        assert parsed.summary.form_941_quarters_duplicated == [2]
        assert [n.reason for n in parsed.checks_not_run] == ["form_941_quarters_incomplete"]

    def test_empty_run_round_trips(self):
        d = reconcile_w2(W2ReconciliationConfig(tax_year=2025, employees=[])).to_dict()
        parsed = _assert_exact_round_trip(W2ReconciliationResponse, d)
        assert parsed.employee_discrepancies == [] and parsed.checks_not_run == []

    def test_drift_is_rejected(self):
        d = _w2_full()
        d["statutory_basis_note"] = None
        with pytest.raises(ValidationError):
            W2ReconciliationResponse.model_validate(d)


# =============================================================================
# Routes: the live response passes response_model and keeps amounts as strings
# =============================================================================


@pytest.fixture
def _tax_figures_in_force(monkeypatch):
    """Pin the clock on the Sprint 856 confirmation deadline (the last day the gate is open)."""
    import tax_figures_status as tfs

    monkeypatch.setattr(tfs, "_today", lambda: tfs.PRACTITIONER_CONFIRMATION_DEADLINE)


ROUTE_CASES = [
    (
        "/audit/form-1099",
        _form_1099_payload,
        Form1099Response,
        lambda body: body["candidates"][0]["total_reportable"],
    ),
    (
        "/audit/book-to-tax",
        _book_to_tax_payload,
        BookToTaxResponse,
        lambda body: body["tax_provision"]["total_tax_expense"],
    ),
    (
        "/audit/cash-flow-projector",
        _cash_flow_payload,
        CashFlowForecastResponse,
        lambda body: body["scenarios"]["base"]["daily"][0]["ending_balance"],
    ),
    (
        "/audit/intercompany-elimination",
        _intercompany_payload,
        IntercompanyEliminationResponse,
        lambda body: body["worksheet"]["consolidated_debits"],
    ),
    (
        "/audit/w2-reconciliation",
        _w2_payload,
        W2ReconciliationResponse,
        None,  # the minimal payload is clean; test_w2_route_amounts_are_strings puts amounts on the wire
    ),
]


@pytest.mark.usefixtures("bypass_csrf", "_tax_figures_in_force")
class TestRoutesServeTheModel:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(("path", "payload_fn", "model", "amount"), ROUTE_CASES, ids=[c[0] for c in ROUTE_CASES])
    async def test_route_response_matches_model(self, override_auth_verified, path, payload_fn, model, amount):
        from main import app

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            r = await client.post(path, json=payload_fn())
        assert r.status_code == 200, r.text
        body = r.json()
        assert model.model_validate(body).model_dump(mode="json") == body
        if amount is not None:
            assert isinstance(amount(body), str)

    @pytest.mark.asyncio
    async def test_w2_route_amounts_are_strings(self, override_auth_verified):
        """The minimal W-2 payload is clean, so add a draft that disagrees to get an amount on the wire."""
        from main import app

        payload = _w2_payload()
        payload["w2_drafts"] = [
            {
                "employee_id": "E001",
                "box_1_federal_wages": "79000.00",
                "box_2_federal_withholding": "12000.00",
                "box_3_ss_wages": "80000.00",
                "box_4_ss_tax_withheld": "4960.00",
                "box_5_medicare_wages": "80000.00",
                "box_6_medicare_tax_withheld": "1160.00",
            }
        ]
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            r = await client.post("/audit/w2-reconciliation", json=payload)
        assert r.status_code == 200, r.text
        body = r.json()
        W2ReconciliationResponse.model_validate(body)
        assert body["w3_totals"]["total_federal_wages"] == "79000.00"
        assert all(isinstance(x["difference"], str) for x in body["employee_discrepancies"])
        assert body["employee_discrepancies"], "the box 1 difference should be reported"
