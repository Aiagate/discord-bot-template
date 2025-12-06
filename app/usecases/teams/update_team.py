"""Update Team use case."""

import logging

from injector import inject

from app.core.result import Err, Ok, Result, combine_all, is_err
from app.domain.aggregates.team import Team
from app.domain.repositories import IUnitOfWork, RepositoryErrorType
from app.domain.value_objects import TeamId, TeamName
from app.mediator import Request, RequestHandler
from app.usecases.result import ErrorType, UseCaseError

logger = logging.getLogger(__name__)


class UpdateTeamResult:
    """Result object for UpdateTeam command."""

    def __init__(self, team_id: str, team_name: str, version: int) -> None:
        self.team_id = team_id
        self.team_name = team_name
        self.version = version


class UpdateTeamCommand(Request[Result[UpdateTeamResult, UseCaseError]]):
    """Command to update team name."""

    def __init__(self, team_id: str, new_name: str) -> None:
        self.team_id = team_id
        self.new_name = new_name


class UpdateTeamHandler(
    RequestHandler[UpdateTeamCommand, Result[UpdateTeamResult, UseCaseError]]
):
    """Handler for UpdateTeam command."""

    @inject
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def handle(
        self, request: UpdateTeamCommand
    ) -> Result[UpdateTeamResult, UseCaseError]:
        """Update team name and return updated team info within a Result."""
        # Validate inputs
        team_id_result = TeamId.from_primitive(request.team_id)
        team_name_result = TeamName.from_primitive(request.new_name)

        combined_result = combine_all((team_id_result, team_name_result))
        if is_err(combined_result):
            error = UseCaseError(
                type=ErrorType.VALIDATION_ERROR, message=str(combined_result.error)
            )
            return Err(error)

        team_id, new_team_name = combined_result.unwrap()

        async with self._uow:
            team_repo = self._uow.GetRepository(Team, TeamId)

            # Get existing team
            get_result = await team_repo.get_by_id(team_id)
            if is_err(get_result):
                repo_error = get_result.error
                if repo_error.type == RepositoryErrorType.NOT_FOUND:
                    error = UseCaseError(
                        type=ErrorType.NOT_FOUND,
                        message=f"Team with id {request.team_id} not found",
                    )
                    return Err(error)
                else:
                    error = UseCaseError(
                        type=ErrorType.UNEXPECTED, message=repo_error.message
                    )
                    return Err(error)

            team = get_result.unwrap()

            # Update team name
            team.change_name(new_team_name)

            # Save updated team (optimistic locking happens here)
            update_result = await team_repo.add(team)
            if is_err(update_result):
                repo_error = update_result.error
                if repo_error.type == RepositoryErrorType.VERSION_CONFLICT:
                    error = UseCaseError(
                        type=ErrorType.CONCURRENCY_CONFLICT,
                        message=(
                            f"Team with id {request.team_id} was modified by another user. "
                            "Please reload and try again."
                        ),
                    )
                    return Err(error)
                else:
                    error = UseCaseError(
                        type=ErrorType.UNEXPECTED, message=repo_error.message
                    )
                    return Err(error)

            # Commit transaction
            commit_result = (await self._uow.commit()).map_err(
                lambda e: UseCaseError(type=ErrorType.UNEXPECTED, message=e.message)
            )

            if is_err(commit_result):
                return commit_result

            updated_team = update_result.unwrap()
            logger.info("Updated team: %s", updated_team)

            return Ok(
                UpdateTeamResult(
                    team_id=updated_team.id.to_primitive(),
                    team_name=updated_team.name.to_primitive(),
                    version=updated_team.version.to_primitive(),
                )
            )
