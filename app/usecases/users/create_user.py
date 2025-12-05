"""Create User use case."""

import logging

from injector import inject

from app.core.result import Err, Ok, Result, combine_all, is_err
from app.domain.aggregates.user import User
from app.domain.repositories import IUnitOfWork
from app.domain.value_objects import DisplayName, Email, UserId
from app.mediator import Request, RequestHandler
from app.usecases.result import ErrorType, UseCaseError

logger = logging.getLogger(__name__)


class CreateUserResult:
    """Result object for CreateUser command."""

    def __init__(self, user_id: str) -> None:
        self.user_id = user_id


class CreateUserCommand(Request[Result[CreateUserResult, UseCaseError]]):
    """Command to create new user."""

    def __init__(self, display_name: str, email: str) -> None:
        self.display_name = display_name
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
        user_id_result = UserId.generate()
        email_result = Email.from_primitive(request.email)
        display_name_result = DisplayName.from_primitive(request.display_name)

        combined_result = combine_all(
            (user_id_result, email_result, display_name_result)
        )
        if is_err(combined_result):
            error = UseCaseError(
                type=ErrorType.VALIDATION_ERROR, message=str(combined_result.error)
            )
            return Err(error)

        user_id, email, display_name = combined_result.unwrap()

        user = User(id=user_id, display_name=display_name, email=email)

        async with self._uow:
            user_repo = self._uow.GetRepository(User)
            add_result = (await user_repo.add(user)).map_err(
                lambda e: UseCaseError(type=ErrorType.UNEXPECTED, message=e.message)
            )

            if is_err(add_result):
                return add_result

            commit_result = (await self._uow.commit()).map_err(
                lambda e: UseCaseError(type=ErrorType.UNEXPECTED, message=e.message)
            )

            if is_err(commit_result):
                return commit_result

            logger.info("Created user: %s", user)
            user_id = user.id.to_primitive()
            return Ok(CreateUserResult(user_id))
