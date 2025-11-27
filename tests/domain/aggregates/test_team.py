"""Tests for Team aggregate."""

from datetime import UTC, datetime

import pytest

from app.domain.aggregates.team import Team
from app.domain.value_objects import TeamId, TeamName


def test_create_team_with_empty_name_raises_error() -> None:
    """Test that creating a Team with an empty name raises ValueError."""
    with pytest.raises(ValueError, match="Team name cannot be empty."):
        TeamName.from_primitive("")


def test_team_change_name() -> None:
    """Test that the change_name method updates the team's name."""
    team = Team(
        id=TeamId.generate(),
        name=TeamName.from_primitive("Old Team"),
    )
    team.change_name(TeamName.from_primitive("New Team"))
    assert team.name.to_primitive() == "New Team"


def test_team_creation_with_valid_data() -> None:
    """Test creating a team with valid data."""
    team_id = TeamId.generate()
    team_name = TeamName.from_primitive("Alpha Team")
    team = Team(id=team_id, name=team_name)
    assert team.id == team_id
    assert team.name == team_name
    assert isinstance(team.created_at, datetime)
    assert isinstance(team.updated_at, datetime)


def test_team_timestamps_use_utc() -> None:
    """Test that team timestamps use UTC timezone."""
    before = datetime.now(UTC)
    team = Team(
        id=TeamId.generate(),
        name=TeamName.from_primitive("Test Team"),
    )
    after = datetime.now(UTC)

    assert before <= team.created_at <= after
    assert before <= team.updated_at <= after


def test_team_with_explicit_timestamps() -> None:
    """Test creating team with explicit timestamps."""
    specific_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    team = Team(
        id=TeamId.generate(),
        name=TeamName.from_primitive("Test Team"),
        created_at=specific_time,
        updated_at=specific_time,
    )

    assert team.created_at == specific_time
    assert team.updated_at == specific_time


def test_team_creation_with_invalid_name_raises_error() -> None:
    """Test that creating team with invalid name raises ValueError."""
    # Test name too long
    with pytest.raises(ValueError, match="must not exceed 100 characters"):
        TeamName.from_primitive("x" * 101)

    # Test name with leading/trailing whitespace
    with pytest.raises(ValueError, match="cannot have leading or trailing whitespace"):
        TeamName.from_primitive("  Team Name  ")
