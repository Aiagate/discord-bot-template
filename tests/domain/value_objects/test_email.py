"""Tests for Email value object."""

import dataclasses

import pytest

from app.domain.value_objects.email import Email


def test_create_valid_email() -> None:
    """Test creating a valid email."""
    email = Email.from_primitive("test@example.com")
    assert email.to_primitive() == "test@example.com"
    assert str(email) == "test@example.com"


def test_create_email_with_plus_sign() -> None:
    """Test creating email with plus sign (subaddressing)."""
    email = Email.from_primitive("user+tag@example.com")
    assert email.to_primitive() == "user+tag@example.com"


def test_create_email_with_subdomain() -> None:
    """Test creating email with subdomain."""
    email = Email.from_primitive("user@mail.example.com")
    assert email.to_primitive() == "user@mail.example.com"


def test_create_email_with_hyphen() -> None:
    """Test creating email with hyphen in domain."""
    email = Email.from_primitive("user@my-domain.com")
    assert email.to_primitive() == "user@my-domain.com"


def test_empty_email_raises_error() -> None:
    """Test that empty email raises ValueError."""
    with pytest.raises(ValueError, match="Email cannot be empty"):
        Email.from_primitive("")


def test_invalid_email_format_raises_error() -> None:
    """Test that invalid email format raises ValueError."""
    invalid_emails = [
        "notanemail",
        "@example.com",
        "user@",
        "user @example.com",
        "user@example",
        "user..name@example.com",
        "user@.com",
        "user@domain.",
    ]
    for invalid_email in invalid_emails:
        with pytest.raises(ValueError, match="Invalid email format"):
            Email.from_primitive(invalid_email)


def test_email_repr() -> None:
    """Test email representation."""
    email = Email.from_primitive("test@example.com")
    assert repr(email) == "Email(test@example.com)"


def test_email_is_immutable() -> None:
    """Test that email is immutable."""
    email = Email.from_primitive("test@example.com")
    with pytest.raises(dataclasses.FrozenInstanceError):
        email._value = "changed@example.com"  # type: ignore[misc]


def test_email_equality() -> None:
    """Test that emails with same value are equal."""
    email1 = Email.from_primitive("test@example.com")
    email2 = Email.from_primitive("test@example.com")
    assert email1 == email2


def test_email_inequality() -> None:
    """Test that emails with different values are not equal."""
    email1 = Email.from_primitive("test1@example.com")
    email2 = Email.from_primitive("test2@example.com")
    assert email1 != email2
