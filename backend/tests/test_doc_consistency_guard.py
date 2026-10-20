"""Sprint 644 — tests for guards.doc_consistency_guard.

Covers each parser and checker plus the run_checks + formatting entry points.
Uses temporary backend/ and docs/ trees so the tests are self-contained and
don't depend on the live repo contents.
"""

from __future__ import annotations

from pathlib import Path

from guards.doc_consistency_guard import (
    CODE_SURFACE_CHECKS,
    Violation,
    _check_api_description,
    _check_code_surfaces,
    _check_jwt_expiry_in_doc,
    _check_pricing_in_doc,
    _check_tier_names_in_doc,
    _check_tool_count_in_doc,
    _parse_jwt_default,
    _parse_marketing_tool_count,
    _parse_price_table,
    _parse_share_ttl,
    _parse_user_tier_enum,
    format_github_annotations,
    format_summary,
    run_checks,
)

# ---------------------------------------------------------------------------
# Fixture: synthetic backend + docs tree
# ---------------------------------------------------------------------------


def _make_backend_tree(
    root: Path,
    *,
    tiers: list[str] = ("free", "solo", "professional", "enterprise"),
    jwt_minutes: int = 30,
    monthly_solo: int = 10000,
    annual_solo: int = 100000,
    share_ttls: dict[str, int] = None,
) -> Path:
    backend = root / "backend"
    backend.mkdir()
    (backend / "guards").mkdir()
    (backend / "billing").mkdir()
    (backend / "shared").mkdir()

    tier_lines = "\n".join(f'    {t.upper()} = "{t}"' for t in tiers)
    (backend / "models.py").write_text(
        f"class UserTier(Enum):\n{tier_lines}\n\n\nclass Unrelated:\n    pass\n",
        encoding="utf-8",
    )
    (backend / "config.py").write_text(
        f'JWT_EXPIRATION_MINUTES = _load_optional("JWT_EXPIRATION_MINUTES", "{jwt_minutes}")\n',
        encoding="utf-8",
    )
    (backend / "billing" / "price_config.py").write_text(
        "PRICE_TABLE = {\n"
        '    "free": {"monthly": 0, "annual": 0},\n'
        f'    "solo": {{"monthly": {monthly_solo}, "annual": {annual_solo}}},\n'
        '    "professional": {"monthly": 50000, "annual": 500000},\n'
        "}\n",
        encoding="utf-8",
    )
    share_ttls = share_ttls or {"free": 24, "solo": 168}
    ent_lines = ["TIER_ENTITLEMENTS = {"]
    for tier, ttl in share_ttls.items():
        ent_lines.append(f"    UserTier.{tier.upper()}:")
        ent_lines.append(f"        share_ttl_hours = {ttl}")
    ent_lines.append("}")
    (backend / "shared" / "entitlements.py").write_text("\n".join(ent_lines) + "\n", encoding="utf-8")

    return backend


def _make_docs(root: Path, *, security_text: str, terms_text: str) -> None:
    docs_dir = root / "docs" / "04-compliance"
    docs_dir.mkdir(parents=True)
    (docs_dir / "SECURITY_POLICY.md").write_text(security_text, encoding="utf-8")
    (docs_dir / "TERMS_OF_SERVICE.md").write_text(terms_text, encoding="utf-8")


# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------


def test_parse_user_tier_enum_extracts_all_tiers(tmp_path):
    backend = _make_backend_tree(tmp_path)
    assert _parse_user_tier_enum(backend) == {"free", "solo", "professional", "enterprise"}


def test_parse_jwt_default_returns_int(tmp_path):
    backend = _make_backend_tree(tmp_path, jwt_minutes=45)
    assert _parse_jwt_default(backend) == 45


def test_parse_jwt_default_none_when_missing(tmp_path):
    backend = _make_backend_tree(tmp_path)
    (backend / "config.py").write_text("# no JWT setting here\n", encoding="utf-8")
    assert _parse_jwt_default(backend) is None


def test_parse_price_table_extracts_cents(tmp_path):
    backend = _make_backend_tree(tmp_path)
    prices = _parse_price_table(backend)
    assert prices["solo"] == {"monthly": 10000, "annual": 100000}
    assert prices["professional"] == {"monthly": 50000, "annual": 500000}


def test_parse_share_ttl(tmp_path):
    backend = _make_backend_tree(tmp_path, share_ttls={"free": 12, "solo": 168})
    ttls = _parse_share_ttl(backend)
    assert ttls == {"free": 12, "solo": 168}


# ---------------------------------------------------------------------------
# Checker tests
# ---------------------------------------------------------------------------


def test_tier_name_check_flags_unknown_tier(tmp_path):
    code_tiers = {"free", "solo", "professional", "enterprise"}
    doc_path = tmp_path / "policy.md"
    doc_path.write_text(
        "| **Team** | $30/month |\n| **Solo** | $10/month |\n",
        encoding="utf-8",
    )
    violations = _check_tier_names_in_doc(code_tiers, doc_path, "policy.md")
    assert len(violations) == 1
    assert violations[0].rule == "tier_name_consistency"
    assert "Team" in violations[0].message


def test_tier_name_check_ignores_known_non_tiers(tmp_path):
    code_tiers = {"free", "solo"}
    doc_path = tmp_path / "policy.md"
    doc_path.write_text(
        "| **Monthly** | rate |\n| **Annual** | rate |\n| **Note** | see below |\n",
        encoding="utf-8",
    )
    assert _check_tier_names_in_doc(code_tiers, doc_path, "policy.md") == []


def test_tier_name_check_ignores_non_table_lines(tmp_path):
    code_tiers = {"free"}
    doc_path = tmp_path / "policy.md"
    doc_path.write_text(
        "Our **Team** plan is the best\nbut only table rows are checked.\n",
        encoding="utf-8",
    )
    assert _check_tier_names_in_doc(code_tiers, doc_path, "policy.md") == []


def test_jwt_expiry_check_flags_mismatch(tmp_path):
    doc_path = tmp_path / "sec.md"
    doc_path.write_text(
        "Access tokens use a 45-minute expiration for safety.\n",
        encoding="utf-8",
    )
    violations = _check_jwt_expiry_in_doc(30, doc_path, "sec.md")
    assert len(violations) == 1
    assert violations[0].rule == "jwt_expiry_consistency"


def test_jwt_expiry_check_matches_default(tmp_path):
    doc_path = tmp_path / "sec.md"
    doc_path.write_text("JWT expiration: 30 minutes.\n", encoding="utf-8")
    assert _check_jwt_expiry_in_doc(30, doc_path, "sec.md") == []


def test_jwt_expiry_check_ignores_non_auth_minutes(tmp_path):
    doc_path = tmp_path / "sec.md"
    doc_path.write_text("Backups run every 15 minutes.\n", encoding="utf-8")
    assert _check_jwt_expiry_in_doc(30, doc_path, "sec.md") == []


def test_pricing_check_flags_monthly_mismatch(tmp_path):
    doc_path = tmp_path / "tos.md"
    doc_path.write_text(
        "### 8.1 Pricing Tiers\n\n| Tier | Price |\n| **Solo** | $99/month |\n### 8.2 Other\n",
        encoding="utf-8",
    )
    code_prices = {"solo": {"monthly": 10000, "annual": 100000}}
    violations = _check_pricing_in_doc(code_prices, doc_path, "tos.md")
    assert len(violations) == 1
    assert violations[0].rule == "pricing_consistency"
    assert "solo monthly" in violations[0].message


def test_pricing_check_ignores_section_8_2(tmp_path):
    doc_path = tmp_path / "tos.md"
    # Monthly mismatch placed in 8.2 (seat pricing) — should not flag.
    doc_path.write_text(
        "### 8.1 Pricing Tiers\n\n| **Solo** | $100/month |\n### 8.2 Seats\n| **Solo** | $30/month seat add-on |\n",
        encoding="utf-8",
    )
    code_prices = {"solo": {"monthly": 10000, "annual": 100000}}
    assert _check_pricing_in_doc(code_prices, doc_path, "tos.md") == []


def test_pricing_check_annual_mismatch(tmp_path):
    doc_path = tmp_path / "tos.md"
    doc_path.write_text(
        "### 8.1 Pricing Tiers\n\n| **Solo** | $100/month — $999/year |\n",
        encoding="utf-8",
    )
    code_prices = {"solo": {"monthly": 10000, "annual": 100000}}
    violations = _check_pricing_in_doc(code_prices, doc_path, "tos.md")
    # Only annual mismatch
    assert any("annual" in v.message for v in violations)


# ---------------------------------------------------------------------------
# run_checks integration + formatter tests
# ---------------------------------------------------------------------------


def test_run_checks_clean_tree_returns_no_violations(tmp_path):
    backend = _make_backend_tree(tmp_path)
    _make_docs(
        tmp_path,
        security_text=("| **Solo** | rate |\n| **Professional** | rate |\nAccess tokens use a 30-minute expiration.\n"),
        terms_text=("### 8.1 Pricing Tiers\n\n| **Solo** | $100/month — $1,000/year |\n### 8.2 Other\n"),
    )
    assert run_checks(backend) == []


def test_run_checks_dirty_tree_collects_all_rules(tmp_path):
    backend = _make_backend_tree(tmp_path, jwt_minutes=30, monthly_solo=10000, annual_solo=100000)
    _make_docs(
        tmp_path,
        security_text=("| **Team** | unknown tier |\nAccess tokens use a 45-minute expiration.\n"),
        terms_text=("### 8.1 Pricing Tiers\n\n| **Solo** | $200/month |\n### 8.2 Seats\n"),
    )
    violations = run_checks(backend)
    rules = {v.rule for v in violations}
    assert "tier_name_consistency" in rules
    assert "jwt_expiry_consistency" in rules
    assert "pricing_consistency" in rules


def test_run_checks_missing_docs_is_safe(tmp_path):
    backend = _make_backend_tree(tmp_path)
    # No docs directory at all — run_checks must not raise.
    assert run_checks(backend) == []


def test_format_summary_no_violations():
    assert "ALL CHECKS PASSED" in format_summary([])


def test_format_summary_lists_each_violation():
    violations = [
        Violation(rule="r1", file="a.md", line=1, message="msg"),
        Violation(rule="r2", file="b.md", line=2, message="other"),
    ]
    out = format_summary(violations)
    assert "2 violation" in out
    assert "r1" in out and "r2" in out


def test_format_github_annotations_emits_error_lines():
    violations = [Violation(rule="r", file="f.md", line=7, message="m")]
    out = format_github_annotations(violations)
    assert out == "::error file=f.md,line=7::[r] m"


# ---------------------------------------------------------------------------
# Tool count consistency (Sprint 784)
# ---------------------------------------------------------------------------

_REGISTRY_STUB = """
Tool(slug="a", is_marketing_audit_tool=True),
Tool(slug="b", is_marketing_audit_tool=True),
Tool(slug="c", is_marketing_audit_tool=False),
"""


def test_parse_marketing_tool_count_counts_only_flagged(tmp_path):
    (tmp_path / "tools_registry.py").write_text(_REGISTRY_STUB, encoding="utf-8")
    assert _parse_marketing_tool_count(tmp_path) == 2


def test_parse_marketing_tool_count_none_when_registry_missing(tmp_path):
    assert _parse_marketing_tool_count(tmp_path) is None


def test_parse_marketing_tool_count_matches_real_registry():
    """The parser must agree with the registry's own computed constant."""
    import tools_registry

    backend_root = Path(tools_registry.__file__).resolve().parent
    assert _parse_marketing_tool_count(backend_root) == tools_registry.MARKETING_AUDIT_TOOL_COUNT


def test_tool_count_check_flags_compound_adjective(tmp_path):
    doc = tmp_path / "README.md"
    doc.write_text("**12-Tool Audit Intelligence Suite**\n", encoding="utf-8")
    violations = _check_tool_count_in_doc(18, doc, "README.md")
    assert len(violations) == 1
    assert violations[0].rule == "tool_count_consistency"
    assert "18" in violations[0].message


def test_tool_count_check_flags_qualified_plural(tmp_path):
    doc = tmp_path / "GUIDE.md"
    doc.write_text("Twelve specialized tools. Ten file formats.\n", encoding="utf-8")
    assert len(_check_tool_count_in_doc(18, doc, "GUIDE.md")) == 1


def test_tool_count_check_flags_all_n_tools(tmp_path):
    doc = tmp_path / "POLICY.md"
    doc.write_text("| Solo | All 12 tools |\n", encoding="utf-8")
    assert len(_check_tool_count_in_doc(18, doc, "POLICY.md")) == 1


def test_tool_count_check_passes_when_correct(tmp_path):
    doc = tmp_path / "README.md"
    doc.write_text(
        "An 18-tool suite. All 18 tools included. Eighteen specialized tools.\n",
        encoding="utf-8",
    )
    assert _check_tool_count_in_doc(18, doc, "README.md") == []


def test_tool_count_check_ignores_markdown_anchors(tmp_path):
    """Heading anchors repeat the heading text, so a TOC looks like '5-tool'.

    This was 9 of the 13 false positives in the check's first draft.
    """
    doc = tmp_path / "GUIDE.md"
    doc.write_text(
        "5. [Tool 3: Journal Entry Testing](#5-tool-3-journal-entry-testing)\n"
        "12. [Tool 10: Fixed Asset Testing](#12-tool-10-fixed-asset-testing)\n",
        encoding="utf-8",
    )
    assert _check_tool_count_in_doc(18, doc, "GUIDE.md") == []


def test_tool_count_check_ignores_bare_subset_counts(tmp_path):
    """'six tools are shown inline' is a true statement about the nav bar."""
    doc = tmp_path / "GUIDE.md"
    doc.write_text("Six tools are shown inline; the rest sit under More.\n", encoding="utf-8")
    assert _check_tool_count_in_doc(18, doc, "GUIDE.md") == []


def test_tool_count_check_ignores_version_history_rows(tmp_path):
    doc = tmp_path / "ARCH.md"
    doc.write_text(
        "| 3.0 | 2026-02-16 | CTO | Updated for Phase XXXIV (11-tool suite, 30 routers) |\n",
        encoding="utf-8",
    )
    assert _check_tool_count_in_doc(18, doc, "ARCH.md") == []


def test_tool_count_check_honours_historical_marker(tmp_path):
    doc = tmp_path / "VISION.md"
    doc.write_text(
        "Launched the 12-tool suite in v1.5.0 <!-- doc-consistency: historical -->\n",
        encoding="utf-8",
    )
    assert _check_tool_count_in_doc(18, doc, "VISION.md") == []


def test_tool_count_check_ignores_small_tier_allowances(tmp_path):
    """'2 tools (TB + Flux)' is a free-tier allowance, not a catalog claim."""
    doc = tmp_path / "POLICY.md"
    doc.write_text("| **Free** | 10/month | 3 | 2 tools (TB + Flux) |\n", encoding="utf-8")
    assert _check_tool_count_in_doc(18, doc, "POLICY.md") == []


def test_api_description_check_flags_mismatch(tmp_path):
    (tmp_path / "main.py").write_text(
        '    description="12-Tool Audit Intelligence Suite for Financial Professionals",\n',
        encoding="utf-8",
    )
    violations = _check_api_description(18, tmp_path)
    assert len(violations) == 1
    assert violations[0].file == "backend/main.py"
    assert "openapi-snapshot" in violations[0].message


def test_api_description_check_passes_when_correct(tmp_path):
    (tmp_path / "main.py").write_text(
        '    description="18-Tool Audit Intelligence Suite for Financial Professionals",\n',
        encoding="utf-8",
    )
    assert _check_api_description(18, tmp_path) == []


def test_api_description_check_safe_when_main_missing(tmp_path):
    assert _check_api_description(18, tmp_path) == []


# ---------------------------------------------------------------------------
# Table cells whose header supplies the word "Tools" (PR #172 review)
# ---------------------------------------------------------------------------


def test_bare_all_n_is_flagged_when_the_row_mentions_tools(tmp_path):
    """`| **Tools** | 2 (TB + Flux) | All 12 | ... |` — the count and the word
    "Tools" sit in different cells, which is how this row survived the first sweep."""
    doc = tmp_path / "GUIDE.md"
    doc.write_text("| **Tools** | 2 (TB + Flux) | All 12 | All 12 | All 12 |\n", encoding="utf-8")
    violations = _check_tool_count_in_doc(18, doc, "GUIDE.md")
    assert violations
    assert all(v.rule == "tool_count_consistency" for v in violations)


def test_bare_all_n_is_ignored_when_the_row_is_about_something_else(tmp_path):
    """`All 10 formats` must not be read as a tool count."""
    doc = tmp_path / "GUIDE.md"
    doc.write_text("| **Formats** | 5 basic | All 10 | All 10 | All 10 |\n", encoding="utf-8")
    assert _check_tool_count_in_doc(18, doc, "GUIDE.md") == []


def test_bare_all_n_passes_when_correct(tmp_path):
    doc = tmp_path / "GUIDE.md"
    doc.write_text("| **Tools** | 2 (TB + Flux) | All 18 | All 18 | All 18 |\n", encoding="utf-8")
    assert _check_tool_count_in_doc(18, doc, "GUIDE.md") == []


def test_all_n_formats_in_a_tools_row_is_not_flagged(tmp_path):
    """A row that mentions tools can still mention formats; only the tool count counts."""
    doc = tmp_path / "GUIDE.md"
    doc.write_text("| Paid tiers | All 18 tools | All 10 formats |\n", encoding="utf-8")
    assert _check_tool_count_in_doc(18, doc, "GUIDE.md") == []


# ---------------------------------------------------------------------------
# Customer-visible code surfaces (PR #172 review)
# ---------------------------------------------------------------------------


def test_code_surface_checks_name_real_files():
    """Each configured surface must exist, or the check silently covers nothing."""
    repo_root = Path(__file__).resolve().parents[2]
    missing = [rel for rel, _, _ in CODE_SURFACE_CHECKS if not (repo_root / rel).exists()]
    assert not missing, f"CODE_SURFACE_CHECKS references missing files: {missing}"


def test_pricing_comparison_mismatch_is_flagged(tmp_path):
    target = tmp_path / "frontend" / "src" / "domain"
    target.mkdir(parents=True)
    (target / "pricing.ts").write_text(
        "  { feature: 'Diagnostic Tools', free: '2 (TB + Flux)', solo: 'All 12' },\n",
        encoding="utf-8",
    )
    violations = _check_code_surfaces(18, tmp_path)
    assert len(violations) == 1
    assert violations[0].file == "frontend/src/domain/pricing.ts"
    assert "what a prospect reads before paying" in violations[0].message


def test_demo_metadata_mismatch_is_flagged(tmp_path):
    target = tmp_path / "frontend" / "src" / "app" / "(marketing)" / "demo"
    target.mkdir(parents=True)
    (target / "layout.tsx").write_text(
        "  description: 'Interactive demo of all 12 audit diagnostic tools.',\n",
        encoding="utf-8",
    )
    violations = _check_code_surfaces(18, tmp_path)
    assert len(violations) == 1
    assert "social share cards" in violations[0].message


def test_code_surfaces_pass_when_correct(tmp_path):
    target = tmp_path / "frontend" / "src" / "domain"
    target.mkdir(parents=True)
    (target / "pricing.ts").write_text("  { solo: 'All 18', professional: 'All 18' },\n", encoding="utf-8")
    assert _check_code_surfaces(18, tmp_path) == []


def test_code_surfaces_skip_missing_files(tmp_path):
    assert _check_code_surfaces(18, tmp_path) == []


def test_code_surfaces_honour_historical_marker(tmp_path):
    target = tmp_path / "frontend" / "src" / "domain"
    target.mkdir(parents=True)
    (target / "pricing.ts").write_text("  { solo: 'All 12' }, // doc-consistency: historical\n", encoding="utf-8")
    assert _check_code_surfaces(18, tmp_path) == []


def test_real_code_surfaces_agree_with_the_registry():
    """End-to-end: the shipped pricing table and demo metadata must be current."""
    import tools_registry

    repo_root = Path(__file__).resolve().parents[2]
    assert _check_code_surfaces(tools_registry.MARKETING_AUDIT_TOOL_COUNT, repo_root) == []
