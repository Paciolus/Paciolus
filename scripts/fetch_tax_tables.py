#!/usr/bin/env python3
"""Fetch a tax year's statutory figures from their IRS sources — Sprint 860.

Reads the published documents, extracts each figure with the sentence it came
from, and compares the result with ``backend/tax_tables/ty<year>.py`` (if it
exists) and the prior year's table. It proposes; it never writes a table: a
person copies the figures into the year's file and a practitioner signs off
(``docs/runbooks/annual-tax-tables.md``).

It never guesses. A figure that cannot be read cleanly is reported as missing,
naming the document, and the script exits 1.

Sources:
* IRS Tax Topic 751 — Social Security wage base, SS / Medicare / Additional
  Medicare rates and threshold. (ssa.gov refuses automated reads.)
* the IRS retirement-limits notice for the year (``--notice-url``; known years
  in ``KNOWN_SOURCES``) — 401(k) and SIMPLE limits and catch-ups.
* the HSA revenue procedure (``--hsa-url``) — HSA self-only and family.
* IRS Instructions for Forms 1099-MISC and 1099-NEC, and 1099-INT — thresholds.

Usage::

    python scripts/fetch_tax_tables.py --year 2027 --notice-url URL --hsa-url URL \
        [--report report.md] [--json out.json]

Exit codes: 0 every figure read and matching any existing table; 1 a figure
could not be read; 2 every figure read, but some differ from the existing table.
"""

from __future__ import annotations

import argparse
import html
import io
import json
import re
import sys
import urllib.request
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))

TT751 = "https://www.irs.gov/taxtopics/tc751"
I1099MEC = "https://www.irs.gov/instructions/i1099mec"
I1099INT = "https://www.irs.gov/instructions/i1099int"

# Per-year documents whose URL changes every year (the notice number is new).
KNOWN_SOURCES: dict[int, dict[str, str]] = {
    2026: {
        "notice": "https://www.irs.gov/pub/irs-drop/n-25-67.pdf",
        "hsa": "https://www.irs.gov/pub/irs-drop/rp-25-19.pdf",
    },
}

_AMOUNT = r"\$(?P<v>[\d,]+(?:\.\d+)?)"
_PERCENT = r"(?P<v>\d+(?:\.\d+)?)%"
_NOTICE_TAIL = r".{0,400}?(?:increased from \$[\d,]+ to|remains) " + _AMOUNT
_SEC = r"(?:section|§)\s*"


@dataclass(frozen=True)
class Spec:
    key: str  # field in W2Figures, or "1099-MISC box 1" etc.
    document: str  # tt751 | notice | hsa | i1099mec | i1099int
    pattern: str  # regex with a ``v`` group; ``{year}`` is substituted
    percent: bool = False


SPECS: tuple[Spec, ...] = (
    Spec("ss_wage_base", "tt751", r"For earnings in {year}, this base limit is " + _AMOUNT),
    Spec("ss_rate", "tt751", r"tax rate for Social Security is " + _PERCENT, percent=True),
    Spec("medicare_rate", "tt751", r"rate for Medicare is " + _PERCENT, percent=True),
    Spec("additional_medicare_rate", "tt751", r"withholding the " + _PERCENT + r" Additional Medicare", percent=True),
    Spec("additional_medicare_threshold", "tt751", r"in excess of " + _AMOUNT + r" in a calendar year"),
    Spec("limit_401k_elective", "notice", _SEC + r"402\(g\)\(1\) on the exclusion" + _NOTICE_TAIL),
    Spec("limit_401k_catchup_50", "notice", _SEC + r"414\(v\)\(2\)\(B\)\(i\) for catch-up" + _NOTICE_TAIL),
    Spec("limit_401k_catchup_60_63", "notice", _SEC + r"414\(v\)\(2\)\(E\)\(i\) for catch-up" + _NOTICE_TAIL),
    Spec("limit_simple_ira", "notice", _SEC + r"408\(p\)\(2\)\(E\)\(i\)\(III\)" + _NOTICE_TAIL),
    Spec(
        "limit_simple_catchup_50",
        "notice",
        _SEC + r"414\(v\)\(2\)\(B\)\(ii\) for catch-up contributions to an applicable employer plan described in "
        r"section 401\(k\)\(11\) or section 408\(p\) that generally applies" + _NOTICE_TAIL,
    ),
    Spec("limit_simple_catchup_60_63", "notice", _SEC + r"414\(v\)\(2\)\(E\)\(ii\) for catch-up" + _NOTICE_TAIL),
    Spec(
        "hsa_self_only",
        "hsa",
        r"For calendar year {year}, the annual limitation on deductions under \W{0,3}\s*223\(b\)\(2\)\(A\)"
        r".{0,120}?is " + _AMOUNT,
    ),
    Spec("hsa_family", "hsa", r"223\(b\)\(2\)\(B\) for an individual with family coverage.{0,80}?is " + _AMOUNT),
    Spec("1099-NEC box 1", "i1099mec", r"Enter nonemployee compensation \(NEC\) of " + _AMOUNT + " or more"),
    Spec("1099-MISC box 1", "i1099mec", r"At least " + _AMOUNT + r" in: Rents"),
    Spec("1099-MISC box 2", "i1099mec", r"At least " + _AMOUNT + r" in royalties"),
    Spec("1099-MISC box 3", "i1099mec", r"At least " + _AMOUNT + r" in: Rents \( box 1 \); [^.]{0,200}?Other income"),
    Spec("1099-MISC box 6", "i1099mec", r"At least " + _AMOUNT + r" in:[^.]{0,800}?[Mm]edical and health care"),
    Spec("1099-MISC box 10", "i1099mec", r"At least " + _AMOUNT + r" in gross proceeds paid to an attorney"),
    Spec("1099-INT box 1", "i1099int", r"reportable in boxes 1, 3, or 8 of at least " + _AMOUNT),
)

# Not published per year: stated in the statute (IRC §223(b)(3)(B)).
STATUTORY = {"hsa_catchup_55": Decimal("1000")}


@dataclass
class Found:
    key: str
    value: str | None
    document: str
    url: str
    excerpt: str
    problem: str = ""


def html_to_text(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw)
    raw = re.sub(r"<[^>]+>", " ", raw)
    return re.sub(r"\s+", " ", html.unescape(raw)).strip()


def pdf_to_text(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return re.sub(r"\s+", " ", " ".join(page.extract_text() or "" for page in reader.pages)).strip()


def fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; tax-table-check)"})
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310 (fixed https URLs)
        data = response.read()
    if url.lower().endswith(".pdf") or data[:4] == b"%PDF":
        return pdf_to_text(data)
    return html_to_text(data.decode("utf-8", errors="replace"))


def _sentence_around(text: str, start: int, end: int) -> str:
    left = text.rfind(". ", 0, start)
    right = text.find(". ", end)
    return text[left + 2 if left >= 0 else max(0, start - 200) : right + 1 if right >= 0 else end + 200].strip()


def _normalise(raw: str, percent: bool) -> str:
    value = Decimal(raw.replace(",", ""))
    if percent:
        value = value / 100
    return format(value.normalize(), "f")


def extract(spec: Spec, text: str, year: int, url: str) -> Found:
    pattern = spec.pattern.replace("{year}", str(year))
    matches = list(re.finditer(pattern, text))
    if not matches:
        return Found(spec.key, None, spec.document, url, "", f"not found in {spec.document} ({url})")
    values = {_normalise(m.group("v"), spec.percent) for m in matches}
    first = matches[0]
    excerpt = _sentence_around(text, first.start(), first.end())
    if len(values) > 1:
        return Found(spec.key, None, spec.document, url, excerpt, f"ambiguous in {spec.document}: {sorted(values)}")
    return Found(spec.key, values.pop(), spec.document, url, excerpt)


def is_draft(text: str) -> bool:
    return bool(re.search(r"\bDRAFT\b|\bdraft as of\b", text[:3000], re.IGNORECASE))


def table_values(year: int) -> dict[str, str] | None:
    import tax_tables

    table = tax_tables.TABLES.get(year)
    if table is None:
        return None
    values: dict[str, str] = {}
    if table.w2 is not None:
        values.update({k: format(f.value.normalize(), "f") for k, f in table.w2.figures().items()})
    for item in table.form_1099 or ():
        values[item.key] = format(item.amount.value.normalize(), "f")
    return values


def run(year: int, sources: dict[str, str | None], texts: dict[str, str] | None = None) -> dict:
    """Read every figure. ``texts`` (document → text) skips the network, for tests."""
    texts = dict(texts or {})
    found: list[Found] = []
    drafts: list[str] = []
    for document in sorted({s.document for s in SPECS}):
        url = sources.get(document)
        if document not in texts:
            if not url:
                texts[document] = ""
                continue
            try:
                texts[document] = fetch_text(url)
            except Exception as exc:  # noqa: BLE001 — reported, never swallowed
                texts[document] = ""
                found.append(Found(f"<{document}>", None, document, url, "", f"could not read {url}: {exc}"))
                continue
        if is_draft(texts[document]):
            drafts.append(document)
    for spec in SPECS:
        url = sources.get(spec.document) or ""
        if not texts.get(spec.document):
            problem = "source not configured — pass its URL" if not url else f"no text from {url}"
            found.append(Found(spec.key, None, spec.document, url, "", problem))
            continue
        found.append(extract(spec, texts[spec.document], year, url))
    for key, value in STATUTORY.items():
        found.append(Found(key, format(value, "f"), "statute", "IRC §223(b)(3)(B)", "statutory, not indexed"))

    existing, prior = table_values(year), table_values(year - 1)
    differs = []
    if existing is not None:
        for f in found:
            if f.value is not None and f.key in existing and Decimal(existing[f.key]) != Decimal(f.value):
                differs.append(f"{f.key}: table {existing[f.key]}, source {f.value}")
    return {
        "year": year,
        "figures": [asdict(f) for f in found],
        "prior": prior or {},
        "existing": existing,
        "missing": [f"{f.key}: {f.problem}" for f in found if f.value is None],
        "differs": differs,
        "draft_documents": drafts,
    }


def report_markdown(result: dict) -> str:
    year = result["year"]
    lines = [f"## Tax year {year}: figures read from the sources", ""]
    if result["missing"]:
        lines += ["**Could not read:**", *[f"- {m}" for m in result["missing"]], ""]
    if result["differs"]:
        lines += [f"**Differs from `ty{year}.py`:**", *[f"- {d}" for d in result["differs"]], ""]
    if result["draft_documents"]:
        lines += [f"**Draft documents** (keep `sources_final=False`): {', '.join(result['draft_documents'])}", ""]
    if result["existing"] is None:
        lines += [f"No `backend/tax_tables/ty{year}.py` yet: these are the proposed figures.", ""]
    lines += ["| Figure | Source value | Prior year | Document | Sentence |", "|---|---|---|---|---|"]
    for f in result["figures"]:
        value = f["value"] if f["value"] is not None else "—"
        prior = result["prior"].get(f["key"], "")
        excerpt = (f["excerpt"] or f["problem"]).replace("|", "\\|")[:300]
        lines.append(f"| `{f['key']}` | {value} | {prior} | [{f['document']}]({f['url']}) | {excerpt} |")
    lines += [
        "",
        "Next: copy into the year's table, run the Sprint 860 tests, and get the practitioner sign-off "
        "(docs/runbooks/annual-tax-tables.md).",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--notice-url")
    parser.add_argument("--hsa-url")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args(argv)

    known = KNOWN_SOURCES.get(args.year, {})
    sources = {
        "tt751": TT751,
        "i1099mec": I1099MEC,
        "i1099int": I1099INT,
        "notice": args.notice_url or known.get("notice"),
        "hsa": args.hsa_url or known.get("hsa"),
    }
    result = run(args.year, sources)
    markdown = report_markdown(result)
    if args.report:
        args.report.write_text(markdown, encoding="utf-8")
    if args.json:
        args.json.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(markdown)
    if result["missing"]:
        return 1
    if result["differs"]:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
