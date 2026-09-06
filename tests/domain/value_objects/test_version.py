"""Tests for Version value object."""

import dataclasses

import pytest
from flow_res import is_err, is_ok

from app.domain.value_objects.version import Version


def test_version_from_primitive_valid() -> None:
    """Test creating Version from valid primitive."""
    result = Version.from_primitive(0)
    assert is_ok(result)
    version = result.value
    assert version.to_primitive() == 0


def test_version_from_primitive_positive() -> None:
    """Test creating Version from positive integer."""
    result = Version.from_primitive(42)
    assert is_ok(result)
    version = result.value
    assert version.to_primitive() == 42


def test_version_from_primitive_negative_fails() -> None:
    """Test that negative version fails validation."""
    result = Version.from_primitive(-1)
    assert is_err(result)
    error = result.error
    assert isinstance(error, ValueError)
    assert "non-negative" in str(error).lower()


def test_version_from_primitive_non_int_fails() -> None:
    """Test that non-int type fails validation."""
    result = Version.from_primitive("5")  # type: ignore[arg-type]
    assert is_err(result)
    error = result.error
    assert isinstance(error, TypeError)


@pytest.mark.parametrize("value", [-1, -100])
def test_version_constructor_rejects_negative_values(value: int) -> None:
    """Test direct construction enforces the non-negative invariant."""
    with pytest.raises(ValueError, match="non-negative"):
        Version(_value=value)


@pytest.mark.parametrize("value", [True, False])
def test_version_constructor_rejects_bool(value: bool) -> None:
    """Test bool is not accepted as an integer version number."""
    with pytest.raises(TypeError, match="Version must be int"):
        Version(_value=value)


@pytest.mark.parametrize("value", [True, False])
def test_version_from_primitive_rejects_bool(value: bool) -> None:
    """Test from_primitive applies the same strict integer policy."""
    result = Version.from_primitive(value)

    assert is_err(result)
    assert isinstance(result.error, TypeError)


def test_version_dataclass_replace_revalidates_value() -> None:
    """Test dataclasses.replace cannot create an invalid version."""
    version = Version(_value=1)

    with pytest.raises(ValueError, match="non-negative"):
        dataclasses.replace(version, _value=-1)


def test_version_increment() -> None:
    """Test version increment returns new instance."""
    version = Version.from_primitive(5).expect("Should succeed")
    incremented = version.increment()

    assert version.to_primitive() == 5  # Original unchanged
    assert incremented.to_primitive() == 6  # New instance incremented


def test_version_immutable() -> None:
    """Test that Version is immutable."""
    version = Version.from_primitive(10).expect("Should succeed")

    with pytest.raises(AttributeError):
        version._value = 20  # type: ignore[misc]


def test_version_str() -> None:
    """Test string representation."""
    version = Version.from_primitive(7).expect("Should succeed")
    assert str(version) == "7"


def test_version_repr() -> None:
    """Test repr representation."""
    version = Version.from_primitive(7).expect("Should succeed")
    assert repr(version) == "Version(7)"
