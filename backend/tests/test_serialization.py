"""
Tests for serialization utilities.
Sprint 41: Centralized dataclass serialization.
"""

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Optional

import pytest

from serialization import SerializableMixin, serialize_dataclass


class Status(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Direction(Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


@dataclass
class SimpleResult(SerializableMixin):
    """Simple dataclass with basic types."""
    name: str
    value: float
    count: int


@dataclass
class ResultWithEnum(SerializableMixin):
    """Dataclass with enum field."""
    name: str
    status: Status


@dataclass
class ResultWithDate(SerializableMixin):
    """Dataclass with date/datetime fields."""
    name: str
    created_date: date
    updated_at: Optional[datetime] = None


@dataclass
class ResultWithRounding(SerializableMixin):
    """Dataclass with fields that need rounding."""
    name: str
    ratio: float
    percentage: float
    raw_value: float

    _round_fields = {'ratio': 2, 'percentage': 1}


@dataclass
class ChildResult(SerializableMixin):
    """Child dataclass for nesting tests."""
    label: str
    score: float

    _round_fields = {'score': 2}


@dataclass
class ParentResult(SerializableMixin):
    """Parent dataclass with nested child."""
    name: str
    child: ChildResult
    children: list[ChildResult]


@dataclass
class ResultWithDict(SerializableMixin):
    """Dataclass with dict of nested objects."""
    name: str
    items: dict[str, ChildResult]


@dataclass
class ResultWithExclusion(SerializableMixin):
    """Dataclass with excluded fields."""
    name: str
    public_value: float
    _internal: str = "internal"

    _exclude_fields = {'secret'}


@dataclass
class ComplexResult(SerializableMixin):
    """Complex dataclass with multiple feature combinations."""
    name: str
    direction: Direction
    value: float
    created: date
    children: list[ChildResult]
    metadata: dict[str, float]

    _round_fields = {'value': 2}


class TestSerializableMixin:
    """Tests for SerializableMixin class."""

    def test_simple_serialization(self):
        """Test basic field serialization."""
        result = SimpleResult(name="test", value=1.5, count=10)
        data = result.to_dict()

        assert data == {"name": "test", "value": 1.5, "count": 10}

    def test_enum_serialization(self):
        """Test enum fields are converted to their values."""
        result = ResultWithEnum(name="test", status=Status.ACTIVE)
        data = result.to_dict()

        assert data == {"name": "test", "status": "active"}

    def test_date_serialization(self):
        """Test date/datetime fields are converted to ISO strings."""
        result = ResultWithDate(
            name="test",
            created_date=date(2025, 1, 15),
            updated_at=datetime(2025, 1, 15, 10, 30, 45)
        )
        data = result.to_dict()

        assert data["name"] == "test"
        assert data["created_date"] == "2025-01-15"
        assert data["updated_at"] == "2025-01-15T10:30:45"

    def test_date_serialization_with_none(self):
        """Test optional date fields handle None."""
        result = ResultWithDate(
            name="test",
            created_date=date(2025, 1, 15),
            updated_at=None
        )
        data = result.to_dict()

        assert data["updated_at"] is None

    def test_rounding(self):
        """Test float fields are rounded according to _round_fields."""
        result = ResultWithRounding(
            name="test",
            ratio=1.23456789,
            percentage=45.6789,
            raw_value=99.99999
        )
        data = result.to_dict()

        assert data["ratio"] == 1.23
        assert data["percentage"] == 45.7
        assert data["raw_value"] == 99.99999  # Not in _round_fields

    def test_nested_dataclass(self):
        """Test nested dataclass serialization."""
        child = ChildResult(label="child1", score=1.2345)
        result = ParentResult(
            name="parent",
            child=child,
            children=[ChildResult(label="c1", score=2.3456), ChildResult(label="c2", score=3.4567)]
        )
        data = result.to_dict()

        assert data["name"] == "parent"
        assert data["child"] == {"label": "child1", "score": 1.23}
        assert data["children"] == [
            {"label": "c1", "score": 2.35},
            {"label": "c2", "score": 3.46}
        ]

    def test_dict_of_dataclasses(self):
        """Test dict containing dataclass values."""
        result = ResultWithDict(
            name="test",
            items={
                "first": ChildResult(label="a", score=1.111),
                "second": ChildResult(label="b", score=2.222)
            }
        )
        data = result.to_dict()

        assert data["items"]["first"] == {"label": "a", "score": 1.11}
        assert data["items"]["second"] == {"label": "b", "score": 2.22}

    def test_underscore_fields_excluded(self):
        """Test fields starting with underscore are excluded."""
        result = ResultWithExclusion(name="test", public_value=1.0)
        data = result.to_dict()

        assert "name" in data
        assert "public_value" in data
        assert "_internal" not in data

    def test_complex_result(self):
        """Test complex dataclass with multiple features."""
        result = ComplexResult(
            name="complex",
            direction=Direction.POSITIVE,
            value=123.456789,
            created=date(2025, 2, 5),
            children=[ChildResult(label="x", score=9.999)],
            metadata={"key1": 1.5, "key2": 2.5}
        )
        data = result.to_dict()

        assert data == {
            "name": "complex",
            "direction": "positive",
            "value": 123.46,
            "created": "2025-02-05",
            "children": [{"label": "x", "score": 10.0}],
            "metadata": {"key1": 1.5, "key2": 2.5}
        }


class TestSerializeDataclassFunction:
    """Tests for standalone serialize_dataclass function."""

    @dataclass
    class PlainResult:
        """Plain dataclass without mixin."""
        name: str
        value: float
        status: Status

    def test_serialize_plain_dataclass(self):
        """Test serializing a dataclass without mixin."""
        result = self.PlainResult(name="plain", value=1.234, status=Status.INACTIVE)
        data = serialize_dataclass(result)

        assert data == {"name": "plain", "value": 1.234, "status": "inactive"}

    def test_serialize_with_rounding(self):
        """Test serializing with explicit round_fields."""
        result = self.PlainResult(name="plain", value=1.23456789, status=Status.ACTIVE)
        data = serialize_dataclass(result, round_fields={'value': 2})

        assert data["value"] == 1.23

    def test_serialize_with_exclusion(self):
        """Test serializing with explicit exclude_fields."""
        result = self.PlainResult(name="test", value=1.0, status=Status.ACTIVE)
        data = serialize_dataclass(result, exclude_fields={'status'})

        assert "name" in data
        assert "value" in data
        assert "status" not in data

    def test_non_dataclass_raises_error(self):
        """Test that non-dataclass raises TypeError."""
        with pytest.raises(TypeError, match="is not a dataclass"):
            serialize_dataclass({"not": "a dataclass"})


class TestEdgeCases:
    """Edge case tests."""

    @dataclass
    class EmptyResult(SerializableMixin):
        pass

    @dataclass
    class NullableResult(SerializableMixin):
        name: Optional[str] = None
        value: Optional[float] = None
        items: Optional[list[str]] = None

    def test_empty_dataclass(self):
        """Test serializing an empty dataclass."""
        result = self.EmptyResult()
        data = result.to_dict()
        assert data == {}

    def test_all_none_values(self):
        """Test dataclass with all None values."""
        result = self.NullableResult()
        data = result.to_dict()
        assert data == {"name": None, "value": None, "items": None}

    def test_empty_list(self):
        """Test dataclass with empty list."""
        result = self.NullableResult(items=[])
        data = result.to_dict()
        assert data["items"] == []
