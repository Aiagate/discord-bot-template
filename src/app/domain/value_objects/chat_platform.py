"""Chat platform value object."""

from __future__ import annotations

from enum import StrEnum

from flow_res import Err, Ok, Result


class ChatPlatform(StrEnum):
    """External messaging platforms supported by the application."""

    DISCORD = "DISCORD"
    LINE = "LINE"

    @classmethod
    def from_primitive(cls, value: str) -> Result[ChatPlatform, ValueError]:
        """Create a platform from its persisted string representation."""
        normalized = value.strip()
        if not normalized:
            return Err(ValueError("Chat platform cannot be empty."))

        try:
            return Ok(cls(normalized.upper()))
        except ValueError:
            return Err(ValueError(f"Invalid chat platform: {value}"))

    def to_primitive(self) -> str:
        """Return the platform value used by persistence."""
        return self.value
