"""Sprint 898 (council 2026-11-25, Accounting Expert): methodology defects in CPA-facing output.

A-F7: the 97% Poisson row was not from the AICPA guide and understated the upper
error limit. It is now computed exactly; the same computation must reproduce the
guide's published rows, or the 3% row cannot be trusted either.

A-F2: the debt-to-equity covenant test could not flag negative equity.
"""

from __future__ import annotations

import math
from decimal import ROUND_CEILING, Decimal

import pytest

from going_concern_engine import CovenantThresholds, _test_covenant_breach
from shared.audit_figure_registry import POISSON_RELIABILITY_FACTORS


def _upper_limit(k: int, risk: float) -> float:
    """Smallest λ with P(X <= k; λ) <= risk (bisection), rounded up to cents."""
    lo, hi = 0.0, 100.0
    for _ in range(300):
        mid = (lo + hi) / 2
        cdf = sum(math.exp(-mid) * mid**i / math.factorial(i) for i in range(k + 1))
        lo, hi = (mid, hi) if cdf > risk else (lo, mid)
    return float(Decimal(str(hi)).quantize(Decimal("0.01"), rounding=ROUND_CEILING))


@pytest.mark.parametrize("risk", [0.05, 0.10])
def test_the_computation_reproduces_the_guides_published_rows(risk):
    published = POISSON_RELIABILITY_FACTORS[risk].values
    assert tuple(_upper_limit(k, risk) for k in range(len(published))) == published


def test_the_3_percent_row_is_the_exact_computation_and_says_so():
    row = POISSON_RELIABILITY_FACTORS[0.03]
    assert row.values == tuple(_upper_limit(k, 0.03) for k in range(len(row.values)))
    assert row.values[3] == 8.51  # the old row said 8.39 — understated
    assert "Computed (not from the AICPA guide)" in row.source


def _breach(total_liabilities: float, total_equity: float, ceiling: float = 3.0):
    return _test_covenant_breach(
        current_assets=100.0,
        current_liabilities=50.0,
        total_liabilities=total_liabilities,
        total_equity=total_equity,
        operating_income=None,
        interest_expense=None,
        thresholds=CovenantThresholds(max_debt_to_equity=ceiling),
    )


def test_negative_equity_breaches_a_debt_to_equity_covenant():
    indicator = _breach(total_liabilities=700_000.0, total_equity=-200_000.0)
    assert indicator.triggered
    assert "debt-to-equity undefined" in indicator.description


def test_zero_equity_with_liabilities_breaches():
    assert _breach(total_liabilities=10.0, total_equity=0.0).triggered


def test_ordinary_leverage_still_compared_with_the_ceiling():
    assert _breach(total_liabilities=400.0, total_equity=100.0).triggered  # 4.0 > 3.0
    assert not _breach(total_liabilities=200.0, total_equity=100.0).triggered  # 2.0


# ---------------------------------------------------------------------------
# A-F1: MUS credit balances are disclosed, not silently skipped
# ---------------------------------------------------------------------------


def _population(credits: int) -> bytes:
    lines = ["ID,Description,Amount"]
    for i in range(1, 51):
        lines.append(f"{i},Item {i},{i * 100}")
    for j in range(credits):
        lines.append(f"C{j},Credit {j},-{(j + 1) * 250}")
    return "\n".join(lines).encode("utf-8")


def _design(credits: int):
    from sampling_engine import SamplingConfig, design_sample

    config = SamplingConfig(method="mus", confidence_level=0.95, tolerable_misstatement=10_000)
    return design_sample(_population(credits), "population.csv", config)


def test_mus_reports_the_credit_balances_it_could_not_select():
    result = _design(credits=3)
    assert result.mus_negative_excluded_count == 3
    assert result.mus_negative_excluded_value == 250 + 500 + 750
    assert not any(float(s.item.recorded_amount) < 0 for s in result.selected_items)


def test_no_credits_reports_zero():
    result = _design(credits=0)
    assert (result.mus_negative_excluded_count, result.mus_negative_excluded_value) == (0, 0.0)


def test_memo_discloses_the_excluded_credits():
    from io import BytesIO

    from pypdf import PdfReader

    from routes.sampling import _run_design
    from sampling_memo_generator import generate_sampling_design_memo

    design = _run_design(_population(3), "population.csv", "mus", 0.95, 10_000, 0, None, None, None)
    assert design["mus_negative_excluded_count"] == 3
    pdf = generate_sampling_design_memo(design)
    text = " ".join(page.extract_text() or "" for page in PdfReader(BytesIO(pdf)).pages)
    text = " ".join(text.split())
    assert "Credit Balances Not Covered by the Selection" in text
    assert "3 items with credit balances totalling $1,500.00" in text


def test_the_memo_export_input_keeps_the_disclosure_fields():
    """PR #339 review: the export schema dropped undeclared fields before the generator saw them."""
    from routes.sampling import _run_design
    from shared.export_schemas import SamplingDesignMemoInput

    design = _run_design(_population(3), "population.csv", "mus", 0.95, 10_000, 0, None, None, None)
    dumped = SamplingDesignMemoInput(**design).model_dump()
    assert dumped["mus_negative_excluded_count"] == 3
    assert dumped["mus_negative_excluded_value"] == 1500.0


def test_the_evaluation_memo_carries_the_disclosure_from_its_design_context():
    from io import BytesIO

    from pypdf import PdfReader

    from routes.sampling import _run_design
    from sampling_memo_generator import generate_sampling_evaluation_memo

    design = _run_design(_population(3), "population.csv", "mus", 0.95, 10_000, 0, None, None, None)
    evaluation = {
        "method": "mus",
        "confidence_level": 0.95,
        "tolerable_misstatement": 10_000,
        "expected_misstatement": 0,
        "population_value": design["population_value"],
        "sample_size": design["actual_sample_size"],
        "sample_value": 0,
        "errors_found": 0,
        "total_misstatement": 0,
        "projected_misstatement": 0,
        "basic_precision": 0,
        "incremental_allowance": 0,
        "upper_error_limit": 0,
        "conclusion": "pass",
        "conclusion_detail": "",
        "errors": [],
        "taintings_ranked": [],
    }
    pdf = generate_sampling_evaluation_memo(evaluation, design_result=design)
    text = " ".join(" ".join((p.extract_text() or "") for p in PdfReader(BytesIO(pdf)).pages).split())
    assert "Credit Balances Not Covered by the Selection" in text
