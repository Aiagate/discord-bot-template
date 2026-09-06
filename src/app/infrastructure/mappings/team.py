"""Explicit mapping between Team and its persistence row."""

from sqlmodel import SQLModel

from app.domain.aggregates.team import Team
from app.domain.value_objects import TeamId, TeamName, Version
from app.infrastructure.mappings._restore_helpers import (
    required_text,
    required_timestamp,
    unwrap_value,
)
from app.infrastructure.orm_models.team_orm import TeamORM


def team_to_orm(team: Team) -> TeamORM:
    """Map a Team aggregate to its database row."""
    return TeamORM(
        id=team.id.to_primitive(),
        name=team.name.to_primitive(),
        version=team.version.to_primitive(),
        created_at=team.created_at,
        updated_at=team.updated_at,
    )


def team_from_orm(row: SQLModel) -> Team:
    """Restore a Team aggregate from its database row."""
    if not isinstance(row, TeamORM):
        raise TypeError("Expected a TeamORM row.")

    return Team.restore(
        team_id=unwrap_value(TeamId.from_primitive(required_text(row.id, "id")), "id"),
        name=unwrap_value(TeamName.from_primitive(row.name), "name"),
        version=unwrap_value(Version.from_primitive(row.version), "version"),
        created_at=required_timestamp(row.created_at, "created_at"),
        updated_at=required_timestamp(row.updated_at, "updated_at"),
    )
