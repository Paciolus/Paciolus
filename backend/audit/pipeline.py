"""Thin orchestrator: calls audit stages in sequence and assembles the result.

This module contains no detection logic of its own. It wires together the
ingestion, classification, anomaly-detection, and risk-summary stages,
delegating all analytic work to the dedicated stage modules.  The two public
entry points -- ``audit_trial_balance_streaming`` and
``audit_trial_balance_multi_sheet`` -- accept raw file bytes and return the
complete audit result dict consumed by the API layer.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Optional

from account_classifier import create_classifier
from audit.classification import (
    validate_balance_sheet_equation,
)
from audit.risk_summary import build_risk_summary
from audit.rules.merger import _merge_anomalies
from audit.streaming_auditor import StreamingAuditor
from classification_validator import run_classification_validation
from column_detector import ColumnMapping
from ratio_engine import CategoryTotals, calculate_analytics
from security_utils import (
    DEFAULT_CHUNK_SIZE,
    clear_memory,
    log_secure_operation,
    process_tb_chunked,
    read_excel_multi_sheet_chunked,
)
from shared.monetary import BALANCE_TOLERANCE, quantize_monetary


def audit_trial_balance_streaming(
    file_bytes: bytes,
    filename: str,
    materiality_threshold: float = 0.0,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    progress_callback: Optional[Callable[[int, str], None]] = None,
    account_type_overrides: Optional[dict[str, str]] = None,
    column_mapping: Optional[dict[str, str]] = None,
) -> dict[str, Any]:
    """Perform a complete streaming audit of a trial balance file."""
    log_secure_operation("streaming_audit_start", f"Starting streaming audit: {filename}")

    # Create classifier with any user overrides (Zero-Storage: session-only)
    classifier = create_classifier(account_type_overrides)
    if account_type_overrides:
        log_secure_operation(
            "classifier_overrides", f"Using {len(account_type_overrides)} user-provided account type overrides"
        )

    # Parse column mapping if provided (Day 9.2 - Zero-Storage: session-only)
    parsed_column_mapping: Optional[ColumnMapping] = None
    if column_mapping:
        parsed_column_mapping = ColumnMapping.from_dict(column_mapping)
        log_secure_operation("column_mapping_override", f"Using user-provided column mapping: {column_mapping}")

    auditor = StreamingAuditor(
        materiality_threshold=materiality_threshold,
        chunk_size=chunk_size,
        progress_callback=progress_callback,
        classifier=classifier,
        column_mapping=parsed_column_mapping,
    )

    try:
        # ── Stage 1: Ingestion ───────────────────────────────────────
        for chunk, rows_processed in process_tb_chunked(file_bytes, filename, chunk_size):
            auditor.process_chunk(chunk, rows_processed)
            del chunk

        # ── Sprint 666 Issue 5 (BLOCKING): Block silent success ──
        # Fail the pipeline explicitly when ingestion produced no rows OR
        # when the required debit/credit columns were never identified.
        # Without this guard, process_chunk's early-return on missing
        # columns silently produced a "balanced / low risk / no exceptions"
        # report on files like tb_no_headers.csv where row 1 was inferred
        # as the header and column detection then failed. That is the
        # exact failure mode the CEO remediation brief classified as
        # BLOCKING. A downstream consumer can key off `analysis_failed`
        # or `failure_reason` to display the failure notice.
        if auditor.total_rows == 0 or auditor.debit_col is None or auditor.credit_col is None:
            if auditor.total_rows == 0:
                failure_reason = "zero_rows_ingested"
                message = (
                    "ANALYSIS COULD NOT BE COMPLETED — No data was successfully "
                    "ingested from the submitted file. Please verify that the file "
                    "contains valid data and correctly formatted headers, then "
                    "resubmit."
                )
            else:
                failure_reason = "columns_not_detected"
                message = (
                    "ANALYSIS COULD NOT BE COMPLETED — The required Debit and "
                    "Credit columns could not be identified in the submitted file. "
                    "Please verify the file has a header row containing 'Account', "
                    "'Debit', and 'Credit' columns, then resubmit."
                )
            log_secure_operation("streaming_audit_failed", f"{failure_reason}: {filename}")
            # Return shape must satisfy TrialBalanceResponse schema so the
            # FastAPI route can serialize it. The `analysis_failed` flag is
            # how downstream consumers (frontend, exports, memo generators)
            # detect that the rest of the payload contains safe-default
            # fabrications rather than real analysis data — they MUST check
            # this flag before using any other field.
            return {
                "status": "failed",
                "analysis_failed": True,
                "failure_reason": failure_reason,
                "error_message": message,
                "filename": filename,
                "balanced": False,
                "total_debits": "0.00",
                "total_credits": "0.00",
                "difference": "0.00",
                "row_count": auditor.total_rows,
                "totals_rows_excluded": auditor.totals_rows_excluded,
                "timestamp": datetime.now(UTC).isoformat(),
                "message": message,
                # Empty analysis collections
                "abnormal_balances": [],
                "material_count": 0,
                "immaterial_count": 0,
                "informational_count": 0,
                "has_risk_alerts": False,
                "materiality_threshold": materiality_threshold,
                "classification_summary": {},
                "risk_summary": {
                    "total_anomalies": 0,
                    "high_severity": 0,
                    "medium_severity": 0,
                    "low_severity": 0,
                    "anomaly_types": {},
                    "risk_score": None,
                    "risk_tier": "not_applicable",
                    "risk_factors": [],
                    "coverage_pct": 0.0,
                },
                "classification_quality": {
                    "issues": [],
                    "quality_score": 0.0,
                    "issue_counts": {},
                    "total_issues": 0,
                },
                "column_detection": (
                    auditor.get_column_detection().to_dict() if auditor.get_column_detection() else None
                ),
                "analytics": {},
                "category_totals": {},
                "balance_sheet_validation": {
                    "is_balanced": False,
                    "status": "balanced",
                    "total_assets": "0.00",
                    "total_liabilities": "0.00",
                    "total_equity": "0.00",
                    "liabilities_plus_equity": "0.00",
                    "difference": "0.00",
                    "abs_difference": "0.00",
                    "severity": None,
                    "recommendation": ("Balance sheet validation not applicable — analysis could not be completed."),
                    "equation": "A = L + E",
                },
                "lead_sheet_grouping": {
                    "summaries": [],
                    "total_debits": 0.0,
                    "total_credits": 0.0,
                    "unclassified_count": 0,
                },
                "materiality_source": "none",
            }

        # ── Stage 2: Classification + Balance Check ──────────────────
        result = auditor.get_balance_result()
        account_classifications = auditor.get_classified_accounts()

        # ── Stage 3: Anomaly Detection ───────────────────────────────
        abnormal_balances = auditor.get_abnormal_balances()
        suspense_accounts = auditor.detect_suspense_accounts()
        concentration_risks = auditor.detect_concentration_risk()
        rounding_anomalies = auditor.detect_rounding_anomalies()
        related_party = auditor.detect_related_party_accounts()
        intercompany = auditor.detect_intercompany_imbalances()
        equity_signals = auditor.detect_equity_signals()
        revenue_concentration = auditor.detect_revenue_concentration()
        expense_concentration = auditor.detect_expense_concentration()

        abnormal_balances = _merge_anomalies(
            abnormal_balances,
            suspense_accounts,
            concentration_risks,
            rounding_anomalies,
            related_party=related_party,
            intercompany=intercompany,
            equity_signals=equity_signals,
            revenue_concentration=revenue_concentration,
            expense_concentration=expense_concentration,
        )

        # ── Stage 4: Risk Summary ────────────────────────────────────
        result["abnormal_balances"] = abnormal_balances
        result["materiality_threshold"] = materiality_threshold
        result["material_count"] = sum(1 for ab in abnormal_balances if ab.get("materiality") == "material")
        _informational_count = sum(1 for ab in abnormal_balances if ab.get("severity") == "informational")
        result["immaterial_count"] = len(abnormal_balances) - result["material_count"] - _informational_count
        result["informational_count"] = _informational_count
        result["has_risk_alerts"] = result["material_count"] > 0

        result["classification_summary"] = auditor.get_classification_summary()
        result["risk_summary"] = build_risk_summary(abnormal_balances)

        # Sprint 526 Fix 5: Compute diagnostic score at analysis time
        from shared.tb_diagnostic_constants import compute_tb_diagnostic_score, get_diagnostic_tier

        anomaly_types = result["risk_summary"].get("anomaly_types", {})
        _has_suspense = anomaly_types.get("suspense_account", 0) > 0
        _has_credit_balance = any(
            ab.get("anomaly_type") in ("abnormal_balance", "natural_balance_violation")
            and (ab.get("type", "").lower() == "asset")
            for ab in abnormal_balances
        )
        _total_debits = Decimal(str(result.get("total_debits", 0)))
        _material_items = [ab for ab in abnormal_balances if ab.get("materiality") == "material"]
        _flagged_value = sum(abs(Decimal(str(ab.get("amount", 0)))) for ab in _material_items)
        _coverage_pct = min(_flagged_value / _total_debits * 100, Decimal("100")) if _total_debits > 0 else Decimal("0")

        risk_score, risk_factors = compute_tb_diagnostic_score(
            result["material_count"],
            result["immaterial_count"],
            _coverage_pct,
            _has_suspense,
            _has_credit_balance,
            abnormal_balances=abnormal_balances,
            informational_count=result["informational_count"],
        )
        result["risk_summary"]["risk_score"] = risk_score
        result["risk_summary"]["risk_tier"] = get_diagnostic_tier(risk_score)
        result["risk_summary"]["risk_factors"] = [(name, pts) for name, pts in risk_factors]
        result["risk_summary"]["coverage_pct"] = float(Decimal(str(_coverage_pct)).quantize(Decimal("0.1")))

        # ── Supplementary analytics ──────────────────────────────────
        # Classification Validator
        cv_result = run_classification_validation(auditor.account_balances, account_classifications)
        result["classification_quality"] = cv_result.to_dict()

        # Build canonical display-name-keyed structures (single pass over accounts).
        # Reused by population profile, all_accounts, result exports, and lead sheets.
        display_balances: dict[str, dict[str, Any]] = {}
        display_classifications: dict[str, str] = {}
        display_subtypes: dict[str, str] = {}
        subtype_source = auditor.provided_account_subtypes or auditor.provided_account_types
        for acct_key in auditor.account_balances:
            display = auditor._display_name(acct_key)
            display_balances[display] = auditor.account_balances[acct_key]
            display_classifications[display] = account_classifications.get(acct_key, "unknown")
            display_subtypes[display] = subtype_source.get(acct_key, "")

        # Population Profile
        from population_profile_engine import compute_population_profile

        pop_profile = compute_population_profile(
            display_balances,
            display_classifications,
            missing_names=auditor.missing_names_count,
            missing_balances=auditor.missing_balances_count,
        )
        result["population_profile"] = pop_profile.to_dict()

        # Surface population profile data quality to top-level (BUG-006)
        if "data_quality" in result["population_profile"]:
            result["data_quality"] = result["population_profile"]["data_quality"]

        # Expense Category Analytical Procedures
        from expense_category_engine import compute_expense_categories

        category_totals_pre = auditor.get_category_totals(account_classifications)
        expense_analytics = compute_expense_categories(
            auditor.account_balances,
            account_classifications,
            category_totals_pre.total_revenue,
            materiality_threshold,
        )
        result["expense_category_analytics"] = expense_analytics.to_dict()

        # Accrual Completeness Estimator
        from accrual_completeness_engine import compute_accrual_completeness

        accrual_report = compute_accrual_completeness(
            auditor.account_balances,
            account_classifications,
        )
        result["accrual_completeness"] = accrual_report.to_dict()

        # Lease Account Diagnostic
        from lease_diagnostic_engine import compute_lease_diagnostic

        lease_report = compute_lease_diagnostic(
            auditor.account_balances,
            account_classifications,
            materiality_threshold=materiality_threshold,
        )
        result["lease_diagnostic"] = lease_report.to_dict()

        # Cutoff Risk Indicator
        from cutoff_risk_engine import compute_cutoff_risk

        cutoff_report = compute_cutoff_risk(
            auditor.account_balances,
            account_classifications,
            materiality_threshold=materiality_threshold,
        )
        result["cutoff_risk"] = cutoff_report.to_dict()

        # Going Concern Indicator Profile
        from going_concern_engine import compute_going_concern_profile

        gc_totals = category_totals_pre
        gc_report = compute_going_concern_profile(
            total_assets=gc_totals.total_assets,
            total_liabilities=gc_totals.total_liabilities,
            total_equity=gc_totals.total_equity,
            current_assets=gc_totals.current_assets,
            current_liabilities=gc_totals.current_liabilities,
            total_revenue=gc_totals.total_revenue,
            total_expenses=gc_totals.total_expenses,
        )
        result["going_concern"] = gc_report.to_dict()

        # Column detection info
        col_detection = auditor.get_column_detection()
        if col_detection:
            result["column_detection"] = col_detection.to_dict()
        else:
            result["column_detection"] = None

        # Category totals and analytics (reuse cached totals from earlier)
        category_totals = category_totals_pre
        analytics = calculate_analytics(category_totals, previous_totals=None)
        result["analytics"] = analytics
        result["category_totals"] = category_totals.to_dict()

        # Balance sheet validation
        balance_sheet_validation = auditor.validate_balance_sheet(category_totals)
        result["balance_sheet_validation"] = balance_sheet_validation

        if not balance_sheet_validation["is_balanced"]:
            result["risk_summary"]["anomaly_types"]["balance_sheet_imbalance"] = 1
            bs_severity = balance_sheet_validation["severity"]
            if bs_severity == "high":
                result["risk_summary"]["high_severity"] += 1
            elif bs_severity == "medium":
                result["risk_summary"]["medium_severity"] += 1
            elif bs_severity == "low":
                result["risk_summary"]["low_severity"] += 1
            result["risk_summary"]["total_anomalies"] += 1

        # Full parsed account list (derived from canonical display structures)
        all_accounts_list = [
            {
                "account": acct,
                "debit": bals["debit"],
                "credit": bals["credit"],
                "type": display_classifications.get(acct, "unknown"),
            }
            for acct, bals in display_balances.items()
        ]
        result["all_accounts"] = all_accounts_list
        result["account_balances"] = display_balances
        result["classified_accounts"] = display_classifications
        result["account_subtypes"] = display_subtypes

        # Lead sheet grouping
        from lead_sheet_mapping import group_by_lead_sheet, lead_sheet_grouping_to_dict

        lead_sheet_result = group_by_lead_sheet(all_accounts_list)
        result["lead_sheet_grouping"] = lead_sheet_grouping_to_dict(lead_sheet_result)

        log_secure_operation(
            "streaming_audit_complete",
            f"Audit complete. Rows: {result['row_count']}, Balanced: {result['balanced']}, "
            f"Material risks: {result['material_count']}, "
            f"BS Equation: {'✓' if balance_sheet_validation['is_balanced'] else '✗'}, "
            f"Column confidence: {col_detection.overall_confidence:.0%}"
            if col_detection
            else "N/A",
        )

        return result

    finally:
        auditor.clear()
        clear_memory()
        log_secure_operation("streaming_audit_cleanup", "Memory cleared")


def audit_trial_balance_multi_sheet(
    file_bytes: bytes,
    filename: str,
    selected_sheets: list[str],
    materiality_threshold: float = 0.0,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    progress_callback: Optional[Callable[[int, str], None]] = None,
    account_type_overrides: Optional[dict[str, str]] = None,
    column_mapping: Optional[dict[str, str]] = None,
) -> dict[str, Any]:
    """Perform a multi-sheet consolidated audit, aggregating totals across selected sheets."""
    log_secure_operation(
        "multi_sheet_audit_start", f"Starting multi-sheet audit: {filename} ({len(selected_sheets)} sheets)"
    )

    classifier = create_classifier(account_type_overrides)

    parsed_column_mapping: Optional[ColumnMapping] = None
    if column_mapping:
        parsed_column_mapping = ColumnMapping.from_dict(column_mapping)

    sheet_results: dict[str, dict[str, Any]] = {}
    consolidated_debits = Decimal("0")
    consolidated_credits = Decimal("0")
    consolidated_rows = 0
    all_abnormal_balances: list[dict[str, Any]] = []
    sheet_column_detections: dict[str, dict[str, Any]] = {}
    column_order_warnings: list[str] = []
    first_sheet_columns: Optional[tuple[str, str, str]] = None
    consolidated_category_totals = CategoryTotals()
    consolidated_account_balances: dict[str, dict[str, Any]] = {}
    consolidated_missing_names = 0
    consolidated_missing_balances = 0

    try:
        for sheet_name in selected_sheets:
            log_secure_operation("multi_sheet_processing", f"Processing sheet: {sheet_name}")

            auditor = StreamingAuditor(
                materiality_threshold=materiality_threshold,
                chunk_size=chunk_size,
                progress_callback=progress_callback,
                classifier=classifier,
                column_mapping=parsed_column_mapping,
            )

            for chunk, rows_processed, current_sheet in read_excel_multi_sheet_chunked(
                file_bytes, [sheet_name], chunk_size
            ):
                auditor.process_chunk(chunk, rows_processed)
                del chunk

            sheet_balance = auditor.get_balance_result()
            sheet_abnormals = auditor.get_abnormal_balances()
            sheet_suspense = auditor.detect_suspense_accounts()
            sheet_concentration = auditor.detect_concentration_risk()
            sheet_rounding = auditor.detect_rounding_anomalies()
            sheet_related_party = auditor.detect_related_party_accounts()
            sheet_intercompany = auditor.detect_intercompany_imbalances()
            sheet_equity_signals = auditor.detect_equity_signals()
            sheet_revenue_conc = auditor.detect_revenue_concentration()
            sheet_expense_conc = auditor.detect_expense_concentration()

            sheet_abnormals = _merge_anomalies(
                sheet_abnormals,
                sheet_suspense,
                sheet_concentration,
                sheet_rounding,
                related_party=sheet_related_party,
                intercompany=sheet_intercompany,
                equity_signals=sheet_equity_signals,
                revenue_concentration=sheet_revenue_conc,
                expense_concentration=sheet_expense_conc,
            )

            for entry in sheet_abnormals:
                entry["sheet_name"] = sheet_name

            sheet_col_detection = auditor.get_column_detection()
            if sheet_col_detection:
                sheet_column_detections[sheet_name] = sheet_col_detection.to_dict()
                current_columns: tuple[str | None, str | None, str | None] = (
                    sheet_col_detection.account_column,
                    sheet_col_detection.debit_column,
                    sheet_col_detection.credit_column,
                )
                if first_sheet_columns is None:
                    first_sheet_columns = current_columns  # type: ignore[assignment]
                elif current_columns != first_sheet_columns:
                    warning = (
                        f"Sheet '{sheet_name}' has different column order: "
                        f"Account='{current_columns[0]}', Debit='{current_columns[1]}', Credit='{current_columns[2]}' "
                        f"(first sheet: Account='{first_sheet_columns[0]}', Debit='{first_sheet_columns[1]}', Credit='{first_sheet_columns[2]}')"
                    )
                    column_order_warnings.append(warning)
                    log_secure_operation("multi_sheet_column_mismatch", warning)

            sheet_results[sheet_name] = {
                "balanced": sheet_balance["balanced"],
                "total_debits": sheet_balance["total_debits"],
                "total_credits": sheet_balance["total_credits"],
                "difference": sheet_balance["difference"],
                "row_count": sheet_balance["row_count"],
                "abnormal_count": len(sheet_abnormals),
                "column_detection": sheet_column_detections.get(sheet_name),
            }

            consolidated_debits += Decimal(str(sheet_balance["total_debits"]))
            consolidated_credits += Decimal(str(sheet_balance["total_credits"]))
            consolidated_rows += sheet_balance["row_count"]
            all_abnormal_balances.extend(sheet_abnormals)

            sheet_classifications = auditor.get_classified_accounts()
            sheet_category_totals = auditor.get_category_totals(sheet_classifications)
            consolidated_category_totals.total_assets += sheet_category_totals.total_assets
            consolidated_category_totals.current_assets += sheet_category_totals.current_assets
            consolidated_category_totals.inventory += sheet_category_totals.inventory
            consolidated_category_totals.total_liabilities += sheet_category_totals.total_liabilities
            consolidated_category_totals.current_liabilities += sheet_category_totals.current_liabilities
            consolidated_category_totals.total_equity += sheet_category_totals.total_equity
            consolidated_category_totals.total_revenue += sheet_category_totals.total_revenue
            consolidated_category_totals.cost_of_goods_sold += sheet_category_totals.cost_of_goods_sold
            consolidated_category_totals.total_expenses += sheet_category_totals.total_expenses

            for acct, bals in auditor.account_balances.items():
                if acct not in consolidated_account_balances:
                    consolidated_account_balances[acct] = {"debit": Decimal("0"), "credit": Decimal("0")}
                consolidated_account_balances[acct]["debit"] += bals["debit"]
                consolidated_account_balances[acct]["credit"] += bals["credit"]

            consolidated_missing_names += auditor.missing_names_count
            consolidated_missing_balances += auditor.missing_balances_count
            auditor.clear()

        # Consolidated balance check
        consolidated_difference = consolidated_debits - consolidated_credits
        is_consolidated_balanced = abs(consolidated_difference) < BALANCE_TOLERANCE

        material_count = sum(1 for ab in all_abnormal_balances if ab.get("materiality") == "material")
        ms_informational_count = sum(1 for ab in all_abnormal_balances if ab.get("severity") == "informational")
        immaterial_count = len(all_abnormal_balances) - material_count - ms_informational_count

        risk_summary = build_risk_summary(all_abnormal_balances)

        # Diagnostic score
        from shared.tb_diagnostic_constants import compute_tb_diagnostic_score, get_diagnostic_tier

        ms_anomaly_types = risk_summary.get("anomaly_types", {})
        ms_has_suspense = ms_anomaly_types.get("suspense_account", 0) > 0
        ms_has_credit_balance = any(
            ab.get("anomaly_type") in ("abnormal_balance", "natural_balance_violation")
            and (ab.get("type", "").lower() == "asset")
            for ab in all_abnormal_balances
        )
        ms_material_items = [ab for ab in all_abnormal_balances if ab.get("materiality") == "material"]
        ms_flagged_value = sum(abs(Decimal(str(ab.get("amount", 0)))) for ab in ms_material_items)
        ms_coverage_pct = (
            min(ms_flagged_value / consolidated_debits * 100, Decimal("100"))
            if consolidated_debits > 0
            else Decimal("0")
        )

        ms_risk_score, ms_risk_factors = compute_tb_diagnostic_score(
            material_count,
            immaterial_count,
            ms_coverage_pct,
            ms_has_suspense,
            ms_has_credit_balance,
            abnormal_balances=all_abnormal_balances,
            informational_count=ms_informational_count,
        )
        risk_summary["risk_score"] = ms_risk_score
        risk_summary["risk_tier"] = get_diagnostic_tier(ms_risk_score)
        risk_summary["risk_factors"] = [(name, pts) for name, pts in ms_risk_factors]
        risk_summary["coverage_pct"] = float(Decimal(str(ms_coverage_pct)).quantize(Decimal("0.1")))

        first_sheet_name = selected_sheets[0] if selected_sheets else None
        primary_col_detection = sheet_column_detections.get(first_sheet_name) if first_sheet_name else None

        result = {
            "status": "success",
            "balanced": is_consolidated_balanced,
            "total_debits": str(quantize_monetary(consolidated_debits)),
            "total_credits": str(quantize_monetary(consolidated_credits)),
            "difference": str(quantize_monetary(consolidated_difference)),
            "row_count": consolidated_rows,
            "timestamp": datetime.now(UTC).isoformat(),
            "message": "Consolidated trial balance is balanced"
            if is_consolidated_balanced
            else "Consolidated trial balance is OUT OF BALANCE",
            "is_consolidated": True,
            "sheet_count": len(selected_sheets),
            "selected_sheets": selected_sheets,
            "sheet_results": sheet_results,
            "abnormal_balances": all_abnormal_balances,
            "materiality_threshold": materiality_threshold,
            "material_count": material_count,
            "immaterial_count": immaterial_count,
            "informational_count": ms_informational_count,
            "has_risk_alerts": material_count > 0,
            "risk_summary": risk_summary,
            "column_detection": primary_col_detection,
            "sheet_column_detections": sheet_column_detections,
            "column_order_warnings": column_order_warnings,
            "has_column_order_mismatch": len(column_order_warnings) > 0,
        }

        # Analytics
        analytics = calculate_analytics(consolidated_category_totals, previous_totals=None)
        result["analytics"] = analytics
        result["category_totals"] = consolidated_category_totals.to_dict()

        # Balance sheet validation
        balance_sheet_validation = validate_balance_sheet_equation(consolidated_category_totals)
        result["balance_sheet_validation"] = balance_sheet_validation

        if not balance_sheet_validation["is_balanced"]:
            bs_risk: dict = result["risk_summary"]  # type: ignore[assignment]
            bs_risk["anomaly_types"]["balance_sheet_imbalance"] = 1
            bs_severity = balance_sheet_validation["severity"]
            if bs_severity == "high":
                bs_risk["high_severity"] += 1
            elif bs_severity == "medium":
                bs_risk["medium_severity"] += 1
            elif bs_severity == "low":
                bs_risk["low_severity"] += 1
            bs_risk["total_anomalies"] += 1

        # Population Profile
        from population_profile_engine import compute_population_profile

        pop_profile = compute_population_profile(
            consolidated_account_balances,
            missing_names=consolidated_missing_names,
            missing_balances=consolidated_missing_balances,
        )
        result["population_profile"] = pop_profile.to_dict()

        # Surface population profile data quality to top-level (BUG-006)
        if "data_quality" in result["population_profile"]:
            result["data_quality"] = result["population_profile"]["data_quality"]

        if "classification_quality" not in result:
            result["classification_quality"] = {
                "issues": [],
                "quality_score": 100.0,
                "issue_counts": {},
                "total_issues": 0,
            }

        # Full parsed account list (classify and build in a single pass)
        classifier_instance = create_classifier(account_type_overrides)
        all_accounts_list = []
        for acct_name, bals in consolidated_account_balances.items():
            net = bals["debit"] - bals["credit"]
            all_accounts_list.append(
                {
                    "account": acct_name,
                    "debit": bals["debit"],
                    "credit": bals["credit"],
                    "type": classifier_instance.classify(acct_name, net).category.value,
                }
            )
        result["all_accounts"] = all_accounts_list

        log_secure_operation(
            "multi_sheet_audit_complete",
            f"Consolidated audit complete. {len(selected_sheets)} sheets, "
            f"{consolidated_rows} total rows, Balanced: {is_consolidated_balanced}, "
            f"BS Equation: {'✓' if balance_sheet_validation['is_balanced'] else '✗'}, "
            f"Column mismatches: {len(column_order_warnings)}",
        )

        return result

    finally:
        clear_memory()
        log_secure_operation("multi_sheet_audit_cleanup", "Memory cleared")
