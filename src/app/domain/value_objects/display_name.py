"""DisplayName value object with validation."""

from dataclasses import dataclass
from typing import ClassVar

from flow_res import Err, Ok, Result


@dataclass(frozen=True)
class DisplayName:
    """DisplayName value object with validation.

    This is an immutable value object that wraps a display name string.
    Display names are validated to ensure they meet minimum requirements.

    Implements IValueObject[str] protocol for automatic persistence layer conversion.
    """

    _value: str

    # ディスプレイネームの最小・最大文字数
    MIN_LENGTH: ClassVar[int] = 1
    MAX_LENGTH: ClassVar[int] = 100

    def __post_init__(self) -> None:
        """Validate the display name when the value object is constructed."""
        if not isinstance(  # type: ignore[reportUnnecessaryIsInstance]
            self._value, str
        ):
            raise TypeError("Display name must be a string.")
        if not self._value:
            raise ValueError("Display name cannot be empty.")
        if len(self._value) < self.MIN_LENGTH:
            raise ValueError(
                f"Display name must be at least {self.MIN_LENGTH} characters long."
            )
        if len(self._value) > self.MAX_LENGTH:
            raise ValueError(
                f"Display name must not exceed {self.MAX_LENGTH} characters."
            )
        if self._value != self._value.strip():
            raise ValueError("Display name cannot have leading or trailing whitespace.")

    def to_primitive(self) -> str:
        """Convert to primitive string type for persistence.

        Returns:
            String representation suitable for database storage
        """
        return self._value

    @classmethod
    def from_primitive(cls, value: str) -> Result["DisplayName", Exception]:
        """Create DisplayName from primitive string.

        Args:
            value: String representation of display name from database

        Returns:
            Result containing DisplayName or a validation error.
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
        return f"DisplayName({self.to_primitive()})"
