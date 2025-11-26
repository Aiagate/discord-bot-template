"""Get User use case."""

import logging

from injector import inject

from app.core.result import Err, Ok, Result
from app.domain.aggregates.user import User
from app.mediator import Request, RequestHandler
from app.repository import IUnitOfWork
from app.usecases.result import ErrorType, UseCaseError
from app.usecases.users.user_dto import UserDTO

logger = logging.getLogger(__name__)


class GetUserResult:
    """Result object for GetUser query."""

    def __init__(self, user: UserDTO) -> None:
        self.user = user


class GetUserQuery(Request[Result[GetUserResult, UseCaseError]]):
    """Query to get user by ID."""

    def __init__(self, user_id: int) -> None:
        self.user_id = user_id


class GetUserHandler(RequestHandler[GetUserQuery, Result[GetUserResult, UseCaseError]]):
    """Handler for GetUser query."""

    @inject
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def handle(
        self, request: GetUserQuery
    ) -> Result[GetUserResult, UseCaseError]:
        """Get user by ID, returning a DTO within a Result."""
        async with self._uow:
            user_repo = self._uow.GetRepository(User, int)
            user_result = await user_repo.get_by_id(request.user_id)

            match user_result:
                case Ok(user):
                    logger.debug("GetUserHandler: user=%s", user)
                    user_dto = UserDTO(id=user.id, name=user.name, email=user.email)
                    return Ok(GetUserResult(user_dto))
                case Err(repo_error):
                    logger.error("Repository error in GetUserHandler: %s", repo_error)
                    # Map repository error to use case error
                    uc_error = UseCaseError(
                        type=ErrorType.NOT_FOUND, message=repo_error.message
                    )
                    return Err(uc_error)
