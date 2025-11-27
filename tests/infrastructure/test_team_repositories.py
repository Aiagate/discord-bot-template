"""Tests for Team repository components."""

import asyncio
from datetime import UTC, datetime

import pytest

from app.core.result import Err, Ok
from app.domain.aggregates.team import Team
from app.domain.value_objects import TeamId, TeamName
from app.repository import IUnitOfWork


@pytest.mark.anyio
async def test_team_repository_save_and_get(uow: IUnitOfWork) -> None:
    """Test saving and retrieving a team."""
    team = Team(
        id=TeamId.generate(),
        name=TeamName.from_primitive("Alpha Team"),
    )

    # Save team
    async with uow:
        repo = uow.GetRepository(Team)
        save_result = await repo.save(team)
        assert isinstance(save_result, Ok)
        saved_team = save_result.value
        assert saved_team.id == team.id
        assert saved_team.name.to_primitive() == "Alpha Team"

    # Retrieve team
    async with uow:
        repo = uow.GetRepository(Team, TeamId)
        get_result = await repo.get_by_id(saved_team.id)
        assert isinstance(get_result, Ok)
        retrieved_team = get_result.value
        assert retrieved_team.id == saved_team.id
        assert retrieved_team.name.to_primitive() == "Alpha Team"


@pytest.mark.anyio
async def test_team_repository_get_non_existent_raises_error(
    uow: IUnitOfWork,
) -> None:
    """Test that getting a non-existent team returns an Err."""
    async with uow:
        repo = uow.GetRepository(Team, TeamId)
        result = await repo.get_by_id(
            TeamId.from_primitive("01ARZ3NDEKTSV4RRFFQ69G5FAV")
        )
        assert isinstance(result, Err)


@pytest.mark.anyio
async def test_team_repository_delete(uow: IUnitOfWork) -> None:
    """Test deleting a team via the repository."""
    team = Team(
        id=TeamId.generate(),
        name=TeamName.from_primitive("ToDelete Team"),
    )

    # 1. Create team
    async with uow:
        repo = uow.GetRepository(Team, TeamId)
        saved_team_result = await repo.save(team)
        assert isinstance(saved_team_result, Ok)
        saved_team = saved_team_result.value

    # 2. Delete team
    async with uow:
        repo = uow.GetRepository(Team, TeamId)
        delete_result = await repo.delete(saved_team.id)
        assert isinstance(delete_result, Ok)

    # 3. Verify team is deleted
    async with uow:
        repo = uow.GetRepository(Team, TeamId)
        get_result = await repo.get_by_id(saved_team.id)
        assert isinstance(get_result, Err)


@pytest.mark.anyio
async def test_team_repository_saves_timestamps(uow: IUnitOfWork) -> None:
    """Test that repository correctly saves and retrieves timestamps."""
    before_creation = datetime.now(UTC)

    team = Team(
        id=TeamId.generate(),
        name=TeamName.from_primitive("Timestamp Team"),
    )

    async with uow:
        repo = uow.GetRepository(Team)
        save_result = await repo.save(team)
        assert isinstance(save_result, Ok)
        saved_team = save_result.value

    after_creation = datetime.now(UTC)

    assert saved_team.created_at >= before_creation
    assert saved_team.created_at <= after_creation
    assert saved_team.updated_at >= before_creation
    assert saved_team.updated_at <= after_creation


@pytest.mark.anyio
async def test_team_repository_updates_timestamp_on_save(uow: IUnitOfWork) -> None:
    """Test that updated_at is automatically updated when saving existing team."""
    team = Team(
        id=TeamId.generate(),
        name=TeamName.from_primitive("Update Team"),
    )

    async with uow:
        repo = uow.GetRepository(Team)
        save_result = await repo.save(team)
        assert isinstance(save_result, Ok)
        saved_team = save_result.value
        original_updated_at = saved_team.updated_at

    await asyncio.sleep(0.01)

    saved_team.name = TeamName.from_primitive("Updated Team")

    async with uow:
        repo = uow.GetRepository(Team)
        update_result = await repo.save(saved_team)
        assert isinstance(update_result, Ok)
        updated_team = update_result.value
        # SQLite doesn't support microsecond precision well,
        # so we just check it's not exactly the same
        assert updated_team.updated_at != original_updated_at
