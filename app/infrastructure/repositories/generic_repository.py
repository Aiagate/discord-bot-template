"""Generic repository implementation for SQLModel."""

import logging
from datetime import UTC, datetime
from typing import Any, TypeVar

from sqlalchemy import delete as sql_delete
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

from app.core.result import Err, Ok, Result
from app.domain.aggregates.team import Team
from app.domain.aggregates.user import User
from app.domain.interfaces import IAuditable, IValueObject
from app.domain.value_objects import Email, TeamId, TeamName, UserId
from app.infrastructure.orm_models.team_orm import TeamORM
from app.infrastructure.orm_models.user_orm import UserORM
from app.repository import RepositoryError, RepositoryErrorType

T = TypeVar("T")
logger = logging.getLogger(__name__)

# Domain型 → ORM型のマッピング
DOMAIN_TO_ORM_MAP: dict[type, type[SQLModel]] = {
    Team: TeamORM,
    User: UserORM,
}


def orm_to_domain(orm_instance: SQLModel) -> Any:
    """Convert ORM model to domain aggregate.

    For IAuditable entities, timestamps are automatically mapped.
    """
    if isinstance(orm_instance, TeamORM):
        # Parse ULID string from database to TeamId using IValueObject protocol
        team_id = (
            TeamId.from_primitive(orm_instance.id)
            if orm_instance.id
            else TeamId.generate()
        )
        # Parse team name string from database to TeamName using IValueObject protocol
        team_name = TeamName.from_primitive(orm_instance.name)
        return Team(
            id=team_id,
            name=team_name,
            created_at=orm_instance.created_at,
            updated_at=orm_instance.updated_at,
        )
    if isinstance(orm_instance, UserORM):
        # Parse ULID string from database to UserId using IValueObject protocol
        user_id = (
            UserId.from_primitive(orm_instance.id)
            if orm_instance.id
            else UserId.generate()
        )
        # Parse email string from database to Email using IValueObject protocol
        email = Email.from_primitive(orm_instance.email)
        return User(
            id=user_id,
            name=orm_instance.name,
            email=email,
            created_at=orm_instance.created_at,
            updated_at=orm_instance.updated_at,
        )
    raise ValueError(f"Unknown ORM type: {type(orm_instance)}")


def domain_to_orm(domain_instance: Any) -> SQLModel:
    """Convert domain aggregate to ORM model.

    For IAuditable entities, timestamps are automatically mapped.
    """
    if isinstance(domain_instance, Team):
        # Convert TeamId to string for database storage using IValueObject protocol
        id_str = domain_instance.id.to_primitive()
        # Convert TeamName to string for database storage using IValueObject protocol
        name_str = domain_instance.name.to_primitive()
        return TeamORM(
            id=id_str,
            name=name_str,
            created_at=domain_instance.created_at,
            updated_at=domain_instance.updated_at,
        )
    if isinstance(domain_instance, User):
        # Convert UserId to string for database storage using IValueObject protocol
        # For new entities (insert), set id to None to let DB generate
        # For existing entities (update), use the ULID string
        id_str = domain_instance.id.to_primitive()
        # Convert Email to string for database storage using IValueObject protocol
        email_str = domain_instance.email.to_primitive()
        return UserORM(
            id=id_str,
            name=domain_instance.name,
            email=email_str,
            created_at=domain_instance.created_at,
            updated_at=domain_instance.updated_at,
        )
    raise ValueError(f"Unknown domain type: {type(domain_instance)}")


class GenericRepository[T, K]:
    """Generic repository implementation for SQLModel.

    Implements both IRepository[T] and IRepositoryWithId[T, K].

    Type Parameters:
        T: Entity type (e.g., User, Order)
        K: Primary key type (e.g., int, str, UserId) - can be None for save-only repos
    """

    def __init__(
        self, session: AsyncSession, entity_type: type[T], key_type: type[K] | None
    ) -> None:
        self._session = session
        self._entity_type = entity_type
        self._key_type = key_type  # Can be None for save-only repositories

        # Get ORM model class for this domain type
        orm_type = DOMAIN_TO_ORM_MAP.get(entity_type)
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

            return Ok(orm_to_domain(orm_instance))
        except SQLAlchemyError as e:
            logger.exception("Database error occurred in get_by_id")
            err = RepositoryError(type=RepositoryErrorType.UNEXPECTED, message=str(e))
            return Err(err)

    async def save(self, entity: T) -> Result[T, RepositoryError]:
        """Save entity.

        For IAuditable entities, automatically updates the updated_at timestamp
        when updating existing entities.
        """
        try:
            orm_instance = domain_to_orm(entity)

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

            return Ok(orm_to_domain(orm_instance))
        except SQLAlchemyError as e:
            logger.exception("Database error occurred in save")
            err = RepositoryError(type=RepositoryErrorType.UNEXPECTED, message=str(e))
            return Err(err)

    async def delete(self, id: K) -> Result[None, RepositoryError]:
        """Delete entity by ID."""
        try:
            # Convert value object to primitive type for database query
            id_value = (
                id.to_primitive()  # type: ignore[attr-defined]
                if isinstance(id, IValueObject)
                else id
            )
            statement = sql_delete(self._orm_type).where(self._orm_type.id == id_value)  # type: ignore[attr-defined]
            await self._session.execute(statement)
            return Ok(None)
        except SQLAlchemyError as e:
            logger.exception("Database error occurred in delete")
            err = RepositoryError(type=RepositoryErrorType.UNEXPECTED, message=str(e))
            return Err(err)
