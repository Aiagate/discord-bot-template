"""Repository interfaces for domain layer."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Protocol

from app.core.result import Result


class RepositoryErrorType(Enum):
    """Enum for repository error types."""

    NOT_FOUND = auto()
    UNEXPECTED = auto()


@dataclass(frozen=True)
class RepositoryError:
    """Represents a specific error from a repository."""

    type: RepositoryErrorType
    message: str


class IRepository[T, K](Protocol):
    """Generic repository interface using structural subtyping.

    Type Parameters:
        T: Entity type (e.g., User, Order)
        K: Primary key type (e.g., int, str, UUID)
    """

    async def get_by_id(self, id: K) -> Result[T, RepositoryError]:
        """Get entity by ID."""
        ...

    async def save(self, entity: T) -> Result[T, RepositoryError]:
        """Save or update entity."""
        ...

    async def delete(self, id: K) -> Result[None, RepositoryError]:
        """Delete entity by ID."""
        ...


class IUnitOfWork(ABC):
    """Unit of Work interface for transaction management."""

    @abstractmethod
    def GetRepository[T, K](
        self, entity_type: type[T], key_type: type[K]
    ) -> IRepository[T, K]:
        """Get repository for entity type T with primary key type K.

        Args:
            entity_type: The domain entity type (e.g., User)
            key_type: The primary key type (e.g., int, str, UUID)

        Returns:
            Repository instance for the specified entity type
        """
        pass

    @abstractmethod
    async def commit(self) -> None:
        """Commit the transaction."""
        pass

    @abstractmethod
    async def rollback(self) -> None:
        """Rollback the transaction."""
        pass

    @abstractmethod
    async def __aenter__(self) -> "IUnitOfWork":
        """Enter async context manager."""
        pass

    @abstractmethod
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context manager with auto-commit/rollback."""
        pass
