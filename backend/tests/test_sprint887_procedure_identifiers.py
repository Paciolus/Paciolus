"""Sprint 887 / 12D (review OUT-17): each flag keeps its test and its suggested procedure.

The memo guessed a flag's test from the words in its text, so an employee named
"Benford Law Gross Pay" moved a PR-T12 flag to PR-T8. The library was keyed by
names the engines do not emit (JE emits ``round_amounts``, the library had
``round_dollar_amounts``) and shared keys across tools (AP's round-dollar test
got JE's text). PR-T12 and PR-T13 had no entry. Selection used ``hash()``,
which changes between processes, plus the flag's position.

Now each flag carries its tool and test identifiers (and payroll flags the
employee), the library is keyed by (tool, test), and the choice depends only on
those identifiers and the client.
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from shared.follow_up_procedures import PROCEDURES, get_follow_up_procedure

BACKEND = Path(__file__).resolve().parent.parent


def _pdf_text(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    return " ".join(" ".join((p.extract_text() or "") for p in reader.pages).split())


def _key_items(text: str) -> str:
    return text.split("Key Items Flagged", 1)[1].split("Authoritative References", 1)[0]


class TestLibraryKeyedByEngineIdentifiers:
    def test_je_round_amounts_has_its_procedure(self):
        assert get_follow_up_procedure("journal_entry_testing", "round_amounts")

    def test_ap_round_dollar_is_aps_own_text(self):
        ap = get_follow_up_procedure("ap_testing", "round_dollar_amounts")
        assert ap and ap not in PROCEDURES["journal_entry_testing"].get("round_amounts", ())

    @pytest.mark.parametrize("tool", ["fixed_asset_testing", "inventory_testing"])
    def test_missing_fields_is_per_tool(self, tool):
        text = get_follow_up_procedure(tool, "missing_fields")
        assert text and text not in PROCEDURES["journal_entry_testing"]["missing_fields"]

    @pytest.mark.parametrize("key", ["PR-T12", "PR-T13"])
    def test_payroll_t12_t13_have_entries(self, key):
        assert get_follow_up_procedure("payroll_testing", key)

    def test_unknown_test_has_no_procedure(self):
        assert get_follow_up_procedure("ap_testing", "missing_fields") == ""

    def test_engine_keys_match_the_library(self):
        """Every library key under a testing tool is one its engine emits."""
        import re

        services = BACKEND / "services" / "audit"
        for tool, folder in {
            "journal_entry_testing": "je_testing",
            "ap_testing": "ap_testing",
            "payroll_testing": "payroll_testing",
            "revenue_testing": "revenue_testing",
            "ar_aging": "ar_aging",
            "fixed_asset_testing": "fixed_asset_testing",
            "inventory_testing": "inventory_testing",
        }.items():
            source = "".join(p.read_text(encoding="utf-8") for p in (services / folder).glob("*.py"))
            emitted = set(re.findall(r'test_key="([A-Za-z0-9_-]+)"', source))
            assert set(PROCEDURES[tool]) <= emitted, (tool, set(PROCEDURES[tool]) - emitted)


def _payroll_result(order: list[str], names: dict[str, str]) -> dict:
    """Two flags: PR-T12 on an employee named like a Benford test, PR-T8 on another."""
    tests = {
        "PR-T8": {"test_name": "Benford's Law on Gross Pay", "test_key": "PR-T8"},
        "PR-T12": {"test_name": "Duplicate Employee Names", "test_key": "PR-T12"},
    }
    flags = {
        "PR-T12": {
            "employee": names["PR-T12"],
            "employee_id": "E-12",
            "test": "Duplicate Employee Names",
            "test_key": "PR-T12",
            "tool": "payroll_testing",
            "issue": "Name shared by two employee IDs",
            "severity": "high",
            "amount": 1000.0,
        },
        "PR-T8": {
            "employee": names["PR-T8"],
            "employee_id": "E-8",
            "test": "Benford's Law on Gross Pay",
            "test_key": "PR-T8",
            "tool": "payroll_testing",
            "issue": "First-digit distribution deviation",
            "severity": "medium",
            "amount": 2000.0,
        },
    }
    test_results = [
        {
            **tests[k],
            "test_tier": "statistical",
            "entries_flagged": 1,
            "total_entries": 50,
            "flag_rate": 0.02,
            "severity": "medium",
            "description": "",
            "flagged_entries": [],
        }
        for k in order
    ]
    return {
        "composite_score": {
            "score": 4.0,
            "risk_tier": "low",
            "tests_run": 2,
            "total_entries": 50,
            "total_flagged": 2,
            "flag_rate": 0.04,
            "flags_by_severity": {"high": 1, "medium": 1, "low": 0},
            "top_findings": [flags[k] for k in order],
        },
        "test_results": test_results,
        "data_quality": {"completeness_score": 100.0, "total_rows": 50},
    }


def _procedure_after(items: str, marker: str) -> str:
    """The suggested follow-up printed for the flag whose text contains ``marker``."""
    tail = items.split(marker, 1)[1]
    return tail.split("Suggested follow-up:", 1)[1].split(".", 1)[0].strip()


class TestFlagsKeepTheirProcedure:
    def _items(self, order: list[str], names: dict[str, str], client: str = "Client A") -> str:
        from payroll_testing_memo_generator import generate_payroll_testing_memo

        pdf = generate_payroll_testing_memo(_payroll_result(order, names), filename="p", client_name=client)
        return _key_items(_pdf_text(pdf))

    def test_benford_named_employee_keeps_pr_t12(self):
        items = self._items(["PR-T12", "PR-T8"], {"PR-T12": "Benford Law Gross Pay", "PR-T8": "Ann Lee"})
        t12 = _procedure_after(items, "Benford Law Gross Pay")
        assert t12 in get_follow_up_procedure("payroll_testing", "PR-T12", seed="Client A")
        assert t12 not in get_follow_up_procedure("payroll_testing", "PR-T8", seed="Client A")

    def test_reordering_and_renaming_keep_each_procedure(self):
        a = self._items(["PR-T12", "PR-T8"], {"PR-T12": "Benford Law Gross Pay", "PR-T8": "Ann Lee"})
        b = self._items(["PR-T8", "PR-T12"], {"PR-T12": "Zed Moss", "PR-T8": "Duplicate Names Vendor"})
        assert _procedure_after(a, "Benford Law Gross Pay") == _procedure_after(b, "Zed Moss")
        assert _procedure_after(a, "Ann Lee") == _procedure_after(b, "Duplicate Names Vendor")

    def test_string_flag_without_identifiers_gets_no_guessed_procedure(self):
        """A legacy text-only flag prints as text; nothing is inferred from its words."""
        from je_testing_memo_generator import generate_je_testing_memo

        result = _payroll_result(["PR-T8"], {"PR-T8": "x", "PR-T12": "y"})
        result["composite_score"]["top_findings"] = ["Benford's Law: 3 entries flagged (1.0%)"]
        items = _key_items(_pdf_text(generate_je_testing_memo(result, filename="j", client_name="Client A")))
        assert "Benford's Law: 3 entries flagged" in items
        assert "Suggested follow-up" not in items


_SUBPROCESS = """
import io, json, sys
sys.path.insert(0, {backend!r})
from tests.test_sprint887_procedure_identifiers import _payroll_result, _pdf_text, _key_items
from payroll_testing_memo_generator import generate_payroll_testing_memo
from je_testing_memo_generator import generate_je_testing_memo
r = _payroll_result(["PR-T12", "PR-T8"], {{"PR-T12": "Benford Law Gross Pay", "PR-T8": "Ann Lee"}})
je = {{
    "composite_score": {{"score": 20.0, "risk_tier": "moderate", "total_flagged": 6,
        "flags_by_severity": {{"high": 2, "medium": 2, "low": 2}},
        "top_findings": ["Round Dollar Amounts: 3 entries flagged (1.5%)", "Unusual Amounts: 3 entries flagged (1.5%)"],
        "top_flags": [
            {{"tool": "journal_entry_testing", "test_key": "round_amounts", "text": "Round Dollar Amounts: 3 entries flagged (1.5%)"}},
            {{"tool": "journal_entry_testing", "test_key": "unusual_amounts", "text": "Unusual Amounts: 3 entries flagged (1.5%)"}}]}},
    "test_results": [], "data_quality": {{}},
}}
out = [_key_items(_pdf_text(generate_payroll_testing_memo(r, filename="p", client_name="Client A"))),
       _key_items(_pdf_text(generate_je_testing_memo(je, filename="j", client_name="Client A")))]
print(json.dumps(out))
"""


def test_identical_exports_match_across_processes():
    script = _SUBPROCESS.format(backend=str(BACKEND))
    outputs = []
    for seed in ("1", "2", "3"):
        env = {**os.environ, "PYTHONHASHSEED": seed}
        done = subprocess.run(
            [sys.executable, "-c", script], cwd=BACKEND, env=env, capture_output=True, text=True, timeout=120
        )
        assert done.returncode == 0, done.stderr[-2000:]
        outputs.append(json.loads(done.stdout.strip().splitlines()[-1]))
    assert outputs[0] == outputs[1] == outputs[2]
    assert "Suggested follow-up" in outputs[0][1]


@pytest.mark.asyncio
@pytest.mark.usefixtures("bypass_csrf", "override_auth_verified")
async def test_real_ap_response_carries_identifiers_the_memo_uses():
    import httpx

    from main import app
    from tests.test_sprint886_supplemental_schedules import _ap_csv

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        screen = (await client.post("/audit/ap-payments", files={"file": ("ap.csv", _ap_csv(), "text/csv")})).json()
        flags = screen["composite_score"]["top_flags"]
        assert flags and {f["tool"] for f in flags} == {"ap_testing"}
        emitted = {t["test_key"] for t in screen["test_results"]}
        assert {f["test_key"] for f in flags} <= emitted
        memo = await client.post("/export/ap-testing-memo", json={**screen, "filename": "ap"})
    items = _key_items(_pdf_text(memo.content))
    first = flags[0]
    expected = get_follow_up_procedure("ap_testing", first["test_key"], seed="ap")
    if expected:
        assert expected[:40] in " ".join(items.split())
