"""Error types specific to the use case layer."""

from dataclasses import dataclass
from enum import Enum, auto


class ErrorType(Enum):
    """Enum for use case error types."""

    NOT_FOUND = auto()
    VALIDATION_ERROR = auto()
    UNEXPECTED = auto()


@dataclass(frozen=True)
class UseCaseError:
    """Represents a specific error from a use case."""

    type: ErrorType
    message: str
