"""Tests for BaseId base class."""

import dataclasses

import pytest
from ulid import ULID

from app.core.result import is_err, is_ok
from app.domain.value_objects.base_id import BaseId


# テスト用のサブクラス定義
class TestId(BaseId):
    """Test ID for testing BaseId functionality."""


def test_generate_creates_new_id() -> None:
    """Test that generate creates a new ID with valid ULID."""
    result = TestId.generate()
    assert is_ok(result)
    test_id = result.unwrap()
    assert test_id is not None
    assert isinstance(test_id._value, ULID)


def test_to_primitive_returns_string() -> None:
    """Test that to_primitive returns string representation."""
    test_id = TestId.generate().unwrap()
    primitive = test_id.to_primitive()
    assert isinstance(primitive, str)
    assert len(primitive) == 26  # ULID length


def test_from_primitive_reconstructs_id() -> None:
    """Test that from_primitive reconstructs ID from string."""
    original = TestId.generate().unwrap()
    primitive = original.to_primitive()
    reconstructed = TestId.from_primitive(primitive).unwrap()
    assert reconstructed == original


def test_from_primitive_with_invalid_string_returns_err() -> None:
    """Test that from_primitive returns Err for invalid string."""
    result = TestId.from_primitive("invalid-ulid")
    assert is_err(result)
    assert "Invalid ULID string" in str(result.error)


def test_base_id_is_immutable() -> None:
    """Test that BaseId is immutable (frozen dataclass)."""
    test_id = TestId.generate().unwrap()
    with pytest.raises(dataclasses.FrozenInstanceError):
        test_id._value = ULID()  # type: ignore[misc]


def test_base_id_equality() -> None:
    """Test that BaseId instances with same ULID are equal."""
    ulid_value = ULID()
    id1 = TestId(_value=ulid_value)
    id2 = TestId(_value=ulid_value)
    assert id1 == id2


def test_base_id_inequality() -> None:
    """Test that BaseId instances with different ULIDs are not equal."""
    id1 = TestId.generate().unwrap()
    id2 = TestId.generate().unwrap()
    assert id1 != id2


def test_str_representation() -> None:
    """Test __str__ returns primitive string."""
    test_id = TestId.generate().unwrap()
    assert str(test_id) == test_id.to_primitive()


def test_repr_includes_class_name() -> None:
    """Test __repr__ includes class name and value."""
    test_id = TestId.generate().unwrap()
    repr_str = repr(test_id)
    assert "TestId" in repr_str
    assert test_id.to_primitive() in repr_str
