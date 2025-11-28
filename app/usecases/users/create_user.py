"""Create User use case."""

import logging

from injector import inject

from app.core.result import Err, Ok, Result
from app.domain.aggregates.user import User
from app.domain.value_objects import Email, UserId
from app.mediator import Request, RequestHandler
from app.repository import IUnitOfWork
from app.usecases.result import ErrorType, UseCaseError
from app.usecases.users.user_dto import UserDTO

logger = logging.getLogger(__name__)


class CreateUserResult:
    """Result object for CreateUser command."""

    def __init__(self, user: UserDTO) -> None:
        self.user = user


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
            user_repo = self._uow.GetRepository(User)  # IRepository[User] - add only
            save_result = await user_repo.add(user)

            match save_result:
                case Ok(saved_user):
                    logger.info("Created user: %s", saved_user)
                    user_dto = UserDTO(
                        id=saved_user.id.to_primitive(),
                        name=saved_user.name,
                        email=saved_user.email.to_primitive(),
                    )
                    return Ok(CreateUserResult(user_dto))
                case Err(repo_error):
                    logger.error(
                        "Repository error in CreateUserHandler: %s", repo_error
                    )
                    uc_error = UseCaseError(
                        type=ErrorType.UNEXPECTED, message=repo_error.message
                    )
                    return Err(uc_error)
