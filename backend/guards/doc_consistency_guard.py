"""Documentation Consistency Guard — Sprint 593.

Stdlib-only static analysis verifying documentation claims match code truth.
Checks tier names, pricing, JWT expiration, share TTL, and aggregate tool counts
across docs and code.

Sprint 784 added the tool-count check. Sprint 689 expanded the catalog 12 -> 18 and
Sprint 717 reconciled the frontend ledger, but the prose did not follow: the FastAPI
description shipped "12-Tool Audit Intelligence Suite" in the **public** OpenAPI
schema for six months, and AGENTS.md, README.md, PRODUCT_VISION.md, ARCHITECTURE.md
and USER_GUIDE.md all still said twelve. `test_catalog_consistency.py` guards the
registry against the frontend ledger; nothing read documentation.

Usage:
    python -m guards.doc_consistency_guard          # from backend/
    python guards/doc_consistency_guard.py          # from backend/

Exit codes:
    0 — all checks pass
    1 — one or more violations found
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

# Documents whose aggregate tool counts must match the registry (Sprint 784).
# Deliberately excluded: COHESION_REMEDIATION.md, docs/archive/**, tasks/archive/**
# and CLAUDE.md's era table — all historical records of the 12-tool era.
TOOL_COUNT_DOCS: tuple[str, ...] = (
    "README.md",
    "AGENTS.md",
    "docs/01-product/PRODUCT_VISION.md",
    "docs/02-technical/ARCHITECTURE.md",
    "docs/03-product/REPORT_STANDARDS_SPEC.md",
    "docs/07-user-facing/USER_GUIDE.md",
)


@dataclass
class Violation:
    """A single consistency violation with file/line diagnostic."""

    rule: str
    file: str
    line: int
    message: str
    severity: str = "error"


# ---------------------------------------------------------------------------
# Parsers: extract truth from code
# ---------------------------------------------------------------------------


def _parse_user_tier_enum(backend_root: Path) -> set[str]:
    """Extract tier names from UserTier enum in models.py."""
    models_path = backend_root / "models.py"
    tiers: set[str] = set()
    in_enum = False
    for line in models_path.read_text(encoding="utf-8").splitlines():
        if "class UserTier" in line:
            in_enum = True
            continue
        if in_enum:
            if line.strip() == "" or (not line.startswith(" ") and not line.startswith("\t")):
                if tiers:
                    break
                continue
            m = re.match(r'\s+\w+\s*=\s*["\'](\w+)["\']', line)
            if m:
                tiers.add(m.group(1).lower())
    return tiers


def _parse_jwt_default(backend_root: Path) -> int | None:
    """Extract JWT_EXPIRATION_MINUTES default from config.py."""
    config_path = backend_root / "config.py"
    text = config_path.read_text(encoding="utf-8")
    m = re.search(r'_load_optional\(\s*"JWT_EXPIRATION_MINUTES"\s*,\s*"(\d+)"\s*\)', text)
    if m:
        return int(m.group(1))
    return None


def _parse_price_table(backend_root: Path) -> dict[str, dict[str, int]]:
    """Extract PRICE_TABLE from billing/price_config.py."""
    config_path = backend_root / "billing" / "price_config.py"
    text = config_path.read_text(encoding="utf-8")
    prices: dict[str, dict[str, int]] = {}
    # Match lines like:  "solo": {"monthly": 10000, "annual": 100000},
    for m in re.finditer(
        r'"(\w+)":\s*\{\s*"monthly":\s*(\d+)\s*,\s*"annual":\s*(\d+)\s*\}',
        text,
    ):
        tier = m.group(1)
        prices[tier] = {"monthly": int(m.group(2)), "annual": int(m.group(3))}
    return prices


def _parse_marketing_tool_count(backend_root: Path) -> int | None:
    """Count tools flagged is_marketing_audit_tool in tools_registry.py.

    Mirrors `tools_registry.MARKETING_AUDIT_TOOL_COUNT`, which is itself computed
    from that flag. Parsed as text, not imported, because this guard is stdlib-only
    and must run without the project's dependencies installed.

    Note the registry holds 19 entries: 18 audit tools plus Multi-Currency
    Conversion, which carries `is_marketing_audit_tool=False` because it is a
    side-car validation layer rather than a tool in the catalog.
    """
    registry_path = backend_root / "tools_registry.py"
    if not registry_path.exists():
        return None
    text = registry_path.read_text(encoding="utf-8")
    count = len(re.findall(r"is_marketing_audit_tool\s*=\s*True", text))
    return count or None


def _parse_share_ttl(backend_root: Path) -> dict[str, int]:
    """Extract share_ttl_hours values from shared/entitlements.py."""
    ent_path = backend_root / "shared" / "entitlements.py"
    text = ent_path.read_text(encoding="utf-8")
    ttls: dict[str, int] = {}
    # Parse TIER_ENTITLEMENTS blocks
    current_tier = None
    for line in text.splitlines():
        tier_match = re.match(r"\s+UserTier\.(\w+):", line)
        if tier_match:
            current_tier = tier_match.group(1).lower()
        ttl_match = re.match(r"\s+share_ttl_hours\s*=\s*(\d+)", line)
        if ttl_match and current_tier:
            ttls[current_tier] = int(ttl_match.group(1))
    return ttls


# ---------------------------------------------------------------------------
# Checkers: verify doc claims match code
# ---------------------------------------------------------------------------


def _check_tier_names_in_doc(
    code_tiers: set[str],
    doc_path: Path,
    doc_rel: str,
) -> list[Violation]:
    """Check that a doc file only references tier names from the code enum."""
    violations: list[Violation] = []
    # Known tier-like words that appear in rate limit tables or pricing tables
    tier_pattern = re.compile(
        r"\*\*(\w+)\*\*",  # Bold markdown: **TierName**
    )
    known_non_tiers = {"anonymous", "data", "tier", "monthly", "annual", "seat", "note"}
    text = doc_path.read_text(encoding="utf-8")
    for i, line in enumerate(text.splitlines(), 1):
        # Only check table rows (lines starting with |)
        if not line.strip().startswith("|"):
            continue
        for m in tier_pattern.finditer(line):
            word = m.group(1).lower()
            if word in known_non_tiers:
                continue
            # Check if this looks like a tier name (simple heuristic: single word, not a header)
            if word in {
                "free",
                "solo",
                "team",
                "organization",
                "professional",
                "enterprise",
                "basic",
                "premium",
                "starter",
            }:
                if word not in code_tiers:
                    violations.append(
                        Violation(
                            rule="tier_name_consistency",
                            file=doc_rel,
                            line=i,
                            message=f'Tier name "{m.group(1)}" not in UserTier enum. Valid tiers: {sorted(code_tiers)}',
                        )
                    )
    return violations


def _check_jwt_expiry_in_doc(
    code_default: int,
    doc_path: Path,
    doc_rel: str,
) -> list[Violation]:
    """Check that JWT expiration claims in docs match config default."""
    violations: list[Violation] = []
    text = doc_path.read_text(encoding="utf-8")
    # Match patterns like "30-minute expiration" or "30 minutes"
    for i, line in enumerate(text.splitlines(), 1):
        for m in re.finditer(r"(\d+)[- ]minute\b", line, re.IGNORECASE):
            claimed = int(m.group(1))
            # Only flag if it's in an auth/JWT context
            context = line.lower()
            if any(kw in context for kw in ("jwt", "access token", "expiration", "expiry")):
                if claimed != code_default:
                    violations.append(
                        Violation(
                            rule="jwt_expiry_consistency",
                            file=doc_rel,
                            line=i,
                            message=f"Doc claims {claimed}-minute JWT expiry, code defaults to {code_default} minutes",
                        )
                    )
    return violations


# Spelled-out numerals that appear in prose tool counts ("Twelve specialized tools").
_NUMBER_WORDS: dict[str, int] = {
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
}

# Catalog-claim phrasings only. Three narrow forms, each verified against the real
# occurrences in TOOL_COUNT_DOCS. A bare "six tools" is NOT a catalog claim — the
# first draft of this check matched "six tools are shown inline" (a true statement
# about the nav bar) and every markdown TOC anchor of the form
# `](#5-tool-3-journal-entry-testing)`, for 13 false positives out of 14.
_TOOL_COUNT_PATTERNS: tuple[re.Pattern[str], ...] = (
    # Compound adjective: "12-tool suite", "18-Tool Audit Intelligence Suite"
    re.compile(r"\b(?P<n>\d{1,2})[-\u2013]tool\b", re.IGNORECASE),
    # "all 18 tools", "all twelve tools"
    re.compile(
        r"\ball\s+(?P<n>\d{1,2}|" + "|".join(_NUMBER_WORDS) + r")\s+tools?\b",
        re.IGNORECASE,
    ),
    # Qualified plural: "18 audit tools", "Twelve specialized tools"
    re.compile(
        r"\b(?P<n>\d{1,2}|" + "|".join(_NUMBER_WORDS) + r")\s+"
        r"(?:audit|diagnostic|specialized|specialised|testing)\s+tools?\b",
        re.IGNORECASE,
    ),
)

# Lines carrying this marker record what was true at a past version (changelogs,
# revision histories, era tables) and keep their numbers.
_HISTORICAL_MARKER = re.compile(r"doc-consistency:\s*historical")

# Markdown link targets and inline code are stripped before matching: a heading
# anchor repeats the heading text, so "## 5. Tool 3: JE Testing" turns into
# "#5-tool-3-je-testing" in every link to it.
_LINK_TARGET = re.compile(r"\]\([^)]*\)")
_INLINE_CODE = re.compile(r"`[^`]*`")


def _strip_noise(line: str) -> str:
    """Remove markdown link targets and inline code spans from a line."""
    return _INLINE_CODE.sub(" ", _LINK_TARGET.sub(" ", line))


def _check_tool_count_in_doc(
    code_count: int,
    doc_path: Path,
    doc_rel: str,
) -> list[Violation]:
    """Check catalog tool-count claims against the registry.

    Skips version-history rows, which describe a past state by design.
    """
    violations: list[Violation] = []
    text = doc_path.read_text(encoding="utf-8", errors="replace")
    for i, raw_line in enumerate(text.splitlines(), 1):
        if _HISTORICAL_MARKER.search(raw_line):
            continue
        # Revision-history rows: "| 3.0 | 2026-02-16 | CTO | Updated for ... 11-tool suite |"
        if re.match(r"\s*\|\s*\d+\.\d+\s*\|\s*\d{4}-\d{2}-\d{2}\s*\|", raw_line):
            continue
        line = _strip_noise(raw_line)
        seen_spans: set[tuple[int, int]] = set()
        for pattern in _TOOL_COUNT_PATTERNS:
            for m in pattern.finditer(line):
                if m.span() in seen_spans:
                    continue
                seen_spans.add(m.span())
                raw = m.group("n").lower()
                claimed = _NUMBER_WORDS.get(raw)
                if claimed is None:
                    try:
                        claimed = int(raw)
                    except ValueError:
                        continue
                # Below five is a per-tier allowance ("2 tools (TB + Flux)"),
                # never a catalog claim — the catalog has never been that small.
                if claimed < 5 or claimed == code_count:
                    continue
                violations.append(
                    Violation(
                        rule="tool_count_consistency",
                        file=doc_rel,
                        line=i,
                        message=(
                            f"Doc claims {m.group(0).strip()!r}, registry has {code_count} "
                            f"(tools_registry.MARKETING_AUDIT_TOOL_COUNT). Update the prose, or mark the "
                            f"line `<!-- doc-consistency: historical -->` if it records a past version."
                        ),
                    )
                )
    return violations


def _check_api_description(code_count: int, backend_root: Path) -> list[Violation]:
    """Check the FastAPI app description's tool count against the registry.

    This is the only *public* tool-count claim in the codebase: it is served in the
    OpenAPI schema and rendered on /docs. Changing it also moves
    scripts/openapi-snapshot.json, which the OpenAPI Schema Drift Check gate
    compares — so regenerate the snapshot in the same commit.
    """
    main_path = backend_root / "main.py"
    if not main_path.exists():
        return []
    violations: list[Violation] = []
    for i, line in enumerate(main_path.read_text(encoding="utf-8").splitlines(), 1):
        m = re.search(r'description\s*=\s*"(?P<n>\d{1,2})-Tool\b', line)
        if not m:
            continue
        claimed = int(m.group("n"))
        if claimed != code_count:
            violations.append(
                Violation(
                    rule="tool_count_consistency",
                    file="backend/main.py",
                    line=i,
                    message=(
                        f"FastAPI description claims {claimed} tools, registry has {code_count} "
                        f"(tools_registry.MARKETING_AUDIT_TOOL_COUNT). This string is public — it ships in "
                        f"the OpenAPI schema. Fix it and regenerate scripts/openapi-snapshot.json."
                    ),
                )
            )
    return violations


def _check_pricing_in_doc(
    code_prices: dict[str, dict[str, int]],
    doc_path: Path,
    doc_rel: str,
) -> list[Violation]:
    """Check base plan pricing table in docs matches code PRICE_TABLE.

    Only checks lines within the '### 8.1 Pricing Tiers' section to avoid
    matching seat add-on pricing in Section 8.2.
    """
    violations: list[Violation] = []
    lines = doc_path.read_text(encoding="utf-8").splitlines()
    in_pricing_section = False
    for i, line in enumerate(lines, 1):
        # Enter section 8.1
        if re.match(r"###\s+8\.1\b", line):
            in_pricing_section = True
            continue
        # Exit on next heading
        if in_pricing_section and re.match(r"###\s+", line):
            break
        if not in_pricing_section or not line.strip().startswith("|"):
            continue
        # Extract tier from bold text in the line
        tier_m = re.search(r"\*\*(\w+)\*\*", line)
        if not tier_m:
            continue
        tier = tier_m.group(1).lower()
        if tier not in code_prices:
            continue
        # Check monthly price
        monthly_m = re.search(r"\$([0-9,]+)/month", line)
        if monthly_m:
            claimed_monthly = int(monthly_m.group(1).replace(",", "")) * 100  # to cents
            if claimed_monthly != code_prices[tier].get("monthly", 0):
                violations.append(
                    Violation(
                        rule="pricing_consistency",
                        file=doc_rel,
                        line=i,
                        message=f"{tier} monthly: doc claims ${claimed_monthly // 100}, code has ${code_prices[tier]['monthly'] // 100}",
                    )
                )
        # Check annual price
        annual_m = re.search(r"\$([0-9,]+)/year", line)
        if annual_m:
            claimed_annual = int(annual_m.group(1).replace(",", "")) * 100
            if claimed_annual != code_prices[tier].get("annual", 0):
                violations.append(
                    Violation(
                        rule="pricing_consistency",
                        file=doc_rel,
                        line=i,
                        message=f"{tier} annual: doc claims ${claimed_annual // 100}, code has ${code_prices[tier]['annual'] // 100}",
                    )
                )
    return violations


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------


def format_github_annotations(violations: list[Violation]) -> str:
    """Format violations as GitHub Actions ::error annotations."""
    lines = []
    for v in violations:
        lines.append(f"::error file={v.file},line={v.line}::[{v.rule}] {v.message}")
    return "\n".join(lines)


def format_summary(violations: list[Violation]) -> str:
    """Format a human-readable summary table."""
    if not violations:
        return "Documentation Consistency Guard: ALL CHECKS PASSED"
    lines = [
        f"Documentation Consistency Guard: {len(violations)} violation(s) found",
        "",
        f"{'Rule':<30} {'File':<50} {'Line':>5}  Message",
        "-" * 130,
    ]
    for v in violations:
        lines.append(f"{v.rule:<30} {v.file:<50} {v.line:>5}  {v.message}")
    return "\n".join(lines)


def run_checks(backend_root: Path) -> list[Violation]:
    """Run all documentation consistency checks."""
    project_root = backend_root.parent
    violations: list[Violation] = []

    # Parse code truth
    code_tiers = _parse_user_tier_enum(backend_root)
    jwt_default = _parse_jwt_default(backend_root)
    code_prices = _parse_price_table(backend_root)
    tool_count = _parse_marketing_tool_count(backend_root)

    # Doc files to check
    security_policy = project_root / "docs" / "04-compliance" / "SECURITY_POLICY.md"
    terms_of_service = project_root / "docs" / "04-compliance" / "TERMS_OF_SERVICE.md"

    # 1. Tier name checks
    if security_policy.exists():
        violations.extend(
            _check_tier_names_in_doc(
                code_tiers,
                security_policy,
                "docs/04-compliance/SECURITY_POLICY.md",
            )
        )
    if terms_of_service.exists():
        violations.extend(
            _check_tier_names_in_doc(
                code_tiers,
                terms_of_service,
                "docs/04-compliance/TERMS_OF_SERVICE.md",
            )
        )

    # 2. JWT expiry check
    if jwt_default is not None and security_policy.exists():
        violations.extend(
            _check_jwt_expiry_in_doc(
                jwt_default,
                security_policy,
                "docs/04-compliance/SECURITY_POLICY.md",
            )
        )

    # 3. Pricing consistency
    if terms_of_service.exists():
        violations.extend(
            _check_pricing_in_doc(
                code_prices,
                terms_of_service,
                "docs/04-compliance/TERMS_OF_SERVICE.md",
            )
        )

    # 4. Aggregate tool-count consistency (Sprint 784)
    if tool_count is not None:
        violations.extend(_check_api_description(tool_count, backend_root))
        for rel in TOOL_COUNT_DOCS:
            doc = project_root / rel
            if doc.exists():
                violations.extend(_check_tool_count_in_doc(tool_count, doc, rel))

    return violations


def main() -> int:
    """Entry point. Returns exit code."""
    script_dir = Path(__file__).resolve().parent
    backend_root = script_dir.parent  # guards/ is inside backend/

    violations = run_checks(backend_root)

    if violations:
        print(format_github_annotations(violations))
        print()
    print(format_summary(violations))

    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
