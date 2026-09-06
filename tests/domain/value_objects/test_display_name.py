"""Tests for DisplayName value object."""

import dataclasses

import pytest
from flow_res import is_err, is_ok

from app.domain.value_objects.display_name import DisplayName


def test_display_name_from_primitive_with_valid_name() -> None:
    """Test creating DisplayName from valid string."""
    result = DisplayName.from_primitive("John Doe")
    assert is_ok(result)
    display_name = result.expect(
        "DisplayName.from_primitive should succeed for valid name"
    )
    assert display_name.to_primitive() == "John Doe"


def test_display_name_from_primitive_with_empty_string() -> None:
    """Test that empty string returns Err."""
    result = DisplayName.from_primitive("")
    assert is_err(result)
    assert "Display name cannot be empty" in str(result.error)


def test_display_name_from_primitive_with_whitespace() -> None:
    """Test that whitespace-only string returns Err."""
    result = DisplayName.from_primitive("   ")
    assert is_err(result)
    # Detected as having leading/trailing whitespace before empty check
    assert "leading or trailing whitespace" in str(result.error)


def test_display_name_from_primitive_with_leading_whitespace() -> None:
    """Test that string with leading whitespace returns Err."""
    result = DisplayName.from_primitive("  John")
    assert is_err(result)
    assert "leading or trailing whitespace" in str(result.error)


def test_display_name_from_primitive_with_trailing_whitespace() -> None:
    """Test that string with trailing whitespace returns Err."""
    result = DisplayName.from_primitive("John  ")
    assert is_err(result)
    assert "leading or trailing whitespace" in str(result.error)


def test_display_name_from_primitive_exceeds_max_length() -> None:
    """Test that string exceeding max length returns Err."""
    long_name = "a" * (DisplayName.MAX_LENGTH + 1)
    result = DisplayName.from_primitive(long_name)
    assert is_err(result)
    assert "must not exceed" in str(result.error)


@pytest.mark.parametrize(
    "value, message",
    [
        ("", "cannot be empty"),
        ("  Alice", "leading or trailing whitespace"),
        ("Alice  ", "leading or trailing whitespace"),
        ("a" * (DisplayName.MAX_LENGTH + 1), "must not exceed"),
    ],
)
def test_display_name_constructor_rejects_invalid_values(
    value: str,
    message: str,
) -> None:
    """Test direct construction enforces display name invariants."""
    with pytest.raises(ValueError, match=message):
        DisplayName(_value=value)


@pytest.mark.parametrize("value", ["A", "x" * DisplayName.MAX_LENGTH])
def test_display_name_constructor_accepts_boundary_values(value: str) -> None:
    """Test both construction paths accept the length boundaries."""
    display_name = DisplayName(_value=value)
    result = DisplayName.from_primitive(value)

    assert display_name.to_primitive() == value
    assert (
        result.expect("DisplayName.from_primitive should accept boundary")
        == display_name
    )


@pytest.mark.parametrize("value", [None, 123])
def test_display_name_rejects_non_string_values(value: object) -> None:
    """Test both construction paths reject non-string values."""
    with pytest.raises(TypeError, match="must be a string"):
        DisplayName(_value=value)  # type: ignore[arg-type]

    result = DisplayName.from_primitive(value)  # type: ignore[arg-type]
    assert is_err(result)
    assert isinstance(result.error, TypeError)


def test_display_name_dataclass_replace_revalidates_value() -> None:
    """Test dataclasses.replace cannot create an invalid display name."""
    display_name = DisplayName(_value="Alice")

    with pytest.raises(ValueError, match="cannot be empty"):
        dataclasses.replace(display_name, _value="")


def test_display_name_length_limits_are_class_constants() -> None:
    """Test validation limits cannot be overridden per instance."""
    with pytest.raises(TypeError):
        DisplayName(_value="Alice", MIN_LENGTH=0)  # type: ignore[call-arg]


def test_display_name_str_representation() -> None:
    """Test __str__ returns the primitive value."""
    display_name = DisplayName.from_primitive("Alice").expect(
        "DisplayName.from_primitive should succeed for valid name"
    )
    assert str(display_name) == "Alice"


def test_display_name_repr() -> None:
    """Test __repr__ returns developer-friendly representation."""
    display_name = DisplayName.from_primitive("Alice").expect(
        "DisplayName.from_primitive should succeed for valid name"
    )
    assert repr(display_name) == "DisplayName(Alice)"


def test_display_name_equality() -> None:
    """Test that two DisplayName instances with same value are equal."""
    name1 = DisplayName.from_primitive("Bob").expect(
        "DisplayName.from_primitive should succeed for valid name"
    )
    name2 = DisplayName.from_primitive("Bob").expect(
        "DisplayName.from_primitive should succeed for valid name"
    )
    assert name1 == name2


def test_display_name_immutability() -> None:
    """Test that DisplayName is immutable (frozen dataclass)."""
    display_name = DisplayName.from_primitive("Charlie").expect(
        "DisplayName.from_primitive should succeed for valid name"
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        display_name._value = "NewName"  # type: ignore[misc]
