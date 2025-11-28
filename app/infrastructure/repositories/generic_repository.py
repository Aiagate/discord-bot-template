"""Generic repository implementation for SQLModel."""

import logging
from datetime import UTC, datetime
from typing import TypeVar

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.result import Err, Ok, Result
from app.domain.interfaces import IAuditable, IValueObject
from app.infrastructure.orm_mapping import ORMMappingRegistry
from app.repository import IRepositoryWithId, RepositoryError, RepositoryErrorType

T = TypeVar("T")
logger = logging.getLogger(__name__)


class GenericRepository[T, K](IRepositoryWithId[T, K]):
    """Generic repository implementation for SQLModel.

    Implements IRepositoryWithId[T, K] (which extends IRepository[T]).

    Type Parameters:
        T: Entity type (e.g., User, Order)
        K: Primary key type (e.g., int, str, UserId) - can be None for repos without get_by_id
    """

    def __init__(
        self, session: AsyncSession, entity_type: type[T], key_type: type[K] | None
    ) -> None:
        self._session = session
        self._entity_type = entity_type
        self._key_type = key_type  # Can be None for repositories without get_by_id

        # Get ORM model class from registry
        orm_type = ORMMappingRegistry.get_orm_type(entity_type)
        if orm_type is None:
            raise ValueError(f"No ORM mapping found for {entity_type}")
        self._orm_type = orm_type

    async def get_by_id(self, id: K) -> Result[T, RepositoryError]:
        """Get entity by ID."""
        try:
            # Convert value object to primitive type for database query
            id_value = (
                id.to_primitive()  # type: ignore[attr-defined]
                if isinstance(id, IValueObject)
                else id
            )
            statement = select(self._orm_type).where(self._orm_type.id == id_value)  # type: ignore[attr-defined]
            result = await self._session.execute(statement)
            orm_instance = result.scalar_one_or_none()

            if orm_instance is None:
                err = RepositoryError(
                    type=RepositoryErrorType.NOT_FOUND,
                    message=f"{self._entity_type.__name__} with id {id} not found",
                )
                return Err(err)

            # Use registry for conversion
            return Ok(ORMMappingRegistry.from_orm(orm_instance))
        except SQLAlchemyError as e:
            logger.exception("Database error occurred in get_by_id")
            err = RepositoryError(type=RepositoryErrorType.UNEXPECTED, message=str(e))
            return Err(err)

    async def add(self, entity: T) -> Result[T, RepositoryError]:
        """Add entity.

        For IAuditable entities, automatically updates the updated_at timestamp
        when updating existing entities.
        """
        try:
            # Use registry for conversion
            orm_instance = ORMMappingRegistry.to_orm(entity)

            # IAuditableエンティティの場合、更新時にupdated_atを自動設定
            is_update = orm_instance.id is not None  # type: ignore[attr-defined]
            if is_update and isinstance(entity, IAuditable):
                orm_instance.updated_at = datetime.now(UTC)  # type: ignore[attr-defined]

            # Add or merge
            if orm_instance.id is None:  # type: ignore[attr-defined]
                self._session.add(orm_instance)
                await self._session.flush()
            else:
                orm_instance = await self._session.merge(orm_instance)
                await self._session.flush()

            # Use registry for conversion
            return Ok(ORMMappingRegistry.from_orm(orm_instance))
        except SQLAlchemyError as e:
            logger.exception("Database error occurred in add")
            err = RepositoryError(type=RepositoryErrorType.UNEXPECTED, message=str(e))
            return Err(err)

    async def delete(self, entity: T) -> Result[None, RepositoryError]:
        """Delete entity."""
        try:
            # Get the entity's ID (check if it has an id attribute)
            entity_id = getattr(entity, "id", None)
            if entity_id is None:
                err = RepositoryError(
                    type=RepositoryErrorType.UNEXPECTED,
                    message="Entity does not have an id attribute",
                )
                return Err(err)

            # Convert value object to primitive type for database query
            id_value = (
                entity_id.to_primitive()  # type: ignore[attr-defined]
                if isinstance(entity_id, IValueObject)
                else entity_id
            )

            # Fetch the ORM instance from the database
            statement = select(self._orm_type).where(self._orm_type.id == id_value)  # type: ignore[attr-defined]
            result = await self._session.execute(statement)
            orm_instance = result.scalar_one_or_none()

            if orm_instance is None:
                err = RepositoryError(
                    type=RepositoryErrorType.NOT_FOUND,
                    message=f"{self._entity_type.__name__} with id {entity_id} not found",
                )
                return Err(err)

            # Delete the ORM instance
            await self._session.delete(orm_instance)
            return Ok(None)
        except SQLAlchemyError as e:
            logger.exception("Database error occurred in delete")
            err = RepositoryError(type=RepositoryErrorType.UNEXPECTED, message=str(e))
            return Err(err)
