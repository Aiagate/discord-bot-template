"""Tests for the Discord direct-message response cog."""

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock

import discord
import pytest
from discord.ext import commands
from flow_res import Ok

from app.application.mediator import ApplicationMediator
from app.presentation.bot.cogs import dm_response_cog
from app.usecases.chat.save_discord_chat import SaveDiscordChatCommand


class _FakeAuthor:
    def __init__(self, author_id: int) -> None:
        self.id = author_id


class _FakeDMChannel:
    def __init__(self, channel_id: int) -> None:
        self.id = channel_id


@pytest.mark.anyio
async def test_on_message_passes_discord_created_at_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A Discord message's creation timestamp reaches the save command unchanged."""
    bot_user = _FakeAuthor(author_id=1)
    author = _FakeAuthor(author_id=2)
    bot = cast(commands.Bot, SimpleNamespace(user=bot_user))
    channel = _FakeDMChannel(channel_id=123)
    occurred_at = datetime(2026, 9, 6, 12, 30, tzinfo=UTC)
    message = cast(
        discord.Message,
        SimpleNamespace(
            author=author,
            channel=channel,
            content="hello",
            created_at=occurred_at,
        ),
    )
    send_async = AsyncMock(return_value=Ok(None))
    mediator = cast(
        ApplicationMediator,
        SimpleNamespace(send_async=send_async),
    )

    monkeypatch.setattr(dm_response_cog.discord, "DMChannel", _FakeDMChannel)

    await dm_response_cog.DirectMessageResponseCog(bot, mediator).on_message(message)

    send_async.assert_awaited_once()
    await_args = send_async.await_args
    assert await_args is not None
    command = await_args.args[0]
    assert isinstance(command, SaveDiscordChatCommand)
    assert command.occurred_at is occurred_at
