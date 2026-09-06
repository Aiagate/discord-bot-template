"""Messages published by the user lifecycle."""

from dataclasses import dataclass

USER_CREATED_TOPIC = "user.created"


@dataclass(frozen=True, slots=True)
class UserCreatedEvent:
    """Payload for the event emitted after a user is committed."""

    user_id: str

    def to_payload(self) -> dict[str, object]:
        """Convert the event to the event bus payload shape."""
        return {"user_id": self.user_id}
