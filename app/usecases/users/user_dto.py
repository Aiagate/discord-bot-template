"""Data Transfer Object for User data."""

from dataclasses import dataclass


@dataclass(frozen=True)
class UserDTO:
    """A plain data structure representing a user."""

    id: int
    name: str
    email: str
