"""Tests for domain models."""

from datetime import UTC, datetime

import pytest

from app.core.result import is_err
from app.domain.aggregates.user import User
from app.domain.value_objects import Email, UserId


def test_create_user_with_empty_name_raises_error() -> None:
    """Test that creating a User with an empty name raises ValueError."""
    with pytest.raises(ValueError, match="User name cannot be empty."):
        User(
            id=UserId.generate().unwrap(),
            name="",
            email=Email.from_primitive("test@example.com").unwrap(),
        )


def test_user_change_email() -> None:
    """Test that the change_email method updates the user's email."""
    user = User(
        id=UserId.generate().unwrap(),
        name="Test User",
        email=Email.from_primitive("old@example.com").unwrap(),
    )
    user.change_email(Email.from_primitive("new@example.com").unwrap())
    assert user.email.to_primitive() == "new@example.com"


def test_user_creation_with_valid_data() -> None:
    """Test creating a user with valid data."""
    user_id = UserId.generate().unwrap()
    email = Email.from_primitive("alice@example.com").unwrap()
    user = User(id=user_id, name="Alice", email=email)
    assert user.id == user_id
    assert user.name == "Alice"
    assert user.email == email
    assert isinstance(user.created_at, datetime)
    assert isinstance(user.updated_at, datetime)


def test_user_timestamps_use_utc() -> None:
    """Test that user timestamps use UTC timezone."""
    before = datetime.now(UTC)
    user = User(
        id=UserId.generate().unwrap(),
        name="Test",
        email=Email.from_primitive("test@example.com").unwrap(),
    )
    after = datetime.now(UTC)

    assert before <= user.created_at <= after
    assert before <= user.updated_at <= after


def test_user_with_explicit_timestamps() -> None:
    """Test creating user with explicit timestamps."""
    specific_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    user = User(
        id=UserId.generate().unwrap(),
        name="Test",
        email=Email.from_primitive("test@example.com").unwrap(),
        created_at=specific_time,
        updated_at=specific_time,
    )

    assert user.created_at == specific_time
    assert user.updated_at == specific_time


def test_creation_with_invalid_email_returns_err() -> None:
    """Test that creating user with invalid email raises ValueError."""
    result = Email.from_primitive("invalid-email")
    assert is_err(result)
    assert "Invalid email format" in str(result.error)
