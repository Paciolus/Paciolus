"""
Shared Scope/Methodology/Citation Builders — Sprint 3

Universal report sections that ensure every generated report includes:
  1. Scope statement (what procedures were performed)
  2. Methodology statement (interpretive context, non-committal language)
  3. Authoritative reference block (FASB or GASB citations)

Uses the Sprint 1 framework resolver to select FASB vs GASB content
from the authoritative language YAML library.

Pure functions — no DB access, no side effects.
"""

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from pdf_generator import ClassicalColors, LedgerRule
from shared.framework_resolution import ResolvedFramework

# =============================================================================
# Non-committal language guardrails
# =============================================================================

APPROVED_PHRASES = (
    "may indicate",
    "could suggest",
    "warrants further procedures",
    "may warrant investigation",
    "could be indicative of",
    "should be evaluated",
    "may require additional inquiry",
    "warrants further review",
    "may not be representative",
    "could require follow-up",
)

BANNED_PATTERNS = (
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

_BANNED_RE = [re.compile(p, re.IGNORECASE) for p in BANNED_PATTERNS]


def validate_non_committal(text: str) -> list[str]:
    """Check text for banned assertive language.

    Returns a list of banned phrases found. An empty list means the text
    passes the non-committal language check.
    """
    violations: list[str] = []
    for pattern, regex in zip(BANNED_PATTERNS, _BANNED_RE):
        if regex.search(text):
            violations.append(pattern)
    return violations


# =============================================================================
# YAML content loading
# =============================================================================

_CONTENT_DIR = Path(__file__).parent / "authoritative_language"


@dataclass(frozen=True)
class AuthoritativeReference:
    """A single authoritative citation entry."""

    body: str  # "FASB" or "GASB"
    reference: str  # "ASC 606-10-25" or "Statement No. 33"
    topic: str  # Human-readable topic
    paragraph: str  # Paragraph reference
    status: str  # "Current"


@dataclass(frozen=True)
class ToolContent:
    """Resolved content for a specific tool + framework combination."""

    scope_statement: str
    methodology_statement: str
    references: tuple[AuthoritativeReference, ...]
    body: str  # "FASB" or "GASB"
    body_full: str  # "Financial Accounting Standards Board"


@lru_cache(maxsize=2)
def _load_yaml(framework: ResolvedFramework) -> dict[str, Any]:
    """Load and cache the YAML content for a framework."""
    filename = "fasb_scope_methodology.yml" if framework == ResolvedFramework.FASB else "gasb_scope_methodology.yml"
    yaml_path = _CONTENT_DIR / filename
    with open(yaml_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_tool_content(
    tool_domain: str,
    framework: ResolvedFramework,
    domain_label: str = "",
) -> ToolContent:
    """Resolve the authoritative content for a tool + framework.

    Args:
        tool_domain: Tool key matching the YAML tools section
            (e.g., "journal_entry_testing", "revenue_testing").
        framework: The resolved framework (FASB or GASB).
        domain_label: Human-readable domain name for the scope statement
            (e.g., "journal entry testing"). Falls back to tool_domain
            with underscores replaced.

    Returns:
        ToolContent with scope, methodology, and citations.
    """
    data = _load_yaml(framework)
    tool_data = data.get("tools", {}).get(tool_domain, {})

    domain = domain_label or tool_domain.replace("_", " ")
    data_desc = tool_data.get("data_description", "data provided by management")

    scope = data["scope_template"].format(
        domain=domain,
        data_description=data_desc,
    )
    methodology = data["methodology_template"]

    body = data["body"]
    body_full = data["body_full"]

    refs: list[AuthoritativeReference] = []
    for ref in tool_data.get("references", []):
        # FASB uses "codification", GASB uses "statement"
        ref_id = ref.get("codification") or ref.get("statement", "")
        refs.append(
            AuthoritativeReference(
                body=body,
                reference=ref_id,
                topic=ref.get("topic", ""),
                paragraph=ref.get("paragraph", ""),
                status=ref.get("status", "Current"),
            )
        )

    return ToolContent(
        scope_statement=scope,
        methodology_statement=methodology,
        references=tuple(refs),
        body=body,
        body_full=body_full,
    )


# =============================================================================
# PDF section builders
# =============================================================================

_DEFAULT_FRAMEWORK = ResolvedFramework.FASB


def build_scope_statement(
    story: list,
    styles: dict,
    doc_width: float,
    tool_domain: str,
    framework: ResolvedFramework = _DEFAULT_FRAMEWORK,
    domain_label: str = "",
) -> None:
    """Append the framework-aware scope statement paragraph to *story*.

    Placed after the existing scope data (leader dots) and before
    the proof summary or methodology section.
    """
    content = get_tool_content(tool_domain, framework, domain_label)
    story.append(Paragraph(content.scope_statement, styles["MemoBody"]))
    story.append(Spacer(1, 6))


def build_methodology_statement(
    story: list,
    styles: dict,
    doc_width: float,
    tool_domain: str,
    framework: ResolvedFramework = _DEFAULT_FRAMEWORK,
    domain_label: str = "",
) -> None:
    """Append the interpretive methodology statement paragraph to *story*.

    Placed after the test table / methodology intro, before the
    results summary or next section.
    """
    content = get_tool_content(tool_domain, framework, domain_label)
    story.append(
        Paragraph(
            f"<b>Interpretive Context:</b> {content.methodology_statement}",
            styles["MemoBody"],
        )
    )
    story.append(Spacer(1, 6))


def build_authoritative_reference_block(
    story: list,
    styles: dict,
    doc_width: float,
    tool_domain: str,
    framework: ResolvedFramework = _DEFAULT_FRAMEWORK,
    domain_label: str = "",
    section_label: str = "",
) -> None:
    """Append the authoritative reference citation table to *story*.

    Renders a structured table of framework-specific citations (FASB ASC
    or GASB Statements) relevant to the tool domain.

    Args:
        story: ReportLab story list.
        styles: Memo style dict.
        doc_width: Document content width.
        tool_domain: Tool key for content lookup.
        framework: Resolved FASB or GASB.
        domain_label: Optional human-readable domain name.
        section_label: Optional section prefix (e.g., "VI.").
    """
    content = get_tool_content(tool_domain, framework, domain_label)

    if not content.references:
        return

    heading = "AUTHORITATIVE REFERENCES"
    if section_label:
        heading = f"{section_label} {heading}"

    story.append(Paragraph(heading, styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    table_data = [["Body", "Reference", "Topic", "Status"]]
    for ref in content.references:
        table_data.append(
            [
                Paragraph(ref.body, styles["MemoTableCell"]),
                Paragraph(ref.reference, styles["MemoTableCell"]),
                Paragraph(ref.topic, styles["MemoTableCell"]),
                Paragraph(ref.status, styles["MemoTableCell"]),
            ]
        )

    col_widths = [0.6 * inch, 1.4 * inch, 3.8 * inch, 0.8 * inch]
    ref_table = Table(table_data, colWidths=col_widths)
    ref_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Times-Roman"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                ("LINEBELOW", (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (0, -1), 0),
            ]
        )
    )
    story.append(ref_table)
    story.append(Spacer(1, 8))
