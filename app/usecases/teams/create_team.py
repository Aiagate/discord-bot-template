"""Create Team use case."""

import logging

from injector import inject

from app.core.result import Ok, Result, is_err
from app.domain.aggregates.team import Team
from app.domain.repositories import IUnitOfWork
from app.domain.value_objects import TeamId, TeamName
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
        team_id_result = TeamId.generate().map_err(
            lambda _: UseCaseError(
                type=ErrorType.UNEXPECTED, message="Failed to generate Team ID."
            )
        )
        team_name_result = TeamName.from_primitive(request.name).map_err(
            lambda e: UseCaseError(type=ErrorType.VALIDATION_ERROR, message=str(e))
        )

        if is_err(team_id_result):
            return team_id_result

        if is_err(team_name_result):
            return team_name_result

        team_id = team_id_result.unwrap()
        team_name = team_name_result.unwrap()

        team = Team(id=team_id, name=team_name)

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
