"""Tax year 2026 — Sprint 860, read from primary sources on 2026-11-24.

Every figure was read from an IRS page or document. The excerpt is the sentence
it came from. ssa.gov refused automated reads (HTTP 403), so the Social Security
wage base is quoted from IRS Tax Topic 751, which states the same base; a
reviewer may also check it at https://www.ssa.gov/oact/cola/cbb.html.

Not signed off. A practitioner checks each figure against its source and then
records the sign-off below (``signed_off_by``, ``signed_off_on``). The sources
are final documents, so ``sources_final`` is already true.

Not modelled, as in 2025: the higher SIMPLE limits for employers with 25 or
fewer employees or that elect them (IRC §408(p)(2)(E)(i); $18,100 deferral and
$3,850 age-50 catch-up for 2026 per Notice 2025-67). A SIMPLE plan using them is
checked against the standard figures.
"""

from __future__ import annotations

from decimal import Decimal

from tax_tables._schema import Figure, SignOff, TaxYearTable, ThresholdFigure, W2Figures

TAX_YEAR = 2026

_TT751 = "https://www.irs.gov/taxtopics/tc751"
_N25_67 = "https://www.irs.gov/pub/irs-drop/n-25-67.pdf"
_RP25_19 = "https://www.irs.gov/pub/irs-drop/rp-25-19.pdf"
_P969 = "https://www.irs.gov/publications/p969"
_I1099MEC = "https://www.irs.gov/instructions/i1099mec"
_I1099INT = "https://www.irs.gov/instructions/i1099int"

_NOTICE = "IRS Notice 2025-67"
_THRESHOLD_2000 = (
    "For tax years beginning after 2025, the minimum threshold amount for reporting certain payments ... "
    "increased to $2,000 and may be adjusted for inflation beginning in calendar year 2027."
)

W2 = W2Figures(
    ss_wage_base=Figure(
        Decimal("184500"),
        "SSA 2026 contribution and benefit base, as stated in IRS Tax Topic 751",
        _TT751,
        "For earnings in 2026, this base limit is $184,500.",
    ),
    ss_rate=Figure(
        Decimal("0.062"),
        "IRC §3101(a); IRS Tax Topic 751",
        _TT751,
        "The current tax rate for Social Security is 6.2% for the employer and 6.2% for the employee, or 12.4% total.",
    ),
    medicare_rate=Figure(
        Decimal("0.0145"),
        "IRC §3101(b)(1); IRS Tax Topic 751",
        _TT751,
        "The current rate for Medicare is 1.45% for the employer and 1.45% for the employee, or 2.9% total.",
    ),
    additional_medicare_rate=Figure(
        Decimal("0.009"),
        "IRC §3101(b)(2); IRS Tax Topic 751",
        _TT751,
        "Employers are responsible for withholding the 0.9% Additional Medicare tax",
    ),
    additional_medicare_threshold=Figure(
        Decimal("200000"),
        "IRC §3102(f) (not indexed); IRS Tax Topic 751",
        _TT751,
        "on an individual's wages paid in excess of $200,000",
    ),
    hsa_self_only=Figure(
        Decimal("4400"),
        "IRC §223(b)(2)(A); Rev. Proc. 2025-19",
        _RP25_19,
        "For calendar year 2026, the annual limitation on deductions under § 223(b)(2)(A) for an individual "
        "with self-only coverage under a high deductible health plan is $4,400.",
    ),
    hsa_family=Figure(
        Decimal("8750"),
        "IRC §223(b)(2)(B); Rev. Proc. 2025-19",
        _RP25_19,
        "... § 223(b)(2)(B) for an individual with family coverage under a high deductible health plan is $8,750.",
    ),
    limit_401k_elective=Figure(
        Decimal("24500"),
        f"IRC §402(g); {_NOTICE}",
        _N25_67,
        "... is increased from $23,500 to $24,500.",
    ),
    limit_401k_catchup_50=Figure(
        Decimal("8000"),
        f"IRC §414(v)(2)(B)(i); {_NOTICE}",
        _N25_67,
        "... individuals aged 50 or over is increased from $7,500 to $8,000.",
    ),
    limit_401k_catchup_60_63=Figure(
        Decimal("11250"),
        f"IRC §414(v)(2)(E)(i) (SECURE 2.0 §109); {_NOTICE}",
        _N25_67,
        "... who attain age 60, 61, 62, or 63 in 2026 remains $11,250.",
    ),
    limit_simple_ira=Figure(
        Decimal("17000"),
        f"IRC §408(p)(2)(E); {_NOTICE}",
        _N25_67,
        "... salary reduction contributions under a SIMPLE retirement account or elective contributions under "
        "a SIMPLE 401(k) plan is increased from $16,500 to $17,000.",
    ),
    hsa_catchup_55=Figure(
        Decimal("1000"),
        "IRC §223(b)(3)(B) (statutory, not indexed); IRS Publication 969",
        _P969,
        "If you are an eligible individual who is age 55 or older at the end of your tax year, your "
        "contribution limit is increased by $1,000.",
    ),
    limit_simple_catchup_50=Figure(
        Decimal("4000"),
        f"IRC §414(v)(2)(B)(ii); {_NOTICE}",
        _N25_67,
        "... section 414(v)(2)(B)(ii) ... aged 50 or over is increased from $3,500 to $4,000.",
    ),
    limit_simple_catchup_60_63=Figure(
        Decimal("5250"),
        f"IRC §414(v)(2)(E)(ii) (SECURE 2.0 §109); {_NOTICE}",
        _N25_67,
        "... section 414(v)(2)(E)(ii) ... age 60, 61, 62, or 63 in 2026 remains $5,250.",
    ),
    catchup_source=(
        "IRC §223(b)(3)(B) (HSA age-55 catch-up, $1,000, statutory); "
        f"IRC §414(v) and {_NOTICE} (SIMPLE catch-up $4,000; age 60-63 $5,250)"
    ),
    source=f"{_NOTICE} (retirement limits); SSA 2026 wage base (IRS Tax Topic 751); Rev. Proc. 2025-19 (HSA)",
    verified_by=(
        "Read from the IRS sources cited per figure on 2026-11-24 (Sprint 860). "
        "Practitioner sign-off: see the tax-year table's sign-off record."
    ),
)

_MEC = "IRS Instructions for Forms 1099-MISC and 1099-NEC"

FORM_1099: tuple[ThresholdFigure, ...] = (
    # The 2026 form numbers the NEC amount box 1a; the threshold is the same.
    ThresholdFigure(
        "1099-NEC",
        1,
        "Nonemployee compensation",
        Figure(
            Decimal("2000"),
            f"IRC §6041A as amended by the One Big Beautiful Bill Act (2025); {_MEC}",
            _I1099MEC,
            "Enter nonemployee compensation (NEC) of $2,000 or more.",
        ),
    ),
    ThresholdFigure(
        "1099-MISC",
        1,
        "Rents",
        Figure(Decimal("2000"), f"IRC §6041 as amended (2025); {_MEC}", _I1099MEC, _THRESHOLD_2000),
    ),
    ThresholdFigure(
        "1099-MISC",
        2,
        "Royalties",
        Figure(Decimal("10"), f"IRC §6050N; {_MEC}", _I1099MEC, "At least $10 in royalties"),
    ),
    ThresholdFigure(
        "1099-MISC",
        3,
        "Other income",
        Figure(Decimal("2000"), f"IRC §6041 as amended (2025); {_MEC}", _I1099MEC, _THRESHOLD_2000),
    ),
    ThresholdFigure(
        "1099-MISC",
        6,
        "Medical and health care payments",
        Figure(Decimal("2000"), f"IRC §6041 as amended (2025); {_MEC}", _I1099MEC, _THRESHOLD_2000),
    ),
    # Unchanged at $600: gross proceeds (box 10) are not among the payments the
    # 2025 change raised. Attorney *fees* are nonemployee compensation (NEC, $2,000).
    ThresholdFigure(
        "1099-MISC",
        10,
        "Gross proceeds paid to an attorney",
        Figure(
            Decimal("600"),
            f"IRC §6045(f); {_MEC}",
            _I1099MEC,
            "At least $600 in gross proceeds paid to an attorney",
        ),
    ),
    ThresholdFigure(
        "1099-INT",
        1,
        "Interest income",
        Figure(
            Decimal("10"),
            "IRC §6049; IRS Instructions for Forms 1099-INT and 1099-OID (Rev. 01/2024)",
            _I1099INT,
            "To whom you paid amounts reportable in boxes 1, 3, or 8 of at least $10",
        ),
    ),
)

TABLE = TaxYearTable(
    tax_year=TAX_YEAR,
    w2=W2,
    form_1099=FORM_1099,
    sign_offs={
        "w2_reconciliation": SignOff(signed_off_by=None, signed_off_on=None, sources_final=True),
        "form_1099": SignOff(signed_off_by=None, signed_off_on=None, sources_final=True),
    },
    acknowledged_large_moves={
        "limit_simple_catchup_50": "Notice 2025-67: increased from $3,500 to $4,000 (14%).",
        "1099-NEC box 1": "One Big Beautiful Bill Act (2025): $600 → $2,000 for payments after 2025.",
        "1099-MISC box 1": "One Big Beautiful Bill Act (2025): $600 → $2,000 for payments after 2025.",
        "1099-MISC box 3": "One Big Beautiful Bill Act (2025): $600 → $2,000 for payments after 2025.",
        "1099-MISC box 6": "One Big Beautiful Bill Act (2025): $600 → $2,000 for payments after 2025.",
    },
)
