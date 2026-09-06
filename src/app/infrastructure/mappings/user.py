"""Explicit mapping between User and its persistence row."""

from sqlmodel import SQLModel

from app.domain.aggregates.user import User
from app.domain.value_objects import DisplayName, Email, UserId, Version
from app.infrastructure.mappings._restore_helpers import (
    required_text,
    required_timestamp,
    unwrap_value,
)
from app.infrastructure.orm_models.user_orm import UserORM


def user_to_orm(user: User) -> UserORM:
    """Map a User aggregate to its database row."""
    return UserORM(
        id=user.id.to_primitive(),
        display_name=user.display_name.to_primitive(),
        email=user.email.to_primitive(),
        version=user.version.to_primitive(),
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def user_from_orm(row: SQLModel) -> User:
    """Restore a User aggregate from its database row."""
    if not isinstance(row, UserORM):
        raise TypeError("Expected a UserORM row.")

    return User.restore(
        user_id=unwrap_value(UserId.from_primitive(required_text(row.id, "id")), "id"),
        display_name=unwrap_value(
            DisplayName.from_primitive(row.display_name), "display_name"
        ),
        email=unwrap_value(Email.from_primitive(row.email), "email"),
        version=unwrap_value(Version.from_primitive(row.version), "version"),
        created_at=required_timestamp(row.created_at, "created_at"),
        updated_at=required_timestamp(row.updated_at, "updated_at"),
    )
