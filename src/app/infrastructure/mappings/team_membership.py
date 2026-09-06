"""Explicit mapping for membership enrollment periods."""

from sqlmodel import SQLModel

from app.domain.aggregates.team_membership import TeamMembership
from app.domain.value_objects import (
    MembershipId,
    MembershipRole,
    MembershipStatus,
    TeamId,
    UserId,
    Version,
)
from app.infrastructure.mappings._restore_helpers import (
    required_text,
    required_timestamp,
    unwrap_value,
)
from app.infrastructure.orm_models.team_membership_orm import TeamMembershipORM


def team_membership_to_orm(membership: TeamMembership) -> TeamMembershipORM:
    """Map one enrollment period to its database row."""
    return TeamMembershipORM(
        id=membership.id.to_primitive(),
        team_id=membership.team_id.to_primitive(),
        user_id=membership.user_id.to_primitive(),
        role=membership.role.value,
        status=membership.status.value,
        version=membership.version.to_primitive(),
        created_at=membership.created_at,
        updated_at=membership.updated_at,
    )


def team_membership_from_orm(row: SQLModel) -> TeamMembership:
    """Restore one enrollment period from its database row."""
    if not isinstance(row, TeamMembershipORM):
        raise TypeError("Expected a TeamMembershipORM row.")

    return TeamMembership.restore(
        membership_id=unwrap_value(
            MembershipId.from_primitive(required_text(row.id, "id")), "id"
        ),
        team_id=unwrap_value(
            TeamId.from_primitive(required_text(row.team_id, "team_id")), "team_id"
        ),
        user_id=unwrap_value(
            UserId.from_primitive(required_text(row.user_id, "user_id")), "user_id"
        ),
        role=unwrap_value(MembershipRole.from_primitive(row.role), "role"),
        status=unwrap_value(MembershipStatus.from_primitive(row.status), "status"),
        version=unwrap_value(Version.from_primitive(row.version), "version"),
        created_at=required_timestamp(row.created_at, "created_at"),
        updated_at=required_timestamp(row.updated_at, "updated_at"),
    )
