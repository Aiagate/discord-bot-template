"""Tests for the LINE ChatMessage save use case."""

from datetime import UTC, datetime

import pytest
from flow_res import is_err

from app.contracts.ports import IChatHistoryQuery, IUnitOfWork
from app.domain.value_objects import LineConversationScope
from app.usecases.chat.save_line_chat import (
    SaveLineChatCommand,
    SaveLineChatHandler,
)


@pytest.mark.anyio
async def test_save_line_chat_persists_group_message(
    uow: IUnitOfWork,
    chat_history_query: IChatHistoryQuery,
) -> None:
    """Incoming LINE group messages retain sender and conversation scope."""
    handler = SaveLineChatHandler(uow)

    result = await handler.handle(
        SaveLineChatCommand(
            external_sender_id="line-user-1",
            conversation_scope=LineConversationScope.group("line-group-1"),
            content="hello",
            occurred_at=datetime(2026, 9, 5, 9, 0, tzinfo=UTC),
        )
    )

    assert not is_err(result)
    assert result.value.id
    history_result = await chat_history_query.get_recent_history(
        LineConversationScope.group("line-group-1"),
        limit=10,
    )

    assert not is_err(history_result)
    assert len(history_result.value) == 1
    message = history_result.value[0]
    assert message.external_sender_id.to_primitive() == "line-user-1"
    assert message.content.payload["text"] == "hello"
    assert message.occurred_at == datetime(2026, 9, 5, 9, 0, tzinfo=UTC)
