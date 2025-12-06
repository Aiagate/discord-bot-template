"""Team aggregate root."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.domain.value_objects import TeamId, TeamName, Version


@dataclass
class Team:
    """Team aggregate root.

    Implements IAuditable: timestamps are infrastructure concerns but exposed
    as read-only fields for auditing and display purposes. The repository layer
    automatically manages created_at and updated_at.

    Implements IVersionable: optimistic locking via version field, which is
    automatically managed by the repository layer during updates.
    """

    id: TeamId
    _name: TeamName
    version: Version
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def name(self) -> TeamName:
        return self._name

    @name.setter
    def name(self, new_name: TeamName) -> None:
        raise AttributeError("Use 'change_name' to modify the team name.")

    def __post_init__(self) -> None:
        """Validate team data."""
        if not self._name:
            raise ValueError("Team name cannot be empty.")

    def change_name(self, new_name: TeamName) -> Team:
        """チーム名を変更するドメインロジック

        Note: updated_at is automatically managed by the repository layer.
        """
        self._name = new_name

        return self

        return self
