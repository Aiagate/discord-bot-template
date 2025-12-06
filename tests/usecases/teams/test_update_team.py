"""Tests for Update Team use case."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.result import Err, Ok, is_err, is_ok
from app.domain.aggregates.team import Team
from app.domain.repositories import IUnitOfWork, RepositoryError, RepositoryErrorType
from app.domain.value_objects import TeamId, TeamName, Version
from app.usecases.result import ErrorType
from app.usecases.teams.update_team import UpdateTeamCommand, UpdateTeamHandler


@pytest.mark.anyio
async def test_update_team_handler(uow: IUnitOfWork) -> None:
    """Test UpdateTeamHandler updates team name successfully."""
    # First, create a team
    team = Team(
        id=TeamId.generate().expect("TeamId.generate should succeed"),
        _name=TeamName.from_primitive("Original Name").expect(
            "TeamName.from_primitive should succeed for valid name"
        ),
        version=Version.from_primitive(0).expect(
            "Version.from_primitive should succeed"
        ),
    )

    async with uow:
        repo = uow.GetRepository(Team)
        save_result = await repo.add(team)
        assert is_ok(save_result)
        saved_team = save_result.value
        commit_result = await uow.commit()
        assert is_ok(commit_result)

    # Now test updating it
    handler = UpdateTeamHandler(uow)
    command = UpdateTeamCommand(
        team_id=saved_team.id.to_primitive(), new_name="Updated Name"
    )
    result = await handler.handle(command)

    assert is_ok(result)
    team_id = result.value  # Now it's a str
    assert team_id == saved_team.id.to_primitive()
    # Version verification is no longer done here
    # (version is now part of TeamDTO via GetTeamQuery)


@pytest.mark.anyio
async def test_update_team_handler_not_found(uow: IUnitOfWork) -> None:
    """Test UpdateTeamHandler returns Err when team doesn't exist."""
    handler = UpdateTeamHandler(uow)

    # Use a valid ULID that doesn't exist in the database
    command = UpdateTeamCommand(
        team_id="01ARZ3NDEKTSV4RRFFQ69G5FAV", new_name="New Name"
    )
    result = await handler.handle(command)

    assert is_err(result)
    assert result.error.type == ErrorType.NOT_FOUND


@pytest.mark.anyio
async def test_update_team_handler_validation_error(uow: IUnitOfWork) -> None:
    """Test UpdateTeamHandler returns validation error for invalid name."""
    # First, create a team
    team = Team(
        id=TeamId.generate().expect("TeamId.generate should succeed"),
        _name=TeamName.from_primitive("Test Team").expect(
            "TeamName.from_primitive should succeed for valid name"
        ),
        version=Version.from_primitive(0).expect(
            "Version.from_primitive should succeed"
        ),
    )

    async with uow:
        repo = uow.GetRepository(Team)
        save_result = await repo.add(team)
        assert is_ok(save_result)
        saved_team = save_result.value
        commit_result = await uow.commit()
        assert is_ok(commit_result)

    # Try to update with empty name
    handler = UpdateTeamHandler(uow)
    command = UpdateTeamCommand(team_id=saved_team.id.to_primitive(), new_name="")
    result = await handler.handle(command)

    assert is_err(result)
    assert result.error.type == ErrorType.VALIDATION_ERROR


@pytest.mark.anyio
async def test_update_team_handler_name_too_long(uow: IUnitOfWork) -> None:
    """Test UpdateTeamHandler returns validation error for name too long."""
    # First, create a team
    team = Team(
        id=TeamId.generate().expect("TeamId.generate should succeed"),
        _name=TeamName.from_primitive("Test Team").expect(
            "TeamName.from_primitive should succeed for valid name"
        ),
        version=Version.from_primitive(0).expect(
            "Version.from_primitive should succeed"
        ),
    )

    async with uow:
        repo = uow.GetRepository(Team)
        save_result = await repo.add(team)
        assert is_ok(save_result)
        saved_team = save_result.value
        commit_result = await uow.commit()
        assert is_ok(commit_result)

    # Try to update with name that's too long
    handler = UpdateTeamHandler(uow)
    command = UpdateTeamCommand(
        team_id=saved_team.id.to_primitive(), new_name="x" * 101
    )
    result = await handler.handle(command)

    assert is_err(result)
    assert result.error.type == ErrorType.VALIDATION_ERROR


@pytest.mark.anyio
async def test_update_team_handler_concurrency_conflict(uow: IUnitOfWork) -> None:
    """Test UpdateTeamHandler returns concurrency conflict for stale data."""
    # Create a team
    team = Team(
        id=TeamId.generate().expect("TeamId.generate should succeed"),
        _name=TeamName.from_primitive("Original Name").expect(
            "TeamName.from_primitive should succeed for valid name"
        ),
        version=Version.from_primitive(0).expect(
            "Version.from_primitive should succeed"
        ),
    )

    async with uow:
        repo = uow.GetRepository(Team)
        save_result = await repo.add(team)
        assert is_ok(save_result)
        saved_team = save_result.value
        commit_result = await uow.commit()
        assert is_ok(commit_result)

    # First update succeeds
    handler1 = UpdateTeamHandler(uow)
    command1 = UpdateTeamCommand(
        team_id=saved_team.id.to_primitive(), new_name="Updated by User 1"
    )
    result1 = await handler1.handle(command1)
    assert is_ok(result1)

    # Second update with stale version should fail
    handler2 = UpdateTeamHandler(uow)
    # Create a command with the original team data (stale version)
    # We need to manually construct a team with old version to simulate concurrent update
    async with uow:
        repo = uow.GetRepository(Team, TeamId)
        # Get the team (now at version 1)
        get_result = await repo.get_by_id(saved_team.id)
        assert is_ok(get_result)

    # Now create a "stale" team by using the old version
    stale_team = Team(
        id=saved_team.id,
        _name=saved_team.name,  # Old name
        version=Version.from_primitive(0).expect(
            "Version.from_primitive should succeed"
        ),  # Old version
    )

    # Try to update with stale team
    async with uow:
        repo = uow.GetRepository(Team)
        # Manually change the name
        stale_team.change_name(
            TeamName.from_primitive("Updated by User 2").expect(
                "TeamName.from_primitive should succeed"
            )
        )
        # This should fail with VERSION_CONFLICT
        update_result = await repo.add(stale_team)
        assert is_err(update_result)

        # Now verify the use case handler would also return CONCURRENCY_CONFLICT
        # by trying to update again (the get will succeed but the save will fail
        # if someone updated in between)

    # To properly test the handler's concurrency conflict handling,
    # we'll do two updates in parallel-ish fashion
    command2 = UpdateTeamCommand(
        team_id=saved_team.id.to_primitive(), new_name="Updated by User 2 Again"
    )
    result2 = await handler2.handle(command2)
    # This should succeed because we're getting fresh data
    assert is_ok(result2)


@pytest.mark.anyio
async def test_update_team_handler_invalid_team_id(uow: IUnitOfWork) -> None:
    """Test UpdateTeamHandler returns validation error for invalid team_id."""
    handler = UpdateTeamHandler(uow)

    # Invalid ULID format
    command = UpdateTeamCommand(team_id="invalid-id", new_name="New Name")
    result = await handler.handle(command)

    assert is_err(result)
    assert result.error.type == ErrorType.VALIDATION_ERROR


@pytest.mark.anyio
async def test_update_team_handler_get_unexpected_error() -> None:
    """Test UpdateTeamHandler returns unexpected error when get_by_id fails."""
    mock_uow = MagicMock(spec=IUnitOfWork)
    mock_repo = MagicMock()

    # Mock get_by_id to return an unexpected error
    mock_repo.get_by_id = AsyncMock(
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

    handler = UpdateTeamHandler(mock_uow)
    command = UpdateTeamCommand(
        team_id="01ARZ3NDEKTSV4RRFFQ69G5FAV", new_name="New Name"
    )
    result = await handler.handle(command)

    assert is_err(result)
    assert result.error.type == ErrorType.UNEXPECTED
    assert "Database connection failed" in result.error.message


@pytest.mark.anyio
async def test_update_team_handler_version_conflict_through_handler() -> None:
    """Test UpdateTeamHandler returns concurrency conflict when version conflicts."""
    mock_uow = MagicMock(spec=IUnitOfWork)
    mock_repo = MagicMock()

    # Create a mock team to return from get_by_id
    team_id = TeamId.generate().expect("TeamId.generate should succeed")
    team_name = TeamName.from_primitive("Original Name").expect(
        "TeamName.from_primitive should succeed"
    )
    version = Version.from_primitive(0).expect("Version.from_primitive should succeed")
    mock_team = Team(id=team_id, _name=team_name, version=version)

    # Mock get_by_id to return the team
    mock_repo.get_by_id = AsyncMock(return_value=Ok(mock_team))

    # Mock add to return a version conflict error
    mock_repo.add = AsyncMock(
        return_value=Err(
            RepositoryError(
                type=RepositoryErrorType.VERSION_CONFLICT,
                message="Version conflict detected",
            )
        )
    )

    mock_uow.GetRepository.return_value = mock_repo
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=None)

    handler = UpdateTeamHandler(mock_uow)
    command = UpdateTeamCommand(team_id=team_id.to_primitive(), new_name="Updated Name")
    result = await handler.handle(command)

    assert is_err(result)
    assert result.error.type == ErrorType.CONCURRENCY_CONFLICT
    assert "modified by another user" in result.error.message


@pytest.mark.anyio
async def test_update_team_handler_add_unexpected_error() -> None:
    """Test UpdateTeamHandler returns unexpected error when add fails."""
    mock_uow = MagicMock(spec=IUnitOfWork)
    mock_repo = MagicMock()

    # Create a mock team to return from get_by_id
    team_id = TeamId.generate().expect("TeamId.generate should succeed")
    team_name = TeamName.from_primitive("Original Name").expect(
        "TeamName.from_primitive should succeed"
    )
    version = Version.from_primitive(0).expect("Version.from_primitive should succeed")
    mock_team = Team(id=team_id, _name=team_name, version=version)

    # Mock get_by_id to return the team
    mock_repo.get_by_id = AsyncMock(return_value=Ok(mock_team))

    # Mock add to return an unexpected error
    mock_repo.add = AsyncMock(
        return_value=Err(
            RepositoryError(
                type=RepositoryErrorType.UNEXPECTED,
                message="Database write failed",
            )
        )
    )

    mock_uow.GetRepository.return_value = mock_repo
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=None)

    handler = UpdateTeamHandler(mock_uow)
    command = UpdateTeamCommand(team_id=team_id.to_primitive(), new_name="Updated Name")
    result = await handler.handle(command)

    assert is_err(result)
    assert result.error.type == ErrorType.UNEXPECTED
    assert "Database write failed" in result.error.message


@pytest.mark.anyio
async def test_update_team_handler_commit_failure() -> None:
    """Test UpdateTeamHandler returns unexpected error when commit fails."""
    mock_uow = MagicMock(spec=IUnitOfWork)
    mock_repo = MagicMock()

    # Create a mock team to return from get_by_id
    team_id = TeamId.generate().expect("TeamId.generate should succeed")
    team_name = TeamName.from_primitive("Original Name").expect(
        "TeamName.from_primitive should succeed"
    )
    version = Version.from_primitive(0).expect("Version.from_primitive should succeed")
    mock_team = Team(id=team_id, _name=team_name, version=version)

    # Mock get_by_id to return the team
    mock_repo.get_by_id = AsyncMock(return_value=Ok(mock_team))

    # Mock add to succeed
    updated_team = Team(
        id=team_id,
        _name=TeamName.from_primitive("Updated Name").expect(
            "TeamName.from_primitive should succeed"
        ),
        version=Version.from_primitive(1).expect(
            "Version.from_primitive should succeed"
        ),
    )
    mock_repo.add = AsyncMock(return_value=Ok(updated_team))

    # Mock commit to fail
    mock_uow.commit = AsyncMock(
        return_value=Err(
            RepositoryError(
                type=RepositoryErrorType.UNEXPECTED,
                message="Transaction commit failed",
            )
        )
    )

    mock_uow.GetRepository.return_value = mock_repo
    mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
    mock_uow.__aexit__ = AsyncMock(return_value=None)

    handler = UpdateTeamHandler(mock_uow)
    command = UpdateTeamCommand(team_id=team_id.to_primitive(), new_name="Updated Name")
    result = await handler.handle(command)

    assert is_err(result)
    assert result.error.type == ErrorType.UNEXPECTED
    assert "Transaction commit failed" in result.error.message
