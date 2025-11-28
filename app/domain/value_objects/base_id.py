"""Base class for ULID-based ID value objects."""

from dataclasses import dataclass
from typing import TypeVar

from ulid import ULID

T = TypeVar("T", bound="BaseId")


@dataclass(frozen=True)
class BaseId:
    """Base class for ULID-based ID value objects.

    This is an immutable value object that wraps a ULID identifier.
    ULIDs are lexicographically sortable, URL-safe, and include timestamp information.

    Implements IValueObject[str] protocol for automatic persistence layer conversion.

    Subclasses automatically inherit:
    - generate() class method for creating new IDs
    - to_primitive() for database serialization
    - from_primitive() for database deserialization
    - __str__() and __repr__() for string representation
    """

    _value: ULID

    @classmethod
    def generate(cls: type[T]) -> T:
        """Generate a new ULID-based ID.

        Returns:
            A new ID instance with a generated ULID
        """
        return cls(_value=ULID())

    def to_primitive(self) -> str:
        """Convert to primitive string type for persistence.

        Returns:
            String representation of ULID suitable for database storage
        """
        return str(self._value)

    @classmethod
    def from_primitive(cls: type[T], value: str) -> T:
        """Create ID from primitive string.

        Args:
            value: String representation of ULID from database

        Returns:
            ID instance

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
        return f"{self.__class__.__name__}({self.to_primitive()})"
