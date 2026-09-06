"""Tests for Email value object."""

import dataclasses

import pytest
from flow_res import is_err, is_ok

from app.domain.value_objects.email import Email


def test_create_valid_email() -> None:
    """Test creating a valid email."""
    result = Email.from_primitive("test@example.com")
    assert is_ok(result)
    email = result.expect("Email.from_primitive should succeed for valid email")
    assert email.to_primitive() == "test@example.com"
    assert str(email) == "test@example.com"


def test_create_email_with_plus_sign() -> None:
    """Test creating email with plus sign (subaddressing)."""
    result = Email.from_primitive("user+tag@example.com")
    assert is_ok(result)
    email = result.expect("Email.from_primitive should succeed for valid email")
    assert email.to_primitive() == "user+tag@example.com"


def test_create_email_with_subdomain() -> None:
    """Test creating email with subdomain."""
    result = Email.from_primitive("user@mail.example.com")
    assert is_ok(result)
    email = result.expect("Email.from_primitive should succeed for valid email")
    assert email.to_primitive() == "user@mail.example.com"


def test_create_email_with_hyphen() -> None:
    """Test creating email with hyphen in domain."""
    result = Email.from_primitive("user@my-domain.com")
    assert is_ok(result)
    email = result.expect("Email.from_primitive should succeed for valid email")
    assert email.to_primitive() == "user@my-domain.com"


def test_empty_email_returns_err() -> None:
    """Test that empty email returns an Err."""
    result = Email.from_primitive("")
    assert is_err(result)
    assert "Email cannot be empty" in str(result.error)


def test_invalid_email_format_returns_err() -> None:
    """Test that invalid email format returns an Err."""
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
        result = Email.from_primitive(invalid_email)
        assert is_err(result)
        assert "Invalid email format" in str(result.error)


def test_email_constructor_normalizes_surrounding_whitespace() -> None:
    """Test direct construction preserves the existing email normalization."""
    email = Email(_value="  test@example.com  ")

    assert email.to_primitive() == "test@example.com"


def test_email_from_primitive_normalizes_surrounding_whitespace() -> None:
    """Test the factory retains email normalization after construction."""
    result = Email.from_primitive("  test@example.com  ")

    email = result.expect("Email.from_primitive should normalize a valid email")
    assert email.to_primitive() == "test@example.com"


@pytest.mark.parametrize(
    "value, message",
    [
        ("", "Email cannot be empty"),
        ("   ", "Email cannot be empty"),
        ("not-an-email", "Invalid email format"),
    ],
)
def test_email_constructor_rejects_invalid_values(value: str, message: str) -> None:
    """Test direct construction enforces email invariants."""
    with pytest.raises(ValueError, match=message):
        Email(_value=value)


@pytest.mark.parametrize("value", [None, 123])
def test_email_rejects_non_string_values(value: object) -> None:
    """Test both construction paths reject non-string values."""
    with pytest.raises(TypeError, match="Email must be a string"):
        Email(_value=value)  # type: ignore[arg-type]

    result = Email.from_primitive(value)  # type: ignore[arg-type]
    assert is_err(result)
    assert isinstance(result.error, TypeError)


def test_email_dataclass_replace_revalidates_value() -> None:
    """Test dataclasses.replace cannot create an invalid email."""
    email = Email(_value="test@example.com")

    with pytest.raises(ValueError, match="Invalid email format"):
        dataclasses.replace(email, _value="invalid-email")


def test_email_repr() -> None:
    """Test email representation."""
    email = Email.from_primitive("test@example.com").expect(
        "Email.from_primitive should succeed for valid email"
    )
    assert repr(email) == "Email(test@example.com)"


def test_email_is_immutable() -> None:
    """Test that email is immutable."""
    email = Email.from_primitive("test@example.com").expect(
        "Email.from_primitive should succeed for valid email"
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        email._value = "changed@example.com"  # type: ignore[misc]


def test_email_equality() -> None:
    """Test that emails with same value are equal."""
    email1 = Email.from_primitive("test@example.com").expect(
        "Email.from_primitive should succeed for valid email"
    )
    email2 = Email.from_primitive("test@example.com").expect(
        "Email.from_primitive should succeed for valid email"
    )
    assert email1 == email2


def test_email_inequality() -> None:
    """Test that emails with different values are not equal."""
    email1 = Email.from_primitive("test1@example.com").expect(
        "Email.from_primitive should succeed for valid email"
    )
    email2 = Email.from_primitive("test2@example.com").expect(
        "Email.from_primitive should succeed for valid email"
    )
    assert email1 != email2
