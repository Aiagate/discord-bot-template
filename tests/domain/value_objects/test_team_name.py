"""Tests for TeamName value object."""

import dataclasses

import pytest
from flow_res import is_err, is_ok

from app.domain.value_objects.team_name import TeamName


def test_create_valid_team_name() -> None:
    """Test creating a valid team name."""
    result = TeamName.from_primitive("Alpha Team")
    assert is_ok(result)
    team_name = result.expect("TeamName.from_primitive should succeed for valid name")
    assert team_name.to_primitive() == "Alpha Team"
    assert str(team_name) == "Alpha Team"


def test_create_team_name_with_single_character() -> None:
    """Test creating team name with minimum length (1 character)."""
    result = TeamName.from_primitive("A")
    assert is_ok(result)
    team_name = result.expect("TeamName.from_primitive should succeed for valid name")
    assert team_name.to_primitive() == "A"


def test_create_team_name_with_max_length() -> None:
    """Test creating team name with maximum length (100 characters)."""
    long_name = "x" * 100
    result = TeamName.from_primitive(long_name)
    assert is_ok(result)
    team_name = result.expect("TeamName.from_primitive should succeed for valid name")
    assert team_name.to_primitive() == long_name


def test_create_team_name_with_special_characters() -> None:
    """Test creating team name with special characters."""
    result = TeamName.from_primitive("Team-Alpha_2024")
    assert is_ok(result)
    team_name = result.expect("TeamName.from_primitive should succeed for valid name")
    assert team_name.to_primitive() == "Team-Alpha_2024"


def test_empty_team_name_returns_err() -> None:
    """Test that empty team name returns an Err."""
    result = TeamName.from_primitive("")
    assert is_err(result)
    assert "Team name cannot be empty" in str(result.error)


def test_team_name_too_long_returns_err() -> None:
    """Test that team name exceeding max length returns an Err."""
    long_name = "x" * 101
    result = TeamName.from_primitive(long_name)
    assert is_err(result)
    assert "must not exceed 100 characters" in str(result.error)


def test_team_name_with_leading_whitespace_returns_err() -> None:
    """Test that team name with leading whitespace returns an Err."""
    result = TeamName.from_primitive("  Team Name")
    assert is_err(result)
    assert "cannot have leading or trailing whitespace" in str(result.error)


def test_team_name_with_trailing_whitespace_returns_err() -> None:
    """Test that team name with trailing whitespace returns an Err."""
    result = TeamName.from_primitive("Team Name  ")
    assert is_err(result)
    assert "cannot have leading or trailing whitespace" in str(result.error)


@pytest.mark.parametrize(
    "value, message",
    [
        ("", "cannot be empty"),
        ("  Alpha Team", "leading or trailing whitespace"),
        ("Alpha Team  ", "leading or trailing whitespace"),
        ("x" * (TeamName.MAX_LENGTH + 1), "must not exceed"),
    ],
)
def test_team_name_constructor_rejects_invalid_values(
    value: str,
    message: str,
) -> None:
    """Test direct construction enforces team name invariants."""
    with pytest.raises(ValueError, match=message):
        TeamName(_value=value)


@pytest.mark.parametrize("value", ["A", "x" * TeamName.MAX_LENGTH])
def test_team_name_constructor_accepts_boundary_values(value: str) -> None:
    """Test both construction paths accept the length boundaries."""
    team_name = TeamName(_value=value)
    result = TeamName.from_primitive(value)

    assert team_name.to_primitive() == value
    assert result.expect("TeamName.from_primitive should accept boundary") == team_name


@pytest.mark.parametrize("value", [None, 123])
def test_team_name_rejects_non_string_values(value: object) -> None:
    """Test both construction paths reject non-string values."""
    with pytest.raises(TypeError, match="must be a string"):
        TeamName(_value=value)  # type: ignore[arg-type]

    result = TeamName.from_primitive(value)  # type: ignore[arg-type]
    assert is_err(result)
    assert isinstance(result.error, TypeError)


def test_team_name_dataclass_replace_revalidates_value() -> None:
    """Test dataclasses.replace cannot create an invalid team name."""
    team_name = TeamName(_value="Alpha Team")

    with pytest.raises(ValueError, match="cannot be empty"):
        dataclasses.replace(team_name, _value="")


def test_team_name_length_limits_are_class_constants() -> None:
    """Test validation limits cannot be overridden per instance."""
    with pytest.raises(TypeError):
        TeamName(_value="Alpha Team", MAX_LENGTH=1)  # type: ignore[call-arg]


def test_team_name_repr() -> None:
    """Test team name representation."""
    team_name = TeamName.from_primitive("Alpha Team").expect(
        "TeamName.from_primitive should succeed for valid name"
    )
    assert repr(team_name) == "TeamName(Alpha Team)"


def test_team_name_is_immutable() -> None:
    """Test that team name is immutable."""
    team_name = TeamName.from_primitive("Alpha Team").expect(
        "TeamName.from_primitive should succeed for valid name"
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        team_name._value = "Changed Team"  # type: ignore[misc]


def test_team_name_equality() -> None:
    """Test that team names with same value are equal."""
    team_name1 = TeamName.from_primitive("Alpha Team").expect(
        "TeamName.from_primitive should succeed for valid name"
    )
    team_name2 = TeamName.from_primitive("Alpha Team").expect(
        "TeamName.from_primitive should succeed for valid name"
    )
    assert team_name1 == team_name2


def test_team_name_inequality() -> None:
    """Test that team names with different values are not equal."""
    team_name1 = TeamName.from_primitive("Alpha Team").expect(
        "TeamName.from_primitive should succeed for valid name"
    )
    team_name2 = TeamName.from_primitive("Beta Team").expect(
        "TeamName.from_primitive should succeed for valid name"
    )
    assert team_name1 != team_name2
