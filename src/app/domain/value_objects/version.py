"""Version value object for optimistic locking."""

from __future__ import annotations

from dataclasses import dataclass

from flow_res import Err, Ok, Result


@dataclass(frozen=True)
class Version:
    """Version value object for optimistic locking.

    Wraps an integer version number used to detect concurrent modifications.
    Implements IValueObject[int] protocol for automatic persistence conversion.
    """

    _value: int

    def __post_init__(self) -> None:
        """Validate the version number, rejecting bool despite its int subclassing."""
        if isinstance(self._value, bool) or not isinstance(  # type: ignore[reportUnnecessaryIsInstance]
            self._value, int
        ):
            raise TypeError(f"Version must be int, got {type(self._value).__name__}")
        if self._value < 0:
            raise ValueError("Version must be non-negative")

    def to_primitive(self) -> int:
        """Convert to primitive int for persistence."""
        return self._value

    @classmethod
    def from_primitive(cls, value: int) -> Result[Version, Exception]:
        """Create Version from primitive int with validation.

        Args:
            value: The version number (must be non-negative integer)

        Returns:
            Result containing Version or a validation error.
        """
        try:
            return Ok(cls(_value=value))
        except (TypeError, ValueError) as error:
            return Err(error)

    def increment(self) -> Version:
        """Return new Version instance with incremented value.

        Returns:
            New Version with value incremented by 1
        """
        return Version(_value=self._value + 1)

    def __str__(self) -> str:
        return str(self._value)

    def __repr__(self) -> str:
        return f"Version({self._value})"
