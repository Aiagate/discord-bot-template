"""Automatic ORM mapping registry with decorator-based registration."""

import logging
from dataclasses import fields, is_dataclass
from typing import Any, ClassVar, TypeVar, cast, get_args, get_origin, get_type_hints

from sqlmodel import SQLModel

from app.core.result import Result, is_err, is_ok
from app.domain.interfaces import IValueObject

logger = logging.getLogger(__name__)

T = TypeVar("T")


def entity_to_orm_dict(entity: Any) -> dict[str, Any]:
    """Convert domain entity to dictionary for ORM model creation.

    Automatically converts IValueObject fields to primitive types.

    Args:
        entity: Domain entity instance (must be a dataclass)

    Returns:
        Dictionary with primitive values suitable for ORM model

    Raises:
        TypeError: If entity is not a dataclass

    Example:
        >>> user = User(id=UserId(...), email=Email("test@example.com"), ...)
        >>> entity_to_orm_dict(user)
        {'id': '01ARZ3NDEK...', 'email': 'test@example.com', ...}
    """
    if not is_dataclass(entity):
        raise TypeError(f"Expected dataclass, got {type(entity).__name__}")

    result: dict[str, Any] = {}

    for field in fields(entity):
        field_value = getattr(entity, field.name)

        # Check if field value implements IValueObject
        if isinstance(field_value, IValueObject):
            # Convert to primitive
            result[field.name] = field_value.to_primitive()
        else:
            # Use as-is for primitive types
            result[field.name] = field_value

    logger.debug(
        f"Converted {type(entity).__name__} to ORM dict: {list(result.keys())}"
    )

    return result


def orm_to_entity[T](orm_instance: SQLModel, entity_type: type[T]) -> T:
    """Convert ORM model to domain entity.

    Automatically converts primitive fields to IValueObject instances
    based on type annotations.

    Args:
        orm_instance: ORM model instance
        entity_type: Target domain entity class (must be a dataclass)

    Returns:
        Domain entity instance

    Raises:
        TypeError: If entity_type is not a dataclass
        ValueError: If conversion fails

    Example:
        >>> user_orm = UserORM(id='01ARZ3NDEK...', email='test@example.com')
        >>> user = orm_to_entity(user_orm, User)
        >>> assert isinstance(user.id, UserId)
        >>> assert isinstance(user.email, Email)
    """
    if not is_dataclass(entity_type):
        raise TypeError(f"Expected dataclass, got {entity_type.__name__}")

    # Get type hints from the entity class
    type_hints = get_type_hints(entity_type)

    kwargs: dict[str, Any] = {}

    for field in fields(entity_type):
        field_name = field.name
        field_type = type_hints.get(field_name)

        if field_type is None:
            raise ValueError(
                f"No type annotation found for field '{field_name}' "
                f"in {entity_type.__name__}"
            )

        # Get the value from ORM instance
        orm_value = getattr(orm_instance, field_name, None)

        # Check if the field type is Optional (Union with None)
        origin = get_origin(field_type)
        args = get_args(field_type)

        # Check if it's a Union type and contains NoneType
        is_optional = origin is not None and type(None) in args
        actual_type = field_type

        if is_optional:
            # Extract the non-None type from Optional[T]
            non_none_types = [arg for arg in args if arg is not type(None)]
            if non_none_types:
                actual_type = non_none_types[0]

        # Check if the actual type implements IValueObject
        if hasattr(actual_type, "from_primitive") and callable(
            actual_type.from_primitive
        ):
            # Special handling for None values
            if orm_value is None:
                if is_optional:
                    # For Optional fields, return None as-is
                    kwargs[field_name] = None
                elif field_name == "id" and hasattr(actual_type, "generate"):
                    # For non-Optional ID fields, generate a new ID
                    id_result = actual_type.generate()
                    if is_err(id_result):
                        raise ValueError(f"Failed to generate ID: {id_result.error}")
                    assert is_ok(id_result)  # type: ignore[reportAssertType]
                    kwargs[field_name] = id_result.unwrap()
                else:
                    raise ValueError(
                        f"Field '{field_name}' is None but "
                        f"{actual_type.__name__} is not Optional and has no "
                        f"generate() method"
                    )
            else:
                # Convert from primitive using from_primitive()
                result = cast(Result[Any, Any], actual_type.from_primitive(orm_value))
                if is_err(result):
                    # This should ideally not happen if data in DB is valid
                    raise ValueError(
                        f"Failed to convert field '{field_name}' "
                        f"from primitive: {result.error}"
                    )
                assert is_ok(result)  # type: ignore[reportAssertType]
                kwargs[field_name] = result.unwrap()
        else:
            # Use primitive value as-is
            kwargs[field_name] = orm_value

    logger.debug(f"Converted {type(orm_instance).__name__} to {entity_type.__name__}")

    return entity_type(**kwargs)


class ORMMappingRegistry:
    """Registry for domain-to-ORM mapping with automatic conversion.

    This class maintains bidirectional mappings between domain aggregates
    and their corresponding ORM models, using automatic conversion based
    on IValueObject protocol.
    """

    _domain_to_orm: ClassVar[dict[type, type[SQLModel]]] = {}

    @classmethod
    def register(
        cls,
        domain_type: type,
        orm_type: type[SQLModel],
    ) -> None:
        """Register a domain-ORM mapping pair.

        Args:
            domain_type: Domain aggregate class (e.g., User, Team)
            orm_type: ORM model class (e.g., UserORM, TeamORM)
        """
        cls._domain_to_orm[domain_type] = orm_type
        logger.debug(
            f"Registered ORM mapping: {domain_type.__name__} <-> {orm_type.__name__}"
        )

    @classmethod
    def get_orm_type(cls, domain_type: type) -> type[SQLModel] | None:
        """Get ORM type for a domain type.

        Args:
            domain_type: Domain aggregate class

        Returns:
            ORM model class or None if not registered
        """
        return cls._domain_to_orm.get(domain_type)

    @classmethod
    def to_orm(cls, domain_instance: Any) -> SQLModel:
        """Convert domain instance to ORM model using automatic conversion.

        Args:
            domain_instance: Domain aggregate instance

        Returns:
            ORM model instance

        Raises:
            ValueError: If domain type is not registered
        """
        domain_type = type(domain_instance)
        orm_type = cls._domain_to_orm.get(domain_type)

        if orm_type is None:
            raise ValueError(
                f"No ORM mapping registered for domain type: {domain_type.__name__}"
            )

        # Use automatic conversion
        orm_dict = entity_to_orm_dict(domain_instance)
        return orm_type(**orm_dict)

    @classmethod
    def from_orm(cls, orm_instance: SQLModel) -> Any:
        """Convert ORM model to domain instance using automatic conversion.

        Args:
            orm_instance: ORM model instance

        Returns:
            Domain aggregate instance

        Raises:
            ValueError: If ORM type is not registered
        """
        # Find domain type by ORM type
        orm_type = type(orm_instance)
        for domain_type, registered_orm_type in cls._domain_to_orm.items():
            if registered_orm_type == orm_type:
                # Use automatic conversion
                return orm_to_entity(orm_instance, domain_type)

        raise ValueError(
            f"No domain mapping registered for ORM type: {orm_type.__name__}"
        )

    @classmethod
    def get_mapping_dict(cls) -> dict[type, type[SQLModel]]:
        """Get the domain-to-ORM mapping dictionary.

        Returns:
            Dictionary mapping domain types to ORM types
        """
        return cls._domain_to_orm.copy()


def register_orm_mapping(
    domain_type: type,
    orm_type: type[SQLModel],
) -> None:
    """Register ORM mapping for a domain type.

    This is a convenience function for registering mappings without
    needing to provide conversion functions (automatic conversion is used).

    Args:
        domain_type: Domain aggregate class
        orm_type: ORM model class

    Example:
        >>> from app.domain.aggregates.user import User
        >>> from app.infrastructure.orm_models.user_orm import UserORM
        >>> register_orm_mapping(User, UserORM)
    """
    ORMMappingRegistry.register(domain_type, orm_type)
