"""Interface for value objects that can be converted to/from primitive types."""

from typing import Protocol, TypeVar, runtime_checkable

T = TypeVar("T")


@runtime_checkable
class IValueObject(Protocol[T]):
    """Protocol for value objects that can be converted to/from primitive types.

    Value objects implementing this protocol can be automatically converted
    between domain and persistence layers. This enables generic repository
    implementations to handle value objects without type-specific logic.

    Type Parameters:
        T: The primitive type used for persistence (e.g., str, int, UUID)

    Example:
        >>> @dataclass(frozen=True)
        >>> class UserId:
        >>>     _value: ULID
        >>>
        >>>     def to_primitive(self) -> str:
        >>>         return str(self._value)
        >>>
        >>>     @classmethod
        >>>     def from_primitive(cls, value: str) -> "UserId":
        >>>         return cls(_value=ULID.from_str(value))
    """

    def to_primitive(self) -> T:
        """Convert value object to primitive type for persistence.

        Returns:
            The primitive representation suitable for database storage.
        """
        ...

    @classmethod
    def from_primitive(cls, value: T) -> "IValueObject[T]":
        """Create value object from primitive type.

        Args:
            value: The primitive value from the database.

        Returns:
            A new instance of the value object.

        Raises:
            ValueError: If the primitive value is invalid.
        """
        ...
