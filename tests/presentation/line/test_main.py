"""Tests for LINE entrypoint helpers."""

from datetime import UTC, datetime
from importlib import import_module
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from flow_res import Err, Ok

from app.usecases.result import ErrorType, UseCaseError


def _load_line_main(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LINE_CHANNEL_SECRET", "secret")
    monkeypatch.setenv("LINE_CHANNEL_ACCESS_TOKEN", "token")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///./bot.db")
    module_name = "app.presentation.line.__main__"
    import sys

    sys.modules.pop(module_name, None)
    return import_module(module_name)


def test_line_timestamp_conversion_rejects_invalid_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Malformed LINE timestamps are rejected instead of being replaced."""
    line_main = _load_line_main(monkeypatch)

    with pytest.raises(ValueError, match="integer"):
        line_main._occurred_at_from_line_timestamp("invalid")


@pytest.mark.anyio
async def test_handle_callback_saves_message(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test LINE webhook handling on a successful save."""
    line_main = _load_line_main(monkeypatch)

    class FakeUserSource:
        def __init__(self, user_id: str) -> None:
            self.user_id = user_id

    class FakeTextMessageContent:
        def __init__(self, text: str) -> None:
            self.id = "msg-1"
            self.text = text
            self.emojis = None
            self.quoted_message_id = None
            self.mark_as_read_token = None

    class FakeMessageEvent:
        def __init__(
            self,
            message: FakeTextMessageContent,
            source: FakeUserSource,
            reply_token: str,
            timestamp: int,
        ) -> None:
            self.message = message
            self.source = source
            self.reply_token = reply_token
            self.timestamp = timestamp

    fake_event = FakeMessageEvent(
        message=FakeTextMessageContent("hello"),
        source=FakeUserSource("u1"),
        reply_token="reply-token",
        timestamp=1_700_000_123_456,
    )

    monkeypatch.setattr(line_main, "MessageEvent", FakeMessageEvent)
    monkeypatch.setattr(line_main, "TextMessageContent", FakeTextMessageContent)
    monkeypatch.setattr(line_main, "UserSource", FakeUserSource)
    monkeypatch.setattr(line_main.parser, "parse", Mock(return_value=[fake_event]))
    monkeypatch.setattr(
        line_main.Mediator, "send_async", AsyncMock(return_value=Ok(None))
    )

    line_bot_api = AsyncMock()
    request = SimpleNamespace(
        headers={"X-Line-Signature": "signature"},
        body=AsyncMock(return_value=b"body"),
        app=SimpleNamespace(state=SimpleNamespace(line_bot_api=line_bot_api)),
    )

    result = await line_main.handle_callback(request)

    assert result == "OK"
    line_bot_api.reply_message.assert_not_awaited()
    line_main.Mediator.send_async.assert_awaited_once()
    command = line_main.Mediator.send_async.await_args.args[0]
    assert command.occurred_at == datetime(
        2023,
        11,
        14,
        22,
        15,
        23,
        456000,
        tzinfo=UTC,
    )


@pytest.mark.anyio
async def test_handle_callback_replies_on_save_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test LINE webhook error handling when save fails."""
    line_main = _load_line_main(monkeypatch)

    class FakeUserSource:
        def __init__(self, user_id: str) -> None:
            self.user_id = user_id

    class FakeTextMessageContent:
        def __init__(self, text: str) -> None:
            self.id = "msg-1"
            self.text = text
            self.emojis = None
            self.quoted_message_id = None
            self.mark_as_read_token = None

    class FakeMessageEvent:
        def __init__(
            self,
            message: FakeTextMessageContent,
            source: FakeUserSource,
            reply_token: str,
            timestamp: int,
        ) -> None:
            self.message = message
            self.source = source
            self.reply_token = reply_token
            self.timestamp = timestamp

    fake_event = FakeMessageEvent(
        message=FakeTextMessageContent("hello"),
        source=FakeUserSource("u1"),
        reply_token="reply-token",
        timestamp=1_700_000_123_456,
    )

    monkeypatch.setattr(line_main, "MessageEvent", FakeMessageEvent)
    monkeypatch.setattr(line_main, "TextMessageContent", FakeTextMessageContent)
    monkeypatch.setattr(line_main, "UserSource", FakeUserSource)
    monkeypatch.setattr(line_main.parser, "parse", Mock(return_value=[fake_event]))
    monkeypatch.setattr(
        line_main.Mediator,
        "send_async",
        AsyncMock(
            return_value=Err(
                UseCaseError(
                    type=ErrorType.UNEXPECTED,
                    message="save failed",
                )
            )
        ),
    )

    line_bot_api = AsyncMock()
    request = SimpleNamespace(
        headers={"X-Line-Signature": "signature"},
        body=AsyncMock(return_value=b"body"),
        app=SimpleNamespace(state=SimpleNamespace(line_bot_api=line_bot_api)),
    )

    result = await line_main.handle_callback(request)

    assert result is None
    line_bot_api.reply_message.assert_awaited_once()
