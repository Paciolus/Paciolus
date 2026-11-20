"""Sprint 888 (CEO brief 13B): plan facts in the published copy match the code.

- One successful analysis run is one upload, whatever the number of files
  (``shared.entitlement_checks.uploads_used_this_period``).
- The allowance resets monthly on every billing interval (``upload_window_start``).
- The formats named are exactly the formats the backend has enabled by default.
- A shared link lasts 24 hours on Professional and 48 on Enterprise.
"""

import re
from pathlib import Path

from models import UserTier
from shared.entitlements import get_entitlements
from shared.file_formats import FORMAT_PROFILES, is_format_enabled

REPO = Path(__file__).resolve().parents[2]
PRICING_TS = (REPO / "frontend" / "src" / "domain" / "pricing.ts").read_text(encoding="utf-8")
README = (REPO / "README.md").read_text(encoding="utf-8")
USER_GUIDE = (REPO / "docs" / "07-user-facing" / "USER_GUIDE.md").read_text(encoding="utf-8")


def _faq(question: str) -> str:
    m = re.search(re.escape(question) + r"',\s*answer:\s*'((?:[^'\\]|\\.)*)'", PRICING_TS)
    assert m, question
    return m.group(1)


def _enabled_extensions() -> set[str]:
    return {
        ext.lstrip(".")
        for fmt, profile in FORMAT_PROFILES.items()
        if profile.parse_supported and is_format_enabled(fmt)
        for ext in profile.extensions
    }


def _disabled_extensions() -> set[str]:
    return {
        ext.lstrip(".")
        for fmt, profile in FORMAT_PROFILES.items()
        if not (profile.parse_supported and is_format_enabled(fmt))
        for ext in profile.extensions
    }


def _named_extensions(text: str) -> set[str]:
    known = {ext.lstrip(".") for p in FORMAT_PROFILES.values() for ext in p.extensions}
    return {ext for ext in known if re.search(rf"(?<![A-Za-z0-9]){re.escape(ext)}\b", text, re.I)}


def test_an_upload_is_one_successful_analysis_run():
    answer = _faq('What counts as an "upload"?')
    assert "successful analysis run counts as one upload" in answer
    assert "fails does not count" in answer
    assert "Each file submitted" not in answer


def test_the_allowance_resets_monthly_on_annual_plans_too():
    answer = _faq("Do uploads roll over between months?")
    assert "reset every month, including on annual plans" in answer
    assert "billing period" not in answer


def test_faq_names_exactly_the_enabled_formats():
    answer = _faq("Are there file size or row limits?")
    assert _named_extensions(answer) == _enabled_extensions()


def test_faq_free_plan_formats_match_entitlements():
    answer = _faq("Are there file size or row limits?")
    free = get_entitlements(UserTier.FREE).formats_allowed
    m = re.search(r"The Free plan accepts ([^.]+)\.", answer)
    assert m
    named = {"csv", "tsv", "txt"} & {w.lower() for w in re.findall(r"\w+", m.group(1))}
    if "Excel" in m.group(1):
        named |= {"xlsx", "xls"}
    assert named == set(free)


def test_readme_and_user_guide_format_lists_are_the_enabled_formats():
    readme_line = next(line for line in README.splitlines() if "File Formats**" in line)
    guide_line = next(line for line in USER_GUIDE.splitlines() if "File Formats:**" in line)
    faq_line = next(line for line in USER_GUIDE.splitlines() if line.startswith("A: Ten formats"))
    for line in (guide_line, faq_line):
        assert _named_extensions(line) == _enabled_extensions(), line
    # The README may mention a disabled format only to say it is off.
    assert _named_extensions(readme_line.split("(ODS is off")[0]) == _enabled_extensions()
    table_rows = [line for line in USER_GUIDE.splitlines() if re.match(r"\| [A-Z][\w ()]+ \| `\.", line)]
    table_exts = {ext for row in table_rows for ext in re.findall(r"`\.(\w+)`", row)}
    assert table_exts == _enabled_extensions()
    for disabled in _disabled_extensions():
        assert f"`.{disabled}`" not in USER_GUIDE


def test_user_guide_states_share_lifetimes_per_plan():
    pro = get_entitlements(UserTier.PROFESSIONAL).share_ttl_hours
    ent = get_entitlements(UserTier.ENTERPRISE).share_ttl_hours
    assert (pro, ent) == (24, 48)
    assert "up to 48 hours" not in USER_GUIDE
    assert f"after {pro} hours on Professional or {ent} hours on Enterprise" in USER_GUIDE
    assert "hourly cleanup" in USER_GUIDE
