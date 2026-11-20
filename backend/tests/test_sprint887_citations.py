"""Sprint 887 / 12J-12K (review OUT-31, OUT-32): authoritative references carry the right titles and periods."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

BACKEND = Path(__file__).resolve().parent.parent
LANG = BACKEND / "shared" / "authoritative_language"


def _refs(file: str, domain: str) -> list[dict]:
    data = yaml.safe_load((LANG / file).read_text(encoding="utf-8"))
    tools = data.get("tools", data)
    return tools[domain]["references"]


def _paragraphs(spec: str) -> set[int]:
    """'25-1 through 25-5, 25-13' -> {1, 2, 3, 4, 5, 13} (the paragraph numbers after the section)."""
    out: set[int] = set()
    for part in spec.split(","):
        m = re.search(r"\d+-(\d+)(?:\s+through\s+\d+-(\d+))?", part)
        if m:
            lo = int(m.group(1))
            out.update(range(lo, int(m.group(2) or lo) + 1))
    return out


class TestRevenueReferences:
    """12J: ASC 606-10-32 is Measurement (contract costs are ASC 340-40)."""

    def test_606_10_32_is_measurement(self):
        ref = next(
            r for r in _refs("fasb_scope_methodology.yml", "revenue_testing") if r["codification"] == "ASC 606-10-32"
        )
        assert ref["topic"] == "Revenue from Contracts with Customers — Measurement"

    def test_every_paragraph_the_revenue_procedures_cite_is_listed(self):
        cited: set[tuple[str, int]] = set()
        for path in [
            BACKEND / "services" / "audit" / "revenue_testing" / "analysis.py",
            BACKEND / "revenue_testing_memo_generator.py",
            BACKEND / "shared" / "follow_up_procedures.py",
        ]:
            for section, para in re.findall(r"ASC 606-10-(\d+)-(\d+)", path.read_text(encoding="utf-8")):
                cited.add((section, int(para)))
        assert cited, "the revenue procedures cite ASC 606 paragraphs"
        listed = {
            r["codification"].rsplit("-", 1)[1]: _paragraphs(r["paragraph"])
            for r in _refs("fasb_scope_methodology.yml", "revenue_testing")
            if r["codification"].startswith("ASC 606-10-")
        }
        missing = sorted(f"606-10-{s}-{p}" for s, p in cited if p not in listed.get(s, set()))
        assert not missing, missing


class TestCompensatedAbsences:
    """12K: GASB Statement 101 replaced Statement 16 for fiscal years beginning after December 15, 2023."""

    def _payroll(self) -> dict[str, dict]:
        return {r["statement"]: r for r in _refs("gasb_scope_methodology.yml", "payroll_testing")}

    def test_statement_101_cited_for_the_periods_it_applies_to(self):
        ref = self._payroll()["Statement No. 101"]
        assert ref["topic"] == "Compensated Absences"
        assert "fiscal years beginning after December 15, 2023" in ref["status"]

    def test_statement_16_cited_only_for_earlier_periods(self):
        ref = self._payroll()["Statement No. 16"]
        assert ref["status"] != "Current"
        assert "Superseded by Statement No. 101" in ref["status"]
        assert "on or before December 15, 2023" in ref["status"]

    def test_gasb_payroll_memo_prints_both_with_their_periods(self):
        import io

        from pypdf import PdfReader

        from payroll_testing_memo_generator import generate_payroll_testing_memo
        from shared.framework_resolution import ResolvedFramework

        pdf = generate_payroll_testing_memo(
            {"composite_score": {"score": 0.0, "risk_tier": "low"}, "test_results": [], "data_quality": {}},
            filename="p",
            resolved_framework=ResolvedFramework.GASB,
        )
        text = " ".join(" ".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(pdf)).pages).split())
        assert "Statement No. 101" in text and "Statement No. 16" in text
        assert "Superseded by Statement No. 101" in text
