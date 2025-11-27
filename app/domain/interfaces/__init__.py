"""Domain interfaces."""

from app.domain.interfaces.auditable import IAuditable
from app.domain.interfaces.value_object import IValueObject

__all__ = ["IAuditable", "IValueObject"]
