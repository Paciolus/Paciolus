"""All anomaly detection rules as composable, individually testable functions.

Each function in this module takes an account-balance mapping (and supporting
metadata such as category classifications, materiality threshold, and keyword
sets) and returns a list of finding dicts.  The functions are pure in the sense
that they do not mutate their inputs and carry no hidden state; any auditor
instance data they need is passed explicitly.  The ``_merge_anomalies``
function combines findings from all detectors into a single de-duplicated
list with priority-based type promotion.
"""

from __future__ import annotations

from collections import Counter
from decimal import Decimal
from typing import Any

from account_classifier import AccountClassifier
from audit.classification import (
    CONFIDENCE_HIGH,
    CONFIDENCE_MEDIUM,
    build_display_name,
    is_balance_abnormal,
    resolve_category,
    resolve_csv_type,
)
from classification_rules import (
    CATEGORY_DISPLAY_NAMES,
    CONCENTRATION_CATEGORIES,
    CONCENTRATION_MIN_CATEGORY_TOTAL,
    CONCENTRATION_THRESHOLD_HIGH,
    CONCENTRATION_THRESHOLD_MEDIUM,
    EQUITY_DIVIDEND_KEYWORDS,
    EQUITY_RETAINED_EARNINGS_KEYWORDS,
    EQUITY_TREASURY_KEYWORDS,
    EXPENSE_CONCENTRATION_THRESHOLD,
    INTERCOMPANY_KEYWORDS,
    NORMAL_BALANCE_MAP,
    RELATED_PARTY_EXCLUSION_KEYWORDS,
    RELATED_PARTY_KEYWORDS,
    REVENUE_CONCENTRATION_THRESHOLD,
    ROUND_NUMBER_TIER1_SUPPRESS,
    ROUNDING_MAX_ANOMALIES,
    ROUNDING_MIN_AMOUNT,
    ROUNDING_PATTERNS,
    SUSPENSE_CONFIDENCE_THRESHOLD,
    SUSPENSE_KEYWORDS,
    AccountCategory,
    NormalBalance,
    classify_round_number_tier,
)
from security_utils import log_secure_operation
from shared.monetary import BALANCE_TOLERANCE

# ── Legacy backward-compatibility attributes ─────────────────────────
# These were class-level attributes on StreamingAuditor. Kept here so
# any test or consumer referencing them by name can still import them.
_ROUNDING_TIER1_KEYWORDS: list[str] = ROUND_NUMBER_TIER1_SUPPRESS
_ROUNDING_TIER1_CATEGORIES: set[str] = set()
_ROUNDING_TIER3_KEYWORDS: list[str] = [
    "suspense",
    "clearing",
    "miscellaneous",
    "sundry",
    "unallocated",
    "unclassified",
]


def detect_abnormal_balances_streaming(
    account_balances: dict[str, dict[str, float]],
    materiality_threshold: float,
    classifier: AccountClassifier,
    provided_account_types: dict[str, str],
    provided_account_names: dict[str, str],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Detect accounts with abnormal balance directions using the heuristic classifier.

    Returns (abnormal_balances_list, classification_stats_dict).
    """
    log_secure_operation(
        "streaming_abnormal",
        f"Analyzing {len(account_balances)} unique accounts (threshold: ${materiality_threshold:,.2f}), "
        f"provided types: {len(provided_account_types)}, provided names: {len(provided_account_names)}",
    )

    abnormal_balances: list[dict[str, Any]] = []
    classification_stats = {"high": 0, "medium": 0, "low": 0, "unknown": 0}

    for account_key, balances in account_balances.items():
        debit_amount = balances["debit"]
        credit_amount = balances["credit"]
        net_balance = debit_amount - credit_amount

        # Skip zero balances (Decimal-aware, Sprint 340)
        if abs(Decimal(str(net_balance))) < BALANCE_TOLERANCE:
            continue

        category = resolve_category(
            account_key,
            net_balance,
            provided_account_types,
            provided_account_names,
            classifier,
        )
        display = build_display_name(account_key, provided_account_names)

        # Also run heuristic for confidence stats and suggestions
        result = classifier.classify(display, net_balance)

        # Use CSV-provided category if available
        csv_raw = provided_account_types.get(account_key, "")
        csv_cat, csv_conf = resolve_csv_type(csv_raw)
        has_csv_type = csv_cat is not None
        effective_category = category
        confidence = csv_conf if has_csv_type else result.confidence

        # Track classification confidence stats
        if effective_category == AccountCategory.UNKNOWN:
            classification_stats["unknown"] += 1
        elif confidence >= CONFIDENCE_HIGH:
            classification_stats["high"] += 1
        elif confidence >= CONFIDENCE_MEDIUM:
            classification_stats["medium"] += 1
        else:
            classification_stats["low"] += 1

        # Check if balance is abnormal
        is_abnormal = is_balance_abnormal(effective_category, net_balance, display)

        if is_abnormal and effective_category != AccountCategory.UNKNOWN:
            abs_amount = abs(net_balance)
            is_material = abs_amount >= materiality_threshold
            materiality_status = "material" if is_material else "immaterial"

            normal = NORMAL_BALANCE_MAP[effective_category]
            expected_balance = "Debit" if normal == NormalBalance.DEBIT else "Credit"
            actual_balance = "Credit" if net_balance < 0 else "Debit"

            if not is_material:
                log_secure_operation(
                    "below_materiality",
                    f"Below materiality: {display} (${abs_amount:,.2f} < ${materiality_threshold:,.2f})",
                )

            abnormal_balances.append(
                {
                    "account": display,
                    "type": CATEGORY_DISPLAY_NAMES.get(effective_category, "Unknown"),
                    "issue": f"Net {actual_balance} balance (should be {expected_balance})",
                    "amount": round(abs_amount, 2),
                    "debit": round(debit_amount, 2),
                    "credit": round(credit_amount, 2),
                    "materiality": materiality_status,
                    "category": effective_category.value,
                    "confidence": confidence,
                    "matched_keywords": result.matched_keywords if not has_csv_type else ["CSV_ACCOUNT_TYPE"],
                    "requires_review": not has_csv_type and result.requires_review,
                    "anomaly_type": "natural_balance_violation",
                    "expected_balance": expected_balance.lower(),
                    "actual_balance": actual_balance.lower(),
                    "severity": "high" if is_material else "low",
                    "suggestions": [
                        {
                            "category": s.category.value,
                            "confidence": s.confidence,
                            "reason": s.reason,
                            "matched_keywords": s.matched_keywords,
                        }
                        for s in result.suggestions
                    ]
                    if result.suggestions and not has_csv_type
                    else [],
                }
            )

    material_count = sum(1 for ab in abnormal_balances if ab.get("materiality") == "material")
    immaterial_count = len(abnormal_balances) - material_count
    log_secure_operation(
        "streaming_abnormal_complete",
        f"Found {len(abnormal_balances)} abnormal balances ({material_count} material, {immaterial_count} below materiality). "
        f"Classification: {classification_stats}",
    )

    return abnormal_balances, classification_stats


def detect_suspense_accounts(
    account_balances: dict[str, dict[str, float]],
    materiality_threshold: float,
    classifier: AccountClassifier,
    provided_account_types: dict[str, str],
    provided_account_names: dict[str, str],
) -> list[dict[str, Any]]:
    """Detect suspense and clearing accounts with outstanding balances.

    Sprint 41 - Phase III: Suspense Account Detector.
    """
    log_secure_operation("suspense_detection", f"Scanning {len(account_balances)} accounts for suspense indicators")

    suspense_accounts: list[dict[str, Any]] = []

    for account_key, balances in account_balances.items():
        debit_amount = balances["debit"]
        credit_amount = balances["credit"]
        net_balance = debit_amount - credit_amount

        if abs(Decimal(str(net_balance))) < BALANCE_TOLERANCE:
            continue

        display = build_display_name(account_key, provided_account_names)
        account_lower = display.lower()
        matched_keywords: list[str] = []
        total_weight = 0.0

        for keyword, weight, is_phrase in SUSPENSE_KEYWORDS:
            if keyword in account_lower:
                matched_keywords.append(keyword)
                total_weight += weight

        confidence = min(total_weight, 1.0)

        if confidence >= SUSPENSE_CONFIDENCE_THRESHOLD:
            abs_amount = abs(net_balance)
            is_material = abs_amount >= materiality_threshold
            materiality_status = "material" if is_material else "immaterial"

            category = resolve_category(
                account_key,
                net_balance,
                provided_account_types,
                provided_account_names,
                classifier,
            )

            suspense_accounts.append(
                {
                    "account": display,
                    "type": CATEGORY_DISPLAY_NAMES.get(category, "Unknown"),
                    "issue": "Suspense/clearing account with outstanding balance",
                    "amount": round(abs_amount, 2),
                    "debit": round(debit_amount, 2),
                    "credit": round(credit_amount, 2),
                    "materiality": materiality_status,
                    "category": category.value,
                    "confidence": confidence,
                    "matched_keywords": matched_keywords,
                    "requires_review": True,
                    "anomaly_type": "suspense_account",
                    "expected_balance": "zero",
                    "actual_balance": "debit" if net_balance > 0 else "credit",
                    "severity": "high" if is_material else "medium",
                    "suggestions": [],
                    "recommendation": (
                        "Investigate and clear this suspense account. "
                        "Determine proper classification for the outstanding balance."
                    ),
                }
            )

    log_secure_operation(
        "suspense_detection_complete", f"Found {len(suspense_accounts)} suspense accounts with balances"
    )

    return suspense_accounts


def detect_concentration_risk(
    account_balances: dict[str, dict[str, float]],
    materiality_threshold: float,
    classifier: AccountClassifier,
    provided_account_types: dict[str, str],
    provided_account_names: dict[str, str],
) -> list[dict[str, Any]]:
    """Detect accounts with unusually high concentration within their category.

    Sprint 42 - Phase III: Concentration Risk Detection.
    """
    log_secure_operation(
        "concentration_detection", f"Analyzing {len(account_balances)} accounts for concentration risk"
    )

    concentration_risks: list[dict[str, Any]] = []

    category_accounts: dict[AccountCategory, list[tuple[str, float, float, float]]] = {
        cat: [] for cat in CONCENTRATION_CATEGORIES
    }
    category_totals_dec: dict[AccountCategory, Decimal] = {cat: Decimal("0") for cat in CONCENTRATION_CATEGORIES}

    for account_key, balances in account_balances.items():
        debit_amount = balances["debit"]
        credit_amount = balances["credit"]
        net_balance = debit_amount - credit_amount

        if abs(Decimal(str(net_balance))) < BALANCE_TOLERANCE:
            continue

        category = resolve_category(
            account_key,
            net_balance,
            provided_account_types,
            provided_account_names,
            classifier,
        )
        display = build_display_name(account_key, provided_account_names)

        if category in CONCENTRATION_CATEGORIES:
            abs_balance = abs(net_balance)
            category_accounts[category].append((display, abs_balance, debit_amount, credit_amount))
            category_totals_dec[category] += Decimal(str(abs_balance))

    for category in CONCENTRATION_CATEGORIES:
        total_dec = category_totals_dec[category]

        if float(total_dec) < CONCENTRATION_MIN_CATEGORY_TOTAL:
            continue

        for display, abs_balance, debit_amount, credit_amount in category_accounts[category]:
            concentration_pct = float(Decimal(str(abs_balance)) / total_dec)

            severity = None
            if concentration_pct >= CONCENTRATION_THRESHOLD_HIGH:
                severity = "high"
            elif concentration_pct >= CONCENTRATION_THRESHOLD_MEDIUM:
                severity = "medium"

            if severity:
                is_material = abs_balance >= materiality_threshold
                materiality_status = "material" if is_material else "immaterial"

                _CATEGORY_PLURAL = {
                    "asset": "assets",
                    "liability": "liabilities",
                    "equity": "equity accounts",
                    "revenue": "revenues",
                    "expense": "expenses",
                }
                cat_plural = _CATEGORY_PLURAL.get(category.value, f"{category.value}s")

                concentration_risks.append(
                    {
                        "account": display,
                        "type": CATEGORY_DISPLAY_NAMES.get(category, "Unknown"),
                        "issue": f"Represents {concentration_pct:.1%} of total {cat_plural}",
                        "amount": round(abs_balance, 2),
                        "debit": round(debit_amount, 2),
                        "credit": round(credit_amount, 2),
                        "materiality": materiality_status,
                        "category": category.value,
                        "confidence": concentration_pct,
                        "matched_keywords": [],
                        "requires_review": True,
                        "anomaly_type": f"{category.value}_concentration",
                        "concentration_percent": round(concentration_pct * 100, 1),
                        "category_total": round(float(total_dec), 2),
                        "severity": severity,
                        "suggestions": [],
                        "recommendation": (
                            f"This account represents {concentration_pct:.1%} of total {cat_plural}. "
                            "Review for over-reliance on a single counterparty and consider "
                            "the impact if this balance becomes uncollectible or disputed."
                        ),
                    }
                )

    concentration_risks.sort(key=lambda x: x["concentration_percent"], reverse=True)

    log_secure_operation(
        "concentration_detection_complete", f"Found {len(concentration_risks)} concentration risk accounts"
    )

    return concentration_risks


def detect_rounding_anomalies(
    account_balances: dict[str, dict[str, float]],
    materiality_threshold: float,
    classifier: AccountClassifier,
    provided_account_types: dict[str, str],
    provided_account_names: dict[str, str],
    provided_account_subtypes: dict[str, str],
) -> list[dict[str, Any]]:
    """Detect suspicious round numbers that may indicate estimation or manipulation.

    Sprint 42 - Phase III: Rounding Anomaly Detection.
    Sprint 536: Three-tier framework (Suppress / Minor / Material).
    """
    log_secure_operation("rounding_detection", f"Analyzing {len(account_balances)} accounts for rounding anomalies")
    log_secure_operation("DEPLOY-VERIFY-536", "tiered round-number detection active")
    log_secure_operation("DEPLOY-VERIFY-537", "informational severity tier active")

    tb_total = sum(abs(b["debit"] - b["credit"]) for b in account_balances.values())

    subtype_source = provided_account_subtypes or provided_account_types

    candidates: list[tuple[dict[str, Any], str, float, str, str]] = []

    for account_key, balances in account_balances.items():
        debit_amount = balances["debit"]
        credit_amount = balances["credit"]
        net_balance = debit_amount - credit_amount
        abs_balance = abs(net_balance)

        if abs_balance < ROUNDING_MIN_AMOUNT:
            continue

        display = build_display_name(account_key, provided_account_names)
        category = resolve_category(
            account_key,
            net_balance,
            provided_account_types,
            provided_account_names,
            classifier,
        )
        subtype_raw = subtype_source.get(account_key, "")

        abs_balance_dec = Decimal(str(abs_balance))
        matched_pattern = None
        for divisor, pattern_name, pattern_severity in ROUNDING_PATTERNS:
            divisor_dec = Decimal(str(divisor))
            remainder_dec = abs_balance_dec % divisor_dec
            is_round = remainder_dec < BALANCE_TOLERANCE or (divisor_dec - remainder_dec) < BALANCE_TOLERANCE
            if is_round:
                matched_pattern = (divisor, pattern_name, pattern_severity)
                break

        if matched_pattern is None:
            continue

        tier = classify_round_number_tier(
            display,
            category,
            subtype_raw,
            abs_balance,
            tb_total,
            materiality_threshold,
        )
        if tier is None:
            continue

        divisor, pattern_name, pattern_severity = matched_pattern

        if divisor >= 100000:
            round_desc = f"${abs_balance / 1000:,.0f}K"
        else:
            round_desc = f"${abs_balance:,.0f}"

        if tier == "informational":
            effective_severity = "informational"
            materiality_status = "immaterial"
            confidence = 0.2
            issue_text = f"Informational Note: Round balance of {round_desc}"
            recommendation = (
                f"Informational Note: Round balance of {round_desc} on {display}. "
                "For this account type, round balances are common in practice and do not "
                "indicate a recording concern in isolation. No procedure required unless "
                "other risk factors are present."
            )
        elif tier == "minor":
            effective_severity = "low"
            materiality_status = "immaterial"
            confidence = 0.3
            issue_text = f"Round amount noted: {round_desc}"
            recommendation = (
                f"Round amount noted: {round_desc}. For this account type, round balances "
                "are common and may reflect estimates or contractual amounts. No immediate "
                "action required \u2014 verify during substantive procedures if material to "
                "the engagement."
            )
        else:
            effective_severity = pattern_severity if abs_balance >= materiality_threshold else "medium"
            materiality_status = "material" if abs_balance >= materiality_threshold else "immaterial"
            confidence = 0.6 if pattern_severity == "high" else 0.4
            issue_text = f"Exactly round amount: {round_desc}"
            recommendation = (
                f"Exactly round amount: {round_desc}. Inspect supporting documentation "
                "for all transactions comprising this balance. Perform targeted vouching "
                "to confirm amounts reflect actual invoiced or contracted values. Assess "
                "whether the pattern indicates estimation rather than transaction-based recording."
            )

        finding: dict[str, Any] = {
            "account": display,
            "type": CATEGORY_DISPLAY_NAMES.get(category, "Unknown"),
            "issue": issue_text,
            "amount": round(abs_balance, 2),
            "debit": round(debit_amount, 2),
            "credit": round(credit_amount, 2),
            "materiality": materiality_status,
            "category": category.value,
            "confidence": confidence,
            "matched_keywords": [],
            "requires_review": True,
            "anomaly_type": "rounding_anomaly",
            "rounding_pattern": pattern_name,
            "rounding_divisor": divisor,
            "severity": effective_severity,
            "suggestions": [],
            "recommendation": recommendation,
            "rounding_tier": tier,
        }
        candidates.append((finding, tier, abs_balance, category.value, subtype_raw.lower().strip()))

    # Second pass: repeated identical amounts (3+) in same type/subtype
    group_amounts: dict[tuple[str, str], list[float]] = {}
    for _, tier, abs_bal, cat_val, sub_val in candidates:
        key = (cat_val, sub_val)
        group_amounts.setdefault(key, []).append(abs_bal)

    repeated_sets: set[tuple[str, str, float]] = set()
    for (cat_val, sub_val), amounts in group_amounts.items():
        counts = Counter(amounts)
        for amt, cnt in counts.items():
            if cnt >= 3:
                repeated_sets.add((cat_val, sub_val, amt))

    rounding_anomalies: list[dict[str, Any]] = []
    for finding, tier, abs_bal, cat_val, sub_val in candidates:
        if (cat_val, sub_val, abs_bal) in repeated_sets:
            n_matching = group_amounts[(cat_val, sub_val)].count(abs_bal)
            matching_accounts = [
                f[0]["account"] for f in candidates if f[3] == cat_val and f[4] == sub_val and f[2] == abs_bal
            ]
            acct_list = ", ".join(matching_accounts)

            if abs_bal >= 100000:
                amt_str = f"${abs_bal / 1000:,.0f}K"
            else:
                amt_str = f"${abs_bal:,.0f}"

            finding["severity"] = "high"
            finding["materiality"] = "material"
            finding["confidence"] = 0.8
            finding["rounding_tier"] = "material"
            finding["issue"] = f"Identical round amount {amt_str} appears across {n_matching} accounts"
            finding["recommendation"] = (
                f"Identical round amount {amt_str} appears across "
                f"{n_matching} accounts ({acct_list}). This pattern may indicate "
                "allocation, estimation, or systematic rounding rather than "
                "transaction-based recording. Obtain documentation for the allocation "
                "methodology and verify each amount independently."
            )

        rounding_anomalies.append(finding)

    rounding_anomalies.sort(key=lambda x: x["amount"], reverse=True)
    if len(rounding_anomalies) > ROUNDING_MAX_ANOMALIES:
        rounding_anomalies = rounding_anomalies[:ROUNDING_MAX_ANOMALIES]

    log_secure_operation("rounding_detection_complete", f"Found {len(rounding_anomalies)} rounding anomalies")

    return rounding_anomalies


def detect_related_party_accounts(
    account_balances: dict[str, dict[str, float]],
    materiality_threshold: float,
    classifier: AccountClassifier,
    provided_account_types: dict[str, str],
    provided_account_names: dict[str, str],
) -> list[dict[str, Any]]:
    """Detect accounts indicating related party activity.

    Sprint 526 Fix 4d. Sprint 530 Fix 2: Tightened keyword matching.
    """
    findings: list[dict[str, Any]] = []
    for account_key, balances in account_balances.items():
        net_balance = balances["debit"] - balances["credit"]
        if abs(Decimal(str(net_balance))) < BALANCE_TOLERANCE:
            continue

        display = build_display_name(account_key, provided_account_names)
        search_text = display.lower()

        if any(excl in search_text for excl in RELATED_PARTY_EXCLUSION_KEYWORDS):
            continue

        matched = []
        weight = 0.0
        for keyword, kw_weight, is_phrase in RELATED_PARTY_KEYWORDS:
            if keyword in search_text:
                matched.append(keyword)
                weight = max(weight, kw_weight)

        if not matched:
            continue

        abs_amount = abs(net_balance)
        category = resolve_category(
            account_key,
            net_balance,
            provided_account_types,
            provided_account_names,
            classifier,
        )
        is_material = abs_amount >= materiality_threshold

        findings.append(
            {
                "account": display,
                "type": CATEGORY_DISPLAY_NAMES.get(category, "Unknown"),
                "issue": "Related party balance \u2014 requires ASC 850 disclosure assessment",
                "amount": round(abs_amount, 2),
                "debit": round(balances["debit"], 2),
                "credit": round(balances["credit"], 2),
                "materiality": "material" if is_material else "immaterial",
                "category": category.value,
                "confidence": weight,
                "matched_keywords": matched,
                "requires_review": True,
                "anomaly_type": "related_party",
                "severity": "high" if is_material else "medium",
                "suggestions": [],
            }
        )

    return findings


def detect_intercompany_imbalances(
    account_balances: dict[str, dict[str, float]],
    materiality_threshold: float,
    classifier: AccountClassifier,
    provided_account_types: dict[str, str],
    provided_account_names: dict[str, str],
) -> list[dict[str, Any]]:
    """Detect intercompany accounts with elimination gaps.

    Sprint 526 Fix 4e.
    """
    ic_accounts: list[tuple[str, str, float, dict]] = []
    for account_key, balances in account_balances.items():
        net_balance = balances["debit"] - balances["credit"]
        if abs(Decimal(str(net_balance))) < BALANCE_TOLERANCE:
            continue

        display = build_display_name(account_key, provided_account_names)
        search_text = display.lower()
        if any(kw in search_text for kw, _w, _p in INTERCOMPANY_KEYWORDS):
            ic_accounts.append((account_key, display, net_balance, balances))

    if not ic_accounts:
        return []

    def _extract_counterparty(name: str) -> str:
        lower = name.lower()
        for sep in [" \u2014 ", " \u2013 ", " - ", "\u2014", "\u2013", "-"]:
            if sep in lower:
                parts = lower.split(sep)
                cp = parts[-1].strip()
                if cp and cp not in ("receivable", "payable", "loan"):
                    return cp
        return ""

    counterparty_groups: dict[str, list[tuple[str, str, float, dict]]] = {}
    for key, display, net, bals in ic_accounts:
        cp = _extract_counterparty(display)
        if cp:
            counterparty_groups.setdefault(cp, []).append((key, display, net, bals))

    findings: list[dict[str, Any]] = []
    for cp_name, accounts in counterparty_groups.items():
        net_total = sum(net for _, _, net, _ in accounts)
        if abs(Decimal(str(net_total))) < BALANCE_TOLERANCE:
            continue

        has_debit = any(net > 0 for _, _, net, _ in accounts)
        has_credit = any(net < 0 for _, _, net, _ in accounts)

        if has_debit and has_credit:
            issue = f"Intercompany elimination gap of ${abs(net_total):,.2f} with {cp_name.title()}"
        elif has_debit:
            issue = f"Intercompany receivable from {cp_name.title()} \u2014 no offsetting payable found"
        else:
            issue = f"Intercompany payable to {cp_name.title()} \u2014 no offsetting receivable found"

        for key, display, net, bals in accounts:
            if abs(net) < 0.01:
                continue
            abs_amount = abs(net)
            category = resolve_category(
                key,
                net,
                provided_account_types,
                provided_account_names,
                classifier,
            )
            is_material = abs_amount >= materiality_threshold

            findings.append(
                {
                    "account": display,
                    "type": CATEGORY_DISPLAY_NAMES.get(category, "Unknown"),
                    "issue": issue,
                    "amount": round(abs_amount, 2),
                    "debit": round(bals["debit"], 2),
                    "credit": round(bals["credit"], 2),
                    "materiality": "material" if is_material else "immaterial",
                    "category": category.value,
                    "confidence": 0.85,
                    "matched_keywords": ["intercompany"],
                    "requires_review": True,
                    "anomaly_type": "intercompany_imbalance",
                    "severity": "high" if is_material else "medium",
                    "suggestions": [],
                    "cross_reference_note": f"Counterparty: {cp_name.title()} \u2014 net exposure: ${abs(net_total):,.2f}",
                }
            )

    return findings


def detect_equity_signals(
    account_balances: dict[str, dict[str, float]],
    materiality_threshold: float,
    classifier: AccountClassifier,
    provided_account_types: dict[str, str],
    provided_account_names: dict[str, str],
) -> list[dict[str, Any]]:
    """Detect abnormal equity patterns (deficit + dividends).

    Sprint 526 Fix 4f.
    """
    findings: list[dict[str, Any]] = []
    equity_accounts: dict[str, tuple[str, float, dict]] = {}

    for account_key, balances in account_balances.items():
        net_balance = balances["debit"] - balances["credit"]
        category = resolve_category(
            account_key,
            net_balance,
            provided_account_types,
            provided_account_names,
            classifier,
        )
        if category == AccountCategory.EQUITY:
            display = build_display_name(account_key, provided_account_names)
            equity_accounts[account_key] = (display, net_balance, balances)

    if not equity_accounts:
        return findings

    retained_earnings_deficit = None
    dividends_declared = None
    treasury_stock = None
    total_equity = Decimal("0")

    for key, (display, net, bals) in equity_accounts.items():
        lower = display.lower()
        total_equity += Decimal(str(net))
        if any(kw in lower for kw, _w, _p in EQUITY_RETAINED_EARNINGS_KEYWORDS):
            retained_earnings_deficit = (key, display, net, bals)
        if any(kw in lower for kw, _w, _p in EQUITY_DIVIDEND_KEYWORDS):
            dividends_declared = (key, display, net, bals)
        if any(kw in lower for kw, _w, _p in EQUITY_TREASURY_KEYWORDS):
            treasury_stock = (key, display, net, bals)

    if retained_earnings_deficit and dividends_declared:
        re_key, re_display, re_net, re_bals = retained_earnings_deficit
        div_key, div_display, div_net, div_bals = dividends_declared
        if re_net > 0:  # Debit balance (deficit)
            combined_return = abs(div_net) + (abs(treasury_stock[2]) if treasury_stock else 0)
            is_material = abs(re_net) >= materiality_threshold

            findings.append(
                {
                    "account": re_display,
                    "type": "Equity",
                    "issue": (
                        f"Accumulated deficit of ${abs(re_net):,.2f} while dividends of "
                        f"${abs(div_net):,.2f} have been declared \u2014 governance and solvency concern"
                    ),
                    "amount": round(abs(re_net), 2),
                    "debit": round(re_bals["debit"], 2),
                    "credit": round(re_bals["credit"], 2),
                    "materiality": "material" if is_material else "immaterial",
                    "category": "equity",
                    "confidence": 0.90,
                    "matched_keywords": ["retained earnings", "deficit", "dividend"],
                    "requires_review": True,
                    "anomaly_type": "equity_signal",
                    "severity": "high" if is_material else "medium",
                    "suggestions": [],
                    "cross_reference_note": (
                        f"Combined capital return: ${combined_return:,.2f} "
                        f"(dividends: ${abs(div_net):,.2f}"
                        + (f", treasury: ${abs(treasury_stock[2]):,.2f}" if treasury_stock else "")
                        + ") declared against a deficit"
                    ),
                }
            )

    return findings


def detect_revenue_concentration(
    account_balances: dict[str, dict[str, float]],
    materiality_threshold: float,
    classifier: AccountClassifier,
    provided_account_types: dict[str, str],
    provided_account_names: dict[str, str],
) -> list[dict[str, Any]]:
    """Revenue concentration analysis.

    Sprint 526 Fix 4g.
    """
    findings: list[dict[str, Any]] = []
    revenue_accounts: list[tuple[str, str, float, dict]] = []
    total_revenue = Decimal("0")

    for account_key, balances in account_balances.items():
        net_balance = balances["debit"] - balances["credit"]
        category = resolve_category(
            account_key,
            net_balance,
            provided_account_types,
            provided_account_names,
            classifier,
        )
        if category == AccountCategory.REVENUE:
            abs_bal = abs(net_balance)
            display = build_display_name(account_key, provided_account_names)
            revenue_accounts.append((account_key, display, abs_bal, balances))
            total_revenue += Decimal(str(abs_bal))

    if float(total_revenue) < CONCENTRATION_MIN_CATEGORY_TOTAL:
        return findings

    for key, display, abs_bal, bals in revenue_accounts:
        pct = float(Decimal(str(abs_bal)) / total_revenue)
        if pct >= REVENUE_CONCENTRATION_THRESHOLD:
            is_material = abs_bal >= materiality_threshold
            findings.append(
                {
                    "account": display,
                    "type": "Revenue",
                    "issue": f"Revenue concentration: {pct:.1%} of total revenue (${float(total_revenue):,.0f})",
                    "amount": round(abs_bal, 2),
                    "debit": round(bals["debit"], 2),
                    "credit": round(bals["credit"], 2),
                    "materiality": "material" if is_material else "immaterial",
                    "category": "revenue",
                    "confidence": pct,
                    "matched_keywords": [],
                    "requires_review": True,
                    "anomaly_type": "concentration_risk",
                    "concentration_percent": round(pct * 100, 1),
                    "category_total": round(float(total_revenue), 2),
                    "severity": "high" if is_material and pct >= REVENUE_CONCENTRATION_THRESHOLD else "medium",
                    "suggestions": [],
                }
            )

    return findings


def detect_expense_concentration(
    account_balances: dict[str, dict[str, float]],
    materiality_threshold: float,
    classifier: AccountClassifier,
    provided_account_types: dict[str, str],
    provided_account_names: dict[str, str],
) -> list[dict[str, Any]]:
    """Expense concentration analysis.

    Sprint 526 Fix 4h.
    """
    findings: list[dict[str, Any]] = []
    expense_accounts: list[tuple[str, str, float, dict]] = []
    total_expense = Decimal("0")

    for account_key, balances in account_balances.items():
        net_balance = balances["debit"] - balances["credit"]
        category = resolve_category(
            account_key,
            net_balance,
            provided_account_types,
            provided_account_names,
            classifier,
        )
        if category == AccountCategory.EXPENSE:
            abs_bal = abs(net_balance)
            display = build_display_name(account_key, provided_account_names)
            expense_accounts.append((account_key, display, abs_bal, balances))
            total_expense += Decimal(str(abs_bal))

    if float(total_expense) < CONCENTRATION_MIN_CATEGORY_TOTAL:
        return findings

    for key, display, abs_bal, bals in expense_accounts:
        pct = float(Decimal(str(abs_bal)) / total_expense)
        if pct >= EXPENSE_CONCENTRATION_THRESHOLD:
            is_material = abs_bal >= materiality_threshold
            findings.append(
                {
                    "account": display,
                    "type": "Expense",
                    "issue": f"Expense concentration: {pct:.1%} of total expenses (${float(total_expense):,.0f})",
                    "amount": round(abs_bal, 2),
                    "debit": round(bals["debit"], 2),
                    "credit": round(bals["credit"], 2),
                    "materiality": "material" if is_material else "immaterial",
                    "category": "expense",
                    "confidence": pct,
                    "matched_keywords": [],
                    "requires_review": True,
                    "anomaly_type": "concentration_risk",
                    "concentration_percent": round(pct * 100, 1),
                    "category_total": round(float(total_expense), 2),
                    "severity": "high" if is_material else "medium",
                    "suggestions": [],
                }
            )

    return findings


def _merge_anomalies(
    abnormal_balances: list[dict[str, Any]],
    suspense_accounts: list[dict[str, Any]],
    concentration_risks: list[dict[str, Any]],
    rounding_anomalies: list[dict[str, Any]],
    *,
    related_party: list[dict[str, Any]] | None = None,
    intercompany: list[dict[str, Any]] | None = None,
    equity_signals: list[dict[str, Any]] | None = None,
    revenue_concentration: list[dict[str, Any]] | None = None,
    expense_concentration: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Merge all anomaly types into abnormal balances.

    Avoids duplicates: if an account already exists in abnormal_balances,
    adds flags to the existing entry instead of creating a new one.
    Mutates and returns abnormal_balances.
    """
    existing_accounts = {ab["account"] for ab in abnormal_balances}

    def _merge_list(items: list[dict[str, Any]], flag_key: str, extra_fields: dict[str, str] | None = None) -> None:
        for item in items:
            if item["account"] not in existing_accounts:
                abnormal_balances.append(item)
                existing_accounts.add(item["account"])
            else:
                for entry in abnormal_balances:
                    if entry["account"] == item["account"]:
                        entry[flag_key] = True
                        if extra_fields:
                            for src, dst in extra_fields.items():
                                if src in item:
                                    entry[dst] = item[src]
                        if entry.get("severity") == "low" and item.get("severity") in ("high", "medium"):
                            entry["severity"] = item["severity"]
                        break

    intercompany_accounts: set[str] = set()
    related_party_accounts: set[str] = set()

    if intercompany:
        _merge_list(intercompany, "is_intercompany_imbalance", {"cross_reference_note": "cross_reference_note"})
        intercompany_accounts = {ic["account"] for ic in intercompany}

    if related_party:
        filtered_related = [rp for rp in related_party if rp["account"] not in intercompany_accounts]
        _merge_list(filtered_related, "is_related_party")
        related_party_accounts = {rp["account"] for rp in filtered_related}

    for entry in abnormal_balances:
        if entry.get("is_intercompany_imbalance") and entry.get("anomaly_type") != "intercompany_imbalance":
            entry["anomaly_type"] = "intercompany_imbalance"
            cross_note = entry.get("cross_reference_note", "")
            if cross_note:
                entry["issue"] = (
                    f"Intercompany receivable with no offsetting payable \u2014 potential consolidation elimination gap. {cross_note}"
                )
            else:
                entry["issue"] = (
                    "Intercompany receivable with no offsetting payable \u2014 potential consolidation elimination gap"
                )
            entry["severity"] = "high"

    filtered_suspense = [
        s
        for s in suspense_accounts
        if s["account"] not in related_party_accounts and s["account"] not in intercompany_accounts
    ]
    _merge_list(
        filtered_suspense,
        "is_suspense_account",
        {"confidence": "suspense_confidence", "matched_keywords": "suspense_keywords"},
    )

    _merge_list(
        concentration_risks,
        "has_concentration_risk",
        {"concentration_percent": "concentration_percent", "category_total": "category_total"},
    )

    filtered_rounding = [r for r in rounding_anomalies if r["account"] not in intercompany_accounts]
    _merge_list(filtered_rounding, "has_rounding_anomaly", {"rounding_pattern": "rounding_pattern"})

    if equity_signals:
        _merge_list(equity_signals, "is_equity_signal", {"cross_reference_note": "cross_reference_note"})
    if revenue_concentration:
        _merge_list(
            revenue_concentration,
            "has_concentration_risk",
            {"concentration_percent": "concentration_percent", "category_total": "category_total"},
        )
    if expense_concentration:
        _merge_list(
            expense_concentration,
            "has_concentration_risk",
            {"concentration_percent": "concentration_percent", "category_total": "category_total"},
        )

    return abnormal_balances
