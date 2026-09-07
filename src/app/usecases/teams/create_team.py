"""Create Team use case."""

import logging
from dataclasses import dataclass

from flow_med import Request, RequestHandler
from flow_res import Err, Ok, Result, combine_all, is_err
from injector import inject

from app.contracts.ports import IUnitOfWork
from app.domain.aggregates.team import Team
from app.domain.value_objects import TeamName
from app.usecases.result import (
    ErrorType,
    UseCaseError,
    UseCaseResultError,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CreateTeamResult:
    id: str


@dataclass(frozen=True)
class CreateTeamCommand(Request[Result[CreateTeamResult, UseCaseResultError]]):
    """Command to create new team."""

    name: str


class CreateTeamHandler(
    RequestHandler[CreateTeamCommand, Result[CreateTeamResult, UseCaseResultError]]
):
    """Handler for CreateTeam command."""

    @inject
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def handle(
        self, request: CreateTeamCommand
    ) -> Result[CreateTeamResult, UseCaseResultError]:
        """Create new team and return as DTO within a Result."""
        team_name_result = TeamName.from_primitive(request.name)

        combined_result = combine_all((team_name_result,)).map_err(
            lambda e: UseCaseError(
                type=ErrorType.VALIDATION_ERROR,
                message=", ".join(str(exc) for exc in e.exceptions),
            )
        )
        if is_err(combined_result):
            return Err(combined_result.error)

        (team_name,) = combined_result.unwrap()

        team = Team.form(name=team_name)

        async with self._uow:
            team_repo = self._uow.GetRepository(Team)
            add_result = await team_repo.add(team)

            if is_err(add_result):
                return Err(add_result.error)

            commit_result = await self._uow.commit()

            if is_err(commit_result):
                return Err(commit_result.error)

            id = team.id.to_primitive()
            return Ok(CreateTeamResult(id=id))
