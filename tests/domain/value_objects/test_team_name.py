"""Tests for TeamName value object."""

import dataclasses

import pytest

from app.domain.value_objects.team_name import TeamName


def test_create_valid_team_name() -> None:
    """Test creating a valid team name."""
    team_name = TeamName.from_primitive("Alpha Team")
    assert team_name.to_primitive() == "Alpha Team"
    assert str(team_name) == "Alpha Team"


def test_create_team_name_with_single_character() -> None:
    """Test creating team name with minimum length (1 character)."""
    team_name = TeamName.from_primitive("A")
    assert team_name.to_primitive() == "A"


def test_create_team_name_with_max_length() -> None:
    """Test creating team name with maximum length (100 characters)."""
    long_name = "x" * 100
    team_name = TeamName.from_primitive(long_name)
    assert team_name.to_primitive() == long_name


def test_create_team_name_with_special_characters() -> None:
    """Test creating team name with special characters."""
    team_name = TeamName.from_primitive("Team-Alpha_2024")
    assert team_name.to_primitive() == "Team-Alpha_2024"


def test_empty_team_name_raises_error() -> None:
    """Test that empty team name raises ValueError."""
    with pytest.raises(ValueError, match="Team name cannot be empty"):
        TeamName.from_primitive("")


def test_team_name_too_long_raises_error() -> None:
    """Test that team name exceeding max length raises ValueError."""
    long_name = "x" * 101
    with pytest.raises(ValueError, match="must not exceed 100 characters"):
        TeamName.from_primitive(long_name)


def test_team_name_with_leading_whitespace_raises_error() -> None:
    """Test that team name with leading whitespace raises ValueError."""
    with pytest.raises(ValueError, match="cannot have leading or trailing whitespace"):
        TeamName.from_primitive("  Team Name")


def test_team_name_with_trailing_whitespace_raises_error() -> None:
    """Test that team name with trailing whitespace raises ValueError."""
    with pytest.raises(ValueError, match="cannot have leading or trailing whitespace"):
        TeamName.from_primitive("Team Name  ")


def test_team_name_repr() -> None:
    """Test team name representation."""
    team_name = TeamName.from_primitive("Alpha Team")
    assert repr(team_name) == "TeamName(Alpha Team)"


def test_team_name_is_immutable() -> None:
    """Test that team name is immutable."""
    team_name = TeamName.from_primitive("Alpha Team")
    with pytest.raises(dataclasses.FrozenInstanceError):
        team_name._value = "Changed Team"  # type: ignore[misc]


def test_team_name_equality() -> None:
    """Test that team names with same value are equal."""
    team_name1 = TeamName.from_primitive("Alpha Team")
    team_name2 = TeamName.from_primitive("Alpha Team")
    assert team_name1 == team_name2


def test_team_name_inequality() -> None:
    """Test that team names with different values are not equal."""
    team_name1 = TeamName.from_primitive("Alpha Team")
    team_name2 = TeamName.from_primitive("Beta Team")
    assert team_name1 != team_name2
