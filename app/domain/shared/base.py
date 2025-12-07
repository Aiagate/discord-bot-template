"""Base class for domain entities with protected mutability."""

from __future__ import annotations

from typing import Any


class DomainEntityBase:
    """Base class for domain entities with protected internal mutability.

    This class provides a mechanism for frozen dataclasses to update their
    internal state through domain methods while preventing external mutation.

    Usage:
        @dataclass(frozen=True)
        class User(DomainEntityBase):
            email: Email

            def change_email(self, new_email: Email) -> User:
                self._update_state("email", new_email)
                return self

    The _update_state method uses object.__setattr__ to bypass the frozen
    constraint. External access to this method is blocked by Pyright's
    reportPrivateUsage rule.
    """

    def _update_state(self, field_name: str, value: Any) -> None:
        """Update internal state of a frozen dataclass field.

        This method should only be called from domain methods within the
        entity itself. External usage will be flagged by Pyright when
        reportPrivateUsage is set to "error".

        Args:
            field_name: The name of the field to update
            value: The new value for the field
        """
        object.__setattr__(self, field_name, value)
