"""Tests for Get Team use case."""

import pytest

from app.core.result import is_err, is_ok
from app.domain.aggregates.team import Team
from app.domain.repositories import IUnitOfWork
from app.domain.value_objects import TeamId, TeamName, Version
from app.usecases.result import ErrorType
from app.usecases.teams.get_team import GetTeamHandler, GetTeamQuery


@pytest.mark.anyio
async def test_get_team_handler(uow: IUnitOfWork) -> None:
    """Test GetTeamHandler retrieves existing team."""
    # First, create a team
    team = Team(
        id=TeamId.generate().expect("TeamId.generate should succeed"),
        _name=TeamName.from_primitive("Alpha Team").expect(
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

    # Now test retrieving it
    handler = GetTeamHandler(uow)
    query = GetTeamQuery(team_id=saved_team.id.to_primitive())
    result = await handler.handle(query)

    assert is_ok(result)
    assert result.value.team.id == saved_team.id.to_primitive()
    assert result.value.team.name == "Alpha Team"


@pytest.mark.anyio
async def test_get_team_handler_not_found(uow: IUnitOfWork) -> None:
    """Test GetTeamHandler returns Err when team doesn't exist."""
    handler = GetTeamHandler(uow)

    # Use a valid ULID that doesn't exist in the database
    query = GetTeamQuery(team_id="01ARZ3NDEKTSV4RRFFQ69G5FAV")
    result = await handler.handle(query)

    assert is_err(result)
    assert result.error.type == ErrorType.NOT_FOUND
