#!/usr/bin/env python3
"""
Sprint 8: Report Standards Policy Validator.

Scans all PDF generator source files for compliance with the
Sprint 0–7 report standardization spec:

  1. Required sections — every generator imports/uses shared builders
  2. Banned assertive phrasing — no language that implies audit assurance
  3. Banned spaced-heading style — no letter-spaced ALL-CAPS headings
  4. Required citation metadata — generators with tool_domain must reference
     authoritative citations

Exit code 0 on pass, 1 on any violation.
Designed for CI integration.
"""

import re
import sys
from pathlib import Path

# Resolve backend root
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

# ---------------------------------------------------------------------------
# 1. Discovery
# ---------------------------------------------------------------------------

GENERATOR_FILES = sorted(
    set(
        list(BACKEND_DIR.glob("*_memo*.py"))
        + list(BACKEND_DIR.glob("*_summary_generator.py"))
        + [BACKEND_DIR / "pdf_generator.py"]
        + list((BACKEND_DIR / "shared").glob("memo_*.py"))
        + list((BACKEND_DIR / "shared").glob("scope_*.py"))
        + list((BACKEND_DIR / "shared").glob("report_*.py"))
    )
)

# ---------------------------------------------------------------------------
# 2. Banned patterns (from scope_methodology.py)
# ---------------------------------------------------------------------------

BANNED_ASSERTIVE_PATTERNS = (
    r"\bproves\b",
    r"\bconfirms\b",
    r"\bestablishes\b",
    r"\bdemonstrates that\b",
    r"\bconclusively\b",
    r"\bdefinitively\b",
    r"\bis evidence of\b",
    r"\bconstitutes fraud\b",
    r"\bis a material misstatement\b",
    r"\bis materially misstated\b",
    r"\bguarantees\b",
    r"\bcertifies\b",
)

_BANNED_RE = [re.compile(p, re.IGNORECASE) for p in BANNED_ASSERTIVE_PATTERNS]

# Spaced caps: 3+ uppercase letters each separated by single space, inside quotes
SPACED_CAPS_PATTERN = re.compile(r'"[A-Z](?:\s[A-Z]){2,}"')

# ALL-CAPS heading in MemoSection or SectionHeader style
ALL_CAPS_HEADING = re.compile(r'Paragraph\(\s*f?"([^"]+)".*?styles\["(?:MemoSection|SectionHeader)"\]')

# ---------------------------------------------------------------------------
# 3. Required imports for different generator categories
# ---------------------------------------------------------------------------

# Every generator (memo or diagnostic) must use at least one of these
SHARED_CHROME_IMPORTS = {
    "report_chrome",
    "memo_base",
    "memo_template",
}

# Generators that define tool_domain should also reference authoritative citations
CITATION_MARKER = "build_authoritative_reference_block"

# ---------------------------------------------------------------------------
# 4. Checks
# ---------------------------------------------------------------------------


def _is_all_caps_heading(text: str) -> bool:
    """Check if heading text is ALL CAPS (ignoring Roman numerals, f-string vars)."""
    cleaned = re.sub(r"^[IVX]+\.\s*", "", text)
    cleaned = re.sub(r"^\{[^}]+\}\.\s*", "", cleaned)
    cleaned = re.sub(r"\{[^}]+\}", "", cleaned)
    alpha_chars = [c for c in cleaned if c.isalpha()]
    if not alpha_chars:
        return False
    return all(c.isupper() for c in alpha_chars) and len(alpha_chars) >= 3


def check_banned_language(filepath: Path, content: str) -> list[str]:
    """Check for banned assertive language in string literals."""
    violations = []
    for lineno, line in enumerate(content.splitlines(), 1):
        # Only check lines with string literals (rough heuristic)
        if '"' not in line and "'" not in line:
            continue
        for pattern, regex in zip(BANNED_ASSERTIVE_PATTERNS, _BANNED_RE):
            if regex.search(line):
                # Exclude lines that are defining the pattern itself
                if "BANNED_PATTERNS" in line or 'r"' in line:
                    continue
                # Exclude comment-only lines
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                violations.append(f"  {filepath.name}:{lineno}: banned pattern '{pattern}' in: {stripped[:80]}")
    return violations


def check_spaced_caps(filepath: Path, content: str) -> list[str]:
    """Check for letter-spaced ALL-CAPS headings."""
    violations = []
    matches = SPACED_CAPS_PATTERN.findall(content)
    for match in matches:
        violations.append(f"  {filepath.name}: spaced-caps heading: {match}")
    return violations


def check_all_caps_headings(filepath: Path, content: str) -> list[str]:
    """Check for ALL-CAPS text in MemoSection/SectionHeader styles."""
    violations = []
    matches = ALL_CAPS_HEADING.findall(content)
    for match in matches:
        if _is_all_caps_heading(match):
            violations.append(f"  {filepath.name}: ALL-CAPS heading: '{match}'")
    return violations


def check_shared_chrome_usage(filepath: Path, content: str) -> list[str]:
    """Check that generators use shared report chrome."""
    violations = []
    # Skip shared modules themselves
    if filepath.parent.name == "shared":
        return violations
    # Skip non-generator modules
    if "generate_" not in content and "build_" not in content:
        return violations

    uses_shared = any(imp in content for imp in SHARED_CHROME_IMPORTS)
    if not uses_shared:
        violations.append(
            f"  {filepath.name}: does not import from any shared chrome module "
            f"({', '.join(sorted(SHARED_CHROME_IMPORTS))})"
        )
    return violations


def check_citation_metadata(filepath: Path, content: str) -> list[str]:
    """Generators with tool_domain should reference authoritative citations."""
    violations = []
    # Only check generators that define tool_domain
    if "tool_domain" not in content:
        return violations
    if filepath.parent.name == "shared":
        return violations

    # Standard template wrappers delegate to memo_template.py which handles citations
    delegates_to_template = "memo_template" in content or "generate_testing_memo" in content
    has_direct_citations = CITATION_MARKER in content or "scope_methodology" in content

    if not delegates_to_template and not has_direct_citations:
        violations.append(
            f"  {filepath.name}: defines tool_domain but does not reference "
            f"authoritative citations ({CITATION_MARKER}) and does not delegate "
            f"to memo_template"
        )
    return violations


# ---------------------------------------------------------------------------
# 5. Main
# ---------------------------------------------------------------------------


def main() -> int:
    """Run all checks and report results."""
    all_violations: dict[str, list[str]] = {
        "Banned Assertive Language": [],
        "Spaced-Caps Headings": [],
        "ALL-CAPS Section Headings": [],
        "Missing Shared Chrome": [],
        "Missing Citation Metadata": [],
    }

    for filepath in GENERATOR_FILES:
        if not filepath.exists():
            continue
        content = filepath.read_text(encoding="utf-8")

        all_violations["Banned Assertive Language"].extend(check_banned_language(filepath, content))
        all_violations["Spaced-Caps Headings"].extend(check_spaced_caps(filepath, content))
        all_violations["ALL-CAPS Section Headings"].extend(check_all_caps_headings(filepath, content))
        all_violations["Missing Shared Chrome"].extend(check_shared_chrome_usage(filepath, content))
        all_violations["Missing Citation Metadata"].extend(check_citation_metadata(filepath, content))

    # Report
    total = sum(len(v) for v in all_violations.values())
    files_scanned = len([f for f in GENERATOR_FILES if f.exists()])

    print(f"Report Standards Validator — scanned {files_scanned} files")
    print("=" * 60)

    if total == 0:
        print("All checks passed.")
        return 0

    for category, violations in all_violations.items():
        if violations:
            print(f"\n{category} ({len(violations)} violation(s)):")
            for v in violations:
                print(v)

    print(f"\nTotal violations: {total}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
