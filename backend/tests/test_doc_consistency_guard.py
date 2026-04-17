"""Sprint 644 — tests for guards.doc_consistency_guard.

Covers each parser and checker plus the run_checks + formatting entry points.
Uses temporary backend/ and docs/ trees so the tests are self-contained and
don't depend on the live repo contents.
"""

from __future__ import annotations

from pathlib import Path

from guards.doc_consistency_guard import (
    Violation,
    _check_jwt_expiry_in_doc,
    _check_pricing_in_doc,
    _check_tier_names_in_doc,
    _parse_jwt_default,
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
