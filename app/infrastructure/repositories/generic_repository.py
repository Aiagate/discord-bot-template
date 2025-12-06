"""Generic repository implementation for SQLModel."""

import logging
from datetime import UTC, datetime
from typing import TypeVar

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.result import Err, Ok, Result
from app.domain.interfaces import IAuditable, IValueObject, IVersionable
from app.domain.repositories import (
    IRepositoryWithId,
    RepositoryError,
    RepositoryErrorType,
)
from app.infrastructure.orm_mapping import ORMMappingRegistry

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
        """Add or update entity with optimistic locking support.

        For entities with a 'version' attribute, implements optimistic locking:
        - On update, checks current version matches database version
        - Returns VERSION_CONFLICT if versions don't match (concurrent update)
        - Auto-increments version on successful update

        For IAuditable entities, automatically updates the updated_at timestamp.
        """
        try:
            # Use registry for conversion
            orm_instance = ORMMappingRegistry.to_orm(entity)

            # Check if this is an update (entity exists in database)
            entity_id = getattr(entity, "id", None)
            is_update = False
            if entity_id is not None and orm_instance.id is not None:  # type: ignore[attr-defined]
                # Check if entity exists in database
                check_stmt = select(self._orm_type).where(
                    self._orm_type.id == orm_instance.id  # type: ignore[attr-defined]
                )
                check_result = await self._session.execute(check_stmt)
                existing = check_result.scalar_one_or_none()
                is_update = existing is not None

            if is_update:
                # Update path with optimistic locking

                # Update timestamp for IAuditable entities
                if isinstance(entity, IAuditable):
                    orm_instance.updated_at = datetime.now(UTC)  # type: ignore[attr-defined]

                # Check if entity implements IVersionable (optimistic locking)
                if isinstance(entity, IVersionable):
                    # Optimistic locking enabled for this entity
                    current_version = entity.version.to_primitive()

                    # Build UPDATE statement with version check
                    # UPDATE table SET col1=val1, version=version+1
                    # WHERE id=? AND version=?

                    # Get all columns to update from orm_instance
                    update_values = {}
                    for column in self._orm_type.__table__.columns:  # type: ignore[attr-defined]
                        col_name = column.name
                        if col_name != "id":  # Don't update ID
                            update_values[col_name] = getattr(orm_instance, col_name)

                    # Increment version in update
                    update_values["version"] = current_version + 1

                    # Execute UPDATE with WHERE id=? AND version=?
                    stmt = (
                        update(self._orm_type)
                        .where(
                            self._orm_type.id == orm_instance.id,  # type: ignore[attr-defined]
                            self._orm_type.version == current_version,  # type: ignore[attr-defined]
                        )
                        .values(**update_values)
                    )

                    result = await self._session.execute(stmt)

                    # Check if any rows were updated
                    if result.rowcount == 0:  # type: ignore[attr-defined]
                        # No rows affected - either not found or version mismatch
                        # Check if entity exists
                        check_stmt = select(self._orm_type).where(
                            self._orm_type.id == orm_instance.id  # type: ignore[attr-defined]
                        )
                        check_result = await self._session.execute(check_stmt)
                        existing = check_result.scalar_one_or_none()

                        if existing is None:
                            # Entity doesn't exist
                            err = RepositoryError(
                                type=RepositoryErrorType.NOT_FOUND,
                                message=f"{self._entity_type.__name__} with id {entity_id} not found",
                            )
                            return Err(err)
                        else:
                            # Entity exists but version mismatch - concurrent update
                            err = RepositoryError(
                                type=RepositoryErrorType.VERSION_CONFLICT,
                                message=(
                                    f"Concurrent modification detected for "
                                    f"{self._entity_type.__name__} with id {entity_id}. "
                                    f"Expected version {current_version}, "
                                    f"but current version is {existing.version}"  # type: ignore[attr-defined]
                                ),
                            )
                            return Err(err)

                    # Fetch updated entity to return
                    fetch_stmt = select(self._orm_type).where(
                        self._orm_type.id == orm_instance.id  # type: ignore[attr-defined]
                    )
                    fetch_result = await self._session.execute(fetch_stmt)
                    updated_orm = fetch_result.scalar_one()

                    return Ok(ORMMappingRegistry.from_orm(updated_orm))
                else:
                    # No version field - fall back to merge (legacy behavior)
                    orm_instance = await self._session.merge(orm_instance)
                    await self._session.flush()
                    return Ok(ORMMappingRegistry.from_orm(orm_instance))
            else:
                # Insert path (new entity)
                self._session.add(orm_instance)
                await self._session.flush()
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
