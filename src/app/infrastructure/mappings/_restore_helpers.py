"""Small helpers shared by explicit persistence mappers."""

from datetime import datetime
from typing import TypeVar

from flow_res import Result, is_err

T = TypeVar("T")


def required_text(value: str | None, field_name: str) -> str:
    """Require a non-null persisted text value."""
    if value is None:
        raise ValueError(f"Persisted field '{field_name}' cannot be null.")
    return value


def required_timestamp(value: datetime | None, field_name: str) -> datetime:
    """Require a non-null persisted timestamp."""
    if value is None:
        raise ValueError(f"Persisted field '{field_name}' cannot be null.")
    return value


def unwrap_value[T, E: Exception](result: Result[T, E], field_name: str) -> T:
    """Convert a failed value-object restoration into a mapping error."""
    if is_err(result):
        raise ValueError(f"Failed to restore field '{field_name}': {result.error}")
    return result.value
