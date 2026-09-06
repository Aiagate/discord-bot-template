"""Tests for ChatMessage mapping to the clean persistence model."""

from datetime import UTC, datetime

import pytest

from app.domain.aggregates.chat_message import ChatMessage
from app.domain.value_objects import AuthorKind, MessageContent, MessageId
from app.infrastructure.mappings.chat_message import chat_message_from_orm
from app.infrastructure.orm_mapping import ORMMappingRegistry
from app.infrastructure.orm_models.chat_message_orm import ChatMessageORM


def test_discord_message_maps_to_clean_columns() -> None:
    """Discord scope and message fields map without legacy columns."""
    message = ChatMessage.create_discord(
        guild_id="guild-1",
        channel_id="channel-1",
        external_sender_id="discord-user-1",
        author_kind=AuthorKind.BOT,
        content=MessageContent.text("hello"),
        occurred_at=datetime(2026, 9, 5, 9, 0, tzinfo=UTC),
    )

    row = ORMMappingRegistry.to_orm(message)

    assert isinstance(row, ChatMessageORM)
    assert row.id == message.id.to_primitive()
    assert row.platform == "DISCORD"
    assert row.conversation_scope == {
        "platform": "DISCORD",
        "guild_id": "guild-1",
        "channel_id": "channel-1",
    }
    assert row.external_sender_id == "discord-user-1"
    assert row.author_kind == "bot"
    assert row.content == message.content.to_primitive()
    assert row.occurred_at == message.occurred_at
    assert not hasattr(row, "version")
    assert not hasattr(row, "updated_at")


@pytest.mark.parametrize(
    "message",
    [
        ChatMessage.create_line_user(
            line_user_id="line-user-1",
            external_sender_id="line-user-1",
            content=MessageContent.text("user"),
            occurred_at=datetime(2026, 9, 5, 9, 0, tzinfo=UTC),
        ),
        ChatMessage.create_line_group(
            line_group_id="line-group-1",
            external_sender_id="line-user-1",
            content=MessageContent.text("group"),
            occurred_at=datetime(2026, 9, 5, 9, 0, tzinfo=UTC),
        ),
        ChatMessage.create_line_room(
            line_room_id="line-room-1",
            external_sender_id="line-user-1",
            content=MessageContent.text("room"),
            occurred_at=datetime(2026, 9, 5, 9, 0, tzinfo=UTC),
        ),
    ],
)
def test_line_message_round_trips_through_mapping(message: ChatMessage) -> None:
    """All LINE scope kinds round-trip as one ChatMessage type."""
    row = ORMMappingRegistry.to_orm(message)
    restored = ORMMappingRegistry.from_orm(row)

    assert isinstance(restored, ChatMessage)
    assert restored.platform == message.platform
    assert restored.conversation_scope == message.conversation_scope
    assert restored.external_sender_id == message.external_sender_id
    assert restored.author_kind == message.author_kind
    assert restored.content == message.content
    assert restored.id == message.id


def test_mapping_rejects_scope_platform_mismatch() -> None:
    """Malformed persisted scope data is rejected at the mapping boundary."""
    row = ChatMessageORM(
        id=MessageId.generate()
        .expect("MessageId.generate should succeed")
        .to_primitive(),
        platform="DISCORD",
        conversation_scope={
            "platform": "LINE",
            "kind": "user",
            "locator": "line-user-1",
        },
        external_sender_id="line-user-1",
        author_kind="user",
        content={"type": "TEXT", "payload": {"text": "invalid"}},
        occurred_at=datetime.now(UTC),
    )

    with pytest.raises(ValueError, match="platform"):
        chat_message_from_orm(row)


def test_mapping_normalizes_naive_driver_timestamp_to_utc() -> None:
    """A driver-stripped timestamp is restored as UTC at the infrastructure edge."""
    row = ChatMessageORM(
        id=MessageId.generate()
        .expect("MessageId.generate should succeed")
        .to_primitive(),
        platform="DISCORD",
        conversation_scope={
            "platform": "DISCORD",
            "guild_id": "guild-1",
            "channel_id": "channel-1",
        },
        external_sender_id="discord-user-1",
        author_kind="user",
        content={"type": "TEXT", "payload": {"text": "hello"}},
        occurred_at=datetime(2026, 9, 5, 9, 0),
    )

    restored = chat_message_from_orm(row)

    assert restored.occurred_at == datetime(2026, 9, 5, 9, 0, tzinfo=UTC)
