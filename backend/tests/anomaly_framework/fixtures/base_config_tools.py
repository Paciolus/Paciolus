"""Clean baselines for the six config-shaped tools (Sprint 823 item 3).

Each factory returns a fresh engine config on which the tool reports nothing
abnormal: no SoD conflict, every intercompany balance reciprocated, W-2 drafts
that tie to payroll and the 941s, 1099 vendors with complete W-9 data, a
book-to-tax run below the M-3 threshold, and a cash position that stays
positive with no deferrable AP. Generators in ``generators/*_generators.py``
inject one departure each.

Figures are small and round so an expected value can be worked by hand.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

# --- Segregation of duties ----------------------------------------------------


def sod_baseline():
    """Four users, each holding one leg of every conflict pair, never two."""
    from sod_engine import RolePermission, UserRoleAssignment

    roles = [
        RolePermission("AP_CLERK", ["ap_invoice_create"]),
        RolePermission("AP_PAYER", ["ap_payment_release"]),
        RolePermission("GL_PREPARER", ["je_create"]),
        RolePermission("GL_APPROVER", ["je_approve"]),
        RolePermission("IT_ADMIN", ["user_admin"]),
    ]
    users = [
        UserRoleAssignment("u1", "Avery Clerk", ["AP_CLERK"]),
        UserRoleAssignment("u2", "Blake Payer", ["AP_PAYER"]),
        UserRoleAssignment("u3", "Casey Preparer", ["GL_PREPARER"]),
        UserRoleAssignment("u4", "Drew Approver", ["GL_APPROVER"]),
        UserRoleAssignment("u5", "Emery Admin", ["IT_ADMIN"]),
    ]
    return {"users": users, "roles": roles}


# --- Intercompany elimination ---------------------------------------------------


def intercompany_baseline():
    """Parent and one subsidiary; a reciprocated balance and fee, both tying."""
    from intercompany_elimination_engine import EntityAccount, EntityTrialBalance, IntercompanyConfig

    parent = EntityTrialBalance(
        "P",
        "Parent Co",
        [
            EntityAccount("Cash", debit=Decimal("250000")),
            EntityAccount("Due from Sub", debit=Decimal("50000"), counterparty_entity="S"),
            EntityAccount("Management fee revenue", credit=Decimal("120000"), counterparty_entity="S"),
            EntityAccount("Retained earnings", credit=Decimal("180000")),
        ],
    )
    sub = EntityTrialBalance(
        "S",
        "Sub Co",
        [
            EntityAccount("Cash", debit=Decimal("10000")),
            EntityAccount("Due to Parent", credit=Decimal("50000"), counterparty_entity="P"),
            EntityAccount("Management fee expense", debit=Decimal("120000"), counterparty_entity="P"),
            EntityAccount("Retained earnings", credit=Decimal("80000")),
        ],
    )
    return IntercompanyConfig(entities=[parent, sub])


# --- W-2 / W-3 reconciliation ---------------------------------------------------

# Two employees; every W-2 box equals payroll, withholding at the statutory
# 6.2% / 1.45%, contributions under every limit, and four 941s that sum to it.
_W2_EMPLOYEES = (
    # id, name, age, wages, federal withholding, hsa, 401k
    ("E1", "Jordan Lee", 41, Decimal("80000"), Decimal("9000"), Decimal("2000"), Decimal("6000")),
    ("E2", "Morgan Diaz", 35, Decimal("60000"), Decimal("6000"), Decimal("0"), Decimal("3000")),
)


def w2_baseline():
    from w2_reconciliation_engine import (
        DEFAULT_STATUTORY_YEAR,
        EmployeePayroll,
        EmployeeW2Draft,
        Form941Quarter,
        HsaCoverage,
        W2ReconciliationConfig,
    )

    employees, drafts = [], []
    for emp_id, name, age, wages, fwh, hsa, k401 in _W2_EMPLOYEES:
        ss_tax = (wages * Decimal("0.062")).quantize(Decimal("0.01"))
        med_tax = (wages * Decimal("0.0145")).quantize(Decimal("0.01"))
        employees.append(
            EmployeePayroll(
                employee_id=emp_id,
                employee_name=name,
                age=age,
                federal_wages=wages,
                federal_withholding=fwh,
                ss_wages=wages,
                ss_tax_withheld=ss_tax,
                medicare_wages=wages,
                medicare_tax_withheld=med_tax,
                hsa_contributions=hsa,
                hsa_coverage=HsaCoverage.SELF_ONLY if hsa else HsaCoverage.NONE,
                retirement_401k=k401,
                retirement_plan_type="401k",
            )
        )
        drafts.append(
            EmployeeW2Draft(
                employee_id=emp_id,
                box_1_federal_wages=wages,
                box_2_federal_withholding=fwh,
                box_3_ss_wages=wages,
                box_4_ss_tax_withheld=ss_tax,
                box_5_medicare_wages=wages,
                box_6_medicare_tax_withheld=med_tax,
                box_12_code_w_hsa=hsa,
                box_12_code_d_401k=k401,
            )
        )
    total_wages = sum((e[3] for e in _W2_EMPLOYEES), Decimal("0"))
    total_fwh = sum((e[4] for e in _W2_EMPLOYEES), Decimal("0"))
    quarters = [
        Form941Quarter(
            quarter=q,
            total_federal_wages=total_wages / 4,
            total_federal_withholding=total_fwh / 4,
            total_ss_wages=total_wages / 4,
            total_medicare_wages=total_wages / 4,
        )
        for q in (1, 2, 3, 4)
    ]
    return W2ReconciliationConfig(
        tax_year=DEFAULT_STATUTORY_YEAR, employees=employees, w2_drafts=drafts, form_941_quarters=quarters
    )


# --- Form 1099 preparation ------------------------------------------------------

# The 2025 table ($600 NEC/MISC, $10 royalties/interest) — the year whose
# figures are not the subject of the 2026 change.
FORM_1099_TAX_YEAR = 2025


def form_1099_baseline():
    from form_1099_engine import (
        EntityType,
        Form1099Config,
        PaymentCategory,
        PaymentMethod,
        VendorPayment,
        VendorRecord,
    )

    def vendor(vid, name, tin, entity):
        return VendorRecord(vid, name, tin, entity, "1 Main St", "Springfield", "IL", "62701")

    vendors = [
        vendor("V1", "Riley Consulting", "123-45-6789", EntityType.INDIVIDUAL),
        vendor("V2", "Harbor Design Partners", "45-6789012", EntityType.PARTNERSHIP),
        vendor("V3", "Northwind Supply Inc", "98-7654321", EntityType.CORPORATION),
    ]
    payments = [
        VendorPayment("V1", Decimal("2500"), PaymentCategory.NONEMPLOYEE_COMP, PaymentMethod.CHECK),
        VendorPayment("V1", Decimal("2500"), PaymentCategory.NONEMPLOYEE_COMP, PaymentMethod.ACH),
        VendorPayment("V2", Decimal("8000"), PaymentCategory.NONEMPLOYEE_COMP, PaymentMethod.CHECK),
        # A corporation paid for services is exempt: never a candidate.
        VendorPayment("V3", Decimal("40000"), PaymentCategory.NONEMPLOYEE_COMP, PaymentMethod.CHECK),
    ]
    return Form1099Config(tax_year=FORM_1099_TAX_YEAR, vendors=vendors, payments=payments)


# --- Book-to-tax reconciliation -------------------------------------------------

BTT_PRETAX_INCOME = Decimal("1000000")
BTT_RATE = Decimal("0.21")
BTT_TOTAL_ASSETS = Decimal("4000000")  # below the $10M Schedule M-3 trigger


def book_to_tax_baseline():
    from book_to_tax_engine import (
        AdjustmentDirection,
        AdjustmentEntry,
        BookToTaxConfig,
        DifferenceType,
    )

    return BookToTaxConfig(
        tax_year=2025,
        book_pretax_income=BTT_PRETAX_INCOME,
        total_assets=BTT_TOTAL_ASSETS,
        federal_tax_rate=BTT_RATE,
        adjustments=[
            AdjustmentEntry(
                "Meals — 50% disallowance",
                Decimal("20000"),
                DifferenceType.PERMANENT,
                AdjustmentDirection.ADD,
                code="meals_50pct",
            ),
        ],
    )


# --- Cash flow projector --------------------------------------------------------


def cash_flow_baseline():
    """Ample cash, AR and AP all current, one monthly payroll well covered."""
    from cash_flow_projector_engine import AgingBuckets, CashFlowConfig, RecurringFlow

    # Relative to today: the engine never reads the clock, but fixture dates are
    # never hardcoded in this repo (the inventory wall-clock time-bomb lesson).
    start = date.today()
    return CashFlowConfig(
        opening_balance=Decimal("500000"),
        start_date=start,
        ar_aging=AgingBuckets(current=Decimal("200000")),
        ap_aging=AgingBuckets(current=Decimal("100000")),
        recurring_flows=[
            RecurringFlow("Payroll", Decimal("-60000"), "monthly", start + timedelta(days=14)),
        ],
        min_safe_cash=Decimal("100000"),
    )
