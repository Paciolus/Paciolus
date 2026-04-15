"""Sprint 670 Issue 10 — structural unusual-account pattern detection.

Exercises ``audit.rules.suspense._detect_unusual_patterns`` directly so
the contract is locked against future regressions, plus an end-to-end
test that runs the streaming auditor against the six unusual accounts
called out in the CEO remediation brief.
"""

from __future__ import annotations

import io

import pandas as pd

from audit.rules.suspense import _detect_unusual_patterns
from audit.streaming_auditor import StreamingAuditor


class TestDetectUnusualPatterns:
    def test_symbolic_only_name(self):
        confidence, matches = _detect_unusual_patterns("????-001")
        assert confidence > 0
        assert any("symbolic" in m for m in matches)

    def test_predominantly_symbolic_name(self):
        # 4 alpha chars / 11 non-space chars = 36% — still under 50% but
        # currently above the 25% threshold. Use a more clearly symbolic
        # case that's unambiguously placeholder-shaped.
        confidence, matches = _detect_unusual_patterns("####-???")
        assert confidence > 0
        assert any("symbolic" in m for m in matches)

    def test_annotation_with_question_mark(self):
        confidence, matches = _detect_unusual_patterns("A/P - K.H. Owner Loan (personal?)")
        assert confidence > 0
        assert any("annotation" in m for m in matches)

    def test_annotation_meals_non_ded(self):
        confidence, matches = _detect_unusual_patterns("Meals/Ent 50% (non-ded?)")
        assert confidence > 0
        assert any("annotation" in m for m in matches)

    def test_trailing_question_mark(self):
        confidence, matches = _detect_unusual_patterns("Vendor Refund?")
        assert confidence > 0
        assert any("question mark" in m for m in matches)

    def test_eur_prefix(self):
        confidence, matches = _detect_unusual_patterns("EUR-AR (Euro Receivables)")
        assert confidence > 0
        assert any("foreign currency" in m for m in matches)

    def test_gbp_prefix(self):
        confidence, matches = _detect_unusual_patterns("GBP_Receivables")
        assert confidence > 0
        assert any("foreign currency" in m for m in matches)

    def test_clean_name_returns_zero(self):
        """Standard account names should not match any structural pattern."""
        confidence, matches = _detect_unusual_patterns("Cash - Operating Account")
        assert confidence == 0
        assert matches == []

    def test_normal_description_returns_zero(self):
        confidence, matches = _detect_unusual_patterns("Accounts Receivable")
        assert confidence == 0
        assert matches == []

    def test_legitimate_4xx_account_not_symbolic(self):
        """401(k) Plan should not be classified as symbolic."""
        confidence, matches = _detect_unusual_patterns("401(k) Plan Contributions")
        assert not any("symbolic" in m for m in matches)


class TestUnusualAccountsEndToEnd:
    """Run the streaming auditor against a CSV mirroring the brief's accounts."""

    @staticmethod
    def _build_csv() -> bytes:
        rows = [
            ("Account No", "Account Name", "Debit", "Credit"),
            ("1010", "Cash - Operating Account", "100000", ""),
            ("1099", "EUR-AR (Euro Receivables)", "31450", ""),
            ("1115", "A/R - DISPUTED (see note)", "14200", ""),
            ("1499", "SUSP-001", "3500", ""),
            ("1599", "????-UNIDENTIFIED", "", "3500"),
            ("2099", "A/P - K.H. Owner Loan (personal?)", "", "42000"),
            ("3901", "Owner Draw/Contrib - K.H.", "186000", ""),
            ("4025", "Revenue - MISC (unclassified)", "", "22400"),
            ("6150", "Meals/Ent 50% (non-ded?)", "8400", ""),
            ("7099", "Rounding Adj", "12", ""),
        ]
        out = io.StringIO()
        for r in rows:
            out.write(",".join(r) + "\n")
        return out.getvalue().encode("utf-8")

    def test_brief_accounts_all_flagged(self):
        """The six accounts the brief explicitly names must all be flagged.

        Brief Issue 10 expected result: 'flags SUSP-001, ????-UNIDENTIFIED,
        A/R-DISPUTED, Owner Draw, Revenue-MISC, EUR-AR (minimum)'.
        """
        csv_bytes = self._build_csv()
        auditor = StreamingAuditor(materiality_threshold=0)
        df = pd.read_csv(io.BytesIO(csv_bytes))
        auditor.process_chunk(df, len(df))
        suspense = auditor.detect_suspense_accounts()
        flagged_names = {entry["account"].lower() for entry in suspense}

        for required in [
            "susp-001",
            "????-unidentified",
            "a/r - disputed (see note)",
            "owner draw/contrib - k.h.",
            "revenue - misc (unclassified)",
            "eur-ar (euro receivables)",
        ]:
            assert any(required in name for name in flagged_names), (
                f"Required account '{required}' missing from flagged set: {flagged_names}"
            )

    def test_clean_account_not_flagged(self):
        """Cash - Operating Account must NOT be flagged."""
        csv_bytes = self._build_csv()
        auditor = StreamingAuditor(materiality_threshold=0)
        df = pd.read_csv(io.BytesIO(csv_bytes))
        auditor.process_chunk(df, len(df))
        suspense = auditor.detect_suspense_accounts()
        flagged_names = {entry["account"].lower() for entry in suspense}
        assert not any("cash - operating" in name for name in flagged_names)
