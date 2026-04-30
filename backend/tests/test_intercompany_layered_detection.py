"""
Sprint 764 — Intercompany layered detection tests.

Covers the layered detection contract:
- Resolver cascade: request → engagement → none.
- Layered detection: metadata-exact → heuristic_separator → heuristic_keyword.
- Findings carry ``detection_method``, ``mapping_source``, and
  detection-quality-aware ``confidence`` scores.
- Backward compatibility: legacy callers (no mapping) match prior behavior.
"""

import json
from unittest.mock import MagicMock

from account_classifier import AccountClassifier
from audit.rules.relationships import detect_intercompany_imbalances
from shared.intercompany_resolver import (
    detection_method_label,
    resolve_counterparty_mapping,
)

# ---------------------------------------------------------------------------
# Resolver cascade: request → engagement → none
# ---------------------------------------------------------------------------


class TestResolverCascade:
    def test_request_mapping_wins_over_engagement(self) -> None:
        # Even if engagement has a stored mapping, the request-supplied
        # one takes precedence.  The engagement_id / db are not even
        # consulted when request_mapping is non-empty.
        request_map = {"Loan from Subsidiary A": "subsidiary_a"}
        mapping, source = resolve_counterparty_mapping(
            request_mapping=request_map,
            engagement_id=999,
            db=MagicMock(),  # unused
        )
        assert source == "request"
        assert mapping == {"loan from subsidiary a": "subsidiary_a"}

    def test_engagement_mapping_used_when_request_absent(self) -> None:
        eng = MagicMock()
        eng.intercompany_counterparties = json.dumps({"Due From Parent Co": "parent_corp"})
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = eng

        mapping, source = resolve_counterparty_mapping(
            request_mapping=None,
            engagement_id=42,
            db=db,
        )
        assert source == "engagement"
        assert mapping == {"due from parent co": "parent_corp"}

    def test_none_when_no_request_no_engagement(self) -> None:
        mapping, source = resolve_counterparty_mapping(
            request_mapping=None,
            engagement_id=None,
            db=None,
        )
        assert source == "none"
        assert mapping == {}

    def test_none_when_engagement_has_no_mapping(self) -> None:
        eng = MagicMock()
        eng.intercompany_counterparties = None
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = eng

        mapping, source = resolve_counterparty_mapping(request_mapping=None, engagement_id=42, db=db)
        assert source == "none"
        assert mapping == {}

    def test_empty_request_mapping_falls_through_to_engagement(self) -> None:
        # An empty dict on the request body should not "win" with empty
        # source — falls through so engagement still gets a chance.
        eng = MagicMock()
        eng.intercompany_counterparties = json.dumps({"Due From Parent": "parent"})
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = eng

        mapping, source = resolve_counterparty_mapping(request_mapping={}, engagement_id=42, db=db)
        assert source == "engagement"

    def test_malformed_engagement_json_falls_back_to_none(self) -> None:
        eng = MagicMock()
        eng.intercompany_counterparties = "{not valid json"
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = eng

        mapping, source = resolve_counterparty_mapping(request_mapping=None, engagement_id=42, db=db)
        assert source == "none"
        assert mapping == {}

    def test_case_folding_on_keys(self) -> None:
        # Account names in the trial balance vary in case; resolver
        # case-folds keys for case-insensitive matching downstream.
        mapping, _ = resolve_counterparty_mapping(
            request_mapping={"DUE FROM Parent CO": "parent_corp"},
            engagement_id=None,
            db=None,
        )
        assert "due from parent co" in mapping


# ---------------------------------------------------------------------------
# detection_method_label classifier
# ---------------------------------------------------------------------------


class TestDetectionMethodLabel:
    def test_metadata_path_takes_precedence(self) -> None:
        assert detection_method_label(used_metadata=True, separator_parsed=False) == "metadata_exact"
        assert detection_method_label(used_metadata=True, separator_parsed=True) == "metadata_exact"

    def test_separator_path_when_no_metadata(self) -> None:
        assert detection_method_label(used_metadata=False, separator_parsed=True) == "heuristic_separator"

    def test_keyword_only_fallback(self) -> None:
        assert detection_method_label(used_metadata=False, separator_parsed=False) == "heuristic_keyword"


# ---------------------------------------------------------------------------
# Layered detection in detect_intercompany_imbalances
# ---------------------------------------------------------------------------


def _balances(*entries: tuple[str, float, float]) -> dict[str, dict[str, float]]:
    """Helper: build the account_balances dict shape the engine expects."""
    return {key: {"debit": d, "credit": c} for key, d, c in entries}


def _classifier() -> AccountClassifier:
    return AccountClassifier()


class TestLayeredDetection:
    def test_metadata_exact_match_used_when_provided(self) -> None:
        # Account name has no separator and no obvious counterparty in
        # the text, but metadata names the counterparty explicitly.
        balances = _balances(
            ("intercompany_loan_a", 50000.0, 0.0),
            ("intercompany_loan_b", 0.0, 50000.0),
        )
        mapping = {
            "intercompany_loan_a": "subsidiary_x",
            "intercompany_loan_b": "subsidiary_x",
        }
        findings = detect_intercompany_imbalances(
            account_balances=balances,
            materiality_threshold=10000.0,
            classifier=_classifier(),
            provided_account_types={},
            provided_account_names={},
            counterparty_mapping=mapping,
            mapping_source="request",
        )
        # Both accounts share counterparty "subsidiary_x" — but
        # has_debit AND has_credit, so net_total = 0 and the group is
        # filtered out by BALANCE_TOLERANCE.  Use a non-offsetting
        # scenario to assert findings presence.
        # We retest the same path with non-offsetting:
        balances2 = _balances(("intercompany_loan_a", 50000.0, 0.0))
        findings2 = detect_intercompany_imbalances(
            account_balances=balances2,
            materiality_threshold=10000.0,
            classifier=_classifier(),
            provided_account_types={},
            provided_account_names={},
            counterparty_mapping={"intercompany_loan_a": "subsidiary_x"},
            mapping_source="request",
        )
        assert len(findings2) >= 1
        f = findings2[0]
        assert f["detection_method"] == "metadata_exact"
        assert f["mapping_source"] == "request"
        assert f["confidence"] == 1.0

    def test_heuristic_separator_when_metadata_misses(self) -> None:
        # Mapping is empty for this specific account, so the engine
        # falls through to the separator parser.
        balances = _balances(
            ("intercompany_-_subsidiary_b", 25000.0, 0.0),
        )
        # Provide a display name so the separator can find a counterparty
        names = {"intercompany_-_subsidiary_b": "Intercompany - Subsidiary B"}
        findings = detect_intercompany_imbalances(
            account_balances=balances,
            materiality_threshold=10000.0,
            classifier=_classifier(),
            provided_account_types={},
            provided_account_names=names,
            counterparty_mapping={},  # empty
            mapping_source="none",
        )
        assert len(findings) >= 1
        f = findings[0]
        assert f["detection_method"] == "heuristic_separator"
        assert f["mapping_source"] == "none"
        assert f["confidence"] == 0.85

    def test_keyword_only_when_no_separator_no_metadata(self) -> None:
        # Account contains the keyword "intercompany" but has no
        # separator; counterparty cannot be extracted.  Account is
        # filtered out (no counterparty group), so no findings.  This
        # documents the boundary: keyword-only triggers IC but cannot
        # be grouped.
        balances = _balances(("intercompany_account", 25000.0, 0.0))
        findings = detect_intercompany_imbalances(
            account_balances=balances,
            materiality_threshold=10000.0,
            classifier=_classifier(),
            provided_account_types={},
            provided_account_names={},
            counterparty_mapping={},
            mapping_source="none",
        )
        # No counterparty extracted ⇒ account does not enter any group
        # ⇒ no findings.  This matches legacy behavior; keyword-only
        # accounts without a counterparty are not flagged here (anomaly
        # detection picks them up via related_party rules instead).
        assert findings == []

    def test_metadata_overrides_keyword_for_non_keyword_accounts(self) -> None:
        # Account has no IC keyword in its name; only metadata flags it
        # as IC.  Layered detection accepts auditor judgment here.
        balances = _balances(("loan_to_affiliate", 75000.0, 0.0))
        names = {"loan_to_affiliate": "Loan to Affiliate"}
        mapping = {"loan to affiliate": "affiliate_co"}
        findings = detect_intercompany_imbalances(
            account_balances=balances,
            materiality_threshold=10000.0,
            classifier=_classifier(),
            provided_account_types={},
            provided_account_names=names,
            counterparty_mapping=mapping,
            mapping_source="engagement",
        )
        assert len(findings) >= 1
        assert findings[0]["detection_method"] == "metadata_exact"
        assert findings[0]["mapping_source"] == "engagement"

    def test_legacy_caller_no_mapping_works_unchanged(self) -> None:
        # The pre-Sprint-764 calling convention (no mapping kwargs)
        # must still produce valid findings with appropriate labels.
        balances = _balances(("intercompany_-_subsidiary_z", 30000.0, 0.0))
        names = {"intercompany_-_subsidiary_z": "Intercompany - Subsidiary Z"}
        findings = detect_intercompany_imbalances(
            account_balances=balances,
            materiality_threshold=10000.0,
            classifier=_classifier(),
            provided_account_types={},
            provided_account_names=names,
        )
        assert len(findings) >= 1
        # Default mapping_source is "none"; method is heuristic_separator.
        assert findings[0]["mapping_source"] == "none"
        assert findings[0]["detection_method"] == "heuristic_separator"

    def test_findings_have_required_explainability_fields(self) -> None:
        balances = _balances(("intercompany_-_subsidiary_q", 20000.0, 0.0))
        names = {"intercompany_-_subsidiary_q": "Intercompany - Subsidiary Q"}
        findings = detect_intercompany_imbalances(
            account_balances=balances,
            materiality_threshold=10000.0,
            classifier=_classifier(),
            provided_account_types={},
            provided_account_names=names,
        )
        for f in findings:
            assert "detection_method" in f
            assert f["detection_method"] in (
                "metadata_exact",
                "heuristic_separator",
                "heuristic_keyword",
            )
            assert "mapping_source" in f
            assert f["mapping_source"] in ("request", "engagement", "none")
            assert "confidence" in f
            assert 0.0 < f["confidence"] <= 1.0


# ---------------------------------------------------------------------------
# Engagement.to_dict surfaces the stored mapping
# ---------------------------------------------------------------------------


class TestEngagementSerialization:
    def test_to_dict_emits_decoded_mapping(self) -> None:
        from datetime import UTC, datetime

        from engagement_model import Engagement, EngagementStatus

        eng = Engagement(
            client_id=1,
            period_start=datetime.now(UTC),
            period_end=datetime.now(UTC),
            status=EngagementStatus.ACTIVE,
            created_by=1,
            intercompany_counterparties=json.dumps({"Due From Parent": "parent_corp"}),
        )
        # Bypass DB roundtrip — set defaults that to_dict expects
        eng.created_at = datetime.now(UTC)
        eng.updated_at = datetime.now(UTC)
        eng.performance_materiality_factor = 0.75
        eng.trivial_threshold_factor = 0.05
        d = eng.to_dict()
        assert d["intercompany_counterparties"] == {"Due From Parent": "parent_corp"}

    def test_to_dict_emits_none_when_unset(self) -> None:
        from datetime import UTC, datetime

        from engagement_model import Engagement, EngagementStatus

        eng = Engagement(
            client_id=1,
            period_start=datetime.now(UTC),
            period_end=datetime.now(UTC),
            status=EngagementStatus.ACTIVE,
            created_by=1,
        )
        eng.created_at = datetime.now(UTC)
        eng.updated_at = datetime.now(UTC)
        eng.performance_materiality_factor = 0.75
        eng.trivial_threshold_factor = 0.05
        d = eng.to_dict()
        assert d["intercompany_counterparties"] is None
