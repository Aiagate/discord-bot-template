"""Get Team use case."""

import logging

from injector import inject

from app.core.result import Err, Ok, Result
from app.domain.aggregates.team import Team
from app.domain.repositories import IUnitOfWork
from app.domain.value_objects import TeamId
from app.mediator import Request, RequestHandler
from app.usecases.result import ErrorType, UseCaseError
from app.usecases.teams.team_dto import TeamDTO

logger = logging.getLogger(__name__)


class GetTeamResult:
    """Result object for GetTeam query."""

    def __init__(self, team: TeamDTO) -> None:
        self.team = team


class GetTeamQuery(Request[Result[GetTeamResult, UseCaseError]]):
    """Query to get team by ID."""

    def __init__(self, team_id: str) -> None:
        self.team_id = team_id


class GetTeamHandler(RequestHandler[GetTeamQuery, Result[GetTeamResult, UseCaseError]]):
    """Handler for GetTeam query."""

    @inject
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def handle(
        self, request: GetTeamQuery
    ) -> Result[GetTeamResult, UseCaseError]:
        """Get team by ID, returning a DTO within a Result."""
        team_id_result = TeamId.from_primitive(request.team_id)
        if isinstance(team_id_result, Err):
            return Err(
                UseCaseError(
                    type=ErrorType.VALIDATION_ERROR,
                    message="Invalid Team ID format.",
                )
            )
        team_id = team_id_result.unwrap()

        async with self._uow:
            team_repo = self._uow.GetRepository(Team, TeamId)
            team_result = await team_repo.get_by_id(team_id)

            match team_result:
                case Ok(team):
                    logger.debug("GetTeamHandler: team=%s", team)
                    team_dto = TeamDTO(
                        id=team.id.to_primitive(),
                        name=team.name.to_primitive(),
                    )
                    return Ok(GetTeamResult(team_dto))
                case Err(repo_error):
                    uc_error = UseCaseError(
                        type=ErrorType.NOT_FOUND, message=repo_error.message
                    )
                    return Err(uc_error)
