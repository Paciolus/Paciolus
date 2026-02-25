"""
Shared Testing Memo Template — Sprint 157

Config-driven PDF memo generator for standard testing battery tools.
Consolidates the identical structure from 7 testing memo generators
(JE, AP, Payroll, Revenue, AR Aging, Fixed Asset, Inventory) into a
single template with parameterized config.

Custom memos (Bank Rec, Three-Way Match, Multi-Period, Anomaly Summary)
are NOT covered — they have fundamentally different section structures.

Each generator file becomes a thin wrapper: config definition + delegation.
"""

import io
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Optional

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

from pdf_generator import LedgerRule, generate_reference_number
from security_utils import log_secure_operation
from shared.framework_resolution import ResolvedFramework
from shared.memo_base import (
    build_disclaimer,
    build_intelligence_stamp,
    build_methodology_section,
    build_proof_summary_section,
    build_results_summary_section,
    build_scope_section,
    build_workpaper_signoff,
    create_memo_styles,
)
from shared.report_chrome import (
    ReportMetadata,
    build_cover_page,
    draw_page_footer,
    find_logo,
)
from shared.scope_methodology import (
    build_authoritative_reference_block,
    build_methodology_statement,
    build_scope_statement,
)


@dataclass
class TestingMemoConfig:
    """Configuration for a standard testing memo.

    Each testing tool defines one of these with its domain-specific text.
    The generate_testing_memo() function uses this config to build the PDF.
    """

    title: str  # "AP Payment Testing Memo"
    ref_prefix: str  # "APT" (replaces PAC- prefix)
    entry_label: str  # "Total Payments Tested"
    flagged_label: str  # "Total Payments Flagged"
    log_prefix: str  # "ap_memo"
    domain: str  # "AP payment testing" (disclaimer)
    test_descriptions: dict[str, str]  # test_key -> description
    methodology_intro: str  # intro paragraph for methodology section
    risk_assessments: dict[str, str]  # {low, elevated, moderate, high} -> conclusion text
    isa_reference: str = "applicable professional standards"
    tool_domain: str = ""  # key into authoritative_language YAML (e.g., "journal_entry_testing")


# Type alias for optional callback hooks
ScopeBuilder = Callable[[list, dict, float, dict[str, Any], dict[str, Any], Optional[str]], None]
ExtraSectionBuilder = Callable[
    [list, dict, float, dict[str, Any], int], int  # returns updated section_counter
]
FindingFormatter = Callable[[Any], str]


def _default_format_finding(finding: Any) -> str:
    """Default finding formatter — just str()."""
    return str(finding)


def generate_testing_memo(
    result: dict[str, Any],
    config: TestingMemoConfig,
    *,
    filename: str = "",
    client_name: Optional[str] = None,
    period_tested: Optional[str] = None,
    prepared_by: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    workpaper_date: Optional[str] = None,
    source_document_title: Optional[str] = None,
    source_context_note: Optional[str] = None,
    build_scope: Optional[ScopeBuilder] = None,
    build_extra_sections: Optional[ExtraSectionBuilder] = None,
    format_finding: Optional[FindingFormatter] = None,
    resolved_framework: ResolvedFramework = ResolvedFramework.FASB,
    include_signoff: bool = False,
) -> bytes:
    """Generate a standard testing memo PDF using the provided config.

    Args:
        result: Tool result dict (e.g., APTestingResult.to_dict())
        config: TestingMemoConfig with all domain-specific text
        filename: Base filename for logging
        client_name: Client/entity name
        period_tested: Period description (e.g., "FY 2025")
        prepared_by: Preparer name
        reviewed_by: Reviewer name
        workpaper_date: Date string (ISO format)
        source_document_title: Parsed document title from metadata (optional)
        source_context_note: Additional context note (optional)
        build_scope: Optional custom scope builder (replaces standard scope)
        build_extra_sections: Optional callback for extra sections (e.g., Benford)
            receives (story, styles, doc_width, result, section_counter)
            returns updated section_counter
        format_finding: Optional finding formatter (e.g., for Payroll dict findings)

    Returns:
        PDF bytes
    """
    log_secure_operation(
        f"{config.log_prefix}_generate",
        f"Generating {config.title}: {filename}",
    )

    styles = create_memo_styles()
    buffer = io.BytesIO()
    reference = generate_reference_number().replace("PAC-", f"{config.ref_prefix}-")

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=1.0 * inch,
        bottomMargin=0.8 * inch,
    )

    story: list = []
    composite = result.get("composite_score", {})
    test_results = result.get("test_results", [])
    data_quality = result.get("data_quality", {})

    # 1. COVER PAGE
    logo_path = find_logo()
    metadata = ReportMetadata(
        title=config.title,
        client_name=client_name or "",
        engagement_period=period_tested or "",
        source_document=filename,
        source_document_title=source_document_title or "",
        source_context_note=source_context_note or "",
        reference=reference,
    )
    build_cover_page(story, styles, metadata, doc.width, logo_path)

    # 2. SCOPE (standard or custom)
    if build_scope is not None:
        build_scope(story, styles, doc.width, composite, data_quality, period_tested)
    else:
        build_scope_section(
            story,
            styles,
            doc.width,
            composite,
            data_quality,
            entry_label=config.entry_label,
            period_tested=period_tested,
            source_document=filename,
            source_document_title=source_document_title,
        )

    # 2a. SCOPE STATEMENT (framework-aware)
    if config.tool_domain:
        build_scope_statement(
            story,
            styles,
            doc.width,
            tool_domain=config.tool_domain,
            framework=resolved_framework,
            domain_label=config.domain,
        )

    # 2b. PROOF SUMMARY (between Scope and Methodology)
    build_proof_summary_section(story, styles, doc.width, result)

    # 3. METHODOLOGY
    build_methodology_section(
        story,
        styles,
        doc.width,
        test_results,
        config.test_descriptions,
        config.methodology_intro,
    )

    # 3a. METHODOLOGY STATEMENT (interpretive context)
    if config.tool_domain:
        build_methodology_statement(
            story,
            styles,
            doc.width,
            tool_domain=config.tool_domain,
            framework=resolved_framework,
            domain_label=config.domain,
        )

    # 4. RESULTS SUMMARY
    build_results_summary_section(
        story,
        styles,
        doc.width,
        composite,
        test_results,
        flagged_label=config.flagged_label,
    )

    # Track section numbering (I=Scope, II=Methodology, III=Results)
    section_counter = 4  # next section is IV

    # 5. KEY FINDINGS (conditional)
    top_findings = composite.get("top_findings", [])
    fmt = format_finding or _default_format_finding
    if top_findings:
        section_label = _roman(section_counter)
        story.append(Paragraph(f"{section_label}. Key Findings", styles["MemoSection"]))
        story.append(LedgerRule(doc.width))
        for i, finding in enumerate(top_findings[:5], 1):
            story.append(Paragraph(f"{i}. {fmt(finding)}", styles["MemoBody"]))
        story.append(Spacer(1, 8))
        section_counter += 1

    # 6. EXTRA SECTIONS (e.g., Benford's Law for JE)
    if build_extra_sections is not None:
        section_counter = build_extra_sections(
            story,
            styles,
            doc.width,
            result,
            section_counter,
        )

    # 6a. AUTHORITATIVE REFERENCES (framework-aware citations)
    if config.tool_domain:
        ref_label = _roman(section_counter)
        build_authoritative_reference_block(
            story,
            styles,
            doc.width,
            tool_domain=config.tool_domain,
            framework=resolved_framework,
            domain_label=config.domain,
            section_label=f"{ref_label}.",
        )
        section_counter += 1

    # 7. CONCLUSION
    section_label = _roman(section_counter)
    story.append(Paragraph(f"{section_label}. Conclusion", styles["MemoSection"]))
    story.append(LedgerRule(doc.width))

    score_val = composite.get("score", 0)
    if score_val < 10:
        assessment = config.risk_assessments["low"]
    elif score_val < 25:
        assessment = config.risk_assessments["elevated"]
    elif score_val < 50:
        assessment = config.risk_assessments["moderate"]
    else:
        assessment = config.risk_assessments["high"]

    story.append(Paragraph(assessment, styles["MemoBody"]))
    story.append(Spacer(1, 12))

    # WORKPAPER SIGN-OFF
    build_workpaper_signoff(
        story, styles, doc.width, prepared_by, reviewed_by, workpaper_date, include_signoff=include_signoff
    )

    # INTELLIGENCE STAMP
    build_intelligence_stamp(story, styles, client_name=client_name, period_tested=period_tested)

    # DISCLAIMER
    build_disclaimer(story, styles, domain=config.domain, isa_reference=config.isa_reference)

    # Build PDF (page footer on all pages: page numbers + disclaimer)
    doc.build(story, onFirstPage=draw_page_footer, onLaterPages=draw_page_footer)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    log_secure_operation(
        f"{config.log_prefix}_complete",
        f"{config.title} generated: {len(pdf_bytes)} bytes",
    )
    return pdf_bytes


def _roman(n: int) -> str:
    """Convert small integer to Roman numeral (I-X range)."""
    numerals = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI", 7: "VII", 8: "VIII", 9: "IX", 10: "X"}
    return numerals.get(n, str(n))
