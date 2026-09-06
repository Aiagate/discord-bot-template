"""Save a LINE ChatMessage use case."""

from dataclasses import dataclass
from datetime import datetime

from flow_med import Request, RequestHandler
from flow_res import Err, Ok, Result, is_err
from injector import inject

from app.contracts.ports import IUnitOfWork
from app.domain.aggregates.chat_message import ChatMessage
from app.domain.value_objects.conversation_scope import LineConversationScope
from app.domain.value_objects.message_content import MessageContent
from app.usecases.result import ErrorType, UseCaseError


@dataclass(frozen=True)
class SaveChatResult:
    """Saved chat result payload."""

    id: str


@dataclass(frozen=True)
class SaveLineChatCommand(Request[Result[SaveChatResult, UseCaseError]]):
    """Command to persist a LINE message with its external occurrence time."""

    external_sender_id: str
    conversation_scope: LineConversationScope
    content: str
    occurred_at: datetime


class SaveLineChatHandler(
    RequestHandler[SaveLineChatCommand, Result[SaveChatResult, UseCaseError]]
):
    """Handle SaveChatCommand."""

    @inject
    def __init__(
        self,
        uow: IUnitOfWork,
    ) -> None:
        self._uow = uow

    async def handle(
        self, request: SaveLineChatCommand
    ) -> Result[SaveChatResult, UseCaseError]:
        """Persist an incoming LINE message."""
        try:
            message = ChatMessage.create_line(
                conversation_scope=request.conversation_scope,
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
