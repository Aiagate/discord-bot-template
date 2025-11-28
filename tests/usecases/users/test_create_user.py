"""Tests for Create User use case."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.result import Err, Ok
from app.repository import IUnitOfWork, RepositoryError, RepositoryErrorType
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


@pytest.mark.anyio
async def test_create_user_handler_invalid_email(uow: IUnitOfWork) -> None:
    """Test CreateUserHandler returns Err on invalid email format."""
    handler = CreateUserHandler(uow)

    # Command with an invalid email format
    command = CreateUserCommand(name="Test User", email="invalid-email")
    result = await handler.handle(command)

    assert isinstance(result, Err)
    assert result.error.type == ErrorType.VALIDATION_ERROR
    assert "Invalid email format" in result.error.message


@pytest.mark.anyio
async def test_create_user_handler_repository_error() -> None:
    """Test CreateUserHandler returns Err when repository fails."""
    # Create a mock UnitOfWork that simulates repository error
    mock_uow = MagicMock(spec=IUnitOfWork)
    mock_repo = MagicMock()

    # Mock the repository to return an Err
    mock_repo.add = AsyncMock(
        return_value=Err(
            RepositoryError(
                type=RepositoryErrorType.UNEXPECTED,
                message="Database connection failed",
            )
        )
    )

    mock_uow.GetRepository.return_value = mock_repo
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=None)

    handler = CreateUserHandler(mock_uow)
    command = CreateUserCommand(name="Test User", email="test@example.com")
    result = await handler.handle(command)

    assert isinstance(result, Err)
    assert result.error.type == ErrorType.UNEXPECTED
    assert "Database connection failed" in result.error.message
