"""Tests for infrastructure repository components."""

import asyncio
from datetime import UTC, datetime

import pytest

from app.core.result import Err, Ok
from app.domain.aggregates.user import User
from app.domain.repositories import IUnitOfWork
from app.domain.value_objects import Email, UserId


@pytest.mark.anyio
async def test_repository_get_non_existent_raises_error(uow: IUnitOfWork) -> None:
    """Test that getting a non-existent entity returns an Err."""
    async with uow:
        repo = uow.GetRepository(User, UserId)
        result = await repo.get_by_id(
            UserId.from_primitive("01ARZ3NDEKTSV4RRFFQ69G5FAV").unwrap()
        )
        assert isinstance(result, Err)


@pytest.mark.anyio
async def test_repository_delete(uow: IUnitOfWork) -> None:
    """Test deleting an entity via the repository."""
    user = User(
        id=UserId.generate().unwrap(),
        name="ToDelete",
        email=Email.from_primitive("delete@example.com").unwrap(),
    )
    saved_user_result = None

    # 1. Create user
    async with uow:
        repo = uow.GetRepository(User, UserId)
        saved_user_result = await repo.add(user)
        assert isinstance(saved_user_result, Ok)
        saved_user = saved_user_result.value
        assert saved_user.id  # ULID should exist
        commit_result = await uow.commit()
        assert isinstance(commit_result, Ok)

    # 2. Delete user
    async with uow:
        repo = uow.GetRepository(User, UserId)
        delete_result = await repo.delete(saved_user)
        assert isinstance(delete_result, Ok)
        commit_result = await uow.commit()
        assert isinstance(commit_result, Ok)

    # 3. Verify user is deleted
    async with uow:
        repo = uow.GetRepository(User, UserId)
        get_result = await repo.get_by_id(saved_user.id)
        assert isinstance(get_result, Err)


@pytest.mark.anyio
async def test_repository_saves_timestamps(uow: IUnitOfWork) -> None:
    """Test that repository correctly saves and retrieves timestamps."""
    before_creation = datetime.now(UTC)

    user = User(
        id=UserId.generate().unwrap(),
        name="TimestampTest",
        email=Email.from_primitive("timestamp@example.com").unwrap(),
    )

    async with uow:
        repo = uow.GetRepository(User)  # IRepository[User] - add only
        save_result = await repo.add(user)
        assert isinstance(save_result, Ok)
        saved_user = save_result.value
        commit_result = await uow.commit()
        assert isinstance(commit_result, Ok)

    after_creation = datetime.now(UTC)

    assert saved_user.created_at >= before_creation
    assert saved_user.created_at <= after_creation
    assert saved_user.updated_at >= before_creation
    assert saved_user.updated_at <= after_creation


@pytest.mark.anyio
async def test_repository_updates_timestamp_on_save(uow: IUnitOfWork) -> None:
    """Test that updated_at is automatically updated when saving existing entity."""
    user = User(
        id=UserId.generate().unwrap(),
        name="UpdateTest",
        email=Email.from_primitive("update@example.com").unwrap(),
    )

    async with uow:
        repo = uow.GetRepository(User)  # IRepository[User] - add only
        save_result = await repo.add(user)
        assert isinstance(save_result, Ok)
        saved_user = save_result.value
        original_updated_at = saved_user.updated_at
        commit_result = await uow.commit()
        assert isinstance(commit_result, Ok)

    await asyncio.sleep(0.01)

    saved_user.email = Email.from_primitive("updated@example.com").unwrap()

    async with uow:
        repo = uow.GetRepository(User)  # IRepository[User] - add only
        update_result = await repo.add(saved_user)
        assert isinstance(update_result, Ok)
        updated_user = update_result.value
        commit_result = await uow.commit()
        assert isinstance(commit_result, Ok)

    assert updated_user.updated_at > original_updated_at
    assert updated_user.created_at == saved_user.created_at
