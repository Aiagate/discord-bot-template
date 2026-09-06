"""Tests for Unit of Work repository and session lifecycle behavior."""

import pytest

from app.contracts.ports import IUnitOfWork
from app.domain.aggregates.user import User
from app.domain.value_objects import UserId


@pytest.mark.anyio
async def test_uow_reuses_repositories_within_one_session(
    uow: IUnitOfWork,
) -> None:
    """Repositories are cached only inside one active transaction scope."""
    async with uow:
        first = uow.GetRepository(User, UserId)
        second = uow.GetRepository(User, UserId)

        assert first is second

    async with uow:
        next_scope_repository = uow.GetRepository(User, UserId)

    assert next_scope_repository is not first


@pytest.mark.anyio
async def test_uow_repository_access_requires_active_session(
    uow: IUnitOfWork,
) -> None:
    """Repository and transaction operations require an active session."""
    with pytest.raises(RuntimeError):
        uow.GetRepository(User, UserId)

    with pytest.raises(RuntimeError):
        await uow.commit()

    with pytest.raises(RuntimeError):
        await uow.rollback()
