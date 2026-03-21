"""
Three-Way Match Testing Memo PDF Generator (Sprint 94 / Sprint 504 rewrite)

Auto-generated matching memo per ISA 505 / ISA 500 / PCAOB AS 1105.
Renaissance Ledger aesthetic consistent with existing PDF exports.

Sections:
1. Scope (documents matched, file counts, config)
2. Methodology (6 tests documented)
3. Match Results (match rates, risk assessment, benchmark, amount totals)
4. Results Summary (composite risk score, tier, severity counts)
5. Material Variances (vendor, PO, invoice, amounts, net direction)
6. Key Findings (4+ findings with suggested procedures)
7. Unmatched Documents (detail tables per document type)
8. Authoritative References
9. Conclusion (4-tier risk scale)
"""

import io
from typing import Any, Optional

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from pdf_generator import (
    ClassicalColors,
    LedgerRule,
    create_leader_dots,
    generate_reference_number,
)
from security_utils import log_secure_operation
from shared.follow_up_procedures import get_follow_up_procedure
from shared.framework_resolution import ResolvedFramework
from shared.memo_base import (
    RISK_SCALE_LEGEND,
    RISK_TIER_DISPLAY,
    build_disclaimer,
    build_intelligence_stamp,
    build_proof_summary_section,
    build_workpaper_signoff,
    create_memo_styles,
)
from shared.report_chrome import (
    ReportMetadata,
    build_cover_page,
    draw_page_footer,
    find_logo,
)
from shared.report_styles import ledger_table_style
from shared.scope_methodology import (
    build_authoritative_reference_block,
    build_methodology_statement,
    build_scope_statement,
)

# =============================================================================
# CONSTANTS
# =============================================================================

# Map engine risk levels (LOW/MEDIUM/HIGH) to the standard 4-tier scale
_ENGINE_TIER_MAPPING = {
    "low": "low",
    "medium": "moderate",
    "high": "elevated",
    "critical": "high",
}

_TEST_DESCRIPTIONS: dict[str, str] = {
    "three_way_full_match": (
        "Structural. Tests whether each invoice has a corresponding PO and GRN "
        "within the configured amount tolerance ($0.01) and date window (30 days). "
        "Three-way match is the primary control over unauthorized payments."
    ),
    "amount_variance": (
        "Statistical. Flags invoice amounts differing from the PO amount by more "
        "than the configured price variance threshold (5%). May indicate unauthorized "
        "price changes, billing errors, or contract non-compliance."
    ),
    "date_variance": (
        "Structural. Flags invoice or receipt dates outside the 30-day window "
        "relative to the PO date. Large gaps may indicate backdated documents or "
        "goods invoiced before delivery."
    ),
    "unmatched_documents": (
        "Structural. Identifies POs, invoices, and receipts with no corresponding "
        "match in the other two sources. Unmatched invoices are the highest fraud "
        "risk \u2014 payment without an authorized PO per ISA 240."
    ),
    "duplicate_invoice_numbers": (
        "Advanced. Flags invoice numbers appearing more than once, indicating "
        "potential duplicate billing or invoice number reuse across vendors."
    ),
    "quantity_variance": (
        "Statistical. Flags cases where invoiced quantity differs from received "
        "quantity per GRN. May indicate billing for undelivered goods."
    ),
}

_MAX_UNMATCHED_ROWS = 20

# Match rate benchmark thresholds
_MATCH_RATE_THRESHOLDS = [
    (0.90, "Within best practice \u2014 no concern"),
    (0.85, "Acceptable \u2014 monitor"),
    (0.80, "Below best practice \u2014 investigate patterns"),
    (0.00, "Below 80% threshold \u2014 systemic review of procure-to-pay controls recommended"),
]

# Conclusion text by risk tier (4-tier scale)
_RISK_CONCLUSIONS: dict[str, str] = {
    "low": (
        "Based on the automated three-way matching procedures applied, "
        "the procurement cycle returned LOW flag density across the automated tests. "
        "Match rates are satisfactory and no variances exceeding the configured "
        "thresholds were detected."
    ),
    "moderate": (
        "Based on the automated three-way matching procedures applied, "
        "the procurement cycle returned MODERATE flag density across the automated tests. "
        "Select variances and unmatched documents should be reviewed for proper "
        "authorization and documentation."
    ),
    "elevated": (
        "Based on the automated three-way matching procedures applied, "
        "the procurement cycle returned ELEVATED flag density across the automated tests. "
        "Material variances and unmatched documents were detected that require "
        "focused investigation. The engagement team should evaluate whether additional "
        "procedures are appropriate per ISA 505 and PCAOB AS 1105."
    ),
    "high": (
        "Based on the automated three-way matching procedures applied, "
        "the procurement cycle returned HIGH flag density across the automated tests. "
        "Significant variances and/or unmatched documents were detected that require "
        "detailed investigation. The engagement team should evaluate whether additional "
        "substantive procedures are appropriate per ISA 505 and PCAOB AS 1105."
    ),
}


# =============================================================================
# RISK SCORING
# =============================================================================


def compute_twm_risk_score(
    full_match_rate: float,
    material_variance_count: int,
    high_variance_count: int,
    net_variance_amount: float,
    unmatched_invoices: int,
    unmatched_pos: int,
    unmatched_receipts: int,
    has_date_variance_high: bool,
    performance_materiality: float = 50_000,
) -> float:
    """Compute a composite risk score (0-100) for three-way match results."""
    score = 0.0

    # Match rate component (max 20)
    if full_match_rate < 0.70:
        score += 20
    elif full_match_rate < 0.80:
        score += 12
    elif full_match_rate < 0.85:
        score += 6
    elif full_match_rate < 0.90:
        score += 3

    # Material variance components (max 30)
    score += min(material_variance_count * 3, 15)
    score += min(high_variance_count * 5, 15)

    # Net variance vs materiality (max 10)
    if net_variance_amount >= performance_materiality:
        score += 10
    elif net_variance_amount >= performance_materiality * 0.5:
        score += 5

    # Unmatched documents (max 21)
    score += min(unmatched_invoices * 2, 10)
    score += min(unmatched_pos * 1, 5)
    score += min(unmatched_receipts * 2, 6)

    # Date variance (max 8)
    if has_date_variance_high:
        score += 8

    return min(score, 100)


# =============================================================================
# SECTION BUILDERS
# =============================================================================


def _build_methodology_table(
    story: list,
    styles: dict,
    doc_width: float,
    test_results: list[dict],
) -> None:
    """Build Section II: Methodology table with all 6 tests."""
    story.append(Paragraph("II. Methodology", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))
    story.append(
        Paragraph(
            "The following automated procurement validation tests were applied "
            "to the purchase order register, invoice log, and receiving log. "
            "Each test is classified by tier (structural, statistical, or advanced) "
            "and described below:",
            styles["MemoBody"],
        )
    )
    story.append(Spacer(1, 4))

    method_data = [["Test", "Tier", "Description"]]
    for tr in test_results:
        test_key = tr.get("test_key", "")
        desc = _TEST_DESCRIPTIONS.get(test_key, tr.get("description", ""))
        method_data.append(
            [
                Paragraph(tr.get("test_name", ""), styles["MemoTableCell"]),
                Paragraph(tr.get("test_tier", "structural").title(), styles["MemoTableCell"]),
                Paragraph(desc, styles["MemoTableCell"]),
            ]
        )

    method_table = Table(method_data, colWidths=[1.5 * inch, 0.8 * inch, 4.3 * inch], repeatRows=1)
    method_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                ("LINEBELOW", (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (0, -1), 0),
            ]
        )
    )
    story.append(method_table)
    story.append(Spacer(1, 8))


def _build_match_results(
    story: list,
    styles: dict,
    doc_width: float,
    summary: dict,
    risk_tier: str,
    risk_score: float = 0,
) -> None:
    """Build Section III: Match Results with benchmark context."""
    story.append(Paragraph("III. Match Results", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    full_count = summary.get("full_match_count", 0)
    partial_count = summary.get("partial_match_count", 0)
    full_rate = summary.get("full_match_rate", 0)
    partial_rate = summary.get("partial_match_rate", 0)

    base_tier_label, _ = RISK_TIER_DISPLAY.get(str(risk_tier).lower(), ("UNKNOWN", ClassicalColors.OBSIDIAN_500))
    tier_label = f"{base_tier_label} ({risk_score:.0f}/100)"

    result_lines = [
        create_leader_dots("Full Matches (3-way)", f"{full_count:,} ({full_rate:.1%})"),
        create_leader_dots("Partial Matches (2-way)", f"{partial_count:,} ({partial_rate:.1%})"),
        create_leader_dots("Material Variances", f"{summary.get('material_variances_count', 0):,}"),
        create_leader_dots("Net Variance", f"${summary.get('net_variance', 0):,.2f}"),
        create_leader_dots("Risk Assessment", tier_label),
    ]

    for line in result_lines:
        story.append(Paragraph(line, styles["MemoLeader"]))
    story.append(Spacer(1, 4))

    # Match rate benchmark
    benchmark_assessment = ""
    for threshold, assessment in _MATCH_RATE_THRESHOLDS:
        if full_rate >= threshold:
            benchmark_assessment = assessment
            break
    if not benchmark_assessment:
        benchmark_assessment = _MATCH_RATE_THRESHOLDS[-1][1]

    story.append(
        Paragraph(
            create_leader_dots("  Benchmark", "85\u201395% (best practice)"),
            styles["MemoLeader"],
        )
    )
    story.append(
        Paragraph(
            create_leader_dots("  Assessment", benchmark_assessment),
            styles["MemoLeader"],
        )
    )
    story.append(Spacer(1, 6))

    # Amount totals table
    amount_data = [
        ["Document Type", "Total Amount"],
        ["Purchase Orders", f"${summary.get('total_po_amount', 0):,.2f}"],
        ["Invoices", f"${summary.get('total_invoice_amount', 0):,.2f}"],
        ["Receipts", f"${summary.get('total_receipt_amount', 0):,.2f}"],
    ]
    amount_table = Table(amount_data, colWidths=[3.0 * inch, 2.5 * inch])
    amount_table.setStyle(TableStyle(ledger_table_style() + [("ALIGN", (1, 0), (-1, -1), "RIGHT")]))
    story.append(amount_table)
    story.append(Spacer(1, 8))


def _build_results_summary(
    story: list,
    styles: dict,
    doc_width: float,
    composite: dict,
    test_results: list[dict],
) -> None:
    """Build Section IV: Results Summary with risk score and severity counts."""
    story.append(Paragraph("IV. Results Summary", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    risk_tier = str(composite.get("risk_tier", "low")).lower()
    base_tier_label, _ = RISK_TIER_DISPLAY.get(risk_tier, ("UNKNOWN", ClassicalColors.OBSIDIAN_500))
    tier_label = f"{base_tier_label} ({composite.get('score', 0):.0f}/100)"

    story.append(
        Paragraph(
            create_leader_dots("Composite Diagnostic Score", f"{composite.get('score', 0):.1f} / 100"),
            styles["MemoLeader"],
        )
    )
    story.append(
        Paragraph(
            create_leader_dots("Diagnostic Tier", tier_label),
            styles["MemoLeader"],
        )
    )
    story.append(Paragraph(RISK_SCALE_LEGEND, styles["MemoBodySmall"]))
    story.append(Spacer(1, 2))

    story.append(
        Paragraph(
            create_leader_dots("Total Items Flagged", f"{composite.get('total_flagged', 0):,}"),
            styles["MemoLeader"],
        )
    )
    story.append(
        Paragraph(
            create_leader_dots("Overall Flag Rate", f"{composite.get('flag_rate', 0):.1%}"),
            styles["MemoLeader"],
        )
    )

    sev = composite.get("flags_by_severity", {})
    story.append(
        Paragraph(
            create_leader_dots("High Severity Flags", str(sev.get("high", 0))),
            styles["MemoLeader"],
        )
    )
    story.append(
        Paragraph(
            create_leader_dots("Medium Severity Flags", str(sev.get("medium", 0))),
            styles["MemoLeader"],
        )
    )
    story.append(
        Paragraph(
            create_leader_dots("Low Severity Flags", str(sev.get("low", 0))),
            styles["MemoLeader"],
        )
    )
    story.append(Spacer(1, 6))

    # Results by test table
    if test_results:
        results_data = [["Test", "Flagged", "Rate", "Severity"]]
        for tr in sorted(test_results, key=lambda t: t.get("flag_rate", 0), reverse=True):
            results_data.append(
                [
                    tr.get("test_name", ""),
                    str(tr.get("entries_flagged", 0)),
                    f"{tr.get('flag_rate', 0):.1%}",
                    tr.get("severity", "low").upper(),
                ]
            )

        results_table = Table(
            results_data,
            colWidths=[2.8 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch],
            repeatRows=1,
        )
        results_table.setStyle(TableStyle(ledger_table_style() + [("ALIGN", (1, 0), (-1, -1), "RIGHT")]))
        story.append(results_table)
        story.append(Spacer(1, 8))


def _build_material_variances(
    story: list,
    styles: dict,
    doc_width: float,
    variances: list[dict],
    summary: dict,
) -> None:
    """Build Section V: Material Variances with vendor/doc columns and net direction."""
    material_variances = [v for v in variances if v.get("severity") in ("high", "medium")]
    if not material_variances:
        return

    story.append(Paragraph("V. Material Variances", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    story.append(
        Paragraph(
            f"{len(material_variances)} material variance(s) were identified requiring review:",
            styles["MemoBody"],
        )
    )

    # Enriched table with vendor and document columns
    var_data = [["Vendor", "PO Number", "Invoice Number", "Field", "PO Value", "Invoice Value", "Variance", "Severity"]]
    for v in sorted(material_variances, key=lambda x: x.get("variance_amount", 0), reverse=True)[:15]:
        field = v.get("field", "amount")
        po_val = v.get("po_value")
        inv_val = v.get("invoice_value")

        if field == "date":
            po_str = str(po_val) if po_val is not None else "\u2014"
            inv_str = str(inv_val) if inv_val is not None else "\u2014"
            var_str = f"{v.get('variance_amount', 0):.0f} days"
        else:
            po_str = f"${po_val:,.2f}" if po_val is not None else "\u2014"
            inv_str = f"${inv_val:,.2f}" if inv_val is not None else "\u2014"
            var_str = f"${v.get('variance_amount', 0):,.2f}"

        var_data.append(
            [
                Paragraph(v.get("vendor", "\u2014"), styles["MemoTableCell"]),
                v.get("po_number", "\u2014"),
                v.get("invoice_number", "\u2014"),
                field.title(),
                po_str,
                inv_str,
                var_str,
                v.get("severity", "low").upper(),
            ]
        )

    var_table = Table(
        var_data,
        colWidths=[1.1 * inch, 0.85 * inch, 0.85 * inch, 0.55 * inch, 0.8 * inch, 0.8 * inch, 0.75 * inch, 0.6 * inch],
    )
    var_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Times-Roman"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                ("LINEBELOW", (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                ("ALIGN", (4, 0), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (0, -1), 0),
            ]
        )
    )
    story.append(var_table)

    if len(material_variances) > 15:
        story.append(
            Paragraph(
                f"+ {len(material_variances) - 15} additional material variances (see CSV export for full list)",
                styles["MemoBodySmall"],
            )
        )
    story.append(Spacer(1, 6))

    # Net variance direction statement
    po_total = summary.get("total_po_amount", 0)
    inv_total = summary.get("total_invoice_amount", 0)
    net_var = inv_total - po_total

    story.append(Paragraph("Net Variance Direction", styles["MemoSection"]))
    net_lines = [
        create_leader_dots("PO-Authorized Total", f"${po_total:,.2f}"),
        create_leader_dots("Invoice Total", f"${inv_total:,.2f}"),
    ]
    if net_var >= 0:
        net_lines.append(
            create_leader_dots("Net Overbilling", f"${net_var:,.2f}  (vendors billed above PO-authorized amounts)")
        )
    else:
        net_lines.append(
            create_leader_dots(
                "Net Underbilling", f"${abs(net_var):,.2f}  (vendors billed below PO-authorized amounts)"
            )
        )

    for line in net_lines:
        story.append(Paragraph(line, styles["MemoLeader"]))
    story.append(Spacer(1, 8))


def _build_key_findings(
    story: list,
    styles: dict,
    doc_width: float,
    composite: dict,
) -> None:
    """Build Section VI: Key Findings with suggested procedures."""
    top_findings = composite.get("top_findings", [])
    if not top_findings:
        return

    story.append(Paragraph("VI. Key Findings", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    # Map finding text to procedure keys
    _FINDING_PROCEDURE_KEYS = [
        "twm_net_overbilling",
        "twm_full_match_rate",
        "twm_unmatched_invoice",
        "twm_date_gap",
    ]

    for i, finding in enumerate(top_findings[:5], 1):
        story.append(Paragraph(f"{i}. {finding}", styles["MemoBody"]))

        # Look up procedure by index mapping or keyword match
        proc_key = _FINDING_PROCEDURE_KEYS[i - 1] if i - 1 < len(_FINDING_PROCEDURE_KEYS) else ""
        procedure = get_follow_up_procedure(proc_key, rotation_index=i)
        if procedure:
            story.append(
                Paragraph(
                    f"<i>Suggested follow-up: {procedure}</i>",
                    styles["MemoBodySmall"],
                )
            )

    story.append(Spacer(1, 8))


def _build_unmatched_documents(
    story: list,
    styles: dict,
    doc_width: float,
    twm_result: dict,
) -> None:
    """Build Section VII: Unmatched Documents with detail tables."""
    unmatched_pos = twm_result.get("unmatched_pos", [])
    unmatched_invoices = twm_result.get("unmatched_invoices", [])
    unmatched_receipts = twm_result.get("unmatched_receipts", [])
    total_unmatched = len(unmatched_pos) + len(unmatched_invoices) + len(unmatched_receipts)

    if total_unmatched == 0:
        return

    story.append(Paragraph("VII. Unmatched Documents", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    unmatched_lines = [
        create_leader_dots("Unmatched POs", str(len(unmatched_pos))),
        create_leader_dots("Unmatched Invoices", str(len(unmatched_invoices))),
        create_leader_dots("Unmatched Receipts", str(len(unmatched_receipts))),
    ]
    for line in unmatched_lines:
        story.append(Paragraph(line, styles["MemoLeader"]))
    story.append(Spacer(1, 6))

    # Unmatched Invoices detail table (HIGHEST RISK)
    if unmatched_invoices:
        story.append(
            Paragraph(
                f"Unmatched Invoices ({len(unmatched_invoices)} items) \u2014 HIGHEST RISK",
                styles["MemoBody"],
            )
        )
        cell_style = styles["MemoTableCell"]
        inv_data = [["Invoice Number", "Vendor", "Invoice Date", "Amount"]]
        for inv in unmatched_invoices[:_MAX_UNMATCHED_ROWS]:
            doc_dict = inv.get("document", inv)
            inv_data.append(
                [
                    Paragraph(str(doc_dict.get("invoice_number", "\u2014")), cell_style),
                    Paragraph(str(doc_dict.get("vendor", "\u2014")), cell_style),
                    Paragraph(str(doc_dict.get("invoice_date", "\u2014")), cell_style),
                    Paragraph(
                        f"${doc_dict.get('amount', doc_dict.get('total_amount', 0)):,.2f}"
                        if doc_dict.get("amount") or doc_dict.get("total_amount")
                        else "\u2014",
                        cell_style,
                    ),
                ]
            )
        inv_table = Table(inv_data, colWidths=[1.3 * inch, 2.0 * inch, 1.2 * inch, 1.3 * inch], repeatRows=1)
        inv_table.setStyle(TableStyle(ledger_table_style() + [("ALIGN", (3, 0), (-1, -1), "RIGHT")]))
        story.append(inv_table)
        if len(unmatched_invoices) > _MAX_UNMATCHED_ROWS:
            story.append(
                Paragraph(
                    f"+ {len(unmatched_invoices) - _MAX_UNMATCHED_ROWS} additional unmatched invoices",
                    styles["MemoBodySmall"],
                )
            )
        story.append(
            Paragraph(
                "<i>Do not release payment until PO authorization is confirmed.</i>",
                styles["MemoBodySmall"],
            )
        )
        story.append(Spacer(1, 6))

    # Unmatched POs detail table
    if unmatched_pos:
        story.append(
            Paragraph(
                f"Unmatched Purchase Orders ({len(unmatched_pos)} items)",
                styles["MemoBody"],
            )
        )
        cell_style_po = styles["MemoTableCell"]
        po_data = [["PO Number", "Vendor", "PO Date", "PO Amount"]]
        for po in unmatched_pos[:_MAX_UNMATCHED_ROWS]:
            doc_dict = po.get("document", po)
            po_data.append(
                [
                    Paragraph(str(doc_dict.get("po_number", "\u2014")), cell_style_po),
                    Paragraph(str(doc_dict.get("vendor", "\u2014")), cell_style_po),
                    Paragraph(str(doc_dict.get("po_date", doc_dict.get("order_date", "\u2014"))), cell_style_po),
                    Paragraph(
                        f"${doc_dict.get('po_amount', doc_dict.get('total_amount', 0)):,.2f}"
                        if doc_dict.get("po_amount") or doc_dict.get("total_amount")
                        else "\u2014",
                        cell_style_po,
                    ),
                ]
            )
        po_table = Table(po_data, colWidths=[1.3 * inch, 2.0 * inch, 1.2 * inch, 1.3 * inch], repeatRows=1)
        po_table.setStyle(TableStyle(ledger_table_style() + [("ALIGN", (3, 0), (-1, -1), "RIGHT")]))
        story.append(po_table)
        if len(unmatched_pos) > _MAX_UNMATCHED_ROWS:
            story.append(
                Paragraph(
                    f"+ {len(unmatched_pos) - _MAX_UNMATCHED_ROWS} additional unmatched POs",
                    styles["MemoBodySmall"],
                )
            )
        story.append(
            Paragraph(
                "<i>Confirm whether open orders are awaiting invoice or should be closed.</i>",
                styles["MemoBodySmall"],
            )
        )
        story.append(Spacer(1, 6))

    # Unmatched Receipts detail table
    if unmatched_receipts:
        story.append(
            Paragraph(
                f"Unmatched Receipts ({len(unmatched_receipts)} items)",
                styles["MemoBody"],
            )
        )
        cell_style_rec = styles["MemoTableCell"]
        rec_data = [["GRN Number", "Vendor", "Receipt Date", "Amount"]]
        for rec in unmatched_receipts[:_MAX_UNMATCHED_ROWS]:
            doc_dict = rec.get("document", rec)
            rec_data.append(
                [
                    Paragraph(
                        str(doc_dict.get("receipt_number", doc_dict.get("grn_number", "\u2014"))), cell_style_rec
                    ),
                    Paragraph(str(doc_dict.get("vendor", "\u2014")), cell_style_rec),
                    Paragraph(str(doc_dict.get("receipt_date", "\u2014")), cell_style_rec),
                    Paragraph(
                        f"${doc_dict.get('amount', doc_dict.get('total_amount', 0)):,.2f}"
                        if doc_dict.get("amount") or doc_dict.get("total_amount")
                        else "\u2014",
                        cell_style_rec,
                    ),
                ]
            )
        rec_table = Table(rec_data, colWidths=[1.3 * inch, 2.0 * inch, 1.2 * inch, 1.3 * inch], repeatRows=1)
        rec_table.setStyle(TableStyle(ledger_table_style() + [("ALIGN", (3, 0), (-1, -1), "RIGHT")]))
        story.append(rec_table)
        if len(unmatched_receipts) > _MAX_UNMATCHED_ROWS:
            story.append(
                Paragraph(
                    f"+ {len(unmatched_receipts) - _MAX_UNMATCHED_ROWS} additional unmatched receipts",
                    styles["MemoBodySmall"],
                )
            )
        story.append(
            Paragraph(
                "<i>Confirm whether an accrual is required for goods received but not invoiced.</i>",
                styles["MemoBodySmall"],
            )
        )
        story.append(Spacer(1, 6))

    story.append(Spacer(1, 4))


# =============================================================================
# MAIN GENERATOR
# =============================================================================


def generate_three_way_match_memo(
    twm_result: dict[str, Any],
    filename: str = "three_way_match",
    client_name: Optional[str] = None,
    period_tested: Optional[str] = None,
    prepared_by: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    workpaper_date: Optional[str] = None,
    source_document_title: Optional[str] = None,
    source_context_note: Optional[str] = None,
    fiscal_year_end: Optional[str] = None,
    resolved_framework: ResolvedFramework = ResolvedFramework.FASB,
    include_signoff: bool = False,
) -> bytes:
    """Generate a PDF testing memo for three-way match results.

    Args:
        twm_result: ThreeWayMatchResult.to_dict() output
        filename: Base filename for the report
        client_name: Client/entity name
        period_tested: Period description (e.g., "FY 2025")
        prepared_by: Preparer name
        reviewed_by: Reviewer name
        workpaper_date: Date string (ISO format)

    Returns:
        PDF bytes
    """
    log_secure_operation("twm_memo_generate", f"Generating three-way match memo: {filename}")

    styles = create_memo_styles()
    buffer = io.BytesIO()
    reference = generate_reference_number().replace("PAC-", "TWM-")

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=1.0 * inch,
        bottomMargin=0.8 * inch,
    )

    story: list = []
    summary = twm_result.get("summary", {})
    variances = twm_result.get("variances", [])
    config = twm_result.get("config", {})
    data_quality = twm_result.get("data_quality", {})
    composite = twm_result.get("composite_score", {})
    test_results = twm_result.get("test_results", [])

    # Map engine risk tier to standard 4-tier scale
    engine_risk = summary.get("risk_assessment", "low")
    risk_tier = composite.get("risk_tier", _ENGINE_TIER_MAPPING.get(engine_risk, "low"))

    # ---- COVER PAGE ----
    logo_path = find_logo()
    metadata = ReportMetadata(
        title="Three-Way Match Validator Memo",
        client_name=client_name or "",
        engagement_period=period_tested or "",
        fiscal_year_end=fiscal_year_end or "",
        source_document=filename,
        source_document_title=source_document_title or "",
        source_context_note=source_context_note or "",
        reference=reference,
    )
    build_cover_page(story, styles, metadata, doc.width, logo_path)

    # ---- I. SCOPE ----
    story.append(Paragraph("I. Scope", styles["MemoSection"]))
    story.append(LedgerRule(doc.width))

    source_scope_lines: list[str] = []
    if source_document_title and filename:
        source_scope_lines.append(create_leader_dots("Source", f"{source_document_title} ({filename})"))
    elif source_document_title:
        source_scope_lines.append(create_leader_dots("Source", source_document_title))
    elif filename:
        source_scope_lines.append(create_leader_dots("Source", filename))

    scope_lines = source_scope_lines + [
        create_leader_dots("Purchase Orders", f"{summary.get('total_pos', 0):,}"),
        create_leader_dots("Invoices", f"{summary.get('total_invoices', 0):,}"),
        create_leader_dots("Receipts / GRNs", f"{summary.get('total_receipts', 0):,}"),
    ]
    if period_tested:
        scope_lines.insert(0, create_leader_dots("Period Tested", period_tested))

    amt_tol = config.get("amount_tolerance", 0.01)
    price_tol = config.get("price_variance_threshold", 0.05)
    date_window = config.get("date_window_days", 30)
    fuzzy = config.get("enable_fuzzy_matching", True)

    scope_lines.extend(
        [
            create_leader_dots("Amount Tolerance", f"${amt_tol:,.2f}"),
            create_leader_dots("Price Variance Threshold", f"{price_tol:.0%}"),
            create_leader_dots("Date Window", f"{date_window} days"),
            create_leader_dots("Fuzzy Matching", "Enabled" if fuzzy else "Disabled"),
        ]
    )

    for line in scope_lines:
        story.append(Paragraph(line, styles["MemoLeader"]))
    story.append(Spacer(1, 4))

    # Scope statement (framework-aware)
    build_scope_statement(
        story,
        styles,
        doc.width,
        tool_domain="three_way_match",
        framework=resolved_framework,
        domain_label="three-way match validation",
    )

    # Proof summary
    col_detection = twm_result.get("column_detection", {})
    po_conf = col_detection.get("po", {}).get("overall_confidence", 0) if col_detection else 0
    inv_conf = col_detection.get("invoice", {}).get("overall_confidence", 0) if col_detection else 0
    rcpt_conf = col_detection.get("receipt", {}).get("overall_confidence", 0) if col_detection else 0
    avg_conf = (po_conf + inv_conf + rcpt_conf) / 3 if col_detection else 0

    unmatched_count = (
        len(twm_result.get("unmatched_pos", []))
        + len(twm_result.get("unmatched_invoices", []))
        + len(twm_result.get("unmatched_receipts", []))
    )

    _proof_result = {
        "composite_score": {
            "tests_run": composite.get("tests_run", 6),
            "total_flagged": composite.get(
                "total_flagged", unmatched_count + summary.get("material_variances_count", 0)
            ),
        },
        "data_quality": {
            "completeness_score": data_quality.get("overall_quality_score", 0),
        },
        "column_detection": {
            "overall_confidence": avg_conf,
        },
        "test_results": test_results
        or [
            {"test_name": "Full Matches", "entries_flagged": 0, "skipped": False},
            {
                "test_name": "Partial Matches",
                "entries_flagged": len(twm_result.get("partial_matches", [])),
                "skipped": False,
            },
            {
                "test_name": "Material Variances",
                "entries_flagged": summary.get("material_variances_count", 0),
                "skipped": False,
            },
            {
                "test_name": "Unmatched POs",
                "entries_flagged": len(twm_result.get("unmatched_pos", [])),
                "skipped": False,
            },
            {
                "test_name": "Unmatched Invoices",
                "entries_flagged": len(twm_result.get("unmatched_invoices", [])),
                "skipped": False,
            },
            {
                "test_name": "Unmatched Receipts",
                "entries_flagged": len(twm_result.get("unmatched_receipts", [])),
                "skipped": False,
            },
        ],
    }
    build_proof_summary_section(story, styles, doc.width, _proof_result)

    # ---- II. METHODOLOGY ----
    if test_results:
        _build_methodology_table(story, styles, doc.width, test_results)

    # Methodology statement (interpretive context)
    build_methodology_statement(
        story,
        styles,
        doc.width,
        tool_domain="three_way_match",
        framework=resolved_framework,
        domain_label="three-way match validation",
    )

    # ---- III. MATCH RESULTS ----
    _build_match_results(story, styles, doc.width, summary, risk_tier, composite.get("score", 0))

    # ---- IV. RESULTS SUMMARY ----
    if composite:
        _build_results_summary(story, styles, doc.width, composite, test_results)

    # ---- V. MATERIAL VARIANCES ----
    _build_material_variances(story, styles, doc.width, variances, summary)

    # ---- VI. KEY FINDINGS ----
    _build_key_findings(story, styles, doc.width, composite)

    # ---- VII. UNMATCHED DOCUMENTS ----
    _build_unmatched_documents(story, styles, doc.width, twm_result)

    # ---- VIII. AUTHORITATIVE REFERENCES ----
    build_authoritative_reference_block(
        story,
        styles,
        doc.width,
        tool_domain="three_way_match",
        framework=resolved_framework,
        domain_label="three-way match validation",
        section_label="VIII.",
    )

    # ---- IX. CONCLUSION ----
    story.append(Paragraph("IX. Conclusion", styles["MemoSection"]))
    story.append(LedgerRule(doc.width))

    assessment = _RISK_CONCLUSIONS.get(risk_tier, _RISK_CONCLUSIONS["low"])
    story.append(Paragraph(assessment, styles["MemoBody"]))
    story.append(Spacer(1, 12))

    # ---- WORKPAPER SIGN-OFF ----
    build_workpaper_signoff(
        story, styles, doc.width, prepared_by, reviewed_by, workpaper_date, include_signoff=include_signoff
    )

    # ---- INTELLIGENCE STAMP ----
    build_intelligence_stamp(story, styles, client_name=client_name, period_tested=period_tested)

    # ---- DISCLAIMER ----
    build_disclaimer(
        story,
        styles,
        domain="three-way match validation",
        isa_reference="ISA 500 (Audit Evidence) and ISA 505 (External Confirmations)",
    )

    # Build PDF
    doc.build(story, onFirstPage=draw_page_footer, onLaterPages=draw_page_footer)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    log_secure_operation("twm_memo_complete", f"TWM memo generated: {len(pdf_bytes)} bytes")
    return pdf_bytes
