"""Platform-specific conversation scope value objects."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain.value_objects.chat_platform import ChatPlatform


def _required_identifier(value: str, name: str) -> str:
    """Normalize and validate a required external identifier."""
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{name} cannot be empty.")
    return normalized


def _optional_identifier(value: str | None, name: str) -> str | None:
    """Normalize an optional external identifier."""
    if value is None:
        return None
    return _required_identifier(value, name)


@dataclass(frozen=True, slots=True)
class DiscordConversationScope:
    """Guild and channel that identify one Discord conversation."""

    guild_id: str
    channel_id: str

    def __post_init__(self) -> None:
        """Validate and normalize the Discord locator."""
        object.__setattr__(
            self,
            "guild_id",
            _required_identifier(self.guild_id, "Discord guild ID"),
        )
        object.__setattr__(
            self,
            "channel_id",
            _required_identifier(self.channel_id, "Discord channel ID"),
        )

    @property
    def platform(self) -> ChatPlatform:
        """Return the platform represented by this scope."""
        return ChatPlatform.DISCORD

    def to_primitive(self) -> dict[str, str]:
        """Return a serializable representation of the scope."""
        return {
            "platform": self.platform.to_primitive(),
            "guild_id": self.guild_id,
            "channel_id": self.channel_id,
        }


class LineConversationKind(StrEnum):
    """Kinds of LINE conversation locators."""

    USER = "user"
    GROUP = "group"
    ROOM = "room"


@dataclass(frozen=True, slots=True)
class LineConversationScope:
    """Exactly one LINE user, group, or room conversation locator."""

    line_user_id: str | None = None
    line_group_id: str | None = None
    line_room_id: str | None = None

    def __post_init__(self) -> None:
        """Reject ambiguous or incomplete LINE conversation locators."""
        normalized_user_id = _optional_identifier(
            self.line_user_id,
            "LINE user ID",
        )
        normalized_group_id = _optional_identifier(
            self.line_group_id,
            "LINE group ID",
        )
        normalized_room_id = _optional_identifier(
            self.line_room_id,
            "LINE room ID",
        )
        present_count = sum(
            value is not None
            for value in (normalized_user_id, normalized_group_id, normalized_room_id)
        )
        if present_count != 1:
            raise ValueError(
                "A LINE conversation scope must contain exactly one of "
                "line_user_id, line_group_id, or line_room_id."
            )

        object.__setattr__(self, "line_user_id", normalized_user_id)
        object.__setattr__(self, "line_group_id", normalized_group_id)
        object.__setattr__(self, "line_room_id", normalized_room_id)

    @classmethod
    def user(cls, user_id: str) -> LineConversationScope:
        """Create a one-to-one LINE conversation scope."""
        return cls(line_user_id=user_id)

    @classmethod
    def group(cls, group_id: str) -> LineConversationScope:
        """Create a LINE group conversation scope."""
        return cls(line_group_id=group_id)

    @classmethod
    def room(cls, room_id: str) -> LineConversationScope:
        """Create a LINE room conversation scope."""
        return cls(line_room_id=room_id)

    @property
    def platform(self) -> ChatPlatform:
        """Return the platform represented by this scope."""
        return ChatPlatform.LINE

    @property
    def kind(self) -> LineConversationKind:
        """Return whether the scope identifies a user, group, or room."""
        if self.line_user_id is not None:
            return LineConversationKind.USER
        if self.line_group_id is not None:
            return LineConversationKind.GROUP
        return LineConversationKind.ROOM

    @property
    def locator(self) -> str:
        """Return the identifier that scopes a LINE history query."""
        return self.line_user_id or self.line_group_id or self.line_room_id or ""

    def to_primitive(self) -> dict[str, str]:
        """Return a serializable representation of the scope."""
        return {
            "platform": self.platform.to_primitive(),
            "kind": self.kind.value,
            "locator": self.locator,
        }


type ConversationScope = DiscordConversationScope | LineConversationScope
