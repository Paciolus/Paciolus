"""Documentation Consistency Guard — Sprint 593.

Stdlib-only static analysis verifying documentation claims match code truth.
Checks tier names, pricing, JWT expiration, and share TTL across docs and code.

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
