"""
Paciolus — Population Profile PDF Memo Generator
Sprint 287: Phase XXXIX / Sprint 511: Enrichment

Custom memo using memo_base.py primitives. Pattern B (custom sections).
Sections: Header → Scope → Descriptive Statistics → Magnitude Distribution →
          Concentration Analysis → Account Type Stratification →
          Benford's Law Analysis → Exception Flags →
          Suggested Procedures → Workpaper Sign-Off → Disclaimer
"""

from typing import Optional

from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from pdf_generator import (
    ClassicalColors,
    DoubleRule,
    LedgerRule,
    create_leader_dots,
    format_classical_date,
    generate_reference_number,
)
from shared.framework_resolution import ResolvedFramework
from shared.memo_base import build_disclaimer, build_intelligence_stamp, build_workpaper_signoff, create_memo_styles
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

# ═══════════════════════════════════════════════════════════════
# Shared table style helpers
# ═══════════════════════════════════════════════════════════════


def _standard_table_style(*, right_align_from: int = 1, courier_cols: list[int] | None = None):
    """Build a standard TableStyle for report tables."""
    commands: list = [
        ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Times-Roman"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
        ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
        ("LINEBELOW", (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
        ("ALIGN", (right_align_from, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (0, -1), 0),
    ]
    for col in courier_cols or []:
        commands.append(("FONTNAME", (col, 1), (col, -1), "Courier"))
    return TableStyle(commands)


def generate_population_profile_memo(
    profile_result: dict,
    filename: str = "population_profile",
    client_name: Optional[str] = None,
    period_tested: Optional[str] = None,
    prepared_by: Optional[str] = None,
    reviewed_by: Optional[str] = None,
    workpaper_date: Optional[str] = None,
    source_document_title: Optional[str] = None,
    source_context_note: Optional[str] = None,
    resolved_framework: ResolvedFramework = ResolvedFramework.FASB,
    include_signoff: bool = False,
) -> bytes:
    """Generate a Population Profile Report PDF memo.

    Args:
        profile_result: Dict from PopulationProfileReport.to_dict()
        filename: Source filename
        client_name: Optional client name for header
        period_tested: Optional period label
        prepared_by: Preparer name for sign-off
        reviewed_by: Reviewer name for sign-off
        workpaper_date: Date for sign-off

    Returns:
        PDF bytes
    """
    import io

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=(8.5 * inch, 11 * inch),
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    doc_width = doc.width
    styles = create_memo_styles()
    story: list = []
    reference = generate_reference_number().replace("PAC-", "PPR-")

    # ── Cover Page (diagonal color bands) ──
    logo_path = find_logo()
    cover_metadata = ReportMetadata(
        title="TB Population Profile Report",
        client_name=client_name or "",
        engagement_period=period_tested or "",
        source_document=filename,
        source_document_title=source_document_title or "",
        source_context_note=source_context_note or "",
        reference=reference,
    )
    build_cover_page(story, styles, cover_metadata, doc_width, logo_path)

    # ── Header ──
    story.append(Paragraph("TB Population Profile Report", styles["MemoTitle"]))
    if client_name:
        story.append(Paragraph(client_name, styles["MemoSubtitle"]))
    story.append(
        Paragraph(
            f"{format_classical_date()} &nbsp;&bull;&nbsp; {reference}",
            styles["MemoRef"],
        )
    )
    story.append(DoubleRule(doc_width))
    story.append(Spacer(1, 16))

    # ── Extract common fields ──
    account_count = profile_result.get("account_count", 0)
    total_abs = profile_result.get("total_abs_balance", 0)
    gini = profile_result.get("gini_coefficient", 0)
    gini_interp = profile_result.get("gini_interpretation", "Low")

    # ── I. SCOPE ──
    story.append(Paragraph("I. Scope", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    # Source document transparency
    if source_document_title and filename:
        source_line = create_leader_dots("Source", f"{source_document_title} ({filename})")
    elif source_document_title:
        source_line = create_leader_dots("Source", source_document_title)
    else:
        source_line = create_leader_dots("Source File", filename)

    scope_lines = [
        source_line,
        create_leader_dots("Unique Accounts", f"{account_count:,}"),
        create_leader_dots("Total Population Value", f"${total_abs:,.2f}"),
        create_leader_dots("Gini Coefficient", f"{gini:.4f} ({gini_interp})"),
    ]
    if period_tested:
        scope_lines.insert(0, create_leader_dots("Period Tested", period_tested))

    # Data quality score in scope
    data_quality = profile_result.get("data_quality")
    if data_quality:
        score = data_quality.get("overall_score", 0)
        scope_lines.append(create_leader_dots("Data Quality Score", f"{score:.1f}%"))

    for line in scope_lines:
        story.append(Paragraph(line, styles["MemoLeader"]))
    story.append(Spacer(1, 6))

    # Gini threshold footnote
    story.append(
        Paragraph(
            "<i>Gini concentration thresholds: Low (&lt; 0.40) · Moderate (0.40–0.65) · High (&gt; 0.65)</i>",
            styles["MemoBody"],
        )
    )
    story.append(Spacer(1, 6))

    build_scope_statement(
        story,
        styles,
        doc_width,
        tool_domain="population_profile",
        framework=resolved_framework,
        domain_label="population profile analysis",
    )

    # ── II. DESCRIPTIVE STATISTICS ──
    story.append(Paragraph("II. Descriptive Statistics", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    stats_data = [["Statistic", "Value"]]
    stats_data.append(["Mean (Absolute Balance)", f"${profile_result.get('mean_abs_balance', 0):,.2f}"])
    stats_data.append(["Median (Absolute Balance)", f"${profile_result.get('median_abs_balance', 0):,.2f}"])
    stats_data.append(["Standard Deviation", f"${profile_result.get('std_dev_abs_balance', 0):,.2f}"])
    stats_data.append(["Minimum", f"${profile_result.get('min_abs_balance', 0):,.2f}"])
    stats_data.append(["Maximum", f"${profile_result.get('max_abs_balance', 0):,.2f}"])
    stats_data.append(["25th Percentile (P25)", f"${profile_result.get('p25', 0):,.2f}"])
    stats_data.append(["75th Percentile (P75)", f"${profile_result.get('p75', 0):,.2f}"])

    stats_table = Table(stats_data, colWidths=[3.5 * inch, 3.0 * inch])
    stats_table.setStyle(_standard_table_style(courier_cols=[1]))
    story.append(stats_table)
    story.append(Spacer(1, 8))

    # Interpretive narrative for descriptive statistics
    mean_val = profile_result.get("mean_abs_balance", 0)
    median_val = profile_result.get("median_abs_balance", 0)
    std_val = profile_result.get("std_dev_abs_balance", 0)
    max_val = profile_result.get("max_abs_balance", 0)
    p25_val = profile_result.get("p25", 0)
    p75_val = profile_result.get("p75", 0)
    skew_direction = "right-skewed (positively skewed)" if mean_val > median_val else "left-skewed"
    cv = std_val / mean_val * 100 if mean_val > 0 else 0
    iqr = p75_val - p25_val

    story.append(
        Paragraph(
            f"The population exhibits a {skew_direction} distribution with a mean of "
            f"${mean_val:,.2f} versus a median of ${median_val:,.2f}. The coefficient of variation "
            f"({cv:.0f}%) indicates {'high' if cv > 100 else 'moderate'} dispersion relative to the mean. "
            f"The interquartile range (IQR) spans ${iqr:,.2f}, with the maximum account balance "
            f"of ${max_val:,.2f} representing a significant outlier at "
            f"{max_val / mean_val:.1f}x the mean.",
            styles["MemoBody"],
        )
    )
    story.append(Spacer(1, 12))

    # ── Data Quality Score Breakdown ──
    if data_quality:
        story.append(Paragraph("<b>Data Quality Score Breakdown</b>", styles["MemoBody"]))
        story.append(Spacer(1, 4))
        dq_data = [["Component", "Weight", "Score"]]
        dq_data.append(
            ["Completeness (missing names/balances)", "40%", f"{data_quality.get('completeness_score', 0):.1f}%"]
        )
        dq_data.append(["Normal Balance Compliance", "35%", f"{data_quality.get('violation_score', 0):.1f}%"])
        dq_data.append(["Active Balances (non-zero)", "25%", f"{data_quality.get('zero_balance_score', 0):.1f}%"])
        dq_data.append(["Overall Score", "", f"{data_quality.get('overall_score', 0):.1f}%"])

        dq_table = Table(dq_data, colWidths=[3.5 * inch, 1.0 * inch, 2.0 * inch])
        dq_style = _standard_table_style(courier_cols=[2])
        # Bold the totals row
        dq_style.add("FONTNAME", (0, -1), (-1, -1), "Times-Bold")
        dq_style.add("LINEABOVE", (0, -1), (-1, -1), 1, ClassicalColors.OBSIDIAN_DEEP)
        dq_table.setStyle(dq_style)
        story.append(dq_table)
        story.append(Spacer(1, 8))

    # ── III. MAGNITUDE DISTRIBUTION ──
    buckets = profile_result.get("buckets", [])
    if buckets:
        story.append(Paragraph("III. Magnitude Distribution", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))

        bucket_data = [["Bucket", "Count", "% of Accounts", "Sum of Balances"]]
        for b in buckets:
            if isinstance(b, dict):
                bucket_data.append(
                    [
                        b.get("label", ""),
                        str(b.get("count", 0)),
                        f"{b.get('percent_count', 0):.1f}%",
                        f"${b.get('sum_abs', 0):,.2f}",
                    ]
                )

        # Verification row: bucket sums should equal total
        bucket_total = sum(b.get("sum_abs", 0) for b in buckets if isinstance(b, dict))
        bucket_data.append(["Total", str(account_count), "100.0%", f"${bucket_total:,.2f}"])

        bucket_table = Table(bucket_data, colWidths=[1.8 * inch, 1.0 * inch, 1.5 * inch, 2.2 * inch])
        b_style = _standard_table_style(courier_cols=[1, 3])
        b_style.add("FONTNAME", (0, -1), (-1, -1), "Times-Bold")
        b_style.add("LINEABOVE", (0, -1), (-1, -1), 1, ClassicalColors.OBSIDIAN_DEEP)
        bucket_table.setStyle(b_style)
        story.append(bucket_table)
        story.append(Spacer(1, 6))

        # Interpretive narrative for magnitude distribution
        large_buckets = [b for b in buckets if isinstance(b, dict) and b.get("label", "") in (">$1M", "$100K–$1M")]
        large_count = sum(b.get("count", 0) for b in large_buckets)
        large_sum = sum(b.get("sum_abs", 0) for b in large_buckets)
        large_pct = large_sum / bucket_total * 100 if bucket_total > 0 else 0

        small_buckets = [b for b in buckets if isinstance(b, dict) and b.get("label", "") in ("Zero (<$0.01)", "<$1K")]
        small_count = sum(b.get("count", 0) for b in small_buckets)

        story.append(
            Paragraph(
                f"Accounts with balances exceeding $100,000 ({large_count} accounts, "
                f"{large_pct:.1f}% of total population value) warrant substantive audit "
                f"attention. Conversely, {small_count} account(s) fall below $1,000 — "
                "these may represent immaterial balances that can be addressed through "
                "analytical procedures rather than detailed testing.",
                styles["MemoBody"],
            )
        )
        story.append(Spacer(1, 16))

    # ── IV. CONCENTRATION ANALYSIS ──
    top_accounts = profile_result.get("top_accounts", [])
    story.append(Paragraph("IV. Concentration Analysis", styles["MemoSection"]))
    story.append(LedgerRule(doc_width))

    # Gini callout
    story.append(
        Paragraph(
            f"The Gini coefficient of <b>{gini:.4f}</b> indicates <b>{gini_interp}</b> concentration. "
            "A Gini of 0 means all accounts have equal balances; 1.0 means one account holds all value. "
            "Higher concentration warrants targeted substantive procedures on dominant accounts.",
            styles["MemoBody"],
        )
    )
    story.append(Spacer(1, 6))

    if top_accounts:
        # Check if any account has account_number
        has_acct_nums = any(t.get("account_number") for t in top_accounts if isinstance(t, dict))

        if has_acct_nums:
            top_data = [["Rank", "Account #", "Account", "Category", "Net Balance", "% of Total"]]
            for t in top_accounts:
                if isinstance(t, dict):
                    top_data.append(
                        [
                            str(t.get("rank", "")),
                            str(t.get("account_number", "")),
                            Paragraph(str(t.get("account", "")), styles["MemoTableCell"]),
                            t.get("category", "Unknown"),
                            f"${t.get('net_balance', 0):,.2f}",
                            f"{t.get('percent_of_total', 0):.1f}%",
                        ]
                    )
            top_table = Table(
                top_data,
                colWidths=[0.4 * inch, 0.7 * inch, 2.1 * inch, 1.0 * inch, 1.5 * inch, 0.8 * inch],
                repeatRows=1,
            )
        else:
            top_data = [["Rank", "Account", "Category", "Net Balance", "% of Total"]]
            for t in top_accounts:
                if isinstance(t, dict):
                    top_data.append(
                        [
                            str(t.get("rank", "")),
                            Paragraph(str(t.get("account", "")), styles["MemoTableCell"]),
                            t.get("category", "Unknown"),
                            f"${t.get('net_balance', 0):,.2f}",
                            f"{t.get('percent_of_total', 0):.1f}%",
                        ]
                    )
            top_table = Table(
                top_data,
                colWidths=[0.5 * inch, 2.5 * inch, 1.2 * inch, 1.5 * inch, 0.8 * inch],
                repeatRows=1,
            )

        net_col = 5 if has_acct_nums else 4
        top_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                    ("FONTNAME", (0, 1), (-1, -1), "Times-Roman"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                    ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                    ("LINEBELOW", (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                    ("ALIGN", (0, 0), (0, -1), "CENTER"),
                    ("ALIGN", (net_col - 1, 0), (-1, -1), "RIGHT"),
                    ("FONTNAME", (net_col - 1, 1), (net_col - 1, -1), "Courier"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("LEFTPADDING", (0, 0), (0, -1), 0),
                ]
            )
        )
        story.append(top_table)
        story.append(Spacer(1, 6))

        # Cumulative concentration narrative
        if len(top_accounts) >= 2:
            cum_pct = sum(t.get("percent_of_total", 0) for t in top_accounts[:5] if isinstance(t, dict))
            story.append(
                Paragraph(
                    f"The top {min(len(top_accounts), 5)} accounts collectively represent "
                    f"{cum_pct:.1f}% of total population value. Per AU-C Section 520, this level "
                    "of concentration requires the auditor to evaluate whether analytical procedures "
                    "alone provide sufficient appropriate audit evidence or whether substantive "
                    "testing of individual balances is necessary.",
                    styles["MemoBody"],
                )
            )

    story.append(Spacer(1, 16))

    # ── IV-A. ACCOUNT TYPE STRATIFICATION ──
    stratification = profile_result.get("account_type_stratification", [])
    if stratification:
        story.append(Paragraph("IV-A. Account Type Stratification", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))

        strat_data = [["Account Type", "Count", "% of Accounts", "Total Balance", "% of Population"]]
        for s in stratification:
            if isinstance(s, dict):
                strat_data.append(
                    [
                        s.get("account_type", ""),
                        str(s.get("count", 0)),
                        f"{s.get('pct_of_accounts', 0):.1f}%",
                        f"${s.get('total_balance', 0):,.2f}",
                        f"{s.get('pct_of_population', 0):.1f}%",
                    ]
                )

        strat_table = Table(
            strat_data,
            colWidths=[1.5 * inch, 0.8 * inch, 1.3 * inch, 1.8 * inch, 1.3 * inch],
        )
        strat_table.setStyle(_standard_table_style(courier_cols=[1, 3]))
        story.append(strat_table)
        story.append(Spacer(1, 6))

        # Flag disproportionate types (>40% of population value)
        disproportionate = [s for s in stratification if isinstance(s, dict) and s.get("pct_of_population", 0) > 40]
        if disproportionate:
            names = ", ".join(s.get("account_type", "") for s in disproportionate)
            story.append(
                Paragraph(
                    f"<i>Note: {names} account(s) represent a disproportionate share "
                    f"(&gt; 40%) of total population value, warranting focused analytical procedures.</i>",
                    styles["MemoBody"],
                )
            )
        else:
            story.append(
                Paragraph(
                    "<i>No single account type exceeds 40% of total population value.</i>",
                    styles["MemoBody"],
                )
            )
        story.append(Spacer(1, 16))

    # ── IV-B. BENFORD'S LAW ANALYSIS ──
    benford = profile_result.get("benford_analysis")
    if benford:
        story.append(Paragraph("IV-B. Benford's Law — First Digit Analysis", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))

        story.append(
            Paragraph(
                "Benford's Law predicts the frequency of leading digits in naturally occurring numerical "
                "datasets. Significant deviation from expected frequencies can indicate data anomalies "
                "warranting further investigation.",
                styles["MemoBody"],
            )
        )
        story.append(Spacer(1, 6))

        if benford.get("passed_prechecks"):
            expected = benford.get("expected_distribution", {})
            actual = benford.get("actual_distribution", {})
            deviation = benford.get("deviation_by_digit", {})

            benford_data = [["Digit", "Expected %", "Observed %", "Variance"]]
            for d in range(1, 10):
                d_str = str(d)
                exp_pct = expected.get(d_str, 0) * 100
                act_pct = actual.get(d_str, 0) * 100
                dev = deviation.get(d_str, 0) * 100
                # Flag digits with deviation > ±5 percentage points
                flag = " *" if abs(dev) > 5 else ""
                benford_data.append(
                    [
                        str(d),
                        f"{exp_pct:.1f}%",
                        f"{act_pct:.1f}%",
                        f"{dev:+.1f}pp{flag}",
                    ]
                )

            benford_table = Table(
                benford_data,
                colWidths=[1.0 * inch, 1.8 * inch, 1.8 * inch, 1.9 * inch],
            )
            benford_table.setStyle(_standard_table_style(courier_cols=[1, 2, 3]))
            story.append(benford_table)
            story.append(Spacer(1, 6))

            # Chi-square and conformance
            chi_sq = benford.get("chi_squared", 0)
            mad = benford.get("mad", 0)
            conformity = benford.get("conformity_level", "unknown")
            conformity_display = conformity.replace("_", " ").title()

            story.append(
                Paragraph(
                    f"Chi-square statistic: <b>{chi_sq:.3f}</b> &nbsp;|&nbsp; "
                    f"MAD: <b>{mad:.5f}</b> &nbsp;|&nbsp; "
                    f"Conformance: <b>{conformity_display}</b>",
                    styles["MemoBody"],
                )
            )
            story.append(Spacer(1, 4))

            # Conformance interpretation
            eligible = benford.get("eligible_count", 0)
            total_benford = benford.get("total_count", 0)
            story.append(
                Paragraph(
                    f"Analysis performed on {eligible:,} of {total_benford:,} accounts "
                    f"(zero-balance accounts excluded). The MAD (Mean Absolute Deviation) "
                    "conformity thresholds follow Nigrini (2012): Conforming (&lt; 0.006), "
                    "Acceptable (&lt; 0.012), Marginally Acceptable (&lt; 0.015), "
                    "Nonconforming (≥ 0.015). "
                    f"The chi-square critical value at p=0.05 with 8 degrees of freedom is 15.507.",
                    styles["MemoBody"],
                )
            )
            story.append(Spacer(1, 4))

            # Note flagged digits
            most_deviated = benford.get("most_deviated_digits", [])
            if most_deviated:
                digits_str = ", ".join(str(d) for d in most_deviated)
                story.append(
                    Paragraph(
                        f"<i>Most deviated digits: {digits_str}. "
                        "Asterisk (*) denotes deviation exceeding ±5 percentage points.</i>",
                        styles["MemoBody"],
                    )
                )
            else:
                story.append(
                    Paragraph(
                        "<i>No significant first-digit anomalies identified.</i>",
                        styles["MemoBody"],
                    )
                )
        else:
            precheck_msg = benford.get("precheck_message", "Prechecks not passed.")
            story.append(
                Paragraph(
                    f"<i>Benford analysis not performed: {precheck_msg}</i>",
                    styles["MemoBody"],
                )
            )
        story.append(Spacer(1, 16))

    # ── V. EXCEPTION FLAGS ──
    exceptions = profile_result.get("exception_flags")
    if exceptions:
        story.append(Paragraph("V. Exception Flags", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))

        # Section introduction
        viol_count = len(exceptions.get("normal_balance_violations", []))
        zero_count = len(exceptions.get("zero_balance_accounts", []))
        nz_count = len(exceptions.get("near_zero_accounts", []))
        dom_count = len(exceptions.get("dominant_accounts", []))
        total_flags = viol_count + zero_count + nz_count + dom_count
        story.append(
            Paragraph(
                f"This section identifies {total_flags} exception(s) across three categories: "
                f"normal balance violations ({viol_count}), zero/near-zero balances "
                f"({zero_count + nz_count}), and dominant account risk flags ({dom_count}). "
                "Each exception should be evaluated by the engagement team to determine "
                "whether it represents a data quality issue, an intentional accounting "
                "treatment (e.g., contra accounts), or a potential misstatement.",
                styles["MemoBody"],
            )
        )
        story.append(Spacer(1, 8))

        # V-A: Normal Balance Violations
        story.append(Paragraph("V-A. Normal Balance Violations", styles["MemoSection"]))
        story.append(Spacer(1, 4))
        story.append(
            Paragraph(
                "Under standard double-entry bookkeeping, assets and expenses carry debit (positive) "
                "normal balances, while liabilities, equity, and revenue carry credit (negative) "
                "normal balances. Accounts whose balance sign contradicts the expected direction "
                "may indicate contra accounts, reclassifications, or posting errors.",
                styles["MemoBody"],
            )
        )
        story.append(Spacer(1, 4))

        violations = exceptions.get("normal_balance_violations", [])
        if violations:
            viol_data = [["Account #", "Account Name", "Type", "Expected", "Actual", "Balance"]]
            for v in violations:
                if isinstance(v, dict):
                    viol_data.append(
                        [
                            v.get("account_number", ""),
                            Paragraph(v.get("account", ""), styles["MemoTableCell"]),
                            v.get("account_type", ""),
                            v.get("expected", ""),
                            v.get("actual", ""),
                            f"${v.get('balance', 0):,.2f}",
                        ]
                    )

            viol_table = Table(
                viol_data,
                colWidths=[0.7 * inch, 2.0 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch, 1.4 * inch],
            )
            viol_table.setStyle(_standard_table_style(right_align_from=5, courier_cols=[5]))
            story.append(viol_table)
        else:
            story.append(
                Paragraph(
                    "<i>No normal balance violations identified in the trial balance population.</i>",
                    styles["MemoBody"],
                )
            )
        story.append(Spacer(1, 8))

        # V-B: Zero and Near-Zero Balances
        story.append(Paragraph("V-B. Zero and Near-Zero Balances", styles["MemoSection"]))
        story.append(Spacer(1, 4))

        zeros = exceptions.get("zero_balance_accounts", [])
        near_zeros = exceptions.get("near_zero_accounts", [])

        if zeros or near_zeros:
            zn_data = [["Account #", "Account Name", "Type", "Balance", "Status"]]
            for z in zeros:
                if isinstance(z, dict):
                    zn_data.append(
                        [
                            z.get("account_number", ""),
                            Paragraph(z.get("account", ""), styles["MemoTableCell"]),
                            z.get("account_type", ""),
                            f"${z.get('balance', 0):,.2f}",
                            "Zero",
                        ]
                    )
            for z in near_zeros:
                if isinstance(z, dict):
                    zn_data.append(
                        [
                            z.get("account_number", ""),
                            Paragraph(z.get("account", ""), styles["MemoTableCell"]),
                            z.get("account_type", ""),
                            f"${z.get('balance', 0):,.2f}",
                            "Near-Zero",
                        ]
                    )

            zn_table = Table(
                zn_data,
                colWidths=[0.7 * inch, 2.3 * inch, 0.8 * inch, 1.4 * inch, 1.3 * inch],
            )
            zn_table.setStyle(_standard_table_style(right_align_from=3, courier_cols=[3]))
            story.append(zn_table)
        else:
            story.append(
                Paragraph(
                    "<i>No zero or near-zero balance accounts identified.</i>",
                    styles["MemoBody"],
                )
            )
        story.append(Spacer(1, 8))

        # V-C: Dominant Account Risk Flags
        story.append(Paragraph("V-C. Dominant Account Risk Flags", styles["MemoSection"]))
        story.append(Spacer(1, 4))

        dominant = exceptions.get("dominant_accounts", [])
        if dominant:
            dom_data = [["Account", "Balance", "% of Total", "Risk Note"]]
            for d in dominant:
                if isinstance(d, dict):
                    dom_data.append(
                        [
                            Paragraph(d.get("account", ""), styles["MemoTableCell"]),
                            f"${d.get('balance', 0):,.2f}",
                            f"{d.get('pct_of_total', 0):.1f}%",
                            Paragraph(d.get("risk_note", ""), styles["MemoTableCell"]),
                        ]
                    )

            dom_table = Table(
                dom_data,
                colWidths=[1.8 * inch, 1.4 * inch, 0.8 * inch, 2.5 * inch],
            )
            dom_table.setStyle(_standard_table_style(right_align_from=1, courier_cols=[1]))
            story.append(dom_table)

            story.append(Spacer(1, 4))
            story.append(
                Paragraph(
                    "<i>Note: The concentration analysis in Section IV also identifies top accounts. "
                    "This section provides separately rendered, actionable risk flags for accounts "
                    "exceeding 10% of total population value.</i>",
                    styles["MemoBody"],
                )
            )
        else:
            story.append(
                Paragraph(
                    "<i>No accounts exceed 10% of total population value.</i>",
                    styles["MemoBody"],
                )
            )
        story.append(Spacer(1, 16))

    # ── VI. SUGGESTED AUDIT PROCEDURES ──
    procedures = profile_result.get("suggested_procedures", [])
    if procedures:
        story.append(Paragraph("VI. Suggested Audit Procedures", styles["MemoSection"]))
        story.append(LedgerRule(doc_width))

        proc_data = [["Priority", "Area", "Procedure"]]
        for p in procedures:
            if isinstance(p, dict):
                proc_data.append(
                    [
                        p.get("priority", ""),
                        p.get("area", ""),
                        Paragraph(p.get("procedure", ""), styles["MemoTableCell"]),
                    ]
                )

        proc_table = Table(
            proc_data,
            colWidths=[0.7 * inch, 1.5 * inch, 4.3 * inch],
            repeatRows=1,
        )
        proc_style = _standard_table_style(right_align_from=99)  # No right align
        proc_table.setStyle(proc_style)
        story.append(proc_table)
        story.append(Spacer(1, 12))

    # ── Methodology & Authoritative References ──
    build_methodology_statement(
        story,
        styles,
        doc_width,
        tool_domain="population_profile",
        framework=resolved_framework,
        domain_label="population profile analysis",
    )
    build_authoritative_reference_block(
        story,
        styles,
        doc_width,
        tool_domain="population_profile",
        framework=resolved_framework,
        domain_label="population profile analysis",
    )

    # ── Workpaper Sign-Off ──
    build_workpaper_signoff(
        story, styles, doc_width, prepared_by, reviewed_by, workpaper_date, include_signoff=include_signoff
    )

    # ── Intelligence Stamp ──
    build_intelligence_stamp(story, styles, client_name=client_name, period_tested=period_tested)

    # ── Disclaimer ──
    build_disclaimer(
        story,
        styles,
        domain="population profile analysis",
        isa_reference="AU-C Section 520 (Analytical Procedures), AU-C Section 530 (Audit Sampling), and AS 2305 (Substantive Analytical Procedures)",
    )

    doc.build(story, onFirstPage=draw_page_footer)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
