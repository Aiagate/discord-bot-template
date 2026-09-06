"""Read-only chat history query application port."""

from __future__ import annotations

from abc import ABC, abstractmethod

from flow_res import Result

from app.domain.aggregates.chat_message import ChatMessage
from app.domain.repositories.interfaces import RepositoryError
from app.domain.value_objects.conversation_scope import ConversationScope


class IChatHistoryQuery(ABC):
    """Query port for retrieving messages within one conversation scope."""

    @abstractmethod
    async def get_recent_history(
        self,
        conversation_scope: ConversationScope,
        limit: int = 20,
    ) -> Result[list[ChatMessage], RepositoryError]:
        """Get recent messages in chronological order."""
        pass
