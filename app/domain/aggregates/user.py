from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.domain.value_objects import DisplayName, Email, UserId


@dataclass
class User:
    """User aggregate root.

    Implements IAuditable: timestamps are infrastructure concerns but exposed
    as read-only fields for auditing and display purposes. The repository layer
    automatically manages created_at and updated_at.
    """

    id: UserId
    display_name: DisplayName
    email: Email
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def change_email(self, new_email: Email) -> User:
        """メールアドレスを変更するドメインロジック

        Note: updated_at is automatically managed by the repository layer.
        """
        self.email = new_email

        return self
