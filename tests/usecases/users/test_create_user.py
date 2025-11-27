"""Tests for Create User use case."""

import pytest

from app.core.result import Err, Ok
from app.repository import IUnitOfWork
from app.usecases.result import ErrorType
from app.usecases.users.create_user import (
    CreateUserCommand,
    CreateUserHandler,
)


@pytest.mark.anyio
async def test_create_user_handler(uow: IUnitOfWork) -> None:
    """Test CreateUserHandler with real database."""
    handler = CreateUserHandler(uow)

    command = CreateUserCommand(name="Alice", email="alice@example.com")
    result = await handler.handle(command)

    assert isinstance(result, Ok)
    assert result.value.user.id  # ULID string should exist
    assert len(result.value.user.id) == 26  # ULID is 26 characters
    assert result.value.user.name == "Alice"
    assert result.value.user.email == "alice@example.com"


@pytest.mark.anyio
async def test_create_user_handler_validation_error(uow: IUnitOfWork) -> None:
    """Test CreateUserHandler returns Err on validation error."""
    handler = CreateUserHandler(uow)

    # Command with an empty name, which should fail domain validation
    command = CreateUserCommand(name="", email="test@example.com")
    result = await handler.handle(command)

    assert isinstance(result, Err)
    assert result.error.type == ErrorType.VALIDATION_ERROR
