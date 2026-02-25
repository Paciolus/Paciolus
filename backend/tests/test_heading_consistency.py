"""
Sprint 5: Heading Readability & Typographic Consistency Tests.

Validates:
- No letter-spaced all-caps headings remain (e.g., "E X E C U T I V E  S U M M A R Y")
- Section headings in MemoSection style use title case (not ALL CAPS)
- pdf_generator SectionHeader headings use title case
- Status badges use readable text (not spaced letters)
"""

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

# ─── Discovery: all Python files that generate PDF headings ──────────────

BACKEND_DIR = Path(__file__).parent.parent

# All memo generators + pdf_generator
GENERATOR_FILES = sorted(
    list(BACKEND_DIR.glob("*_memo*.py"))
    + list(BACKEND_DIR.glob("*_memo_*.py"))
    + [BACKEND_DIR / "pdf_generator.py"]
    + list(BACKEND_DIR.glob("*_summary_generator.py"))
    + list((BACKEND_DIR / "shared").glob("memo_*.py"))
    + list((BACKEND_DIR / "shared").glob("scope_*.py"))
)

# Deduplicate
GENERATOR_FILES = sorted(set(f for f in GENERATOR_FILES if f.exists()))

# Pattern: 3+ uppercase letters each separated by spaces, e.g. "E X E C"
SPACED_CAPS_PATTERN = re.compile(r'"[A-Z](?:\s[A-Z]){2,}"')

# Pattern: Section heading with ALL-CAPS text in MemoSection style
# Matches: Paragraph("ALL CAPS TEXT", styles["MemoSection"])
ALL_CAPS_MEMO_HEADING = re.compile(r'Paragraph\(\s*f?"([^"]+)".*?styles\["MemoSection"\]')

# Pattern: Section heading with ALL-CAPS text in SectionHeader style
ALL_CAPS_SECTION_HEADING = re.compile(r'Paragraph\(\s*"([^"]+)".*?styles\["SectionHeader"\]')


def _is_all_caps_heading(text: str) -> bool:
    """Check if a heading string is all uppercase (ignoring Roman numerals, punctuation, f-string vars)."""
    # Strip Roman numeral prefix: "IV. " or "{section_num}. "
    cleaned = re.sub(r"^[IVX]+\.\s*", "", text)
    cleaned = re.sub(r"^\{[^}]+\}\.\s*", "", cleaned)
    # Strip f-string expressions
    cleaned = re.sub(r"\{[^}]+\}", "", cleaned)
    # Remove punctuation and whitespace for the check
    alpha_chars = [c for c in cleaned if c.isalpha()]
    if not alpha_chars:
        return False
    return all(c.isupper() for c in alpha_chars) and len(alpha_chars) >= 3


# ─── Tests ───────────────────────────────────────────────────────────────


class TestNoSpacedCapsHeadings:
    """Ensure no letter-spaced all-caps headings remain anywhere."""

    @pytest.mark.parametrize("filepath", GENERATOR_FILES, ids=lambda f: f.name)
    def test_no_spaced_caps_in_generator(self, filepath: Path):
        """No letter-spaced headings like 'E X E C U T I V E  S U M M A R Y'."""
        content = filepath.read_text(encoding="utf-8")
        matches = SPACED_CAPS_PATTERN.findall(content)
        assert not matches, f"{filepath.name} contains letter-spaced heading(s): {matches}"


class TestMemoSectionTitleCase:
    """Ensure MemoSection headings use title case, not ALL CAPS."""

    @pytest.mark.parametrize("filepath", GENERATOR_FILES, ids=lambda f: f.name)
    def test_memo_section_not_all_caps(self, filepath: Path):
        """MemoSection headings should be title case (e.g. 'I. Scope' not 'I. SCOPE')."""
        content = filepath.read_text(encoding="utf-8")
        matches = ALL_CAPS_MEMO_HEADING.findall(content)
        all_caps = [m for m in matches if _is_all_caps_heading(m)]
        assert not all_caps, f"{filepath.name} has ALL-CAPS MemoSection heading(s): {all_caps}"


class TestSectionHeaderTitleCase:
    """Ensure SectionHeader headings in pdf_generator use title case."""

    def test_pdf_generator_section_headers_title_case(self):
        """SectionHeader paragraphs should use title case, not spaced caps."""
        content = (BACKEND_DIR / "pdf_generator.py").read_text(encoding="utf-8")
        matches = ALL_CAPS_SECTION_HEADING.findall(content)
        all_caps = [m for m in matches if _is_all_caps_heading(m)]
        assert not all_caps, f"pdf_generator.py has ALL-CAPS SectionHeader heading(s): {all_caps}"


class TestStatusBadgesReadable:
    """Ensure status badges use readable text, not spaced letters."""

    def test_no_spaced_status_badges(self):
        """Status badges like 'BALANCED' should not be letter-spaced."""
        content = (BACKEND_DIR / "pdf_generator.py").read_text(encoding="utf-8")
        # Look for spaced patterns in status/badge text
        spaced = SPACED_CAPS_PATTERN.findall(content)
        assert not spaced, f"pdf_generator.py contains spaced status badge(s): {spaced}"


class TestHeadingHierarchyDocumented:
    """Ensure the heading hierarchy is documented in report_styles.py."""

    def test_heading_hierarchy_in_report_styles(self):
        """report_styles.py should document the heading hierarchy."""
        content = (BACKEND_DIR / "shared" / "report_styles.py").read_text(encoding="utf-8")
        assert "H1" in content, "report_styles.py should document H1 heading level"
        assert "H2" in content, "report_styles.py should document H2 heading level"
        assert "H3" in content, "report_styles.py should document H3 heading level"
        assert "title case" in content.lower(), "report_styles.py should mention title case"
