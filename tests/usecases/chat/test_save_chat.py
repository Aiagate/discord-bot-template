"""Tests for the Discord ChatMessage save use case."""

from datetime import UTC, datetime

import pytest
from flow_res import is_err

from app.contracts.ports import IChatHistoryQuery, IUnitOfWork
from app.domain.value_objects import DiscordConversationScope
from app.usecases.chat.save_discord_chat import (
    SaveDiscordChatCommand,
    SaveDiscordChatHandler,
)


@pytest.mark.anyio
async def test_save_chat_persists_discord_message(
    uow: IUnitOfWork,
    chat_history_query: IChatHistoryQuery,
) -> None:
    """Incoming Discord messages retain external sender and scope."""
    handler = SaveDiscordChatHandler(uow)

    result = await handler.handle(
        SaveDiscordChatCommand(
            external_sender_id="discord-user-1",
            guild_id="guild-1",
            channel_id="channel-1",
            content="hello",
            occurred_at=datetime(2026, 9, 5, 9, 0, tzinfo=UTC),
        )
    )

    assert not is_err(result)
    assert result.value.id
    history_result = await chat_history_query.get_recent_history(
        DiscordConversationScope(guild_id="guild-1", channel_id="channel-1"),
        limit=10,
    )

    assert not is_err(history_result)
    assert len(history_result.value) == 1
    message = history_result.value[0]
    assert message.external_sender_id.to_primitive() == "discord-user-1"
    assert message.content.payload["text"] == "hello"
    assert message.occurred_at == datetime(2026, 9, 5, 9, 0, tzinfo=UTC)
