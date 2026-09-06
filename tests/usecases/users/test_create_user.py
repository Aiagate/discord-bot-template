"""Tests for Create User use case."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from flow_res import Err, is_err, is_ok

from app.contracts.ports import IUnitOfWork
from app.domain.repositories import RepositoryError, RepositoryErrorType
from app.usecases.result import ErrorType
from app.usecases.users.create_user import (
    CreateUserCommand,
    CreateUserHandler,
)


@pytest.mark.anyio
async def test_create_user_handler(uow: IUnitOfWork, event_bus: AsyncMock) -> None:
    """Test CreateUserHandler with real database."""
    handler = CreateUserHandler(uow, event_bus)

    command = CreateUserCommand(display_name="Alice", email="alice@example.com")
    result = await handler.handle(command)

    assert is_ok(result)
    user_id = result.value.id  # Now it's a str
    assert user_id  # ULID string should exist
    assert len(user_id) == 26  # ULID is 26 characters


@pytest.mark.anyio
async def test_create_user_handler_invalid_email(
    uow: IUnitOfWork, event_bus: AsyncMock
) -> None:
    """Test CreateUserHandler returns Err on invalid email format."""
    handler = CreateUserHandler(uow, event_bus)

    # Command with an invalid email format
    command = CreateUserCommand(display_name="Test User", email="invalid-email")
    result = await handler.handle(command)

    assert is_err(result)
    assert result.error.type == ErrorType.VALIDATION_ERROR
    assert "Invalid email format" in result.error.message


@pytest.mark.anyio
async def test_create_user_handler_repository_error(event_bus: AsyncMock) -> None:
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

    handler = CreateUserHandler(mock_uow, event_bus)
    command = CreateUserCommand(display_name="Test User", email="test@example.com")
    result = await handler.handle(command)

    assert is_err(result)
    assert result.error.type == ErrorType.UNEXPECTED
    assert "Database connection failed" in result.error.message


@pytest.mark.anyio
async def test_create_user_succeeds_when_event_publication_fails(
    uow: IUnitOfWork,
    event_bus: AsyncMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A committed user is successful even when notification is unavailable."""
    event_bus.publish.side_effect = RuntimeError("event bus unavailable")
    handler = CreateUserHandler(uow, event_bus)

    result = await handler.handle(
        CreateUserCommand(display_name="Alice", email="failure@example.com")
    )

    assert is_ok(result)
    assert "Failed to publish user.created" in caplog.text
    event_bus.publish.assert_awaited_once()


@pytest.mark.anyio
async def test_create_user_does_not_swallow_cancellation(
    uow: IUnitOfWork,
    event_bus: AsyncMock,
) -> None:
    """Cancellation during publication propagates to the caller."""
    event_bus.publish.side_effect = asyncio.CancelledError()
    handler = CreateUserHandler(uow, event_bus)

    with pytest.raises(asyncio.CancelledError):
        await handler.handle(
            CreateUserCommand(display_name="Alice", email="cancel@example.com")
        )
