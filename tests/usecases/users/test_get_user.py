"""Tests for Get User use case."""

import pytest

from app.core.result import Err, Ok
from app.domain.aggregates.user import User
from app.domain.value_objects import Email, UserId
from app.repository import IUnitOfWork
from app.usecases.result import ErrorType
from app.usecases.users.get_user import GetUserHandler, GetUserQuery


@pytest.mark.anyio
async def test_get_user_handler(uow: IUnitOfWork) -> None:
    """Test GetUserHandler successfully returns a user."""
    # Setup: Create user first
    saved_user = None
    async with uow:
        repo = uow.GetRepository(User, str)
        user = User(
            id=UserId.generate(),
            name="Bob",
            email=Email.from_primitive("bob@example.com"),
        )
        save_result = await repo.save(user)
        assert isinstance(save_result, Ok)
        saved_user = save_result.value

    # Test: Get user via handler
    handler = GetUserHandler(uow)
    query = GetUserQuery(user_id=saved_user.id.to_primitive())
    result = await handler.handle(query)

    assert isinstance(result, Ok)
    assert result.value.user.id == saved_user.id.to_primitive()
    assert result.value.user.name == "Bob"
    assert result.value.user.email == "bob@example.com"


@pytest.mark.anyio
async def test_get_user_handler_not_found(uow: IUnitOfWork) -> None:
    """Test GetUserHandler returns Err when user is not found."""
    handler = GetUserHandler(uow)
    query = GetUserQuery(user_id="01ARZ3NDEKTSV4RRFFQ69G5FAV")  # Non-existent ULID
    result = await handler.handle(query)

    assert isinstance(result, Err)
    assert result.error.type == ErrorType.NOT_FOUND
