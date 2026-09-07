"""Create User use case."""

import asyncio
import logging
from dataclasses import dataclass

from flow_med import Request, RequestHandler
from flow_res import Err, Ok, Result, combine_all, is_err
from injector import inject

from app.contracts.messages import USER_CREATED_TOPIC, UserCreatedEvent
from app.contracts.ports import IUnitOfWork
from app.contracts.ports.event_bus import IEventBus
from app.domain.aggregates.user import User
from app.domain.value_objects import DisplayName, Email
from app.usecases.result import (
    ErrorType,
    UseCaseError,
    UseCaseResultError,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CreateUserResult:
    id: str


@dataclass(frozen=True)
class CreateUserCommand(Request[Result[CreateUserResult, UseCaseResultError]]):
    """Command to create new user."""

    display_name: str
    email: str


class CreateUserHandler(
    RequestHandler[CreateUserCommand, Result[CreateUserResult, UseCaseResultError]]
):
    """Handler for CreateUser command."""

    @inject
    def __init__(self, uow: IUnitOfWork, event_bus: IEventBus) -> None:
        self._uow = uow
        self._event_bus = event_bus

    async def handle(
        self, request: CreateUserCommand
    ) -> Result[CreateUserResult, UseCaseResultError]:
        """Create new user and return as DTO within a Result."""
        email_result = Email.from_primitive(request.email)
        display_name_result = DisplayName.from_primitive(request.display_name)

        combined_result = combine_all((email_result, display_name_result)).map_err(
            lambda e: UseCaseError(
                type=ErrorType.VALIDATION_ERROR,
                message=", ".join(str(exc) for exc in e.exceptions),
            )
        )
        if is_err(combined_result):
            return Err(combined_result.error)

        email, display_name = combined_result.unwrap()

        user = User.register(display_name=display_name, email=email)

        async with self._uow:
            user_repo = self._uow.GetRepository(User)
            add_result = await user_repo.add(user)

            if is_err(add_result):
                return Err(add_result.error)

            commit_result = await self._uow.commit()

            if is_err(commit_result):
                return Err(commit_result.error)

            user_id = user.id.to_primitive()

        try:
            event = UserCreatedEvent(user_id=user_id)
            await self._event_bus.publish(USER_CREATED_TOPIC, event.to_payload())
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception(
                "Failed to publish %s for user %s",
                USER_CREATED_TOPIC,
                user_id,
            )

        return Ok(CreateUserResult(id=user_id))
