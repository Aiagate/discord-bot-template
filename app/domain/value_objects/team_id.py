"""TeamId value object."""

from dataclasses import dataclass

from ulid import ULID


@dataclass(frozen=True)
class TeamId:
    """TeamId value object using ULID.

    This is an immutable value object that wraps a ULID identifier.
    ULIDs are lexicographically sortable, URL-safe, and include timestamp information.

    Implements IValueObject[str] protocol for automatic persistence layer conversion.
    """

    _value: ULID

    @classmethod
    def generate(cls) -> "TeamId":
        """Generate a new ULID-based TeamId.

        Returns:
            A new TeamId instance with a generated ULID
        """
        return cls(_value=ULID())

    def to_primitive(self) -> str:
        """Convert to primitive string type for persistence.

        Returns:
            String representation of ULID suitable for database storage
        """
        return str(self._value)

    @classmethod
    def from_primitive(cls, value: str) -> "TeamId":
        """Create TeamId from primitive string.

        Args:
            value: String representation of ULID from database

        Returns:
            TeamId instance

        Raises:
            ValueError: If the string is not a valid ULID
        """
        try:
            return cls(_value=ULID.from_str(value))
        except ValueError as e:
            raise ValueError(f"Invalid ULID string: {value}") from e

    def __str__(self) -> str:
        """String representation."""
        return self.to_primitive()

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"TeamId({self.to_primitive()})"
