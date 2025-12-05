"""Data Transfer Object for User data."""

from dataclasses import dataclass


@dataclass(frozen=True)
class UserDTO:
    """A plain data structure representing a user."""

    id: str
    display_name: str
    email: str
