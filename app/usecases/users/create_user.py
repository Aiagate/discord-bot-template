"""Create User use case."""

import logging

from injector import inject

from app.core.result import Err, Ok, Result
from app.domain.aggregates.user import User
from app.domain.repositories import IUnitOfWork
from app.domain.value_objects import Email, UserId
from app.mediator import Request, RequestHandler
from app.usecases.result import ErrorType, UseCaseError

logger = logging.getLogger(__name__)


class CreateUserResult:
    """Result object for CreateUser command."""

    def __init__(self, user_id: str) -> None:
        self.user_id = user_id


class CreateUserCommand(Request[Result[CreateUserResult, UseCaseError]]):
    """Command to create new user."""

    def __init__(self, name: str, email: str) -> None:
        self.name = name
        self.email = email


class CreateUserHandler(
    RequestHandler[CreateUserCommand, Result[CreateUserResult, UseCaseError]]
):
    """Handler for CreateUser command."""

    @inject
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def handle(
        self, request: CreateUserCommand
    ) -> Result[CreateUserResult, UseCaseError]:
        """Create new user and return as DTO within a Result."""
        try:
            email = Email.from_primitive(request.email)
            user = User(id=UserId.generate(), name=request.name, email=email)
        except ValueError as e:
            # Handle potential validation errors from the domain
            error = UseCaseError(type=ErrorType.VALIDATION_ERROR, message=str(e))
            return Err(error)

        async with self._uow:
            user_repo = self._uow.GetRepository(User)
            save_result = await user_repo.add(user)

            match save_result:
                case Ok(saved_user):
                    logger.info("Created user: %s", saved_user)
                    user_id = saved_user.id.to_primitive()
                    return Ok(CreateUserResult(user_id))
                case Err(repo_error):
                    logger.error(
                        "Repository error in CreateUserHandler: %s", repo_error
                    )
                    uc_error = UseCaseError(
                        type=ErrorType.UNEXPECTED, message=repo_error.message
                    )
                    return Err(uc_error)
