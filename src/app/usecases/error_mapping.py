"""Classify errors at the application boundary."""

from app.domain.repositories import RepositoryErrorType
from app.usecases.result import ErrorType, UseCaseError, UseCaseResultError

_DEFAULT_PUBLIC_MESSAGES = {
    ErrorType.NOT_FOUND: "The requested resource was not found.",
    ErrorType.CONFLICT: "The request conflicts with existing data.",
    ErrorType.CONCURRENCY_CONFLICT: (
        "The resource was changed by another request. Please reload and try again."
    ),
    ErrorType.UNEXPECTED: "An unexpected error occurred. Please try again later.",
}


def classify_error(error: UseCaseResultError) -> UseCaseError:
    """Classify an internal error at the application boundary.

    Validation and domain errors are already expressed as ``UseCaseError``
    values and pass through unchanged.  Repository errors are translated
    exactly once here, when a request crosses from the mediator into a
    presentation adapter.
    """
    if isinstance(error, UseCaseError):
        return error

    error_type = {
        RepositoryErrorType.NOT_FOUND: ErrorType.NOT_FOUND,
        RepositoryErrorType.ALREADY_EXISTS: ErrorType.CONFLICT,
        RepositoryErrorType.VERSION_CONFLICT: ErrorType.CONCURRENCY_CONFLICT,
    }.get(error.type, ErrorType.UNEXPECTED)
    return UseCaseError(
        type=error_type,
        message=error.message,
        public_message=_DEFAULT_PUBLIC_MESSAGES[error_type],
    )
