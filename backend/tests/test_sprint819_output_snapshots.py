"""Sprint 819: output snapshots for the backend-deduplication refactors.

Sprint 819 consolidates code that every testing tool, the promoted JSON tools and
the export endpoints duplicated. Its hard rule is that **the JSON/API output must
not change**. These snapshots were captured on the code *before* the refactors
and must stay byte-identical across them.

Each case runs an engine on seeded synthetic data (deterministic: fixed seed,
fixed dates, frozen clock) and compares ``json.dumps(result.to_dict())`` — key
order included — against ``tests/snapshots/sprint819/<case>.json``.

Regenerate only when a change to the output is intended::

    SPRINT819_UPDATE_SNAPSHOTS=1 pytest tests/test_sprint819_output_snapshots.py
"""

from __future__ import annotations

import json
import os
import random
from collections.abc import Callable
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest
from freezegun import freeze_time

SNAPSHOT_DIR = Path(__file__).parent / "snapshots" / "sprint819"
UPDATE = os.environ.get("SPRINT819_UPDATE_SNAPSHOTS") == "1"
FROZEN_NOW = "2026-06-30 12:00:00"

_VENDORS = ["Acme Corp", "Acme Corporation", "Beta LLC", "Gamma Supply", "Delta Services", "Epsilon Ltd", "Zeta Inc"]
_USERS = ["jsmith", "mjones", "admin", "akim", "system"]
_DATE_STYLES = ["%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d", "%d-%b-%Y", "%Y-%m-%d %H:%M:%S"]


def _amount(rng: random.Random) -> str:
    roll = rng.random()
    if roll < 0.08:
        return f"{rng.choice([10000, 20000, 25000, 50000, 100000, 150000, 250000]):.2f}"
    if roll < 0.12:
        return f"{rng.choice([9999.0, 4999.5, 2499.99]):.2f}"
    if roll < 0.15:
        return f"{rng.uniform(200000, 900000):.2f}"
    return f"{rng.lognormvariate(7, 1.2):.2f}"


def _day(rng: random.Random, start: date = date(2025, 1, 1), span: int = 365) -> date:
    return start + timedelta(days=rng.randrange(span))


def _fmt(rng: random.Random, d: date) -> str:
    return d.strftime(rng.choice(_DATE_STYLES))


# =============================================================================
# Testing-tool datasets
# =============================================================================


def _je_case() -> dict:
    from je_testing_engine import run_je_testing

    rng = random.Random(8191)
    cols = [
        "Entry ID",
        "Entry Date",
        "Posting Date",
        "Account",
        "Debit",
        "Credit",
        "Description",
        "Posted By",
        "Source",
    ]
    accounts = ["Cash", "Accounts Receivable", "Revenue", "Inventory", "Accounts Payable", "Suspense", "Misc Expense"]
    rows: list[dict] = []
    for i in range(420):
        amt = _amount(rng)
        d = _day(rng)
        post = d + timedelta(days=rng.choice([0, 0, 0, 1, 45]))
        user = rng.choice(_USERS)
        desc = rng.choice(["Receipt", "Adjustment", "", "Reclass", "Manual entry", "Correction per CFO"])
        a, b = rng.sample(accounts, 2)
        credit = amt if rng.random() > 0.03 else f"{float(amt) - 13:.2f}"
        rows.append(
            {
                "Entry ID": f"JE-{i:04d}",
                "Entry Date": _fmt(rng, d),
                "Posting Date": post.isoformat(),
                "Account": a,
                "Debit": amt,
                "Credit": "0",
                "Description": desc,
                "Posted By": user,
                "Source": rng.choice(["GL", "AP", "Manual"]),
            }
        )
        rows.append(
            {
                "Entry ID": f"JE-{i:04d}",
                "Entry Date": _fmt(rng, d),
                "Posting Date": post.isoformat(),
                "Account": b,
                "Debit": "0",
                "Credit": credit,
                "Description": desc,
                "Posted By": user,
                "Source": rng.choice(["GL", "AP", "Manual"]),
            }
        )
    rows.extend([dict(rows[3]), dict(rows[4])])  # exact duplicates
    return run_je_testing(rows, cols).to_dict()


def _ap_case() -> dict:
    from ap_testing_engine import run_ap_testing

    rng = random.Random(8192)
    cols = [
        "Vendor Name",
        "Vendor ID",
        "Invoice Number",
        "Invoice Date",
        "Payment Date",
        "Amount",
        "Check Number",
        "Description",
        "GL Account",
        "Payment Method",
        "PO Number",
    ]
    rows: list[dict] = []
    for i in range(260):
        inv = _day(rng)
        pay = inv + timedelta(days=rng.choice([-5, 0, 15, 30, 30, 45, 90]))
        rows.append(
            {
                "Vendor Name": rng.choice(_VENDORS),
                "Vendor ID": f"V{rng.randrange(1, 9):02d}",
                "Invoice Number": f"INV-{rng.randrange(1000, 1200)}",
                "Invoice Date": _fmt(rng, inv),
                "Payment Date": _fmt(rng, pay),
                "Amount": _amount(rng),
                "Check Number": str(5000 + i + (3 if i > 100 else 0)),
                "Description": rng.choice(["Supplies", "Consulting", "", "Rent", "Misc"]),
                "GL Account": rng.choice(["6000", "6100", "1200", ""]),
                "Payment Method": rng.choice(["Check", "ACH", "Wire"]),
                "PO Number": rng.choice(["", f"PO-{rng.randrange(100, 400)}"]),
            }
        )
    rows.append(dict(rows[10]))
    return run_ap_testing(rows, cols).to_dict()


def _payroll_rows(rng: random.Random) -> tuple[list[str], list[dict]]:
    headers = [
        "Employee Name",
        "Employee ID",
        "Gross Pay",
        "Net Pay",
        "Deductions",
        "Pay Date",
        "Department",
        "Check Number",
        "Pay Type",
        "Hours",
        "Rate",
        "Hire Date",
        "Termination Date",
        "Bank Account",
        "Address",
        "Tax ID",
    ]
    names = [f"Employee {c}{n}" for c in "ABCDEFGH" for n in range(6)] + ["John Smith", "Jon Smith", ""]
    rows: list[dict] = []
    for i in range(300):
        name = rng.choice(names)
        gross = rng.choice(["10000.00", "25000.00", "50000.00", "100000.00"]) if rng.random() < 0.06 else _amount(rng)
        ded = f"{float(gross) * 0.28:.2f}"
        net = f"{float(gross) - float(ded) + (5 if rng.random() < 0.05 else 0):.2f}"
        pay = _day(rng)
        rows.append(
            {
                "Employee Name": name,
                "Employee ID": f"E{sum(map(ord, name)) % 97:03d}" if name else "",
                "Gross Pay": gross if rng.random() > 0.01 else "0",
                "Net Pay": net,
                "Deductions": ded,
                "Pay Date": _fmt(rng, pay),
                "Department": rng.choice(["Engineering", "Sales", "Ops", ""]),
                "Check Number": str(9000 + i),
                "Pay Type": rng.choice(["Regular", "Bonus", "Overtime"]),
                "Hours": f"{rng.choice([80, 80, 86, 120]):.1f}",
                "Rate": f"{rng.uniform(20, 90):.2f}",
                "Hire Date": "2020-01-15",
                "Termination Date": rng.choice(["", "", "", "2025-03-31"]),
                "Bank Account": rng.choice(["111", "222", "333", "444", "111"]),
                "Address": rng.choice(["1 Main St", "2 Oak Ave", "3 Elm Rd"]),
                "Tax ID": rng.choice(["123-45-6789", "987-65-4321", ""]),
            }
        )
    return headers, rows


def _payroll_case() -> dict:
    from payroll_testing_engine import run_payroll_testing

    rng = random.Random(8193)
    headers, rows = _payroll_rows(rng)
    for i, r in enumerate(rows):
        if i % 50 == 0:
            r["Pay Date"] = "2025-07-15"
    return run_payroll_testing(headers, rows, filename="payroll.csv").to_dict()


def _payroll_ghost_case() -> dict:
    """PR-T9 ghost indicators, in-file and against an HR master (Sprint 642)."""
    from payroll_testing_engine import PayrollTestingConfig, run_payroll_testing

    headers = ["Employee Name", "Employee ID", "Gross Pay", "Pay Date", "Department", "Address"]
    rows: list[dict] = []
    months = ["2025-01-15", "2025-02-15", "2025-03-15", "2025-04-15", "2025-05-15", "2025-06-15"]
    for n in range(8):  # regular employees, paid every month
        for d in months:
            rows.append(
                {
                    "Employee Name": f"Regular {n}",
                    "Employee ID": f"R{n}",
                    "Gross Pay": f"{4000 + n * 10}.00",
                    "Pay Date": d,
                    "Department": "Ops",
                    "Address": f"{n} Elm St",
                }
            )
    for d in ("2025-01-15", "2025-06-15"):  # boundary-only, no department
        rows.append(
            {
                "Employee Name": "Edge Case",
                "Employee ID": "G1",
                "Gross Pay": "5000.00",
                "Pay Date": d,
                "Department": "",
                "Address": "1 Exec Way",
            }
        )
    rows.append(
        {
            "Employee Name": "One Shot",
            "Employee ID": "G2",
            "Gross Pay": "9000.00",
            "Pay Date": "2025-03-15",
            "Department": "Ops",
            "Address": "9 Oak",
        }
    )
    rows.append(
        {
            "Employee Name": "Late Leaver",
            "Employee ID": "R7",
            "Gross Pay": "4070.00",
            "Pay Date": "2025-06-30",
            "Department": "Ops",
            "Address": "7 Elm St",
        }
    )
    hr = [
        {
            "Employee ID": f"R{n}",
            "Employee Name": f"Regular {n}",
            "Status": "Active",
            "Termination Date": "",
            "Address": f"{n} Elm St",
            "Title": "Clerk",
        }
        for n in range(8)
    ]
    hr[7]["Termination Date"] = "2025-05-31"
    hr.append(
        {
            "Employee ID": "X1",
            "Employee Name": "Boss",
            "Status": "Active",
            "Termination Date": "",
            "Address": "1 Exec Way",
            "Title": "Chief Executive Officer",
        }
    )
    hr.append(
        {
            "Employee ID": "G1",
            "Employee Name": "Edge Case",
            "Status": "Active",
            "Termination Date": "",
            "Address": "1 Exec Way",
            "Title": "Analyst",
        }
    )

    def fresh() -> list[dict]:
        # The engine releases its input rows (zero-storage), so each run gets a copy.
        return [dict(r) for r in rows]

    return {
        "in_file": run_payroll_testing(headers, fresh(), filename="ghost.csv").to_dict(),
        "hr_master": run_payroll_testing(headers, fresh(), filename="ghost.csv", hr_master_rows=hr).to_dict(),
        "hr_master_min2": run_payroll_testing(
            headers,
            fresh(),
            config=PayrollTestingConfig(ghost_min_indicators=2),
            filename="ghost.csv",
            hr_master_rows=hr,
        ).to_dict(),
        "disabled": run_payroll_testing(headers, fresh(), config=PayrollTestingConfig(enable_ghost=False)).to_dict(),
        "no_dates": run_payroll_testing(headers, [{**r, "Pay Date": ""} for r in fresh()]).to_dict(),
    }


def _revenue_case() -> dict:
    from revenue_testing_engine import run_revenue_testing

    rng = random.Random(8194)
    cols = [
        "Date",
        "Amount",
        "Account Name",
        "Account Number",
        "Description",
        "Entry Type",
        "Reference",
        "Posted By",
        "Contract ID",
        "Performance Obligation ID",
        "Recognition Method",
        "Contract Modification",
        "Allocation Basis",
        "Obligation Satisfaction Date",
    ]
    rows: list[dict] = []
    for i in range(240):
        d = _day(rng)
        amt = _amount(rng)
        if rng.random() < 0.05:
            amt = f"-{amt}"
        rows.append(
            {
                "Date": _fmt(rng, d),
                "Amount": amt,
                "Account Name": rng.choice(["Product Revenue", "Service Revenue", "Sales Returns", "Deferred Revenue"]),
                "Account Number": rng.choice(["4000", "4100", "4900", "2400"]),
                "Description": rng.choice(["Subscription", "License", "", "Manual adjustment", "Year-end true-up"]),
                "Entry Type": rng.choice(["standard", "manual", "adjustment"]),
                "Reference": f"R{i:04d}",
                "Posted By": rng.choice(_USERS),
                "Contract ID": rng.choice(["", f"C-{rng.randrange(1, 15)}"]),
                "Performance Obligation ID": rng.choice(["", "PO1", "PO2"]),
                "Recognition Method": rng.choice(["", "point_in_time", "over_time", "ratably"]),
                "Contract Modification": rng.choice(["", "", "yes"]),
                "Allocation Basis": rng.choice(["", "SSP", "residual"]),
                "Obligation Satisfaction Date": rng.choice(
                    ["", (d + timedelta(days=rng.randrange(-40, 60))).isoformat()]
                ),
            }
        )
    return run_revenue_testing(rows, cols).to_dict()


def _ar_case() -> dict:
    from ar_aging_engine import ARAgingConfig, run_ar_aging

    rng = random.Random(8195)
    tb_cols = ["Account Name", "Account Number", "Debit", "Credit"]
    tb_rows = [
        {"Account Name": "Accounts Receivable - Trade", "Account Number": "1200", "Debit": "412345.67", "Credit": "0"},
        {
            "Account Name": "Allowance for Doubtful Accounts",
            "Account Number": "1210",
            "Debit": "0",
            "Credit": "3000.00",
        },
        {"Account Name": "Sales Revenue", "Account Number": "4000", "Debit": "0", "Credit": "2500000.00"},
        {"Account Name": "Bad Debt Expense", "Account Number": "6500", "Debit": "1500.00", "Credit": "0"},
    ]
    sl_cols = [
        "Customer Name",
        "Customer ID",
        "Invoice Number",
        "Invoice Date",
        "Due Date",
        "Amount",
        "Credit Limit",
    ]
    sl_rows: list[dict] = []
    for i in range(180):
        inv = _day(rng, date(2024, 6, 1), 560)
        due = inv + timedelta(days=30)
        amt = _amount(rng)
        if rng.random() < 0.04:
            amt = f"-{amt}"
        sl_rows.append(
            {
                "Customer Name": rng.choice(_VENDORS),
                "Customer ID": f"C{rng.randrange(1, 9)}",
                "Invoice Number": f"AR-{i:04d}",
                "Invoice Date": _fmt(rng, inv),
                "Due Date": rng.choice([_fmt(rng, due), due.isoformat(), "", "not a date"]),
                "Amount": amt,
                "Credit Limit": rng.choice(["", "50000", "100000"]),
            }
        )
    out: dict[str, Any] = {}
    for label, as_of in (("iso", "2025-12-31"), ("us", "12/31/2025"), ("eu", "31/12/2025")):
        cfg = ARAgingConfig()
        if hasattr(cfg, "as_of_date"):
            cfg.as_of_date = as_of
        out[label] = run_ar_aging(tb_rows, tb_cols, sl_rows, sl_cols, config=cfg).to_dict()
    out["tb_only"] = run_ar_aging(tb_rows[:3], tb_cols).to_dict()
    return out


def _fa_case() -> dict:
    from fixed_asset_testing_engine import run_fixed_asset_testing

    rng = random.Random(8196)
    cols = [
        "Asset ID",
        "Description",
        "Original Cost",
        "Accumulated Depreciation",
        "Acquisition Date",
        "Useful Life",
        "Depreciation Method",
        "Residual Value",
        "Location",
        "Category",
        "Net Book Value",
    ]
    rows: list[dict] = []
    for i in range(140):
        cost = float(_amount(rng)) + 1000
        acq = _day(rng, date(2005, 1, 1), 7400)
        life = rng.choice([3, 5, 7, 10, 39, 40, 0])
        acc = cost * rng.choice([0.1, 0.4, 0.9, 1.0, 1.2])
        rows.append(
            {
                "Asset ID": f"FA-{i:03d}" if i % 37 else "FA-001",
                "Description": rng.choice(["Truck", "Laptop", "Building", "Office Furniture", ""]),
                "Original Cost": round(cost, 2),
                "Accumulated Depreciation": round(acc, 2),
                "Acquisition Date": rng.choice([_fmt(rng, acq), acq.isoformat(), "", "2030-01-01"]),
                "Useful Life": life,
                "Depreciation Method": rng.choice(["Straight-line", "Declining Balance", "", "SL"]),
                "Residual Value": round(cost * rng.choice([0, 0.05, 0.1, 0.6]), 2),
                "Location": rng.choice(["HQ", "Plant", ""]),
                "Category": rng.choice(["Vehicles", "Computer Equipment", "Buildings", "Furniture"]),
                "Net Book Value": round(cost - acc, 2),
            }
        )
    return run_fixed_asset_testing(rows, cols).to_dict()


def _inventory_case() -> dict:
    from inventory_testing_engine import run_inventory_testing

    rng = random.Random(8197)
    cols = [
        "Item ID",
        "Description",
        "Quantity",
        "Unit Cost",
        "Extended Value",
        "Location",
        "Last Movement Date",
        "Category",
        "Selling Price",
    ]
    rows: list[dict] = []
    for i in range(160):
        qty = rng.choice([0, -3, 5, 12, 100, 1000, 25000])
        cost = round(rng.lognormvariate(3, 1), 2)
        ext = qty * cost * rng.choice([1, 1, 1, 1.1])
        rows.append(
            {
                "Item ID": f"IT-{i:03d}" if i % 41 else "IT-000",
                "Description": rng.choice(["Widget", "Gadget", "Bolt", ""]),
                "Quantity": qty,
                "Unit Cost": cost,
                "Extended Value": round(ext, 2),
                "Location": rng.choice(["WH-A", "WH-B", ""]),
                "Last Movement Date": _fmt(rng, _day(rng, date(2024, 1, 1), 900)),
                "Category": rng.choice(["Raw Materials", "Finished Goods", "WIP"]),
                "Selling Price": round(cost * rng.choice([0.7, 1.2, 1.5]), 2),
            }
        )
    return run_inventory_testing(rows, cols).to_dict()


def _three_way_case() -> dict:
    from three_way_match_engine import (
        detect_invoice_columns,
        detect_po_columns,
        detect_receipt_columns,
        parse_invoices,
        parse_purchase_orders,
        parse_receipts,
        run_three_way_match,
    )

    rng = random.Random(8198)
    po_cols = ["PO Number", "Vendor", "Description", "Quantity", "Unit Price", "Total Amount", "Order Date", "Approver"]
    inv_cols = [
        "Invoice Number",
        "PO Number",
        "Vendor",
        "Description",
        "Quantity",
        "Unit Price",
        "Total",
        "Invoice Date",
    ]
    rec_cols = ["Receipt Number", "PO Number", "Vendor", "Description", "Quantity Received", "Receipt Date"]
    pos, invs, recs = [], [], []
    for i in range(90):
        qty = rng.choice([1, 5, 10, 100])
        price = round(rng.uniform(10, 900), 2)
        vendor = rng.choice(_VENDORS)
        desc = rng.choice(["Widgets", "Bolts", "Services", "Paper"])
        po = f"PO-{i:04d}"
        d = _day(rng)
        pos.append(
            {
                "PO Number": po,
                "Vendor": vendor,
                "Description": desc,
                "Quantity": qty,
                "Unit Price": price,
                "Total Amount": round(qty * price, 2),
                "Order Date": d.isoformat(),
                "Approver": rng.choice(_USERS),
            }
        )
        if rng.random() < 0.9:
            iq = qty + rng.choice([0, 0, 0, 1, -1])
            ip = price * rng.choice([1, 1, 1, 1.03, 0.9])
            invs.append(
                {
                    "Invoice Number": f"I-{i:04d}",
                    "PO Number": po if rng.random() < 0.85 else "",
                    "Vendor": vendor if rng.random() < 0.9 else vendor + " Inc",
                    "Description": desc,
                    "Quantity": iq,
                    "Unit Price": round(ip, 2),
                    "Total": round(iq * ip, 2),
                    "Invoice Date": (d + timedelta(days=rng.randrange(0, 40))).isoformat(),
                }
            )
        if rng.random() < 0.85:
            recs.append(
                {
                    "Receipt Number": f"R-{i:04d}",
                    "PO Number": po if rng.random() < 0.9 else "",
                    "Vendor": vendor,
                    "Description": desc,
                    "Quantity Received": qty + rng.choice([0, 0, -1]),
                    "Receipt Date": (d + timedelta(days=rng.randrange(0, 20))).isoformat(),
                }
            )
    from three_way_match_engine import ThreeWayMatchConfig

    po_objs = parse_purchase_orders(pos, detect_po_columns(po_cols))
    inv_objs = parse_invoices(invs, detect_invoice_columns(inv_cols))
    out: dict[str, Any] = {
        "default": run_three_way_match(
            po_objs, inv_objs, parse_receipts(recs, detect_receipt_columns(rec_cols))
        ).to_dict()
    }

    # Receipts linked only through the invoice reference (no PO number on the
    # receipt), multi-line POs sharing a number, and fuzzy matching switched off.
    rec_cols2 = [*rec_cols, "Invoice Ref"]
    recs2 = [
        {**r, "PO Number": "", "Invoice Ref": f"I-{r['Receipt Number'][2:]}"}
        if k % 3 == 0
        else {**r, "Invoice Ref": ""}
        for k, r in enumerate(recs)
    ]
    pos2 = [{**p, "PO Number": "PO-0001"} if k in (2, 3) else p for k, p in enumerate(pos)]
    for label, cfg in (
        ("inv_ref", ThreeWayMatchConfig()),
        ("no_fuzzy", ThreeWayMatchConfig(enable_fuzzy_matching=False)),
    ):
        out[label] = run_three_way_match(
            parse_purchase_orders(pos2, detect_po_columns(po_cols)),
            inv_objs,
            parse_receipts(recs2, detect_receipt_columns(rec_cols2)),
            cfg,
        ).to_dict()
    out["empty"] = run_three_way_match([], [], []).to_dict()
    return out


def _currency_case() -> dict:
    from currency_engine import CurrencyRateTable, RateValidationError, convert_trial_balance, parse_rate_table

    rate_rows = [
        {"effective_date": "2025-12-31", "from_currency": "EUR", "to_currency": "USD", "rate": "1.10"},
        {"effective_date": "06/30/2025", "from_currency": "EUR", "to_currency": "USD", "rate": "1.08"},
        {"effective_date": "2025-12-31", "from_currency": "GBP", "to_currency": "USD", "rate": "1.27"},
        {"effective_date": "2024-12-31", "from_currency": "JPY", "to_currency": "USD", "rate": "0.0067"},
        {"effective_date": "12/31/2025", "from_currency": "CAD", "to_currency": "USD", "rate": "0.74"},
    ]
    rates = parse_rate_table(rate_rows)
    table = CurrencyRateTable(rates=rates, presentation_currency="USD")
    tb = []
    for i, cur in enumerate(["USD", "EUR", "GBP", "JPY", "CAD", "CHF", "", "eur"] * 3):
        tb.append(
            {
                "Account Number": str(1000 + i),
                "Account Name": f"Account {i}",
                "Balance": f"{(i + 1) * 1234.5:.2f}",
                "Currency": cur,
            }
        )
    out: dict[str, Any] = {
        "rates": [r.to_dict() if hasattr(r, "to_dict") else repr(r) for r in rates],
        "conversion": convert_trial_balance(
            tb, table, "Balance", "Currency", "Account Number", "Account Name", date(2025, 12, 31)
        ).to_dict(),
        "conversion_latest": convert_trial_balance(
            tb, table, "Balance", None, "Account Number", "Account Name"
        ).to_dict(),
    }
    # Typed (Excel-like) cells: int account numbers, float / NaN / text amounts,
    # missing currencies, no name column (falls back to "description").
    typed = [
        {"Account Code": 1000 + i, "Description": f"Line {i}", "Amount": amt, "Curr": cur}
        for i, (amt, cur) in enumerate(
            [
                (1500.25, "EUR"),
                (float("nan"), "EUR"),
                ("$1,234.56", "GBP"),
                ("(250.00)", "JPY"),
                (0, None),
                (99.5, None),
                (12, "XYZ"),
                (7, "usd"),
                (3.3, "CHF"),
                (None, "CAD"),
            ]
        )
    ]
    for label, kwargs in {
        "conversion_typed": {"currency_column": "Curr", "target_date": date(2025, 12, 31)},
        "conversion_typed_detect": {},
        "conversion_typed_no_account_cols": {"account_number_column": "nope", "account_name_column": "nope"},
    }.items():
        typed_result = convert_trial_balance(typed, table, "Amount", **kwargs)
        out[label] = typed_result.to_dict()
        out[label + ":rows"] = typed_result.converted_rows
    bad: dict[str, str] = {}
    for label, raw in {
        "eu_slash": "31/12/2025",
        "dotted": "31.12.2025",
        "compact": "20251231",
        "us_dash": "12-31-2025",
        "empty": "",
        "iso_time": "2025-12-31 00:00:00",
        "two_digit": "12/31/25",
    }.items():
        try:
            parse_rate_table([{"effective_date": raw, "from_currency": "EUR", "to_currency": "USD", "rate": "1.1"}])
            bad[label] = "accepted"
        except RateValidationError as exc:
            bad[label] = str(exc)
    out["date_errors"] = bad
    return out


CASES: dict[str, Callable[[], Any]] = {
    "je": _je_case,
    "ap": _ap_case,
    "payroll": _payroll_case,
    "payroll_ghost": _payroll_ghost_case,
    "revenue": _revenue_case,
    "ar_aging": _ar_case,
    "fixed_assets": _fa_case,
    "inventory": _inventory_case,
    "three_way_match": _three_way_case,
    "currency": _currency_case,
}


def _render(obj: Any) -> str:
    return json.dumps(obj, indent=1, default=str, ensure_ascii=False) + "\n"


def check_snapshot(name: str, payload: Any) -> None:
    path = SNAPSHOT_DIR / f"{name}.json"
    rendered = _render(payload)
    if UPDATE or not path.exists():
        if not UPDATE:
            pytest.fail(f"missing snapshot {path.name}; run with SPRINT819_UPDATE_SNAPSHOTS=1")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered, encoding="utf-8", newline="\n")
        return
    expected = path.read_text(encoding="utf-8")
    assert rendered == expected, f"{name}: output changed (snapshot {path.name})"


@pytest.mark.parametrize("name", sorted(CASES))
def test_engine_output_unchanged(name: str) -> None:
    with freeze_time(FROZEN_NOW):
        payload = CASES[name]()
    check_snapshot(name, payload)
