"""Create Team use case."""

import logging

from injector import inject

from app.core.result import Err, Ok, Result
from app.domain.aggregates.team import Team
from app.domain.value_objects import TeamId, TeamName
from app.mediator import Request, RequestHandler
from app.repository import IUnitOfWork
from app.usecases.result import ErrorType, UseCaseError
from app.usecases.teams.team_dto import TeamDTO

logger = logging.getLogger(__name__)


class CreateTeamResult:
    """Result object for CreateTeam command."""

    def __init__(self, team: TeamDTO) -> None:
        self.team = team


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
        try:
            team_name = TeamName.from_primitive(request.name)
            team = Team(id=TeamId.generate(), name=team_name)
        except ValueError as e:
            # Handle potential validation errors from the domain
            error = UseCaseError(type=ErrorType.VALIDATION_ERROR, message=str(e))
            return Err(error)

        async with self._uow:
            team_repo = self._uow.GetRepository(Team)  # IRepository[Team] - save only
            save_result = await team_repo.save(team)

            match save_result:
                case Ok(saved_team):
                    logger.info("Created team: %s", saved_team)
                    team_dto = TeamDTO(
                        id=saved_team.id.to_primitive(),
                        name=saved_team.name.to_primitive(),
                    )
                    return Ok(CreateTeamResult(team_dto))
                case Err(repo_error):
                    logger.error(
                        "Repository error in CreateTeamHandler: %s", repo_error
                    )
                    uc_error = UseCaseError(
                        type=ErrorType.UNEXPECTED, message=repo_error.message
                    )
                    return Err(uc_error)
