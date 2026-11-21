"""Sprint 890 (CEO brief 15C, review ST-10): frontend wire types match the published response schemas.

The frontend's response types are written by hand. This cross-language check walks each tool's
top-level TypeScript response interface alongside the OpenAPI schema the backend publishes
(``scripts/openapi-snapshot.json``), following nested interfaces through the schema's ``$ref``s,
and fails when a field exists on one side only. It covers the five promoted JSON tools and the
trial balance account entries whose amount type was wrong.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
TYPES = REPO / "frontend" / "src" / "types"
SNAPSHOT = json.loads((REPO / "scripts" / "openapi-snapshot.json").read_text(encoding="utf-8"))
SCHEMAS = SNAPSHOT["components"]["schemas"]

_IFACE = re.compile(r"export interface (\w+)(?: extends [\w, ]+)? \{(.*?)\n\}", re.S)
_PROP = re.compile(r"^\s{2}(\w+)(\??):\s*([^\n;]+)", re.M)


def _interfaces(ts_file: str) -> dict[str, dict[str, str]]:
    text = (TYPES / ts_file).read_text(encoding="utf-8")
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"//[^\n]*", "", text)
    return {name: {m.group(1): m.group(3).strip() for m in _PROP.finditer(body)} for name, body in _IFACE.findall(text)}


def _ref_name(prop: dict) -> str | None:
    """The component a property points at, through arrays, nullables and dict values."""
    for candidate in (prop, prop.get("items", {}), prop.get("additionalProperties") or {}):
        if isinstance(candidate, dict) and "$ref" in candidate:
            return candidate["$ref"].rsplit("/", 1)[-1]
    for branch in prop.get("anyOf", []):
        name = _ref_name(branch)
        if name:
            return name
    return None


def _schema(name: str) -> dict:
    for key in (name, f"{name}-Output"):
        if key in SCHEMAS:
            return SCHEMAS[key]
    raise KeyError(name)


def _walk(ts: dict[str, dict[str, str]], iface: str, schema_name: str, path: str, seen: set, problems: list) -> None:
    if (iface, schema_name) in seen:
        return
    seen.add((iface, schema_name))
    ts_props = ts[iface]
    schema_props = _schema(schema_name).get("properties", {})
    for missing in sorted(set(schema_props) - set(ts_props)):
        problems.append(f"{path}.{missing}: sent by the backend, not declared in {iface}")
    for extra in sorted(set(ts_props) - set(schema_props)):
        problems.append(f"{path}.{extra}: declared in {iface}, not in the backend schema {schema_name}")
    for prop, ts_type in ts_props.items():
        if prop not in schema_props:
            continue
        inner = re.sub(r"\[\]|\| null|\| undefined|Record<string,\s*|>", " ", ts_type).split()
        nested = next((t for t in inner if t in ts), None)
        ref = _ref_name(schema_props[prop])
        if not (nested and ref):
            continue
        if ts_type.startswith("Record<"):
            # A TS record of X against an object schema with named members, each an X.
            for member, member_schema in _schema(ref).get("properties", {}).items():
                member_ref = _ref_name(member_schema)
                if member_ref:
                    _walk(ts, nested, member_ref, f"{path}.{prop}.{member}", seen, problems)
            continue
        _walk(ts, nested, ref, f"{path}.{prop}", seen, problems)


CASES = [
    ("form1099.ts", "Form1099Response", "Form1099Response"),
    ("bookToTax.ts", "BookToTaxResponse", "BookToTaxResponse"),
    ("cashFlowProjector.ts", "CashFlowForecastResponse", "CashFlowForecastResponse"),
    ("intercompany.ts", "IntercompanyEliminationResponse", "IntercompanyEliminationResponse"),
    ("w2Reconciliation.ts", "W2ReconciliationResponse", "W2ReconciliationResponse"),
]


@pytest.mark.parametrize(("ts_file", "iface", "schema"), CASES, ids=[c[1] for c in CASES])
def test_promoted_tool_types_match_the_schema(ts_file, iface, schema):
    ts = _interfaces(ts_file)
    problems: list[str] = []
    _walk(ts, iface, schema, iface, set(), problems)
    assert not problems, "\n".join(problems)


def test_trial_balance_account_amounts_are_numbers_on_both_sides():
    account = _schema("TrialBalanceAccountResponse")["properties"]
    for key in ("debit", "credit"):
        assert account[key].get("type") == "number", (key, account[key])
    text = (TYPES / "diagnostic.ts").read_text(encoding="utf-8")
    assert re.search(r"all_accounts\?:\s*Array<\{[^}]*debit:\s*number", text, re.S) or re.search(
        r"debit:\s*number", text
    ), "frontend/src/types/diagnostic.ts should declare account debit/credit as numbers"
