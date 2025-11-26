"""Tests for domain models."""

from datetime import UTC, datetime

import pytest

from app.domain.aggregates.user import User


def test_create_user_with_empty_name_raises_error() -> None:
    """Test that creating a User with an empty name raises ValueError."""
    with pytest.raises(ValueError, match="User name cannot be empty."):
        User(id=0, name="", email="test@example.com")


def test_user_change_email() -> None:
    """Test that the change_email method updates the user's email."""
    user = User(id=1, name="Test User", email="old@example.com")
    user.change_email("new@example.com")
    assert user.email == "new@example.com"


def test_user_creation_with_valid_data() -> None:
    """Test creating a user with valid data."""
    user = User(id=1, name="Alice", email="alice@example.com")
    assert user.id == 1
    assert user.name == "Alice"
    assert user.email == "alice@example.com"
    assert isinstance(user.created_at, datetime)
    assert isinstance(user.updated_at, datetime)


def test_user_timestamps_use_utc() -> None:
    """Test that user timestamps use UTC timezone."""
    before = datetime.now(UTC)
    user = User(id=1, name="Test", email="test@example.com")
    after = datetime.now(UTC)

    assert before <= user.created_at <= after
    assert before <= user.updated_at <= after


def test_user_with_explicit_timestamps() -> None:
    """Test creating user with explicit timestamps."""
    specific_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    user = User(
        id=1,
        name="Test",
        email="test@example.com",
        created_at=specific_time,
        updated_at=specific_time,
    )

    assert user.created_at == specific_time
    assert user.updated_at == specific_time
