"""Shared application messages."""

from app.contracts.messages.user_events import (
    USER_CREATED_TOPIC,
    UserCreatedEvent,
)

__all__ = ["USER_CREATED_TOPIC", "UserCreatedEvent"]
