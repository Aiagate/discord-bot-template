"""External platform actor identifier value object."""

from __future__ import annotations

from dataclasses import dataclass

from flow_res import Err, Ok, Result


@dataclass(frozen=True, slots=True)
class ExternalActorId:
    """Identifier assigned to a message author by an external platform."""

    _value: str

    def __post_init__(self) -> None:
        """Reject missing actor identifiers and normalize surrounding space."""
        normalized = self._value.strip()
        if not normalized:
            raise ValueError("External actor ID cannot be empty.")
        object.__setattr__(self, "_value", normalized)

    @classmethod
    def from_primitive(cls, value: str) -> Result[ExternalActorId, ValueError]:
        """Create an external actor identifier from a persisted string."""
        try:
            return Ok(cls(value))
        except ValueError as error:
            return Err(error)

    def to_primitive(self) -> str:
        """Return the platform identifier used by persistence."""
        return self._value

    def __str__(self) -> str:
        """Return the external identifier."""
        return self._value
