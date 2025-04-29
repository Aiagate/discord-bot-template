"""SQLAlchemy Unit of Work implementation."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.infrastructure.repositories.generic_repository import GenericRepository
from app.repository import IRepository, IUnitOfWork


class SQLAlchemyUnitOfWork(IUnitOfWork):
    """SQLAlchemy implementation of Unit of Work."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None
        self._repositories: dict[tuple[type, type], Any] = {}

    def GetRepository[T, K](
        self, entity_type: type[T], key_type: type[K]
    ) -> IRepository[T, K]:
        """Get repository for entity type with specified key type."""
        if self._session is None:
            raise RuntimeError(
                "UnitOfWork session not initialized. Use 'async with' context."
            )

        # Use tuple of (entity_type, key_type) as cache key
        cache_key = (entity_type, key_type)

        # Return cached repository if exists
        if cache_key in self._repositories:
            return self._repositories[cache_key]

        # Create new repository
        repository = GenericRepository[T, K](self._session, entity_type, key_type)
        self._repositories[cache_key] = repository
        return repository

    async def commit(self) -> None:
        """Commit the transaction."""
        if self._session is None:
            raise RuntimeError("UnitOfWork session not initialized.")
        await self._session.commit()

    async def rollback(self) -> None:
        """Rollback the transaction."""
        if self._session is None:
            raise RuntimeError("UnitOfWork session not initialized.")
        await self._session.rollback()

    async def __aenter__(self) -> "SQLAlchemyUnitOfWork":
        """Enter async context manager."""
        self._session = self._session_factory()
        await self._session.__aenter__()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context manager with auto-commit/rollback."""
        if self._session is None:
            return

        try:
            if exc_type is None:
                # No exception - commit
                await self.commit()
            else:
                # Exception occurred - rollback
                await self.rollback()
        finally:
            await self._session.__aexit__(exc_type, exc_val, exc_tb)
            self._session = None
            self._repositories.clear()
