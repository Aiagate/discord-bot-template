"""Tests for mapping application errors to HTTP statuses."""

import pytest
from fastapi import status

from app.presentation.api.error_mapping import http_status_for_error
from app.usecases.result import ErrorType


@pytest.mark.parametrize(
    ("error_type", "expected_status"),
    (
        (ErrorType.NOT_FOUND, status.HTTP_404_NOT_FOUND),
        (ErrorType.CONFLICT, status.HTTP_409_CONFLICT),
        (ErrorType.CONCURRENCY_CONFLICT, status.HTTP_409_CONFLICT),
        (ErrorType.VALIDATION_ERROR, status.HTTP_400_BAD_REQUEST),
        (ErrorType.UNEXPECTED, status.HTTP_500_INTERNAL_SERVER_ERROR),
    ),
)
def test_http_status_for_error(
    error_type: ErrorType,
    expected_status: int,
) -> None:
    """Map every use case error category to its HTTP status."""
    assert http_status_for_error(error_type) == expected_status
