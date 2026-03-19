"""
Diagnostic Intelligence Summary section renderers.

Contains all the section builders for the PaciolusReportGenerator
(generate_audit_report / generate_diagnostic_pdf): table of contents,
data intake summary, executive summary, population composition, risk
assessment, exception details, limitations, and the classical footer.
"""

from datetime import UTC, datetime

from reportlab.lib.units import inch
from reportlab.platypus import KeepTogether, Paragraph, Spacer, Table, TableStyle

from pdf.components import DoubleRule, LedgerRule, create_leader_dots
from pdf.styles import ClassicalColors

# ---------------------------------------------------------------------------
# Table of Contents
# ---------------------------------------------------------------------------


def render_table_of_contents(story: list, styles: dict) -> None:
    """Fix 5: Build a compact Table of Contents on page 2."""
    story.append(Paragraph("Table of Contents", styles["SectionHeader"]))
    story.append(LedgerRule(color=ClassicalColors.GOLD_INSTITUTIONAL, thickness=1))
    story.append(Spacer(1, 8))

    toc_entries = [
        "Data Intake Summary",
        "Executive Summary",
        "Population Composition",
        "Risk Assessment",
        "Exception Details",
        "Limitations",
    ]

    for i, entry in enumerate(toc_entries, 1):
        story.append(
            Paragraph(
                f"{i}. &nbsp;&nbsp;{entry}",
                styles["BodyText"],
            )
        )

    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            "<i>Page numbers are sequential from the cover page. "
            "Section ordering reflects the standard diagnostic report structure.</i>",
            styles["BodyText"],
        )
    )
    story.append(Spacer(1, 12))


# ---------------------------------------------------------------------------
# Data Intake Summary
# ---------------------------------------------------------------------------


def render_data_intake_summary(story: list, styles: dict, audit_result: dict, filename: str) -> None:
    """Fix 12: Data Intake Summary section."""
    story.append(Paragraph("Data Intake Summary", styles["SectionHeader"]))
    story.append(LedgerRule(color=ClassicalColors.OBSIDIAN_DEEP, thickness=1))
    story.append(Spacer(1, 4))

    row_count = audit_result.get("row_count", 0)
    col_detection = audit_result.get("column_detection", {})
    data_quality = audit_result.get("data_quality", {})

    rows_accepted = row_count
    rows_rejected = data_quality.get("rows_rejected", 0)
    null_accounts = data_quality.get("null_account_codes", 0)
    duplicates_detected = data_quality.get("duplicate_accounts", False)
    unrecognized_types = data_quality.get("unrecognized_types", 0)
    completeness = data_quality.get("completeness_score", 100)

    cell_style = styles["TableCell"]
    header_style = styles["TableHeader"]

    intake_data = [
        [Paragraph("Field", header_style), Paragraph("Value", header_style)],
        [Paragraph("File Received", cell_style), Paragraph(filename or "\u2014", cell_style)],
        [Paragraph("Rows Submitted", cell_style), Paragraph(f"{row_count + rows_rejected:,}", cell_style)],
        [Paragraph("Rows Accepted", cell_style), Paragraph(f"{rows_accepted:,}", cell_style)],
        [Paragraph("Rows Rejected / Skipped", cell_style), Paragraph(str(rows_rejected), cell_style)],
        [Paragraph("Null / Blank Account Codes", cell_style), Paragraph(str(null_accounts), cell_style)],
        [
            Paragraph("Duplicate Account Codes", cell_style),
            Paragraph("Yes" if duplicates_detected else "No", cell_style),
        ],
        [Paragraph("Unrecognized Account Types", cell_style), Paragraph(str(unrecognized_types), cell_style)],
        [Paragraph("Data Completeness", cell_style), Paragraph(f"{completeness:.0f}%", cell_style)],
    ]

    if col_detection:
        confidence = col_detection.get("overall_confidence", 0)
        if isinstance(confidence, (int, float)):
            intake_data.append(
                [
                    Paragraph("Column Detection Confidence", cell_style),
                    Paragraph(f"{confidence:.0%}", cell_style),
                ]
            )

    intake_table = Table(intake_data, colWidths=[3.0 * inch, 3.5 * inch], repeatRows=1)
    intake_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                ("LINEBELOW", (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (0, -1), 0),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [ClassicalColors.WHITE, ClassicalColors.OATMEAL_PAPER]),
            ]
        )
    )
    story.append(intake_table)

    if rows_rejected == 0 and null_accounts == 0 and not duplicates_detected:
        story.append(Spacer(1, 4))
        story.append(
            Paragraph(
                "<i>No data quality issues were identified during intake processing.</i>",
                styles["BodyText"],
            )
        )

    story.append(Spacer(1, 12))


# ---------------------------------------------------------------------------
# Executive Summary
# ---------------------------------------------------------------------------


def render_executive_summary(story: list, styles: dict, audit_result: dict) -> None:
    """Build the executive summary with leader dots and status badge."""
    story.append(Paragraph("Executive Summary", styles["SectionHeader"]))
    story.append(LedgerRule(color=ClassicalColors.OBSIDIAN_DEEP, thickness=1))

    # Fix 8: Formal Trial Balance Status indicator
    is_balanced = audit_result.get("balanced", False)
    difference = audit_result.get("difference", 0)

    if is_balanced:
        status_label = "BALANCED"
        status_detail = f"Debits equal Credits (${abs(difference):,.2f} variance)"
        badge_border = ClassicalColors.SAGE
        status_style = "BalancedStatus"
    else:
        status_label = "OUT OF BALANCE"
        status_detail = f"Variance of ${abs(difference):,.2f} identified"
        badge_border = ClassicalColors.CLAY
        status_style = "UnbalancedStatus"

    badge_data = [
        [Paragraph(f"\u2713  {status_label}", styles[status_style])],
        [Paragraph(status_detail, styles["BodyText"])],
    ]
    badge_table = Table(badge_data, colWidths=[5 * inch])
    badge_table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1.5, badge_border),
                ("TOPPADDING", (0, 0), (0, 0), 8),
                ("BOTTOMPADDING", (0, -1), (-1, -1), 8),
                ("TOPPADDING", (0, 1), (0, 1), 2),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("BACKGROUND", (0, 0), (-1, -1), ClassicalColors.OATMEAL_PAPER),
            ]
        )
    )
    badge_table.hAlign = "CENTER"

    story.append(Spacer(1, 8))
    story.append(badge_table)
    story.append(Spacer(1, 10))

    # Financial summary with leader dots
    total_debits = audit_result.get("total_debits", 0)
    total_credits = audit_result.get("total_credits", 0)
    difference = audit_result.get("difference", 0)
    row_count = audit_result.get("row_count", 0)
    threshold = audit_result.get("materiality_threshold", 0)

    leader_lines = [
        create_leader_dots("Total Debits", f"${total_debits:,.2f}"),
        create_leader_dots("Total Credits", f"${total_credits:,.2f}"),
        create_leader_dots("Variance", f"${difference:,.2f}"),
        create_leader_dots("Rows Analyzed", f"{row_count:,}"),
        create_leader_dots("Materiality Threshold", f"${threshold:,.2f}"),
    ]

    if audit_result.get("is_consolidated"):
        sheet_count = audit_result.get("sheet_count", 0)
        leader_lines.append(create_leader_dots("Sheets Consolidated", str(sheet_count)))

    for line in leader_lines:
        story.append(Paragraph(line, styles["LeaderLine"]))

    story.append(Spacer(1, 12))

    # Change 2: Risk-Weighted Coverage metric
    if total_debits > 0:
        abnormal_balances = audit_result.get("abnormal_balances", [])
        material_items = [ab for ab in abnormal_balances if ab.get("materiality") == "material"]
        flagged_value = sum(abs(ab.get("amount", 0)) for ab in material_items)
        coverage_pct = flagged_value / total_debits * 100 if total_debits else 0
        # Sprint 526 Fix 5: Cap coverage at 100%
        coverage_pct = min(coverage_pct, 100.0)

        coverage_lines = [
            create_leader_dots("Flagged Value (Material)", f"${flagged_value:,.2f}"),
            create_leader_dots("Total TB Population", f"${total_debits:,.2f}"),
            create_leader_dots("Risk-Weighted Coverage", f"{coverage_pct:.1f}%"),
        ]
        for line in coverage_lines:
            story.append(Paragraph(line, styles["LeaderLine"]))

        if flagged_value > 0:
            note = (
                f"Material exceptions affect {coverage_pct:.1f}% of total trial balance value "
                f"by amount. Accounts above materiality threshold warrant corroborating "
                f"procedures before conclusions can be drawn."
            )
        else:
            note = "Risk-Weighted Coverage: 0.0% \u2014 No material exceptions identified."
        story.append(Spacer(1, 2))
        story.append(Paragraph(note, styles["BodyText"]))
        story.append(Spacer(1, 6))


# ---------------------------------------------------------------------------
# Population Composition
# ---------------------------------------------------------------------------


def render_population_composition(story: list, styles: dict, audit_result: dict) -> None:
    """Build the Population Composition section (Change 5)."""
    category_totals = audit_result.get("category_totals", {})
    if not category_totals:
        return

    row_count = audit_result.get("row_count", 0)

    type_mapping = [
        ("Asset", category_totals.get("total_assets", 0)),
        ("Liability", category_totals.get("total_liabilities", 0)),
        ("Equity", category_totals.get("total_equity", 0)),
        ("Revenue", category_totals.get("total_revenue", 0)),
        ("Expense", category_totals.get("total_expenses", 0)),
    ]

    grand_balance = sum(abs(v) for _, v in type_mapping)
    if grand_balance <= 0:
        return

    pop_profile = audit_result.get("population_profile", {})
    section_density = pop_profile.get("section_density", [])

    density_counts: dict[str, int] = {}
    for sd in section_density:
        label = sd.get("section_label", "")
        count = sd.get("account_count", 0)
        if "Asset" in label:
            density_counts["Asset"] = density_counts.get("Asset", 0) + count
        elif "Liabilit" in label:
            density_counts["Liability"] = density_counts.get("Liability", 0) + count
        elif "Equity" in label:
            density_counts["Equity"] = density_counts.get("Equity", 0) + count
        elif "Revenue" in label:
            density_counts["Revenue"] = density_counts.get("Revenue", 0) + count
        elif "Cost" in label or "Expense" in label or "Other" in label:
            density_counts["Expense"] = density_counts.get("Expense", 0) + count

    type_rows: list[tuple[str, int, float, float]] = []
    classified_count = sum(density_counts.values())
    unclassified_count = max(0, row_count - classified_count) if density_counts else 0

    for type_name, balance in type_mapping:
        count = density_counts.get(type_name, 0)
        abs_balance = abs(balance)
        pct = abs_balance / grand_balance * 100
        type_rows.append((type_name, count, abs_balance, pct))

    if unclassified_count > 0:
        type_rows.append(("Other / Unclassified", unclassified_count, 0.0, 0.0))

    if not any(r[2] > 0 for r in type_rows):
        return

    story.append(Paragraph("Population Composition", styles["SectionHeader"]))
    story.append(LedgerRule(color=ClassicalColors.OBSIDIAN_DEEP, thickness=1))
    story.append(Spacer(1, 4))

    cell_style = styles["TableCell"]
    header_style = styles["TableHeader"]

    table_data = [
        [
            Paragraph("Account Type", header_style),
            Paragraph("Count", header_style),
            Paragraph("Gross Balance", header_style),
            Paragraph("% of Gross Total", header_style),
        ]
    ]

    total_count = 0
    for type_name, count, balance, pct in type_rows:
        total_count += count
        table_data.append(
            [
                Paragraph(type_name, cell_style),
                Paragraph(str(count) if count > 0 else "\u2014", cell_style),
                Paragraph(f"${balance:,.2f}", cell_style),
                Paragraph(f"{pct:.1f}%", cell_style),
            ]
        )

    table_data.append(
        [
            Paragraph("Total", styles["TableHeader"]),
            Paragraph(str(total_count) if total_count > 0 else str(row_count), styles["TableHeader"]),
            Paragraph(f"${grand_balance:,.2f}", styles["TableHeader"]),
            Paragraph("100.0%", styles["TableHeader"]),
        ]
    )

    comp_table = Table(
        table_data,
        colWidths=[1.8 * inch, 0.8 * inch, 2.2 * inch, 1.2 * inch],
        repeatRows=1,
    )
    comp_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
                ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
                ("LINEBELOW", (0, 1), (-1, -2), 0.25, ClassicalColors.LEDGER_RULE),
                ("LINEABOVE", (0, -1), (-1, -1), 1, ClassicalColors.OBSIDIAN_600),
                ("FONTNAME", (0, -1), (-1, -1), "Times-Bold"),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -2), [ClassicalColors.WHITE, ClassicalColors.OATMEAL_PAPER]),
            ]
        )
    )

    story.append(comp_table)

    gross_footnote = (
        "Gross Balance represents the sum of absolute account-level balances within each type. "
        "This column is not additive to a net trial balance total, as it includes both "
        "debit and credit balances without netting."
    )
    story.append(Spacer(1, 2))
    story.append(Paragraph(f"<i>{gross_footnote}</i>", styles["BodyText"]))

    col_detection = audit_result.get("column_detection", {})
    if col_detection:
        acct_confidence = col_detection.get("account_confidence", 1.0)
        if acct_confidence < 0.9:
            footnote = (
                f"Account type classification based on {acct_confidence:.0%} column confidence. "
                f"Unclassified accounts are excluded from type-specific tests."
            )
            story.append(Spacer(1, 2))
            story.append(Paragraph(f"<i>{footnote}</i>", styles["BodyText"]))

    story.append(Spacer(1, 6))


# ---------------------------------------------------------------------------
# Risk Assessment
# ---------------------------------------------------------------------------


def render_risk_summary(story: list, styles: dict, audit_result: dict) -> None:
    """Build the risk summary section with composite risk score."""
    from shared.memo_base import RISK_SCALE_LEGEND, RISK_TIER_DISPLAY
    from shared.tb_diagnostic_constants import compute_tb_risk_score, get_risk_tier

    story.append(Paragraph("Risk Assessment", styles["SectionHeader"]))
    story.append(LedgerRule(color=ClassicalColors.OBSIDIAN_DEEP, thickness=1))
    story.append(Spacer(1, 6))

    risk_summary = audit_result.get("risk_summary", {})
    material_count = audit_result.get("material_count", 0)
    immaterial_count = audit_result.get("immaterial_count", 0)
    informational_count = audit_result.get("informational_count", 0)
    total_anomalies = risk_summary.get("total_anomalies", material_count + immaterial_count + informational_count)
    high_severity = risk_summary.get("high_severity", material_count)
    low_severity = risk_summary.get("low_severity", immaterial_count)
    informational_severity = risk_summary.get("informational_count", informational_count)

    # Change 3: Composite Diagnostic Score
    abnormal_balances = audit_result.get("abnormal_balances", [])
    anomaly_types = risk_summary.get("anomaly_types", {})
    has_suspense = anomaly_types.get("suspense_account", 0) > 0
    has_credit_balance = any(
        ab.get("anomaly_type") in ("abnormal_balance", "natural_balance_violation")
        and ab.get("type", "").lower() == "asset"
        for ab in abnormal_balances
    )

    total_debits = audit_result.get("total_debits", 0)
    material_items = [ab for ab in abnormal_balances if ab.get("materiality") == "material"]
    flagged_value = sum(abs(ab.get("amount", 0)) for ab in material_items)
    coverage_pct = flagged_value / total_debits * 100 if total_debits > 0 else 0

    # Sprint 526 Fix 5: Use pre-computed score from API response when available
    pre_computed_score = risk_summary.get("risk_score")
    pre_computed_factors = risk_summary.get("risk_factors")
    if pre_computed_score is not None and pre_computed_factors is not None:
        risk_score = pre_computed_score
        risk_factors = [(name, pts) for name, pts in pre_computed_factors]
    else:
        risk_score, risk_factors = compute_tb_risk_score(
            material_count,
            immaterial_count,
            coverage_pct,
            has_suspense,
            has_credit_balance,
            abnormal_balances=abnormal_balances,
            informational_count=informational_count,
        )
    risk_tier = get_risk_tier(risk_score)
    base_tier_label, _ = RISK_TIER_DISPLAY.get(str(risk_tier).lower(), ("UNKNOWN", ClassicalColors.OBSIDIAN_500))
    tier_label = f"{base_tier_label} ({risk_score:.0f}/100)"

    score_lines = [
        create_leader_dots("Composite Diagnostic Score", f"{risk_score} / 100"),
        create_leader_dots("Diagnostic Tier", tier_label),
    ]
    for line in score_lines:
        story.append(Paragraph(line, styles["LeaderLine"]))
    story.append(Paragraph(RISK_SCALE_LEGEND, styles["BodyText"]))

    if risk_factors:
        story.append(Spacer(1, 4))
        story.append(Paragraph("<b>Score Decomposition</b>", styles["BodyText"]))
        for factor_name, contribution in risk_factors:
            story.append(
                Paragraph(
                    create_leader_dots(f"  {factor_name}", f"+{contribution}"),
                    styles["LeaderLine"],
                )
            )
        story.append(LedgerRule(color=ClassicalColors.LEDGER_RULE, thickness=0.5))
        story.append(
            Paragraph(
                create_leader_dots("  <b>Total (capped at 100)</b>", f"<b>{risk_score}</b>"),
                styles["LeaderLine"],
            )
        )

    story.append(Spacer(1, 6))

    # Risk metrics table (Sprint 537: 4-column with informational)
    risk_data = [
        ["Total Findings", "Material Exceptions", "Minor Observations", "Informational Notes"],
        [str(total_anomalies), str(high_severity), str(low_severity), str(informational_severity)],
    ]

    risk_table = Table(risk_data, colWidths=[1.5 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch])
    risk_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Times-Roman"),
                ("FONTSIZE", (0, 0), (-1, 0), 8),
                ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_500),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("FONTNAME", (0, 1), (-1, 1), "Times-Bold"),
                ("FONTSIZE", (0, 1), (-1, 1), 22),
                ("TEXTCOLOR", (0, 1), (0, 1), ClassicalColors.OBSIDIAN_DEEP),
                ("TEXTCOLOR", (1, 1), (1, 1), ClassicalColors.CLAY),
                ("TEXTCOLOR", (2, 1), (2, 1), ClassicalColors.OBSIDIAN_500),
                ("TEXTCOLOR", (3, 1), (3, 1), ClassicalColors.LEDGER_RULE),
                ("ALIGN", (0, 1), (-1, 1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )

    story.append(risk_table)
    story.append(Spacer(1, 6))


# ---------------------------------------------------------------------------
# Exception Details (Anomalies)
# ---------------------------------------------------------------------------


def render_anomaly_details(story: list, styles: dict, audit_result: dict) -> None:
    """Build the anomaly details with ledger-style tables."""
    abnormal_balances = audit_result.get("abnormal_balances", [])

    if not abnormal_balances:
        story.append(Paragraph("No exceptions identified. The trial balance appears sound.", styles["BodyText"]))
        return

    story.append(Paragraph("Exception Details", styles["SectionHeader"]))
    story.append(LedgerRule(color=ClassicalColors.OBSIDIAN_DEEP, thickness=1))
    story.append(Spacer(1, 4))

    # Separate by materiality / severity tier (Sprint 537: three tiers)
    material = [ab for ab in abnormal_balances if ab.get("materiality") == "material"]
    informational = [ab for ab in abnormal_balances if ab.get("severity") == "informational"]
    immaterial = [
        ab
        for ab in abnormal_balances
        if ab.get("materiality") == "immaterial" and ab.get("severity") != "informational"
    ]

    # Fix 3: Sort findings by absolute amount descending within each tier
    material.sort(key=lambda ab: abs(ab.get("amount", 0)), reverse=True)
    immaterial.sort(key=lambda ab: abs(ab.get("amount", 0)), reverse=True)
    informational.sort(key=lambda ab: abs(ab.get("amount", 0)), reverse=True)

    if material:
        story.append(Paragraph(f"Material Exceptions ({len(material)})", styles["SubsectionHeader"]))
        story.append(_create_ledger_table(styles, material, is_material=True))
        story.append(Spacer(1, 10))

    if immaterial:
        story.append(Paragraph(f"Minor Observations ({len(immaterial)})", styles["SubsectionHeader"]))
        story.append(_create_ledger_table(styles, immaterial, is_material=False))
        story.append(Spacer(1, 10))

    if informational:
        story.append(Paragraph(f"Informational Notes ({len(informational)})", styles["SubsectionHeader"]))
        story.append(
            Paragraph(
                "<i>Informational Notes are surfaced for practitioner awareness and require no "
                "immediate procedure. They may be relevant in the context of expanded procedures "
                "or other findings.</i>",
                styles["BodyText"],
            )
        )
        story.append(Spacer(1, 4))
        story.append(_create_informational_table(styles, informational))


def _create_ledger_table(styles: dict, anomalies: list, is_material: bool) -> KeepTogether:
    """Create a ledger-style table with horizontal rules only."""
    from shared.tb_diagnostic_constants import get_concentration_benchmark, get_tb_suggested_procedure

    cell_style = styles["TableCell"]
    header_style = styles["TableHeader"]

    data = [
        [
            Paragraph("Rank", header_style),
            Paragraph("Ref", header_style),
            Paragraph("Account", header_style),
            Paragraph("Nature of Exception", header_style),
            Paragraph("Amount", header_style),
        ]
    ]

    ref_prefix = "TB-M" if is_material else "TB-I"

    total_amount = 0
    has_pattern_based = False
    for idx, ab in enumerate(anomalies, start=1):
        ref_num = f"{ref_prefix}{idx:03d}"

        account = ab.get("account", "Unknown")
        if ab.get("sheet_name"):
            account = f"{account} ({ab['sheet_name']})"

        acc_type = ab.get("type", "Unknown")

        issue_text = ab.get("issue", "")
        issue_parts = [f"<b>{issue_text}</b>"]
        issue_parts.append(f'<br/><font size="7" color="#616161"><i>{acc_type}</i></font>')

        benchmark = get_concentration_benchmark(ab)
        if benchmark:
            issue_parts.append(f'<br/><font size="7" color="#616161"><i>{benchmark}</i></font>')

        cross_ref = ab.get("cross_reference_note")
        if cross_ref:
            issue_parts.append(f'<br/><font size="7" color="#4A7C59"><i>{cross_ref}</i></font>')

        procedure = get_tb_suggested_procedure(ab, is_material=is_material, rotation_index=idx)
        issue_parts.append(f'<br/><font size="7"><i>Suggested Procedure: {procedure}</i></font>')

        issue_cell = Paragraph("".join(issue_parts), cell_style)

        amount = ab.get("amount", 0)
        total_amount += amount

        anomaly_type = ab.get("anomaly_type", "")
        amount_display = f"${amount:,.2f}"
        if anomaly_type == "rounding_anomaly":
            txn_count = ab.get("transaction_count")
            if txn_count and txn_count > 1:
                per_txn = ab.get("per_transaction_amount")
                if per_txn is None and amount != 0:
                    per_txn = abs(amount) / txn_count
                if per_txn is not None:
                    amount_display += (
                        f'<br/><font size="6"><i>({txn_count} transactions \u00d7 ${per_txn:,.2f})</i></font>'
                    )
                else:
                    amount_display += f'<br/><font size="6"><i>(sum of {txn_count} flagged transactions)</i></font>'
                has_pattern_based = True

        rank_label = f"P{idx}"

        data.append(
            [
                Paragraph(f"<b>{rank_label}</b>", cell_style),
                Paragraph(ref_num, cell_style),
                Paragraph(account, cell_style),
                issue_cell,
                Paragraph(amount_display, cell_style),
            ]
        )

    data.append(
        [
            Paragraph("", cell_style),
            Paragraph("", cell_style),
            Paragraph("", cell_style),
            Paragraph("TOTAL", styles["TableHeader"]),
            Paragraph(f"${total_amount:,.2f}", styles["TableHeader"]),
        ]
    )

    table = Table(data, colWidths=[0.5 * inch, 0.6 * inch, 1.3 * inch, 2.6 * inch, 1.0 * inch], repeatRows=1)

    table_elements = []

    accent_color = ClassicalColors.CLAY if is_material else ClassicalColors.OBSIDIAN_500

    style_commands = [
        ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
        ("LINEBELOW", (0, 0), (-1, 0), 1, ClassicalColors.OBSIDIAN_DEEP),
        ("LINEBELOW", (0, 1), (-1, -2), 0.25, ClassicalColors.LEDGER_RULE),
        ("LINEABOVE", (0, -1), (-1, -1), 1, ClassicalColors.OBSIDIAN_600),
        ("FONTNAME", (-2, -1), (-1, -1), "Times-Bold"),
        ("LINEBEFORE", (0, 1), (0, -1), 2, accent_color),
        ("ALIGN", (-1, 0), (-1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (0, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [ClassicalColors.WHITE, ClassicalColors.OATMEAL_PAPER]),
    ]

    table.setStyle(TableStyle(style_commands))
    table_elements.append(table)

    table_elements.append(Spacer(1, 2))
    table_elements.append(
        Paragraph(
            '<i><font size="7">Amounts shown reflect signed balances. '
            "Negative values indicate credit-balance findings. "
            "Amount represents account balance unless otherwise noted.</font></i>",
            styles["BodyText"],
        )
    )

    if has_pattern_based:
        table_elements.append(
            Paragraph(
                '<i><font size="7">For pattern-based findings (e.g., round-number anomalies), '
                "the amount shown may represent the sum of flagged transactions rather than "
                "the account balance.</font></i>",
                styles["BodyText"],
            )
        )

    return KeepTogether(table_elements)


def _create_informational_table(styles: dict, anomalies: list) -> KeepTogether:
    """Sprint 537: Compact table for informational notes."""
    cell_style = styles["TableCell"]
    header_style = styles["TableHeader"]

    data = [
        [
            Paragraph("Ref", header_style),
            Paragraph("Account", header_style),
            Paragraph("Nature of Note", header_style),
            Paragraph("Amount", header_style),
        ]
    ]

    for idx, ab in enumerate(anomalies, start=1):
        ref_num = f"TB-N{idx:03d}"
        account = ab.get("account", "Unknown")
        issue_text = ab.get("issue", "")
        acc_type = ab.get("type", "Unknown")
        issue_cell = Paragraph(
            f'{issue_text}<br/><font size="7" color="#616161"><i>{acc_type}</i></font>',
            cell_style,
        )
        amount = ab.get("amount", 0)
        data.append(
            [
                Paragraph(ref_num, cell_style),
                Paragraph(account, cell_style),
                issue_cell,
                Paragraph(f"${amount:,.2f}", cell_style),
            ]
        )

    table = Table(data, colWidths=[0.6 * inch, 1.5 * inch, 3.0 * inch, 0.9 * inch], repeatRows=1)
    style_commands = [
        ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("TEXTCOLOR", (0, 0), (-1, 0), ClassicalColors.OBSIDIAN_DEEP),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, ClassicalColors.OBSIDIAN_500),
        ("LINEBELOW", (0, 1), (-1, -1), 0.25, ClassicalColors.LEDGER_RULE),
        ("LINEBEFORE", (0, 1), (0, -1), 1, ClassicalColors.LEDGER_RULE),
        ("ALIGN", (-1, 0), (-1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [ClassicalColors.WHITE, ClassicalColors.OATMEAL_PAPER]),
    ]
    table.setStyle(TableStyle(style_commands))
    return KeepTogether([table])


# ---------------------------------------------------------------------------
# Limitations
# ---------------------------------------------------------------------------


def render_limitations(story: list, styles: dict) -> None:
    """Fix 10: Build the formal Limitations section on the final page."""
    story.append(Spacer(1, 16))
    story.append(Paragraph("Limitations", styles["SectionHeader"]))
    story.append(LedgerRule(color=ClassicalColors.OBSIDIAN_DEEP, thickness=1))
    story.append(Spacer(1, 4))

    limitation_text = (
        "This report was prepared using Paciolus Diagnostic Intelligence and is intended to "
        "support the professional judgment of the engagement practitioner. The procedures "
        "reflected herein are analytical and diagnostic in nature and do not constitute an "
        "audit, review, compilation, or attestation engagement as defined under AICPA "
        "professional standards or PCAOB auditing standards. Findings and observations "
        "require independent corroboration before conclusions may be drawn."
    )
    story.append(Paragraph(limitation_text, styles["BodyText"]))
    story.append(Spacer(1, 6))

    practitioner_text = (
        "Practitioner information appearing on the cover of this report is provided by the "
        "user and reflects the engagement team responsible for applying professional judgment "
        "to this output. Paciolus does not review, endorse, certify, or assume responsibility "
        "for conclusions drawn by the engagement practitioner. The presence of practitioner "
        "credentials in this report does not constitute a representation by Paciolus regarding "
        "the quality or completeness of any professional engagement."
    )
    story.append(Paragraph(practitioner_text, styles["BodyText"]))
    story.append(Spacer(1, 6))

    zero_storage = (
        "Zero-Storage Architecture: All financial data was processed in-memory during this "
        "analysis session and was not persisted to any storage medium. No client financial "
        "data is retained by Paciolus after the analysis session concludes."
    )
    story.append(Paragraph(f"<i>{zero_storage}</i>", styles["BodyText"]))
    story.append(Spacer(1, 8))


# ---------------------------------------------------------------------------
# Classical Footer
# ---------------------------------------------------------------------------


def render_classical_footer(story: list, styles: dict) -> None:
    """Build the classical document footer, kept together to avoid page split."""
    inner = []

    inner.append(Spacer(1, 12))
    inner.append(DoubleRule(width=6.5 * inch, color=ClassicalColors.LEDGER_RULE, thick=0.5, thin=0.25, spaceAfter=8))

    inner.append(Paragraph('"Particularis de Computis et Scripturis"', styles["FooterMotto"]))

    inner.append(Spacer(1, 8))

    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    inner.append(
        Paragraph(f"Generated by Paciolus\u00ae Diagnostic Intelligence  \u00b7  {timestamp}", styles["Footer"])
    )

    inner.append(
        Paragraph(
            "Zero-Storage Architecture: Your financial data was processed in-memory and never stored.",
            styles["Footer"],
        )
    )

    story.append(KeepTogether(inner))
