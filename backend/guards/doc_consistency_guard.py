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
    # Qualified plural: "18 audit tools", "Twelve specialized tools",
    # "twelve audit diagnostic tools", "Twelve purpose-built tools".
    #
    # Sprint 789b widened this twice, each change driven by a string that was
    # live on a marketing page: the group now repeats `{1,2}` so a stacked pair
    # of adjectives cannot slip between the count and the noun ("all twelve
    # audit diagnostic tools" on /demo), and `purpose-built` joined the list
    # ("Twelve purpose-built tools" in the slideshow).
    #
    # The list stays closed rather than becoming `[a-z-]+`. An open adjective
    # class would flag "the 6 remaining tools" and "7 new tools" — which is the
    # 13-of-14 false-positive rate the original draft of this check had, and is
    # pinned by test_customer_copy_ignores_non_catalog_claims. Only add an
    # adjective here when a real occurrence needs it; `core` was tried and
    # dropped, because "Core tools & exports" carries no count and the
    # alternative would have widened the pattern for nothing.
    re.compile(
        r"\b(?P<n>\d{1,2}|" + "|".join(_NUMBER_WORDS) + r")\s+"
        r"(?:(?:audit|diagnostic|specialized|specialised|testing|purpose-built)\s+){1,2}"
        r"tools?\b",
        re.IGNORECASE,
    ),
)

# A table cell can say just "All 12" while the row label or column header supplies the
# word "Tools" — which is how the tier table in USER_GUIDE.md and the public pricing
# comparison in frontend/src/domain/pricing.ts both survived the first sweep. Matched
# only on lines that also mention tools somewhere, so "All 10 formats" is untouched.
_BARE_ALL_IN_TOOLS_ROW = re.compile(
    r"\ball\s+(?P<n>\d{1,2}|" + "|".join(_NUMBER_WORDS) + r")\b(?!\s+(?:formats?|file))",
    re.IGNORECASE,
)
_ROW_MENTIONS_TOOLS = re.compile(r"\btools?\b", re.IGNORECASE)

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
        # Patterns overlap by design — "All 12 tools" matches both the qualified-plural
        # form and the bare "All N" form — so suppress any match that overlaps one
        # already reported on this line, rather than deduping on an exact span.
        reported_spans: list[tuple[int, int]] = []
        patterns = list(_TOOL_COUNT_PATTERNS)
        if _ROW_MENTIONS_TOOLS.search(line):
            patterns.append(_BARE_ALL_IN_TOOLS_ROW)
        for pattern in patterns:
            for m in pattern.finditer(line):
                start, stop = m.span()
                if any(start < prev_stop and prev_start < stop for prev_start, prev_stop in reported_spans):
                    continue
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
                reported_spans.append((start, stop))
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


# Customer-visible code surfaces carrying a tool count. The first version of this
# check covered backend/main.py only, which left the public pricing comparison and the
# demo route's page metadata stale while the gate reported success.
#
# Each entry: (repo-relative path, compiled pattern with an `n` group, why it matters).
#
# Sprint 789b: these two remain because each needs a *bespoke* pattern — a bare
# `'All 18'` table cell, and the digit-only metadata string. Everything else moved to
# the glob scan below, because this hand-maintained list is what let three stale
# strings sit on live pages. Sprint 784 added `demo/layout.tsx` and stopped there, so
# the /demo route's **metadata** was corrected to 18 while the visible page body in
# the sibling `demo/page.tsx` still said "all twelve audit diagnostic tools" — and
# the gate reported ALL CHECKS PASSED. A per-file allowlist only ever guards the files
# someone remembered to add.
CODE_SURFACE_CHECKS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "frontend/src/domain/pricing.ts",
        re.compile(r"'All (?P<n>\d{1,2})'"),
        "the pricing page's plan-comparison table — what a prospect reads before paying",
    ),
    (
        "frontend/src/app/(marketing)/demo/layout.tsx",
        re.compile(r"all (?P<n>\d{1,2}) audit diagnostic tools", re.IGNORECASE),
        "the /demo route's page metadata (search results and social share cards)",
    ),
)


# Globs covering copy a customer can actually read: the marketing route group, the
# marketing components rendered inside it, the upgrade modal shown at checkout, and the
# two shared gates whose prose states the entitlement. Scanned with the same
# numeral-aware _TOOL_COUNT_PATTERNS the documentation uses, rather than a bespoke
# per-file regex.
#
# The boundary is deliberate and worth stating: **the gate reads what a customer sees.**
# Workspace and tool pages are excluded — they render counts from `tool-ledger.ts` and
# from live `toolRuns.length`, both already tied to the registry by
# `test_catalog_consistency.py`, so scanning them would only add false-positive surface
# (`{toolRuns.length}/18 tools`). Code comments inside the scanned files are *not*
# excluded: a comment saying "all 18 tools" is a claim a future editor will trust.
CUSTOMER_COPY_GLOBS: tuple[str, ...] = (
    "frontend/src/app/(marketing)/**/*.tsx",
    "frontend/src/components/marketing/**/*.tsx",
    "frontend/src/components/billing/UpgradeModal.tsx",
    "frontend/src/components/shared/UpgradeGate.tsx",
    "frontend/src/components/shared/GuestCTA.tsx",
)


def _claimed_count(raw: str) -> int | None:
    """Resolve a matched count, spelled-out or numeric. None if unparseable."""
    lowered = raw.lower()
    if lowered in _NUMBER_WORDS:
        return _NUMBER_WORDS[lowered]
    return int(lowered) if lowered.isdigit() else None


def _check_code_surfaces(code_count: int, project_root: Path) -> list[Violation]:
    """Check customer-visible tool counts outside the documentation tree."""
    violations: list[Violation] = []
    for rel, pattern, why in CODE_SURFACE_CHECKS:
        path = project_root / rel
        if not path.exists():
            continue
        for i, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if _HISTORICAL_MARKER.search(line):
                continue
            for m in pattern.finditer(line):
                claimed = int(m.group("n"))
                if claimed < 5 or claimed == code_count:
                    continue
                violations.append(
                    Violation(
                        rule="tool_count_consistency",
                        file=rel,
                        line=i,
                        message=(
                            f"Claims {m.group(0).strip()!r} but the registry has {code_count} "
                            f"(tools_registry.MARKETING_AUDIT_TOOL_COUNT). This is {why}."
                        ),
                    )
                )
    return violations


def _check_customer_copy(code_count: int, project_root: Path) -> list[Violation]:
    """Check tool-count claims in customer-facing frontend copy (Sprint 789b).

    Same patterns as the documentation check, so a claim phrased in prose is caught
    wherever it is written. One finding per line, since several patterns can match the
    same claim.
    """
    violations: list[Violation] = []
    seen: set[tuple[str, int]] = set()

    for glob in CUSTOMER_COPY_GLOBS:
        for path in sorted(project_root.glob(glob)):
            rel = path.relative_to(project_root).as_posix()
            for i, raw_line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if _HISTORICAL_MARKER.search(raw_line):
                    continue
                if (rel, i) in seen:
                    continue
                line = _strip_noise(raw_line)
                # PR #183 review: `finditer`, not `search`. With `search` only the
                # first match per pattern was examined, so a line reading
                # "An 18-tool suite — formerly a 12-tool suite" passed: the first
                # match equalled the registry count, the loop moved to the next
                # pattern, and the stale claim beside it was never checked.
                # `_check_tool_count_in_doc` already iterated; this one did not.
                flagged = False
                for pattern in _TOOL_COUNT_PATTERNS:
                    if flagged:
                        break
                    for match in pattern.finditer(line):
                        claimed = _claimed_count(match.group("n"))
                        if claimed is None or claimed < 5 or claimed == code_count:
                            continue
                        seen.add((rel, i))
                        violations.append(
                            Violation(
                                rule="tool_count_consistency",
                                file=rel,
                                line=i,
                                message=(
                                    f"Customer-facing copy claims {match.group(0).strip()!r} but the "
                                    f"registry has {code_count} "
                                    f"(tools_registry.MARKETING_AUDIT_TOOL_COUNT). Update the copy, or "
                                    f"mark the line `doc-consistency: historical` if it records a past "
                                    f"version."
                                ),
                            )
                        )
                        # One violation per line still: the reader needs the line,
                        # not every phrasing on it.
                        flagged = True
                        break
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

    # 4. Aggregate tool-count consistency (Sprint 784; customer copy added 789b)
    if tool_count is not None:
        violations.extend(_check_api_description(tool_count, backend_root))
        violations.extend(_check_code_surfaces(tool_count, project_root))
        violations.extend(_check_customer_copy(tool_count, project_root))
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
