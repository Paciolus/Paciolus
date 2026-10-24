"""Methodology sources catalog — consistency tests.

`frontend/src/content/methodology-sources.ts` tells a client, for every tool
and test, what rule the test applies, which authority (if any) the rule comes
from, and which numbers are Paciolus's own choices. A wrong citation there is
worse than none, so this guard holds it to the same registries as the rest of
the catalog:

1. Every code in a `sources: [...]` array is registered in
   `standards_registry.STANDARDS_BY_CODE`.
2. Every marketing audit tool in `tools_registry` has an entry (matched by
   slug == `toolKey`), with the registry display name.
3. Every `kind` is one of the four declared values, and every rule has one.
4. A rule attributed to an authority (any kind except `convention`) names at
   least one source.
5. A testing-suite tool has at least one rule per engine test.

The TS file is parsed with regexes, mirroring how `test_catalog_consistency.py`
reads `tool-ledger.ts`, so the file must keep `toolKey:`, `test:`, `kind:` and
`sources:` each on a single line with single-quoted strings.
"""

from __future__ import annotations

import re
from pathlib import Path

import standards_registry
import tools_registry

REPO_ROOT = Path(__file__).resolve().parents[2]
METHODOLOGY_PATH = REPO_ROOT / "frontend" / "src" / "content" / "methodology-sources.ts"

VALID_KINDS = frozenset({"requirement", "guidance", "published-method", "convention"})

# Entries that are not tools in tools_registry but belong in the catalog.
NON_TOOL_KEYS = frozenset({"composite_risk_score"})

_TOOL_KEY = re.compile(r"^\s*toolKey:\s*'([^']+)'", re.MULTILINE)
_TOOL_NAME = re.compile(r"^\s*toolName:\s*'((?:[^'\\]|\\.)*)'", re.MULTILINE)
_TEST = re.compile(r"^\s*test:\s*'((?:[^'\\]|\\.)*)'", re.MULTILINE)
_KIND = re.compile(r"^\s*kind:\s*'([^']*)'", re.MULTILINE)
_SOURCES = re.compile(r"^\s*sources:\s*\[([^\]]*)\]", re.MULTILINE)
_QUOTED = re.compile(r"'((?:[^'\\]|\\.)*)'")


def _text() -> str:
    return METHODOLOGY_PATH.read_text(encoding="utf-8")


def _tool_blocks(text: str) -> dict[str, str]:
    """Map toolKey -> the text of that tool's entry (up to the next toolKey)."""
    starts = [(m.start(), m.group(1)) for m in _TOOL_KEY.finditer(text)]
    blocks: dict[str, str] = {}
    for i, (pos, key) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(text)
        assert key not in blocks, f"duplicate toolKey {key!r} in methodology-sources.ts"
        blocks[key] = text[pos:end]
    return blocks


def _rule_blocks(tool_block: str) -> list[str]:
    starts = [m.start() for m in _TEST.finditer(tool_block)]
    return [tool_block[s : (starts[i + 1] if i + 1 < len(starts) else len(tool_block))] for i, s in enumerate(starts)]


def _sources(rule_block: str) -> list[str]:
    m = _SOURCES.search(rule_block)
    assert m, f"rule has no single-line `sources: [...]`:\n{rule_block[:200]}"
    return [s.replace("\\'", "'") for s in _QUOTED.findall(m.group(1))]


# ───────────────────────── Tests ─────────────────────────


def test_file_exists_and_parses():
    text = _text()
    assert _tool_blocks(text), "no `toolKey:` entries found in methodology-sources.ts"
    assert "export const METHODOLOGY_SOURCES" in text


def test_every_cited_source_is_registered():
    unregistered: dict[str, set[str]] = {}
    for key, block in _tool_blocks(_text()).items():
        for rule in _rule_blocks(block):
            for code in _sources(rule):
                if code not in standards_registry.STANDARDS_BY_CODE:
                    unregistered.setdefault(key, set()).add(code)
    assert not unregistered, (
        f"Sources not registered in standards_registry.py: { {k: sorted(v) for k, v in unregistered.items()} }. "
        "Register the authority (only if it is real) or correct the citation."
    )


def test_every_marketing_tool_has_an_entry():
    blocks = _tool_blocks(_text())
    slugs = {t.slug for t in tools_registry.marketing_audit_tools()}
    missing = slugs - set(blocks)
    assert not missing, f"methodology-sources.ts has no entry for: {sorted(missing)}"


def test_no_unknown_tool_keys():
    blocks = _tool_blocks(_text())
    known = {t.slug for t in tools_registry.all_tools()} | NON_TOOL_KEYS
    unknown = set(blocks) - known
    assert not unknown, f"toolKey values not in tools_registry: {sorted(unknown)}"


def test_tool_names_match_registry():
    mismatched: list[str] = []
    for key, block in _tool_blocks(_text()).items():
        if key in NON_TOOL_KEYS:
            continue
        m = _TOOL_NAME.search(block)
        assert m, f"{key}: no toolName"
        expected = tools_registry.get(key).display_name
        if m.group(1).replace("\\'", "'") != expected:
            mismatched.append(f"{key}: {m.group(1)!r} != registry {expected!r}")
    assert not mismatched, mismatched


def test_every_rule_has_a_valid_kind():
    problems: list[str] = []
    for key, block in _tool_blocks(_text()).items():
        rules = _rule_blocks(block)
        assert rules, f"{key}: no rules"
        for rule in rules:
            test_name = _TEST.search(rule).group(1)
            kinds = _KIND.findall(rule)
            if len(kinds) != 1:
                problems.append(f"{key} / {test_name}: expected one `kind:`, found {len(kinds)}")
            elif kinds[0] not in VALID_KINDS:
                problems.append(f"{key} / {test_name}: invalid kind {kinds[0]!r}")
    assert not problems, problems


def test_attributed_rules_name_a_source():
    """Anything but a Paciolus convention must say which authority it comes from."""
    bare: list[str] = []
    for key, block in _tool_blocks(_text()).items():
        for rule in _rule_blocks(block):
            kind = _KIND.search(rule).group(1)
            if kind != "convention" and not _sources(rule):
                bare.append(f"{key} / {_TEST.search(rule).group(1)} ({kind})")
    assert not bare, f"rules attributed to an authority with no source: {bare}"


def test_testing_tools_cover_every_test():
    blocks = _tool_blocks(_text())
    short: list[str] = []
    for tool in tools_registry.marketing_audit_tools():
        if tool.test_count is None:
            continue
        n = len(_rule_blocks(blocks[tool.slug]))
        if n < tool.test_count:
            short.append(f"{tool.slug}: {n} rules for {tool.test_count} tests")
    assert not short, short


# ───────────────────────── Sprint 835: authorities ─────────────────────────

AUTHORITIES_PATH = REPO_ROOT / "frontend" / "src" / "content" / "authorities.ts"
_PREFIXES = re.compile(r"^\s*prefixes:\s*\[([^\]]*)\]", re.MULTILINE)


def test_every_cited_source_has_an_authority_on_the_sources_page():
    """Each cited code must resolve to an issuer (and a place to read it) by prefix."""
    prefixes = [
        p for m in _PREFIXES.finditer(AUTHORITIES_PATH.read_text(encoding="utf-8")) for p in _QUOTED.findall(m.group(1))
    ]
    assert prefixes, "no `prefixes:` found in authorities.ts"
    orphans = sorted(
        {
            code
            for block in _tool_blocks(_text()).values()
            for rule in _rule_blocks(block)
            for code in _sources(rule)
            if not any(code.startswith(p) for p in prefixes)
        }
    )
    assert not orphans, f"cited codes with no authority in authorities.ts: {orphans}"
