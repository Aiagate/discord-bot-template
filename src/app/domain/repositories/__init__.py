"""Repository interfaces for domain layer."""

from app.domain.repositories.interfaces import (
    IRepository,
    IRepositoryWithId,
    RepositoryError,
    RepositoryErrorType,
)

__all__ = [
    "IRepository",
    "IRepositoryWithId",
    "RepositoryError",
    "RepositoryErrorType",
]
