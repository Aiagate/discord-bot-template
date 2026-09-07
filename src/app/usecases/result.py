"""Error types specific to the use case layer."""

from dataclasses import dataclass, field
from enum import Enum, auto

from app.domain.repositories import RepositoryError


class ErrorType(Enum):
    """Enum for use case error types."""

    NOT_FOUND = auto()
    VALIDATION_ERROR = auto()
    UNEXPECTED = auto()
    CONCURRENCY_CONFLICT = auto()
    CONFLICT = auto()


@dataclass(frozen=True)
class UseCaseError(Exception):
    """Represents a specific error from a use case."""

    type: ErrorType
    message: str
    public_message: str | None = field(default=None, compare=False, repr=False)

    @property
    def display_message(self) -> str:
        """Return the message safe to expose at a presentation boundary."""
        if self.public_message is not None:
            return self.public_message
        return self.message

    def __str__(self) -> str:
        """Return message for exception representation."""
        return self.message


type UseCaseResultError = RepositoryError | UseCaseError
