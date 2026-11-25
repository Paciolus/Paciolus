"""Tax year 2025 — Sprint 860 moved these figures here unchanged.

W-2 figures: formerly ``w2_reconciliation_engine.STATUTORY_LIMITS_BY_YEAR[2025]``
(Sprint 811 labelled them 2025; Sprint 826 added the catch-ups). 1099 figures:
formerly ``form_1099_engine._PRE_2026_ITEMS`` (Sprint 837). The 1099 table also
serves every tax year before 2025 — the $600 rules applied for decades.

The excerpts are empty: these figures were carried over, not re-read from the
sources in Sprint 860. The sign-off is where a practitioner confirms them.
"""

from __future__ import annotations

from decimal import Decimal

from tax_tables._schema import Figure, SignOff, TaxYearTable, ThresholdFigure, W2Figures

TAX_YEAR = 2025

_SSA_CBB = "https://www.ssa.gov/oact/cola/cbb.html"
_N24_80 = "https://www.irs.gov/pub/irs-drop/n-24-80.pdf"
_RP24_25 = "https://www.irs.gov/pub/irs-drop/rp-24-25.pdf"
_IRC = "https://www.law.cornell.edu/uscode/text/26"
_I1099MEC = "https://www.irs.gov/instructions/i1099mec"
_I1099INT = "https://www.irs.gov/instructions/i1099int"

W2 = W2Figures(
    ss_wage_base=Figure(Decimal("176100"), "SSA 2025 contribution and benefit base", _SSA_CBB),
    ss_rate=Figure(Decimal("0.062"), "IRC §3101(a)", f"{_IRC}/3101"),
    medicare_rate=Figure(Decimal("0.0145"), "IRC §3101(b)(1)", f"{_IRC}/3101"),
    additional_medicare_rate=Figure(Decimal("0.009"), "IRC §3101(b)(2)", f"{_IRC}/3101"),
    additional_medicare_threshold=Figure(Decimal("200000"), "IRC §3102(f) (not indexed)", f"{_IRC}/3102"),
    hsa_self_only=Figure(Decimal("4300"), "IRC §223(b)(2)(A); Rev. Proc. 2024-25", _RP24_25),
    hsa_family=Figure(Decimal("8550"), "IRC §223(b)(2)(B); Rev. Proc. 2024-25", _RP24_25),
    limit_401k_elective=Figure(Decimal("23500"), "IRC §402(g); IRS Notice 2024-80", _N24_80),
    limit_401k_catchup_50=Figure(Decimal("7500"), "IRC §414(v)(2)(B)(i); IRS Notice 2024-80", _N24_80),
    limit_401k_catchup_60_63=Figure(
        Decimal("11250"), "IRC §414(v)(2)(E)(i) (SECURE 2.0 §109); IRS Notice 2024-80", _N24_80
    ),
    limit_simple_ira=Figure(Decimal("16500"), "IRC §408(p)(2)(E); IRS Notice 2024-80", _N24_80),
    hsa_catchup_55=Figure(Decimal("1000"), "IRC §223(b)(3)(B) (statutory, not indexed)", f"{_IRC}/223"),
    limit_simple_catchup_50=Figure(Decimal("3500"), "IRC §414(v)(2)(B)(ii); IRS Notice 2024-80", _N24_80),
    limit_simple_catchup_60_63=Figure(
        Decimal("5250"), "IRC §414(v)(2)(E)(ii) (SECURE 2.0 §109); IRS Notice 2024-80", _N24_80
    ),
    catchup_source=(
        "IRC §223(b)(3)(B) (HSA age-55 catch-up, $1,000, statutory); "
        "IRC §414(v) and IRS Notice 2024-80 (SIMPLE catch-up $3,500; age 60-63 $5,250)"
    ),
    source="IRS Notice 2024-80 (retirement limits); SSA 2025 wage base; Rev. Proc. 2024-25 (HSA)",
    verified_by=(
        "These are the figures that shipped under a '2026' heading. The 2026-10-22 "
        "full-spectrum review identified them as the 2025 set, which is how they are "
        "now labelled. Not independently re-verified against the notices — Sprint 793b "
        "owns practitioner confirmation of both 2025 and 2026. The three catch-up "
        "figures (Sprint 826) restate IRC §223(b)(3)(B) and IRS Notice 2024-80 and are "
        "on the same 793b confirmation list."
    ),
)

FORM_1099: tuple[ThresholdFigure, ...] = (
    ThresholdFigure("1099-NEC", 1, "Nonemployee compensation", Figure(Decimal("600"), "IRC §6041A(a)", _I1099MEC)),
    ThresholdFigure("1099-MISC", 1, "Rents", Figure(Decimal("600"), "IRC §6041(a)", _I1099MEC)),
    ThresholdFigure("1099-MISC", 2, "Royalties", Figure(Decimal("10"), "IRC §6050N", _I1099MEC)),
    ThresholdFigure("1099-MISC", 3, "Other income", Figure(Decimal("600"), "IRC §6041(a)", _I1099MEC)),
    ThresholdFigure(
        "1099-MISC", 6, "Medical and health care payments", Figure(Decimal("600"), "IRC §6041(a)", _I1099MEC)
    ),
    ThresholdFigure(
        "1099-MISC", 10, "Gross proceeds paid to an attorney", Figure(Decimal("600"), "IRC §6045(f)", _I1099MEC)
    ),
    ThresholdFigure("1099-INT", 1, "Interest income", Figure(Decimal("10"), "IRC §6049", _I1099INT)),
)

TABLE = TaxYearTable(
    tax_year=TAX_YEAR,
    w2=W2,
    form_1099=FORM_1099,
    sign_offs={
        "w2_reconciliation": SignOff(),
        "form_1099": SignOff(),
    },
)
