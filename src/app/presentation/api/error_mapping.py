"""HTTP mappings for application errors returned by API handlers."""

from fastapi import status

from app.usecases.result import ErrorType


def http_status_for_error(error_type: ErrorType) -> int:
    """Return the HTTP status corresponding to a use case error type."""
    if error_type is ErrorType.NOT_FOUND:
        return status.HTTP_404_NOT_FOUND

    if error_type in (ErrorType.CONFLICT, ErrorType.CONCURRENCY_CONFLICT):
        return status.HTTP_409_CONFLICT

    if error_type is ErrorType.VALIDATION_ERROR:
        return status.HTTP_400_BAD_REQUEST

    return status.HTTP_500_INTERNAL_SERVER_ERROR
