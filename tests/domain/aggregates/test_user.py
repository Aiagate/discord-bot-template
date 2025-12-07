"""Tests for domain models."""

from dataclasses import FrozenInstanceError, is_dataclass
from datetime import UTC, datetime

import pytest

from app.core.result import is_err
from app.domain.aggregates.user import User
from app.domain.value_objects import DisplayName, Email, UserId


def test_create_user_with_empty_name_raises_error() -> None:
    """Test that creating a User with an empty display name returns Err."""
    result = DisplayName.from_primitive("")
    assert is_err(result)
    assert "Display name cannot be empty" in str(result.error)


def test_user_change_email() -> None:
    """Test that the change_email method updates the user's email."""
    user = User(
        id=UserId.generate().expect("UserId.generate should succeed"),
        display_name=DisplayName.from_primitive("Test User").expect(
            "DisplayName.from_primitive should succeed for valid display name"
        ),
        email=Email.from_primitive("old@example.com").expect(
            "Email.from_primitive should succeed for valid email"
        ),
    )
    user.change_email(
        Email.from_primitive("new@example.com").expect(
            "Email.from_primitive should succeed for valid email"
        )
    )
    assert user.email.to_primitive() == "new@example.com"


def test_user_creation_with_valid_data() -> None:
    """Test creating a user with valid data."""
    user_id = UserId.generate().expect("UserId.generate should succeed")
    email = Email.from_primitive("alice@example.com").expect(
        "Email.from_primitive should succeed for valid email"
    )
    display_name = DisplayName.from_primitive("Alice").expect(
        "DisplayName.from_primitive should succeed for valid display name"
    )
    user = User(id=user_id, display_name=display_name, email=email)
    assert user.id == user_id
    assert user.display_name == display_name
    assert user.email == email
    assert isinstance(user.created_at, datetime)
    assert isinstance(user.updated_at, datetime)


def test_user_timestamps_use_utc() -> None:
    """Test that user timestamps use UTC timezone."""
    before = datetime.now(UTC)
    user = User(
        id=UserId.generate().expect("UserId.generate should succeed"),
        display_name=DisplayName.from_primitive("Test").expect(
            "DisplayName.from_primitive should succeed for valid display name"
        ),
        email=Email.from_primitive("test@example.com").expect(
            "Email.from_primitive should succeed for valid email"
        ),
    )
    after = datetime.now(UTC)

    assert before <= user.created_at <= after
    assert before <= user.updated_at <= after


def test_user_with_explicit_timestamps() -> None:
    """Test creating user with explicit timestamps."""
    specific_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    user = User(
        id=UserId.generate().expect("UserId.generate should succeed"),
        display_name=DisplayName.from_primitive("Test").expect(
            "DisplayName.from_primitive should succeed for valid display name"
        ),
        email=Email.from_primitive("test@example.com").expect(
            "Email.from_primitive should succeed for valid email"
        ),
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


def test_user_direct_assignment_raises_frozen_error() -> None:
    """Test that direct field assignment raises FrozenInstanceError."""
    user = User(
        id=UserId.generate().expect("UserId.generate should succeed"),
        display_name=DisplayName.from_primitive("Test User").expect(
            "DisplayName.from_primitive should succeed for valid display name"
        ),
        email=Email.from_primitive("test@example.com").expect(
            "Email.from_primitive should succeed for valid email"
        ),
    )

    with pytest.raises(FrozenInstanceError):
        user.email = Email.from_primitive("hacked@example.com").expect(  # type: ignore[misc]
            "Email.from_primitive should succeed"
        )


def test_user_is_frozen_dataclass() -> None:
    """Test that User is a frozen dataclass and hashable."""
    assert is_dataclass(User)
    user = User(
        id=UserId.generate().expect("UserId.generate should succeed"),
        display_name=DisplayName.from_primitive("Test").expect(
            "DisplayName.from_primitive should succeed"
        ),
        email=Email.from_primitive("test@example.com").expect(
            "Email.from_primitive should succeed"
        ),
    )
    # Frozen dataclasses can be used as dict keys
    user_dict = {user: "value"}
    assert user_dict[user] == "value"
