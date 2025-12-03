"""Tests for Get User use case."""

import pytest

from app.core.result import is_err, is_ok
from app.domain.aggregates.user import User
from app.domain.repositories import IUnitOfWork
from app.domain.value_objects import Email, UserId
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
            id=UserId.generate().unwrap(),
            name="Bob",
            email=Email.from_primitive("bob@example.com").unwrap(),
        )
        save_result = await repo.add(user)
        assert is_ok(save_result)
        saved_user = save_result.value
        commit_result = await uow.commit()
        assert is_ok(commit_result)

    # Test: Get user via handler
    handler = GetUserHandler(uow)
    query = GetUserQuery(user_id=saved_user.id.to_primitive())
    result = await handler.handle(query)

    assert is_ok(result)
    assert result.value.user.id == saved_user.id.to_primitive()
    assert result.value.user.name == "Bob"
    assert result.value.user.email == "bob@example.com"


@pytest.mark.anyio
async def test_get_user_handler_not_found(uow: IUnitOfWork) -> None:
    """Test GetUserHandler returns Err when user is not found."""
    handler = GetUserHandler(uow)
    query = GetUserQuery(user_id="01ARZ3NDEKTSV4RRFFQ69G5FAV")  # Non-existent ULID
    result = await handler.handle(query)

    assert is_err(result)
    assert result.error.type == ErrorType.NOT_FOUND
