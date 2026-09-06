"""Tests for current membership period uniqueness."""

import pytest
from flow_res import is_err, is_ok

from app.contracts.ports import IUnitOfWork
from app.domain.aggregates.team_membership import TeamMembership
from app.domain.repositories import RepositoryErrorType
from app.domain.value_objects import MembershipId, TeamId, UserId


@pytest.mark.anyio
async def test_partial_index_allows_leaved_history_but_rejects_current_duplicate(
    uow: IUnitOfWork,
) -> None:
    """Only PENDING and ACTIVE periods participate in uniqueness."""
    team_id = TeamId.generate().expect("valid id")
    user_id = UserId.generate().expect("valid id")
    first = TeamMembership.request_join(team_id=team_id, user_id=user_id)
    duplicate = TeamMembership.request_join(team_id=team_id, user_id=user_id)

    async with uow:
        repository = uow.GetRepository(TeamMembership, MembershipId)
        first_result = await repository.add(first)
        assert is_ok(first_result)
        await uow.commit()

    async with uow:
        repository = uow.GetRepository(TeamMembership)
        duplicate_result = await repository.add(duplicate)
        assert is_err(duplicate_result)
        assert duplicate_result.error.type is RepositoryErrorType.ALREADY_EXISTS

    first.leave()
    async with uow:
        repository = uow.GetRepository(TeamMembership)
        leave_result = await repository.update(first)
        assert is_ok(leave_result)
        await uow.commit()

    async with uow:
        repository = uow.GetRepository(TeamMembership)
        rejoin = await repository.add(
            TeamMembership.request_join(team_id=team_id, user_id=user_id)
        )
        assert is_ok(rejoin)
        await uow.commit()


@pytest.mark.anyio
async def test_current_membership_update_retains_optimistic_locking(
    uow: IUnitOfWork,
) -> None:
    """Enrollment periods retain repository version conflict behavior."""
    membership = TeamMembership.join(
        team_id=TeamId.generate().expect("valid id"),
        user_id=UserId.generate().expect("valid id"),
    )

    async with uow:
        repository = uow.GetRepository(TeamMembership)
        saved = await repository.add(membership)
        assert is_ok(saved)
        await uow.commit()

    async with uow:
        repository = uow.GetRepository(TeamMembership, MembershipId)
        first_loaded = await repository.get_by_id(membership.id)
        second_loaded = await repository.get_by_id(membership.id)
        assert is_ok(first_loaded)
        assert is_ok(second_loaded)

    first_loaded.value.leave()
    second_loaded.value.change_role(membership.role)

    async with uow:
        repository = uow.GetRepository(TeamMembership)
        first_update = await repository.update(first_loaded.value)
        assert is_ok(first_update)
        await uow.commit()

    async with uow:
        repository = uow.GetRepository(TeamMembership)
        second_update = await repository.update(second_loaded.value)

    assert is_err(second_update)
    assert second_update.error.type is RepositoryErrorType.VERSION_CONFLICT
