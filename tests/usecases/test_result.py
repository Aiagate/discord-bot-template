"""Tests for the use-case result error contract."""

from app.usecases.result import ErrorType, UseCaseError


def test_public_message_does_not_change_legacy_error_identity() -> None:
    """Display metadata does not affect equality or the legacy repr."""
    legacy_error = UseCaseError(
        type=ErrorType.UNEXPECTED,
        message="database detail",
    )
    error_with_display_message = UseCaseError(
        type=ErrorType.UNEXPECTED,
        message="database detail",
        public_message="An unexpected error occurred.",
    )

    assert error_with_display_message == legacy_error
    assert repr(error_with_display_message) == repr(legacy_error)
    assert error_with_display_message.display_message == (
        "An unexpected error occurred."
    )
