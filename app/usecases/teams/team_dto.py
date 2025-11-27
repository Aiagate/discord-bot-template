"""Data Transfer Object for Team data."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TeamDTO:
    """A plain data structure representing a team."""

    id: str
    name: str
