"""Anomaly merger — combines findings from all detectors into a deduplicated list."""

from __future__ import annotations

from typing import Any


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
