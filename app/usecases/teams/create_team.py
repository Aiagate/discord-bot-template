"""Create Team use case."""

import logging

from injector import inject

from app.core.result import Err, Ok, Result, combine_all, is_err
from app.domain.aggregates.team import Team
from app.domain.repositories import IUnitOfWork
from app.domain.value_objects import TeamId, TeamName, Version
from app.mediator import Request, RequestHandler
from app.usecases.result import ErrorType, UseCaseError

logger = logging.getLogger(__name__)


class CreateTeamResult:
    """Result object for CreateTeam command."""

    def __init__(self, team_id: str) -> None:
        self.team_id = team_id


class CreateTeamCommand(Request[Result[CreateTeamResult, UseCaseError]]):
    """Command to create new team."""

    def __init__(self, name: str) -> None:
        self.name = name


class CreateTeamHandler(
    RequestHandler[CreateTeamCommand, Result[CreateTeamResult, UseCaseError]]
):
    """Handler for CreateTeam command."""

    @inject
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def handle(
        self, request: CreateTeamCommand
    ) -> Result[CreateTeamResult, UseCaseError]:
        """Create new team and return as DTO within a Result."""
        team_id_result = TeamId.generate()
        team_name_result = TeamName.from_primitive(request.name)
        version_result = Version.from_primitive(0)

        combined_result = combine_all(
            (team_id_result, team_name_result, version_result)
        )
        if is_err(combined_result):
            error = UseCaseError(
                type=ErrorType.VALIDATION_ERROR, message=str(combined_result.error)
            )
            return Err(error)

        team_id, team_name, version = combined_result.unwrap()

        team = Team(id=team_id, name=team_name, version=version)

        async with self._uow:
            team_repo = self._uow.GetRepository(Team)
            add_result = (await team_repo.add(team)).map_err(
                lambda e: UseCaseError(type=ErrorType.UNEXPECTED, message=e.message)
            )

            if is_err(add_result):
                return add_result

            commit_result = (await self._uow.commit()).map_err(
                lambda e: UseCaseError(type=ErrorType.UNEXPECTED, message=e.message)
            )

            if is_err(commit_result):
                return commit_result

            logger.info("Created team: %s", team)
            team_id = team.id.to_primitive()
            return Ok(CreateTeamResult(team_id))
