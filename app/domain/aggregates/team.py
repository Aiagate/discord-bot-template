"""Team aggregate root."""

from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.domain.value_objects import TeamId, TeamName


@dataclass
class Team:
    """Team aggregate root.

    Implements IAuditable: timestamps are infrastructure concerns but exposed
    as read-only fields for auditing and display purposes. The repository layer
    automatically manages created_at and updated_at.
    """

    id: TeamId
    name: TeamName
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        """Validate team data."""
        if not self.name:
            raise ValueError("Team name cannot be empty.")

    def change_name(self, new_name: TeamName) -> "Team":
        """チーム名を変更するドメインロジック

        Note: updated_at is automatically managed by the repository layer.
        """
        self.name = new_name

        return self
