"""Sprint 860: the tax-table fetcher reads figures with their sentences, never guesses.

Offline: the documents are short passages in the wording the 2026 sources use
(checked live against the IRS pages on 2026-11-24, when every 2026 figure read
matched ``tax_tables/ty2026.py``).
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import fetch_tax_tables as fetch  # noqa: E402  (path manipulation above)

TT751 = (
    "Social Security and Medicare withholding rates The current tax rate for Social Security is 6.2% for the "
    "employer and 6.2% for the employee, or 12.4% total. The current rate for Medicare is 1.45% for the employer "
    "and 1.45% for the employee, or 2.9% total. Employers are responsible for withholding the 0.9% Additional "
    "Medicare tax on an individual's wages paid in excess of $200,000 in a calendar year, without regard to "
    "filing status. For earnings in 2026, this base limit is $184,500. Refer to Publication 15."
)
NOTICE = (
    "The limitation under section 402(g)(1) on the exclusion for elective deferrals described in section "
    "402(g)(3) is increased from $23,500 to $24,500. The limitation under section 414(v)(2)(B)(i) for catch-up "
    "contributions to an applicable employer plan other than a plan described in section 401(k)(11) or section "
    "408(p) that generally applies for individuals aged 50 or over is increased from $7,500 to $8,000. The "
    "limitation under section 414(v)(2)(E)(i) for catch-up contributions to an applicable employer plan other "
    "than a plan described in section 401(k)(11) or section 408(p) that applies for individuals who attain 2 age "
    "60, 61, 62, or 63 in 2026 remains $11,250. The limitation under section 408(p)(2)(E)(i)(III) that generally "
    "applies to salary reduction contributions under a SIMPLE retirement account is increased from $16,500 to "
    "$17,000. The limitation for certain of those accounts under section 408(p)(2)(E)(i)(I) or (II) is increased "
    "from $17,600 to $18,100. The limitation under section 414(v)(2)(B)(ii) for catch-up contributions to an "
    "applicable employer plan described in section 401(k)(11) or section 408(p) that generally applies for "
    "individuals aged 50 or over is increased from $3,500 to $4,000. The limitation under section "
    "414(v)(2)(E)(ii) for catch-up contributions to an applicable employer plan described in section 401(k)(11) "
    "or section 408(p) that applies for individuals who attain age 60, 61, 62, or 63 in 2026 remains $5,250."
)
HSA = (
    "For calendar year 2026, the annual limitation on deductions under § 223(b)(2)(A) for an individual with "
    "self-only coverage under a high - 2 - deductible health plan is $4,400. For calendar year 2026, the annual "
    "limitation on deductions under § 223(b)(2)(B) for an individual with family coverage under a high deductible "
    "health plan is $8,750."
)
MEC = (
    "Enter nonemployee compensation (NEC) of $2,000 or more. At least $10 in royalties (see the instructions for "
    "box 2). At least $2,000 in: Rents ( box 1 ); Prizes and awards ( box 3 ); Other income payments ( box 3 ); "
    "Medical and health care payments ( box 6 ). At least $600 in gross proceeds paid to an attorney ( box 10 )."
)
INT = "To whom you paid amounts reportable in boxes 1, 3, or 8 of at least $10."

TEXTS = {"tt751": TT751, "notice": NOTICE, "hsa": HSA, "i1099mec": MEC, "i1099int": INT}
SOURCES = {doc: f"https://example.test/{doc}" for doc in TEXTS}


def _values(result: dict) -> dict[str, str | None]:
    return {f["key"]: f["value"] for f in result["figures"]}


def test_reads_every_2026_figure_and_matches_the_table():
    result = fetch.run(2026, SOURCES, texts=TEXTS)
    assert result["missing"] == []
    assert result["differs"] == []
    values = _values(result)
    assert values["ss_wage_base"] == "184500"
    assert values["ss_rate"] == "0.062"
    assert values["limit_simple_ira"] == "17000"  # not the $18,100 higher-limit figure
    assert values["limit_simple_catchup_50"] == "4000"
    assert values["1099-MISC box 6"] == "2000"
    assert values["1099-MISC box 10"] == "600"


def test_each_figure_carries_its_sentence():
    result = fetch.run(2026, SOURCES, texts=TEXTS)
    wage = next(f for f in result["figures"] if f["key"] == "ss_wage_base")
    assert wage["excerpt"] == "For earnings in 2026, this base limit is $184,500."


def test_a_figure_it_cannot_read_is_reported_naming_the_document():
    texts = {**TEXTS, "hsa": "This revenue procedure has no figures."}
    result = fetch.run(2026, SOURCES, texts=texts)
    assert any(m.startswith("hsa_self_only: not found in hsa") for m in result["missing"])
    assert fetch.main  # exit code 1 path is `missing`


def test_wrong_year_is_not_read_as_this_year():
    result = fetch.run(2027, SOURCES, texts=TEXTS)
    assert any(m.startswith("ss_wage_base:") for m in result["missing"])


def test_an_unconfigured_source_is_reported_not_skipped():
    sources = {**SOURCES, "notice": None}
    texts = {k: v for k, v in TEXTS.items() if k != "notice"}
    result = fetch.run(2026, sources, texts=texts)
    assert any("limit_401k_elective: source not configured" in m for m in result["missing"])


def test_a_differing_figure_is_reported():
    texts = {**TEXTS, "tt751": TT751.replace("$184,500", "$190,000")}
    result = fetch.run(2026, SOURCES, texts=texts)
    assert result["differs"] == ["ss_wage_base: table 184500, source 190000"]


def test_two_different_values_are_ambiguous_not_picked():
    texts = {**TEXTS, "i1099int": INT + " Elsewhere: reportable in boxes 1, 3, or 8 of at least $600."}
    result = fetch.run(2026, SOURCES, texts=texts)
    assert any(m.startswith("1099-INT box 1: ambiguous") for m in result["missing"])


def test_draft_documents_are_flagged():
    texts = {**TEXTS, "i1099mec": "DRAFT — not for filing. " + MEC}
    assert fetch.run(2026, SOURCES, texts=texts)["draft_documents"] == ["i1099mec"]


def test_report_lists_figures_with_prior_year():
    markdown = fetch.report_markdown(fetch.run(2026, SOURCES, texts=TEXTS))
    assert "| `ss_wage_base` | 184500 | 176100 |" in markdown
