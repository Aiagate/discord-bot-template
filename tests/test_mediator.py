"""Tests for the Mediator."""

import pytest

from app.mediator import HandlerNotFoundError, Mediator, Request, RequestHandler


class MyQuery(Request[str]):
    pass


class MyQueryHandler(RequestHandler[MyQuery, str]):
    async def handle(self, request: MyQuery) -> str:
        return "Handled"


class AnotherQuery(Request[int]):
    pass


@pytest.mark.anyio
async def test_mediator_send_registered_request() -> None:
    """Test that a request with an auto-registered handler can be sent."""
    # The MyQueryHandler should be auto-registered via the metaclass
    result = await Mediator.send_async(MyQuery())
    assert result == "Handled"


@pytest.mark.anyio
async def test_mediator_send_unregistered_raises_error() -> None:
    """Test that sending an unregistered request raises HandlerNotFoundError."""
    with pytest.raises(
        HandlerNotFoundError, match="Handler not found for request type"
    ):
        await Mediator.send_async(AnotherQuery())
