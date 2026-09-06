"""Save a Discord ChatMessage use case."""

from dataclasses import dataclass
from datetime import datetime

from flow_med import Request, RequestHandler
from flow_res import Err, Ok, Result, is_err
from injector import inject

from app.contracts.ports import IUnitOfWork
from app.domain.aggregates.chat_message import ChatMessage
from app.domain.value_objects.message_content import MessageContent
from app.usecases.result import ErrorType, UseCaseError


@dataclass(frozen=True)
class SaveChatResult:
    """Saved chat result payload."""

    id: str


@dataclass(frozen=True)
class SaveDiscordChatCommand(Request[Result[SaveChatResult, UseCaseError]]):
    """Command to persist a Discord message with its external occurrence time."""

    external_sender_id: str
    guild_id: str
    channel_id: str
    content: str
    occurred_at: datetime


class SaveDiscordChatHandler(
    RequestHandler[SaveDiscordChatCommand, Result[SaveChatResult, UseCaseError]]
):
    """Handle SaveChatCommand."""

    @inject
    def __init__(
        self,
        uow: IUnitOfWork,
    ) -> None:
        self._uow = uow

    async def handle(
        self, request: SaveDiscordChatCommand
    ) -> Result[SaveChatResult, UseCaseError]:
        """Persist an incoming Discord message."""
        try:
            message = ChatMessage.create_discord(
                guild_id=request.guild_id,
                channel_id=request.channel_id,
                external_sender_id=request.external_sender_id,
                content=MessageContent.text(request.content),
                occurred_at=request.occurred_at,
            )
        except (TypeError, ValueError) as error:
            return Err(
                UseCaseError(type=ErrorType.VALIDATION_ERROR, message=str(error))
            )

        async with self._uow:
            repository = self._uow.GetRepository(ChatMessage)
            add_result = await repository.add(message)
            if is_err(add_result):
                return Err(
                    UseCaseError(
                        type=ErrorType.UNEXPECTED,
                        message="Failed to save chat message",
                    )
                )

            commit_result = await self._uow.commit()
            if is_err(commit_result):
                return Err(
                    UseCaseError(
                        type=ErrorType.UNEXPECTED,
                        message="Failed to persist chat message",
                    )
                )

            return Ok(SaveChatResult(id=add_result.value.id.to_primitive()))
