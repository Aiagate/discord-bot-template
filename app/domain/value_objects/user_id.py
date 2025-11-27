"""UserId value object."""

from dataclasses import dataclass

from ulid import ULID


@dataclass(frozen=True)
class UserId:
    """UserId value object using ULID.

    This is an immutable value object that wraps a ULID identifier.
    ULIDs are lexicographically sortable, URL-safe, and include timestamp information.

    Implements IValueObject[str] protocol for automatic persistence layer conversion.
    """

    _value: ULID

    @classmethod
    def generate(cls) -> "UserId":
        """Generate a new ULID-based UserId.

        Returns:
            A new UserId instance with a generated ULID
        """
        return cls(_value=ULID())

    def to_primitive(self) -> str:
        """Convert to primitive string type for persistence.

        Returns:
            String representation of ULID suitable for database storage
        """
        return str(self._value)

    @classmethod
    def from_primitive(cls, value: str) -> "UserId":
        """Create UserId from primitive string.

        Args:
            value: String representation of ULID from database

        Returns:
            UserId instance

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
        return f"UserId({self.to_primitive()})"
