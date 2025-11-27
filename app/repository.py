"""Repository interfaces for domain layer."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Protocol, overload

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


class IRepository[T](Protocol):
    """Repository interface for save operations only.

    Use this when you only need to save entities (e.g., Create operations).
    Does not require knowledge of ID type.

    Type Parameters:
        T: Entity type (e.g., User, Order)
    """

    async def save(self, entity: T) -> Result[T, RepositoryError]:
        """Save or update entity."""
        ...


class IRepositoryWithId[T, K](IRepository[T], Protocol):
    """Repository interface with ID-based operations.

    Extends IRepository[T] with get_by_id and delete operations.
    Use this when you need to retrieve or delete entities by ID.

    Type Parameters:
        T: Entity type (e.g., User, Order)
        K: Primary key type (e.g., int, str, UserId)
    """

    async def get_by_id(self, id: K) -> Result[T, RepositoryError]:
        """Get entity by ID."""
        ...

    async def delete(self, id: K) -> Result[None, RepositoryError]:
        """Delete entity by ID."""
        ...


class IUnitOfWork(ABC):
    """Unit of Work interface for transaction management."""

    @overload
    def GetRepository[T](self, entity_type: type[T]) -> IRepository[T]:
        """Get repository for save-only operations.

        Args:
            entity_type: The domain entity type (e.g., User)

        Returns:
            Repository instance with save-only operations
        """
        ...

    @overload
    def GetRepository[T, K](
        self, entity_type: type[T], key_type: type[K]
    ) -> IRepositoryWithId[T, K]:
        """Get repository with ID-based operations.

        Args:
            entity_type: The domain entity type (e.g., User)
            key_type: The primary key type (e.g., int, str, UserId)

        Returns:
            Repository instance with all operations (save, get_by_id, delete)
        """
        ...

    @abstractmethod
    def GetRepository[T, K](
        self, entity_type: type[T], key_type: type[K] | None = None
    ) -> IRepository[T] | IRepositoryWithId[T, K]:
        """Get repository for entity type.

        This method is overloaded:
        - GetRepository(User) -> IRepository[User] (save only)
        - GetRepository(User, UserId) -> IRepositoryWithId[User, UserId] (all ops)

        Args:
            entity_type: The domain entity type
            key_type: Optional primary key type

        Returns:
            Repository instance
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
