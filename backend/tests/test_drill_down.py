"""
Tests for the shared drill-down detail table builder — Sprint FIX-4.

Covers:
- Populated rows render data rows
- Empty rows with suppress_empty=False render the labeled empty state
- Empty rows with suppress_empty=True render nothing (backward-compatible default)
"""

import sys
from pathlib import Path

import pytest
from reportlab.platypus import Paragraph as RParagraph

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.drill_down import _EMPTY_STATE_TEXT, build_drill_down_table
from shared.memo_base import create_memo_styles


@pytest.fixture()
def styles():
    return create_memo_styles()


class TestDrillDownTable:
    """Tests for build_drill_down_table behavior."""

    def test_populated_rows_render_table(self, styles):
        """A drill-down with populated rows renders those rows."""
        story: list = []
        build_drill_down_table(
            story,
            styles,
            doc_width=468.0,
            title="Test Detail",
            headers=["Col A", "Col B"],
            rows=[["val1", "val2"]],
        )
        # Should render title Paragraph, Spacer, Table, Spacer (at minimum)
        assert len(story) >= 3
        # First element should be the title paragraph
        assert isinstance(story[0], RParagraph)

    def test_empty_rows_suppress_empty_false_renders_placeholder(self, styles):
        """A drill-down with zero rows and suppress_empty=False renders the placeholder."""
        story: list = []
        build_drill_down_table(
            story,
            styles,
            doc_width=468.0,
            title="Empty Detail",
            headers=["Col A", "Col B"],
            rows=[],
            suppress_empty=False,
        )
        # Should render: title Paragraph, Spacer, placeholder Paragraph, Spacer
        assert len(story) == 4
        # Find the placeholder paragraph
        paragraphs = [e for e in story if isinstance(e, RParagraph)]
        placeholder_texts = [p.text for p in paragraphs]
        expected_text = _EMPTY_STATE_TEXT.format(title="Empty Detail")
        assert any(expected_text in t for t in placeholder_texts), (
            f"Expected placeholder text '{expected_text}' not found in: {placeholder_texts}"
        )

    def test_empty_rows_suppress_empty_true_renders_nothing(self, styles):
        """A drill-down with zero rows and suppress_empty=True renders nothing."""
        story: list = []
        build_drill_down_table(
            story,
            styles,
            doc_width=468.0,
            title="Silent Empty",
            headers=["Col A", "Col B"],
            rows=[],
            suppress_empty=True,
        )
        assert len(story) == 0

    def test_default_suppress_empty_is_true(self, styles):
        """Default behavior (no suppress_empty arg) renders nothing on empty rows."""
        story: list = []
        build_drill_down_table(
            story,
            styles,
            doc_width=468.0,
            title="Default Empty",
            headers=["Col A"],
            rows=[],
        )
        assert len(story) == 0
