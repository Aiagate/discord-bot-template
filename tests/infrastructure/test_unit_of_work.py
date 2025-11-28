"""Tests for infrastructure Unit of Work component."""

import pytest

from app.core.result import Ok
from app.domain.aggregates.user import User
from app.domain.repositories import IUnitOfWork
from app.domain.value_objects import Email, UserId


@pytest.mark.anyio
async def test_uow_rollback(uow: IUnitOfWork) -> None:
    """Test that the Unit of Work rolls back transactions on error."""
    user = User(
        id=UserId.generate(),
        name="Rollback Test",
        email=Email.from_primitive("rollback@example.com"),
    )
    initial_user = None

    # 1. Save a user and get its ID
    async with uow:
        repo = uow.GetRepository(User, UserId)
        save_result = await repo.add(user)
        assert isinstance(save_result, Ok)
        initial_user = save_result.value
        assert initial_user.id  # ULID should exist

    # 2. Attempt to update the user in a failing transaction
    try:
        async with uow:
            repo = uow.GetRepository(User, UserId)
            get_result = await repo.get_by_id(initial_user.id)
            assert isinstance(get_result, Ok)
            user_to_update = get_result.value
            user_to_update.name = "Updated Name"
            await repo.add(user_to_update)
            raise ValueError("Simulating a failure")
    except ValueError:
        # Expected failure
        pass

    # 3. Verify that the name was NOT updated
    async with uow:
        repo = uow.GetRepository(User, UserId)
        retrieved_result = await repo.get_by_id(initial_user.id)
        assert isinstance(retrieved_result, Ok)
        retrieved_user = retrieved_result.value
        assert retrieved_user.name == "Rollback Test"
