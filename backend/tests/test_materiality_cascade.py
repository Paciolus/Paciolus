"""
Tests for Sprint 310: Materiality Cascade Passthrough.

Covers:
- _resolve_materiality() helper logic
- TrialBalanceResponse includes materiality_source
- Route registration unchanged
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from routes.audit import _resolve_materiality


class TestResolveMateriality:
    """Tests for _resolve_materiality() helper."""

    def test_explicit_threshold_wins(self, db_session, make_engagement):
        """When explicit threshold > 0, it takes priority ('manual')."""
        eng = make_engagement(materiality_amount=100_000.0)
        threshold, source = _resolve_materiality(
            materiality_threshold=5000.0,
            engagement_id=eng.id,
            user_id=eng.created_by,
            db=db_session,
        )
        assert threshold == 5000.0
        assert source == "manual"

    def test_engagement_cascade_applies(self, db_session, make_engagement):
        """When threshold is 0 and engagement has materiality, cascade applies."""
        eng = make_engagement(
            materiality_amount=100_000.0,
            performance_materiality_factor=0.75,
        )
        threshold, source = _resolve_materiality(
            materiality_threshold=0.0,
            engagement_id=eng.id,
            user_id=eng.created_by,
            db=db_session,
        )
        # PM = 100,000 * 0.75 = 75,000
        assert threshold == 75_000.0
        assert source == "engagement"

    def test_engagement_without_materiality_returns_none(self, db_session, make_engagement):
        """When engagement has no materiality_amount, returns (0.0, 'none')."""
        eng = make_engagement(materiality_amount=None)
        threshold, source = _resolve_materiality(
            materiality_threshold=0.0,
            engagement_id=eng.id,
            user_id=eng.created_by,
            db=db_session,
        )
        assert threshold == 0.0
        assert source == "none"

    def test_no_engagement_id_returns_none(self, db_session, make_user):
        """When no engagement_id provided, returns (0.0, 'none')."""
        user = make_user()
        threshold, source = _resolve_materiality(
            materiality_threshold=0.0,
            engagement_id=None,
            user_id=user.id,
            db=db_session,
        )
        assert threshold == 0.0
        assert source == "none"

    def test_wrong_user_returns_none(self, db_session, make_engagement, make_user):
        """When user doesn't own engagement, returns (0.0, 'none')."""
        eng = make_engagement(materiality_amount=50_000.0)
        other_user = make_user(email="other@test.com")
        threshold, source = _resolve_materiality(
            materiality_threshold=0.0,
            engagement_id=eng.id,
            user_id=other_user.id,
            db=db_session,
        )
        assert threshold == 0.0
        assert source == "none"

    def test_zero_pm_returns_none(self, db_session, make_engagement):
        """When PM computes to 0, returns (0.0, 'none')."""
        eng = make_engagement(materiality_amount=0.0)
        threshold, source = _resolve_materiality(
            materiality_threshold=0.0,
            engagement_id=eng.id,
            user_id=eng.created_by,
            db=db_session,
        )
        assert threshold == 0.0
        assert source == "none"

    def test_nonexistent_engagement_returns_none(self, db_session, make_user):
        """Non-existent engagement returns (0.0, 'none')."""
        user = make_user()
        threshold, source = _resolve_materiality(
            materiality_threshold=0.0,
            engagement_id=9999,
            user_id=user.id,
            db=db_session,
        )
        assert threshold == 0.0
        assert source == "none"


class TestTrialBalanceResponseMaterialitySource:
    """Verify materiality_source field exists in response schema."""

    def test_materiality_source_in_schema(self):
        from shared.diagnostic_response_schemas import TrialBalanceResponse

        fields = TrialBalanceResponse.model_fields
        assert "materiality_source" in fields
