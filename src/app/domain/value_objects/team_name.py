"""TeamName value object with validation."""

from dataclasses import dataclass
from typing import ClassVar

from flow_res import Err, Ok, Result


@dataclass(frozen=True)
class TeamName:
    """TeamName value object with validation.

    This is an immutable value object that wraps a team name string.
    Team names are validated to ensure they meet minimum requirements.

    Implements IValueObject[str] protocol for automatic persistence layer conversion.
    """

    _value: str

    # チーム名の最小・最大文字数
    MIN_LENGTH: ClassVar[int] = 1
    MAX_LENGTH: ClassVar[int] = 100

    def __post_init__(self) -> None:
        """Validate the team name when the value object is constructed."""
        if not isinstance(  # type: ignore[reportUnnecessaryIsInstance]
            self._value, str
        ):
            raise TypeError("Team name must be a string.")
        if not self._value:
            raise ValueError("Team name cannot be empty.")
        if len(self._value) < self.MIN_LENGTH:
            raise ValueError(
                f"Team name must be at least {self.MIN_LENGTH} characters long."
            )
        if len(self._value) > self.MAX_LENGTH:
            raise ValueError(f"Team name must not exceed {self.MAX_LENGTH} characters.")
        if self._value != self._value.strip():
            raise ValueError("Team name cannot have leading or trailing whitespace.")

    def to_primitive(self) -> str:
        """Convert to primitive string type for persistence.

        Returns:
            String representation suitable for database storage
        """
        return self._value

    @classmethod
    def from_primitive(cls, value: str) -> Result["TeamName", Exception]:
        """Create TeamName from primitive string.

        Args:
            value: String representation of team name from database

        Returns:
            Result containing TeamName or a validation error.
        """
        try:
            return Ok(cls(_value=value))
        except (TypeError, ValueError) as error:
            return Err(error)

    def __str__(self) -> str:
        """String representation."""
        return self.to_primitive()

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"TeamName({self.to_primitive()})"
