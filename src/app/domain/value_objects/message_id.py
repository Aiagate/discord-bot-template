"""Message identifier value object."""

from dataclasses import dataclass

from app.domain.value_objects.base_id import BaseId


@dataclass(frozen=True)
class MessageId(BaseId):
    """ULID identifying one persisted chat message."""
