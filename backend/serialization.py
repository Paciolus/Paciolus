"""
Paciolus Serialization Utilities
Sprint 41: Centralized dataclass serialization

Provides a mixin for automatic dictionary serialization of dataclasses,
handling common cases like enums, dates, and nested dataclasses.
"""

from dataclasses import fields, is_dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, Optional, Set


class SerializableMixin:
    """
    Mixin providing automatic to_dict() serialization for dataclasses.

    Features:
    - Enum values converted to their .value
    - date/datetime converted to ISO format strings
    - Nested dataclasses recursively serialized
    - Optional field rounding for floats
    - Optional field exclusion

    Usage:
        @dataclass
        class MyResult(SerializableMixin):
            name: str
            value: float
            status: SomeEnum

            # Optional: specify fields to round
            _round_fields: ClassVar[Dict[str, int]] = {'value': 2}
            # Optional: specify fields to exclude
            _exclude_fields: ClassVar[Set[str]] = {'internal_cache'}

        result = MyResult(name="test", value=1.234567, status=SomeEnum.ACTIVE)
        result.to_dict()  # {'name': 'test', 'value': 1.23, 'status': 'active'}
    """

    # Override in subclasses to specify rounding precision
    # Format: {'field_name': decimal_places}
    _round_fields: Dict[str, int] = {}

    # Override in subclasses to exclude fields from serialization
    _exclude_fields: Set[str] = set()

    def to_dict(self) -> Dict[str, Any]:
        """Convert dataclass to dictionary for API/JSON serialization."""
        if not is_dataclass(self):
            raise TypeError(f"{self.__class__.__name__} must be a dataclass to use SerializableMixin")

        result = {}
        round_fields = getattr(self.__class__, '_round_fields', {})
        exclude_fields = getattr(self.__class__, '_exclude_fields', set())

        for field in fields(self):
            if field.name.startswith('_') or field.name in exclude_fields:
                continue

            value = getattr(self, field.name)
            result[field.name] = self._serialize_value(value, field.name, round_fields)

        return result

    def _serialize_value(
        self,
        value: Any,
        field_name: str,
        round_fields: Dict[str, int]
    ) -> Any:
        """Recursively serialize a value to a JSON-compatible type."""
        if value is None:
            return None

        # Enum → value
        if isinstance(value, Enum):
            return value.value

        # Date/datetime → ISO string
        if isinstance(value, (date, datetime)):
            return value.isoformat()

        # Float with optional rounding
        if isinstance(value, float):
            precision = round_fields.get(field_name)
            if precision is not None:
                return round(value, precision)
            return value

        # Nested dataclass with SerializableMixin
        if is_dataclass(value) and hasattr(value, 'to_dict'):
            return value.to_dict()

        # List of items (e.g., list of dataclasses)
        if isinstance(value, list):
            return [
                item.to_dict() if is_dataclass(item) and hasattr(item, 'to_dict')
                else self._serialize_value(item, '', round_fields)
                for item in value
            ]

        # Dict of items
        if isinstance(value, dict):
            return {
                k: (v.to_dict() if is_dataclass(v) and hasattr(v, 'to_dict')
                    else self._serialize_value(v, '', round_fields))
                for k, v in value.items()
            }

        # Primitives pass through
        return value


def serialize_dataclass(
    obj: Any,
    round_fields: Optional[Dict[str, int]] = None,
    exclude_fields: Optional[Set[str]] = None
) -> Dict[str, Any]:
    """
    Standalone function to serialize any dataclass to a dictionary.

    Use this for dataclasses that don't inherit from SerializableMixin.

    Args:
        obj: A dataclass instance
        round_fields: Dict mapping field names to decimal places for rounding
        exclude_fields: Set of field names to exclude from output

    Returns:
        Dictionary representation of the dataclass

    Usage:
        @dataclass
        class SimpleResult:
            name: str
            value: float

        result = SimpleResult(name="test", value=1.234567)
        serialize_dataclass(result, round_fields={'value': 2})
        # {'name': 'test', 'value': 1.23}
    """
    if not is_dataclass(obj):
        raise TypeError(f"{type(obj).__name__} is not a dataclass")

    round_fields = round_fields or {}
    exclude_fields = exclude_fields or set()

    def serialize_value(value: Any, field_name: str) -> Any:
        if value is None:
            return None
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        if isinstance(value, float):
            precision = round_fields.get(field_name)
            if precision is not None:
                return round(value, precision)
            return value
        if is_dataclass(value):
            if hasattr(value, 'to_dict'):
                return value.to_dict()
            return serialize_dataclass(value, round_fields)
        if isinstance(value, list):
            return [serialize_value(item, '') for item in value]
        if isinstance(value, dict):
            return {k: serialize_value(v, '') for k, v in value.items()}
        return value

    result = {}
    for field in fields(obj):
        if field.name.startswith('_') or field.name in exclude_fields:
            continue
        value = getattr(obj, field.name)
        result[field.name] = serialize_value(value, field.name)

    return result
